import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.hwr_benchmark import (
    prepare_case_context,
    read_bounded_json,
    run_benchmark,
    validate_benchmark_case,
    validate_benchmark_plan,
    validate_benchmark_run_record,
)
from tools.hwr_reference import HwrError, load_repository


ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "benchmarks/plans/offline-fixture-science-001.json"
CASE_PATHS = sorted((ROOT / "benchmarks/cases").glob("*.json"))
FIXTURE_ADAPTER_PATH = ROOT / "tools/hwr_benchmark_fixture_adapter.py"
RUNNER_PATH = ROOT / "tools/hwr_benchmark.py"


class BenchmarkRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repository = load_repository(ROOT)
        cls.plan = read_bounded_json(PLAN_PATH, "benchmark plan")

    def test_checked_in_cases_are_structurally_and_context_valid(self) -> None:
        self.assertEqual(2, len(CASE_PATHS))
        for case_path in CASE_PATHS:
            with self.subTest(case=case_path.name):
                case = read_bounded_json(case_path, "benchmark case")
                self.assertEqual([], validate_benchmark_case(case))
                task, _, run = prepare_case_context(self.repository, case)
                self.assertEqual("context-ready", run["state"])
                self.assertTrue(
                    all(
                        source.get("snapshot", {}).get("content")
                        for source in task["sources"]
                    )
                )

    def test_offline_runner_preserves_common_inputs_and_treatment_boundary(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory) / "run"
            manifest, warnings = run_benchmark(
                self.repository,
                self.plan,
                plan_path=PLAN_PATH,
                workspace=workspace,
                executable=sys.executable,
                arguments=[str(FIXTURE_ADAPTER_PATH)],
                pass_env=[],
            )

            baseline_packet = json.loads(
                (
                    workspace
                    / "attempts/r01-baseline/packet.json"
                ).read_text(encoding="utf-8")
            )
            rules_packet = json.loads(
                (
                    workspace
                    / "attempts/r01-rules-assisted/packet.json"
                ).read_text(encoding="utf-8")
            )

        self.assertEqual("complete", manifest["status"])
        self.assertEqual(2, manifest["counts"]["attempted"])
        self.assertEqual(2, manifest["counts"]["completed"])
        self.assertEqual(0, manifest["counts"]["excluded"])
        self.assertEqual([], warnings)
        self.assertEqual(
            baseline_packet["common_input"],
            rules_packet["common_input"],
        )
        self.assertIsNone(baseline_packet["treatment_context"])
        self.assertIsInstance(rules_packet["treatment_context"], dict)
        self.assertTrue(rules_packet["treatment_context"]["module_manifest"])
        self.assertEqual("not-run", manifest["evaluation"]["status"])
        self.assertIn("No comparative conclusion", manifest["evaluation"]["conclusion"])
        self.assertEqual([], validate_benchmark_run_record(manifest))

    def test_adapter_failure_is_preserved_without_discarding_other_arm(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            manifest, _ = run_benchmark(
                self.repository,
                self.plan,
                plan_path=PLAN_PATH,
                workspace=Path(temporary_directory) / "run",
                executable=sys.executable,
                arguments=[
                    str(FIXTURE_ADAPTER_PATH),
                    "--fail-arm",
                    "baseline",
                ],
                pass_env=[],
            )

        self.assertEqual("complete-with-failures", manifest["status"])
        self.assertEqual(1, manifest["counts"]["failed"])
        self.assertEqual(1, manifest["counts"]["completed"])
        baseline = manifest["attempts"][0]
        rules = manifest["attempts"][1]
        self.assertEqual("failed", baseline["status"])
        self.assertEqual("ADAPTER_FAILED", baseline["error"]["code"])
        self.assertEqual("completed", rules["status"])

    def test_invalid_adapter_results_are_retained_as_invalid_attempts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory) / "run"
            manifest, _ = run_benchmark(
                self.repository,
                self.plan,
                plan_path=PLAN_PATH,
                workspace=workspace,
                executable=sys.executable,
                arguments=[
                    "-c",
                    "import sys; sys.stdin.read(); print('{}')",
                ],
                pass_env=[],
            )

            raw_results = list(workspace.glob("attempts/*/result-raw.json"))

        self.assertEqual("complete-with-failures", manifest["status"])
        self.assertEqual(2, manifest["counts"]["invalid"])
        self.assertEqual(2, len(raw_results))
        self.assertTrue(
            all(
                attempt["error"]["code"] == "BENCHMARK_RESULT_INVALID"
                for attempt in manifest["attempts"]
            )
        )

    def test_plan_safety_limits_and_cli(self) -> None:
        invalid = copy.deepcopy(self.plan)
        invalid["repetitions"] = 11
        invalid["controls"]["retry_policy"] = "retry-until-favorable"
        errors = validate_benchmark_plan(invalid)
        self.assertTrue(any("repetitions" in error for error in errors))
        self.assertTrue(any("retry_policy" in error for error in errors))

        with tempfile.TemporaryDirectory() as temporary_directory:
            result = subprocess.run(
                [
                    "python3",
                    str(RUNNER_PATH),
                    "--plan",
                    str(PLAN_PATH),
                    "--workspace",
                    str(Path(temporary_directory) / "run"),
                    "--executable",
                    sys.executable,
                    "--arg",
                    str(FIXTURE_ADAPTER_PATH),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        self.assertEqual(0, result.returncode, result.stderr)
        envelope = json.loads(result.stdout)
        self.assertTrue(envelope["ok"])
        self.assertEqual("complete", envelope["data"]["status"])

    def test_non_empty_workspace_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            workspace = Path(temporary_directory)
            (workspace / "existing.txt").write_text("keep", encoding="utf-8")
            with self.assertRaises(HwrError) as raised:
                run_benchmark(
                    self.repository,
                    self.plan,
                    plan_path=PLAN_PATH,
                    workspace=workspace,
                    executable=sys.executable,
                    arguments=[str(FIXTURE_ADAPTER_PATH)],
                    pass_env=[],
                )
        self.assertEqual("BENCHMARK_WORKSPACE_NOT_EMPTY", raised.exception.code)


if __name__ == "__main__":
    unittest.main()
