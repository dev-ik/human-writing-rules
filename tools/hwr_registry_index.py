#!/usr/bin/env python3
"""Build and verify the deterministic consolidated HWR registry index."""

import argparse
import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path
from typing import Optional

try:
    from .hwr_reference import HwrError, REGISTRY_FILES, load_repository
except ImportError:
    from hwr_reference import HwrError, REGISTRY_FILES, load_repository


GENERATED_INDEX_SCHEMA = (
    "https://human-writing-rules.example/"
    "schemas/generated-registry-index.schema.json"
)
GENERATED_INDEX_VERSION = "1.0"
MAX_GENERATED_INDEX_BYTES = 10 * 1024 * 1024
DEFAULT_REPOSITORY = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = Path("registry/generated-index.json")
VALUE_INDEXES = (
    ("languages", "languages"),
    ("formats", "formats"),
    ("topics", "topics"),
    ("platforms", "platforms"),
    ("skills", "skills"),
    ("tones", "tones"),
)
SELECTOR_FIELDS = ("languages", "platforms", "formats", "topics")


def keyed_entries(entries: object, label: str) -> dict[str, dict]:
    if not isinstance(entries, list):
        raise HwrError(
            "REGISTRY_INDEX_SOURCE_INVALID",
            f"{label} must be an array",
        )
    result: dict[str, dict] = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise HwrError(
                "REGISTRY_INDEX_SOURCE_INVALID",
                f"{label}[{index}] must be an object",
            )
        entry_id = entry.get("id")
        if not isinstance(entry_id, str) or not entry_id:
            raise HwrError(
                "REGISTRY_INDEX_SOURCE_INVALID",
                f"{label}[{index}].id must be a non-empty string",
            )
        if entry_id in result:
            raise HwrError(
                "REGISTRY_INDEX_SOURCE_INVALID",
                f"{label} contains duplicate ID {entry_id}",
            )
        result[entry_id] = {
            key: value for key, value in entry.items() if key != "id"
        }
    return {entry_id: result[entry_id] for entry_id in sorted(result)}


def build_generated_registry_index(repository: dict) -> dict:
    objects: dict[str, dict] = {}
    for source in sorted(repository["objects"], key=lambda item: item["id"]):
        selectors = {
            field: list(source.get(field, []))
            for field in SELECTOR_FIELDS
            if source.get(field)
        }
        record = {
            "kind": source["kind"],
            "title": source["title"],
            "status": source["status"],
            "path": source["path"],
            "requires": list(source.get("requires", [])),
        }
        if source.get("tags"):
            record["tags"] = list(source["tags"])
        if selectors:
            record["selectors"] = selectors
        objects[source["id"]] = record

    values: dict[str, dict[str, dict]] = {}
    counts = {"objects": len(objects)}
    for registry_name, collection_key in VALUE_INDEXES:
        registry = repository["registries"][registry_name]
        values[registry_name] = keyed_entries(
            registry.get(collection_key),
            f"registry/{registry_name}.json:{collection_key}",
        )
        counts[registry_name] = len(values[registry_name])

    rfcs = keyed_entries(
        repository["registries"]["rfcs"].get("rfcs"),
        "registry/rfcs.json:rfcs",
    )
    counts["rfcs"] = len(rfcs)
    return {
        "$schema": GENERATED_INDEX_SCHEMA,
        "schema_version": GENERATED_INDEX_VERSION,
        "spec_revision": repository["spec_revision"],
        "source_revision": repository["registry_revision"],
        "source_files": [f"registry/{name}" for name in REGISTRY_FILES],
        "counts": counts,
        "defaults": {
            "topic_fallback": repository["registries"]["topics"].get("fallback"),
        },
        "objects": objects,
        "values": values,
        "rfcs": rfcs,
    }


def render_generated_registry_index(index: dict) -> str:
    return json.dumps(
        index,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"


def atomic_write(path: Path, content: str) -> None:
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
            temporary.write(content)
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
            "REGISTRY_INDEX_WRITE_FAILED",
            f"Generated registry index could not be written: {path}",
            [{"error_type": type(exc).__name__}],
        ) from exc


def check_generated_registry_index(path: Path, expected: dict) -> dict:
    expected_text = render_generated_registry_index(expected)
    try:
        with path.open("rb") as stream:
            actual_bytes = stream.read(MAX_GENERATED_INDEX_BYTES + 1)
    except FileNotFoundError as exc:
        raise HwrError(
            "GENERATED_REGISTRY_INDEX_MISSING",
            f"Generated registry index does not exist: {path}",
        ) from exc
    except OSError as exc:
        raise HwrError(
            "GENERATED_REGISTRY_INDEX_READ_FAILED",
            f"Generated registry index could not be read: {path}",
            [{"error_type": type(exc).__name__}],
        ) from exc
    if len(actual_bytes) > MAX_GENERATED_INDEX_BYTES:
        raise HwrError(
            "GENERATED_REGISTRY_INDEX_TOO_LARGE",
            f"Generated registry index exceeds {MAX_GENERATED_INDEX_BYTES} bytes",
        )
    try:
        actual_text = actual_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HwrError(
            "GENERATED_REGISTRY_INDEX_ENCODING",
            "Generated registry index must be UTF-8",
        ) from exc
    try:
        actual = json.loads(actual_text)
    except json.JSONDecodeError as exc:
        raise HwrError(
            "GENERATED_REGISTRY_INDEX_INVALID",
            f"Generated registry index is invalid JSON: {exc.msg}",
        ) from exc
    if actual != expected:
        raise HwrError(
            "GENERATED_REGISTRY_INDEX_STALE",
            "Generated registry index does not match canonical registries",
            [
                {
                    "expected_sha256": hashlib.sha256(
                        expected_text.encode("utf-8")
                    ).hexdigest(),
                    "actual_sha256": hashlib.sha256(actual_bytes).hexdigest(),
                }
            ],
        )
    if actual_text != expected_text:
        raise HwrError(
            "GENERATED_REGISTRY_INDEX_NON_CANONICAL",
            "Generated registry index has non-canonical formatting",
        )
    return {
        "valid": True,
        "file": str(path),
        "source_revision": expected["source_revision"],
        "objects": expected["counts"]["objects"],
        "values": sum(
            count
            for name, count in expected["counts"].items()
            if name not in {"objects", "rfcs"}
        ),
        "rfcs": expected["counts"]["rfcs"],
        "bytes": len(actual_bytes),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build or verify the deterministic consolidated registry index."
    )
    parser.add_argument(
        "--repo",
        default=str(DEFAULT_REPOSITORY),
        help="Human Writing Rules repository root.",
    )
    parser.add_argument(
        "--out",
        default=str(DEFAULT_OUTPUT),
        help="Output path, relative to --repo unless absolute.",
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--write", action="store_true")
    action.add_argument("--check", action="store_true")
    action.add_argument("--stdout", action="store_true")
    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    repository_root = Path(args.repo).expanduser().resolve()
    output = Path(args.out).expanduser()
    if not output.is_absolute():
        output = repository_root / output
    try:
        repository = load_repository(repository_root)
        generated = build_generated_registry_index(repository)
        if args.stdout:
            sys.stdout.write(render_generated_registry_index(generated))
            return 0
        if args.write:
            atomic_write(output, render_generated_registry_index(generated))
            result = {
                "written": True,
                "file": str(output),
                "source_revision": generated["source_revision"],
            }
        else:
            result = check_generated_registry_index(output, generated)
    except HwrError as exc:
        print(f"error [{exc.code}]: {exc.message}", file=sys.stderr)
        for detail in exc.details:
            print(f"  {detail}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
