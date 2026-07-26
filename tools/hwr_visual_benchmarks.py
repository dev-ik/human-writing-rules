#!/usr/bin/env python3
"""Validate checked-in visual benchmark fixtures and acceptance records."""

import argparse
import hashlib
import json
import re
import struct
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Optional

try:
    from .hwr_openai_adapter import AdapterError, validate_png
except ImportError:
    from hwr_openai_adapter import AdapterError, validate_png


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_SCHEMA = (
    "https://human-writing-rules.example/schemas/"
    "visual-benchmark-fixture.schema.json"
)
ACCEPTANCE_SCHEMA = (
    "https://human-writing-rules.example/schemas/"
    "visual-acceptance-record.schema.json"
)
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_ARTIFACT_BYTES = 5 * 1024 * 1024
MAX_ASSET_BYTES = 50 * 1024 * 1024
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
DIMENSIONS = (
    "media_decision",
    "factual_consistency",
    "text_image_alignment",
    "documentary_integrity",
    "platform_handoff",
    "accessibility",
    "rights_provenance",
)
ASSET_DIMENSIONS = DIMENSIONS[1:]
MODES = {"none", "auto", "required"}
DECISIONS = {"none", "selected", "blocked"}
OVERALL_VALUES = {"pass", "fail", "blocked", "incomplete"}
VERDICTS = {"pass", "fail", "not-applicable", "not-reviewed"}
HARD_FAILURE_STATUSES = {"triggered", "not-triggered", "not-reviewed"}
FIXTURE_FIELDS = {
    "$schema",
    "id",
    "revision",
    "spec_revision",
    "fixture_purpose",
    "requested_mode",
    "decision",
    "decision_rationale",
    "artifact",
    "brief",
    "visual_record",
    "asset",
    "acceptance_path",
    "required_dimensions",
    "hard_failures",
    "expected_overall",
    "known_limitations",
}
ACCEPTANCE_FIELDS = {
    "$schema",
    "fixture_id",
    "fixture_revision",
    "acceptance_revision",
    "evaluator",
    "artifact_sha256",
    "asset_sha256",
    "asset_evaluated",
    "dimensions",
    "hard_failures",
    "overall",
    "limitations",
}


class VisualBenchmarkError(Exception):
    pass


def read_bounded(path: Path, limit: int, label: str) -> bytes:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise VisualBenchmarkError(f"{label} cannot be read: {path}") from exc
    if size > limit:
        raise VisualBenchmarkError(f"{label} exceeds {limit} bytes: {path}")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise VisualBenchmarkError(f"{label} cannot be read: {path}") from exc


def read_bounded_json(path: Path, label: str) -> dict:
    raw = read_bounded(path, MAX_JSON_BYTES, label)
    try:
        value = json.loads(raw.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise VisualBenchmarkError(f"{label} is not UTF-8: {path}") from exc
    except json.JSONDecodeError as exc:
        raise VisualBenchmarkError(
            f"{label} contains invalid JSON at {exc.lineno}:{exc.colno}: {path}"
        ) from exc
    if not isinstance(value, dict):
        raise VisualBenchmarkError(f"{label} root must be an object: {path}")
    return value


def resolve_repository_file(
    root: Path,
    relative_path: Any,
    label: str,
) -> Optional[Path]:
    if not isinstance(relative_path, str) or not relative_path:
        return None
    pure_path = PurePosixPath(relative_path)
    if pure_path.is_absolute() or ".." in pure_path.parts:
        return None
    candidate = root / pure_path
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root.resolve())
    except (OSError, ValueError):
        return None
    if not resolved.is_file():
        return None
    return resolved


def digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def validate_sha256(value: Any, label: str, errors: list[str]) -> None:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        errors.append(f"{label} must be a lowercase SHA-256 digest")


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


