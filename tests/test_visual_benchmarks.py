import copy
import json
import subprocess
import unittest
from pathlib import Path

from tools.hwr_visual_benchmarks import (
    DIMENSIONS,
    read_bounded_json,
    validate_checked_in_visual_benchmarks,
    validate_visual_fixture,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = ROOT / "benchmarks/visual-fixtures"
ACCEPTANCE_DIR = ROOT / "benchmarks/visual-acceptance"
RUNNER_PATH = ROOT / "tools/hwr_visual_benchmarks.py"


def load_fixture(name: str) -> tuple[dict, dict]:
    fixture = read_bounded_json(FIXTURE_DIR / name, f"fixture {name}")
    acceptance = read_bounded_json(
        ROOT / fixture["acceptance_path"],
        f"acceptance for {name}",
    )
    return fixture, acceptance


class VisualBenchmarkTests(unittest.TestCase):
    def test_checked_in_fixtures_are_valid(self) -> None:
        summary, errors = validate_checked_in_visual_benchmarks(ROOT)
        self.assertEqual([], errors)
        self.assertEqual(3, summary["fixtures"])
        self.assertEqual(2, summary["passed"])
        self.assertEqual(1, summary["failed"])
        self.assertEqual(2, summary["assets_checked"])

    def test_auto_none_does_not_evaluate_asset_dimensions(self) -> None:
        fixture, acceptance = load_fixture(
            "auto-none-repository-announcement-001.json"
        )
        self.assertEqual("auto", fixture["requested_mode"])
        self.assertEqual("none", fixture["decision"])
        self.assertFalse(acceptance["asset_evaluated"])
        dimensions = {item["id"]: item for item in acceptance["dimensions"]}
        self.assertEqual(set(DIMENSIONS), set(dimensions))
        self.assertTrue(dimensions["media_decision"]["applies"])
        self.assertEqual("pass", dimensions["media_decision"]["verdict"])
        for dimension_id in DIMENSIONS[1:]:
            self.assertFalse(dimensions[dimension_id]["applies"])
            self.assertEqual(
                "not-applicable",
                dimensions[dimension_id]["verdict"],
            )

    def test_selected_fixture_checks_real_png_and_all_dimensions(self) -> None:
        fixture, acceptance = load_fixture("selected-mysticism-cover-001.json")
        errors, assets_checked, overall = validate_visual_fixture(
            fixture,
            ROOT,
            acceptance_override=acceptance,
        )
        self.assertEqual([], errors)
        self.assertEqual(1, assets_checked)
        self.assertEqual("pass", overall)
        self.assertEqual(1536, fixture["asset"]["width"])
        self.assertEqual(1024, fixture["asset"]["height"])
        self.assertTrue(acceptance["asset_evaluated"])
        self.assertTrue(all(item["applies"] for item in acceptance["dimensions"]))

    def test_negative_fixture_preserves_hard_failure(self) -> None:
        fixture, acceptance = load_fixture(
            "false-documentary-mysticism-cover-001.json"
        )
        errors, assets_checked, overall = validate_visual_fixture(
            fixture,
            ROOT,
            acceptance_override=acceptance,
        )
        self.assertEqual([], errors)
        self.assertEqual(1, assets_checked)
        self.assertEqual("fail", overall)
        statuses = {
            item["id"]: item["status"] for item in acceptance["hard_failures"]
        }
        self.assertEqual("triggered", statuses["false-documentary-visual"])

    def test_auto_none_rejects_asset_evaluation(self) -> None:
        fixture, acceptance = load_fixture(
            "auto-none-repository-announcement-001.json"
        )
        mutated = copy.deepcopy(acceptance)
        mutated["asset_evaluated"] = True
        errors, _, _ = validate_visual_fixture(
            fixture,
            ROOT,
            acceptance_override=mutated,
        )
        self.assertTrue(any("asset_evaluated must be False" in error for error in errors))

    def test_required_visual_can_be_recorded_as_blocked(self) -> None:
        fixture, acceptance = load_fixture(
            "auto-none-repository-announcement-001.json"
        )
        blocked_fixture = copy.deepcopy(fixture)
        blocked_fixture["fixture_purpose"] = "boundary"
        blocked_fixture["requested_mode"] = "required"
        blocked_fixture["decision"] = "blocked"
        blocked_fixture["expected_overall"] = "blocked"
        blocked_acceptance = copy.deepcopy(acceptance)
        blocked_acceptance["overall"] = "blocked"
        blocked_acceptance["dimensions"][0]["verdict"] = "fail"
        errors, assets_checked, overall = validate_visual_fixture(
            blocked_fixture,
            ROOT,
            acceptance_override=blocked_acceptance,
        )
        self.assertEqual([], errors)
        self.assertEqual(0, assets_checked)
        self.assertEqual("blocked", overall)

    def test_selected_fixture_rejects_wrong_asset_digest(self) -> None:
        fixture, acceptance = load_fixture("selected-mysticism-cover-001.json")
        mutated = copy.deepcopy(fixture)
        mutated["asset"]["sha256"] = "0" * 64
        errors, _, _ = validate_visual_fixture(
            mutated,
            ROOT,
            acceptance_override=acceptance,
        )
        self.assertTrue(any("asset.sha256 mismatch" in error for error in errors))

    def test_cli_check(self) -> None:
        result = subprocess.run(
            ["python3", str(RUNNER_PATH), "--check"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        envelope = json.loads(result.stdout)
        self.assertTrue(envelope["ok"])
        self.assertEqual(3, envelope["data"]["fixtures"])


if __name__ == "__main__":
    unittest.main()
