import importlib.util
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "strip_stale_xcstrings.py"
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


if __name__ == "__main__":
    unittest.main()
