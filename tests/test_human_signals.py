import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class HumanSignalsTests(unittest.TestCase):
    def test_human_signal_rules_define_legitimate_texture_and_edit_pass(self) -> None:
        text = (ROOT / "rules/human-signals/core.md").read_text(encoding="utf-8")

        for expected in (
            "## Legitimate human texture",
            "## Thought-shaped variation",
            "## Reader proximity",
            "## Human edit pass",
            "Do not invent texture.",
            "Avoid stock AI-like connective tissue",
            "Replace stock setup, hype, and transition phrases",
            "Do not vary sentence length, add fragments, or break paragraphs merely to simulate spontaneity.",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)

    def test_prohibited_practices_reject_deceptive_humanization(self) -> None:
        text = (
            ROOT / "rules/human-signals/prohibited-practices.md"
        ).read_text(encoding="utf-8")

        for expected in (
            "invented first-person anecdotes",
            "fake uncertainty",
            "deliberate grammar errors",
            "optimize for a detector to classify the text as human-written",
            "defeat AI-detection",
            "style mimicry",
            "reject the deceptive mechanism",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)

    def test_reviewer_checks_reader_proximity_and_legitimate_texture(self) -> None:
        text = (ROOT / "reviewers/human-signals.md").read_text(encoding="utf-8")

        for expected in (
            "Reader proximity is concrete",
            "Human texture is legitimate",
            "Structure follows the material",
            "compressed where it relies on generic abstractions",
            "Stock setup, hype, and transition phrases",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, text)


if __name__ == "__main__":
    unittest.main()
