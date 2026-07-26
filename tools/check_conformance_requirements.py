#!/usr/bin/env python3
"""Check traceability for every MUST/MUST NOT/SHOULD/SHOULD NOT source unit."""

import json
import re
from pathlib import Path
from typing import Optional


ROOT = Path(__file__).resolve().parents[1]
REQUIREMENTS_PATH = ROOT / "conformance/requirements.json"
RFC_REGISTRY_PATH = ROOT / "registry/rfcs.json"

NORMATIVE_TERM_RE = re.compile(
    r"\bMUST NOT\b|\bSHOULD NOT\b|\bMUST\b|\bSHOULD\b"
)
INLINE_CODE_RE = re.compile(r"`+[^`]*`+")
REQUIREMENT_ID_RE = re.compile(
    r"^HWR-(SCOPE|PIPE|OBJ|RESOLVE|REVIEW|BENCH)-[0-9]{3}$"
)

ALLOWED_OWNERS = {
    "spec-governance",
    "pipeline",
    "object-model",
    "resolver",
    "review",
    "benchmark",
}
ALLOWED_PROFILES = {"editorial-core", "editorial-visual", "benchmark"}
ALLOWED_METHODS = {
    "manual-review",
    "automated-validator",
    "automated-test",
    "conformance-fixture",
    "benchmark-audit",
}
ALLOWED_STATUSES = {"planned", "implemented", "verified", "not-applicable"}


def load_json(path: Path, errors: list[str]) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        errors.append(f"missing JSON file: {path.relative_to(ROOT)}")
        return {}
    except json.JSONDecodeError as exc:
        errors.append(
            f"invalid JSON in {path.relative_to(ROOT)}:"
            f"{exc.lineno}:{exc.colno}: {exc.msg}"
        )
        return {}

    if not isinstance(value, dict):
        errors.append(f"JSON root must be an object: {path.relative_to(ROOT)}")
        return {}
    return value


def normalize_source_text(text: str) -> str:
    return " ".join(text.split())


def source_key(rfc_id: str, section: str, source_text: str) -> tuple[str, str, str]:
    return rfc_id, section, normalize_source_text(source_text)


def count_normative_terms(text: str) -> dict[str, int]:
    visible_text = INLINE_CODE_RE.sub("", text)
    matches = NORMATIVE_TERM_RE.findall(visible_text)
    return {
        "must": sum(term == "MUST" for term in matches),
        "must_not": sum(term == "MUST NOT" for term in matches),
        "should": sum(term == "SHOULD" for term in matches),
        "should_not": sum(term == "SHOULD NOT" for term in matches),
    }


def extract_normative_units(path: Path, rfc_id: str) -> list[dict]:
    """Return physical Markdown lines containing unquoted normative terms.

    A physical line is the traceability unit. A colon-ended unit still governs
    its subordinate list or table in the RFC; the matrix does not duplicate
    that normative content.
    """

    units: list[dict] = []
    section = ""
    fence_marker: Optional[str] = None

    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        stripped = raw_line.strip()

        if stripped.startswith(("```", "~~~")):
            marker = stripped[:3]
            if fence_marker is None:
                fence_marker = marker
            elif fence_marker == marker:
                fence_marker = None
            continue
        if fence_marker is not None:
            continue

        heading = re.match(r"^#{1,6}\s+(.+?)\s*#*$", stripped)
        if heading:
            section = heading.group(1).strip()

        terms = count_normative_terms(stripped)
        if sum(terms.values()) == 0:
            continue

        units.append(
            {
                "rfc": rfc_id,
                "section": section,
                "source_text": stripped,
                "line": line_number,
                "normative_terms": terms,
            }
        )

    return units


def validate_string_list(
    value: object,
    label: str,
    allowed: set[str],
    errors: list[str],
) -> list[str]:
    if not isinstance(value, list) or not value:
        errors.append(f"{label} must be a non-empty array")
        return []
    if not all(isinstance(item, str) and item for item in value):
        errors.append(f"{label} must contain non-empty strings")
        return []

    strings = list(value)
    if len(strings) != len(set(strings)):
        errors.append(f"{label} must not contain duplicates")
    unknown = sorted(set(strings) - allowed)
    if unknown:
        errors.append(f"{label} contains unknown values: {', '.join(unknown)}")
    return strings


