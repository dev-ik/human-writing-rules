#!/usr/bin/env python3
"""Command-line interface for the Human Writing Rules reference runner."""

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

try:
    from .hwr_adapter_runtime import (
        DEFAULT_MAX_OUTPUT_BYTES,
        DEFAULT_TIMEOUT_SECONDS,
        run_adapter_stage,
    )
    from .hwr_reference import (
        HwrError,
        apply_artifact_record,
        apply_content_design,
        apply_review_record,
        apply_visual_record,
        build_adapter_packet,
        build_intake_plan,
        build_run_plan,
        create_source_snapshot,
        doctor,
        finalize_run,
        load_task_with_source_snapshots,
        load_repository,
        read_json,
        resolve_modules,
        validate_run_record,
    )
    from .hwr_workflow import resume_editorial_workflow, run_editorial_workflow
except ImportError:
    from hwr_adapter_runtime import (
        DEFAULT_MAX_OUTPUT_BYTES,
        DEFAULT_TIMEOUT_SECONDS,
        run_adapter_stage,
    )
    from hwr_reference import (
        HwrError,
        apply_artifact_record,
        apply_content_design,
        apply_review_record,
        apply_visual_record,
        build_adapter_packet,
        build_intake_plan,
        build_run_plan,
        create_source_snapshot,
        doctor,
        finalize_run,
        load_task_with_source_snapshots,
        load_repository,
        read_json,
        resolve_modules,
        validate_run_record,
    )
    from hwr_workflow import resume_editorial_workflow, run_editorial_workflow


DEFAULT_REPOSITORY = Path(__file__).resolve().parents[1]
EXIT_BY_CODE = {
    "INVALID_INPUT": 2,
    "INVALID_LIMIT": 2,
    "INVALID_TASK": 2,
    "INVALID_JSON": 2,
    "INVALID_JSON_ROOT": 2,
    "FILE_NOT_FOUND": 2,
    "OUTPUT_EXISTS": 2,
    "SOURCE_ENCODING_INVALID": 2,
    "SOURCE_FILE_INVALID": 2,
    "SOURCE_FILE_NOT_FOUND": 2,
    "SOURCE_MEDIA_TYPE_UNSUPPORTED": 2,
    "SOURCE_READ_FAILED": 2,
    "SOURCE_ROOT_INVALID": 2,
    "SOURCE_ROOT_NOT_FOUND": 2,
    "SOURCE_SNAPSHOT_INVALID": 2,
    "SOURCE_SNAPSHOT_TOO_LARGE": 2,
    "SOURCE_SNAPSHOT_TOTAL_TOO_LARGE": 2,
    "SOURCE_TOO_LARGE": 2,
    "UNSAFE_SOURCE_PATH": 2,
    "RUN_INVALID": 3,
    "ADAPTER_ENV_INVALID": 4,
    "ADAPTER_ENV_MISSING": 4,
    "ADAPTER_CWD_INVALID": 4,
    "ADAPTER_NOT_EXECUTABLE": 4,
    "ADAPTER_NOT_FOUND": 4,
    "ADAPTER_START_FAILED": 4,
    "ADAPTER_TIMEOUT_INVALID": 4,
    "ADAPTER_TIMEOUT": 4,
    "ADAPTER_OUTPUT_LIMIT_INVALID": 4,
    "ADAPTER_PACKET_TOO_LARGE": 4,
    "ADAPTER_FAILED": 4,
    "ADAPTER_OUTPUT_TOO_LARGE": 4,
    "ADAPTER_STDERR_TOO_LARGE": 4,
    "ADAPTER_OUTPUT_ENCODING": 4,
    "ADAPTER_OUTPUT_INVALID_JSON": 4,
    "ADAPTER_OUTPUT_INVALID_ROOT": 4,
    "ADAPTER_STAGE_MISMATCH": 4,
}


def add_config_task_arguments(parser: argparse.ArgumentParser, task_optional: bool) -> None:
    parser.add_argument(
        "--config",
        required=True,
        help="Path to a Human Writing Rules config JSON file.",
    )
    parser.add_argument(
        "--task",
        required=not task_optional,
        help="Path to a task-record JSON file.",
    )


