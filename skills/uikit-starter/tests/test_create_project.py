from __future__ import annotations

import importlib.util
import tempfile
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


class GeneratedReadmeTests(unittest.TestCase):
    def test_generated_readme_documents_run_ios_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            create_project.write_generated_readme(
                repo_root=repo_root,
                project_name="CapArt",
                display_name="CapArt",
                source_dir_name="CapArt",
                tests_name="CapArtTests",
                bundle_id="com.zach.capart",
                development_team=None,
                swift_version="6.0",
            )

            content = (repo_root / "README.md").read_text(encoding="utf-8")

        self.assertIn("make run-ios", content)
        self.assertIn("install it on the booted simulator, and launch it", content)

    def test_generated_readme_documents_narrow_base_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            create_project.write_generated_readme(
                repo_root=repo_root,
                project_name="CapArt",
                display_name="CapArt",
                source_dir_name="CapArt",
                tests_name="CapArtTests",
                bundle_id="com.zach.capart",
                development_team=None,
                swift_version="6.0",
            )

            content = (repo_root / "README.md").read_text(encoding="utf-8")

        self.assertIn("`Configuration/Base.xcconfig` is intentionally narrow", content)
        self.assertIn("leaves target/platform settings", content)
        self.assertIn("`SWIFT_VERSION`", content)

    def test_generated_readme_documents_committed_development_team(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            create_project.write_generated_readme(
                repo_root=repo_root,
                project_name="CapArt",
                display_name="CapArt",
                source_dir_name="CapArt",
                tests_name="CapArtTests",
                bundle_id="com.zach.capart",
                development_team="S56VW4D8X4",
                swift_version="6.0",
            )

            content = (repo_root / "README.md").read_text(encoding="utf-8")

        self.assertIn("DEVELOPMENT_TEAM = S56VW4D8X4", content)
        self.assertIn("PRODUCT_BUNDLE_IDENTIFIER = com.zach.capart", content)
        self.assertIn("Signing & Capabilities", content)


if __name__ == "__main__":
    unittest.main()
