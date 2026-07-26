#!/usr/bin/env python3
"""Validate runtime objects, indexes, dependencies, and starter configuration."""

import json
import re
from pathlib import Path, PurePosixPath
from typing import Optional

try:
    from .check_conformance_requirements import validate_requirements
    from .hwr_benchmark import (
        prepare_case_context,
        validate_benchmark_case,
        validate_benchmark_plan,
    )
    from .hwr_registry_index import (
        build_generated_registry_index,
        check_generated_registry_index,
    )
    from .hwr_release import validate_checked_in_release
    from .hwr_reviewed_examples import validate_checked_in_reviewed_examples
    from .hwr_visual_benchmarks import validate_checked_in_visual_benchmarks
    from .hwr_reference import (
        HwrError,
        apply_artifact_record,
        apply_content_design,
        apply_review_record,
        build_adapter_packet,
        build_run_plan,
        finalize_run,
        load_task_with_source_snapshots,
        load_repository,
        validate_run_record,
        validate_task_record,
    )
    from .run_conformance_fixtures import validate_fixture_suites
except ImportError:
    from check_conformance_requirements import validate_requirements
    from hwr_benchmark import (
        prepare_case_context,
        validate_benchmark_case,
        validate_benchmark_plan,
    )
    from hwr_registry_index import (
        build_generated_registry_index,
        check_generated_registry_index,
    )
    from hwr_release import validate_checked_in_release
    from hwr_reviewed_examples import validate_checked_in_reviewed_examples
    from hwr_visual_benchmarks import validate_checked_in_visual_benchmarks
    from hwr_reference import (
        HwrError,
        apply_artifact_record,
        apply_content_design,
        apply_review_record,
        build_adapter_packet,
        build_run_plan,
        finalize_run,
        load_task_with_source_snapshots,
        load_repository,
        validate_run_record,
        validate_task_record,
    )
    from run_conformance_fixtures import validate_fixture_suites


ROOT = Path(__file__).resolve().parents[1]
OBJECTS_PATH = ROOT / "registry/objects.json"
ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]+$")
RFC_ID_RE = re.compile(r"^RFC-[0-9]{4}$")
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
ALLOWED_KINDS = {
    "core",
    "principle",
    "rule",
    "language",
    "format",
    "topic",
    "platform",
    "tone",
    "skill",
    "reviewer",
    "benchmark",
    "example",
    "rfc",
}
ALLOWED_STATUSES = {"draft", "active", "deprecated"}
REQUIRED_REVIEWERS = {
    "reviewer.source",
    "reviewer.language",
    "reviewer.human-signals",
    "reviewer.editor",
}


def load_json(path: Path, errors: list[str]) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing JSON file: {path.relative_to(ROOT)}")
        return {}
    except json.JSONDecodeError as exc:
        errors.append(
            f"invalid JSON in {path.relative_to(ROOT)}:{exc.lineno}:{exc.colno}: {exc.msg}"
        )
        return {}
    if not isinstance(value, dict):
        errors.append(f"JSON root must be an object: {path.relative_to(ROOT)}")
        return {}
    return value


def parse_frontmatter(path: Path, errors: list[str]) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        errors.append(f"missing frontmatter: {path.relative_to(ROOT)}")
        return {}
    try:
        end = lines.index("---", 1)
    except ValueError:
        errors.append(f"unterminated frontmatter: {path.relative_to(ROOT)}")
        return {}

    metadata: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, separator, value = line.partition(":")
        if not separator:
            errors.append(f"invalid frontmatter line in {path.relative_to(ROOT)}: {line}")
            continue
        metadata[key.strip()] = value.strip().strip("\"'")
    return metadata