def validate_defaults(
    defaults: object,
    indexed_rfc_ids: set[str],
    errors: list[str],
) -> dict[str, dict]:
    if not isinstance(defaults, dict):
        errors.append("conformance/requirements.json: rfc_defaults must be an object")
        return {}

    default_ids = set(defaults)
    for rfc_id in sorted(indexed_rfc_ids - default_ids):
        errors.append(f"missing conformance defaults for {rfc_id}")
    for rfc_id in sorted(default_ids - indexed_rfc_ids):
        errors.append(f"conformance defaults reference unknown RFC {rfc_id}")

    validated: dict[str, dict] = {}
    prefixes: set[str] = set()
    required_fields = {"id_prefix", "owner", "profiles", "verification_method"}

    for rfc_id, value in defaults.items():
        label = f"rfc_defaults.{rfc_id}"
        if not isinstance(value, dict):
            errors.append(f"{label} must be an object")
            continue
        missing = required_fields - value.keys()
        if missing:
            errors.append(f"{label} missing fields: {', '.join(sorted(missing))}")
            continue

        prefix = value.get("id_prefix")
        if not isinstance(prefix, str) or not re.fullmatch(
            r"HWR-(SCOPE|PIPE|OBJ|RESOLVE|REVIEW|BENCH)", prefix
        ):
            errors.append(f"{label}.id_prefix is invalid: {prefix!r}")
        elif prefix in prefixes:
            errors.append(f"duplicate requirement ID prefix: {prefix}")
        else:
            prefixes.add(prefix)

        owner = value.get("owner")
        if owner not in ALLOWED_OWNERS:
            errors.append(f"{label}.owner is invalid: {owner!r}")

        validate_string_list(
            value.get("profiles"), f"{label}.profiles", ALLOWED_PROFILES, errors
        )

        method = value.get("verification_method")
        if method not in ALLOWED_METHODS:
            errors.append(f"{label}.verification_method is invalid: {method!r}")

        validated[rfc_id] = value

    return validated


def validate_retired_requirements(
    retired: object,
    indexed_rfc_ids: set[str],
    seen_ids: set[str],
    errors: list[str],
) -> int:
    if not isinstance(retired, list):
        errors.append("retired_requirements must be an array")
        return 0

    for index, requirement in enumerate(retired):
        label = f"retired_requirements[{index}]"
        if not isinstance(requirement, dict):
            errors.append(f"{label} must be an object")
            continue
        required = {"id", "rfc", "removed_in", "reason"}
        missing = required - requirement.keys()
        if missing:
            errors.append(f"{label} missing fields: {', '.join(sorted(missing))}")
            continue

        requirement_id = requirement.get("id")
        if (
            not isinstance(requirement_id, str)
            or not REQUIREMENT_ID_RE.fullmatch(requirement_id)
        ):
            errors.append(f"{label}.id is invalid: {requirement_id!r}")
        elif requirement_id in seen_ids:
            errors.append(f"duplicate active or retired requirement ID: {requirement_id}")
        else:
            seen_ids.add(requirement_id)

        if requirement.get("rfc") not in indexed_rfc_ids:
            errors.append(f"{label}.rfc references an unknown RFC")
        for field in ("removed_in", "reason"):
            if not isinstance(requirement.get(field), str) or not requirement[field].strip():
                errors.append(f"{label}.{field} must be a non-empty string")

    return len(retired)


