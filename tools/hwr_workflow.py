#!/usr/bin/env python3
"""Persisted end-to-end orchestration for one HWR editorial run."""

import json
import os
import tempfile
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
        build_run_plan,
        finalize_run,
        read_json,
        require_valid_run,
    )
except ImportError:
    from hwr_adapter_runtime import (
        DEFAULT_MAX_OUTPUT_BYTES,
        DEFAULT_TIMEOUT_SECONDS,
        run_adapter_stage,
    )
    from hwr_reference import (
        HwrError,
        build_run_plan,
        finalize_run,
        read_json,
        require_valid_run,
    )


WORKFLOW_SCHEMA_VERSION = "1.0"


def atomic_write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(value)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_name = temporary.name
        os.replace(temporary_name, path)
    except OSError as exc:
        if temporary_name is not None:
            try:
                Path(temporary_name).unlink()
            except OSError:
                pass
        raise HwrError(
            "WORKFLOW_WRITE_FAILED",
            f"Workflow output could not be written: {path}",
            [{"error_type": type(exc).__name__}],
        ) from exc


def atomic_write_json(path: Path, value: object) -> None:
    atomic_write_text(
        path,
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
    )


def prepare_workspace(path: Path) -> Path:
    workspace = path.expanduser().resolve()
    if workspace.exists():
        if not workspace.is_dir():
            raise HwrError(
                "WORKFLOW_DIR_INVALID",
                f"Workflow workspace is not a directory: {workspace}",
            )
        try:
            has_entries = next(workspace.iterdir(), None) is not None
        except OSError as exc:
            raise HwrError(
                "WORKFLOW_DIR_INVALID",
                f"Workflow workspace cannot be inspected: {workspace}",
            ) from exc
        if has_entries:
            raise HwrError(
                "WORKFLOW_DIR_NOT_EMPTY",
                f"Workflow workspace must be empty: {workspace}",
            )
    else:
        try:
            workspace.mkdir(parents=True)
        except OSError as exc:
            raise HwrError(
                "WORKFLOW_DIR_INVALID",
                f"Workflow workspace cannot be created: {workspace}",
            ) from exc
    return workspace


def expand_arguments(arguments: list[str], workspace: Path, stage: str) -> list[str]:
    return [
        argument.replace("{workspace}", str(workspace)).replace("{stage}", stage)
        for argument in arguments
    ]


def persist_run(
    workspace: Path,
    run: dict,
    *,
    sequence: int,
    label: str,
) -> Path:
    path = workspace / "runs" / f"run-{sequence:02d}-{label}.json"
    atomic_write_json(path, run)
    return path


def write_output_package(workspace: Path, run: dict) -> dict[str, str]:
    output_directory = workspace / "output"
    package = run["output_package"]
    paths = {
        "publication": output_directory / "publication.md",
        "visual_assets": output_directory / "visual-assets.json",
        "source_notes": output_directory / "source-notes.json",
        "review_report": output_directory / "review-report.json",
        "revision_summary": output_directory / "revision-summary.json",
        "audit": output_directory / "audit.json",
        "final_run": output_directory / "run-final.json",
    }
    atomic_write_text(
        paths["publication"],
        package["publication_copy"]["content"].rstrip() + "\n",
    )
    for key in (
        "visual_assets",
        "source_notes",
        "review_report",
        "revision_summary",
        "audit",
    ):
        atomic_write_json(paths[key], package[key])
    atomic_write_json(paths["final_run"], run)
    return {key: str(path) for key, path in paths.items()}