def validate_objects(errors: list[str]) -> tuple[dict[str, dict], list[dict]]:
    data = load_json(OBJECTS_PATH, errors)
    objects = data.get("objects", [])
    if not isinstance(objects, list):
        errors.append("registry/objects.json: objects must be an array")
        return {}, []

    by_id: dict[str, dict] = {}
    paths: dict[str, str] = {}
    required_fields = {"id", "kind", "title", "status", "path"}
    list_fields = {"tags", "languages", "platforms", "formats", "topics", "requires"}

    for index, obj in enumerate(objects):
        label = f"registry/objects.json objects[{index}]"
        if not isinstance(obj, dict):
            errors.append(f"{label} must be an object")
            continue

        missing = required_fields - obj.keys()
        if missing:
            errors.append(f"{label} missing fields: {', '.join(sorted(missing))}")
            continue

        object_id = obj["id"]
        if not isinstance(object_id, str) or not ID_RE.fullmatch(object_id):
            errors.append(f"invalid object id: {object_id!r}")
            continue
        if object_id in by_id:
            errors.append(f"duplicate object id: {object_id}")
            continue
        by_id[object_id] = obj

        if obj["kind"] not in ALLOWED_KINDS:
            errors.append(f"{object_id} has unknown kind: {obj['kind']}")
        if obj["status"] not in ALLOWED_STATUSES:
            errors.append(f"{object_id} has unknown status: {obj['status']}")
        if not isinstance(obj["title"], str) or not obj["title"].strip():
            errors.append(f"{object_id} has an empty title")

        for field in list_fields:
            value = obj.get(field, [])
            if not isinstance(value, list) or not all(
                isinstance(item, str) and item for item in value
            ):
                errors.append(f"{object_id}.{field} must be an array of non-empty strings")

        relative_path = obj["path"]
        if not isinstance(relative_path, str):
            errors.append(f"{object_id}.path must be a string")
            continue
        pure_path = PurePosixPath(relative_path)
        if pure_path.is_absolute() or ".." in pure_path.parts:
            errors.append(f"{object_id} has unsafe path: {relative_path}")
            continue
        if relative_path in paths:
            errors.append(
                f"duplicate object path: {relative_path} ({paths[relative_path]}, {object_id})"
            )
        paths[relative_path] = object_id

        object_path = ROOT / relative_path
        if not object_path.is_file():
            errors.append(f"missing object path: {relative_path}")
            continue
        metadata = parse_frontmatter(object_path, errors)
        for field in ("id", "kind", "status"):
            if metadata.get(field) != obj[field]:
                errors.append(
                    f"{object_id} frontmatter {field}={metadata.get(field)!r}, "
                    f"registry has {obj[field]!r}"
                )

    for object_id, obj in by_id.items():
        for dependency in obj.get("requires", []):
            if dependency == object_id:
                errors.append(f"{object_id} requires itself")
            elif dependency not in by_id:
                errors.append(f"{object_id} requires unknown object {dependency}")

    validate_dependency_cycles(by_id, errors)
    validate_runtime_coverage(paths, errors)
    return by_id, objects


def validate_dependency_cycles(by_id: dict[str, dict], errors: list[str]) -> None:
    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(object_id: str) -> None:
        status = state.get(object_id, 0)
        if status == 2:
            return
        if status == 1:
            start = stack.index(object_id)
            cycle = stack[start:] + [object_id]
            errors.append(f"dependency cycle: {' -> '.join(cycle)}")
            return
        state[object_id] = 1
        stack.append(object_id)
        for dependency in by_id[object_id].get("requires", []):
            if dependency in by_id:
                visit(dependency)
        stack.pop()
        state[object_id] = 2

    for object_id in by_id:
        visit(object_id)


def validate_runtime_coverage(paths: dict[str, str], errors: list[str]) -> None:
    patterns = (
        "core/*.md",
        "principles/*.md",
        "rules/**/*.md",
        "skills/*/SKILL.md",
        "reviewers/*.md",
    )
    runtime_files: set[str] = set()
    for pattern in patterns:
        runtime_files.update(
            path.relative_to(ROOT).as_posix() for path in ROOT.glob(pattern) if path.is_file()
        )
    unregistered = sorted(runtime_files - paths.keys())
    for path in unregistered:
        errors.append(f"unregistered runtime module: {path}")


