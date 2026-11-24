import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "template" / "Scripts" / "strip_stale_xcstrings.py"
spec = importlib.util.spec_from_file_location("strip_stale_xcstrings", SCRIPT)
strip_stale_xcstrings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(strip_stale_xcstrings)


def unit(value: str) -> dict:
    return {"stringUnit": {"state": "translated", "value": value}}


class NormalizeTests(unittest.TestCase):
    def test_keeps_plural_variations_unchanged(self) -> None:
        plural = {"variations": {"plural": {"one": unit("%lld item"), "other": unit("%lld items")}}}
        doc = {"sourceLanguage": "en", "strings": {"%lld items": {"localizations": {"en": plural}}}}

        new_doc, _, fixed, _ = strip_stale_xcstrings.normalize(doc)

        self.assertEqual(fixed, 0)
        self.assertEqual(new_doc["strings"]["%lld items"]["localizations"]["en"], plural)

    def test_keeps_substitutions_unchanged(self) -> None:
        sub = {
            "stringUnit": {"state": "translated", "value": "%#@items@"},
            "substitutions": {
                "items": {"variations": {"plural": {"one": unit("%arg item"), "other": unit("%arg items")}}}
            },
        }
        doc = {"sourceLanguage": "en", "strings": {"%lld items": {"localizations": {"en": sub}}}}

        new_doc, _, fixed, _ = strip_stale_xcstrings.normalize(doc)

        self.assertEqual(fixed, 0)
        self.assertEqual(new_doc["strings"]["%lld items"]["localizations"]["en"], sub)

    def test_info_plist_keeps_source_value_and_strips_stale(self) -> None:
        doc = {
            "sourceLanguage": "en",
            "strings": {
                "OldKey": {"extractionState": "stale", "localizations": {"en": unit("Old")}},
                "CFBundleDisplayName": {
                    "localizations": {"en": {"stringUnit": {"state": "new", "value": "Kinako"}}}
                },
            },
        }

        new_doc, removed, fixed, _ = strip_stale_xcstrings.normalize(doc, mirror_source_from_key=False)

        self.assertEqual((removed, fixed), (1, 1))
        self.assertEqual(list(new_doc["strings"]), ["CFBundleDisplayName"])
        en_unit = new_doc["strings"]["CFBundleDisplayName"]["localizations"]["en"]["stringUnit"]
        self.assertEqual(en_unit, {"state": "translated", "value": "Kinako"})

    def test_removes_stale_and_mirrors_source_value(self) -> None:
        doc = {
            "sourceLanguage": "en",
            "strings": {
                "Old": {"extractionState": "stale", "localizations": {"en": unit("Old")}},
                "Hello": {"localizations": {"en": unit("Hi")}},
            },
        }

        new_doc, removed, fixed, _ = strip_stale_xcstrings.normalize(doc)

        self.assertEqual((removed, fixed), (1, 1))
        self.assertEqual(list(new_doc["strings"]), ["Hello"])
        self.assertEqual(new_doc["strings"]["Hello"]["localizations"]["en"]["stringUnit"]["value"], "Hello")


class IterXcstringsTests(unittest.TestCase):
    def test_skips_derived_data_and_custom_tables(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for folder in ("App/Resources", ".DerivedData/SourcePackages/checkouts/Some/Resources"):
                (root / folder).mkdir(parents=True)
                (root / folder / "Localizable.xcstrings").write_text("{}", encoding="utf-8")
            (root / "App/Resources/InfoPlist.xcstrings").write_text("{}", encoding="utf-8")
            custom = root / "App/Resources/Checkout.xcstrings"
            custom.write_text('{"strings": {"Old": {"extractionState": "stale"}}}', encoding="utf-8")

            found = [path.relative_to(root) for path in strip_stale_xcstrings.iter_xcstrings(root)]

        self.assertEqual(
            found,
            [Path("App/Resources/Localizable.xcstrings"), Path("App/Resources/InfoPlist.xcstrings")],
        )


if __name__ == "__main__":
    unittest.main()