def validate_file_reference(
    reference: Any,
    root: Path,
    label: str,
    errors: list[str],
    *,
    limit: int,
    allowed_fields: Optional[set[str]] = None,
) -> tuple[Optional[Path], Optional[bytes]]:
    if not isinstance(reference, dict):
        errors.append(f"{label} must be an object")
        return None, None
    validate_exact_fields(
        reference,
        allowed_fields or {"path", "sha256"},
        label,
        errors,
    )
    path = resolve_repository_file(root, reference.get("path"), label)
    if path is None:
        errors.append(f"{label}.path must resolve to a repository file")
        return None, None
    validate_sha256(reference.get("sha256"), f"{label}.sha256", errors)
    try:
        data = read_bounded(path, limit, label)
    except VisualBenchmarkError as exc:
        errors.append(str(exc))
        return path, None
    actual = digest_bytes(data)
    if reference.get("sha256") != actual:
        errors.append(
            f"{label}.sha256 mismatch: declared {reference.get('sha256')!r}, "
            f"actual {actual}"
        )
    return path, data


def png_dimensions(image: bytes) -> tuple[int, int]:
    return struct.unpack(">II", image[16:24])


def validate_visual_record(
    reference: Any,
    asset: dict,
    root: Path,
    label: str,
    errors: list[str],
) -> None:
    path, _ = validate_file_reference(
        reference,
        root,
        f"{label}.visual_record",
        errors,
        limit=MAX_JSON_BYTES,
    )
    if path is None:
        return
    try:
        record = read_bounded_json(path, f"{label}.visual_record")
    except VisualBenchmarkError as exc:
        errors.append(str(exc))
        return
    items = record.get("items")
    if not isinstance(items, list):
        errors.append(f"{label}.visual_record.items must be an array")
        return
    matches = [
        item
        for item in items
        if isinstance(item, dict) and item.get("asset") == asset.get("path")
    ]
    if len(matches) != 1:
        errors.append(
            f"{label}.visual_record must contain exactly one item for "
            f"{asset.get('path')!r}"
        )
        return
    item = matches[0]
    expected_dimensions = f"{asset.get('width')}x{asset.get('height')}"
    for field, expected in (
        ("sha256", asset.get("sha256")),
        ("dimensions", expected_dimensions),
        ("format", "PNG"),
    ):
        if item.get(field) != expected:
            errors.append(
                f"{label}.visual_record item {field}={item.get(field)!r}, "
                f"expected {expected!r}"
            )
    for field in ("caption", "alt_text", "provenance", "disclosure"):
        if not isinstance(item.get(field), str) or not item[field].strip():
            errors.append(f"{label}.visual_record item requires non-empty {field}")


def validate_asset(
    asset: Any,
    root: Path,
    label: str,
    errors: list[str],
) -> int:
    if not isinstance(asset, dict):
        errors.append(f"{label}.asset must be an object")
        return 0
    validate_exact_fields(
        asset,
        {
            "path",
            "media_type",
            "sha256",
            "width",
            "height",
            "provenance",
            "disclosure",
        },
        f"{label}.asset",
        errors,
    )
    if asset.get("media_type") != "image/png":
        errors.append(f"{label}.asset.media_type must be 'image/png'")
    for field in ("provenance", "disclosure"):
        if not isinstance(asset.get(field), str) or not asset[field].strip():
            errors.append(f"{label}.asset.{field} must be a non-empty string")
    for field in ("width", "height"):
        value = asset.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            errors.append(f"{label}.asset.{field} must be a positive integer")

    path, image = validate_file_reference(
        asset,
        root,
        f"{label}.asset",
        errors,
        limit=MAX_ASSET_BYTES,
        allowed_fields={
            "path",
            "media_type",
            "sha256",
            "width",
            "height",
            "provenance",
            "disclosure",
        },
    )
    if path is None or image is None:
        return 0
    try:
        validate_png(image)
    except AdapterError as exc:
        errors.append(f"{label}.asset PNG validation failed: {exc}")
        return 0
    width, height = png_dimensions(image)
    if asset.get("width") != width or asset.get("height") != height:
        errors.append(
            f"{label}.asset dimensions mismatch: declared "
            f"{asset.get('width')}x{asset.get('height')}, actual {width}x{height}"
        )
    return 1