def validate_index(
    filename: str,
    collection_key: str,
    expected_kind: str,
    by_id: dict[str, dict],
    errors: list[str],
    selector_field: Optional[str] = None,
) -> tuple[set[str], dict[str, dict]]:
    path = ROOT / "registry" / filename
    data = load_json(path, errors)
    entries = data.get(collection_key, [])
    if not isinstance(entries, list):
        errors.append(f"registry/{filename}: {collection_key} must be an array")
        return set(), {}

    ids: set[str] = set()
    by_value: dict[str, dict] = {}
    modules: set[str] = set()
    for index, entry in enumerate(entries):
        label = f"registry/{filename} {collection_key}[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label} must be an object")
            continue
        value = entry.get("id")
        module = entry.get("module")
        if not isinstance(value, str) or not value:
            errors.append(f"{label} has invalid id")
            continue
        if value in ids:
            errors.append(f"duplicate {collection_key} id: {value}")
        ids.add(value)
        by_value[value] = entry

        if not isinstance(module, str) or not module:
            errors.append(f"{label} has invalid module")
            continue
        if module in modules:
            errors.append(f"duplicate {collection_key} module: {module}")
        modules.add(module)
        obj = by_id.get(module)
        if obj is None:
            errors.append(f"{label} references unknown module {module}")
        elif obj["kind"] != expected_kind:
            errors.append(
                f"{label} module {module} has kind {obj['kind']}, expected {expected_kind}"
            )
        elif selector_field and value not in obj.get(selector_field, []):
            errors.append(
                f"{label} id {value} is absent from {module}.{selector_field}"
            )

    return ids, by_value


def validate_indexes(by_id: dict[str, dict], errors: list[str]) -> dict[str, set[str]]:
    languages, _ = validate_index(
        "languages.json", "languages", "language", by_id, errors, "languages"
    )
    formats, _ = validate_index(
        "formats.json", "formats", "format", by_id, errors, "formats"
    )
    topics, _ = validate_index(
        "topics.json", "topics", "topic", by_id, errors, "topics"
    )
    tones, _ = validate_index("tones.json", "tones", "tone", by_id, errors)
    skills, _ = validate_index("skills.json", "skills", "skill", by_id, errors)
    platforms, platform_entries = validate_index(
        "platforms.json", "platforms", "platform", by_id, errors, "platforms"
    )

    topics_data = load_json(ROOT / "registry/topics.json", errors)
    if topics_data.get("fallback") not in topics:
        errors.append(
            f"registry/topics.json has unknown fallback: {topics_data.get('fallback')!r}"
        )

    for platform_id, entry in platform_entries.items():
        default_format = entry.get("default_format")
        if default_format not in formats:
            errors.append(
                f"platform {platform_id} has unknown default_format {default_format!r}"
            )
            continue
        module = by_id.get(entry.get("module"), {})
        applicable_formats = module.get("formats", [])
        if applicable_formats and default_format not in applicable_formats:
            errors.append(
                f"platform {platform_id} default_format {default_format} "
                f"is absent from {module.get('id')}.formats"
            )

    return {
        "languages": languages,
        "formats": formats,
        "topics": topics,
        "tones": tones,
        "skills": skills,
        "platforms": platforms,
    }


