import json
import shutil
import tempfile
import unittest
from pathlib import Path

from tools.check_conformance_requirements import (
    count_normative_terms,
    extract_normative_units,
    validate_requirements,
)


ROOT = Path(__file__).resolve().parents[1]


class ConformanceRequirementsTests(unittest.TestCase):
    def make_repository_fixture(self) -> Path:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        root = Path(temporary_directory.name)

        shutil.copytree(ROOT / "conformance", root / "conformance")
        shutil.copytree(ROOT / "registry", root / "registry")
        shutil.copytree(ROOT / "rfcs", root / "rfcs")
        return root

    def test_checked_in_matrix_covers_normative_profile(self) -> None:
        errors: list[str] = []

        result = validate_requirements(ROOT, errors)

        self.assertEqual([], errors)
        self.assertEqual((200, 132, 66, 27, 2, 0, 0), result)

    def test_changed_normative_source_requires_matrix_review(self) -> None:
        root = self.make_repository_fixture()
        rfc_path = root / "rfcs/RFC-0001-vision-and-scope.md"
        original = "A conforming implementation MUST be able to:"
        changed = "A conforming implementation MUST demonstrably be able to:"
        text = rfc_path.read_text(encoding="utf-8")
        self.assertIn(original, text)
        rfc_path.write_text(text.replace(original, changed, 1), encoding="utf-8")
        errors: list[str] = []

        validate_requirements(root, errors)

        self.assertTrue(
            any("HWR-SCOPE-002 is stale" in error for error in errors),
            errors,
        )
        self.assertTrue(
            any("unmapped normative source unit" in error for error in errors),
            errors,
        )

    def test_verified_status_requires_evidence(self) -> None:
        root = self.make_repository_fixture()
        manifest_path = root / "conformance/requirements.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["requirements"][0]["status"] = "verified"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        errors: list[str] = []

        validate_requirements(root, errors)

        self.assertTrue(
            any("evidence is required when status is verified" in error for error in errors),
            errors,
        )

    def test_inline_code_keywords_are_not_counted(self) -> None:
        terms = count_normative_terms(
            "The implementation MUST preserve a disclosed `SHOULD` deviation "
            "and MUST NOT reinterpret a literal `MUST`."
        )

        self.assertEqual(
            {"must": 1, "must_not": 1, "should": 0, "should_not": 0},
            terms,
        )

    def test_may_is_permission_not_a_requirement_unit(self) -> None:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        path = Path(temporary_directory.name) / "RFC-9999.md"
        path.write_text(
            "# Test\n\nAn implementation MAY vary.\n\n"
            "An implementation SHOULD explain the variation.\n",
            encoding="utf-8",
        )

        units = extract_normative_units(path, "RFC-9999")

        self.assertEqual(1, len(units))
        self.assertEqual(
            "An implementation SHOULD explain the variation.",
            units[0]["source_text"],
        )


if __name__ == "__main__":
    unittest.main()
