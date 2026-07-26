#!/usr/bin/env python3
"""Validate and execute the pinned offline release gates."""

import argparse
from datetime import date
import json
import os
import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any, Optional


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "release/manifest.json"
MANIFEST_SCHEMA = (
    "https://human-writing-rules.example/schemas/release-manifest.schema.json"
)
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_DIAGNOSTIC_CHARS = 4000
RELEASE_RE = re.compile(
    r"^[0-9]+\.[0-9]+\.[0-9]+(?:-[0-9A-Za-z.-]+)?$"
)
SHA256_REVISION_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
MANIFEST_FIELDS = {
    "$schema",
    "release",
    "status",
    "channel",
    "release_date",
    "spec_revision",
    "registry_source_revision",
    "profiles",
    "compatibility",
    "expected_counts",
    "required_artifacts",
    "gates",
    "unsupported_capabilities",
    "known_limitations",
}
COMPATIBILITY_FIELDS = {
    "stability",
    "identifier_policy",
    "schema_policy",
    "minimum_python",
    "ci_python",
    "npm_role",
    "network_default",
    "provider_core",
}
COUNT_FIELDS = {
    "objects",
    "rfcs",
    "requirements",
    "conformance_cases",
    "benchmark_cases",
    "benchmark_plans",
    "visual_fixtures",
    "reviewed_examples",
    "topics",
    "platforms",
}
REQUIRED_PROFILES = {"editorial-core", "editorial-visual", "benchmark"}
REQUIRED_ARTIFACTS = {
    "README.md",
    "LICENSE",
    "CHANGELOG.md",
    "COMPATIBILITY.md",
    "RELEASING.md",
    "MIGRATING-TO-1.0.md",
    "GOVERNANCE.md",
    "SUPPORT.md",
    "SECURITY.md",
    "CODE_OF_CONDUCT.md",
    "VERSION",
    "AGENTS.md",
    "schemas/release-manifest.schema.json",
    "schemas/stability-review.schema.json",
    "rfcs/README.md",
    "registry/generated-index.json",
    "conformance/requirements.json",
    "examples/reviewed-examples.json",
    "benchmarks/README.md",
    "release/1.0.0.md",
    "release/stability-review.json",
    "release/manifest.json",
}
REQUIRED_GATES = {
    "unit-tests": [
        "python3",
        "-m",
        "unittest",
        "discover",
        "-s",
        "tests",
        "-p",
        "test_*.py",
    ],
    "repository-validation": ["npm", "run", "check"],
    "normative-requirements": ["npm", "run", "check:conformance"],
    "conformance-fixtures": ["npm", "run", "test:fixtures"],
    "generated-registry-index": ["npm", "run", "check:registry-index"],
    "visual-benchmarks": ["npm", "run", "check:visual-benchmarks"],
    "reviewed-example-coverage": ["npm", "run", "check:reviewed-examples"],
    "runner-doctor": ["npm", "run", "runner:doctor"],
}


class ReleaseError(Exception):
    pass


def read_bounded_json(path: Path, label: str) -> dict:
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise ReleaseError(f"{label} cannot be read: {path}") from exc
    if size > MAX_JSON_BYTES:
        raise ReleaseError(f"{label} exceeds {MAX_JSON_BYTES} bytes: {path}")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ReleaseError(f"{label} cannot be read: {path}") from exc
    try:
        value = json.loads(raw.decode("utf-8"))
    except UnicodeDecodeError as exc:
        raise ReleaseError(f"{label} is not UTF-8: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ReleaseError(
            f"{label} contains invalid JSON at {exc.lineno}:{exc.colno}: {path}"
        ) from exc
    if not isinstance(value, dict):
        raise ReleaseError(f"{label} root must be an object: {path}")
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
    allow_empty: bool = False,
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


def resolve_repository_file(root: Path, relative_path: Any) -> Optional[Path]:
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