def validate_starter_config(
    by_id: dict[str, dict],
    indexes: dict[str, set[str]],
    spec_revision: str,
    errors: list[str],
) -> None:
    config = load_json(ROOT / "starter-kit/.human-writing-rules/config.json", errors)
    for field in ("version", "spec_revision", "language", "content_type"):
        if field not in config:
            errors.append(f"starter config missing required field: {field}")
    if spec_revision and config.get("spec_revision") != spec_revision:
        errors.append(
            "starter config spec_revision "
            f"{config.get('spec_revision')!r} does not match RFC index {spec_revision!r}"
        )

    references = (
        ("language", "languages"),
        ("content_type", "formats"),
        ("topic", "topics"),
        ("platform", "platforms"),
        ("tone", "tones"),
    )
    for field, index_name in references:
        value = config.get(field)
        if value is not None and value not in indexes[index_name]:
            errors.append(f"starter config {field} references unknown value: {value}")

    skill = config.get("skill")
    if skill is not None and skill not in indexes["skills"]:
        errors.append(f"starter config references unknown skill: {skill}")

    reviewers = config.get("reviewers", [])
    if not isinstance(reviewers, list):
        errors.append("starter config reviewers must be an array")
        reviewers = []
    if len(reviewers) != len(set(reviewers)):
        errors.append("starter config reviewers contains duplicates")
    for reviewer in reviewers:
        if reviewer not in by_id or by_id[reviewer]["kind"] != "reviewer":
            errors.append(f"starter config references unknown reviewer: {reviewer}")
    missing_reviewers = REQUIRED_REVIEWERS - set(reviewers)
    if missing_reviewers:
        errors.append(
            "starter config missing required reviewers: "
            + ", ".join(sorted(missing_reviewers))
        )

    if config.get("content_type") and "reviewer.format" not in reviewers:
        errors.append("starter config must include reviewer.format")
    if config.get("topic") and "reviewer.topic" not in reviewers:
        errors.append("starter config must include reviewer.topic")
    if config.get("platform") and "reviewer.platform" not in reviewers:
        errors.append("starter config must include reviewer.platform")

    visuals = config.get("visuals", {})
    visual_mode = visuals.get("mode") if isinstance(visuals, dict) else None
    if visual_mode not in {"none", "auto", "required"}:
        errors.append("starter config visuals.mode must be none, auto, or required")
    if visual_mode in {"auto", "required"} and "reviewer.visual" not in reviewers:
        errors.append(
            "starter config must include reviewer.visual for auto or required visuals"
        )

    if config.get("risk_level") not in {"low", "medium", "high"}:
        errors.append("starter config risk_level must be low, medium, or high")
    if config.get("author_perspective") not in {
        "editorial",
        "first-person",
        "expert",
        "reporter",
        "neutral",
    }:
        errors.append("starter config has unknown author_perspective")

    max_count = visuals.get("max_count") if isinstance(visuals, dict) else None
    if not isinstance(max_count, int) or isinstance(max_count, bool) or max_count < 0:
        errors.append("starter config visuals.max_count must be a non-negative integer")


def validate_reference_runner(errors: list[str]) -> tuple[int, int, int, int]:
    try:
        repository = load_repository(ROOT)
    except HwrError as exc:
        errors.append(f"reference runner repository load failed: {exc.message}")
        errors.extend(f"reference runner: {detail}" for detail in exc.details)
        return 0, 0, 0, 0

    try:
        check_generated_registry_index(
            ROOT / "registry/generated-index.json",
            build_generated_registry_index(repository),
        )
    except HwrError as exc:
        errors.append(f"generated registry index failed [{exc.code}]: {exc.message}")
        errors.extend(
            f"generated registry index: {detail}" for detail in exc.details
        )

    config = load_json(ROOT / "starter-kit/.human-writing-rules/config.json", errors)
    if config.get("registry_revision") != repository["registry_revision"]:
        errors.append(
            "starter config registry_revision "
            f"{config.get('registry_revision')!r} does not match "
            f"{repository['registry_revision']!r}"
        )

    task_count = 0
    ready_count = 0
    blocked_count = 0
    for task_path in sorted((ROOT / "examples/tasks").glob("*.json")):
        task_count += 1
        task = load_json(task_path, errors)
        task_errors = validate_task_record(task)
        if task_errors:
            errors.extend(
                f"{task_path.relative_to(ROOT)}: {message}"
                for message in task_errors
            )
            continue
        try:
            run = build_run_plan(repository, config, task)
        except HwrError as exc:
            errors.append(
                f"{task_path.relative_to(ROOT)}: runner failed "
                f"[{exc.code}] {exc.message}"
            )
            errors.extend(
                f"{task_path.relative_to(ROOT)}: {detail}"
                for detail in exc.details
            )
            continue
        run_errors = validate_run_record(repository, run)
        errors.extend(
            f"{task_path.relative_to(ROOT)} run: {message}"
            for message in run_errors
        )
        if run.get("state") == "blocked":
            blocked_count += 1
        elif run.get("state") == "context-ready":
            ready_count += 1

    if task_count == 0:
        errors.append("reference runner requires at least one example task")
    if ready_count == 0:
        errors.append("reference runner requires a context-ready example task")
    if blocked_count == 0:
        errors.append("reference runner requires a blocked example task")

    snapshot_task_path = ROOT / "examples/source-snapshots/task.json"
    try:
        snapshot_task = load_task_with_source_snapshots(snapshot_task_path)
        snapshot_run = build_run_plan(repository, config, snapshot_task)
        snapshot_packet = build_adapter_packet(repository, snapshot_run, "design")
    except HwrError as exc:
        errors.append(
            f"source snapshot example failed [{exc.code}]: {exc.message}"
        )
        errors.extend(f"source snapshot example: {detail}" for detail in exc.details)
    else:
        snapshot_content = (
            snapshot_packet.get("sources", [{}])[0]
            .get("snapshot", {})
            .get("content")
        )
        if not isinstance(snapshot_content, str) or not snapshot_content:
            errors.append("source snapshot example did not reach the adapter packet")

    lifecycle_count = 0
    lifecycle_task = load_json(
        ROOT / "examples/tasks/ru-science-article.json",
        errors,
    )
    transition_paths = {
        "design": ROOT / "examples/transitions/ru-science-design.json",
        "draft": ROOT / "examples/transitions/ru-science-draft.json",
        "edit": ROOT / "examples/transitions/ru-science-edit.json",
        "review": ROOT / "examples/transitions/ru-science-review.json",
    }
    transitions = {
        name: load_json(path, errors) for name, path in transition_paths.items()
    }
    try:
        lifecycle = build_run_plan(repository, config, lifecycle_task)
        build_adapter_packet(repository, lifecycle, "design")
        lifecycle = apply_content_design(
            repository,
            lifecycle,
            transitions["design"],
        )
        build_adapter_packet(repository, lifecycle, "draft")
        lifecycle = apply_artifact_record(
            repository,
            lifecycle,
            transitions["draft"],
        )
        build_adapter_packet(repository, lifecycle, "edit")
        lifecycle = apply_artifact_record(
            repository,
            lifecycle,
            transitions["edit"],
        )
        build_adapter_packet(repository, lifecycle, "review")
        lifecycle = apply_review_record(
            repository,
            lifecycle,
            transitions["review"],
        )
        lifecycle = finalize_run(repository, lifecycle)
    except HwrError as exc:
        errors.append(
            f"reference lifecycle fixture failed [{exc.code}]: {exc.message}"
        )
        errors.extend(f"reference lifecycle: {detail}" for detail in exc.details)
    else:
        run_errors = validate_run_record(repository, lifecycle)
        errors.extend(
            f"reference lifecycle final run: {message}"
            for message in run_errors
        )
        if lifecycle.get("state") != "ready":
            errors.append("reference lifecycle fixture did not reach ready")
        elif not run_errors:
            lifecycle_count = 1

    return task_count, ready_count, blocked_count, lifecycle_count


