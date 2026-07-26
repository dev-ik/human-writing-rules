#!/usr/bin/env python3
"""Validate reviewed examples and registry-wide topic/platform coverage."""

import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any, Optional


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "examples/reviewed-examples.json"
CATALOG_SCHEMA = (
    "https://human-writing-rules.example/schemas/"
    "reviewed-example-catalog.schema.json"
)
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_EXAMPLE_BYTES = 512 * 1024
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
BASE_REVIEWERS = {
    "reviewer.source",
    "reviewer.language",
    "reviewer.human-signals",
    "reviewer.format",
    "reviewer.topic",
    "reviewer.platform",
    "reviewer.editor",
}
CATALOG_FIELDS = {
    "$schema",
    "version",
    "spec_revision",
    "coverage_policy",
    "required_sections",
    "required_reviewers",
    "examples",
}
ENTRY_FIELDS = {
    "id",
    "revision",
    "status",
    "language",
    "content_type",
    "topic",
    "platform",
    "visual_mode",
    "visual_decision",
    "path",
    "sha256",
    "reviewers",
    "limitations",
}
CONTENT_TYPES = {"article", "social-post"}
VISUAL_MODES = {"none", "auto", "required"}
VISUAL_DECISIONS = {"none", "selected-brief", "selected-asset", "blocked"}


class ReviewedExampleError(Exception):
    pass


def read_bounded(path: Path, limit: int, label: str) -> bytes:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise ReviewedExampleError(f"{label} cannot be read: {path}") from exc
    if size > limit:
        raise ReviewedExampleError(f"{label} exceeds {limit} bytes: {path}")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise ReviewedExampleError(f"{label} cannot be read: {path}") from exc


