import importlib.util
import shutil
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_DIR = REPO_ROOT / "template"
SCRIPT = REPO_ROOT / "skills" / "uikit-starter" / "scripts" / "create_project.py"

spec = importlib.util.spec_from_file_location("create_project", SCRIPT)
create_project = importlib.util.module_from_spec(spec)
spec.loader.exec_module(create_project)


class ConfigureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp()) / "Mottai"
        self.addCleanup(shutil.rmtree, self.root.parent)
        create_project.copy_template(TEMPLATE_DIR, self.root)

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

    def test_generated_files_equal_template_files(self) -> None:
        create_project.configure(self.root, "Mottai", "Mottai", "org.zaxh.Mottai", "")

        listed = subprocess.run(
            ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
            cwd=TEMPLATE_DIR,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        expected = {
            name.replace("ModernUIKit.xcworkspace/", "Mottai.xcworkspace/")
            for name in listed
            if (TEMPLATE_DIR / name).is_symlink() or (TEMPLATE_DIR / name).exists()
        } | {"README.md"}
        actual = {
            path.relative_to(self.root).as_posix()
            for path in self.root.rglob("*")
            if path.is_symlink() or path.is_file()
        }
        self.assertEqual(actual, expected)
        self.assertTrue((self.root / "CLAUDE.md").is_symlink())

    def test_generated_mise_runs_standalone_checks(self) -> None:
        create_project.configure(self.root, "Mottai", "Mottai", "org.zaxh.Mottai", "")

        mise = (self.root / "mise.toml").read_text()
        self.assertNotIn("test-tooling", mise)
        self.assertIn({"task": "test"}, tomllib.loads(mise)["tasks"]["check"]["run"])


if __name__ == "__main__":
    unittest.main()
