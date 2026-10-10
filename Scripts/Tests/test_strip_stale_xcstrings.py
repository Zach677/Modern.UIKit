import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "strip_stale_xcstrings.py"
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
    def test_skips_derived_data_checkouts(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for folder in ("App/Resources", ".DerivedData/SourcePackages/checkouts/Some/Resources"):
                (root / folder).mkdir(parents=True)
                (root / folder / "Localizable.xcstrings").write_text("{}")

            found = [path.relative_to(root) for path in strip_stale_xcstrings.iter_xcstrings(root)]

        self.assertEqual(found, [Path("App/Resources/Localizable.xcstrings")])


if __name__ == "__main__":
    unittest.main()