def validate_benchmarks(
    by_id: dict[str, dict],
    indexes: dict[str, set[str]],
    spec_revision: str,
    errors: list[str],
) -> tuple[int, int]:
    benchmark_ids: set[str] = set()
    count = 0
    try:
        repository = load_repository(ROOT)
    except HwrError as exc:
        errors.append(f"benchmark repository load failed [{exc.code}]: {exc.message}")
        repository = None
    for path in sorted((ROOT / "benchmarks/cases").glob("*.json")):
        case = load_json(path, errors)
        label = path.relative_to(ROOT).as_posix()
        count += 1
        case_errors = validate_benchmark_case(case)
        errors.extend(f"{label}: {message}" for message in case_errors)

        benchmark_id = case.get("id")
        if not isinstance(benchmark_id, str) or not benchmark_id:
            errors.append(f"{label} has invalid id")
        elif benchmark_id in benchmark_ids:
            errors.append(f"duplicate benchmark id: {benchmark_id}")
        else:
            benchmark_ids.add(benchmark_id)
        if spec_revision and case.get("spec_revision") != spec_revision:
            errors.append(
                f"{label} spec_revision {case.get('spec_revision')!r} "
                f"does not match RFC index {spec_revision!r}"
            )

        references = (
            ("language", "languages"),
            ("content_type", "formats"),
            ("topic", "topics"),
            ("platform", "platforms"),
        )
        for field, index_name in references:
            value = case.get(field)
            if value not in indexes[index_name]:
                errors.append(f"{label} {field} references unknown value: {value!r}")

        skill = case.get("skill")
        if skill is not None and skill not in indexes["skills"]:
            errors.append(f"{label} references unknown skill: {skill}")

        for module in case.get("required_modules", []):
            if module not in by_id:
                errors.append(f"{label} references unknown required module: {module}")

        reviewers = case.get("required_reviewers", [])
        if not isinstance(reviewers, list):
            errors.append(f"{label} required_reviewers must be an array")
            reviewers = []
        for reviewer in reviewers:
            if reviewer not in by_id or by_id[reviewer]["kind"] != "reviewer":
                errors.append(f"{label} references unknown reviewer: {reviewer}")
        missing = REQUIRED_REVIEWERS - set(reviewers)
        if missing:
            errors.append(
                f"{label} missing required reviewers: {', '.join(sorted(missing))}"
            )
        if case.get("content_type") and "reviewer.format" not in reviewers:
            errors.append(f"{label} must include reviewer.format")
        if case.get("topic") and "reviewer.topic" not in reviewers:
            errors.append(f"{label} must include reviewer.topic")
        if case.get("platform") and "reviewer.platform" not in reviewers:
            errors.append(f"{label} must include reviewer.platform")

        visuals = case.get("visuals", {})
        visual_mode = visuals.get("mode") if isinstance(visuals, dict) else None
        if visual_mode not in {"none", "auto", "required"}:
            errors.append(f"{label} has invalid visuals.mode")
        if visual_mode in {"auto", "required"} and "reviewer.visual" not in reviewers:
            errors.append(f"{label} must include reviewer.visual")

        if repository is not None and not case_errors:
            try:
                prepare_case_context(repository, case)
            except HwrError as exc:
                errors.append(
                    f"{label} is not runnable [{exc.code}]: {exc.message}"
                )
                errors.extend(f"{label}: {detail}" for detail in exc.details)

    plan_count = 0
    for path in sorted((ROOT / "benchmarks/plans").glob("*.json")):
        plan_count += 1
        plan = load_json(path, errors)
        label = path.relative_to(ROOT).as_posix()
        plan_errors = validate_benchmark_plan(plan)
        errors.extend(f"{label}: {message}" for message in plan_errors)
        case_path = plan.get("case_path")
        if isinstance(case_path, str):
            pure_path = PurePosixPath(case_path)
            if pure_path.is_absolute() or ".." in pure_path.parts:
                errors.append(f"{label} has unsafe case_path: {case_path}")
            elif not (ROOT / pure_path).is_file():
                errors.append(f"{label} references missing case: {case_path}")
    if plan_count == 0:
        errors.append("benchmark runner requires at least one execution plan")
    return count, plan_count


