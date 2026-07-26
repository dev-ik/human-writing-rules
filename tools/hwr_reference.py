#!/usr/bin/env python3
"""Vendor-neutral reference orchestration for Human Writing Rules."""

import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Optional


SPEC_SCHEMA_VERSION = "1.0"
ALLOWED_PERSPECTIVES = {
    "editorial",
    "first-person",
    "expert",
    "reporter",
    "neutral",
}
ALLOWED_RISK_LEVELS = {"low", "medium", "high"}
ALLOWED_VISUAL_MODES = {"none", "auto", "required"}
ALLOWED_CLAIM_CLASSIFICATIONS = {
    "verified-fact",
    "source-claim",
    "opinion",
    "inference",
    "assumption",
    "unknown",
}
ALLOWED_CLAIM_DISPOSITIONS = {
    "use",
    "narrow",
    "attribute",
    "research",
    "omit",
}
ALLOWED_ASSESSMENTS = {
    "source_freshness": {"adequate", "inadequate", "unknown", "not-applicable"},
    "platform_constraints": {"known", "unknown", "not-applicable"},
    "perspective": {"authorized", "unauthorized", "unknown", "not-applicable"},
    "rights": {"cleared", "blocked", "unknown", "not-applicable"},
}
ALLOWED_RUN_STATES = {
    "blocked",
    "context-ready",
    "media-decided",
    "drafted",
    "edited",
    "reviewed",
    "revising",
    "ready",
}
ALLOWED_ARTIFACT_STAGES = {"draft", "edit", "revision"}
ALLOWED_REVIEW_STATUSES = {"pass", "fail", "input-error"}
ALLOWED_FINDING_SEVERITIES = {"blocker", "major", "minor", "note"}
ALLOWED_FINDING_STATUSES = {
    "open",
    "fixed",
    "withdrawn",
    "deferred",
    "accepted-risk",
}
MATERIAL_FINDING_STATUSES = {"open", "deferred", "accepted-risk"}
ALLOWED_READINESS_CANDIDATES = {
    "publication-ready",
    "ready-with-minor-findings",
    "not-ready",
    "input-failure",
}
REQUIRED_ROOTS = [
    "core.writing-pipeline",
    "core.content-model",
    "core.context-selection",
    "rule.source-integrity",
    "rule.human-signals.core",
    "reviewer.source",
    "reviewer.language",
    "reviewer.human-signals",
    "reviewer.editor",
]
REVIEW_ORDER = [
    "reviewer.source",
    "reviewer.topic",
    "reviewer.format",
    "reviewer.language",
    "reviewer.human-signals",
    "reviewer.platform",
    "reviewer.visual",
    "reviewer.editor",
]
REGISTRY_FILES = [
    "objects.json",
    "languages.json",
    "formats.json",
    "topics.json",
    "platforms.json",
    "skills.json",
    "tones.json",
    "rfcs.json",
]
SOURCE_SNAPSHOT_SCHEMA = (
    "https://human-writing-rules.example/schemas/source-snapshot.schema.json"
)
SOURCE_SNAPSHOT_VERSION = "1.0"
MAX_SOURCE_SNAPSHOT_BYTES = 2 * 1024 * 1024
MAX_SOURCE_SNAPSHOT_DOCUMENT_BYTES = MAX_SOURCE_SNAPSHOT_BYTES + 256 * 1024
MAX_SOURCE_SNAPSHOT_TOTAL_BYTES = 8 * 1024 * 1024
ALLOWED_SOURCE_MEDIA_TYPES = {
    "application/json",
    "application/xml",
    "text/csv",
    "text/html",
    "text/markdown",
    "text/plain",
}