def add_transition_arguments(
    parser: argparse.ArgumentParser,
    *,
    input_required: bool,
) -> None:
    parser.add_argument("--file", required=True, help="Current run-record JSON file.")
    if input_required:
        parser.add_argument(
            "--input",
            required=True,
            help="Stage result JSON file to apply.",
        )
    parser.add_argument(
        "--out",
        help="Write the updated run record here instead of returning it inline.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Allow --out to overwrite an existing file.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="hwr",
        description=(
            "Resolve Human Writing Rules modules, exchange vendor-neutral "
            "adapter packets, and enforce editorial lifecycle transitions. "
            "This reference CLI does not generate prose."
        ),
    )
    parser.add_argument(
        "--repo",
        default=str(DEFAULT_REPOSITORY),
        help="Path to the Human Writing Rules repository.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a stable JSON envelope to stdout.",
    )

    commands = parser.add_subparsers(dest="command", required=True)

    commands.add_parser(
        "doctor",
        help="Verify the offline repository, revisions, and available capabilities.",
    )

    registry = commands.add_parser(
        "registry",
        help="Read a raw local registry document.",
    )
    registry_commands = registry.add_subparsers(
        dest="registry_command", required=True
    )
    registry_get = registry_commands.add_parser(
        "get",
        help="Return one exact registry JSON document.",
    )
    registry_get.add_argument(
        "name",
        choices=[
            "objects",
            "languages",
            "formats",
            "topics",
            "platforms",
            "skills",
            "tones",
            "rfcs",
        ],
    )

    objects = commands.add_parser(
        "objects",
        help="Discover or read registered runtime objects.",
    )
    object_commands = objects.add_subparsers(dest="objects_command", required=True)
    objects_list = object_commands.add_parser(
        "list",
        help="List registered objects with optional applicability filters.",
    )
    objects_list.add_argument("--kind", help="Filter by exact object kind.")
    objects_list.add_argument("--language", help="Filter by language selector.")
    objects_list.add_argument("--format", dest="format_value", help="Filter by format selector.")
    objects_list.add_argument("--topic", help="Filter by topic selector.")
    objects_list.add_argument("--platform", help="Filter by platform selector.")
    objects_list.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum objects to return; default 100.",
    )
    objects_get = object_commands.add_parser(
        "get",
        help="Return one exact object by stable ID.",
    )
    objects_get.add_argument("object_id")

    sources = commands.add_parser(
        "sources",
        help="Create integrity-checked local source snapshots.",
    )
    source_commands = sources.add_subparsers(
        dest="sources_command",
        required=True,
    )
    sources_snapshot = source_commands.add_parser(
        "snapshot",
        help="Snapshot one bounded UTF-8 source file without network access.",
    )
    sources_snapshot.add_argument(
        "--input",
        required=True,
        help="Source file path relative to --source-root.",
    )
    sources_snapshot.add_argument(
        "--source-root",
        default=".",
        help="Allowed root for source input; default is the current directory.",
    )
    sources_snapshot.add_argument("--source-id", required=True)
    sources_snapshot.add_argument("--snapshot-id", required=True)
    sources_snapshot.add_argument(
        "--media-type",
        required=True,
        choices=[
            "application/json",
            "application/xml",
            "text/csv",
            "text/html",
            "text/markdown",
            "text/plain",
        ],
    )
    sources_snapshot.add_argument(
        "--captured-at",
        help="Optional caller-supplied capture timestamp or date.",
    )
    sources_snapshot.add_argument("--rights", help="Optional rights note.")
    sources_snapshot.add_argument("--notes", help="Optional scope or handling note.")
    sources_snapshot.add_argument(
        "--out",
        required=True,
        help="Write the source-snapshot JSON document here.",
    )
    sources_snapshot.add_argument(
        "--force",
        action="store_true",
        help="Allow --out to overwrite an existing file.",
    )

    modules = commands.add_parser(
        "modules",
        help="Resolve the smallest sufficient module set.",
    )
    module_commands = modules.add_subparsers(dest="modules_command", required=True)
    modules_resolve = module_commands.add_parser(
        "resolve",
        help="Resolve config and optional task overrides into dependency order.",
    )
    add_config_task_arguments(modules_resolve, task_optional=True)

    runs = commands.add_parser(
        "runs",
        help="Plan, validate, and advance a versioned editorial run record.",
    )
    run_commands = runs.add_subparsers(dest="runs_command", required=True)
    runs_questions = run_commands.add_parser(
        "questions",
        help=(
            "Build the next bounded question batch for an agent-led intake "
            "without drafting."
        ),
    )
    add_config_task_arguments(runs_questions, task_optional=True)
    runs_questions.add_argument(
        "--source-root",
        help=(
            "Allowed root for task snapshot_path values; "
            "default is the task file directory."
        ),
    )
    runs_questions.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum questions in the current batch; default and maximum 5.",
    )
    runs_plan = run_commands.add_parser(
        "plan",
        help="Build a pre-draft run record with gates, media, and review plan.",
    )
    add_config_task_arguments(runs_plan, task_optional=False)
    runs_plan.add_argument(
        "--source-root",
        help=(
            "Allowed root for task snapshot_path values; "
            "default is the task file directory."
        ),
    )
    runs_plan.add_argument(
        "--out",
        help="Write the run record to this JSON file instead of returning it inline.",
    )
    runs_plan.add_argument(
        "--force",
        action="store_true",
        help="Allow --out to overwrite an existing file.",
    )
    runs_check = run_commands.add_parser(
        "check",
        help="Validate an existing run record against the current repository.",
    )
    runs_check.add_argument("--file", required=True, help="Run-record JSON file.")
    runs_design = run_commands.add_parser(
        "apply-design",
        help="Apply a content-design result and enter media-decided.",
    )
    add_transition_arguments(runs_design, input_required=True)
    runs_artifact = run_commands.add_parser(
        "apply-artifact",
        help="Apply a draft, edit, or revision artifact result.",
    )
    add_transition_arguments(runs_artifact, input_required=True)
    runs_review = run_commands.add_parser(
        "apply-review",
        help="Apply a structured review report.",
    )
    add_transition_arguments(runs_review, input_required=True)
    runs_visual = run_commands.add_parser(
        "apply-visual",
        help="Apply produced visual assets for the current artifact revision.",
    )
    add_transition_arguments(runs_visual, input_required=True)
    runs_finalize = run_commands.add_parser(
        "finalize",
        help="Finalize a reviewed run when every readiness invariant passes.",
    )
    add_transition_arguments(runs_finalize, input_required=False)

    adapters = commands.add_parser(
        "adapters",
        help="Build vendor-neutral packets for model, tool, or human adapters.",
    )
    adapter_commands = adapters.add_subparsers(
        dest="adapters_command",
        required=True,
    )
    adapters_packet = adapter_commands.add_parser(
        "packet",
        help="Export the exact inputs and output schema for one pipeline stage.",
    )
    adapters_packet.add_argument("--file", required=True, help="Run-record JSON file.")
    adapters_packet.add_argument(
        "--stage",
        required=True,
        choices=["design", "draft", "edit", "visual", "review", "revision"],
    )
    adapters_run = adapter_commands.add_parser(
        "run",
        help="Run one trusted external adapter over stdin/stdout and apply its result.",
    )
    adapters_run.add_argument("--file", required=True, help="Current run-record JSON file.")
    adapters_run.add_argument(
        "--stage",
        required=True,
        choices=["design", "draft", "edit", "visual", "review", "revision"],
    )
    adapters_run.add_argument(
        "--executable",
        required=True,
        help="Executable path or PATH name; no shell is used.",
    )
    adapters_run.add_argument(
        "--arg",
        action="append",
        default=[],
        help="One adapter argument; repeat as needed. Use --arg=-x for values starting with '-'.",
    )
    adapters_run.add_argument(
        "--pass-env",
        action="append",
        default=[],
        help="Explicitly pass one existing environment variable; repeat as needed.",
    )
    adapters_run.add_argument(
        "--cwd",
        help="Adapter working directory; defaults to the current directory.",
    )
    adapters_run.add_argument(
        "--timeout-seconds",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Execution timeout, greater than 0 and at most 600; default 120.",
    )
    adapters_run.add_argument(
        "--max-output-bytes",
        type=int,
        default=DEFAULT_MAX_OUTPUT_BYTES,
        help="Maximum adapter stdout size; default 10485760.",
    )
    adapters_run.add_argument(
        "--out",
        help="Write the updated run record here instead of returning it inline.",
    )
    adapters_run.add_argument(
        "--force",
        action="store_true",
        help="Allow --out to overwrite an existing file.",
    )

    workflows = commands.add_parser(
        "workflows",
        help="Run a persisted end-to-end editorial workflow through one adapter.",
    )
    workflow_commands = workflows.add_subparsers(
        dest="workflows_command",
        required=True,
    )
    workflows_run = workflow_commands.add_parser(
        "run",
        help="Plan, execute, review, and package one artifact in a new workspace.",
    )
    add_config_task_arguments(workflows_run, task_optional=False)
    workflows_run.add_argument(
        "--source-root",
        help=(
            "Allowed root for task snapshot_path values; "
            "default is the task file directory."
        ),
    )
    workflows_run.add_argument(
        "--workspace",
        required=True,
        help="New or empty directory for run records and the separated output package.",
    )
    workflows_run.add_argument(
        "--executable",
        required=True,
        help="Executable path or PATH name; no shell is used.",
    )
    workflows_run.add_argument(
        "--arg",
        action="append",
        default=[],
        help=(
            "One adapter argument; repeat as needed. "
            "Supports {workspace} and {stage} placeholders."
        ),
    )
    workflows_run.add_argument(
        "--pass-env",
        action="append",
        default=[],
        help="Explicitly pass one existing environment variable; repeat as needed.",
    )
    workflows_run.add_argument(
        "--cwd",
        help="Adapter working directory; defaults to the current directory.",
    )
    workflows_run.add_argument(
        "--timeout-seconds",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Per-stage timeout, greater than 0 and at most 600; default 120.",
    )
    workflows_run.add_argument(
        "--max-output-bytes",
        type=int,
        default=DEFAULT_MAX_OUTPUT_BYTES,
        help="Maximum adapter stdout size per stage; default 10485760.",
    )
    workflows_resume = workflow_commands.add_parser(
        "resume",
        help="Resume a stopped workflow and perform at most one revision cycle.",
    )
    workflows_resume.add_argument(
        "--workspace",
        required=True,
        help="Existing persisted workflow directory.",
    )
    workflows_resume.add_argument(
        "--executable",
        required=True,
        help="Executable path or PATH name; no shell is used.",
    )
    workflows_resume.add_argument(
        "--arg",
        action="append",
        default=[],
        help=(
            "One adapter argument; repeat as needed. "
            "Supports {workspace} and {stage} placeholders."
        ),
    )
    workflows_resume.add_argument(
        "--pass-env",
        action="append",
        default=[],
        help="Explicitly pass one existing environment variable; repeat as needed.",
    )
    workflows_resume.add_argument(
        "--cwd",
        help="Adapter working directory; defaults to the current directory.",
    )
    workflows_resume.add_argument(
        "--timeout-seconds",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Per-stage timeout, greater than 0 and at most 600; default 120.",
    )
    workflows_resume.add_argument(
        "--max-output-bytes",
        type=int,
        default=DEFAULT_MAX_OUTPUT_BYTES,
        help="Maximum adapter stdout size per stage; default 10485760.",
    )

    return parser


