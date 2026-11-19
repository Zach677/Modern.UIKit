import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

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
        self.assertIn("TARGETED_DEVICE_FAMILY = 1\n", base)
        self.assertIn("SUPPORTS_MACCATALYST = NO\n", base)

    def test_platform_flags_set_device_family_and_catalyst(self) -> None:
        create_project.configure(
            self.root, "Mottai", "Mottai", "org.zaxh.Mottai", "", ipad=True, mac_catalyst=True
        )

        base = (self.root / "Configuration" / "Base.xcconfig").read_text()
        self.assertIn("TARGETED_DEVICE_FAMILY = 1,2\n", base)
        self.assertIn("SUPPORTS_MACCATALYST = YES\n", base)

    def test_mac_catalyst_implies_ipad(self) -> None:
        create_project.configure(self.root, "Mottai", "Mottai", "org.zaxh.Mottai", "", mac_catalyst=True)

        base = (self.root / "Configuration" / "Base.xcconfig").read_text()
        self.assertIn("TARGETED_DEVICE_FAMILY = 1,2\n", base)
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
        self.assertIn('{ task = "test" }', mise.split("[tasks.check]", 1)[1].split("\n[", 1)[0])


class PrerequisiteTests(unittest.TestCase):
    def run_main(self, *flags: str) -> str:
        parent = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, parent)
        argv = ["create_project.py", "--repo", "Mottai", "--bundle-id", "org.zaxh.Mottai",
                "--template-dir", str(TEMPLATE_DIR), "--parent-dir", str(parent), *flags]
        which = lambda name: "/usr/bin/git" if name == "git" else None
        with mock.patch.object(sys, "argv", argv), mock.patch.object(create_project.shutil, "which", which):
            with self.assertRaises(SystemExit) as raised:
                create_project.main()
        self.assertFalse((parent / "Mottai").exists())
        return str(raised.exception.code)

    def test_missing_commands_stop_before_any_change(self) -> None:
        message = self.run_main()
        self.assertIn("gh not found. Install it from https://cli.github.com, then rerun.", message)
        self.assertIn("mise not found. Install it from https://mise.jdx.dev, then rerun.", message)

    def test_no_remote_does_not_need_gh(self) -> None:
        message = self.run_main("--no-remote")
        self.assertNotIn("gh not found", message)
        self.assertIn("mise not found", message)


if __name__ == "__main__":
    unittest.main()
