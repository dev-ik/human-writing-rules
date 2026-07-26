#!/usr/bin/env python3
"""Deterministic, evaluator-neutral benchmark execution harness."""

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path, PurePosixPath
from typing import Optional

try:
    from .hwr_adapter_runtime import (
        DEFAULT_MAX_OUTPUT_BYTES,
        DEFAULT_TIMEOUT_SECONDS,
        invoke_adapter,
    )
    from .hwr_reference import (
        HwrError,
        build_adapter_packet,
        build_run_plan,
        create_source_snapshot,
        load_repository,
        read_json,
    )
    from .hwr_workflow import atomic_write_json
except ImportError:
    from hwr_adapter_runtime import (
        DEFAULT_MAX_OUTPUT_BYTES,
        DEFAULT_TIMEOUT_SECONDS,
        invoke_adapter,
    )
    from hwr_reference import (
        HwrError,
        build_adapter_packet,
        build_run_plan,
        create_source_snapshot,
        load_repository,
        read_json,
    )
    from hwr_workflow import atomic_write_json


BENCHMARK_PACKET_VERSION = "benchmark-1.0"
BENCHMARK_RESULT_VERSION = "1.0"
BENCHMARK_RECORD_VERSION = "1.0"
BENCHMARK_RECORD_SCHEMA = (
    "https://human-writing-rules.example/schemas/benchmark-run-record.schema.json"
)
MAX_BENCHMARK_JSON_BYTES = 5 * 1024 * 1024
MAX_REPETITIONS = 10
MAX_ATTEMPTS = 50
DEFAULT_REPOSITORY = Path(__file__).resolve().parents[1]
ALLOWED_TREATMENTS = {"baseline", "rules-assisted"}
ALLOWED_RESULT_STATUSES = {"completed", "blocked", "failed", "invalid"}
REQUIRED_OUTPUT_PARTS = {
    "publication_copy",
    "visual_assets",
    "source_notes",
    "review_report",
    "audit",
}
BENCHMARK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def resolve_repository_file(root: Path, value: object, label: str) -> Path:
    if not isinstance(value, str) or not value:
        raise HwrError("BENCHMARK_PATH_INVALID", f"{label} must be a relative path")
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts:
        raise HwrError(
            "BENCHMARK_PATH_INVALID",
            f"{label} must remain inside the repository: {value}",
        )
    candidate = (root / pure).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise HwrError(
            "BENCHMARK_PATH_INVALID",
            f"{label} resolves outside the repository: {value}",
        ) from exc
    if not candidate.is_file():
        raise HwrError(
            "BENCHMARK_FILE_NOT_FOUND",
            f"{label} does not exist: {value}",
        )
    return candidate