def validate_acceptance_record(
    fixture: dict,
    acceptance: Any,
    label: str,
    errors: list[str],
) -> None:
    if not isinstance(acceptance, dict):
        errors.append(f"{label}.acceptance must be an object")
        return
    validate_exact_fields(
        acceptance,
        ACCEPTANCE_FIELDS,
        f"{label}.acceptance",
        errors,
    )
    if acceptance.get("$schema") != ACCEPTANCE_SCHEMA:
        errors.append(f"{label}.acceptance has an unknown $schema")
    if acceptance.get("fixture_id") != fixture.get("id"):
        errors.append(f"{label}.acceptance fixture_id does not match")
    if acceptance.get("fixture_revision") != fixture.get("revision"):
        errors.append(f"{label}.acceptance fixture_revision does not match")
    if acceptance.get("artifact_sha256") != fixture.get("artifact", {}).get("sha256"):
        errors.append(f"{label}.acceptance artifact_sha256 does not match")
    if (
        not isinstance(acceptance.get("acceptance_revision"), str)
        or not acceptance["acceptance_revision"].strip()
    ):
        errors.append(f"{label}.acceptance acceptance_revision must be non-empty")

    evaluator = acceptance.get("evaluator")
    if not isinstance(evaluator, dict):
        errors.append(f"{label}.acceptance evaluator must be an object")
    else:
        validate_exact_fields(
            evaluator,
            {"id", "type", "independence", "notes"},
            f"{label}.acceptance evaluator",
            errors,
        )
        if not isinstance(evaluator.get("id"), str) or not evaluator["id"].strip():
            errors.append(f"{label}.acceptance evaluator.id must be non-empty")
        if evaluator.get("type") not in {"human", "tool", "fixture"}:
            errors.append(f"{label}.acceptance evaluator.type is invalid")
        if evaluator.get("independence") not in {
            "independent",
            "not-independent",
            "not-applicable",
        }:
            errors.append(f"{label}.acceptance evaluator.independence is invalid")
        if not isinstance(evaluator.get("notes"), str):
            errors.append(f"{label}.acceptance evaluator.notes must be a string")

    decision = fixture.get("decision")
    selected = decision == "selected"
    asset = fixture.get("asset")
    expected_asset_sha = asset.get("sha256") if isinstance(asset, dict) else None
    if acceptance.get("asset_sha256") != expected_asset_sha:
        errors.append(f"{label}.acceptance asset_sha256 does not match")
    if acceptance.get("asset_evaluated") is not selected:
        errors.append(
            f"{label}.acceptance asset_evaluated must be {selected} "
            f"for decision {decision!r}"
        )

    dimensions = acceptance.get("dimensions")
    if not isinstance(dimensions, list):
        errors.append(f"{label}.acceptance dimensions must be an array")
        dimensions = []
    dimension_map: dict[str, dict] = {}
    for index, dimension in enumerate(dimensions):
        if not isinstance(dimension, dict):
            errors.append(f"{label}.acceptance dimensions[{index}] must be an object")
            continue
        validate_exact_fields(
            dimension,
            {"id", "applies", "verdict", "evidence", "findings"},
            f"{label}.acceptance dimensions[{index}]",
            errors,
        )
        dimension_id = dimension.get("id")
        if not isinstance(dimension_id, str) or not dimension_id:
            errors.append(f"{label}.acceptance dimensions[{index}] has invalid id")
            continue
        if dimension_id in dimension_map:
            errors.append(f"{label}.acceptance has duplicate dimension {dimension_id}")
        dimension_map[dimension_id] = dimension
        expected_applies = dimension_id == "media_decision" or (
            selected and dimension_id in ASSET_DIMENSIONS
        )
        if dimension.get("applies") is not expected_applies:
            errors.append(
                f"{label}.acceptance dimension {dimension_id} applies must be "
                f"{expected_applies}"
            )
        verdict = dimension.get("verdict")
        if verdict not in VERDICTS:
            errors.append(
                f"{label}.acceptance dimension {dimension_id} has invalid verdict"
            )
        elif expected_applies and verdict == "not-applicable":
            errors.append(
                f"{label}.acceptance applicable dimension {dimension_id} "
                "cannot be not-applicable"
            )
        elif not expected_applies and verdict != "not-applicable":
            errors.append(
                f"{label}.acceptance non-applicable dimension {dimension_id} "
                "must be not-applicable"
            )
        if not isinstance(dimension.get("evidence"), str):
            errors.append(
                f"{label}.acceptance dimension {dimension_id} evidence must be a string"
            )
        validate_string_list(
            dimension.get("findings"),
            f"{label}.acceptance dimension {dimension_id} findings",
            errors,
        )

    required_dimensions = fixture.get("required_dimensions")
    if isinstance(required_dimensions, list):
        if set(dimension_map) != set(required_dimensions):
            errors.append(
                f"{label}.acceptance dimensions must exactly match "
                "fixture.required_dimensions"
            )

    hard_failures = acceptance.get("hard_failures")
    if not isinstance(hard_failures, list):
        errors.append(f"{label}.acceptance hard_failures must be an array")
        hard_failures = []
    hard_failure_map: dict[str, dict] = {}
    for index, hard_failure in enumerate(hard_failures):
        if not isinstance(hard_failure, dict):
            errors.append(
                f"{label}.acceptance hard_failures[{index}] must be an object"
            )
            continue
        validate_exact_fields(
            hard_failure,
            {"id", "status", "evidence"},
            f"{label}.acceptance hard_failures[{index}]",
            errors,
        )
        failure_id = hard_failure.get("id")
        if not isinstance(failure_id, str) or not failure_id:
            errors.append(
                f"{label}.acceptance hard_failures[{index}] has invalid id"
            )
            continue
        if failure_id in hard_failure_map:
            errors.append(f"{label}.acceptance has duplicate hard failure {failure_id}")
        hard_failure_map[failure_id] = hard_failure
        if hard_failure.get("status") not in HARD_FAILURE_STATUSES:
            errors.append(
                f"{label}.acceptance hard failure {failure_id} has invalid status"
            )
        if not isinstance(hard_failure.get("evidence"), str):
            errors.append(
                f"{label}.acceptance hard failure {failure_id} evidence "
                "must be a string"
            )
    fixture_hard_failures = fixture.get("hard_failures")
    if isinstance(fixture_hard_failures, list):
        if set(hard_failure_map) != set(fixture_hard_failures):
            errors.append(
                f"{label}.acceptance hard_failures must exactly match fixture"
            )

    overall = acceptance.get("overall")
    if overall not in OVERALL_VALUES:
        errors.append(f"{label}.acceptance has invalid overall")
        return
    if overall != fixture.get("expected_overall"):
        errors.append(
            f"{label}.acceptance overall {overall!r} does not match "
            f"expected_overall {fixture.get('expected_overall')!r}"
        )

    applicable_verdicts = [
        dimension.get("verdict")
        for dimension in dimension_map.values()
        if dimension.get("applies") is True
    ]
    hard_statuses = [
        failure.get("status") for failure in hard_failure_map.values()
    ]
    if overall == "pass":
        if any(verdict != "pass" for verdict in applicable_verdicts):
            errors.append(f"{label}.acceptance pass requires every applicable dimension to pass")
        if any(status != "not-triggered" for status in hard_statuses):
            errors.append(f"{label}.acceptance pass requires no hard failure")
    elif overall == "fail":
        if "fail" not in applicable_verdicts and "triggered" not in hard_statuses:
            errors.append(
                f"{label}.acceptance fail requires a failed dimension "
                "or triggered hard failure"
            )
    elif overall == "blocked" and decision != "blocked":
        errors.append(f"{label}.acceptance blocked requires decision 'blocked'")
    elif overall == "incomplete":
        if (
            "not-reviewed" not in applicable_verdicts
            and "not-reviewed" not in hard_statuses
        ):
            errors.append(
                f"{label}.acceptance incomplete requires an unreviewed item"
            )

    validate_string_list(
        acceptance.get("limitations"),
        f"{label}.acceptance limitations",
        errors,
    )


