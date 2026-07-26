import copy
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from tools.hwr_reference import HwrError, load_repository
from tools.hwr_registry_index import (
    build_generated_registry_index,
    check_generated_registry_index,
    render_generated_registry_index,
)


ROOT = Path(__file__).resolve().parents[1]
GENERATED_INDEX_PATH = ROOT / "registry/generated-index.json"
GENERATOR_PATH = ROOT / "tools/hwr_registry_index.py"


class RegistryIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.repository = load_repository(ROOT)
        cls.generated = build_generated_registry_index(cls.repository)

    def test_checked_in_index_is_current_and_canonical(self) -> None:
        result = check_generated_registry_index(
            GENERATED_INDEX_PATH,
            self.generated,
        )

        self.assertTrue(result["valid"])
        self.assertEqual(50, result["objects"])
        self.assertEqual(29, result["values"])
        self.assertEqual(6, result["rfcs"])
        self.assertEqual(
            self.repository["registry_revision"],
            result["source_revision"],
        )

    def test_generation_is_deterministic_and_sorted(self) -> None:
        first = render_generated_registry_index(self.generated)
        second = render_generated_registry_index(
            build_generated_registry_index(self.repository)
        )

        self.assertEqual(first, second)
        parsed = json.loads(first)
        self.assertEqual(sorted(parsed["objects"]), list(parsed["objects"]))
        self.assertEqual(
            sorted(parsed["values"]["topics"]),
            list(parsed["values"]["topics"]),
        )

    def test_stale_and_noncanonical_indexes_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary = Path(temporary_directory)
            stale = copy.deepcopy(self.generated)
            stale["defaults"]["topic_fallback"] = "science"
            stale_path = temporary / "stale.json"
            stale_path.write_text(
                render_generated_registry_index(stale),
                encoding="utf-8",
            )
            with self.assertRaises(HwrError) as stale_error:
                check_generated_registry_index(stale_path, self.generated)
            self.assertEqual(
                "GENERATED_REGISTRY_INDEX_STALE",
                stale_error.exception.code,
            )

            noncanonical_path = temporary / "noncanonical.json"
            noncanonical_path.write_text(
                json.dumps(self.generated, ensure_ascii=False),
                encoding="utf-8",
            )
            with self.assertRaises(HwrError) as formatting_error:
                check_generated_registry_index(
                    noncanonical_path,
                    self.generated,
                )
            self.assertEqual(
                "GENERATED_REGISTRY_INDEX_NON_CANONICAL",
                formatting_error.exception.code,
            )

    def test_generator_cli_checks_the_committed_index(self) -> None:
        result = subprocess.run(
            ["python3", str(GENERATOR_PATH), "--check"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, result.returncode, result.stderr)
        output = json.loads(result.stdout)
        self.assertTrue(output["valid"])
        self.assertEqual(
            self.repository["registry_revision"],
            output["source_revision"],
        )


if __name__ == "__main__":
    unittest.main()
