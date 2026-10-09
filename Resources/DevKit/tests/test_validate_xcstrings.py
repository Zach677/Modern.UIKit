import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate_xcstrings.py"
spec = importlib.util.spec_from_file_location("validate_xcstrings", SCRIPT)
validate_xcstrings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validate_xcstrings)


def unit(value: str) -> dict:
    return {"stringUnit": {"state": "translated", "value": value}}


class ValidateFileTests(unittest.TestCase):
    def validate(self, swift: str, strings: dict) -> list[str]:
        root = Path(tempfile.mkdtemp())
        resources = root / "App" / "Resources"
        resources.mkdir(parents=True)
        (root / "App" / "View.swift").write_text(swift)
        catalog = resources / "Localizable.xcstrings"
        catalog.write_text(json.dumps({"sourceLanguage": "en", "strings": strings, "version": "1.0"}))
        return validate_xcstrings.validate_file(catalog, root, {"zh-Hans"})

    def test_interpolated_string_matches_format_specifier_key(self) -> None:
        errors = self.validate(
            'let text = String(localized: "Good for \\(days) days")',
            {"Good for %lld days": {"localizations": {"en": unit("Good for %lld days"), "zh-Hans": unit("还能放 %lld 天")}}},
        )
        self.assertEqual(errors, [])

    def test_plural_variations_are_valid(self) -> None:
        plural = lambda one, other: {"variations": {"plural": {"one": unit(one), "other": unit(other)}}}
        errors = self.validate(
            'let text = String(localized: "\\(count) items")',
            {"%lld items": {"localizations": {"en": plural("%lld item", "%lld items"), "zh-Hans": plural("%lld 件", "%lld 件")}}},
        )
        self.assertEqual(errors, [])

    def test_missing_translation_still_fails(self) -> None:
        errors = self.validate(
            'let text = String(localized: "Hello")',
            {"Hello": {"localizations": {"en": unit("Hello")}}},
        )
        self.assertTrue(any("missing zh-Hans" in error for error in errors), errors)

    def test_unregistered_key_still_fails(self) -> None:
        errors = self.validate('let text = String(localized: "Hello")', {})
        self.assertTrue(any("missing from the catalog" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