def validate_visual_fixture(
    fixture: Any,
    root: Path = ROOT,
    *,
    acceptance_override: Optional[dict] = None,
    label: str = "visual fixture",
    expected_spec_revision: Optional[str] = None,
) -> tuple[list[str], int, Optional[str]]:
    errors: list[str] = []
    assets_checked = 0
    if not isinstance(fixture, dict):
        return [f"{label} must be an object"], 0, None
    validate_exact_fields(fixture, FIXTURE_FIELDS, label, errors)
    if fixture.get("$schema") != FIXTURE_SCHEMA:
        errors.append(f"{label} has an unknown $schema")
    for field in ("id", "revision", "spec_revision", "decision_rationale"):
        if not isinstance(fixture.get(field), str) or not fixture[field].strip():
            errors.append(f"{label}.{field} must be a non-empty string")
    if expected_spec_revision and fixture.get("spec_revision") != expected_spec_revision:
        errors.append(
            f"{label}.spec_revision {fixture.get('spec_revision')!r} "
            f"does not match {expected_spec_revision!r}"
        )
    if fixture.get("fixture_purpose") not in {"positive", "negative", "boundary"}:
        errors.append(
            f"{label}.fixture_purpose must be positive, negative, or boundary"
        )
    mode = fixture.get("requested_mode")
    decision = fixture.get("decision")
    if mode not in MODES:
        errors.append(f"{label}.requested_mode is invalid")
    if decision not in DECISIONS:
        errors.append(f"{label}.decision is invalid")
    if mode == "none" and decision != "none":
        errors.append(f"{label} mode none requires decision none")
    if mode == "required" and decision == "none":
        errors.append(f"{label} mode required cannot use decision none")

    _, _ = validate_file_reference(
        fixture.get("artifact"),
        root,
        f"{label}.artifact",
        errors,
        limit=MAX_ARTIFACT_BYTES,
    )
    asset = fixture.get("asset")
    brief = fixture.get("brief")
    visual_record = fixture.get("visual_record")
    if decision == "selected":
        if not isinstance(brief, dict):
            errors.append(f"{label}.brief is required for a selected asset")
        else:
            validate_exact_fields(
                brief,
                {
                    "purpose",
                    "reader_benefit",
                    "evidence_basis",
                    "must_not_imply",
                    "asset_type",
                    "acceptance_criteria",
                },
                f"{label}.brief",
                errors,
            )
            for field in ("purpose", "reader_benefit", "asset_type"):
                if not isinstance(brief.get(field), str) or not brief[field].strip():
                    errors.append(f"{label}.brief.{field} must be a non-empty string")
            for field in ("evidence_basis", "must_not_imply", "acceptance_criteria"):
                validate_string_list(
                    brief.get(field),
                    f"{label}.brief.{field}",
                    errors,
                )
        assets_checked += validate_asset(asset, root, label, errors)
        if visual_record is not None and isinstance(asset, dict):
            validate_visual_record(visual_record, asset, root, label, errors)
    else:
        if asset is not None:
            errors.append(f"{label}.asset must be null for decision {decision!r}")
        if visual_record is not None:
            errors.append(
                f"{label}.visual_record must be null for decision {decision!r}"
            )
        if decision == "none" and brief is not None:
            errors.append(f"{label}.brief must be null for decision none")

    required_dimensions = validate_string_list(
        fixture.get("required_dimensions"),
        f"{label}.required_dimensions",
        errors,
        allow_empty=False,
    )
    if set(required_dimensions) != set(DIMENSIONS):
        errors.append(f"{label}.required_dimensions must contain the RFC visual dimensions")
    validate_string_list(
        fixture.get("hard_failures"),
        f"{label}.hard_failures",
        errors,
    )
    validate_string_list(
        fixture.get("known_limitations"),
        f"{label}.known_limitations",
        errors,
    )
    if fixture.get("expected_overall") not in OVERALL_VALUES:
        errors.append(f"{label}.expected_overall is invalid")
    if fixture.get("fixture_purpose") == "positive" and fixture.get(
        "expected_overall"
    ) != "pass":
        errors.append(f"{label} positive fixtures must expect pass")
    if fixture.get("fixture_purpose") == "negative" and fixture.get(
        "expected_overall"
    ) != "fail":
        errors.append(f"{label} negative fixtures must expect fail")
    if fixture.get("fixture_purpose") == "boundary" and fixture.get(
        "expected_overall"
    ) not in {"blocked", "incomplete"}:
        errors.append(
            f"{label} boundary fixtures must expect blocked or incomplete"
        )
    if decision == "blocked" and fixture.get("expected_overall") != "blocked":
        errors.append(f"{label} blocked decisions must expect blocked")
    if fixture.get("expected_overall") == "blocked" and decision != "blocked":
        errors.append(f"{label} expected blocked requires decision blocked")

    acceptance = acceptance_override
    if acceptance is None:
        acceptance_path = resolve_repository_file(
            root,
            fixture.get("acceptance_path"),
            f"{label}.acceptance_path",
        )
        if acceptance_path is None:
            errors.append(
                f"{label}.acceptance_path must resolve to a repository file"
            )
        else:
            try:
                acceptance = read_bounded_json(
                    acceptance_path,
                    f"{label}.acceptance",
                )
            except VisualBenchmarkError as exc:
                errors.append(str(exc))
    if acceptance is not None:
        validate_acceptance_record(fixture, acceptance, label, errors)
    return errors, assets_checked, (
        acceptance.get("overall") if isinstance(acceptance, dict) else None
    )


