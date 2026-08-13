import copy
import json
import subprocess
import unittest
from pathlib import Path

from tools.hwr_reviewed_examples import (
    CATALOG_PATH,
    read_bounded_json,
    validate_checked_in_reviewed_examples,
    validate_reviewed_example_catalog,
)


ROOT = Path(__file__).resolve().parents[1]
RUNNER_PATH = ROOT / "tools/hwr_reviewed_examples.py"


class ReviewedExampleCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = read_bounded_json(CATALOG_PATH, "reviewed catalog")

    def test_checked_in_catalog_is_valid_and_complete(self) -> None:
        summary, errors = validate_checked_in_reviewed_examples(ROOT)
        self.assertEqual([], errors)
        self.assertEqual(21, summary["examples"])
        self.assertEqual(11, summary["topics_covered"])
        self.assertEqual(11, summary["platforms_covered"])
        self.assertEqual(2, summary["languages_covered"])
        self.assertEqual(14, summary["articles"])
        self.assertEqual(7, summary["social_posts"])

    def test_catalog_covers_every_registered_topic_and_platform(self) -> None:
        topics = {
            item["id"]
            for item in read_bounded_json(
                ROOT / "registry/topics.json",
                "topic registry",
            )["topics"]
        }
        platforms = {
            item["id"]
            for item in read_bounded_json(
                ROOT / "registry/platforms.json",
                "platform registry",
            )["platforms"]
        }
        covered_topics = {item["topic"] for item in self.catalog["examples"]}
        covered_platforms = {item["platform"] for item in self.catalog["examples"]}
        self.assertEqual(topics, covered_topics)
        self.assertEqual(platforms, covered_platforms)

    def test_wrong_artifact_digest_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.catalog)
        mutated["examples"][0]["sha256"] = "0" * 64
        _, errors = validate_reviewed_example_catalog(mutated, ROOT)
        self.assertTrue(any("sha256 mismatch" in error for error in errors))

    def test_missing_topic_coverage_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.catalog)
        mutated["examples"] = [
            item for item in mutated["examples"] if item["topic"] != "general"
        ]
        _, errors = validate_reviewed_example_catalog(mutated, ROOT)
        self.assertTrue(
            any("missing topic coverage: general" in error for error in errors)
        )

    def test_auto_visual_requires_visual_reviewer(self) -> None:
        mutated = copy.deepcopy(self.catalog)
        science = next(
            item
            for item in mutated["examples"]
            if item["id"] == "example.ru.article.science"
        )
        science["reviewers"].remove("reviewer.visual")
        _, errors = validate_reviewed_example_catalog(mutated, ROOT)
        self.assertTrue(any("requires reviewer.visual" in error for error in errors))

    def test_none_mode_cannot_select_visual(self) -> None:
        mutated = copy.deepcopy(self.catalog)
        mutated["examples"][0]["visual_decision"] = "selected-brief"
        _, errors = validate_reviewed_example_catalog(mutated, ROOT)
        self.assertTrue(
            any("visual mode none requires decision none" in error for error in errors)
        )

    def test_noncanonical_coverage_policy_is_rejected(self) -> None:
        mutated = copy.deepcopy(self.catalog)
        mutated["coverage_policy"]["cross_product_required"] = True
        _, errors = validate_reviewed_example_catalog(mutated, ROOT)
        self.assertTrue(
            any("cross_product_required must be false" in error for error in errors)
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
        self.assertEqual(21, envelope["data"]["examples"])


if __name__ == "__main__":
    unittest.main()