def read_bounded_json(path: Path, label: str) -> dict:
    raw = read_bounded(path, MAX_JSON_BYTES, label)
    try:
        value = json.loads(raw.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise ReviewedExampleError(f"{label} is not UTF-8: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReviewedExampleError(
            f"{label} contains invalid JSON at {exc.lineno}:{exc.colno}: {path}"
        ) from exc
    if not isinstance(value, dict):
        raise ReviewedExampleError(f"{label} root must be an object: {path}")
    return value


def validate_exact_fields(
    value: dict,
    fields: set[str],
    label: str,
    errors: list[str],
) -> None:
    missing = fields - value.keys()
    unknown = value.keys() - fields
    if missing:
        errors.append(f"{label} missing fields: {', '.join(sorted(missing))}")
    if unknown:
        errors.append(f"{label} has unknown fields: {', '.join(sorted(unknown))}")


def validate_string_list(
    value: Any,
    label: str,
    errors: list[str],
    *,
    allow_empty: bool = True,
) -> list[str]:
    if (
        not isinstance(value, list)
        or not all(isinstance(item, str) and item for item in value)
        or len(value) != len(set(value))
        or (not allow_empty and not value)
    ):
        errors.append(f"{label} must be a unique array of non-empty strings")
        return []
    return value


def resolve_repository_file(
    root: Path,
    relative_path: Any,
) -> Optional[Path]:
    if not isinstance(relative_path, str) or not relative_path:
        return None
    pure_path = PurePosixPath(relative_path)
    if pure_path.is_absolute() or ".." in pure_path.parts:
        return None
    try:
        resolved = (root / pure_path).resolve(strict=True)
        resolved.relative_to(root.resolve())
    except (OSError, ValueError):
        return None
    return resolved if resolved.is_file() else None


def load_index_values(root: Path, filename: str, key: str) -> set[str]:
    data = read_bounded_json(root / "registry" / filename, f"registry/{filename}")
    entries = data.get(key)
    if not isinstance(entries, list):
        raise ReviewedExampleError(f"registry/{filename} {key} must be an array")
    values = {
        entry.get("id")
        for entry in entries
        if isinstance(entry, dict) and isinstance(entry.get("id"), str)
    }
    if len(values) != len(entries):
        raise ReviewedExampleError(f"registry/{filename} contains invalid IDs")
    return values


def extract_section(text: str, heading: str, next_heading: Optional[str]) -> str:
    start_token = f"## {heading}\n"
    start = text.find(start_token)
    if start < 0:
        return ""
    start += len(start_token)
    if next_heading is None:
        return text[start:]
    end = text.find(f"\n## {next_heading}\n", start)
    return text[start:] if end < 0 else text[start:end]


def validate_task_marker(
    task_section: str,
    marker: str,
    expected: str,
    label: str,
    errors: list[str],
) -> None:
    pattern = re.compile(
        rf"(?im)^-\s*{re.escape(marker)}:\s*`?([^`\n]+)`?\s*$"
    )
    match = pattern.search(task_section)
    if match is None:
        errors.append(f"{label} task framing is missing {marker}")
        return
    actual = match.group(1).strip().lower()
    if expected.lower() not in actual:
        errors.append(
            f"{label} task framing {marker}={actual!r}, expected "
            f"to contain {expected!r}"
        )


def validate_example_markdown(
    entry: dict,
    text: str,
    required_sections: list[str],
    label: str,
    errors: list[str],
) -> None:
    positions: list[int] = []
    for section in required_sections:
        token = f"\n## {section}\n"
        position = text.find(token)
        if position < 0:
            errors.append(f"{label} is missing section {section!r}")
        positions.append(position)
    present_positions = [position for position in positions if position >= 0]
    if present_positions != sorted(present_positions):
        errors.append(f"{label} required sections are out of order")

    final_artifact = extract_section(text, "Final artifact", "Media decision")
    if not final_artifact.strip():
        errors.append(f"{label} Final artifact must not be empty")
    elif entry.get("content_type") == "article" and not re.search(
        r"(?m)^#\s+\S",
        final_artifact,
    ):
        errors.append(f"{label} article Final artifact must contain a title")
    review_result = extract_section(text, "Review result", None)
    revision = entry.get("revision")
    if isinstance(revision, str) and revision not in review_result:
        errors.append(f"{label} Review result does not name revision {revision!r}")
    if "Readiness:" not in review_result:
        errors.append(f"{label} Review result must contain Readiness")

    task_section = extract_section(text, "Task framing", "Resolved modules")
    validate_task_marker(
        task_section,
        "Content type",
        str(entry.get("content_type", "")),
        label,
        errors,
    )
    validate_task_marker(
        task_section,
        "Topic",
        str(entry.get("topic", "")),
        label,
        errors,
    )
    platform_expected = str(entry.get("platform", ""))
    validate_task_marker(
        task_section,
        "Platform",
        platform_expected,
        label,
        errors,
    )
    validate_task_marker(
        task_section,
        "Visual mode",
        str(entry.get("visual_mode", "")),
        label,
        errors,
    )

    resolved = extract_section(text, "Resolved modules", "Evidence map")
    expected_modules = (
        f"format.{entry.get('content_type')}.foundation",
        f"topic.{entry.get('topic')}.foundation",
        f"platform.{entry.get('platform')}.foundation",
        f"language.{entry.get('language')}.foundation",
    )
    for module in expected_modules:
        if module not in resolved:
            errors.append(f"{label} Resolved modules is missing {module}")

    media = extract_section(text, "Media decision", "Source notes")
    decision = entry.get("visual_decision")
    if decision == "selected-brief" and not re.search(
        r"(?i)\b(brief|visual handoff)\b",
        media,
    ):
        errors.append(f"{label} selected-brief requires a visual handoff or brief")
    if decision == "selected-asset" and not re.search(
        r"(?i)\b(asset|visual assets?)\b",
        media,
    ):
        errors.append(f"{label} selected-asset requires an asset handoff")
    if decision == "none" and not re.search(
        r"(?i)\b(no visual|no generated visual|none|omit|omission)\b",
        media,
    ):
        errors.append(f"{label} decision none is not explicit in Media decision")


def validate_reviewed_example_catalog(
    catalog: Any,
    root: Path = ROOT,
) -> tuple[dict[str, int], list[str]]:
    errors: list[str] = []
    empty_summary = {
        "examples": 0,
        "topics_covered": 0,
        "platforms_covered": 0,
        "languages_covered": 0,
        "articles": 0,
        "social_posts": 0,
    }
    if not isinstance(catalog, dict):
        return empty_summary, ["reviewed example catalog must be an object"]
    validate_exact_fields(catalog, CATALOG_FIELDS, "reviewed catalog", errors)
    if catalog.get("$schema") != CATALOG_SCHEMA:
        errors.append("reviewed catalog has an unknown $schema")
    for field in ("version", "spec_revision"):
        if not isinstance(catalog.get(field), str) or not catalog[field].strip():
            errors.append(f"reviewed catalog {field} must be a non-empty string")

    try:
        rfc_index = read_bounded_json(root / "registry/rfcs.json", "RFC index")
        topics = load_index_values(root, "topics.json", "topics")
        platforms = load_index_values(root, "platforms.json", "platforms")
        languages = load_index_values(root, "languages.json", "languages")
        formats = load_index_values(root, "formats.json", "formats")
    except ReviewedExampleError as exc:
        return empty_summary, errors + [str(exc)]
    if catalog.get("spec_revision") != rfc_index.get("version"):
        errors.append(
            "reviewed catalog spec_revision does not match registry/rfcs.json"
        )

    coverage_policy = catalog.get("coverage_policy")
    if not isinstance(coverage_policy, dict):
        errors.append("reviewed catalog coverage_policy must be an object")
    else:
        validate_exact_fields(
            coverage_policy,
            {"topics", "platforms", "cross_product_required"},
            "reviewed catalog coverage_policy",
            errors,
        )
        for field in ("topics", "platforms"):
            if (
                coverage_policy.get(field)
                != "every-registered-value-at-least-once"
            ):
                errors.append(
                    f"reviewed catalog coverage_policy.{field} is invalid"
                )
        if coverage_policy.get("cross_product_required") is not False:
            errors.append(
                "reviewed catalog coverage_policy.cross_product_required "
                "must be false"
            )

    required_sections = validate_string_list(
        catalog.get("required_sections"),
        "reviewed catalog required_sections",
        errors,
        allow_empty=False,
    )
    expected_sections = {
        "Task framing",
        "Resolved modules",
        "Evidence map",
        "Context gate",
        "Content design",
        "Final artifact",
        "Media decision",
        "Source notes",
        "Review result",
    }
    if set(required_sections) != expected_sections:
        errors.append("reviewed catalog required_sections is not canonical")
    required_reviewers = set(
        validate_string_list(
            catalog.get("required_reviewers"),
            "reviewed catalog required_reviewers",
            errors,
            allow_empty=False,
        )
    )
    if required_reviewers != BASE_REVIEWERS:
        errors.append("reviewed catalog required_reviewers is not canonical")

    entries = catalog.get("examples")
    if not isinstance(entries, list) or not entries:
        return empty_summary, errors + [
            "reviewed catalog examples must be a non-empty array"
        ]

    ids: set[str] = set()
    paths: set[str] = set()
    covered_topics: set[str] = set()
    covered_platforms: set[str] = set()
    covered_languages: set[str] = set()
    counts = {"article": 0, "social-post": 0}
    for index, entry in enumerate(entries):
        label = f"reviewed catalog examples[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{label} must be an object")
            continue
        validate_exact_fields(entry, ENTRY_FIELDS, label, errors)
        for field in ("id", "revision"):
            if not isinstance(entry.get(field), str) or not entry[field].strip():
                errors.append(f"{label}.{field} must be a non-empty string")
        entry_id = entry.get("id")
        if isinstance(entry_id, str):
            if entry_id in ids:
                errors.append(f"duplicate reviewed example id: {entry_id}")
            ids.add(entry_id)
        if entry.get("status") != "reviewed":
            errors.append(f"{label}.status must be reviewed")

        for field, allowed in (
            ("language", languages),
            ("content_type", formats & CONTENT_TYPES),
            ("topic", topics),
            ("platform", platforms),
        ):
            value = entry.get(field)
            if value not in allowed:
                errors.append(f"{label}.{field} references unknown value {value!r}")
        if entry.get("topic") in topics:
            covered_topics.add(entry["topic"])
        if entry.get("platform") in platforms:
            covered_platforms.add(entry["platform"])
        if entry.get("language") in languages:
            covered_languages.add(entry["language"])
        if entry.get("content_type") in counts:
            counts[entry["content_type"]] += 1

        mode = entry.get("visual_mode")
        decision = entry.get("visual_decision")
        if mode not in VISUAL_MODES:
            errors.append(f"{label}.visual_mode is invalid")
        if decision not in VISUAL_DECISIONS:
            errors.append(f"{label}.visual_decision is invalid")
        if mode == "none" and decision != "none":
            errors.append(f"{label} visual mode none requires decision none")
        if mode == "required" and decision == "none":
            errors.append(f"{label} required visual cannot decide none")

        reviewers = set(
            validate_string_list(
                entry.get("reviewers"),
                f"{label}.reviewers",
                errors,
                allow_empty=False,
            )
        )
        missing_reviewers = required_reviewers - reviewers
        if missing_reviewers:
            errors.append(
                f"{label} missing reviewers: {', '.join(sorted(missing_reviewers))}"
            )
        if mode in {"auto", "required"} and "reviewer.visual" not in reviewers:
            errors.append(f"{label} requires reviewer.visual")
        validate_string_list(
            entry.get("limitations"),
            f"{label}.limitations",
            errors,
            allow_empty=False,
        )

        relative_path = entry.get("path")
        if isinstance(relative_path, str):
            if relative_path in paths:
                errors.append(f"duplicate reviewed example path: {relative_path}")
            paths.add(relative_path)
        path = resolve_repository_file(root, relative_path)
        if path is None or path.suffix != ".md":
            errors.append(f"{label}.path must resolve to a Markdown file")
            continue
        try:
            raw = read_bounded(path, MAX_EXAMPLE_BYTES, label)
            text = raw.decode("utf-8")
        except (ReviewedExampleError, UnicodeDecodeError) as exc:
            errors.append(f"{label} cannot be loaded as bounded UTF-8: {exc}")
            continue
        sha256 = entry.get("sha256")
        if not isinstance(sha256, str) or not SHA256_RE.fullmatch(sha256):
            errors.append(f"{label}.sha256 must be a lowercase SHA-256 digest")
        actual_sha256 = hashlib.sha256(raw).hexdigest()
        if sha256 != actual_sha256:
            errors.append(
                f"{label}.sha256 mismatch: declared {sha256!r}, "
                f"actual {actual_sha256}"
            )
        validate_example_markdown(
            entry,
            text,
            required_sections,
            label,
            errors,
        )

    missing_topics = topics - covered_topics
    missing_platforms = platforms - covered_platforms
    if missing_topics:
        errors.append(
            "reviewed examples missing topic coverage: "
            + ", ".join(sorted(missing_topics))
        )
    if missing_platforms:
        errors.append(
            "reviewed examples missing platform coverage: "
            + ", ".join(sorted(missing_platforms))
        )

    actual_example_paths = {
        path.relative_to(root).as_posix()
        for language in languages
        for path in (root / "examples" / language).rglob("*.md")
        if path.is_file()
    }
    for orphan in sorted(actual_example_paths - paths):
        errors.append(f"uncataloged reviewed example: {orphan}")
    for missing in sorted(paths - actual_example_paths):
        errors.append(f"catalog path is outside reviewed example tree: {missing}")

    summary = {
        "examples": len(entries),
        "topics_covered": len(covered_topics),
        "platforms_covered": len(covered_platforms),
        "languages_covered": len(covered_languages),
        "articles": counts["article"],
        "social_posts": counts["social-post"],
    }
    return summary, errors


def validate_checked_in_reviewed_examples(
    root: Path = ROOT,
) -> tuple[dict[str, int], list[str]]:
    try:
        catalog = read_bounded_json(
            root / "examples/reviewed-examples.json",
            "reviewed example catalog",
        )
    except ReviewedExampleError as exc:
        return {
            "examples": 0,
            "topics_covered": 0,
            "platforms_covered": 0,
            "languages_covered": 0,
            "articles": 0,
            "social_posts": 0,
        }, [str(exc)]
    return validate_reviewed_example_catalog(catalog, root)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate reviewed example structure and registry coverage."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate the checked-in reviewed example catalog",
    )
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    summary, errors = validate_checked_in_reviewed_examples(ROOT)
    envelope = {"ok": not errors, "data": summary}
    if errors:
        envelope["errors"] = errors
    print(json.dumps(envelope, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