def run_editorial_workflow(
    repository: dict,
    config: dict,
    task: dict,
    *,
    workspace: Path,
    executable: str,
    arguments: list[str],
    pass_env: list[str],
    working_directory: Optional[str] = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
) -> tuple[dict, list[dict]]:
    workflow_directory = prepare_workspace(workspace)
    manifest_path = workflow_directory / "workflow.json"
    warnings: list[dict] = []
    run = build_run_plan(repository, config, task)
    sequence = 0
    current_path = persist_run(
        workflow_directory,
        run,
        sequence=sequence,
        label="planned",
    )
    manifest = {
        "$schema": (
            "https://human-writing-rules.example/"
            "schemas/workflow-record.schema.json"
        ),
        "schema_version": WORKFLOW_SCHEMA_VERSION,
        "run_id": run["run_id"],
        "status": "blocked" if run["state"] == "blocked" else "running",
        "state": run["state"],
        "workspace": str(workflow_directory),
        "current_run_file": str(current_path),
        "stages": [
            {
                "stage": "plan",
                "input_state": None,
                "output_state": run["state"],
                "run_file": str(current_path),
            }
        ],
        "output_files": {},
        "warnings": warnings,
    }
    atomic_write_json(manifest_path, manifest)
    if run["state"] == "blocked":
        manifest["blockers"] = run["blockers"]
        atomic_write_json(manifest_path, manifest)
        return manifest, warnings

    def apply_stage(stage: str) -> None:
        nonlocal run, sequence
        input_state = run["state"]
        run, stage_warnings = run_adapter_stage(
            repository,
            run,
            stage,
            executable=executable,
            arguments=expand_arguments(arguments, workflow_directory, stage),
            pass_env=pass_env,
            working_directory=working_directory,
            timeout_seconds=timeout_seconds,
            max_output_bytes=max_output_bytes,
        )
        for warning in stage_warnings:
            warnings.append({"stage": stage, **warning})
        sequence += 1
        run_path = persist_run(
            workflow_directory,
            run,
            sequence=sequence,
            label=stage,
        )
        manifest["state"] = run["state"]
        manifest["current_run_file"] = str(run_path)
        manifest["stages"].append(
            {
                "stage": stage,
                "input_state": input_state,
                "output_state": run["state"],
                "run_file": str(run_path),
            }
        )
        atomic_write_json(manifest_path, manifest)

    try:
        for stage in ("design", "draft", "edit"):
            apply_stage(stage)
        visual_assets = run["output_package"]["visual_assets"]
        if visual_assets.get("status") == "pending-production":
            apply_stage("visual")
        apply_stage("review")

        if run["state"] == "revising":
            manifest["status"] = "needs-revision"
            manifest["open_findings"] = [
                finding
                for finding in run["output_package"]["review_report"].get(
                    "findings", []
                )
                if finding.get("severity") in {"blocker", "major"}
                and finding.get("status") in {
                    "open",
                    "deferred",
                    "accepted-risk",
                }
            ]
            atomic_write_json(manifest_path, manifest)
            return manifest, warnings
        if run["state"] != "reviewed":
            raise HwrError(
                "WORKFLOW_STATE_UNEXPECTED",
                f"Review ended in unexpected state: {run['state']}",
            )

        input_state = run["state"]
        run = finalize_run(repository, run)
        sequence += 1
        final_run_path = persist_run(
            workflow_directory,
            run,
            sequence=sequence,
            label="finalized",
        )
        manifest["state"] = run["state"]
        manifest["current_run_file"] = str(final_run_path)
        manifest["stages"].append(
            {
                "stage": "finalize",
                "input_state": input_state,
                "output_state": run["state"],
                "run_file": str(final_run_path),
            }
        )
        manifest["output_files"] = write_output_package(workflow_directory, run)
        manifest["status"] = "complete"
        atomic_write_json(manifest_path, manifest)
        return manifest, warnings
    except HwrError as error:
        manifest["status"] = "failed"
        manifest["state"] = run["state"]
        manifest["error"] = {
            "code": error.code,
            "message": error.message,
            "details": error.details,
        }
        atomic_write_json(manifest_path, manifest)
        raise


