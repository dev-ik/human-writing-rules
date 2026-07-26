#!/usr/bin/env python3
"""Safe stdin/stdout execution boundary for external HWR adapters."""

import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from typing import Optional

try:
    from .hwr_reference import (
        HwrError,
        apply_artifact_record,
        apply_content_design,
        apply_review_record,
        apply_visual_record,
        build_adapter_packet,
    )
except ImportError:
    from hwr_reference import (
        HwrError,
        apply_artifact_record,
        apply_content_design,
        apply_review_record,
        apply_visual_record,
        build_adapter_packet,
    )


DEFAULT_TIMEOUT_SECONDS = 120.0
DEFAULT_MAX_OUTPUT_BYTES = 10 * 1024 * 1024
MAX_OUTPUT_BYTES = 100 * 1024 * 1024
MAX_PACKET_BYTES = 25 * 1024 * 1024
MAX_DIAGNOSTIC_BYTES = 64 * 1024
MAX_STDERR_BYTES = 1024 * 1024
ENV_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(token|secret|password|api[_-]?key|authorization)"
    r"(\s*[:=]\s*)([^\s,;]+)"
)
BEARER_RE = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]+")


def redact_diagnostics(value: str) -> str:
    value = SECRET_ASSIGNMENT_RE.sub(r"\1\2[REDACTED]", value)
    return BEARER_RE.sub("Bearer [REDACTED]", value)


def read_diagnostic(stream) -> tuple[str, bool]:
    stream.seek(0, os.SEEK_END)
    size = stream.tell()
    stream.seek(0)
    payload = stream.read(MAX_DIAGNOSTIC_BYTES)
    text = payload.decode("utf-8", errors="replace")
    return redact_diagnostics(text), size > MAX_DIAGNOSTIC_BYTES


def build_adapter_environment(pass_env: list[str]) -> dict[str, str]:
    environment: dict[str, str] = {}
    for name in ("PATH", "LANG", "LC_ALL", "LC_CTYPE"):
        value = os.environ.get(name)
        if value is not None:
            environment[name] = value
    for name in ("TMPDIR", "TMP", "TEMP"):
        value = os.environ.get(name)
        if value is not None and Path(value).is_dir():
            environment[name] = value

    for name in pass_env:
        if not ENV_NAME_RE.fullmatch(name):
            raise HwrError(
                "ADAPTER_ENV_INVALID",
                f"Invalid environment variable name: {name!r}",
            )
        if name not in os.environ:
            raise HwrError(
                "ADAPTER_ENV_MISSING",
                f"Requested environment variable is not set: {name}",
            )
        environment[name] = os.environ[name]
    return environment


def resolve_working_directory(value: Optional[str]) -> Path:
    directory = Path(value).expanduser().resolve() if value else Path.cwd().resolve()
    if not directory.is_dir():
        raise HwrError(
            "ADAPTER_CWD_INVALID",
            f"Adapter working directory does not exist: {directory}",
        )
    return directory


def resolve_executable(
    executable: str,
    working_directory: Path,
    environment: dict[str, str],
) -> Path:
    has_path_component = (
        Path(executable).is_absolute()
        or os.sep in executable
        or (os.altsep is not None and os.altsep in executable)
    )
    if has_path_component:
        candidate = Path(executable).expanduser()
        if not candidate.is_absolute():
            candidate = working_directory / candidate
        candidate = candidate.resolve()
        if not candidate.is_file() or not os.access(candidate, os.X_OK):
            raise HwrError(
                "ADAPTER_NOT_EXECUTABLE",
                f"Adapter executable is unavailable or not executable: {candidate}",
            )
        return candidate

    resolved = shutil.which(executable, path=environment.get("PATH", os.defpath))
    if resolved is None:
        raise HwrError(
            "ADAPTER_NOT_FOUND",
            f"Adapter executable was not found on PATH: {executable}",
        )
    return Path(resolved).resolve()


def validate_runtime_limits(timeout_seconds: float, max_output_bytes: int) -> None:
    if timeout_seconds <= 0 or timeout_seconds > 600:
        raise HwrError(
            "ADAPTER_TIMEOUT_INVALID",
            "Adapter timeout must be greater than 0 and at most 600 seconds",
        )
    if max_output_bytes < 1024 or max_output_bytes > MAX_OUTPUT_BYTES:
        raise HwrError(
            "ADAPTER_OUTPUT_LIMIT_INVALID",
            "Adapter output limit must be between 1024 and 104857600 bytes",
        )