def validate_rfcs(errors: list[str]) -> tuple[int, int, str]:
    data = load_json(ROOT / "registry/rfcs.json", errors)
    entries = data.get("rfcs", [])
    if not isinstance(entries, list):
        errors.append("registry/rfcs.json: rfcs must be an array")
        return 0, 0, ""
    if not isinstance(data.get("profile"), str) or not data.get("profile"):
        errors.append("registry/rfcs.json: profile must be a non-empty string")

    allowed_statuses = {"draft", "active", "deprecated", "superseded", "withdrawn"}
    by_id: dict[str, dict] = {}
    paths: dict[str, str] = {}
    required = {"id", "title", "status", "revision", "path", "depends_on"}

    for index, entry in enumerate(entries):
        label = f"registry/rfcs.json rfcs[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label} must be an object")
            continue
        missing = required - entry.keys()
        if missing:
            errors.append(f"{label} missing fields: {', '.join(sorted(missing))}")
            continue

        rfc_id = entry["id"]
        if not isinstance(rfc_id, str) or not RFC_ID_RE.fullmatch(rfc_id):
            errors.append(f"{label} has invalid id: {rfc_id!r}")
            continue
        if rfc_id in by_id:
            errors.append(f"duplicate RFC id: {rfc_id}")
            continue
        by_id[rfc_id] = entry

        if entry["status"] not in allowed_statuses:
            errors.append(f"{rfc_id} has unknown RFC status: {entry['status']}")
        if not isinstance(entry["title"], str) or not entry["title"].strip():
            errors.append(f"{rfc_id} has an empty title")
        if not isinstance(entry["revision"], str) or not entry["revision"].strip():
            errors.append(f"{rfc_id} has an invalid revision")
        if not isinstance(entry["depends_on"], list) or not all(
            isinstance(item, str) and RFC_ID_RE.fullmatch(item)
            for item in entry["depends_on"]
        ):
            errors.append(f"{rfc_id}.depends_on must contain RFC IDs")

        relative_path = entry["path"]
        if not isinstance(relative_path, str):
            errors.append(f"{rfc_id}.path must be a string")
            continue
        pure_path = PurePosixPath(relative_path)
        if pure_path.is_absolute() or ".." in pure_path.parts:
            errors.append(f"{rfc_id} has unsafe path: {relative_path}")
            continue
        if relative_path in paths:
            errors.append(
                f"duplicate RFC path: {relative_path} ({paths[relative_path]}, {rfc_id})"
            )
        paths[relative_path] = rfc_id

        path = ROOT / relative_path
        if not path.is_file():
            errors.append(f"missing RFC path: {relative_path}")
            continue
        metadata = parse_frontmatter(path, errors)
        for field in ("id", "status", "revision"):
            if metadata.get(field) != entry[field]:
                errors.append(
                    f"{rfc_id} frontmatter {field}={metadata.get(field)!r}, "
                    f"index has {entry[field]!r}"
                )
        if metadata.get("normative") != "true":
            errors.append(f"{rfc_id} frontmatter normative must be true")
        frontmatter_dependencies = [
            item.strip()
            for item in metadata.get("depends_on", "").split(",")
            if item.strip()
        ]
        if frontmatter_dependencies != entry["depends_on"]:
            errors.append(
                f"{rfc_id} frontmatter depends_on={frontmatter_dependencies!r}, "
                f"index has {entry['depends_on']!r}"
            )
        text = path.read_text(encoding="utf-8")
        if "\n## Abstract\n" not in text:
            errors.append(f"{rfc_id} is missing an Abstract section")
        if "\n## Conformance" not in text:
            errors.append(f"{rfc_id} is missing a Conformance section")
        if "MUST" not in text:
            errors.append(f"{rfc_id} contains no normative MUST requirement")

    for rfc_id, entry in by_id.items():
        for dependency in entry.get("depends_on", []):
            if dependency == rfc_id:
                errors.append(f"{rfc_id} depends on itself")
            elif dependency not in by_id:
                errors.append(f"{rfc_id} depends on unknown RFC {dependency}")

    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(rfc_id: str) -> None:
        status = state.get(rfc_id, 0)
        if status == 2:
            return
        if status == 1:
            start = stack.index(rfc_id)
            errors.append(
                f"RFC dependency cycle: {' -> '.join(stack[start:] + [rfc_id])}"
            )
            return
        state[rfc_id] = 1
        stack.append(rfc_id)
        for dependency in by_id[rfc_id].get("depends_on", []):
            if dependency in by_id:
                visit(dependency)
        stack.pop()
        state[rfc_id] = 2

    for rfc_id in by_id:
        visit(rfc_id)

    indexed_paths = set(paths)
    actual_paths = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "rfcs").glob("RFC-*.md")
        if path.is_file()
    }
    for path in sorted(actual_paths - indexed_paths):
        errors.append(f"unindexed normative RFC: {path}")
    for path in sorted(indexed_paths - actual_paths):
        errors.append(f"RFC index path does not match a normative RFC file: {path}")

    edge_count = sum(len(entry.get("depends_on", [])) for entry in entries)
    return len(entries), edge_count, str(data.get("version", ""))