def resume_editorial_workflow(
    repository: dict,
    *,
    workspace: Path,
    executable: str,
    arguments: list[str],
    pass_env: list[str],
    working_directory: Optional[str] = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
) -> tuple[dict, list[dict]]:
    workflow_directory = workspace.expanduser().resolve()
    manifest_path = workflow_directory / "workflow.json"
    if not workflow_directory.is_dir() or not manifest_path.is_file():
        raise HwrError(
            "WORKFLOW_NOT_FOUND",
            f"Persisted workflow was not found: {workflow_directory}",
        )
    manifest = read_json(manifest_path)
    if manifest.get("status") in {"complete", "blocked"}:
        raise HwrError(
            "WORKFLOW_NOT_RESUMABLE",
            f"Workflow status {manifest.get('status')!r} cannot be resumed",
        )
    current_path_value = manifest.get("current_run_file")
    if not isinstance(current_path_value, str) or not current_path_value:
        raise HwrError(
            "WORKFLOW_RECORD_INVALID",
            "Workflow manifest is missing current_run_file",
        )
    current_path = Path(current_path_value).expanduser().resolve()
    try:
        current_path.relative_to(workflow_directory)
    except ValueError as exc:
        raise HwrError(
            "WORKFLOW_RECORD_INVALID",
            "Workflow current_run_file escapes its workspace",
        ) from exc
    run = read_json(current_path)
    require_valid_run(repository, run)
    if manifest.get("run_id") != run.get("run_id"):
        raise HwrError(
            "WORKFLOW_RECORD_INVALID",
            "Workflow manifest and current run use different run IDs",
        )

    warnings: list[dict] = []
    recorded_warnings = manifest.get("warnings", [])
    if not isinstance(recorded_warnings, list):
        raise HwrError(
            "WORKFLOW_RECORD_INVALID",
            "Workflow manifest warnings must be an array",
        )
    manifest["warnings"] = recorded_warnings
    stages = manifest.get("stages")
    if not isinstance(stages, list) or not stages:
        raise HwrError(
            "WORKFLOW_RECORD_INVALID",
            "Workflow manifest is missing stage history",
        )
    sequence = len(stages) - 1
    revision_applied = False
    manifest["status"] = "running"
    manifest.pop("error", None)
    manifest.pop("open_findings", None)
    atomic_write_json(manifest_path, manifest)

    def apply_stage(stage: str) -> None:
        nonlocal run, sequence
        input_state = run["state"]
        run, stage_warnings = run_adapter_stage(
            repository,
            run,
            stage,
            executable=executable,
            arguments=expand_arguments(arguments, workflow_directory, stage),
            pass_env=pass_env,
            working_directory=working_directory,
            timeout_seconds=timeout_seconds,
            max_output_bytes=max_output_bytes,
        )
        for warning in stage_warnings:
            annotated = {"stage": stage, **warning}
            warnings.append(annotated)
            recorded_warnings.append(annotated)
        sequence += 1
        run_path = persist_run(
            workflow_directory,
            run,
            sequence=sequence,
            label=stage,
        )
        manifest["state"] = run["state"]
        manifest["current_run_file"] = str(run_path)
        manifest["stages"].append(
            {
                "stage": stage,
                "input_state": input_state,
                "output_state": run["state"],
                "run_file": str(run_path),
            }
        )
        atomic_write_json(manifest_path, manifest)

    try:
        while True:
            state = run["state"]
            if state == "context-ready":
                apply_stage("design")
            elif state == "media-decided":
                apply_stage("draft")
            elif state == "drafted":
                apply_stage("edit")
            elif state == "edited":
                visual_assets = run["output_package"]["visual_assets"]
                apply_stage(
                    "visual"
                    if visual_assets.get("status") == "pending-production"
                    else "review"
                )
            elif state == "revising":
                if revision_applied:
                    manifest["status"] = "needs-revision"
                    manifest["open_findings"] = [
                        finding
                        for finding in run["output_package"]["review_report"].get(
                            "findings", []
                        )
                        if finding.get("severity") in {"blocker", "major"}
                        and finding.get("status") in {
                            "open",
                            "deferred",
                            "accepted-risk",
                        }
                    ]
                    atomic_write_json(manifest_path, manifest)
                    return manifest, warnings
                apply_stage("revision")
                revision_applied = True
            elif state == "reviewed":
                input_state = run["state"]
                run = finalize_run(repository, run)
                sequence += 1
                run_path = persist_run(
                    workflow_directory,
                    run,
                    sequence=sequence,
                    label="finalized",
                )
                manifest["state"] = run["state"]
                manifest["current_run_file"] = str(run_path)
                manifest["stages"].append(
                    {
                        "stage": "finalize",
                        "input_state": input_state,
                        "output_state": run["state"],
                        "run_file": str(run_path),
                    }
                )
            elif state == "ready":
                manifest["output_files"] = write_output_package(
                    workflow_directory,
                    run,
                )
                manifest["status"] = "complete"
                atomic_write_json(manifest_path, manifest)
                return manifest, warnings
            else:
                raise HwrError(
                    "WORKFLOW_STATE_UNEXPECTED",
                    f"Workflow cannot resume from state: {state}",
                )
    except HwrError as error:
        manifest["status"] = "failed"
        manifest["state"] = run["state"]
        manifest["error"] = {
            "code": error.code,
            "message": error.message,
            "details": error.details,
        }
        atomic_write_json(manifest_path, manifest)
        raise