def invoke_adapter(
    packet: dict,
    *,
    executable: str,
    arguments: list[str],
    pass_env: list[str],
    working_directory: Optional[str],
    timeout_seconds: float,
    max_output_bytes: int,
) -> tuple[dict, dict, list[dict]]:
    validate_runtime_limits(timeout_seconds, max_output_bytes)
    environment = build_adapter_environment(pass_env)
    directory = resolve_working_directory(working_directory)
    resolved_executable = resolve_executable(executable, directory, environment)
    packet_payload = json.dumps(
        packet,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    if len(packet_payload) > MAX_PACKET_BYTES:
        raise HwrError(
            "ADAPTER_PACKET_TOO_LARGE",
            "Adapter packet exceeds the 25 MiB safety limit",
            [{"bytes": len(packet_payload), "limit": MAX_PACKET_BYTES}],
        )

    command = [str(resolved_executable), *arguments]
    started = time.monotonic()
    with tempfile.TemporaryFile() as stdout_stream, tempfile.TemporaryFile() as stderr_stream:
        try:
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=stdout_stream,
                stderr=stderr_stream,
                cwd=directory,
                env=environment,
            )
        except (OSError, ValueError) as exc:
            raise HwrError(
                "ADAPTER_START_FAILED",
                "Adapter process could not be started",
                [{"error_type": type(exc).__name__}],
            ) from exc
        stop_monitor = threading.Event()
        output_exceeded = threading.Event()
        diagnostic_exceeded = threading.Event()

        def monitor_output() -> None:
            while not stop_monitor.wait(0.01):
                if process.poll() is not None:
                    return
                if os.fstat(stdout_stream.fileno()).st_size > max_output_bytes:
                    output_exceeded.set()
                    process.kill()
                    return
                if os.fstat(stderr_stream.fileno()).st_size > MAX_STDERR_BYTES:
                    diagnostic_exceeded.set()
                    process.kill()
                    return

        monitor = threading.Thread(
            target=monitor_output,
            name="hwr-adapter-output-monitor",
            daemon=True,
        )
        monitor.start()
        timed_out = False
        try:
            process.communicate(
                input=packet_payload,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            timed_out = True
            process.kill()
            process.communicate()
        finally:
            stop_monitor.set()
            monitor.join(timeout=1)

        elapsed_ms = round((time.monotonic() - started) * 1000)
        diagnostic, diagnostic_truncated = read_diagnostic(stderr_stream)
        stdout_stream.seek(0, os.SEEK_END)
        output_size = stdout_stream.tell()
        if timed_out:
            details: list[object] = [
                {
                    "timeout_seconds": timeout_seconds,
                    "stderr_present": bool(diagnostic),
                    "stderr_truncated": diagnostic_truncated,
                }
            ]
            if diagnostic:
                details.append({"stderr": diagnostic})
            raise HwrError(
                "ADAPTER_TIMEOUT",
                "Adapter execution exceeded its timeout",
                details,
            )
        if output_exceeded.is_set() or output_size > max_output_bytes:
            raise HwrError(
                "ADAPTER_OUTPUT_TOO_LARGE",
                "Adapter stdout exceeds the configured limit",
                [{"bytes": output_size, "limit": max_output_bytes}],
            )
        if diagnostic_exceeded.is_set():
            raise HwrError(
                "ADAPTER_STDERR_TOO_LARGE",
                "Adapter stderr exceeds the 1 MiB safety limit",
                [{"limit": MAX_STDERR_BYTES}],
            )
        stdout_stream.seek(0)
        output_payload = stdout_stream.read()

    if process.returncode != 0:
        details = [
            {
                "exit_code": process.returncode,
                "stderr_present": bool(diagnostic),
                "stderr_truncated": diagnostic_truncated,
            }
        ]
        if diagnostic:
            details.append({"stderr": diagnostic})
        raise HwrError(
            "ADAPTER_FAILED",
            "Adapter process returned a non-zero exit code",
            details,
        )

    try:
        output_text = output_payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HwrError(
            "ADAPTER_OUTPUT_ENCODING",
            "Adapter stdout is not valid UTF-8",
        ) from exc
    try:
        record = json.loads(output_text)
    except json.JSONDecodeError as exc:
        raise HwrError(
            "ADAPTER_OUTPUT_INVALID_JSON",
            "Adapter stdout must contain exactly one JSON object",
            [
                {
                    "line": exc.lineno,
                    "column": exc.colno,
                    "message": exc.msg,
                }
            ],
        ) from exc
    if not isinstance(record, dict):
        raise HwrError(
            "ADAPTER_OUTPUT_INVALID_ROOT",
            "Adapter stdout JSON root must be an object",
        )

    invocation = {
        "protocol_version": packet["protocol_version"],
        "stage": packet["stage"],
        "executable": resolved_executable.name,
        "argument_count": len(arguments),
        "passed_environment_names": sorted(set(pass_env)),
        "elapsed_ms": elapsed_ms,
        "stdout_bytes": output_size,
        "stderr_present": bool(diagnostic),
        "stderr_truncated": diagnostic_truncated,
    }
    warnings = []
    if diagnostic:
        warnings.append(
            {
                "code": "ADAPTER_STDERR",
                "message": diagnostic,
                "truncated": diagnostic_truncated,
            }
        )
    return record, invocation, warnings


def run_adapter_stage(
    repository: dict,
    run: dict,
    stage: str,
    *,
    executable: str,
    arguments: list[str],
    pass_env: list[str],
    working_directory: Optional[str] = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
) -> tuple[dict, list[dict]]:
    packet = build_adapter_packet(repository, run, stage)
    record, invocation, warnings = invoke_adapter(
        packet,
        executable=executable,
        arguments=arguments,
        pass_env=pass_env,
        working_directory=working_directory,
        timeout_seconds=timeout_seconds,
        max_output_bytes=max_output_bytes,
    )
    if stage == "design":
        updated = apply_content_design(repository, run, record)
    elif stage in {"draft", "edit", "revision"}:
        if record.get("stage") != stage:
            raise HwrError(
                "ADAPTER_STAGE_MISMATCH",
                f"Adapter returned stage {record.get('stage')!r}; expected {stage!r}",
            )
        updated = apply_artifact_record(repository, run, record)
    elif stage == "visual":
        updated = apply_visual_record(repository, run, record)
    elif stage == "review":
        updated = apply_review_record(repository, run, record)
    else:
        raise HwrError("UNKNOWN_ADAPTER_STAGE", f"Unknown adapter stage: {stage}")

    history = updated["output_package"]["audit"]["history"]
    history[-1]["adapter_runtime"] = invocation
    return updated, warnings
