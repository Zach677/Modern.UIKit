from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "create_project.py"
SPEC = importlib.util.spec_from_file_location("create_project", SCRIPT_PATH)
create_project = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(create_project)


class DisplayNameTests(unittest.TestCase):
    def test_omitted_display_name_uses_project_name_verbatim(self) -> None:
        self.assertEqual(create_project.resolve_display_name("CapArt", None), "CapArt")

    def test_explicit_display_name_is_trimmed(self) -> None:
        self.assertEqual(
            create_project.resolve_display_name("CapArt", "  Cap Art  "),
            "Cap Art",
        )

    def test_blank_display_name_is_rejected(self) -> None:
        with self.assertRaises(SystemExit):
            create_project.resolve_display_name("CapArt", "   ")


if __name__ == "__main__":
    unittest.main()