def validate_requirements(
    root: Path = ROOT,
    errors: Optional[list[str]] = None,
) -> tuple[int, int, int, int, int, int, int]:
    """Return active, MUST, MUST NOT, SHOULD, SHOULD NOT, verified, retired."""

    if errors is None:
        errors = []

    requirements_path = root / "conformance/requirements.json"
    rfc_registry_path = root / "registry/rfcs.json"
    manifest = load_json(requirements_path, errors)
    registry = load_json(rfc_registry_path, errors)

    if manifest.get("schema_version") != "1.0":
        errors.append("conformance schema_version must equal '1.0'")
    if manifest.get("spec_revision") != registry.get("version"):
        errors.append(
            "conformance spec_revision must equal registry/rfcs.json version "
            f"({registry.get('version')!r})"
        )

    rfc_entries = registry.get("rfcs", [])
    if not isinstance(rfc_entries, list):
        errors.append("registry/rfcs.json: rfcs must be an array")
        rfc_entries = []

    indexed_rfcs: dict[str, Path] = {}
    for index, entry in enumerate(rfc_entries):
        if not isinstance(entry, dict):
            errors.append(f"registry/rfcs.json rfcs[{index}] must be an object")
            continue
        rfc_id = entry.get("id")
        relative_path = entry.get("path")
        if not isinstance(rfc_id, str) or not isinstance(relative_path, str):
            errors.append(
                f"registry/rfcs.json rfcs[{index}] needs string id and path"
            )
            continue
        indexed_rfcs[rfc_id] = root / relative_path

    indexed_rfc_ids = set(indexed_rfcs)
    defaults = validate_defaults(
        manifest.get("rfc_defaults"), indexed_rfc_ids, errors
    )

    extracted: dict[tuple[str, str, str], dict] = {}
    for rfc_id, path in indexed_rfcs.items():
        if not path.is_file():
            errors.append(f"missing normative RFC: {path.relative_to(root)}")
            continue
        for unit in extract_normative_units(path, rfc_id):
            key = source_key(unit["rfc"], unit["section"], unit["source_text"])
            if key in extracted:
                errors.append(
                    f"duplicate normative source unit in {rfc_id}: "
                    f"{unit['section']} / {unit['source_text']}"
                )
                continue
            extracted[key] = unit

    requirements = manifest.get("requirements", [])
    if not isinstance(requirements, list):
        errors.append("requirements must be an array")
        requirements = []

    seen_ids: set[str] = set()
    mapped_sources: dict[tuple[str, str, str], str] = {}
    verified_count = 0
    positive_count = 0
    negative_count = 0
    recommendation_count = 0
    negative_recommendation_count = 0

    for index, requirement in enumerate(requirements):
        label = f"requirements[{index}]"
        if not isinstance(requirement, dict):
            errors.append(f"{label} must be an object")
            continue

        required_fields = {
            "id",
            "rfc",
            "section",
            "source_text",
            "normative_terms",
            "status",
        }
        missing = required_fields - requirement.keys()
        if missing:
            errors.append(f"{label} missing fields: {', '.join(sorted(missing))}")
            continue

        requirement_id = requirement.get("id")
        if (
            not isinstance(requirement_id, str)
            or not REQUIREMENT_ID_RE.fullmatch(requirement_id)
        ):
            errors.append(f"{label}.id is invalid: {requirement_id!r}")
        elif requirement_id in seen_ids:
            errors.append(f"duplicate requirement ID: {requirement_id}")
        else:
            seen_ids.add(requirement_id)

        rfc_id = requirement.get("rfc")
        if rfc_id not in indexed_rfc_ids:
            errors.append(f"{label}.rfc references unknown RFC: {rfc_id!r}")
        default = defaults.get(rfc_id, {})
        prefix = default.get("id_prefix")
        if (
            isinstance(requirement_id, str)
            and isinstance(prefix, str)
            and not requirement_id.startswith(f"{prefix}-")
        ):
            errors.append(
                f"{requirement_id} does not use the {rfc_id} prefix {prefix}-"
            )

        section = requirement.get("section")
        source_text = requirement.get("source_text")
        if not isinstance(section, str) or not section.strip():
            errors.append(f"{label}.section must be a non-empty string")
            section = ""
        if not isinstance(source_text, str) or not source_text.strip():
            errors.append(f"{label}.source_text must be a non-empty string")
            source_text = ""

        key = source_key(str(rfc_id), section, source_text)
        if key in mapped_sources:
            errors.append(
                f"{label} duplicates source mapped by {mapped_sources[key]}"
            )
        else:
            mapped_sources[key] = str(requirement_id)

        actual = extracted.get(key)
        if actual is None:
            errors.append(
                f"{requirement_id} is stale or its RFC source changed: "
                f"{rfc_id} / {section} / {source_text}"
            )

        terms = requirement.get("normative_terms")
        if (
            not isinstance(terms, dict)
            or set(terms) != {"must", "must_not", "should", "should_not"}
            or not all(
                isinstance(terms.get(name), int) and terms[name] >= 0
                for name in ("must", "must_not", "should", "should_not")
            )
        ):
            errors.append(
                f"{label}.normative_terms must contain non-negative integers "
                "must, must_not, should, and should_not"
            )
        else:
            positive_count += terms["must"]
            negative_count += terms["must_not"]
            recommendation_count += terms["should"]
            negative_recommendation_count += terms["should_not"]
            if actual is not None and terms != actual["normative_terms"]:
                errors.append(
                    f"{requirement_id} normative term counts changed: "
                    f"matrix={terms}, source={actual['normative_terms']}"
                )

        owner = requirement.get("owner", default.get("owner"))
        if owner not in ALLOWED_OWNERS:
            errors.append(f"{label}.owner is invalid after defaults: {owner!r}")

        profiles = requirement.get("profiles", default.get("profiles"))
        validate_string_list(
            profiles, f"{label}.profiles after defaults", ALLOWED_PROFILES, errors
        )

        method = requirement.get(
            "verification_method", default.get("verification_method")
        )
        if method not in ALLOWED_METHODS:
            errors.append(
                f"{label}.verification_method is invalid after defaults: {method!r}"
            )

        status = requirement.get("status")
        if status not in ALLOWED_STATUSES:
            errors.append(f"{label}.status is invalid: {status!r}")
        if status == "verified":
            verified_count += 1
            if not isinstance(requirement.get("evidence"), str) or not requirement[
                "evidence"
            ].strip():
                errors.append(f"{label}.evidence is required when status is verified")
        if status == "not-applicable":
            if not isinstance(requirement.get("rationale"), str) or not requirement[
                "rationale"
            ].strip():
                errors.append(
                    f"{label}.rationale is required when status is not-applicable"
                )

    for key, unit in extracted.items():
        if key not in mapped_sources:
            errors.append(
                "unmapped normative source unit: "
                f"{unit['rfc']}:{unit['line']} [{unit['section']}] "
                f"{unit['source_text']}"
            )

    retired_count = validate_retired_requirements(
        manifest.get("retired_requirements", []),
        indexed_rfc_ids,
        seen_ids,
        errors,
    )

    extracted_positive = sum(
        unit["normative_terms"]["must"] for unit in extracted.values()
    )
    extracted_negative = sum(
        unit["normative_terms"]["must_not"] for unit in extracted.values()
    )
    extracted_recommendations = sum(
        unit["normative_terms"]["should"] for unit in extracted.values()
    )
    extracted_negative_recommendations = sum(
        unit["normative_terms"]["should_not"] for unit in extracted.values()
    )
    if positive_count != extracted_positive:
        errors.append(
            f"matrix covers {positive_count} MUST terms; source has "
            f"{extracted_positive}"
        )
    if negative_count != extracted_negative:
        errors.append(
            f"matrix covers {negative_count} MUST NOT terms; source has "
            f"{extracted_negative}"
        )
    if recommendation_count != extracted_recommendations:
        errors.append(
            f"matrix covers {recommendation_count} SHOULD terms; source has "
            f"{extracted_recommendations}"
        )
    if negative_recommendation_count != extracted_negative_recommendations:
        errors.append(
            "matrix covers "
            f"{negative_recommendation_count} SHOULD NOT terms; source has "
            f"{extracted_negative_recommendations}"
        )

    return (
        len(requirements),
        positive_count,
        negative_count,
        recommendation_count,
        negative_recommendation_count,
        verified_count,
        retired_count,
    )


def main() -> None:
    errors: list[str] = []
    (
        active,
        must,
        must_not,
        should,
        should_not,
        verified,
        retired,
    ) = validate_requirements(ROOT, errors)
    if errors:
        raise SystemExit("\n".join(errors))
    print(
        "OK: "
        f"{active} active requirements, "
        f"{must} MUST terms, "
        f"{must_not} MUST NOT terms, "
        f"{should} SHOULD terms, "
        f"{should_not} SHOULD NOT terms, "
        f"{verified} verified, "
        f"{retired} retired"
    )


if __name__ == "__main__":
    main()
