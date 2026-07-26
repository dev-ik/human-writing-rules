#!/usr/bin/env python3
"""Fixture-only HWR adapter used for offline lifecycle tests and examples."""

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = {
    "design": ROOT / "examples/transitions/ru-science-design.json",
    "draft": ROOT / "examples/transitions/ru-science-draft.json",
    "edit": ROOT / "examples/transitions/ru-science-edit.json",
    "revision": ROOT / "examples/transitions/ru-science-edit.json",
    "visual": ROOT / "examples/transitions/ru-science-visual.json",
    "review": ROOT / "examples/transitions/ru-science-review.json",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--separate-visual",
        action="store_true",
        help="Return no embedded edit visuals so the visual stage is exercised.",
    )
    parser.add_argument(
        "--major-review",
        action="store_true",
        help="Return one unresolved major source finding during review.",
    )
    parser.add_argument(
        "--fixture-dir",
        type=Path,
        help="Read stage JSON files from this directory instead of built-in fixtures.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        packet = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"invalid packet: {exc}", file=sys.stderr)
        return 2
    if not isinstance(packet, dict):
        print("packet root must be an object", file=sys.stderr)
        return 2

    stage = packet.get("stage")
    fixture_path = (
        args.fixture_dir / f"{stage}.json"
        if args.fixture_dir is not None
        else FIXTURES.get(stage)
    )
    if fixture_path is None or not fixture_path.is_file():
        print(f"unsupported fixture stage: {stage!r}", file=sys.stderr)
        return 3

    result = json.loads(fixture_path.read_text(encoding="utf-8"))
    result["run_id"] = packet.get("run_id")
    current_artifact = packet.get("current_artifact") or {}
    if stage == "review":
        result["artifact_revision"] = current_artifact.get("artifact_revision")
        prior_findings = packet.get("review_context", {}).get("findings", [])
        if prior_findings and not args.major_review:
            result["findings"] = [
                {**finding, "status": "fixed"}
                for finding in prior_findings
                if finding.get("severity") in {"blocker", "major"}
            ]
    if stage == "revision":
        result["stage"] = "revision"
        result["artifact_revision"] = "fixture-artifact-revision-1"
        result["parent_revision"] = current_artifact.get("artifact_revision")
        result["addressed_findings"] = [
            finding["id"]
            for finding in packet.get("review_context", {}).get("findings", [])
            if finding.get("severity") in {"blocker", "major"}
            and finding.get("status") in {
                "open",
                "deferred",
                "accepted-risk",
            }
        ]
    if stage == "edit":
        result["parent_revision"] = current_artifact.get("artifact_revision")
    if stage == "visual":
        result["artifact_revision"] = current_artifact.get("artifact_revision")
    if stage == "edit" and args.separate_visual:
        result["visuals"] = []
    if stage == "review" and args.major_review:
        result["review_revision"] = "fixture-review-major-1"
        result["readiness_candidate"] = "not-ready"
        result["reviewers"][0]["status"] = "fail"
        result["findings"] = [
            {
                "id": "fixture-source-major-1",
                "reviewer": "reviewer.source",
                "severity": "major",
                "location": "paragraph-3",
                "summary": "Qualification is too far from the inference",
                "reason": "The claim could be read as measured effectiveness",
                "rule": "rule.source-integrity",
                "claim_ids": ["C-002"],
                "correction": "Keep the qualification in the same sentence",
                "status": "open",
            }
        ]
    json.dump(result, sys.stdout, ensure_ascii=False, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
