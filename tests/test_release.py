import copy
import json
import subprocess
import unittest
from pathlib import Path

from tools.hwr_release import (
    MANIFEST_PATH,
    read_bounded_json,
    validate_checked_in_release,
    validate_release_manifest,
)


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "tools/hwr_release.py"


class ReleaseCandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = read_bounded_json(MANIFEST_PATH, "release manifest")

    def test_checked_in_candidate_is_valid(self) -> None:
        summary, errors = validate_checked_in_release(ROOT)
        self.assertEqual([], errors)
        self.assertEqual("1.0.0", summary["release"])
        self.assertEqual("candidate", summary["status"])
        self.assertEqual("stable", summary["channel"])
        self.assertEqual(8, summary["gates"])
        self.assertEqual(22, summary["artifacts"])
        self.assertEqual(200, summary["counts"]["requirements"])
        self.assertEqual(16, summary["counts"]["reviewed_examples"])

    def test_version_files_match_candidate(self) -> None:
        version = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
        package = read_bounded_json(ROOT / "package.json", "package.json")
        self.assertEqual(self.manifest["release"], version)
        self.assertEqual(self.manifest["release"], package["version"])
        self.assertTrue(package["private"])

    def test_spec_revision_mismatch_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.manifest)
        mutated["spec_revision"] = "1.0.1"
        _, errors = validate_release_manifest(mutated, ROOT)
        self.assertTrue(
            any("spec_revision does not match" in error for error in errors)
        )

    def test_registry_source_revision_mismatch_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.manifest)
        mutated["registry_source_revision"] = "sha256:" + "0" * 64
        _, errors = validate_release_manifest(mutated, ROOT)
        self.assertTrue(
            any(
                "registry_source_revision does not match" in error
                for error in errors
            )
        )

    def test_stable_channel_requires_stable_compatibility(self) -> None:
        mutated = copy.deepcopy(self.manifest)
        mutated["compatibility"]["stability"] = "pre-stable"
        _, errors = validate_release_manifest(mutated, ROOT)
        self.assertTrue(
            any(
                "stable channel requires stable compatibility" in error
                for error in errors
            )
        )

    def test_stable_channel_rejects_prerelease_version(self) -> None:
        mutated = copy.deepcopy(self.manifest)
        mutated["release"] = "1.0.1-rc.1"
        _, errors = validate_release_manifest(mutated, ROOT)
        self.assertTrue(
            any(
                "stable channel requires a final release version" in error
                for error in errors
            )
        )

    def test_missing_gate_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.manifest)
        mutated["gates"] = [
            gate for gate in mutated["gates"] if gate["id"] != "unit-tests"
        ]
        _, errors = validate_release_manifest(mutated, ROOT)
        self.assertTrue(any("release gates missing: unit-tests" in error for error in errors))

    def test_gate_command_substitution_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.manifest)
        mutated["gates"][0]["argv"] = ["python3", "-c", "print('skip')"]
        _, errors = validate_release_manifest(mutated, ROOT)
        self.assertTrue(any("not the canonical command" in error for error in errors))

    def test_missing_required_artifact_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.manifest)
        mutated["required_artifacts"].remove("COMPATIBILITY.md")
        _, errors = validate_release_manifest(mutated, ROOT)
        self.assertTrue(
            any(
                "required_artifacts missing: COMPATIBILITY.md" in error
                for error in errors
            )
        )

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
        self.assertEqual("candidate", envelope["data"]["status"])


if __name__ == "__main__":
    unittest.main()
