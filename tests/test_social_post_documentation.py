import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SocialPostDocumentationTests(unittest.TestCase):
    def test_social_format_and_platform_objects_are_registered(self) -> None:
        registry = json.loads(
            (ROOT / "registry/objects.json").read_text(encoding="utf-8")
        )
        by_id = {entry["id"]: entry for entry in registry["objects"]}

        social_post = by_id["format.social-post.foundation"]
        self.assertEqual(["social-post"], social_post["formats"])
        self.assertTrue(
            {
                "core.writing-pipeline",
                "rule.source-integrity",
                "rule.human-signals.core",
                "rule.style.no-template-pressure",
            }.issubset(social_post["requires"])
        )

        social = by_id["platform.social.foundation"]
        self.assertEqual(["social"], social["platforms"])
        self.assertEqual(["social-post"], social["formats"])

        for platform in ("telegram", "linkedin"):
            with self.subTest(platform=platform):
                entry = by_id[f"platform.{platform}.foundation"]
                self.assertEqual([platform], entry["platforms"])
                self.assertEqual(["social-post"], entry["formats"])
                self.assertIn("platform.social.foundation", entry["requires"])

    def test_guide_covers_the_full_social_post_run(self) -> None:
        text = (
            ROOT / "guides/social-post-production.md"
        ).read_text(encoding="utf-8")
        required_headings = [
            "## Start a run",
            "## Step 1 — Create the post control record",
            "## Step 2 — Select the post job and form",
            "## Step 3 — Build the evidence boundary",
            "## Step 4 — Pass the context gate",
            "## Step 5 — Design the post",
            "## Step 6 — Make the media decision",
            "## Step 7 — Draft for meaning",
            "## Step 8 — Adapt to the platform",
            "## Step 9 — Apply the topic profile",
            "## Step 10 — Review, revise, and package",
            "## Adapting a finished article",
            "## Final release checklist",
        ]

        for heading in required_headings:
            with self.subTest(heading=heading):
                self.assertIn(heading, text)

    def test_runtime_modules_define_control_media_and_platform_boundaries(self) -> None:
        social_format = (
            ROOT / "rules/format/social-post/foundation.md"
        ).read_text(encoding="utf-8")
        for heading in (
            "## Post control record",
            "## Claim budget",
            "## Context gate",
            "## Media decision",
            "## Draft and compression",
            "## Ordered series",
            "## Completion gate",
            "## Blocked result",
        ):
            with self.subTest(module="social-post", heading=heading):
                self.assertIn(heading, social_format)

        expected_platform_sections = {
            "social": [
                "## Platform record",
                "## Feed context",
                "## Platform elements",
                "## Media",
            ],
            "telegram": [
                "## Message design",
                "## Links and distribution",
                "## Media",
            ],
            "linkedin": [
                "## Professional context",
                "## Claims and next steps",
                "## Links and media",
            ],
        }
        for platform, headings in expected_platform_sections.items():
            text = (
                ROOT / f"rules/platform/{platform}/foundation.md"
            ).read_text(encoding="utf-8")
            for heading in headings:
                with self.subTest(platform=platform, heading=heading):
                    self.assertIn(heading, text)

    def test_topic_social_examples_expose_complete_artifact_packages(self) -> None:
        paths = [
            ROOT / "examples/ru/telegram/science-explainer.md",
            ROOT / "examples/ru/linkedin/technology-explainer.md",
            ROOT / "examples/ru/social/entertainment-review.md",
            ROOT / "examples/ru/telegram/product-launch.md",
            ROOT / "examples/en/linkedin/opensource.md",
        ]
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

        for path in paths:
            text = path.read_text(encoding="utf-8")
            for section in required_sections:
                with self.subTest(path=path.name, section=section):
                    self.assertIn(section, text)

    def test_readme_and_starter_kit_expose_social_guide(self) -> None:
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        starter = (ROOT / "starter-kit/README.md").read_text(encoding="utf-8")

        self.assertIn(
            "[Producing a grounded social post](guides/social-post-production.md)",
            readme,
        )
        self.assertIn(
            "[Producing a grounded social post]"
            "(../guides/social-post-production.md#start-a-run)",
            starter,
        )


if __name__ == "__main__":
    unittest.main()