def validate_checked_in_visual_benchmarks(
    root: Path = ROOT,
) -> tuple[dict[str, int], list[str]]:
    errors: list[str] = []
    fixtures = sorted((root / "benchmarks/visual-fixtures").glob("*.json"))
    if not fixtures:
        return {
            "fixtures": 0,
            "passed": 0,
            "failed": 0,
            "blocked": 0,
            "incomplete": 0,
            "assets_checked": 0,
        }, ["visual benchmarks require at least one fixture"]
    try:
        rfc_index = read_bounded_json(root / "registry/rfcs.json", "RFC index")
        spec_revision = rfc_index.get("version")
    except VisualBenchmarkError as exc:
        errors.append(str(exc))
        spec_revision = None
    summary = {
        "fixtures": len(fixtures),
        "passed": 0,
        "failed": 0,
        "blocked": 0,
        "incomplete": 0,
        "assets_checked": 0,
    }
    fixture_ids: set[str] = set()
    acceptance_paths: set[str] = set()
    for path in fixtures:
        relative = path.relative_to(root).as_posix()
        try:
            fixture = read_bounded_json(path, relative)
        except VisualBenchmarkError as exc:
            errors.append(str(exc))
            continue
        fixture_id = fixture.get("id")
        if isinstance(fixture_id, str):
            if fixture_id in fixture_ids:
                errors.append(f"duplicate visual fixture id: {fixture_id}")
            fixture_ids.add(fixture_id)
        acceptance_path = fixture.get("acceptance_path")
        if isinstance(acceptance_path, str):
            if acceptance_path in acceptance_paths:
                errors.append(
                    f"duplicate visual acceptance path: {acceptance_path}"
                )
            acceptance_paths.add(acceptance_path)
        fixture_errors, assets_checked, overall = validate_visual_fixture(
            fixture,
            root,
            label=relative,
            expected_spec_revision=(
                spec_revision if isinstance(spec_revision, str) else None
            ),
        )
        errors.extend(fixture_errors)
        summary["assets_checked"] += assets_checked
        if overall in OVERALL_VALUES:
            summary[
                {
                    "pass": "passed",
                    "fail": "failed",
                    "blocked": "blocked",
                    "incomplete": "incomplete",
                }[overall]
            ] += 1

    checked_in_acceptance = {
        path.relative_to(root).as_posix()
        for path in (root / "benchmarks/visual-acceptance").glob("*.json")
    }
    for orphan in sorted(checked_in_acceptance - acceptance_paths):
        errors.append(f"orphan visual acceptance record: {orphan}")
    return summary, errors


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate visual benchmark fixtures and acceptance records."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="validate all checked-in visual benchmark fixtures",
    )
    args = parser.parse_args()
    if not args.check:
        parser.error("--check is required")
    summary, errors = validate_checked_in_visual_benchmarks(ROOT)
    envelope = {"ok": not errors, "data": summary}
    if errors:
        envelope["errors"] = errors
    print(json.dumps(envelope, ensure_ascii=False, indent=2))
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