def command_name(args: argparse.Namespace) -> str:
    parts = [args.command]
    for field in (
        "registry_command",
        "objects_command",
        "sources_command",
        "modules_command",
        "runs_command",
        "adapters_command",
        "workflows_command",
    ):
        value = getattr(args, field, None)
        if value:
            parts.append(value)
    return ".".join(parts)


def success_envelope(command: str, data: object, warnings: Optional[list] = None) -> dict:
    return {
        "ok": True,
        "command": command,
        "data": data,
        "warnings": warnings or [],
    }


def error_envelope(command: str, error: HwrError) -> dict:
    return {
        "ok": False,
        "command": command,
        "error": {
            "code": error.code,
            "message": error.message,
            "details": error.details,
        },
    }


def print_human(command: str, data: object) -> None:
    if command == "doctor" and isinstance(data, dict):
        status = "ready" if data.get("ready") else "not ready"
        print(
            f"HWR reference runner: {status}\n"
            f"Repository: {data.get('repository')}\n"
            f"Spec: {data.get('spec_revision')}\n"
            f"Registry: {data.get('registry_revision')}\n"
            f"Objects: {data.get('object_count')}\n"
            "Model adapter: not configured"
        )
        return
    if command == "objects.list" and isinstance(data, dict):
        for entry in data.get("items", []):
            print(f"{entry['id']}\t{entry['kind']}\t{entry['path']}")
        print(f"Returned {data.get('count', 0)} object(s).", file=sys.stderr)
        return
    print(json.dumps(data, ensure_ascii=False, indent=2))


