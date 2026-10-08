import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / "skills" / "uikit-starter" / "scripts" / "create_project.py"

spec = importlib.util.spec_from_file_location("create_project", SCRIPT)
create_project = importlib.util.module_from_spec(spec)
spec.loader.exec_module(create_project)


class ConfigureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.root)
        for name in ["Configuration", ".github", "skills", "App", "ModernUIKit.xcworkspace"]:
            shutil.copytree(REPO_ROOT / name, self.root / name, ignore=shutil.ignore_patterns("__pycache__"))
        for name in ["CONTRIBUTING.md", "AI_POLICY.md", "HACKING.md", "LICENSE", "README.md", "AGENTS.md", "mise.toml"]:
            shutil.copy(REPO_ROOT / name, self.root / name)

    def test_sets_app_identity_in_base_xcconfig(self) -> None:
        create_project.configure(self.root, "Mottai", "趁鲜", "org.zaxh.Mottai", "ABCDE12345")

        base = (self.root / "Configuration" / "Base.xcconfig").read_text()
        self.assertIn("APP_DISPLAY_NAME = 趁鲜\n", base)
        self.assertIn("APP_BUNDLE_IDENTIFIER = org.zaxh.Mottai\n", base)
        self.assertIn("DEVELOPMENT_TEAM = ABCDE12345\n", base)
        self.assertIn("TARGETED_DEVICE_FAMILY = 1,2\n", base)
        self.assertIn("SUPPORTS_MACCATALYST = NO\n", base)

    def test_platform_flags_set_device_family_and_catalyst(self) -> None:
        create_project.configure(
            self.root, "Mottai", "Mottai", "org.zaxh.Mottai", "", iphone_only=True, mac_catalyst=True
        )

        base = (self.root / "Configuration" / "Base.xcconfig").read_text()
        self.assertIn("TARGETED_DEVICE_FAMILY = 1\n", base)
        self.assertIn("SUPPORTS_MACCATALYST = YES\n", base)

    def test_renames_workspace_to_repo_name(self) -> None:
        create_project.configure(self.root, "Mottai", "趁鲜", "org.zaxh.Mottai", "")

        self.assertEqual([p.name for p in self.root.glob("*.xcworkspace")], ["Mottai.xcworkspace"])
        self.assertIn("`Mottai.xcworkspace`", (self.root / "README.md").read_text())

    def test_empty_team_leaves_no_trailing_space(self) -> None:
        create_project.configure(self.root, "Mottai", "Mottai", "org.zaxh.Mottai", "")

        base = (self.root / "Configuration" / "Base.xcconfig").read_text()
        self.assertIn("DEVELOPMENT_TEAM =\n", base)

    def test_removes_template_only_files_and_keeps_app_files(self) -> None:
        create_project.configure(self.root, "Mottai", "Mottai", "org.zaxh.Mottai", "")

        for relative in create_project.TEMPLATE_ONLY_PATHS:
            self.assertFalse((self.root / relative).exists(), relative)
        self.assertFalse((self.root / ".github").exists())
        self.assertTrue((self.root / "AGENTS.md").exists())
        self.assertTrue((self.root / "App" / "Resources" / "Info.plist").exists())
        self.assertIn("# Mottai", (self.root / "README.md").read_text())

    def test_generated_project_does_not_reference_removed_tooling(self) -> None:
        create_project.configure(self.root, "Mottai", "Mottai", "org.zaxh.Mottai", "")

        self.assertNotIn("test-tooling", (self.root / "mise.toml").read_text())
        for path in self.root.rglob("*"):
            if path.is_file() and path.suffix in {"", ".md", ".toml", ".yml", ".sh", ".py"}:
                self.assertNotIn("skills/uikit-starter", path.read_text(errors="ignore"), path)


if __name__ == "__main__":
    unittest.main()
