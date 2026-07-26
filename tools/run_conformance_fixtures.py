#!/usr/bin/env python3
"""Validate and execute declarative conformance-checker fixtures."""

import json
import re
import shutil
import tempfile
from pathlib import Path, PurePosixPath
from typing import Optional

try:
    from .check_conformance_requirements import validate_requirements
except ImportError:
    from check_conformance_requirements import validate_requirements


ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = ROOT / "conformance/fixtures"
ALLOWED_MUTATIONS = {
    "text-replace",
    "text-append",
    "requirement-set",
    "manifest-set",
    "reuse-retired-id",
}
CASE_ID_RE = re.compile(r"^CONF-[A-Z0-9-]+$")
RFC_BY_PREFIX = {
    "HWR-SCOPE": "RFC-0001",
    "HWR-PIPE": "RFC-0002",
    "HWR-OBJ": "RFC-0003",
    "HWR-RESOLVE": "RFC-0004",
    "HWR-REVIEW": "RFC-0005",
    "HWR-BENCH": "RFC-0006",
}


def load_json(path: Path, errors: list[str]) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing JSON file: {path}")
        return {}
    except json.JSONDecodeError as exc:
        errors.append(f"invalid JSON in {path}:{exc.lineno}:{exc.colno}: {exc.msg}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"JSON root must be an object: {path}")
        return {}
    return value


def safe_fixture_path(root: Path, relative_path: object, label: str) -> Path:
    if not isinstance(relative_path, str):
        raise ValueError(f"{label}.path must be a string")
    pure_path = PurePosixPath(relative_path)
    if pure_path.is_absolute() or ".." in pure_path.parts:
        raise ValueError(f"{label}.path is unsafe: {relative_path}")
    path = root / relative_path
    if not path.is_file():
        raise ValueError(f"{label}.path does not exist: {relative_path}")
    return path


def set_dotted_field(target: dict, dotted_field: object, value: object, label: str) -> None:
    if not isinstance(dotted_field, str) or not dotted_field:
        raise ValueError(f"{label}.field must be a non-empty string")
    parts = dotted_field.split(".")
    current = target
    for part in parts[:-1]:
        child = current.get(part)
        if not isinstance(child, dict):
            raise ValueError(f"{label}.field cannot resolve {dotted_field}")
        current = child
    current[parts[-1]] = value


def find_requirement(manifest: dict, requirement_id: object, label: str) -> dict:
    if not isinstance(requirement_id, str):
        raise ValueError(f"{label}.requirement_id must be a string")
    matches = [
        requirement
        for requirement in manifest.get("requirements", [])
        if isinstance(requirement, dict) and requirement.get("id") == requirement_id
    ]
    if len(matches) != 1:
        raise ValueError(
            f"{label}.requirement_id must resolve once: {requirement_id}"
        )
    return matches[0]


def apply_mutations(root: Path, mutations: list[dict]) -> None:
    manifest_path = root / "conformance/requirements.json"
    manifest: Optional[dict] = None
    manifest_changed = False

    for index, mutation in enumerate(mutations):
        label = f"mutations[{index}]"
        mutation_type = mutation["type"]

        if mutation_type in {"text-replace", "text-append"}:
            path = safe_fixture_path(root, mutation.get("path"), label)
            text = path.read_text(encoding="utf-8")
            if mutation_type == "text-replace":
                old = mutation.get("old")
                new = mutation.get("new")
                if not isinstance(old, str) or not old:
                    raise ValueError(f"{label}.old must be a non-empty string")
                if not isinstance(new, str):
                    raise ValueError(f"{label}.new must be a string")
                occurrences = text.count(old)
                if occurrences != 1:
                    raise ValueError(
                        f"{label}.old must occur exactly once; found {occurrences}"
                    )
                text = text.replace(old, new, 1)
            else:
                appended = mutation.get("text")
                if not isinstance(appended, str) or not appended:
                    raise ValueError(f"{label}.text must be a non-empty string")
                text += appended
            path.write_text(text, encoding="utf-8")
            continue

        if manifest is None:
            manifest = load_json(manifest_path, [])

        if mutation_type == "requirement-set":
            requirement = find_requirement(
                manifest, mutation.get("requirement_id"), label
            )
            set_dotted_field(
                requirement, mutation.get("field"), mutation.get("value"), label
            )
        elif mutation_type == "manifest-set":
            set_dotted_field(
                manifest, mutation.get("field"), mutation.get("value"), label
            )
        elif mutation_type == "reuse-retired-id":
            requirement_id = mutation.get("requirement_id")
            find_requirement(manifest, requirement_id, label)
            prefix = str(requirement_id).rsplit("-", 1)[0]
            if prefix not in RFC_BY_PREFIX:
                raise ValueError(
                    f"{label}.requirement_id has an unknown prefix: {requirement_id}"
                )
            manifest.setdefault("retired_requirements", []).append(
                {
                    "id": requirement_id,
                    "rfc": RFC_BY_PREFIX[prefix],
                    "removed_in": mutation.get("removed_in"),
                    "reason": mutation.get("reason"),
                }
            )
        else:
            raise ValueError(f"{label}.type is unsupported: {mutation_type}")
        manifest_changed = True

    if manifest_changed and manifest is not None:
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


def validate_fixture_suites(
    root: Path = ROOT,
    errors: Optional[list[str]] = None,
) -> tuple[list[dict], int]:
    if errors is None:
        errors = []

    fixture_paths = sorted((root / "conformance/fixtures").glob("*.json"))
    if not fixture_paths:
        errors.append("no conformance fixture suites found")
        return [], 0

    rfc_registry = load_json(root / "registry/rfcs.json", errors)
    requirements = load_json(root / "conformance/requirements.json", errors)
    spec_revision = rfc_registry.get("version")
    known_requirements = {
        requirement.get("id")
        for requirement in requirements.get("requirements", [])
        if isinstance(requirement, dict)
    }

    suites: list[dict] = []
    seen_case_ids: set[str] = set()
    case_count = 0

    for path in fixture_paths:
        suite = load_json(path, errors)
        suites.append(suite)
        relative_path = path.relative_to(root).as_posix()
        if suite.get("schema_version") != "1.0":
            errors.append(f"{relative_path}: schema_version must equal '1.0'")
        if suite.get("spec_revision") != spec_revision:
            errors.append(
                f"{relative_path}: spec_revision must equal {spec_revision!r}"
            )
        if suite.get("target") != "conformance-requirements":
            errors.append(
                f"{relative_path}: target must equal 'conformance-requirements'"
            )

        cases = suite.get("cases")
        if not isinstance(cases, list) or not cases:
            errors.append(f"{relative_path}: cases must be a non-empty array")
            continue

        for index, case in enumerate(cases):
            case_count += 1
            label = f"{relative_path} cases[{index}]"
            if not isinstance(case, dict):
                errors.append(f"{label} must be an object")
                continue

            case_id = case.get("id")
            if not isinstance(case_id, str) or not CASE_ID_RE.fullmatch(case_id):
                errors.append(f"{label}.id is invalid: {case_id!r}")
            elif case_id in seen_case_ids:
                errors.append(f"duplicate fixture case ID: {case_id}")
            else:
                seen_case_ids.add(case_id)

            if not isinstance(case.get("description"), str) or not case[
                "description"
            ].strip():
                errors.append(f"{label}.description must be a non-empty string")

            related = case.get("related_requirements", [])
            if not isinstance(related, list) or not all(
                isinstance(item, str) for item in related
            ):
                errors.append(f"{label}.related_requirements must be an array")
            else:
                for requirement_id in related:
                    if requirement_id not in known_requirements:
                        errors.append(
                            f"{label} references unknown requirement {requirement_id}"
                        )

            mutations = case.get("mutations")
            if not isinstance(mutations, list):
                errors.append(f"{label}.mutations must be an array")
                continue
            for mutation_index, mutation in enumerate(mutations):
                mutation_label = f"{label}.mutations[{mutation_index}]"
                if not isinstance(mutation, dict):
                    errors.append(f"{mutation_label} must be an object")
                    continue
                if mutation.get("type") not in ALLOWED_MUTATIONS:
                    errors.append(
                        f"{mutation_label}.type is invalid: {mutation.get('type')!r}"
                    )
                    continue
                if "path" in mutation:
                    path_value = mutation["path"]
                    if not isinstance(path_value, str):
                        errors.append(f"{mutation_label}.path must be a string")
                    else:
                        pure_path = PurePosixPath(path_value)
                        if pure_path.is_absolute() or ".." in pure_path.parts:
                            errors.append(
                                f"{mutation_label}.path is unsafe: {path_value}"
                            )
                mutation_type = mutation["type"]
                required_by_type = {
                    "text-replace": {"path", "old", "new"},
                    "text-append": {"path", "text"},
                    "requirement-set": {"requirement_id", "field", "value"},
                    "manifest-set": {"field", "value"},
                    "reuse-retired-id": {
                        "requirement_id",
                        "removed_in",
                        "reason",
                    },
                }
                missing = required_by_type[mutation_type] - mutation.keys()
                if missing:
                    errors.append(
                        f"{mutation_label} missing fields: "
                        f"{', '.join(sorted(missing))}"
                    )

            expected = case.get("expected")
            if not isinstance(expected, dict):
                errors.append(f"{label}.expected must be an object")
                continue
            if not isinstance(expected.get("valid"), bool):
                errors.append(f"{label}.expected.valid must be boolean")
            error_contains = expected.get("error_contains")
            if not isinstance(error_contains, list) or not all(
                isinstance(item, str) and item for item in error_contains
            ):
                errors.append(
                    f"{label}.expected.error_contains must contain strings"
                )
            elif expected.get("valid") and error_contains:
                errors.append(
                    f"{label} expects success but declares expected errors"
                )

    return suites, case_count


def copy_fixture_repository(source: Path, destination: Path) -> None:
    for relative_path in ("conformance", "registry", "rfcs"):
        shutil.copytree(source / relative_path, destination / relative_path)


def run_fixtures(root: Path = ROOT) -> tuple[int, list[str]]:
    definition_errors: list[str] = []
    suites, case_count = validate_fixture_suites(root, definition_errors)
    if definition_errors:
        return 0, definition_errors

    failures: list[str] = []
    executed = 0

    for suite in suites:
        for case in suite["cases"]:
            executed += 1
            with tempfile.TemporaryDirectory() as temporary_directory:
                fixture_root = Path(temporary_directory)
                copy_fixture_repository(root, fixture_root)
                try:
                    apply_mutations(fixture_root, case["mutations"])
                except ValueError as exc:
                    failures.append(f"{case['id']}: invalid mutation: {exc}")
                    continue

                validation_errors: list[str] = []
                validate_requirements(fixture_root, validation_errors)
                expected = case["expected"]
                actual_valid = not validation_errors
                if actual_valid != expected["valid"]:
                    failures.append(
                        f"{case['id']}: expected valid={expected['valid']}, "
                        f"got valid={actual_valid}; errors={validation_errors}"
                    )
                    continue
                for fragment in expected["error_contains"]:
                    if not any(fragment in error for error in validation_errors):
                        failures.append(
                            f"{case['id']}: missing error fragment {fragment!r}; "
                            f"errors={validation_errors}"
                        )

    if executed != case_count:
        failures.append(f"expected to execute {case_count} cases, executed {executed}")
    return executed, failures


def main() -> None:
    executed, failures = run_fixtures(ROOT)
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"OK: {executed} conformance fixture cases")


if __name__ == "__main__":
    main()