def validate_markdown_links(errors: list[str]) -> int:
    checked = 0
    for path in sorted(ROOT.rglob("*.md")):
        relative_source = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK_RE.finditer(text):
            target = match.group(1).strip()
            if (
                not target
                or target.startswith(("#", "http://", "https://", "mailto:"))
                or "://" in target
            ):
                continue
            target = target.split("#", 1)[0]
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            candidate = (path.parent / target).resolve()
            checked += 1
            try:
                candidate.relative_to(ROOT.resolve())
            except ValueError:
                errors.append(
                    f"Markdown link escapes repository: {relative_source} -> {target}"
                )
                continue
            if not candidate.exists():
                errors.append(f"broken Markdown link: {relative_source} -> {target}")
    return checked


def main() -> None:
    errors: list[str] = []
    for json_file in (
        "package.json",
        "schemas/object.schema.json",
        "schemas/config.schema.json",
        "schemas/task-record.schema.json",
        "schemas/source-snapshot.schema.json",
        "schemas/generated-registry-index.schema.json",
        "schemas/benchmark-case.schema.json",
        "schemas/benchmark-plan.schema.json",
        "schemas/benchmark-arm-result.schema.json",
        "schemas/benchmark-run-record.schema.json",
        "schemas/release-manifest.schema.json",
        "schemas/stability-review.schema.json",
        "schemas/reviewed-example-catalog.schema.json",
        "schemas/visual-benchmark-fixture.schema.json",
        "schemas/visual-acceptance-record.schema.json",
        "schemas/run-record.schema.json",
        "schemas/content-design.schema.json",
        "schemas/artifact-record.schema.json",
        "schemas/visual-assets-record.schema.json",
        "schemas/review-report.schema.json",
        "schemas/adapter-packet.schema.json",
        "schemas/workflow-record.schema.json",
        "schemas/conformance-fixture.schema.json",
        "schemas/conformance-requirements.schema.json",
    ):
        load_json(ROOT / json_file, errors)

    by_id, objects = validate_objects(errors)
    indexes = validate_indexes(by_id, errors)
    rfc_count, rfc_edge_count, spec_revision = validate_rfcs(errors)
    (
        requirement_count,
        requirement_must_count,
        requirement_must_not_count,
        requirement_should_count,
        requirement_should_not_count,
        verified_requirement_count,
        retired_requirement_count,
    ) = validate_requirements(ROOT, errors)
    _, conformance_fixture_count = validate_fixture_suites(ROOT, errors)
    validate_starter_config(by_id, indexes, spec_revision, errors)
    (
        runner_task_count,
        runner_ready_count,
        runner_blocked_count,
        runner_lifecycle_count,
    ) = (
        validate_reference_runner(errors)
    )
    benchmark_count, benchmark_plan_count = validate_benchmarks(
        by_id,
        indexes,
        spec_revision,
        errors,
    )
    visual_benchmark_summary, visual_benchmark_errors = (
        validate_checked_in_visual_benchmarks(ROOT)
    )
    errors.extend(visual_benchmark_errors)
    reviewed_example_summary, reviewed_example_errors = (
        validate_checked_in_reviewed_examples(ROOT)
    )
    errors.extend(reviewed_example_errors)
    release_summary, release_errors = validate_checked_in_release(ROOT)
    errors.extend(release_errors)
    link_count = validate_markdown_links(errors)

    if errors:
        raise SystemExit("\n".join(errors))

    edge_count = sum(len(obj.get("requires", [])) for obj in objects)
    print(
        "OK: "
        f"{len(objects)} objects, "
        f"{edge_count} dependencies, "
        f"{len(indexes['formats'])} formats, "
        f"{len(indexes['topics'])} topics, "
        f"{len(indexes['platforms'])} platforms, "
        f"{len(indexes['skills'])} skills, "
        f"{rfc_count} RFCs/{rfc_edge_count} RFC dependencies, "
        f"{requirement_count} requirements "
        f"({requirement_must_count} MUST/"
        f"{requirement_must_not_count} MUST NOT, "
        f"{requirement_should_count} SHOULD/"
        f"{requirement_should_not_count} SHOULD NOT, "
        f"{verified_requirement_count} verified/"
        f"{retired_requirement_count} retired), "
        f"{conformance_fixture_count} conformance fixtures, "
        f"{runner_task_count} runner tasks "
        f"({runner_ready_count} context-ready/{runner_blocked_count} blocked), "
        f"{runner_lifecycle_count} ready lifecycle, "
        f"{benchmark_count} benchmark cases/{benchmark_plan_count} plans, "
        f"{visual_benchmark_summary['fixtures']} visual fixtures "
        f"({visual_benchmark_summary['passed']} pass/"
        f"{visual_benchmark_summary['failed']} expected fail, "
        f"{visual_benchmark_summary['assets_checked']} assets checked), "
        f"{reviewed_example_summary['examples']} reviewed examples "
        f"({reviewed_example_summary['topics_covered']} topics/"
        f"{reviewed_example_summary['platforms_covered']} platforms), "
        f"release {release_summary.get('release')} "
        f"({release_summary.get('status')}/{release_summary.get('gates')} gates), "
        f"{link_count} local Markdown links"
    )


if __name__ == "__main__":
    main()
