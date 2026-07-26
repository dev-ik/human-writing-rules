#!/usr/bin/env python3
"""Offline-only benchmark arm adapter fixture."""

import argparse
import json
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fail-arm")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        packet = json.load(sys.stdin)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        print(f"invalid benchmark packet: {exc}", file=sys.stderr)
        return 2
    if not isinstance(packet, dict) or packet.get("stage") != "benchmark-run":
        print("unsupported benchmark packet", file=sys.stderr)
        return 2
    arm = packet.get("arm", {})
    if arm.get("id") == args.fail_arm:
        print("fixture arm failure", file=sys.stderr)
        return 7

    sources = packet.get("common_input", {}).get("source_records", [])
    treatment = arm.get("treatment")
    treatment_label = (
        "с контекстом Human Writing Rules"
        if treatment == "rules-assisted"
        else "с базовой инструкцией"
    )
    result = {
        "protocol_version": "1.0",
        "attempt_id": packet.get("attempt_id"),
        "case_id": packet.get("case", {}).get("id"),
        "case_revision": packet.get("case", {}).get("revision"),
        "arm_id": arm.get("id"),
        "status": "completed",
        "source_access": [
            {
                "source_id": source.get("id"),
                "status": "available",
            }
            for source in sources
        ],
        "output_unit": {
            "publication_copy": (
                "Офлайн-фикстура benchmark arm "
                f"{arm.get('id')}: запуск {treatment_label}. "
                "Этот текст проверяет протокол исполнения и не является "
                "свидетельством качества."
            ),
            "visual_assets": [],
            "source_notes": {
                "fixture": True,
                "source_count": len(sources),
            },
            "review_report": {
                "status": "not-evaluated",
                "findings": [],
            },
            "audit": {
                "adapter": "hwr-benchmark-fixture",
                "treatment_context_received": (
                    packet.get("treatment_context") is not None
                ),
            },
        },
        "errors": [],
        "manual_interventions": [],
        "hard_failures": [],
    }
    json.dump(result, sys.stdout, ensure_ascii=False, separators=(",", ":"))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