def count_conformance_cases(root: Path) -> int:
    total = 0
    for path in sorted((root / "conformance/fixtures").glob("*.json")):
        suite = read_bounded_json(path, path.relative_to(root).as_posix())
        cases = suite.get("cases")
        if not isinstance(cases, list):
            raise ReleaseError(f"{path.relative_to(root)} cases must be an array")
        total += len(cases)
    return total


def current_counts(root: Path) -> dict[str, int]:
    objects = read_bounded_json(root / "registry/objects.json", "object registry")
    rfcs = read_bounded_json(root / "registry/rfcs.json", "RFC registry")
    requirements = read_bounded_json(
        root / "conformance/requirements.json",
        "conformance requirements",
    )
    reviewed = read_bounded_json(
        root / "examples/reviewed-examples.json",
        "reviewed example catalog",
    )
    topics = read_bounded_json(root / "registry/topics.json", "topic registry")
    platforms = read_bounded_json(
        root / "registry/platforms.json",
        "platform registry",
    )
    return {
        "objects": len(objects.get("objects", [])),
        "rfcs": len(rfcs.get("rfcs", [])),
        "requirements": len(requirements.get("requirements", [])),
        "conformance_cases": count_conformance_cases(root),
        "benchmark_cases": len(list((root / "benchmarks/cases").glob("*.json"))),
        "benchmark_plans": len(list((root / "benchmarks/plans").glob("*.json"))),
        "visual_fixtures": len(
            list((root / "benchmarks/visual-fixtures").glob("*.json"))
        ),
        "reviewed_examples": len(reviewed.get("examples", [])),
        "topics": len(topics.get("topics", [])),
        "platforms": len(platforms.get("platforms", [])),
    }