def read_bounded_json(path: Path, label: str) -> dict:
    try:
        with path.open("rb") as stream:
            payload = stream.read(MAX_BENCHMARK_JSON_BYTES + 1)
    except OSError as exc:
        raise HwrError(
            "BENCHMARK_READ_FAILED",
            f"{label} could not be read: {path}",
            [{"error_type": type(exc).__name__}],
        ) from exc
    if len(payload) > MAX_BENCHMARK_JSON_BYTES:
        raise HwrError(
            "BENCHMARK_INPUT_TOO_LARGE",
            f"{label} exceeds {MAX_BENCHMARK_JSON_BYTES} bytes",
        )
    try:
        value = json.loads(payload.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise HwrError(
            "BENCHMARK_ENCODING_INVALID",
            f"{label} must be UTF-8 JSON",
        ) from exc
    except json.JSONDecodeError as exc:
        raise HwrError(
            "BENCHMARK_JSON_INVALID",
            f"{label} is invalid JSON: {exc.msg}",
            [{"line": exc.lineno, "column": exc.colno}],
        ) from exc
    if not isinstance(value, dict):
        raise HwrError(
            "BENCHMARK_JSON_ROOT_INVALID",
            f"{label} JSON root must be an object",
        )
    return value


def non_empty_strings(value: object) -> bool:
    return (
        isinstance(value, list)
        and all(isinstance(item, str) and item for item in value)
    )


def validate_benchmark_case(case: dict) -> list[str]:
    errors: list[str] = []
    for field in (
        "id",
        "revision",
        "profile",
        "spec_revision",
        "language",
        "content_type",
        "topic",
        "platform",
        "risk_level",
        "intent",
        "author_perspective",
        "task_path",
        "config_path",
    ):
        if not isinstance(case.get(field), str) or not case[field]:
            errors.append(f"{field} must be a non-empty string")
    if not isinstance(case.get("audience"), (str, dict)):
        errors.append("audience must be a string or object")
    benchmark_input = case.get("input")
    if not isinstance(benchmark_input, dict):
        errors.append("input must be an object")
    elif not isinstance(benchmark_input.get("brief"), str) or not benchmark_input[
        "brief"
    ]:
        errors.append("input.brief must be a non-empty string")
    for field in (
        "constraints",
        "required_modules",
        "required_reviewers",
        "expected_output_parts",
        "known_limitations",
    ):
        if not non_empty_strings(case.get(field)):
            errors.append(f"{field} must be an array of non-empty strings")
        elif len(case[field]) != len(set(case[field])):
            errors.append(f"{field} must not contain duplicates")
    output_parts = case.get("expected_output_parts", [])
    missing_output_parts = sorted(REQUIRED_OUTPUT_PARTS - set(output_parts))
    if missing_output_parts:
        errors.append(
            "expected_output_parts omits: " + ", ".join(missing_output_parts)
        )

    visuals = case.get("visuals")
    if not isinstance(visuals, dict) or visuals.get("mode") not in {
        "none",
        "auto",
        "required",
    }:
        errors.append("visuals.mode must be none, auto, or required")

    source_materials = case.get("source_materials")
    if not isinstance(source_materials, list) or not source_materials:
        errors.append("source_materials must be a non-empty array")
    else:
        source_ids: list[str] = []
        for index, source in enumerate(source_materials):
            label = f"source_materials[{index}]"
            if not isinstance(source, dict):
                errors.append(f"{label} must be an object")
                continue
            for field in (
                "source_id",
                "path",
                "media_type",
                "captured_at",
                "rights",
            ):
                if not isinstance(source.get(field), str) or not source[field]:
                    errors.append(f"{label}.{field} must be a non-empty string")
            if isinstance(source.get("source_id"), str):
                source_ids.append(source["source_id"])
        if len(source_ids) != len(set(source_ids)):
            errors.append("source_materials must not contain duplicate source IDs")

    evaluation = case.get("evaluation")
    if not isinstance(evaluation, dict):
        errors.append("evaluation must be an object")
    else:
        if not non_empty_strings(evaluation.get("dimensions")):
            errors.append("evaluation.dimensions must be a non-empty string array")
        if not isinstance(evaluation.get("instructions"), str) or not evaluation[
            "instructions"
        ]:
            errors.append("evaluation.instructions must be a non-empty string")
        hard_failures = evaluation.get("hard_failures")
        if not isinstance(hard_failures, list) or not hard_failures:
            errors.append("evaluation.hard_failures must be a non-empty array")
        else:
            hard_failure_ids: list[str] = []
            for index, failure in enumerate(hard_failures):
                label = f"evaluation.hard_failures[{index}]"
                if not isinstance(failure, dict):
                    errors.append(f"{label} must be an object")
                    continue
                for field in ("id", "description"):
                    if not isinstance(failure.get(field), str) or not failure[field]:
                        errors.append(f"{label}.{field} must be a non-empty string")
                if isinstance(failure.get("id"), str):
                    hard_failure_ids.append(failure["id"])
            if len(hard_failure_ids) != len(set(hard_failure_ids)):
                errors.append("evaluation hard-failure IDs must be unique")
    return errors


def validate_benchmark_plan(plan: dict) -> list[str]:
    errors: list[str] = []
    for field in (
        "benchmark_run_id",
        "revision",
        "case_path",
        "run_date",
        "execution_order",
        "treatment_difference",
    ):
        if not isinstance(plan.get(field), str) or not plan[field]:
            errors.append(f"{field} must be a non-empty string")
    if isinstance(plan.get("benchmark_run_id"), str) and not BENCHMARK_ID_RE.fullmatch(
        plan["benchmark_run_id"]
    ):
        errors.append("benchmark_run_id must contain only letters, digits, ., _, or -")
    repetitions = plan.get("repetitions")
    if (
        not isinstance(repetitions, int)
        or isinstance(repetitions, bool)
        or repetitions < 1
        or repetitions > MAX_REPETITIONS
    ):
        errors.append(f"repetitions must be between 1 and {MAX_REPETITIONS}")
    if plan.get("execution_order") != "declared-arm-order":
        errors.append("execution_order must be 'declared-arm-order'")

    controls = plan.get("controls")
    if not isinstance(controls, dict):
        errors.append("controls must be an object")
    else:
        for field in ("provider", "model", "model_revision", "retry_policy"):
            if not isinstance(controls.get(field), str) or not controls[field]:
                errors.append(f"controls.{field} must be a non-empty string")
        if controls.get("retry_policy") != "none":
            errors.append("controls.retry_policy must be 'none' in runner version 1.0")
        for field in (
            "settings",
            "execution_environment",
            "tool_configuration",
            "retrieval_configuration",
        ):
            if not isinstance(controls.get(field), dict):
                errors.append(f"controls.{field} must be an object")
        if not non_empty_strings(controls.get("output_requirements")):
            errors.append(
                "controls.output_requirements must be a non-empty string array"
            )
        budget = controls.get("time_budget_seconds")
        if (
            not isinstance(budget, (int, float))
            or isinstance(budget, bool)
            or budget <= 0
            or budget > 600
        ):
            errors.append(
                "controls.time_budget_seconds must be greater than 0 and at most 600"
            )

    arms = plan.get("arms")
    if not isinstance(arms, list) or len(arms) < 2:
        errors.append("arms must contain at least two arm records")
        arms = []
    arm_ids: list[str] = []
    treatments: list[str] = []
    for index, arm in enumerate(arms):
        label = f"arms[{index}]"
        if not isinstance(arm, dict):
            errors.append(f"{label} must be an object")
            continue
        for field in ("id", "treatment", "description"):
            if not isinstance(arm.get(field), str) or not arm[field]:
                errors.append(f"{label}.{field} must be a non-empty string")
        if arm.get("treatment") not in ALLOWED_TREATMENTS:
            errors.append(f"{label}.treatment is invalid")
        if not non_empty_strings(arm.get("instructions")):
            errors.append(f"{label}.instructions must be a non-empty string array")
        if isinstance(arm.get("id"), str):
            arm_ids.append(arm["id"])
            if not BENCHMARK_ID_RE.fullmatch(arm["id"]):
                errors.append(
                    f"{label}.id must contain only letters, digits, ., _, or -"
                )
        if isinstance(arm.get("treatment"), str):
            treatments.append(arm["treatment"])
    if len(arm_ids) != len(set(arm_ids)):
        errors.append("arm IDs must be unique")
    for required_treatment in sorted(ALLOWED_TREATMENTS):
        if required_treatment not in treatments:
            errors.append(f"plan requires a {required_treatment} arm")
    if (
        isinstance(repetitions, int)
        and not isinstance(repetitions, bool)
        and repetitions * len(arms) > MAX_ATTEMPTS
    ):
        errors.append(f"plan exceeds the {MAX_ATTEMPTS}-attempt safety limit")
    return errors


def validate_arm_result(result: dict, packet: dict, case: dict) -> list[str]:
    errors: list[str] = []
    allowed_fields = {
        "protocol_version",
        "attempt_id",
        "case_id",
        "case_revision",
        "arm_id",
        "status",
        "source_access",
        "output_unit",
        "errors",
        "manual_interventions",
        "hard_failures",
    }
    extra_fields = sorted(set(result) - allowed_fields)
    if extra_fields:
        errors.append("result contains unknown fields: " + ", ".join(extra_fields))
    expected = {
        "protocol_version": BENCHMARK_RESULT_VERSION,
        "attempt_id": packet["attempt_id"],
        "case_id": case["id"],
        "case_revision": case["revision"],
        "arm_id": packet["arm"]["id"],
    }
    for field, value in expected.items():
        if result.get(field) != value:
            errors.append(f"{field} must equal {value!r}")
    status = result.get("status")
    if status not in ALLOWED_RESULT_STATUSES:
        errors.append("status is invalid")
    for field in ("source_access", "errors", "manual_interventions", "hard_failures"):
        if not isinstance(result.get(field), list):
            errors.append(f"{field} must be an array")

    source_access = result.get("source_access")
    if isinstance(source_access, list):
        known_source_ids = {
            source["source_id"] for source in case["source_materials"]
        }
        reported_source_ids: list[str] = []
        for index, access in enumerate(source_access):
            label = f"source_access[{index}]"
            if not isinstance(access, dict):
                errors.append(f"{label} must be an object")
                continue
            source_id = access.get("source_id")
            if source_id not in known_source_ids:
                errors.append(f"{label}.source_id is unknown")
            elif isinstance(source_id, str):
                reported_source_ids.append(source_id)
            if access.get("status") not in {
                "available",
                "unavailable",
                "redacted",
                "error",
            }:
                errors.append(f"{label}.status is invalid")
        if len(reported_source_ids) != len(set(reported_source_ids)):
            errors.append("source_access must not contain duplicate source IDs")
        if status == "completed":
            missing_sources = sorted(known_source_ids - set(reported_source_ids))
            if missing_sources:
                errors.append(
                    "completed result omits source access: "
                    + ", ".join(missing_sources)
                )

    known_failures = {
        failure["id"] for failure in case["evaluation"]["hard_failures"]
    }
    hard_failures = result.get("hard_failures", [])
    if isinstance(hard_failures, list):
        if not all(isinstance(item, str) and item for item in hard_failures):
            errors.append("hard_failures must contain non-empty IDs")
        else:
            unknown = sorted(set(hard_failures) - known_failures)
            if unknown:
                errors.append(
                    "hard_failures references unknown IDs: " + ", ".join(unknown)
                )
            if len(hard_failures) != len(set(hard_failures)):
                errors.append("hard_failures must not contain duplicates")

    output_unit = result.get("output_unit")
    if status == "completed":
        if not isinstance(output_unit, dict):
            errors.append("completed result requires output_unit")
        else:
            missing = sorted(REQUIRED_OUTPUT_PARTS - output_unit.keys())
            if missing:
                errors.append("output_unit omits: " + ", ".join(missing))
            publication_copy = output_unit.get("publication_copy")
            if not isinstance(publication_copy, str) or not publication_copy:
                errors.append("output_unit.publication_copy must be non-empty")
            if not isinstance(output_unit.get("visual_assets"), list):
                errors.append("output_unit.visual_assets must be an array")
            for field in ("source_notes", "review_report", "audit"):
                if not isinstance(output_unit.get(field), dict):
                    errors.append(f"output_unit.{field} must be an object")
    elif output_unit is not None and not isinstance(output_unit, dict):
        errors.append("output_unit must be an object or null")

    error_items = result.get("errors")
    if status in {"failed", "invalid"} and error_items == []:
        errors.append(f"{status} result requires at least one error")
    return errors


def validate_benchmark_run_record(record: dict) -> list[str]:
    errors: list[str] = []
    if record.get("$schema") != BENCHMARK_RECORD_SCHEMA:
        errors.append("run record uses an unknown schema")
    if record.get("schema_version") != BENCHMARK_RECORD_VERSION:
        errors.append("run record schema_version is invalid")
    attempts = record.get("attempts")
    counts = record.get("counts")
    if not isinstance(attempts, list):
        errors.append("attempts must be an array")
        attempts = []
    if not isinstance(counts, dict):
        errors.append("counts must be an object")
        counts = {}
    attempt_ids: list[str] = []
    observed = {status: 0 for status in ALLOWED_RESULT_STATUSES}
    hard_failure_count = 0
    for index, attempt in enumerate(attempts):
        label = f"attempts[{index}]"
        if not isinstance(attempt, dict):
            errors.append(f"{label} must be an object")
            continue
        attempt_id = attempt.get("attempt_id")
        if not isinstance(attempt_id, str) or not attempt_id:
            errors.append(f"{label}.attempt_id must be non-empty")
        else:
            attempt_ids.append(attempt_id)
        status = attempt.get("status")
        if status not in ALLOWED_RESULT_STATUSES:
            errors.append(f"{label}.status is invalid")
        else:
            observed[status] += 1
        hard_failures = attempt.get("hard_failures")
        if not isinstance(hard_failures, list):
            errors.append(f"{label}.hard_failures must be an array")
        else:
            hard_failure_count += len(hard_failures)
    if len(attempt_ids) != len(set(attempt_ids)):
        errors.append("attempt IDs must be unique")
    if counts.get("attempted") != len(attempts):
        errors.append("counts.attempted does not match attempts")
    for status, count in observed.items():
        if counts.get(status) != count:
            errors.append(f"counts.{status} does not match attempts")
    if counts.get("hard_failures") != hard_failure_count:
        errors.append("counts.hard_failures does not match attempts")
    if counts.get("excluded") != 0:
        errors.append("runner version 1.0 must not exclude attempts")
    expected_status = (
        "complete"
        if attempts and observed["completed"] == len(attempts)
        else "complete-with-failures"
    )
    if record.get("status") != expected_status:
        errors.append(f"run status must be {expected_status}")
    evaluation = record.get("evaluation")
    if not isinstance(evaluation, dict) or evaluation.get("status") != "not-run":
        errors.append("execution record evaluation status must be not-run")
    return errors


def prepare_workspace(path: Path) -> Path:
    workspace = path.expanduser().resolve()
    if workspace.exists():
        if not workspace.is_dir():
            raise HwrError(
                "BENCHMARK_WORKSPACE_INVALID",
                f"Benchmark workspace is not a directory: {workspace}",
            )
        if next(workspace.iterdir(), None) is not None:
            raise HwrError(
                "BENCHMARK_WORKSPACE_NOT_EMPTY",
                f"Benchmark workspace must be empty: {workspace}",
            )
    else:
        try:
            workspace.mkdir(parents=True)
        except OSError as exc:
            raise HwrError(
                "BENCHMARK_WORKSPACE_INVALID",
                f"Benchmark workspace could not be created: {workspace}",
            ) from exc
    return workspace


def file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            while chunk := stream.read(1024 * 1024):
                digest.update(chunk)
    except OSError as exc:
        raise HwrError(
            "BENCHMARK_READ_FAILED",
            f"Benchmark input could not be hashed: {path}",
            [{"error_type": type(exc).__name__}],
        ) from exc
    return f"sha256:{digest.hexdigest()}"


def prepare_case_context(repository: dict, case: dict) -> tuple[dict, dict, dict]:
    root = repository["root"]
    task_path = resolve_repository_file(root, case["task_path"], "case.task_path")
    config_path = resolve_repository_file(
        root,
        case["config_path"],
        "case.config_path",
    )
    task = read_json(task_path)
    config = read_json(config_path)
    task = copy.deepcopy(task)
    sources_by_id = {
        source.get("id"): source
        for source in task.get("sources", [])
        if isinstance(source, dict)
    }
    declared_source_ids = {
        material["source_id"] for material in case["source_materials"]
    }
    task_source_ids = set(sources_by_id)
    if task_source_ids != declared_source_ids:
        raise HwrError(
            "BENCHMARK_SOURCE_MISMATCH",
            "Benchmark case must pin the complete task source set",
            [
                {
                    "undeclared_task_sources": sorted(
                        task_source_ids - declared_source_ids
                    ),
                    "case_sources_absent_from_task": sorted(
                        declared_source_ids - task_source_ids
                    ),
                }
            ],
        )
    for material in case["source_materials"]:
        source_id = material["source_id"]
        if source_id not in sources_by_id:
            raise HwrError(
                "BENCHMARK_SOURCE_MISMATCH",
                f"Case source {source_id} is absent from the task",
            )
        if sources_by_id[source_id].get("snapshot") is not None:
            raise HwrError(
                "BENCHMARK_SOURCE_MISMATCH",
                f"Task source {source_id} already contains a snapshot",
            )
        snapshot = create_source_snapshot(
            material["path"],
            source_root=root,
            source_id=source_id,
            snapshot_id=f"{case['id']}:{case['revision']}:{source_id}",
            media_type=material["media_type"],
            captured_at=material["captured_at"],
            rights=material["rights"],
            notes=material.get("notes"),
        )
        sources_by_id[source_id]["snapshot"] = snapshot

    run = build_run_plan(repository, config, task)
    if run["state"] != "context-ready":
        raise HwrError(
            "BENCHMARK_CASE_BLOCKED",
            "Benchmark task did not pass the context gate",
            run["blockers"],
        )
    resolved_inputs = run["resolution"]["inputs"]
    for field in (
        "language",
        "content_type",
        "topic",
        "platform",
        "risk_level",
        "audience",
        "intent",
        "author_perspective",
    ):
        if resolved_inputs.get(field) != case[field]:
            raise HwrError(
                "BENCHMARK_CASE_MISMATCH",
                f"Case {field} does not match resolved task input",
                [{"case": case[field], "resolved": resolved_inputs.get(field)}],
            )
    if case.get("skill") != resolved_inputs.get("skill"):
        raise HwrError(
            "BENCHMARK_CASE_MISMATCH",
            "Case skill does not match resolved task input",
        )
    if case["visuals"]["mode"] != resolved_inputs.get("visual_mode"):
        raise HwrError(
            "BENCHMARK_CASE_MISMATCH",
            "Case visual mode does not match resolved task input",
        )
    if case["constraints"] != run["task"]["constraints"]:
        raise HwrError(
            "BENCHMARK_CASE_MISMATCH",
            "Case constraints do not match resolved task constraints",
        )
    missing_modules = sorted(
        set(case["required_modules"]) - set(run["resolution"]["dependency_order"])
    )
    if missing_modules:
        raise HwrError(
            "BENCHMARK_MODULES_MISSING",
            "Resolved task omits required benchmark modules",
            missing_modules,
        )
    resolved_reviewers = {
        reviewer["reviewer_id"] for reviewer in run["review_plan"]
    }
    missing_reviewers = sorted(
        set(case["required_reviewers"]) - resolved_reviewers
    )
    if missing_reviewers:
        raise HwrError(
            "BENCHMARK_REVIEWERS_MISSING",
            "Resolved task omits required benchmark reviewers",
            missing_reviewers,
        )
    return task, config, run


def build_benchmark_packet(
    repository: dict,
    case: dict,
    plan: dict,
    arm: dict,
    repetition: int,
    task: dict,
    config: dict,
    run: dict,
) -> dict:
    attempt_id = f"r{repetition:02d}-{arm['id']}"
    treatment_context = None
    if arm["treatment"] == "rules-assisted":
        design_packet = build_adapter_packet(repository, run, "design")
        treatment_context = {
            "spec_revision": repository["spec_revision"],
            "registry_revision": repository["registry_revision"],
            "config": config,
            "resolution": run["resolution"],
            "gates": run["gates"],
            "claim_ledger": run["claim_ledger"],
            "module_manifest": design_packet["module_manifest"],
        }
    return {
        "protocol_version": BENCHMARK_PACKET_VERSION,
        "stage": "benchmark-run",
        "packet_id": f"{plan['benchmark_run_id']}:{attempt_id}",
        "benchmark_run_id": plan["benchmark_run_id"],
        "attempt_id": attempt_id,
        "repetition": repetition,
        "case": case,
        "arm": arm,
        "controls": plan["controls"],
        "common_input": {
            "task": task,
            "source_records": task["sources"],
            "expected_output_parts": case["expected_output_parts"],
            "evaluation_dimensions": case["evaluation"]["dimensions"],
            "hard_failures": case["evaluation"]["hard_failures"],
        },
        "treatment_context": treatment_context,
    }


def run_benchmark(
    repository: dict,
    plan: dict,
    *,
    plan_path: Path,
    workspace: Path,
    executable: str,
    arguments: list[str],
    pass_env: list[str],
    working_directory: Optional[str] = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_output_bytes: int = DEFAULT_MAX_OUTPUT_BYTES,
) -> tuple[dict, list[dict]]:
    plan_errors = validate_benchmark_plan(plan)
    if plan_errors:
        raise HwrError(
            "BENCHMARK_PLAN_INVALID",
            "Benchmark execution plan is invalid",
            plan_errors,
        )
    case_path = resolve_repository_file(
        repository["root"],
        plan["case_path"],
        "plan.case_path",
    )
    case = read_bounded_json(case_path, "benchmark case")
    case_errors = validate_benchmark_case(case)
    if case_errors:
        raise HwrError(
            "BENCHMARK_CASE_INVALID",
            "Benchmark case is invalid",
            case_errors,
        )
    if case["spec_revision"] != repository["spec_revision"]:
        raise HwrError(
            "BENCHMARK_SPEC_MISMATCH",
            "Benchmark case spec revision does not match the repository",
        )
    task, config, prepared_run = prepare_case_context(repository, case)
    benchmark_workspace = prepare_workspace(workspace)
    manifest_path = benchmark_workspace / "benchmark-run.json"
    warnings: list[dict] = []
    manifest = {
        "$schema": BENCHMARK_RECORD_SCHEMA,
        "schema_version": BENCHMARK_RECORD_VERSION,
        "benchmark_run_id": plan["benchmark_run_id"],
        "status": "running",
        "case": {
            "id": case["id"],
            "revision": case["revision"],
            "path": plan["case_path"],
            "task_path": case["task_path"],
            "case_file": str(case_path),
            "sha256": file_digest(case_path),
        },
        "plan": {
            "revision": plan["revision"],
            "file": str(plan_path.expanduser().resolve()),
            "sha256": file_digest(plan_path.expanduser().resolve()),
        },
        "spec_revision": repository["spec_revision"],
        "registry_revision": repository["registry_revision"],
        "run_date": plan["run_date"],
        "execution_order": plan["execution_order"],
        "controls": plan["controls"],
        "treatment_difference": plan["treatment_difference"],
        "workspace": str(benchmark_workspace),
        "attempts": [],
        "counts": {
            "attempted": 0,
            "completed": 0,
            "blocked": 0,
            "failed": 0,
            "invalid": 0,
            "hard_failures": 0,
            "excluded": 0,
        },
        "evaluation": {
            "status": "not-run",
            "dimensions": case["evaluation"]["dimensions"],
            "instructions": case["evaluation"]["instructions"],
            "conclusion": (
                "No comparative conclusion is produced by the execution runner."
            ),
        },
        "known_limitations": case["known_limitations"],
        "warnings": warnings,
    }
    atomic_write_json(manifest_path, manifest)

    for repetition in range(1, plan["repetitions"] + 1):
        for arm in plan["arms"]:
            packet = build_benchmark_packet(
                repository,
                case,
                plan,
                arm,
                repetition,
                task,
                config,
                prepared_run,
            )
            attempt_id = packet["attempt_id"]
            attempt_directory = benchmark_workspace / "attempts" / attempt_id
            packet_path = attempt_directory / "packet.json"
            raw_result_path = attempt_directory / "result-raw.json"
            atomic_write_json(packet_path, packet)
            attempt = {
                "attempt_id": attempt_id,
                "arm_id": arm["id"],
                "treatment": arm["treatment"],
                "repetition": repetition,
                "status": "running",
                "packet_file": str(packet_path),
                "result_file": None,
                "invocation": None,
                "error": None,
                "hard_failures": [],
            }
            manifest["attempts"].append(attempt)
            manifest["counts"]["attempted"] += 1
            atomic_write_json(manifest_path, manifest)
            try:
                result, invocation, adapter_warnings = invoke_adapter(
                    packet,
                    executable=executable,
                    arguments=arguments,
                    pass_env=pass_env,
                    working_directory=working_directory,
                    timeout_seconds=timeout_seconds,
                    max_output_bytes=max_output_bytes,
                )
                atomic_write_json(raw_result_path, result)
                attempt["result_file"] = str(raw_result_path)
                attempt["invocation"] = invocation
                result_errors = validate_arm_result(result, packet, case)
                if result_errors:
                    attempt["status"] = "invalid"
                    attempt["error"] = {
                        "code": "BENCHMARK_RESULT_INVALID",
                        "message": "Benchmark arm result is invalid",
                        "details": result_errors,
                    }
                else:
                    attempt["status"] = result["status"]
                    attempt["hard_failures"] = result["hard_failures"]
                    manifest["counts"]["hard_failures"] += len(
                        result["hard_failures"]
                    )
                for warning in adapter_warnings:
                    warnings.append({"attempt_id": attempt_id, **warning})
            except HwrError as exc:
                attempt["status"] = "failed"
                attempt["error"] = {
                    "code": exc.code,
                    "message": exc.message,
                    "details": exc.details,
                }
            manifest["counts"][attempt["status"]] += 1
            atomic_write_json(manifest_path, manifest)

    incomplete = (
        manifest["counts"]["attempted"] - manifest["counts"]["completed"]
    )
    manifest["status"] = "complete" if incomplete == 0 else "complete-with-failures"
    record_errors = validate_benchmark_run_record(manifest)
    if record_errors:
        raise HwrError(
            "BENCHMARK_RECORD_INVALID",
            "Generated benchmark run record is invalid",
            record_errors,
        )
    atomic_write_json(manifest_path, manifest)
    return manifest, warnings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Execute all declared arms in one pinned HWR benchmark plan."
    )
    parser.add_argument("--repo", default=str(DEFAULT_REPOSITORY))
    parser.add_argument("--plan", required=True)
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--executable", required=True)
    parser.add_argument("--arg", action="append", default=[])
    parser.add_argument("--pass-env", action="append", default=[])
    parser.add_argument("--cwd")
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
    )
    parser.add_argument(
        "--max-output-bytes",
        type=int,
        default=DEFAULT_MAX_OUTPUT_BYTES,
    )
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        repository = load_repository(Path(args.repo))
        plan_path = Path(args.plan)
        plan = read_bounded_json(plan_path, "benchmark plan")
        manifest, warnings = run_benchmark(
            repository,
            plan,
            plan_path=plan_path,
            workspace=Path(args.workspace),
            executable=args.executable,
            arguments=args.arg,
            pass_env=args.pass_env,
            working_directory=args.cwd,
            timeout_seconds=args.timeout_seconds,
            max_output_bytes=args.max_output_bytes,
        )
    except HwrError as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": {
                        "code": exc.code,
                        "message": exc.message,
                        "details": exc.details,
                    },
                },
                ensure_ascii=False,
                separators=(",", ":"),
            )
        )
        return 2
    print(
        json.dumps(
            {"ok": True, "data": manifest, "warnings": warnings},
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
