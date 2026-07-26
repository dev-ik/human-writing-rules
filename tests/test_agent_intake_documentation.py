import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class AgentIntakeDocumentationTests(unittest.TestCase):
    def test_agent_instructions_require_bounded_adaptive_questions(self) -> None:
        instructions = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

        self.assertIn("## Agent-led intake", instructions)
        self.assertIn("at most five questions", instructions)
        self.assertIn("Do not repeat answered questions", instructions)
        self.assertIn("Do not ask the user to build a claim ledger", instructions)
        self.assertIn("use your judgment", instructions)

    def test_public_guides_route_conversational_requests_to_intake(self) -> None:
        intake = (ROOT / "guides/agent-led-intake.md").read_text(encoding="utf-8")
        article = (ROOT / "guides/article-production.md").read_text(
            encoding="utf-8"
        )
        social = (ROOT / "guides/social-post-production.md").read_text(
            encoding="utf-8"
        )
        starter = (ROOT / "starter-kit/README.md").read_text(encoding="utf-8")
        runner = (ROOT / "reference-runner/README.md").read_text(
            encoding="utf-8"
        )

        self.assertIn("## Bounded rounds", intake)
        self.assertIn("agent-led intake", article)
        self.assertIn("agent-led intake", social)
        self.assertIn("runs questions", starter)
        self.assertIn("runs questions", runner)
        self.assertIn("agent_actions", runner)

    def test_intake_schema_and_cli_are_linked(self) -> None:
        intake = (ROOT / "guides/agent-led-intake.md").read_text(encoding="utf-8")
        schema = ROOT / "schemas/intake-plan.schema.json"

        self.assertTrue(schema.is_file())
        self.assertIn("schemas/intake-plan.schema.json", intake)
        self.assertIn("--limit 5", intake)


if __name__ == "__main__":
    unittest.main()