class HwrError(Exception):
    """A stable CLI-facing error."""

    def __init__(
        self,
        code: str,
        message: str,
        details: Optional[list[object]] = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or []


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise HwrError(
            "FILE_NOT_FOUND",
            f"JSON file does not exist: {path}",
            [str(path)],
        ) from exc
    except json.JSONDecodeError as exc:
        raise HwrError(
            "INVALID_JSON",
            f"Invalid JSON in {path}:{exc.lineno}:{exc.colno}: {exc.msg}",
            [{"path": str(path), "line": exc.lineno, "column": exc.colno}],
        ) from exc
    if not isinstance(value, dict):
        raise HwrError("INVALID_JSON_ROOT", f"JSON root must be an object: {path}")
    return value


def safe_relative_path(root: Path, value: str, label: str) -> Path:
    pure_path = PurePosixPath(value)
    if pure_path.is_absolute() or ".." in pure_path.parts:
        raise HwrError("UNSAFE_PATH", f"{label} contains an unsafe path: {value}")
    return root / pure_path


def resolve_source_path(root: Path, value: str, label: str) -> Path:
    if not isinstance(value, str) or not value.strip():
        raise HwrError("UNSAFE_SOURCE_PATH", f"{label} must be a relative path")
    pure_path = PurePosixPath(value)
    if pure_path.is_absolute() or ".." in pure_path.parts:
        raise HwrError(
            "UNSAFE_SOURCE_PATH",
            f"{label} must remain inside the source root: {value}",
        )
    try:
        resolved_root = root.expanduser().resolve(strict=True)
    except FileNotFoundError as exc:
        raise HwrError(
            "SOURCE_ROOT_NOT_FOUND",
            f"Source root does not exist: {root}",
        ) from exc
    if not resolved_root.is_dir():
        raise HwrError(
            "SOURCE_ROOT_INVALID",
            f"Source root is not a directory: {resolved_root}",
        )
    try:
        resolved_path = (resolved_root / pure_path).resolve(strict=True)
    except FileNotFoundError as exc:
        raise HwrError(
            "SOURCE_FILE_NOT_FOUND",
            f"{label} does not exist inside the source root: {value}",
        ) from exc
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise HwrError(
            "UNSAFE_SOURCE_PATH",
            f"{label} resolves outside the source root: {value}",
        ) from exc
    if not resolved_path.is_file():
        raise HwrError(
            "SOURCE_FILE_INVALID",
            f"{label} is not a regular file: {value}",
        )
    return resolved_path


def validate_source_snapshot(
    snapshot: object,
    *,
    expected_source_id: Optional[str] = None,
) -> list[str]:
    if not isinstance(snapshot, dict):
        return ["snapshot must be an object"]

    errors: list[str] = []
    allowed_fields = {
        "$schema",
        "schema_version",
        "snapshot_id",
        "source_id",
        "media_type",
        "origin",
        "captured_at",
        "sha256",
        "bytes",
        "content",
        "rights",
        "notes",
    }
    extra_fields = sorted(set(snapshot) - allowed_fields)
    if extra_fields:
        errors.append(
            "snapshot contains unknown fields: " + ", ".join(extra_fields)
        )
    if snapshot.get("$schema", SOURCE_SNAPSHOT_SCHEMA) != SOURCE_SNAPSHOT_SCHEMA:
        errors.append("snapshot $schema is not the source-snapshot schema")
    if snapshot.get("schema_version") != SOURCE_SNAPSHOT_VERSION:
        errors.append(
            f"snapshot schema_version must be {SOURCE_SNAPSHOT_VERSION!r}"
        )
    for field in ("snapshot_id", "source_id", "media_type", "sha256", "content"):
        if not isinstance(snapshot.get(field), str):
            errors.append(f"snapshot {field} must be a string")
    for field in ("snapshot_id", "source_id"):
        value = snapshot.get(field)
        if isinstance(value, str) and not value.strip():
            errors.append(f"snapshot {field} must not be empty")

    source_id = snapshot.get("source_id")
    if expected_source_id is not None and source_id != expected_source_id:
        errors.append(
            f"snapshot source_id {source_id!r} does not match {expected_source_id!r}"
        )

    media_type = snapshot.get("media_type")
    if isinstance(media_type, str) and media_type not in ALLOWED_SOURCE_MEDIA_TYPES:
        errors.append(f"snapshot media_type is unsupported: {media_type!r}")

    origin = snapshot.get("origin")
    if not isinstance(origin, dict):
        errors.append("snapshot origin must be an object")
    else:
        if set(origin) - {"kind", "path"}:
            errors.append("snapshot origin contains unknown fields")
        if origin.get("kind") != "local-file":
            errors.append("snapshot origin.kind must be 'local-file'")
        origin_path = origin.get("path")
        if not isinstance(origin_path, str) or not origin_path.strip():
            errors.append("snapshot origin.path must be a non-empty relative path")
        else:
            pure_origin = PurePosixPath(origin_path)
            if pure_origin.is_absolute() or ".." in pure_origin.parts:
                errors.append("snapshot origin.path must be a safe relative path")

    captured_at = snapshot.get("captured_at")
    if captured_at is not None and (
        not isinstance(captured_at, str) or not captured_at.strip()
    ):
        errors.append("snapshot captured_at must be a non-empty string when present")
    for field in ("rights", "notes"):
        value = snapshot.get(field)
        if value is not None and not isinstance(value, str):
            errors.append(f"snapshot {field} must be a string when present")

    byte_count = snapshot.get("bytes")
    if (
        not isinstance(byte_count, int)
        or isinstance(byte_count, bool)
        or byte_count < 0
        or byte_count > MAX_SOURCE_SNAPSHOT_BYTES
    ):
        errors.append(
            "snapshot bytes must be an integer between 0 and "
            f"{MAX_SOURCE_SNAPSHOT_BYTES}"
        )

    content = snapshot.get("content")
    if isinstance(content, str):
        if "\x00" in content:
            errors.append("snapshot content must not contain NUL bytes")
        encoded = content.encode("utf-8")
        if len(encoded) > MAX_SOURCE_SNAPSHOT_BYTES:
            errors.append(
                f"snapshot content exceeds {MAX_SOURCE_SNAPSHOT_BYTES} bytes"
            )
        if isinstance(byte_count, int) and byte_count != len(encoded):
            errors.append("snapshot bytes does not match UTF-8 content length")
        expected_digest = f"sha256:{hashlib.sha256(encoded).hexdigest()}"
        if snapshot.get("sha256") != expected_digest:
            errors.append("snapshot sha256 does not match content")
    return errors


def create_source_snapshot(
    input_path: str,
    *,
    source_root: Path,
    source_id: str,
    snapshot_id: str,
    media_type: str,
    captured_at: Optional[str] = None,
    rights: Optional[str] = None,
    notes: Optional[str] = None,
) -> dict:
    if not isinstance(source_id, str) or not source_id.strip():
        raise HwrError("SOURCE_SNAPSHOT_INVALID", "source_id must not be empty")
    if not isinstance(snapshot_id, str) or not snapshot_id.strip():
        raise HwrError("SOURCE_SNAPSHOT_INVALID", "snapshot_id must not be empty")
    if media_type not in ALLOWED_SOURCE_MEDIA_TYPES:
        raise HwrError(
            "SOURCE_MEDIA_TYPE_UNSUPPORTED",
            f"Unsupported source media type: {media_type}",
            sorted(ALLOWED_SOURCE_MEDIA_TYPES),
        )

    source_file = resolve_source_path(source_root, input_path, "source input")
    try:
        with source_file.open("rb") as stream:
            payload = stream.read(MAX_SOURCE_SNAPSHOT_BYTES + 1)
    except OSError as exc:
        raise HwrError(
            "SOURCE_READ_FAILED",
            f"Source input could not be read: {input_path}",
            [{"error_type": type(exc).__name__}],
        ) from exc
    if len(payload) > MAX_SOURCE_SNAPSHOT_BYTES:
        raise HwrError(
            "SOURCE_TOO_LARGE",
            f"Source input exceeds {MAX_SOURCE_SNAPSHOT_BYTES} bytes",
            [{"bytes": len(payload), "limit": MAX_SOURCE_SNAPSHOT_BYTES}],
        )
    try:
        content = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HwrError(
            "SOURCE_ENCODING_INVALID",
            "Source input must be UTF-8 text",
            [{"start": exc.start, "end": exc.end}],
        ) from exc
    if "\x00" in content:
        raise HwrError(
            "SOURCE_ENCODING_INVALID",
            "Source input contains NUL bytes and is not accepted as text",
        )

    resolved_root = source_root.expanduser().resolve(strict=True)
    relative_origin = source_file.relative_to(resolved_root).as_posix()
    snapshot = {
        "$schema": SOURCE_SNAPSHOT_SCHEMA,
        "schema_version": SOURCE_SNAPSHOT_VERSION,
        "snapshot_id": snapshot_id,
        "source_id": source_id,
        "media_type": media_type,
        "origin": {
            "kind": "local-file",
            "path": relative_origin,
        },
        "sha256": f"sha256:{hashlib.sha256(payload).hexdigest()}",
        "bytes": len(payload),
        "content": content,
    }
    for field, value in (
        ("captured_at", captured_at),
        ("rights", rights),
        ("notes", notes),
    ):
        if value is not None:
            snapshot[field] = value
    errors = validate_source_snapshot(snapshot, expected_source_id=source_id)
    if errors:
        raise HwrError(
            "SOURCE_SNAPSHOT_INVALID",
            "Created source snapshot is invalid",
            errors,
        )
    return snapshot


def read_source_snapshot_document(path: Path, label: str) -> dict:
    try:
        with path.open("rb") as stream:
            payload = stream.read(MAX_SOURCE_SNAPSHOT_DOCUMENT_BYTES + 1)
    except OSError as exc:
        raise HwrError(
            "SOURCE_READ_FAILED",
            f"{label} could not be read",
            [{"error_type": type(exc).__name__}],
        ) from exc
    if len(payload) > MAX_SOURCE_SNAPSHOT_DOCUMENT_BYTES:
        raise HwrError(
            "SOURCE_SNAPSHOT_TOO_LARGE",
            f"Snapshot document exceeds {MAX_SOURCE_SNAPSHOT_DOCUMENT_BYTES} bytes",
            [{"path": str(path)}],
        )
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HwrError(
            "SOURCE_ENCODING_INVALID",
            f"{label} must be UTF-8 JSON",
            [{"start": exc.start, "end": exc.end}],
        ) from exc
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise HwrError(
            "INVALID_JSON",
            f"Invalid JSON in {label}:{exc.lineno}:{exc.colno}: {exc.msg}",
            [{"path": str(path), "line": exc.lineno, "column": exc.colno}],
        ) from exc
    if not isinstance(value, dict):
        raise HwrError(
            "INVALID_JSON_ROOT",
            f"JSON root must be an object: {label}",
        )
    return value


def load_task_with_source_snapshots(
    task_path: Path,
    *,
    source_root: Optional[Path] = None,
) -> dict:
    task = read_json(task_path)
    root = (
        source_root.expanduser()
        if source_root is not None
        else task_path.expanduser().resolve().parent
    )
    try:
        resolved_root = root.resolve(strict=True)
    except FileNotFoundError as exc:
        raise HwrError(
            "SOURCE_ROOT_NOT_FOUND",
            f"Source root does not exist: {root}",
        ) from exc
    if not resolved_root.is_dir():
        raise HwrError(
            "SOURCE_ROOT_INVALID",
            f"Source root is not a directory: {resolved_root}",
        )

    hydrated = copy.deepcopy(task)
    total_bytes = 0
    for index, source in enumerate(hydrated.get("sources", [])):
        if not isinstance(source, dict):
            continue
        snapshot_path = source.get("snapshot_path")
        inline_snapshot = source.get("snapshot")
        if snapshot_path is not None and inline_snapshot is not None:
            raise HwrError(
                "SOURCE_SNAPSHOT_INVALID",
                f"sources[{index}] must not define both snapshot and snapshot_path",
            )
        if snapshot_path is not None:
            snapshot_file = resolve_source_path(
                resolved_root,
                snapshot_path,
                f"sources[{index}].snapshot_path",
            )
            inline_snapshot = read_source_snapshot_document(
                snapshot_file,
                f"sources[{index}].snapshot_path",
            )
            source["snapshot"] = inline_snapshot
            del source["snapshot_path"]
        if inline_snapshot is None:
            continue
        snapshot_errors = validate_source_snapshot(
            inline_snapshot,
            expected_source_id=source.get("id"),
        )
        if snapshot_errors:
            raise HwrError(
                "SOURCE_SNAPSHOT_INVALID",
                f"sources[{index}] has an invalid snapshot",
                snapshot_errors,
            )
        total_bytes += inline_snapshot["bytes"]
        if total_bytes > MAX_SOURCE_SNAPSHOT_TOTAL_BYTES:
            raise HwrError(
                "SOURCE_SNAPSHOT_TOTAL_TOO_LARGE",
                f"Source snapshots exceed {MAX_SOURCE_SNAPSHOT_TOTAL_BYTES} bytes",
                [{"bytes": total_bytes, "limit": MAX_SOURCE_SNAPSHOT_TOTAL_BYTES}],
            )
    return hydrated


def compute_registry_revision(root: Path) -> str:
    registry_payload: dict[str, object] = {}
    for filename in REGISTRY_FILES:
        registry_payload[filename] = read_json(root / "registry" / filename)
    canonical = json.dumps(
        registry_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"sha256:{hashlib.sha256(canonical).hexdigest()}"


def load_repository(root: Path) -> dict:
    root = root.resolve()
    if not root.is_dir():
        raise HwrError("REPOSITORY_NOT_FOUND", f"Repository not found: {root}")

    registries = {
        filename.removesuffix(".json"): read_json(root / "registry" / filename)
        for filename in REGISTRY_FILES
    }
    objects = registries["objects"].get("objects", [])
    if not isinstance(objects, list):
        raise HwrError("INVALID_REGISTRY", "registry/objects.json objects must be an array")

    by_id: dict[str, dict] = {}
    for index, entry in enumerate(objects):
        if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
            raise HwrError(
                "INVALID_REGISTRY",
                f"registry/objects.json objects[{index}] is invalid",
            )
        object_id = entry["id"]
        if object_id in by_id:
            raise HwrError("DUPLICATE_OBJECT", f"Duplicate object ID: {object_id}")
        path_value = entry.get("path")
        if not isinstance(path_value, str):
            raise HwrError(
                "INVALID_OBJECT_PATH", f"{object_id}.path must be a string"
            )
        object_path = safe_relative_path(root, path_value, f"{object_id}.path")
        if not object_path.is_file():
            raise HwrError(
                "MISSING_OBJECT_FILE",
                f"Registered object file does not exist: {path_value}",
            )
        by_id[object_id] = entry

    index_specs = {
        "languages": "languages",
        "formats": "formats",
        "topics": "topics",
        "platforms": "platforms",
        "skills": "skills",
        "tones": "tones",
    }
    indexes: dict[str, dict[str, dict]] = {}
    for registry_name, collection_name in index_specs.items():
        collection = registries[registry_name].get(collection_name, [])
        if not isinstance(collection, list):
            raise HwrError(
                "INVALID_REGISTRY",
                f"registry/{registry_name}.json {collection_name} must be an array",
            )
        index: dict[str, dict] = {}
        for entry in collection:
            if not isinstance(entry, dict) or not isinstance(entry.get("id"), str):
                raise HwrError(
                    "INVALID_REGISTRY",
                    f"registry/{registry_name}.json contains an invalid entry",
                )
            index[entry["id"]] = entry
        indexes[registry_name] = index

    for object_id, entry in by_id.items():
        requires = entry.get("requires", [])
        if not isinstance(requires, list) or not all(
            isinstance(item, str) for item in requires
        ):
            raise HwrError(
                "INVALID_DEPENDENCIES",
                f"{object_id}.requires must be an array of object IDs",
            )
        for dependency in requires:
            if dependency not in by_id:
                raise HwrError(
                    "UNKNOWN_DEPENDENCY",
                    f"{object_id} requires unknown object {dependency}",
                )
    topological_order(list(by_id), by_id)

    for registry_name, entries in indexes.items():
        for public_value, entry in entries.items():
            module = entry.get("module")
            if module not in by_id:
                raise HwrError(
                    "UNKNOWN_INDEX_MODULE",
                    f"{registry_name}.{public_value} references unknown module {module}",
                )

    spec_revision = registries["rfcs"].get("version")
    if not isinstance(spec_revision, str) or not spec_revision:
        raise HwrError(
            "INVALID_SPEC_REVISION",
            "registry/rfcs.json version must be a non-empty string",
        )

    return {
        "root": root,
        "registries": registries,
        "objects": objects,
        "by_id": by_id,
        "indexes": indexes,
        "spec_revision": spec_revision,
        "registry_revision": compute_registry_revision(root),
    }


def validate_config(config: dict) -> list[str]:
    errors: list[str] = []
    for field in ("version", "spec_revision", "language", "content_type"):
        if not isinstance(config.get(field), str) or not config[field].strip():
            errors.append(f"{field} must be a non-empty string")

    if config.get("author_perspective") is not None:
        if config["author_perspective"] not in ALLOWED_PERSPECTIVES:
            errors.append("author_perspective is invalid")
    if config.get("risk_level") is not None:
        if config["risk_level"] not in ALLOWED_RISK_LEVELS:
            errors.append("risk_level is invalid")

    visuals = config.get("visuals", {})
    if not isinstance(visuals, dict):
        errors.append("visuals must be an object")
    elif visuals.get("mode", "auto") not in ALLOWED_VISUAL_MODES:
        errors.append("visuals.mode must be none, auto, or required")

    reviewers = config.get("reviewers", [])
    if not isinstance(reviewers, list) or not all(
        isinstance(item, str) and item for item in reviewers
    ):
        errors.append("reviewers must be an array of object IDs")
    elif len(reviewers) != len(set(reviewers)):
        errors.append("reviewers must not contain duplicates")
    return errors


def validate_task_record(task: dict) -> list[str]:
    errors: list[str] = []
    if not isinstance(task.get("task_id"), str) or not task["task_id"].strip():
        errors.append("task_id must be a non-empty string")

    for field in (
        "language",
        "locale",
        "content_type",
        "topic",
        "platform",
        "skill",
        "tone",
        "author_perspective",
        "risk_level",
    ):
        if field in task and task[field] is not None:
            if not isinstance(task[field], str) or not task[field].strip():
                errors.append(f"{field} must be a non-empty string when present")

    assessments = task.get("assessments", {})
    if not isinstance(assessments, dict):
        errors.append("assessments must be an object")
        assessments = {}
    for name, allowed in ALLOWED_ASSESSMENTS.items():
        value = assessments.get(name, "unknown")
        if value not in allowed:
            errors.append(f"assessments.{name} is invalid: {value!r}")

    sources = task.get("sources", [])
    if not isinstance(sources, list):
        errors.append("sources must be an array")
        sources = []
    source_ids: set[str] = set()
    snapshot_ids: set[str] = set()
    total_snapshot_bytes = 0
    for index, source in enumerate(sources):
        label = f"sources[{index}]"
        if not isinstance(source, dict):
            errors.append(f"{label} must be an object")
            continue
        for field in ("id", "title", "role"):
            if not isinstance(source.get(field), str) or not source[field].strip():
                errors.append(f"{label}.{field} must be a non-empty string")
        source_id = source.get("id")
        if isinstance(source_id, str):
            if source_id in source_ids:
                errors.append(f"duplicate source ID: {source_id}")
            source_ids.add(source_id)
        snapshot_path = source.get("snapshot_path")
        snapshot = source.get("snapshot")
        if snapshot_path is not None and (
            not isinstance(snapshot_path, str) or not snapshot_path.strip()
        ):
            errors.append(f"{label}.snapshot_path must be a non-empty string")
        if snapshot_path is not None and snapshot is not None:
            errors.append(f"{label} must not define both snapshot and snapshot_path")
        if snapshot is not None:
            snapshot_errors = validate_source_snapshot(
                snapshot,
                expected_source_id=source_id if isinstance(source_id, str) else None,
            )
            errors.extend(f"{label}.{message}" for message in snapshot_errors)
            if isinstance(snapshot, dict):
                snapshot_id = snapshot.get("snapshot_id")
                if isinstance(snapshot_id, str):
                    if snapshot_id in snapshot_ids:
                        errors.append(f"duplicate snapshot ID: {snapshot_id}")
                    snapshot_ids.add(snapshot_id)
                byte_count = snapshot.get("bytes")
                if isinstance(byte_count, int) and not isinstance(byte_count, bool):
                    total_snapshot_bytes += byte_count
    if total_snapshot_bytes > MAX_SOURCE_SNAPSHOT_TOTAL_BYTES:
        errors.append(
            "source snapshots exceed "
            f"{MAX_SOURCE_SNAPSHOT_TOTAL_BYTES} total bytes"
        )

    claims = task.get("claims", [])
    if not isinstance(claims, list):
        errors.append("claims must be an array")
        claims = []
    claim_ids: set[str] = set()
    for index, claim in enumerate(claims):
        label = f"claims[{index}]"
        if not isinstance(claim, dict):
            errors.append(f"{label} must be an object")
            continue
        for field in ("id", "text", "classification", "disposition"):
            if not isinstance(claim.get(field), str) or not claim[field].strip():
                errors.append(f"{label}.{field} must be a non-empty string")
        claim_id = claim.get("id")
        if isinstance(claim_id, str):
            if claim_id in claim_ids:
                errors.append(f"duplicate claim ID: {claim_id}")
            claim_ids.add(claim_id)
        if claim.get("classification") not in ALLOWED_CLAIM_CLASSIFICATIONS:
            errors.append(f"{label}.classification is invalid")
        if claim.get("disposition") not in ALLOWED_CLAIM_DISPOSITIONS:
            errors.append(f"{label}.disposition is invalid")
        if not isinstance(claim.get("material", True), bool):
            errors.append(f"{label}.material must be boolean")
        supporting_sources = claim.get("source_ids", [])
        if not isinstance(supporting_sources, list) or not all(
            isinstance(item, str) and item for item in supporting_sources
        ):
            errors.append(f"{label}.source_ids must be an array of source IDs")
        else:
            for source_id in supporting_sources:
                if source_id not in source_ids:
                    errors.append(f"{label} references unknown source {source_id}")

    media = task.get("media", {})
    if not isinstance(media, dict):
        errors.append("media must be an object")
    elif media.get("decision", "pending") not in {
        "pending",
        "none",
        "selected",
        "blocked",
    }:
        errors.append("media.decision is invalid")
    return errors


def value_with_origin(
    config: dict,
    task: dict,
    field: str,
) -> tuple[object, str]:
    if field in task and task[field] is not None:
        return task[field], "task"
    if field in config and config[field] is not None:
        return config[field], "config"
    return None, "missing"


def append_unique(values: list[str], value: str) -> None:
    if value not in values:
        values.append(value)


def topological_order(root_ids: list[str], by_id: dict[str, dict]) -> list[str]:
    state: dict[str, int] = {}
    stack: list[str] = []
    ordered: list[str] = []

    def visit(object_id: str) -> None:
        if object_id not in by_id:
            raise HwrError("UNKNOWN_OBJECT", f"Unknown object ID: {object_id}")
        status = state.get(object_id, 0)
        if status == 2:
            return
        if status == 1:
            start = stack.index(object_id)
            raise HwrError(
                "DEPENDENCY_CYCLE",
                "Object dependency cycle detected",
                stack[start:] + [object_id],
            )
        state[object_id] = 1
        stack.append(object_id)
        for dependency in by_id[object_id].get("requires", []):
            visit(dependency)
        stack.pop()
        state[object_id] = 2
        ordered.append(object_id)

    for root_id in root_ids:
        visit(root_id)
    return ordered


def resolve_modules(repository: dict, config: dict, task: Optional[dict] = None) -> dict:
    task = task or {}
    config_errors = validate_config(config)
    task_errors = validate_task_record(task) if task else []
    structural_errors = config_errors + task_errors
    if structural_errors:
        raise HwrError(
            "INVALID_INPUT",
            "Config or task record is structurally invalid",
            structural_errors,
        )

    if config.get("spec_revision") != repository["spec_revision"]:
        raise HwrError(
            "SPEC_REVISION_MISMATCH",
            "Config spec_revision does not match registry/rfcs.json",
            [
                {
                    "config": config.get("spec_revision"),
                    "repository": repository["spec_revision"],
                }
            ],
        )
    pinned_registry = config.get("registry_revision")
    if (
        pinned_registry is not None
        and pinned_registry != repository["registry_revision"]
    ):
        raise HwrError(
            "REGISTRY_REVISION_MISMATCH",
            "Config registry_revision does not match the current registry digest",
            [
                {
                    "config": pinned_registry,
                    "repository": repository["registry_revision"],
                }
            ],
        )

    indexes = repository["indexes"]
    by_id = repository["by_id"]
    inputs: dict[str, object] = {}
    origins: dict[str, str] = {}
    fallbacks: list[dict] = []
    inferences: list[dict] = []
    warnings: list[dict] = []
    roots = list(REQUIRED_ROOTS)

    language, origin = value_with_origin(config, task, "language")
    if language not in indexes["languages"]:
        raise HwrError("UNKNOWN_LANGUAGE", f"Unknown language: {language!r}")
    inputs["language"] = language
    origins["language"] = origin
    append_unique(roots, indexes["languages"][language]["module"])

    locale, locale_origin = value_with_origin(config, task, "locale")
    if locale is None:
        locale = indexes["languages"][language].get("default_locale")
        locale_origin = "inferred"
        inferences.append(
            {
                "field": "locale",
                "value": locale,
                "reason": f"default locale for language {language}",
            }
        )
    inputs["locale"] = locale
    origins["locale"] = locale_origin

    content_type, origin = value_with_origin(config, task, "content_type")
    if content_type not in indexes["formats"]:
        raise HwrError(
            "UNKNOWN_CONTENT_TYPE", f"Unknown content_type: {content_type!r}"
        )
    inputs["content_type"] = content_type
    origins["content_type"] = origin
    append_unique(roots, indexes["formats"][content_type]["module"])
    append_unique(roots, "reviewer.format")

    topic, origin = value_with_origin(config, task, "topic")
    if topic not in indexes["topics"]:
        fallback_topic = repository["registries"]["topics"].get("fallback")
        if fallback_topic not in indexes["topics"]:
            raise HwrError("TOPIC_FALLBACK_MISSING", "Topic fallback is invalid")
        fallbacks.append(
            {
                "field": "topic",
                "input": topic,
                "value": fallback_topic,
                "reason": "unknown or missing topic",
            }
        )
        topic = fallback_topic
        origin = "fallback"
    inputs["topic"] = topic
    origins["topic"] = origin
    append_unique(roots, indexes["topics"][topic]["module"])
    append_unique(roots, "reviewer.topic")

    platform, origin = value_with_origin(config, task, "platform")
    if platform not in indexes["platforms"]:
        generic_platform = "blog" if content_type == "article" else "social"
        fallbacks.append(
            {
                "field": "platform",
                "input": platform,
                "value": generic_platform,
                "reason": f"generic platform for format {content_type}",
            }
        )
        platform = generic_platform
        origin = "fallback" if origin != "missing" else "inferred"
    platform_entry = indexes["platforms"][platform]
    if platform_entry.get("default_format") != content_type:
        raise HwrError(
            "PLATFORM_FORMAT_CONFLICT",
            f"Platform {platform} is incompatible with content_type {content_type}",
            [
                {
                    "platform_default_format": platform_entry.get("default_format"),
                    "content_type": content_type,
                }
            ],
        )
    inputs["platform"] = platform
    origins["platform"] = origin
    append_unique(roots, platform_entry["module"])
    append_unique(roots, "reviewer.platform")

    skill, origin = value_with_origin(config, task, "skill")
    if skill is not None:
        if skill not in indexes["skills"]:
            raise HwrError("UNKNOWN_SKILL", f"Unknown skill: {skill!r}")
        inputs["skill"] = skill
        origins["skill"] = origin
        append_unique(roots, indexes["skills"][skill]["module"])
    else:
        inputs["skill"] = None
        origins["skill"] = "omitted"

    tone, origin = value_with_origin(config, task, "tone")
    if tone is not None:
        if tone not in indexes["tones"]:
            raise HwrError("UNKNOWN_TONE", f"Unknown tone: {tone!r}")
        inputs["tone"] = tone
        origins["tone"] = origin
        append_unique(roots, indexes["tones"][tone]["module"])
    else:
        inputs["tone"] = None
        origins["tone"] = "omitted"
        inferences.append(
            {
                "field": "register",
                "value": "direct-neutral",
                "reason": "no tone module selected",
            }
        )

    for field in ("audience", "intent", "author_perspective"):
        value, value_origin = value_with_origin(config, task, field)
        inputs[field] = value
        origins[field] = value_origin

    perspective = inputs["author_perspective"]
    if perspective is not None and perspective not in ALLOWED_PERSPECTIVES:
        raise HwrError(
            "UNKNOWN_AUTHOR_PERSPECTIVE",
            f"Unknown author perspective: {perspective!r}",
        )

    risk_level, origin = value_with_origin(config, task, "risk_level")
    if risk_level is None:
        risk_level = indexes["topics"][topic].get("default_risk", "low")
        origin = "inferred"
        inferences.append(
            {
                "field": "risk_level",
                "value": risk_level,
                "reason": f"default risk for topic {topic}",
            }
        )
    if risk_level not in ALLOWED_RISK_LEVELS:
        raise HwrError("UNKNOWN_RISK_LEVEL", f"Unknown risk level: {risk_level!r}")
    inputs["risk_level"] = risk_level
    origins["risk_level"] = origin

    visuals = task.get("visuals", config.get("visuals", {}))
    if not isinstance(visuals, dict):
        raise HwrError("INVALID_VISUAL_CONFIG", "visuals must be an object")
    visual_mode = visuals.get("mode", "auto")
    if visual_mode not in ALLOWED_VISUAL_MODES:
        raise HwrError("UNKNOWN_VISUAL_MODE", f"Unknown visual mode: {visual_mode}")
    inputs["visual_mode"] = visual_mode
    origins["visual_mode"] = "task" if "visuals" in task else (
        "config" if "visuals" in config else "inferred"
    )
    if visual_mode in {"auto", "required"}:
        append_unique(roots, "rule.visual-integrity")
        append_unique(roots, "reviewer.visual")

    configured_reviewers = task.get("reviewers", config.get("reviewers", []))
    if not isinstance(configured_reviewers, list):
        raise HwrError("INVALID_REVIEWERS", "reviewers must be an array")
    for reviewer_id in configured_reviewers:
        reviewer = by_id.get(reviewer_id)
        if reviewer is None or reviewer.get("kind") != "reviewer":
            raise HwrError(
                "UNKNOWN_REVIEWER", f"Unknown reviewer object: {reviewer_id}"
            )
        append_unique(roots, reviewer_id)

    dependency_order = topological_order(roots, by_id)
    for object_id in roots:
        obj = by_id[object_id]
        selectors = (
            ("languages", language),
            ("formats", content_type),
            ("topics", topic),
            ("platforms", platform),
        )
        for selector_name, selected_value in selectors:
            selector = obj.get(selector_name, [])
            if selector and selected_value not in selector:
                raise HwrError(
                    "OBJECT_APPLICABILITY_ERROR",
                    f"{object_id} excludes {selector_name}={selected_value}",
                )

    return {
        "spec_revision": repository["spec_revision"],
        "registry_revision": repository["registry_revision"],
        "inputs": inputs,
        "origins": origins,
        "root_objects": roots,
        "dependency_order": dependency_order,
        "fallbacks": fallbacks,
        "inferences": inferences,
        "conflicts": [],
        "warnings": warnings,
    }


def blocker(code: str, field: str, message: str, remediation: str) -> dict:
    return {
        "code": code,
        "field": field,
        "message": message,
        "remediation": remediation,
    }


def build_context_gate(config: dict, task: dict, resolution: dict) -> dict:
    blockers: list[dict] = []
    inputs = resolution["inputs"]

    required_context = {
        "subject": task.get("subject"),
        "reader_promise": task.get("reader_promise"),
        "audience": inputs.get("audience"),
        "intent": inputs.get("intent"),
        "author_perspective": inputs.get("author_perspective"),
    }
    for field, value in required_context.items():
        if value is None or value == "" or value == []:
            blockers.append(
                blocker(
                    "MISSING_CONTEXT",
                    field,
                    f"Required context is missing: {field}",
                    f"Provide {field} before drafting.",
                )
            )

    if (
        inputs.get("content_type") == "article"
        and not task.get("central_question")
    ):
        blockers.append(
            blocker(
                "MISSING_CENTRAL_QUESTION",
                "central_question",
                "An article needs a central reader question.",
                "Provide the question the article must answer.",
            )
        )

    assessments = task.get("assessments", {})
    perspective = inputs.get("author_perspective")
    perspective_assessment = assessments.get("perspective", "unknown")
    if perspective in {"first-person", "expert"}:
        if perspective_assessment != "authorized":
            blockers.append(
                blocker(
                    "UNAUTHORIZED_PERSPECTIVE",
                    "assessments.perspective",
                    f"{perspective} perspective is not verified as authorized.",
                    "Supply authorized author material or choose a legitimate perspective.",
                )
            )

    source_config = config.get("sources", {})
    source_required = (
        isinstance(source_config, dict) and source_config.get("required", False)
    )
    sources = task.get("sources", [])
    if source_required and not sources:
        blockers.append(
            blocker(
                "MISSING_REQUIRED_SOURCES",
                "sources",
                "The config requires sources but the task contains none.",
                "Add source records or change the task scope.",
            )
        )

    freshness = assessments.get("source_freshness", "unknown")
    if (source_required or sources) and freshness not in {"adequate", "not-applicable"}:
        blockers.append(
            blocker(
                "SOURCE_FRESHNESS_UNRESOLVED",
                "assessments.source_freshness",
                f"Source freshness is {freshness}.",
                "Assess the source set against the task cutoff.",
            )
        )

    platform_assessment = assessments.get("platform_constraints", "unknown")
    if platform_assessment not in {"known", "not-applicable"}:
        blockers.append(
            blocker(
                "PLATFORM_CONSTRAINTS_UNRESOLVED",
                "assessments.platform_constraints",
                "Material platform constraints have not been assessed.",
                "Verify current platform constraints or mark them not applicable.",
            )
        )

    claims = task.get("claims", [])
    if not claims:
        blockers.append(
            blocker(
                "EMPTY_CLAIM_LEDGER",
                "claims",
                "The task contains no planned claims.",
                "Add at least one classified planned claim.",
            )
        )

    for claim in claims:
        if not claim.get("material", True) or claim.get("disposition") == "omit":
            continue
        claim_id = claim["id"]
        classification = claim["classification"]
        source_ids = claim.get("source_ids", [])
        qualification = claim.get("qualification")
        disposition = claim["disposition"]

        if classification in {"verified-fact", "source-claim"} and not source_ids:
            blockers.append(
                blocker(
                    "UNSUPPORTED_MATERIAL_CLAIM",
                    f"claims.{claim_id}",
                    f"Material {classification} claim has no supporting source.",
                    "Add source IDs, narrow, research, or omit the claim.",
                )
            )
        if classification in {"inference", "assumption"} and not qualification:
            blockers.append(
                blocker(
                    "UNQUALIFIED_NONFACTUAL_CLAIM",
                    f"claims.{claim_id}",
                    f"Material {classification} lacks a qualification.",
                    "Expose the reasoning or limitation, narrow, or omit the claim.",
                )
            )
        if classification == "unknown" and disposition not in {"research", "omit"}:
            blockers.append(
                blocker(
                    "UNKNOWN_CLAIM_SELECTED",
                    f"claims.{claim_id}",
                    "An unknown claim cannot be selected for drafting.",
                    "Research or omit the claim.",
                )
            )
        if disposition == "research":
            blockers.append(
                blocker(
                    "RESEARCH_REQUIRED",
                    f"claims.{claim_id}",
                    "A material claim still requires research.",
                    "Complete research, reclassify, narrow, or omit the claim.",
                )
            )

    return {
        "gate": "context-gate",
        "status": "pass" if not blockers else "blocked",
        "blockers": blockers,
        "checked_claims": len(claims),
        "checked_sources": len(sources),
    }


def build_media_decision(config: dict, task: dict, resolution: dict) -> dict:
    mode = resolution["inputs"]["visual_mode"]
    media = task.get("media", {})
    decision = media.get("decision", "pending")
    reason = media.get("reason")
    findings: list[dict] = []

    if mode == "none":
        if decision == "selected":
            findings.append(
                blocker(
                    "VISUAL_MODE_CONFLICT",
                    "media.decision",
                    "A selected asset conflicts with visuals.mode=none.",
                    "Change visual mode or remove the selected asset.",
                )
            )
        else:
            decision = "none"
            reason = reason or "Visual production is disabled by config."

    if mode == "required" and decision == "none":
        findings.append(
            blocker(
                "REQUIRED_VISUAL_OMITTED",
                "media.decision",
                "Visual mode is required but the media decision is none.",
                "Select a supportable asset or mark the visual gate blocked.",
            )
        )

    if decision == "selected":
        brief = media.get("brief")
        if not isinstance(brief, dict):
            findings.append(
                blocker(
                    "MISSING_VISUAL_BRIEF",
                    "media.brief",
                    "Selected media needs a visual brief.",
                    "Provide the visual purpose, evidence boundary, handoff, and acceptance criteria.",
                )
            )
        else:
            for field in (
                "purpose",
                "reader_benefit",
                "evidence_basis",
                "must_not_imply",
                "asset_type",
                "acceptance_criteria",
            ):
                value = brief.get(field)
                if value is None or value == "" or value == []:
                    findings.append(
                        blocker(
                            "INCOMPLETE_VISUAL_BRIEF",
                            f"media.brief.{field}",
                            f"Selected media brief is missing {field}.",
                            f"Provide media.brief.{field}.",
                        )
                    )
        rights = task.get("assessments", {}).get("rights", "unknown")
        if rights not in {"cleared", "not-applicable"}:
            findings.append(
                blocker(
                    "VISUAL_RIGHTS_UNRESOLVED",
                    "assessments.rights",
                    f"Visual rights assessment is {rights}.",
                    "Clear rights or select a supportable alternative.",
                )
            )

    if decision == "blocked":
        findings.append(
            blocker(
                "VISUAL_GATE_BLOCKED",
                "media.decision",
                reason or "The visual gate is explicitly blocked.",
                "Resolve the visual blocker or omit the asset when mode permits.",
            )
        )

    if findings:
        status = "blocked"
    elif decision == "pending":
        status = "pending"
    else:
        status = "ready"

    return {
        "mode": mode,
        "decision": decision,
        "status": status,
        "reason": reason,
        "brief": media.get("brief"),
        "findings": findings,
    }


def build_review_plan(repository: dict, resolution: dict) -> list[dict]:
    selected = {
        object_id
        for object_id in resolution["root_objects"]
        if repository["by_id"][object_id].get("kind") == "reviewer"
    }
    ordered = [reviewer_id for reviewer_id in REVIEW_ORDER if reviewer_id in selected]
    for reviewer_id in sorted(selected - set(ordered)):
        ordered.append(reviewer_id)
    return [
        {
            "reviewer_id": reviewer_id,
            "title": repository["by_id"][reviewer_id]["title"],
            "status": "pending",
        }
        for reviewer_id in ordered
    ]


def build_run_plan(repository: dict, config: dict, task: dict) -> dict:
    task_errors = validate_task_record(task)
    if task_errors:
        raise HwrError("INVALID_TASK", "Task record is structurally invalid", task_errors)

    resolution = resolve_modules(repository, config, task)
    context_gate = build_context_gate(config, task, resolution)
    media_decision = build_media_decision(config, task, resolution)

    if context_gate["status"] == "blocked":
        state = "blocked"
        blocked_stage = "context-gate"
    elif media_decision["status"] == "blocked":
        state = "blocked"
        blocked_stage = "visual-gate"
    else:
        state = "context-ready"
        blocked_stage = None

    blockers = list(context_gate["blockers"]) + list(media_decision["findings"])
    if blockers:
        next_actions = [item["remediation"] for item in blockers]
    else:
        next_actions = [
            "Create the content design from the reader promise and claim ledger."
        ]
        if media_decision["decision"] == "pending":
            next_actions.append(
                "Complete the media decision before visual production."
            )
        elif media_decision["decision"] == "selected":
            next_actions.append(
                "Produce or commission the selected asset from the approved brief."
            )
        next_actions.append("Draft for meaning, then run the declared review plan.")

    if media_decision["status"] == "blocked":
        visual_output_status = "blocked"
    elif media_decision["decision"] == "pending":
        visual_output_status = "pending"
    elif media_decision["decision"] == "selected":
        visual_output_status = "planned"
    else:
        visual_output_status = "not-applicable"

    sources = []
    for source in task.get("sources", []):
        run_source = {
            key: source.get(key)
            for key in (
                "id",
                "title",
                "role",
                "location",
                "publication_date",
                "retrieved_at",
                "version",
                "status",
                "scope",
                "rights",
                "notes",
                "snapshot",
            )
            if source.get(key) is not None
        }
        sources.append(run_source)

    source_note_records = []
    for source in sources:
        note_source = copy.deepcopy(source)
        snapshot = note_source.get("snapshot")
        if isinstance(snapshot, dict):
            note_source["snapshot"] = {
                key: value
                for key, value in snapshot.items()
                if key != "content"
            }
        source_note_records.append(note_source)

    return {
        "schema_version": SPEC_SCHEMA_VERSION,
        "run_id": f"{task['task_id']}:{task.get('revision', '1')}",
        "task_id": task["task_id"],
        "task_revision": str(task.get("revision", "1")),
        "spec_revision": repository["spec_revision"],
        "registry_revision": repository["registry_revision"],
        "state": state,
        "blocked_stage": blocked_stage,
        "task": {
            "subject": task.get("subject"),
            "central_question": task.get("central_question"),
            "reader_promise": task.get("reader_promise"),
            "primary_job": task.get("primary_job"),
            "artifact_form": task.get("artifact_form"),
            "resolved_inputs": resolution["inputs"],
            "constraints": task.get("constraints", config.get("constraints", [])),
            "required_disclosures": task.get("required_disclosures", []),
        },
        "resolution": resolution,
        "sources": sources,
        "claim_ledger": task.get("claims", []),
        "gates": {
            "framing": {"status": "pass"},
            "module_resolution": {"status": "pass"},
            "context": context_gate,
            "media": media_decision,
        },
        "content_design": {
            "status": "pending" if state != "blocked" else "blocked",
            "reader_promise": task.get("reader_promise"),
            "working_thesis": None,
            "sections_or_units": [],
        },
        "review_plan": build_review_plan(repository, resolution),
        "output_package": {
            "publication_copy": {"status": "not-started", "content": None},
            "visual_assets": {"status": visual_output_status, "items": []},
            "source_notes": {
                "status": "prepared",
                "sources": source_note_records,
                "unresolved_claims": [
                    claim["id"]
                    for claim in task.get("claims", [])
                    if claim["classification"] == "unknown"
                    or claim["disposition"] == "research"
                ],
            },
            "review_report": {"status": "not-started", "findings": []},
            "revision_summary": {"status": "not-started", "changes": []},
            "audit": {
                "status": "prepared",
                "fallbacks": resolution["fallbacks"],
                "inferences": resolution["inferences"],
                "deviations": [],
                "history": [
                    {
                        "event": "run-planned",
                        "from_state": None,
                        "to_state": state,
                        "record_revision": task.get("revision", "1"),
                    }
                ],
            },
        },
        "blockers": blockers,
        "next_actions": list(dict.fromkeys(next_actions)),
    }


def validate_run_record(repository: dict, run: dict) -> list[str]:
    errors: list[str] = []
    required = {
        "schema_version",
        "run_id",
        "task_id",
        "task_revision",
        "spec_revision",
        "registry_revision",
        "state",
        "blocked_stage",
        "task",
        "resolution",
        "sources",
        "claim_ledger",
        "gates",
        "content_design",
        "review_plan",
        "output_package",
        "blockers",
        "next_actions",
    }
    missing = required - run.keys()
    if missing:
        errors.append(f"run record missing fields: {', '.join(sorted(missing))}")

    if run.get("schema_version") != SPEC_SCHEMA_VERSION:
        errors.append(f"schema_version must equal {SPEC_SCHEMA_VERSION}")
    if run.get("spec_revision") != repository["spec_revision"]:
        errors.append("run spec_revision does not match the repository")
    if run.get("registry_revision") != repository["registry_revision"]:
        errors.append("run registry_revision does not match the repository")
    if run.get("state") not in ALLOWED_RUN_STATES:
        errors.append("run state is invalid")
    blocked_stage = run.get("blocked_stage")
    if run.get("state") == "blocked":
        if not isinstance(blocked_stage, str) or not blocked_stage:
            errors.append("blocked state requires blocked_stage")
    elif blocked_stage is not None:
        errors.append("non-blocked state requires blocked_stage to be null")

    task = run.get("task")
    if not isinstance(task, dict):
        errors.append("task must be an object")

    resolution = run.get("resolution")
    resolved_roots: list[str] = []
    if not isinstance(resolution, dict):
        errors.append("resolution must be an object")
    else:
        resolved_order: list[str] = []
        for field in ("root_objects", "dependency_order"):
            values = resolution.get(field)
            if not isinstance(values, list) or not all(
                isinstance(item, str) for item in values
            ):
                errors.append(f"resolution.{field} must be an array of object IDs")
                continue
            unknown = sorted(set(values) - repository["by_id"].keys())
            if unknown:
                errors.append(
                    f"resolution.{field} references unknown objects: {', '.join(unknown)}"
                )
            if len(values) != len(set(values)):
                errors.append(f"resolution.{field} must not contain duplicates")
            if field == "root_objects":
                resolved_roots = values
            else:
                resolved_order = values
        missing_roots = sorted(set(resolved_roots) - set(resolved_order))
        if missing_roots:
            errors.append(
                "resolution.dependency_order omits root objects: "
                + ", ".join(missing_roots)
            )
        positions = {
            object_id: index for index, object_id in enumerate(resolved_order)
        }
        for object_id in resolved_order:
            for dependency in repository["by_id"].get(object_id, {}).get(
                "requires", []
            ):
                if dependency not in positions or positions[dependency] >= positions[object_id]:
                    errors.append(
                        f"dependency order places {dependency} after {object_id}"
                    )

    gates = run.get("gates")
    if not isinstance(gates, dict):
        errors.append("gates must be an object")
    else:
        context_gate = gates.get("context")
        media_gate = gates.get("media")
        if not isinstance(context_gate, dict):
            errors.append("gates.context must be an object")
            context_status = None
        else:
            context_status = context_gate.get("status")
        if not isinstance(media_gate, dict):
            errors.append("gates.media must be an object")
            media_status = None
        else:
            media_status = media_gate.get("status")
        if run.get("state") == "context-ready" and context_status != "pass":
            errors.append("context-ready state requires a passing context gate")
        if run.get("state") == "ready":
            if context_status != "pass" or media_status not in {"ready", "not-applicable"}:
                errors.append("ready state requires passing context and media gates")

    sources = run.get("sources")
    if not isinstance(sources, list) or not all(
        isinstance(source, dict) for source in sources
    ):
        errors.append("sources must be an array of objects")
    else:
        total_snapshot_bytes = 0
        snapshot_ids: set[str] = set()
        for index, source in enumerate(sources):
            snapshot = source.get("snapshot")
            if snapshot is None:
                continue
            snapshot_errors = validate_source_snapshot(
                snapshot,
                expected_source_id=source.get("id"),
            )
            errors.extend(
                f"sources[{index}].{message}" for message in snapshot_errors
            )
            byte_count = snapshot.get("bytes") if isinstance(snapshot, dict) else None
            if isinstance(byte_count, int) and not isinstance(byte_count, bool):
                total_snapshot_bytes += byte_count
            snapshot_id = (
                snapshot.get("snapshot_id") if isinstance(snapshot, dict) else None
            )
            if isinstance(snapshot_id, str):
                if snapshot_id in snapshot_ids:
                    errors.append(f"duplicate snapshot ID: {snapshot_id}")
                snapshot_ids.add(snapshot_id)
        if total_snapshot_bytes > MAX_SOURCE_SNAPSHOT_TOTAL_BYTES:
            errors.append(
                "source snapshot total exceeds "
                f"{MAX_SOURCE_SNAPSHOT_TOTAL_BYTES} bytes"
            )

    claim_ledger = run.get("claim_ledger")
    if not isinstance(claim_ledger, list) or not all(
        isinstance(claim, dict) for claim in claim_ledger
    ):
        errors.append("claim_ledger must be an array of objects")

    content_design = run.get("content_design")
    if not isinstance(content_design, dict):
        errors.append("content_design must be an object")
    elif run.get("state") in {
        "media-decided",
        "drafted",
        "edited",
        "reviewed",
        "revising",
        "ready",
    } and content_design.get("status") != "ready":
        errors.append(f"{run.get('state')} state requires a ready content design")

    review_plan = run.get("review_plan")
    if not isinstance(review_plan, list):
        errors.append("review_plan must be an array")
    else:
        reviewer_ids: list[str] = []
        for index, review in enumerate(review_plan):
            label = f"review_plan[{index}]"
            if not isinstance(review, dict):
                errors.append(f"{label} must be an object")
                continue
            reviewer_id = review.get("reviewer_id")
            if not isinstance(reviewer_id, str) or not reviewer_id:
                errors.append(f"{label}.reviewer_id must be a non-empty string")
                reviewer = None
            else:
                reviewer = repository["by_id"].get(reviewer_id)
            if isinstance(reviewer_id, str) and (
                reviewer is None or reviewer.get("kind") != "reviewer"
            ):
                errors.append(f"{label} references an unknown reviewer")
            elif reviewer is not None and reviewer_id not in resolved_roots:
                errors.append(f"{label} reviewer is absent from resolution.root_objects")
            if not isinstance(review.get("title"), str) or not review["title"]:
                errors.append(f"{label}.title must be a non-empty string")
            if review.get("status") not in {"pending", "pass", "fail", "skipped"}:
                errors.append(f"{label}.status is invalid")
            if isinstance(reviewer_id, str):
                reviewer_ids.append(reviewer_id)
        if len(reviewer_ids) != len(set(reviewer_ids)):
            errors.append("review_plan must not contain duplicate reviewers")

    blockers = run.get("blockers")
    if not isinstance(blockers, list):
        errors.append("blockers must be an array")
    elif run.get("state") == "blocked" and not blockers:
        errors.append("blocked state requires at least one blocker")
    elif run.get("state") != "blocked" and blockers:
        errors.append("non-blocked state cannot retain blockers")

    output_package = run.get("output_package")
    if not isinstance(output_package, dict):
        errors.append("output_package must be an object")
    else:
        required_outputs = {
            "publication_copy",
            "visual_assets",
            "source_notes",
            "review_report",
            "revision_summary",
            "audit",
        }
        missing_outputs = required_outputs - output_package.keys()
        if missing_outputs:
            errors.append(
                "output_package missing fields: "
                + ", ".join(sorted(missing_outputs))
            )
        publication_copy = output_package.get("publication_copy")
        if not isinstance(publication_copy, dict):
            errors.append("output_package.publication_copy must be an object")
            publication_status = None
        else:
            publication_status = publication_copy.get("status")
        if publication_status == "ready" and run.get("state") != "ready":
            errors.append("publication_copy cannot be ready when run state is not ready")
        expected_publication_status = {
            "drafted": "drafted",
            "edited": "edited",
            "reviewed": "edited",
            "revising": "edited",
            "ready": "ready",
        }.get(run.get("state"))
        if (
            expected_publication_status is not None
            and publication_status != expected_publication_status
        ):
            errors.append(
                f"{run.get('state')} state requires publication_copy.status "
                f"{expected_publication_status}"
            )
        if run.get("state") in {
            "drafted",
            "edited",
            "reviewed",
            "revising",
            "ready",
        } and (
            not isinstance(publication_copy, dict)
            or not isinstance(publication_copy.get("artifact_revision"), str)
            or not publication_copy["artifact_revision"]
        ):
            errors.append(f"{run.get('state')} state requires an artifact revision")

        visual_assets = output_package.get("visual_assets")
        if not isinstance(visual_assets, dict):
            errors.append("output_package.visual_assets must be an object")
        else:
            if visual_assets.get("status") in {"produced", "reviewed"}:
                visual_artifact_revision = visual_assets.get("artifact_revision")
                publication_revision = (
                    publication_copy.get("artifact_revision")
                    if isinstance(publication_copy, dict)
                    else None
                )
                if visual_artifact_revision != publication_revision:
                    errors.append(
                        "produced visual assets must target the current artifact revision"
                    )
            if run.get("state") == "ready" and isinstance(gates, dict):
                media_gate = gates.get("media", {})
                if (
                    isinstance(media_gate, dict)
                    and media_gate.get("decision") == "selected"
                    and (
                        visual_assets.get("status") != "reviewed"
                        or not visual_assets.get("items")
                    )
                ):
                    errors.append("ready selected media requires reviewed visual assets")

        review_report = output_package.get("review_report")
        if not isinstance(review_report, dict):
            errors.append("output_package.review_report must be an object")
        elif run.get("state") in {"reviewed", "ready"}:
            if review_report.get("status") != "complete":
                errors.append(f"{run.get('state')} state requires a complete review")
            incomplete = [
                reviewer.get("reviewer_id")
                for reviewer in review_plan
                if isinstance(reviewer, dict) and reviewer.get("status") != "pass"
            ] if isinstance(review_plan, list) else []
            if incomplete:
                errors.append(
                    f"{run.get('state')} state has incomplete reviewers: "
                    + ", ".join(str(item) for item in incomplete)
                )

        source_notes = output_package.get("source_notes")
        if not isinstance(source_notes, dict):
            errors.append("output_package.source_notes must be an object")
        elif run.get("state") == "ready" and source_notes.get("status") != "ready":
            errors.append("ready state requires ready source notes")

        audit = output_package.get("audit")
        if not isinstance(audit, dict):
            errors.append("output_package.audit must be an object")
        elif not isinstance(audit.get("history"), list):
            errors.append("output_package.audit.history must be an array")
        elif run.get("state") == "ready" and audit.get("status") != "complete":
            errors.append("ready state requires a complete audit")

    next_actions = run.get("next_actions")
    if not isinstance(next_actions, list) or not all(
        isinstance(action, str) and action for action in next_actions
    ):
        errors.append("next_actions must be an array of non-empty strings")
    return errors


def require_valid_run(repository: dict, run: dict) -> None:
    errors = validate_run_record(repository, run)
    if errors:
        raise HwrError("RUN_INVALID", "Run record is invalid", errors)


def require_transition(run: dict, event: str, allowed_states: set[str]) -> None:
    if run.get("state") not in allowed_states:
        raise HwrError(
            "INVALID_TRANSITION",
            f"Cannot apply {event} while run state is {run.get('state')!r}",
            [
                {
                    "event": event,
                    "current_state": run.get("state"),
                    "allowed_states": sorted(allowed_states),
                }
            ],
        )


def require_matching_run_id(run: dict, record: dict) -> None:
    if record.get("run_id") != run.get("run_id"):
        raise HwrError(
            "RUN_ID_MISMATCH",
            "Adapter result run_id does not match the run record",
            [
                {
                    "run": run.get("run_id"),
                    "adapter_result": record.get("run_id"),
                }
            ],
        )


def append_history(
    run: dict,
    event: str,
    from_state: str,
    to_state: str,
    record_revision: Optional[str] = None,
) -> None:
    audit = run["output_package"]["audit"]
    history = audit.setdefault("history", [])
    history.append(
        {
            "event": event,
            "from_state": from_state,
            "to_state": to_state,
            "record_revision": record_revision,
        }
    )


def validate_content_design_record(run: dict, record: dict) -> list[str]:
    errors: list[str] = []
    for field in ("run_id", "design_revision", "reader_promise", "working_thesis"):
        if not isinstance(record.get(field), str) or not record[field].strip():
            errors.append(f"{field} must be a non-empty string")
    sections = record.get("sections_or_units")
    known_claims = {
        claim.get("id")
        for claim in run.get("claim_ledger", [])
        if isinstance(claim, dict)
    }
    if not isinstance(sections, list) or not sections:
        errors.append("sections_or_units must be a non-empty array")
    else:
        section_ids: list[str] = []
        for index, section in enumerate(sections):
            label = f"sections_or_units[{index}]"
            if not isinstance(section, dict):
                errors.append(f"{label} must be an object")
                continue
            for field in ("id", "purpose"):
                if not isinstance(section.get(field), str) or not section[field].strip():
                    errors.append(f"{label}.{field} must be a non-empty string")
            if isinstance(section.get("id"), str):
                section_ids.append(section["id"])
            claim_ids = section.get("claim_ids", [])
            if not isinstance(claim_ids, list) or not all(
                isinstance(claim_id, str) and claim_id for claim_id in claim_ids
            ):
                errors.append(f"{label}.claim_ids must be an array of claim IDs")
            else:
                unknown = sorted(set(claim_ids) - known_claims)
                if unknown:
                    errors.append(
                        f"{label} references unknown claims: {', '.join(unknown)}"
                    )
        if len(section_ids) != len(set(section_ids)):
            errors.append("sections_or_units must not contain duplicate IDs")
    metadata = record.get("public_metadata", {})
    if not isinstance(metadata, dict):
        errors.append("public_metadata must be an object")
    visual_role = record.get("visual_role")
    if visual_role is not None and (
        not isinstance(visual_role, str) or not visual_role.strip()
    ):
        errors.append("visual_role must be null or a non-empty string")
    adapter = record.get("adapter")
    if adapter is not None:
        if not isinstance(adapter, dict):
            errors.append("adapter must be an object")
        else:
            if not isinstance(adapter.get("id"), str) or not adapter["id"].strip():
                errors.append("adapter.id must be a non-empty string")
            if adapter.get("mode") not in {"human", "model", "tool"}:
                errors.append("adapter.mode must be human, model, or tool")
    return errors


def apply_content_design(repository: dict, run: dict, record: dict) -> dict:
    require_valid_run(repository, run)
    require_transition(run, "content-design", {"context-ready"})
    errors = validate_content_design_record(run, record)
    if errors:
        raise HwrError(
            "CONTENT_DESIGN_INVALID",
            "Content design record is invalid",
            errors,
        )
    require_matching_run_id(run, record)
    if record["reader_promise"] != run["task"].get("reader_promise"):
        raise HwrError(
            "READER_PROMISE_MISMATCH",
            "Content design reader_promise does not match the gated task",
        )
    media_status = run["gates"]["media"].get("status")
    if media_status not in {"ready", "not-applicable"}:
        raise HwrError(
            "MEDIA_DECISION_INCOMPLETE",
            "Content design cannot advance until the media decision is complete",
            [{"media_status": media_status}],
        )

    updated = copy.deepcopy(run)
    previous_state = updated["state"]
    updated["content_design"] = {
        "status": "ready",
        "design_revision": record["design_revision"],
        "reader_promise": record["reader_promise"],
        "working_thesis": record["working_thesis"],
        "sections_or_units": record["sections_or_units"],
        "public_metadata": record.get("public_metadata", {}),
        "visual_role": record.get("visual_role"),
        "adapter": record.get("adapter"),
    }
    updated["state"] = "media-decided"
    updated["next_actions"] = [
        "Export a draft adapter packet and create a meaning-complete draft."
    ]
    append_history(
        updated,
        "content-design-applied",
        previous_state,
        updated["state"],
        record["design_revision"],
    )
    return updated


def validate_artifact_record(run: dict, record: dict) -> list[str]:
    errors: list[str] = []
    for field in ("run_id", "artifact_revision", "stage"):
        if not isinstance(record.get(field), str) or not record[field].strip():
            errors.append(f"{field} must be a non-empty string")
    if record.get("stage") not in ALLOWED_ARTIFACT_STAGES:
        errors.append("stage must be draft, edit, or revision")

    publication = record.get("publication")
    if not isinstance(publication, dict):
        errors.append("publication must be an object")
    else:
        if publication.get("content_type") not in {"article", "social-post"}:
            errors.append("publication.content_type is invalid")
        if not isinstance(publication.get("text"), str) or not publication["text"].strip():
            errors.append("publication.text must be a non-empty string")
        if not isinstance(publication.get("metadata", {}), dict):
            errors.append("publication.metadata must be an object")

    visuals = record.get("visuals", [])
    if not isinstance(visuals, list) or not all(
        isinstance(visual, dict) for visual in visuals
    ):
        errors.append("visuals must be an array of objects")

    known_claims = {
        claim.get("id")
        for claim in run.get("claim_ledger", [])
        if isinstance(claim, dict)
    }
    claim_usage = record.get("claim_usage", [])
    if not isinstance(claim_usage, list):
        errors.append("claim_usage must be an array")
    else:
        used_claims: list[str] = []
        for index, usage in enumerate(claim_usage):
            label = f"claim_usage[{index}]"
            if not isinstance(usage, dict):
                errors.append(f"{label} must be an object")
                continue
            claim_id = usage.get("claim_id")
            if not isinstance(claim_id, str) or not claim_id:
                errors.append(f"{label}.claim_id must be a non-empty string")
            elif claim_id not in known_claims:
                errors.append(f"{label} references unknown claim {claim_id}")
            else:
                used_claims.append(claim_id)
            locations = usage.get("locations", [])
            if not isinstance(locations, list) or not all(
                isinstance(location, str) and location for location in locations
            ):
                errors.append(f"{label}.locations must be an array of strings")
        if len(used_claims) != len(set(used_claims)):
            errors.append("claim_usage must not contain duplicate claim IDs")

    adapter = record.get("adapter")
    if not isinstance(adapter, dict):
        errors.append("adapter must be an object")
    else:
        if not isinstance(adapter.get("id"), str) or not adapter["id"].strip():
            errors.append("adapter.id must be a non-empty string")
        if adapter.get("mode") not in {"human", "model", "tool"}:
            errors.append("adapter.mode must be human, model, or tool")

    addressed = record.get("addressed_findings", [])
    if not isinstance(addressed, list) or not all(
        isinstance(finding_id, str) and finding_id for finding_id in addressed
    ):
        errors.append("addressed_findings must be an array of finding IDs")
    elif len(addressed) != len(set(addressed)):
        errors.append("addressed_findings must not contain duplicates")
    return errors


def validate_visual_assets(record: dict) -> list[str]:
    errors: list[str] = []
    for index, visual in enumerate(record.get("visuals", [])):
        label = f"visuals[{index}]"
        for field in ("asset", "purpose", "caption", "alt_text", "provenance"):
            if not isinstance(visual.get(field), str) or not visual[field].strip():
                errors.append(f"{label}.{field} must be a non-empty string")
    return errors


def validate_visual_record(record: dict) -> list[str]:
    errors: list[str] = []
    for field in ("run_id", "artifact_revision", "visual_revision"):
        if not isinstance(record.get(field), str) or not record[field].strip():
            errors.append(f"{field} must be a non-empty string")
    items = record.get("items")
    if not isinstance(items, list) or not items:
        errors.append("items must be a non-empty array")
    elif not all(isinstance(item, dict) for item in items):
        errors.append("items must contain only objects")
    else:
        errors.extend(validate_visual_assets({"visuals": items}))
    adapter = record.get("adapter")
    if not isinstance(adapter, dict):
        errors.append("adapter must be an object")
    else:
        if not isinstance(adapter.get("id"), str) or not adapter["id"].strip():
            errors.append("adapter.id must be a non-empty string")
        if adapter.get("mode") not in {"human", "model", "tool"}:
            errors.append("adapter.mode must be human, model, or tool")
    return errors


def apply_visual_record(repository: dict, run: dict, record: dict) -> dict:
    require_valid_run(repository, run)
    require_transition(run, "visual", {"edited"})
    errors = validate_visual_record(record)
    if errors:
        raise HwrError("VISUAL_RECORD_INVALID", "Visual record is invalid", errors)
    require_matching_run_id(run, record)

    if run["gates"]["media"].get("decision") != "selected":
        raise HwrError(
            "VISUAL_NOT_SELECTED",
            "A visual record may only be applied when the media decision is selected",
        )
    current_revision = run["output_package"]["publication_copy"].get(
        "artifact_revision"
    )
    if record["artifact_revision"] != current_revision:
        raise HwrError(
            "ARTIFACT_REVISION_MISMATCH",
            "Visuals must target the current frozen artifact revision",
        )
    current_visuals = run["output_package"]["visual_assets"]
    if current_visuals.get("status") in {"produced", "reviewed"}:
        raise HwrError(
            "VISUAL_ALREADY_PRODUCED",
            "The current artifact revision already has produced visual assets",
        )

    updated = copy.deepcopy(run)
    previous_state = updated["state"]
    updated["output_package"]["visual_assets"] = {
        "status": "produced",
        "artifact_revision": record["artifact_revision"],
        "visual_revision": record["visual_revision"],
        "items": record["items"],
        "adapter": record["adapter"],
    }
    updated["next_actions"] = [
        "Export a review adapter packet and run every declared reviewer."
    ]
    append_history(
        updated,
        "visual-assets-applied",
        previous_state,
        updated["state"],
        record["visual_revision"],
    )
    return updated


def apply_artifact_record(repository: dict, run: dict, record: dict) -> dict:
    require_valid_run(repository, run)
    errors = validate_artifact_record(run, record)
    if errors:
        raise HwrError("ARTIFACT_INVALID", "Artifact record is invalid", errors)
    require_matching_run_id(run, record)

    stage = record["stage"]
    expected_states = {
        "draft": {"media-decided"},
        "edit": {"drafted"},
        "revision": {"revising"},
    }
    require_transition(run, stage, expected_states[stage])

    current_publication = run["output_package"]["publication_copy"]
    if stage in {"edit", "revision"}:
        current_revision = current_publication.get("artifact_revision")
        if record.get("parent_revision") != current_revision:
            raise HwrError(
                "PARENT_REVISION_MISMATCH",
                "Artifact parent_revision does not match the current artifact",
                [
                    {
                        "current": current_revision,
                        "submitted": record.get("parent_revision"),
                    }
                ],
            )
    if record["artifact_revision"] == current_publication.get("artifact_revision"):
        raise HwrError(
            "ARTIFACT_REVISION_REUSED",
            "A transition must create a new artifact revision",
        )

    expected_content_type = run["resolution"]["inputs"]["content_type"]
    if record["publication"]["content_type"] != expected_content_type:
        raise HwrError(
            "CONTENT_TYPE_MISMATCH",
            "Artifact content type does not match the resolved task",
        )

    claim_by_id = {
        claim["id"]: claim
        for claim in run["claim_ledger"]
        if isinstance(claim, dict) and isinstance(claim.get("id"), str)
    }
    for usage in record.get("claim_usage", []):
        claim = claim_by_id[usage["claim_id"]]
        if claim.get("disposition") == "omit" or claim.get("classification") == "unknown":
            raise HwrError(
                "PROHIBITED_CLAIM_USED",
                f"Artifact uses claim {usage['claim_id']} that must not be drafted",
            )

    visual_errors = validate_visual_assets(record)
    if visual_errors:
        raise HwrError(
            "VISUAL_ASSETS_INVALID",
            "Visual assets are incomplete or inconsistent",
            visual_errors,
        )
    if stage != "revision" and record.get("addressed_findings"):
        raise HwrError(
            "UNEXPECTED_REVISION_MAPPING",
            "Only a revision artifact may address review findings",
        )

    updated = copy.deepcopy(run)
    previous_state = updated["state"]
    publication_status = "drafted" if stage == "draft" else "edited"
    updated["output_package"]["publication_copy"] = {
        "status": publication_status,
        "artifact_revision": record["artifact_revision"],
        "content_type": record["publication"]["content_type"],
        "content": record["publication"]["text"],
        "metadata": record["publication"].get("metadata", {}),
        "claim_usage": record.get("claim_usage", []),
        "adapter": record["adapter"],
    }
    if record.get("visuals"):
        updated["output_package"]["visual_assets"] = {
            "status": "produced",
            "artifact_revision": record["artifact_revision"],
            "visual_revision": f"embedded:{record['artifact_revision']}",
            "items": record["visuals"],
            "adapter": record["adapter"],
        }
    elif (
        stage in {"edit", "revision"}
        and updated["gates"]["media"].get("decision") == "selected"
    ):
        updated["output_package"]["visual_assets"] = {
            "status": "pending-production",
            "items": [],
        }

    if stage == "draft":
        updated["state"] = "drafted"
        updated["next_actions"] = [
            "Edit the frozen draft for evidence, structure, language, format, and platform."
        ]
    elif stage == "edit":
        updated["state"] = "edited"
        if (
            updated["gates"]["media"].get("decision") == "selected"
            and updated["output_package"]["visual_assets"].get("status")
            == "pending-production"
        ):
            updated["next_actions"] = [
                "Export a visual adapter packet and produce the selected visual assets."
            ]
        else:
            updated["next_actions"] = [
                "Export a review adapter packet and run every declared reviewer."
            ]
    else:
        previous_report = updated["output_package"]["review_report"]
        findings = previous_report.get("findings", [])
        finding_by_id = {
            finding.get("id"): finding
            for finding in findings
            if isinstance(finding, dict)
        }
        addressed = set(record.get("addressed_findings", []))
        unknown_findings = sorted(addressed - finding_by_id.keys())
        if unknown_findings:
            raise HwrError(
                "UNKNOWN_FINDING",
                "Revision references unknown findings",
                unknown_findings,
            )
        if not addressed:
            raise HwrError(
                "EMPTY_REVISION_MAPPING",
                "A revision must identify at least one addressed finding",
            )
        for finding_id in addressed:
            finding_by_id[finding_id]["status"] = "fixed"
        remaining_material = [
            finding
            for finding in findings
            if finding.get("severity") in {"blocker", "major"}
            and finding.get("status") in MATERIAL_FINDING_STATUSES
        ]
        previous_report["status"] = "awaiting-re-review"
        previous_report["pending_artifact_revision"] = record["artifact_revision"]
        for reviewer in updated["review_plan"]:
            reviewer["status"] = "pending"
        updated["state"] = "revising" if remaining_material else "edited"
        if remaining_material:
            updated["next_actions"] = [
                "Address the remaining blocker and major findings."
            ]
        elif (
            updated["gates"]["media"].get("decision") == "selected"
            and updated["output_package"]["visual_assets"].get("status")
            == "pending-production"
        ):
            updated["next_actions"] = [
                "Export a visual adapter packet and produce the selected visual assets."
            ]
        else:
            updated["next_actions"] = [
                "Re-run affected reviewers against the new artifact revision."
            ]

    revision_summary = updated["output_package"]["revision_summary"]
    revision_summary["status"] = "updated"
    revision_summary.setdefault("changes", []).append(
        {
            "stage": stage,
            "artifact_revision": record["artifact_revision"],
            "parent_revision": record.get("parent_revision"),
            "addressed_findings": record.get("addressed_findings", []),
        }
    )
    append_history(
        updated,
        f"{stage}-artifact-applied",
        previous_state,
        updated["state"],
        record["artifact_revision"],
    )
    return updated


def validate_review_record(repository: dict, run: dict, record: dict) -> list[str]:
    errors: list[str] = []
    for field in ("run_id", "artifact_revision", "review_revision"):
        if not isinstance(record.get(field), str) or not record[field].strip():
            errors.append(f"{field} must be a non-empty string")
    if record.get("readiness_candidate") not in ALLOWED_READINESS_CANDIDATES:
        errors.append("readiness_candidate is invalid")

    expected_reviewers = {
        review["reviewer_id"] for review in run.get("review_plan", [])
    }
    reviewers = record.get("reviewers")
    observed_reviewers: list[str] = []
    if not isinstance(reviewers, list):
        errors.append("reviewers must be an array")
    else:
        for index, reviewer in enumerate(reviewers):
            label = f"reviewers[{index}]"
            if not isinstance(reviewer, dict):
                errors.append(f"{label} must be an object")
                continue
            reviewer_id = reviewer.get("reviewer_id")
            if not isinstance(reviewer_id, str) or not reviewer_id:
                errors.append(f"{label}.reviewer_id must be a non-empty string")
            else:
                observed_reviewers.append(reviewer_id)
                obj = repository["by_id"].get(reviewer_id)
                if obj is None or obj.get("kind") != "reviewer":
                    errors.append(f"{label} references an unknown reviewer")
            if reviewer.get("status") not in ALLOWED_REVIEW_STATUSES:
                errors.append(f"{label}.status is invalid")
        if len(observed_reviewers) != len(set(observed_reviewers)):
            errors.append("reviewers must not contain duplicates")
        missing = sorted(expected_reviewers - set(observed_reviewers))
        extra = sorted(set(observed_reviewers) - expected_reviewers)
        if missing:
            errors.append(f"reviewers missing required IDs: {', '.join(missing)}")
        if extra:
            errors.append(f"reviewers contain undeclared IDs: {', '.join(extra)}")

    known_claims = {
        claim.get("id")
        for claim in run.get("claim_ledger", [])
        if isinstance(claim, dict)
    }
    findings = record.get("findings")
    finding_ids: list[str] = []
    if not isinstance(findings, list):
        errors.append("findings must be an array")
    else:
        required_finding_fields = {
            "id",
            "reviewer",
            "severity",
            "location",
            "summary",
            "reason",
            "rule",
            "claim_ids",
            "correction",
            "status",
        }
        for index, finding in enumerate(findings):
            label = f"findings[{index}]"
            if not isinstance(finding, dict):
                errors.append(f"{label} must be an object")
                continue
            missing_fields = required_finding_fields - finding.keys()
            if missing_fields:
                errors.append(
                    f"{label} missing fields: {', '.join(sorted(missing_fields))}"
                )
                continue
            finding_id = finding.get("id")
            if not isinstance(finding_id, str) or not finding_id:
                errors.append(f"{label}.id must be a non-empty string")
            else:
                finding_ids.append(finding_id)
            if finding.get("reviewer") not in expected_reviewers:
                errors.append(f"{label}.reviewer is not in the review plan")
            if finding.get("severity") not in ALLOWED_FINDING_SEVERITIES:
                errors.append(f"{label}.severity is invalid")
            if finding.get("status") not in ALLOWED_FINDING_STATUSES:
                errors.append(f"{label}.status is invalid")
            for field in ("location", "summary", "reason", "rule", "correction"):
                if not isinstance(finding.get(field), str) or not finding[field].strip():
                    errors.append(f"{label}.{field} must be a non-empty string")
            claim_ids = finding.get("claim_ids")
            if not isinstance(claim_ids, list) or not all(
                isinstance(claim_id, str) and claim_id for claim_id in claim_ids
            ):
                errors.append(f"{label}.claim_ids must be an array")
            else:
                unknown = sorted(set(claim_ids) - known_claims)
                if unknown:
                    errors.append(
                        f"{label} references unknown claims: {', '.join(unknown)}"
                    )
        if len(finding_ids) != len(set(finding_ids)):
            errors.append("findings must not contain duplicate IDs")

    limitations = record.get("limitations", [])
    if not isinstance(limitations, list) or not all(
        isinstance(item, str) and item for item in limitations
    ):
        errors.append("limitations must be an array of strings")
    adapter = record.get("adapter")
    if not isinstance(adapter, dict):
        errors.append("adapter must be an object")
    elif not isinstance(adapter.get("id"), str) or not adapter["id"].strip():
        errors.append("adapter.id must be a non-empty string")
    return errors


def apply_review_record(repository: dict, run: dict, record: dict) -> dict:
    require_valid_run(repository, run)
    require_transition(run, "review", {"edited"})
    if run["gates"]["media"].get("decision") == "selected":
        visual_assets = run["output_package"]["visual_assets"]
        if visual_assets.get("status") != "produced" or not visual_assets.get("items"):
            raise HwrError(
                "VISUAL_PRODUCTION_INCOMPLETE",
                "Selected visuals must be produced before review",
            )
    errors = validate_review_record(repository, run, record)
    if errors:
        raise HwrError("REVIEW_INVALID", "Review record is invalid", errors)
    require_matching_run_id(run, record)
    current_revision = run["output_package"]["publication_copy"].get(
        "artifact_revision"
    )
    if record["artifact_revision"] != current_revision:
        raise HwrError(
            "ARTIFACT_REVISION_MISMATCH",
            "Review must target the current frozen artifact revision",
        )
    input_failures = [
        reviewer["reviewer_id"]
        for reviewer in record["reviewers"]
        if reviewer["status"] == "input-error"
    ]
    if input_failures:
        raise HwrError(
            "REVIEW_INPUT_FAILURE",
            "Review cannot complete because reviewers reported missing inputs",
            input_failures,
        )

    previous_findings = run["output_package"]["review_report"].get("findings", [])
    required_previous = {
        finding.get("id")
        for finding in previous_findings
        if isinstance(finding, dict)
        and finding.get("severity") in {"blocker", "major"}
    }
    submitted_findings = {finding["id"] for finding in record["findings"]}
    missing_previous = sorted(required_previous - submitted_findings)
    if missing_previous:
        raise HwrError(
            "REVIEW_HISTORY_INCOMPLETE",
            "Re-review omitted prior blocker or major findings",
            missing_previous,
        )

    material_findings = [
        finding
        for finding in record["findings"]
        if finding["severity"] in {"blocker", "major"}
        and finding["status"] in MATERIAL_FINDING_STATUSES
    ]
    readiness = record["readiness_candidate"]
    if material_findings and readiness != "not-ready":
        raise HwrError(
            "READINESS_CONFLICT",
            "Open material findings require readiness_candidate not-ready",
        )
    if not material_findings and readiness not in {
        "publication-ready",
        "ready-with-minor-findings",
    }:
        raise HwrError(
            "READINESS_CONFLICT",
            "A complete material review requires a readiness candidate",
        )
    findings_by_reviewer: dict[str, list[dict]] = {}
    for finding in record["findings"]:
        findings_by_reviewer.setdefault(finding["reviewer"], []).append(finding)
    failed_without_material_finding = [
        reviewer["reviewer_id"]
        for reviewer in record["reviewers"]
        if reviewer["status"] == "fail"
        and not any(
            finding["severity"] in {"blocker", "major"}
            and finding["status"] in MATERIAL_FINDING_STATUSES
            for finding in findings_by_reviewer.get(reviewer["reviewer_id"], [])
        )
    ]
    if failed_without_material_finding:
        raise HwrError(
            "REVIEW_STATUS_CONFLICT",
            "A failed reviewer must return an unresolved blocker or major finding",
            failed_without_material_finding,
        )

    updated = copy.deepcopy(run)
    previous_state = updated["state"]
    reviewer_status = {
        reviewer["reviewer_id"]: reviewer["status"]
        for reviewer in record["reviewers"]
    }
    for planned in updated["review_plan"]:
        planned["status"] = reviewer_status[planned["reviewer_id"]]
    updated["output_package"]["review_report"] = {
        "status": "complete",
        "artifact_revision": record["artifact_revision"],
        "review_revision": record["review_revision"],
        "reviewers": record["reviewers"],
        "findings": record["findings"],
        "limitations": record.get("limitations", []),
        "readiness_candidate": readiness,
        "adapter": record["adapter"],
    }
    if (
        updated["gates"]["media"].get("decision") == "selected"
        and reviewer_status.get("reviewer.visual") == "pass"
    ):
        updated["output_package"]["visual_assets"]["status"] = "reviewed"
    updated["state"] = "revising" if material_findings else "reviewed"
    updated["next_actions"] = (
        ["Revise the artifact against every open blocker and major finding."]
        if material_findings
        else ["Finalize the reviewed output package."]
    )
    append_history(
        updated,
        "review-applied",
        previous_state,
        updated["state"],
        record["review_revision"],
    )
    return updated


def finalize_run(repository: dict, run: dict) -> dict:
    require_valid_run(repository, run)
    require_transition(run, "finalize", {"reviewed"})
    report = run["output_package"]["review_report"]
    if report.get("status") != "complete":
        raise HwrError("REVIEW_INCOMPLETE", "Finalization requires a complete review")
    incomplete_reviewers = [
        reviewer["reviewer_id"]
        for reviewer in run["review_plan"]
        if reviewer.get("status") != "pass"
    ]
    if incomplete_reviewers:
        raise HwrError(
            "REVIEW_INCOMPLETE",
            "Every required reviewer must pass before finalization",
            incomplete_reviewers,
        )
    material_findings = [
        finding
        for finding in report.get("findings", [])
        if finding.get("severity") in {"blocker", "major"}
        and finding.get("status") in MATERIAL_FINDING_STATUSES
    ]
    if material_findings:
        raise HwrError(
            "MATERIAL_FINDINGS_OPEN",
            "Open blocker or major findings prevent finalization",
            [finding.get("id") for finding in material_findings],
        )
    if run["gates"]["media"].get("decision") == "selected":
        visual_assets = run["output_package"]["visual_assets"]
        if visual_assets.get("status") != "reviewed" or not visual_assets.get("items"):
            raise HwrError(
                "VISUAL_REVIEW_INCOMPLETE",
                "Selected visuals must exist and pass visual review",
            )

    updated = copy.deepcopy(run)
    previous_state = updated["state"]
    updated["state"] = "ready"
    updated["output_package"]["publication_copy"]["status"] = "ready"
    updated["output_package"]["source_notes"]["status"] = "ready"
    updated["output_package"]["review_report"]["readiness"] = report[
        "readiness_candidate"
    ]
    updated["output_package"]["audit"]["status"] = "complete"
    updated["next_actions"] = [
        "Publish or hand off the separated output package without internal notes in public copy."
    ]
    append_history(
        updated,
        "run-finalized",
        previous_state,
        updated["state"],
        report.get("review_revision"),
    )
    return updated


def build_adapter_packet(repository: dict, run: dict, stage: str) -> dict:
    require_valid_run(repository, run)
    expected_states = {
        "design": {"context-ready"},
        "draft": {"media-decided"},
        "edit": {"drafted"},
        "visual": {"edited"},
        "review": {"edited"},
        "revision": {"revising"},
    }
    if stage not in expected_states:
        raise HwrError("UNKNOWN_ADAPTER_STAGE", f"Unknown adapter stage: {stage}")
    require_transition(run, f"adapter-packet:{stage}", expected_states[stage])

    schema_by_stage = {
        "design": "schemas/content-design.schema.json",
        "draft": "schemas/artifact-record.schema.json",
        "edit": "schemas/artifact-record.schema.json",
        "visual": "schemas/visual-assets-record.schema.json",
        "review": "schemas/review-report.schema.json",
        "revision": "schemas/artifact-record.schema.json",
    }
    instructions = {
        "design": [
            "Define the minimum sufficient structure from the reader promise.",
            "Map section purposes to known claim IDs; do not introduce new facts.",
        ],
        "draft": [
            "Write for meaning before engagement optimization.",
            "Preserve claim classifications, source scope, qualifications, and disclosures.",
        ],
        "edit": [
            "Edit the frozen draft without removing evidence boundaries or required disclosures.",
            "Return a new artifact revision; selected visual assets may be produced separately before review.",
        ],
        "visual": [
            "Produce only the selected media brief for the current frozen artifact revision.",
            "Keep conceptual status, evidence limits, provenance, caption, and alt text explicit.",
        ],
        "review": [
            "Evaluate one frozen artifact revision against every declared reviewer scope.",
            "Return structured findings; do not silently rewrite the artifact.",
        ],
        "revision": [
            "Address named findings with the smallest useful correction.",
            "Return a new artifact revision and preserve unaffected valid material.",
        ],
    }
    current_publication = run["output_package"]["publication_copy"]
    current_revision = current_publication.get("artifact_revision", "none")
    if stage == "visual":
        if run["gates"]["media"].get("decision") != "selected":
            raise HwrError(
                "VISUAL_NOT_SELECTED",
                "A visual packet requires a selected media decision",
            )
        current_visuals = run["output_package"]["visual_assets"]
        if current_visuals.get("status") in {"produced", "reviewed"}:
            raise HwrError(
                "VISUAL_ALREADY_PRODUCED",
                "The current artifact revision already has produced visual assets",
            )
    if stage == "review" and run["gates"]["media"].get("decision") == "selected":
        current_visuals = run["output_package"]["visual_assets"]
        if current_visuals.get("status") != "produced" or not current_visuals.get("items"):
            raise HwrError(
                "VISUAL_PRODUCTION_INCOMPLETE",
                "Selected visuals must be produced before a review packet is exported",
            )
    return {
        "protocol_version": "1.0",
        "packet_id": f"{run['run_id']}:{stage}:{current_revision}",
        "stage": stage,
        "run_id": run["run_id"],
        "input_state": run["state"],
        "required_output_schema": schema_by_stage[stage],
        "instructions": instructions[stage],
        "task": run["task"],
        "module_manifest": [
            {
                "id": object_id,
                "kind": repository["by_id"][object_id]["kind"],
                "path": repository["by_id"][object_id]["path"],
                "content": (
                    repository["root"] / repository["by_id"][object_id]["path"]
                ).read_text(encoding="utf-8"),
            }
            for object_id in run["resolution"]["dependency_order"]
        ],
        "sources": run["sources"],
        "claim_ledger": run["claim_ledger"],
        "gates": run["gates"],
        "content_design": run["content_design"],
        "current_artifact": (
            current_publication
            if current_publication.get("status") != "not-started"
            else None
        ),
        "visual_assets": run["output_package"]["visual_assets"],
        "review_context": run["output_package"]["review_report"],
    }


def doctor(repository: dict) -> dict:
    return {
        "ready": True,
        "mode": "offline",
        "auth_required": False,
        "repository": str(repository["root"]),
        "spec_revision": repository["spec_revision"],
        "registry_revision": repository["registry_revision"],
        "object_count": len(repository["objects"]),
        "indexes": {
            name: len(entries)
            for name, entries in repository["indexes"].items()
        },
        "capabilities": [
            "registry-read",
            "generated-registry-index",
            "benchmark-runner",
            "reviewed-example-coverage",
            "release-verification",
            "visual-benchmark-acceptance",
            "object-discovery",
            "module-resolution",
            "local-source-snapshots",
            "context-gate",
            "claim-ledger-check",
            "media-decision-check",
            "review-plan",
            "adapter-packets",
            "visual-production-stage",
            "subprocess-adapter-runtime",
            "persisted-editorial-workflow",
            "lifecycle-transitions",
            "readiness-gate",
            "run-record-validation",
        ],
        "model_adapter": "not-configured",
        "provider_adapters": [
            {
                "id": "openai.responses+images",
                "status": "available-not-configured",
                "network_default": "disabled",
            }
        ],
    }