def write_run_record(path_value: str, run: dict, force: bool) -> dict:
    path = Path(path_value).expanduser().resolve()
    if path.exists() and not force:
        raise HwrError(
            "OUTPUT_EXISTS",
            f"Output file already exists: {path}",
            ["Use --force to overwrite it."],
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(run, ensure_ascii=False, indent=2) + "\n"
    path.write_text(payload, encoding="utf-8")
    return {
        "output_file": str(path),
        "bytes": len(payload.encode("utf-8")),
        "run_id": run["run_id"],
        "state": run["state"],
    }


def write_source_snapshot(path_value: str, snapshot: dict, force: bool) -> dict:
    path = Path(path_value).expanduser().resolve()
    if path.exists() and not force:
        raise HwrError(
            "OUTPUT_EXISTS",
            f"Output file already exists: {path}",
            ["Use --force to overwrite it."],
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n"
    path.write_text(payload, encoding="utf-8")
    return {
        "output_file": str(path),
        "snapshot_id": snapshot["snapshot_id"],
        "source_id": snapshot["source_id"],
        "sha256": snapshot["sha256"],
        "source_bytes": snapshot["bytes"],
        "document_bytes": len(payload.encode("utf-8")),
    }


def transition_result(args: argparse.Namespace, run: dict) -> object:
    if args.out:
        return write_run_record(args.out, run, args.force)
    return run


def dispatch(args: argparse.Namespace) -> tuple[object, list]:
    repository = load_repository(Path(args.repo))
    warnings: list = []

    if args.command == "doctor":
        return doctor(repository), warnings

    if args.command == "registry" and args.registry_command == "get":
        return repository["registries"][args.name], warnings

    if args.command == "objects" and args.objects_command == "get":
        entry = repository["by_id"].get(args.object_id)
        if entry is None:
            raise HwrError("OBJECT_NOT_FOUND", f"Unknown object ID: {args.object_id}")
        return entry, warnings

    if args.command == "objects" and args.objects_command == "list":
        if args.limit < 1 or args.limit > 1000:
            raise HwrError("INVALID_LIMIT", "--limit must be between 1 and 1000")
        filters = {
            "kind": args.kind,
            "languages": args.language,
            "formats": args.format_value,
            "topics": args.topic,
            "platforms": args.platform,
        }
        items: list[dict] = []
        for entry in repository["objects"]:
            matches = True
            for field, expected in filters.items():
                if expected is None:
                    continue
                if field == "kind":
                    matches = entry.get(field) == expected
                else:
                    selector = entry.get(field, [])
                    matches = not selector or expected in selector
                if not matches:
                    break
            if matches:
                items.append(entry)
        items = sorted(items, key=lambda entry: entry["id"])[: args.limit]
        return {"items": items, "count": len(items), "limit": args.limit}, warnings

    if args.command == "sources" and args.sources_command == "snapshot":
        snapshot = create_source_snapshot(
            args.input,
            source_root=Path(args.source_root),
            source_id=args.source_id,
            snapshot_id=args.snapshot_id,
            media_type=args.media_type,
            captured_at=args.captured_at,
            rights=args.rights,
            notes=args.notes,
        )
        return write_source_snapshot(args.out, snapshot, args.force), warnings

    if args.command == "modules" and args.modules_command == "resolve":
        config = read_json(Path(args.config))
        task = read_json(Path(args.task)) if args.task else {}
        resolution = resolve_modules(repository, config, task)
        return resolution, resolution["warnings"]

    if args.command == "runs" and args.runs_command == "plan":
        config = read_json(Path(args.config))
        task = load_task_with_source_snapshots(
            Path(args.task),
            source_root=Path(args.source_root) if args.source_root else None,
        )
        run = build_run_plan(repository, config, task)
        if args.out:
            return write_run_record(args.out, run, args.force), warnings
        return run, warnings

    if args.command == "runs" and args.runs_command == "questions":
        config = read_json(Path(args.config))
        if args.task:
            task = load_task_with_source_snapshots(
                Path(args.task),
                source_root=Path(args.source_root) if args.source_root else None,
            )
        else:
            task = {"task_id": "interactive-intake"}
        return build_intake_plan(
            repository,
            config,
            task,
            limit=args.limit,
        ), warnings

    if args.command == "runs" and args.runs_command == "check":
        run = read_json(Path(args.file))
        errors = validate_run_record(repository, run)
        if errors:
            raise HwrError("RUN_INVALID", "Run record is invalid", errors)
        return {
            "valid": True,
            "run_id": run["run_id"],
            "state": run["state"],
            "spec_revision": run["spec_revision"],
            "registry_revision": run["registry_revision"],
        }, warnings

    if args.command == "runs" and args.runs_command == "apply-design":
        run = read_json(Path(args.file))
        record = read_json(Path(args.input))
        updated = apply_content_design(repository, run, record)
        return transition_result(args, updated), warnings

    if args.command == "runs" and args.runs_command == "apply-artifact":
        run = read_json(Path(args.file))
        record = read_json(Path(args.input))
        updated = apply_artifact_record(repository, run, record)
        return transition_result(args, updated), warnings

    if args.command == "runs" and args.runs_command == "apply-review":
        run = read_json(Path(args.file))
        record = read_json(Path(args.input))
        updated = apply_review_record(repository, run, record)
        return transition_result(args, updated), warnings

    if args.command == "runs" and args.runs_command == "apply-visual":
        run = read_json(Path(args.file))
        record = read_json(Path(args.input))
        updated = apply_visual_record(repository, run, record)
        return transition_result(args, updated), warnings

    if args.command == "runs" and args.runs_command == "finalize":
        run = read_json(Path(args.file))
        updated = finalize_run(repository, run)
        return transition_result(args, updated), warnings

    if args.command == "adapters" and args.adapters_command == "packet":
        run = read_json(Path(args.file))
        return build_adapter_packet(repository, run, args.stage), warnings

    if args.command == "adapters" and args.adapters_command == "run":
        run = read_json(Path(args.file))
        updated, adapter_warnings = run_adapter_stage(
            repository,
            run,
            args.stage,
            executable=args.executable,
            arguments=args.arg,
            pass_env=args.pass_env,
            working_directory=args.cwd,
            timeout_seconds=args.timeout_seconds,
            max_output_bytes=args.max_output_bytes,
        )
        return transition_result(args, updated), adapter_warnings

    if args.command == "workflows" and args.workflows_command == "run":
        config = read_json(Path(args.config))
        task = load_task_with_source_snapshots(
            Path(args.task),
            source_root=Path(args.source_root) if args.source_root else None,
        )
        return run_editorial_workflow(
            repository,
            config,
            task,
            workspace=Path(args.workspace),
            executable=args.executable,
            arguments=args.arg,
            pass_env=args.pass_env,
            working_directory=args.cwd,
            timeout_seconds=args.timeout_seconds,
            max_output_bytes=args.max_output_bytes,
        )

    if args.command == "workflows" and args.workflows_command == "resume":
        return resume_editorial_workflow(
            repository,
            workspace=Path(args.workspace),
            executable=args.executable,
            arguments=args.arg,
            pass_env=args.pass_env,
            working_directory=args.cwd,
            timeout_seconds=args.timeout_seconds,
            max_output_bytes=args.max_output_bytes,
        )

    raise HwrError("UNKNOWN_COMMAND", "Unsupported command")


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    current_command = command_name(args)
    try:
        data, warnings = dispatch(args)
    except HwrError as error:
        if args.json:
            print(
                json.dumps(
                    error_envelope(current_command, error),
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )
        else:
            print(f"error [{error.code}]: {error.message}", file=sys.stderr)
            for detail in error.details:
                print(f"  {detail}", file=sys.stderr)
        return EXIT_BY_CODE.get(error.code, 3)

    envelope = success_envelope(current_command, data, warnings)
    if args.json:
        print(json.dumps(envelope, ensure_ascii=False, separators=(",", ":")))
    else:
        print_human(current_command, data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