def validate_release_manifest(
    manifest: Any,
    root: Path = ROOT,
) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    summary: dict[str, Any] = {
        "release": None,
        "status": None,
        "channel": None,
        "spec_revision": None,
        "gates": 0,
        "artifacts": 0,
        "counts": {},
    }
    if not isinstance(manifest, dict):
        return summary, ["release manifest must be an object"]
    validate_exact_fields(manifest, MANIFEST_FIELDS, "release manifest", errors)
    if manifest.get("$schema") != MANIFEST_SCHEMA:
        errors.append("release manifest has an unknown $schema")

    release = manifest.get("release")
    summary["release"] = release
    if not isinstance(release, str) or not RELEASE_RE.fullmatch(release):
        errors.append("release manifest release must be a semantic version")
    summary["status"] = manifest.get("status")
    summary["channel"] = manifest.get("channel")
    summary["spec_revision"] = manifest.get("spec_revision")
    if manifest.get("status") not in {"candidate", "released", "withdrawn"}:
        errors.append("release manifest status is invalid")
    if manifest.get("channel") not in {
        "draft-preview",
        "release-candidate",
        "stable",
    }:
        errors.append("release manifest channel is invalid")
    if manifest.get("status") == "candidate" and manifest.get("release_date") is not None:
        errors.append("candidate release_date must be null")
    if manifest.get("status") == "released":
        release_date = manifest.get("release_date")
        valid_release_date = False
        if isinstance(release_date, str):
            try:
                valid_release_date = (
                    date.fromisoformat(release_date).isoformat() == release_date
                )
            except ValueError:
                pass
        if not valid_release_date:
            errors.append(
                "released manifest requires release_date in YYYY-MM-DD format"
            )

    try:
        version_file = (root / "VERSION").read_text(encoding="utf-8").strip()
    except OSError as exc:
        errors.append(f"VERSION cannot be read: {exc}")
        version_file = None
    try:
        package = read_bounded_json(root / "package.json", "package.json")
        rfc_registry = read_bounded_json(
            root / "registry/rfcs.json",
            "RFC registry",
        )
        generated_index = read_bounded_json(
            root / "registry/generated-index.json",
            "generated registry index",
        )
    except ReleaseError as exc:
        return summary, errors + [str(exc)]
    if version_file != release:
        errors.append(f"VERSION {version_file!r} does not match release {release!r}")
    if package.get("version") != release:
        errors.append(
            f"package.json version {package.get('version')!r} "
            f"does not match release {release!r}"
        )
    if package.get("private") is not True:
        errors.append("package.json must remain private for repository releases")
    if manifest.get("spec_revision") != rfc_registry.get("version"):
        errors.append("release spec_revision does not match RFC registry")
    source_revision = manifest.get("registry_source_revision")
    if (
        not isinstance(source_revision, str)
        or not SHA256_REVISION_RE.fullmatch(source_revision)
    ):
        errors.append("release registry_source_revision is invalid")
    if source_revision != generated_index.get("source_revision"):
        errors.append(
            "release registry_source_revision does not match generated index"
        )

    profiles = set(
        validate_string_list(
            manifest.get("profiles"),
            "release profiles",
            errors,
        )
    )
    if profiles != REQUIRED_PROFILES:
        errors.append("release profiles must contain all published profiles")

    compatibility = manifest.get("compatibility")
    if not isinstance(compatibility, dict):
        errors.append("release compatibility must be an object")
    else:
        validate_exact_fields(
            compatibility,
            COMPATIBILITY_FIELDS,
            "release compatibility",
            errors,
        )
        for field in ("identifier_policy", "schema_policy", "npm_role"):
            if (
                not isinstance(compatibility.get(field), str)
                or not compatibility[field].strip()
            ):
                errors.append(f"release compatibility.{field} must be non-empty")
        expected_values = {
            "minimum_python": "3.9",
            "network_default": "disabled",
            "provider_core": "vendor-neutral",
        }
        for field, expected in expected_values.items():
            if compatibility.get(field) != expected:
                errors.append(
                    f"release compatibility.{field} must equal {expected!r}"
                )
        if compatibility.get("ci_python") != ["3.9", "3.12"]:
            errors.append(
                "release compatibility.ci_python must equal ['3.9', '3.12']"
            )
        rfc_statuses = {
            entry.get("status")
            for entry in rfc_registry.get("rfcs", [])
            if isinstance(entry, dict)
        }
        if "draft" in rfc_statuses:
            if compatibility.get("stability") != "pre-stable":
                errors.append("draft RFCs require pre-stable compatibility")
            if manifest.get("channel") == "stable":
                errors.append("draft RFCs cannot use the stable channel")
        if manifest.get("channel") == "stable":
            if compatibility.get("stability") != "stable":
                errors.append("stable channel requires stable compatibility")
            if isinstance(release, str) and "-" in release:
                errors.append("stable channel requires a final release version")
            non_active_rfcs = [
                entry.get("id")
                for entry in rfc_registry.get("rfcs", [])
                if isinstance(entry, dict) and entry.get("status") != "active"
            ]
            if non_active_rfcs:
                errors.append(
                    "stable channel requires active RFCs: "
                    + ", ".join(str(item) for item in non_active_rfcs)
                )
            try:
                object_registry = read_bounded_json(
                    root / "registry/objects.json",
                    "object registry",
                )
            except ReleaseError as exc:
                errors.append(str(exc))
            else:
                non_active_objects = [
                    entry.get("id")
                    for entry in object_registry.get("objects", [])
                    if isinstance(entry, dict) and entry.get("status") != "active"
                ]
                if non_active_objects:
                    errors.append(
                        "stable channel requires active objects: "
                        + ", ".join(str(item) for item in non_active_objects)
                    )

    expected_counts = manifest.get("expected_counts")
    try:
        actual_counts = current_counts(root)
    except ReleaseError as exc:
        errors.append(str(exc))
        actual_counts = {}
    summary["counts"] = actual_counts
    if not isinstance(expected_counts, dict):
        errors.append("release expected_counts must be an object")
    else:
        validate_exact_fields(
            expected_counts,
            COUNT_FIELDS,
            "release expected_counts",
            errors,
        )
        for field in COUNT_FIELDS:
            expected = expected_counts.get(field)
            if (
                not isinstance(expected, int)
                or isinstance(expected, bool)
                or expected < 1
            ):
                errors.append(
                    f"release expected_counts.{field} must be a positive integer"
                )
            elif actual_counts.get(field) != expected:
                errors.append(
                    f"release expected_counts.{field}={expected}, "
                    f"actual {actual_counts.get(field)}"
                )

    artifacts = set(
        validate_string_list(
            manifest.get("required_artifacts"),
            "release required_artifacts",
            errors,
        )
    )
    summary["artifacts"] = len(artifacts)
    if artifacts != REQUIRED_ARTIFACTS:
        missing = REQUIRED_ARTIFACTS - artifacts
        extra = artifacts - REQUIRED_ARTIFACTS
        if missing:
            errors.append(
                "release required_artifacts missing: "
                + ", ".join(sorted(missing))
            )
        if extra:
            errors.append(
                "release required_artifacts has unexpected paths: "
                + ", ".join(sorted(extra))
            )
    for artifact in artifacts:
        if resolve_repository_file(root, artifact) is None:
            errors.append(f"release artifact is missing or unsafe: {artifact}")

    stability_path = resolve_repository_file(
        root,
        "release/stability-review.json",
    )
    if stability_path is not None:
        try:
            stability_review = read_bounded_json(
                stability_path,
                "stability review",
            )
        except ReleaseError as exc:
            errors.append(str(exc))
        else:
            if stability_review.get("target_release") != release:
                errors.append("stability review target_release does not match")
            if stability_review.get("spec_revision") != manifest.get(
                "spec_revision"
            ):
                errors.append("stability review spec_revision does not match")
            if (
                stability_review.get("decision")
                != "ready-for-stable-candidate"
            ):
                errors.append("stability review decision is not ready")
            reviewer = stability_review.get("reviewer")
            if not isinstance(reviewer, dict):
                errors.append("stability review reviewer must be an object")
            elif (
                reviewer.get("type") != "internal"
                or reviewer.get("independence") != "not-independent"
            ):
                errors.append(
                    "stability review must preserve its internal "
                    "non-independent boundary"
                )
            dimensions = stability_review.get("dimensions")
            if not isinstance(dimensions, list) or len(dimensions) < 1:
                errors.append("stability review dimensions must be non-empty")
            elif any(
                not isinstance(item, dict) or item.get("verdict") != "pass"
                for item in dimensions
            ):
                errors.append("stability review dimensions must pass")

    gates = manifest.get("gates")
    if not isinstance(gates, list):
        errors.append("release gates must be an array")
        gates = []
    summary["gates"] = len(gates)
    gate_ids: set[str] = set()
    for index, gate in enumerate(gates):
        label = f"release gates[{index}]"
        if not isinstance(gate, dict):
            errors.append(f"{label} must be an object")
            continue
        validate_exact_fields(
            gate,
            {"id", "argv", "timeout_seconds"},
            label,
            errors,
        )
        gate_id = gate.get("id")
        if not isinstance(gate_id, str) or not gate_id:
            errors.append(f"{label}.id must be non-empty")
            continue
        if gate_id in gate_ids:
            errors.append(f"duplicate release gate id: {gate_id}")
        gate_ids.add(gate_id)
        argv = validate_string_list(
            gate.get("argv"),
            f"{label}.argv",
            errors,
        )
        if gate_id not in REQUIRED_GATES:
            errors.append(f"unknown release gate id: {gate_id}")
        elif argv != REQUIRED_GATES[gate_id]:
            errors.append(f"{label}.argv is not the canonical command")
        timeout = gate.get("timeout_seconds")
        if (
            not isinstance(timeout, int)
            or isinstance(timeout, bool)
            or timeout < 1
            or timeout > 600
        ):
            errors.append(f"{label}.timeout_seconds must be between 1 and 600")
    if gate_ids != set(REQUIRED_GATES):
        missing = set(REQUIRED_GATES) - gate_ids
        if missing:
            errors.append("release gates missing: " + ", ".join(sorted(missing)))

    validate_string_list(
        manifest.get("unsupported_capabilities"),
        "release unsupported_capabilities",
        errors,
    )
    validate_string_list(
        manifest.get("known_limitations"),
        "release known_limitations",
        errors,
    )
    return summary, errors


