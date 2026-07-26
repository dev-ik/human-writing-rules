import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ArticleDocumentationTests(unittest.TestCase):
    def test_article_and_topic_objects_are_registered(self) -> None:
        registry = json.loads(
            (ROOT / "registry/objects.json").read_text(encoding="utf-8")
        )
        by_id = {entry["id"]: entry for entry in registry["objects"]}

        article = by_id["format.article.foundation"]
        self.assertEqual(["article"], article["formats"])
        self.assertTrue(
            {
                "core.writing-pipeline",
                "rule.source-integrity",
                "rule.human-signals.core",
                "rule.style.no-template-pressure",
            }.issubset(article["requires"])
        )

        for topic in ("science", "technology", "entertainment"):
            with self.subTest(topic=topic):
                entry = by_id[f"topic.{topic}.foundation"]
                self.assertEqual([topic], entry["topics"])
                self.assertIn("topic.general.foundation", entry["requires"])

    def test_guide_covers_the_full_article_run(self) -> None:
        text = (ROOT / "guides/article-production.md").read_text(encoding="utf-8")
        required_headings = [
            "## Step 1 — Create the article control record",
            "## Step 2 — Select the article job",
            "## Step 3 — Build the research plan",
            "## Step 4 — Pass the context gate",
            "## Step 5 — Design the article",
            "## Step 6 — Make the media decision",
            "## Step 7 — Draft in controlled passes",
            "## Step 8 — Finish article elements",
            "## Step 9 — Review and revise",
            "## Step 10 — Package the result",
            "## Science article profile",
            "## Technology article profile",
            "## Entertainment article profile",
            "## Final release checklist",
        ]

        for heading in required_headings:
            with self.subTest(heading=heading):
                self.assertIn(heading, text)

    def test_topic_modules_define_evidence_visuals_and_completion(self) -> None:
        expected_sections = {
            "science": [
                "## Research object record",
                "## Evidence",
                "## Writing",
                "## Visuals",
                "## Science completion checks",
            ],
            "technology": [
                "## Technical object record",
                "## Evidence",
                "## Writing",
                "## Visuals",
                "## Technology completion checks",
            ],
            "entertainment": [
                "## Work identity record",
                "## Evidence",
                "## Writing",
                "## Visuals",
                "## Entertainment completion checks",
            ],
        }

        for topic, headings in expected_sections.items():
            text = (
                ROOT / f"rules/topic/{topic}/foundation.md"
            ).read_text(encoding="utf-8")
            for heading in headings:
                with self.subTest(topic=topic, heading=heading):
                    self.assertIn(heading, text)

    def test_topic_examples_expose_internal_and_public_artifacts(self) -> None:
        required_sections = [
            "## Task framing",
            "## Resolved modules",
            "## Evidence map",
            "## Context gate",
            "## Content design",
            "## Final artifact",
            "## Media decision",
            "## Source notes",
            "## Review result",
        ]

        for topic in ("science", "technology", "entertainment"):
            text = (
                ROOT / f"examples/ru/article/{topic}.md"
            ).read_text(encoding="utf-8")
            for section in required_sections:
                with self.subTest(topic=topic, section=section):
                    self.assertIn(section, text)

    def test_readme_exposes_article_guide(self) -> None:
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(
            "[Producing a grounded article](guides/article-production.md)",
            text,
        )


if __name__ == "__main__":
    unittest.main()
