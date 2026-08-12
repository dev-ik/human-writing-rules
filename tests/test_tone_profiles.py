import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ToneProfileTests(unittest.TestCase):
    def test_style_tones_are_registered_and_require_human_signals(self) -> None:
        registry = json.loads(
            (ROOT / "registry/objects.json").read_text(encoding="utf-8")
        )
        by_id = {entry["id"]: entry for entry in registry["objects"]}
        tones = json.loads(
            (ROOT / "registry/tones.json").read_text(encoding="utf-8")
        )
        tone_ids = {entry["id"] for entry in tones["tones"]}

        for tone in ("blogger", "developer", "writer", "screenwriter", "amateur"):
            with self.subTest(tone=tone):
                self.assertIn(tone, tone_ids)
                entry = by_id[f"tone.{tone}"]
                self.assertEqual("tone", entry["kind"])
                self.assertIn("rule.human-signals.core", entry["requires"])

    def test_style_tones_do_not_grant_authority_or_invent_experience(self) -> None:
        expected_guards = {
            "blogger": "Do not invent parasocial familiarity",
            "developer": "does not authorize the text to claim engineering experience",
            "writer": "Do not imitate a named living author",
            "screenwriter": "Do not fabricate quotes",
            "amateur": "does not permit fake naivety",
        }

        for tone, guard in expected_guards.items():
            text = (ROOT / f"rules/tone/{tone}.md").read_text(encoding="utf-8")
            with self.subTest(tone=tone):
                self.assertIn(guard, text)


if __name__ == "__main__":
    unittest.main()