def validate_checked_in_release(
    root: Path = ROOT,
) -> tuple[dict[str, Any], list[str]]:
    try:
        manifest = read_bounded_json(
            root / "release/manifest.json",
            "release manifest",
        )
    except ReleaseError as exc:
        return {}, [str(exc)]
    return validate_release_manifest(manifest, root)


def diagnostic_text(value: bytes) -> tuple[str, int, bool]:
    decoded = value.decode("utf-8", errors="replace")
    truncated = len(decoded) > MAX_DIAGNOSTIC_CHARS
    if truncated:
        decoded = decoded[-MAX_DIAGNOSTIC_CHARS:]
    return decoded, len(value), truncated


def verify_release(manifest: dict, root: Path = ROOT) -> tuple[dict, list[str]]:
    validation, errors = validate_release_manifest(manifest, root)
    result = {
        "release": validation.get("release"),
        "status": "invalid" if errors else "running",
        "attempted": 0,
        "passed": 0,
        "failed": 0,
        "gates": [],
    }
    if errors:
        return result, errors
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    for gate in manifest["gates"]:
        gate_result = {
            "id": gate["id"],
            "argv": gate["argv"],
            "status": "running",
            "returncode": None,
            "stdout": "",
            "stdout_bytes": 0,
            "stdout_truncated": False,
            "stderr": "",
            "stderr_bytes": 0,
            "stderr_truncated": False,
        }
        result["gates"].append(gate_result)
        result["attempted"] += 1
        try:
            completed = subprocess.run(
                gate["argv"],
                cwd=root,
                env=environment,
                check=False,
                capture_output=True,
                timeout=gate["timeout_seconds"],
            )
        except FileNotFoundError as exc:
            gate_result["status"] = "failed"
            gate_result["stderr"] = str(exc)
            result["failed"] += 1
            break
        except subprocess.TimeoutExpired as exc:
            gate_result["status"] = "timeout"
            stdout, stdout_bytes, stdout_truncated = diagnostic_text(
                exc.stdout or b""
            )
            stderr, stderr_bytes, stderr_truncated = diagnostic_text(
                exc.stderr or b""
            )
            gate_result.update(
                {
                    "stdout": stdout,
                    "stdout_bytes": stdout_bytes,
                    "stdout_truncated": stdout_truncated,
                    "stderr": stderr,
                    "stderr_bytes": stderr_bytes,
                    "stderr_truncated": stderr_truncated,
                }
            )
            result["failed"] += 1
            break
        stdout, stdout_bytes, stdout_truncated = diagnostic_text(completed.stdout)
        stderr, stderr_bytes, stderr_truncated = diagnostic_text(completed.stderr)
        gate_result.update(
            {
                "returncode": completed.returncode,
                "stdout": stdout,
                "stdout_bytes": stdout_bytes,
                "stdout_truncated": stdout_truncated,
                "stderr": stderr,
                "stderr_bytes": stderr_bytes,
                "stderr_truncated": stderr_truncated,
            }
        )
        if completed.returncode == 0:
            gate_result["status"] = "pass"
            result["passed"] += 1
        else:
            gate_result["status"] = "failed"
            result["failed"] += 1
            break
    result["status"] = "pass" if result["failed"] == 0 else "failed"
    return result, []


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate or execute the pinned release gates."
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true")
    action.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    try:
        manifest = read_bounded_json(MANIFEST_PATH, "release manifest")
    except ReleaseError as exc:
        print(
            json.dumps(
                {"ok": False, "errors": [str(exc)]},
                ensure_ascii=False,
                indent=2,
            )
        )
        raise SystemExit(1)
    if args.verify:
        data, errors = verify_release(manifest, ROOT)
    else:
        data, errors = validate_release_manifest(manifest, ROOT)
    envelope = {"ok": not errors and data.get("status") != "failed", "data": data}
    if errors:
        envelope["errors"] = errors
    print(json.dumps(envelope, ensure_ascii=False, indent=2))
    raise SystemExit(0 if envelope["ok"] else 1)


if __name__ == "__main__":
    main()
