import importlib.util
import os
import re
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


def build_settings_by_owner(pbxproj: str, owner_kind: str, owner_name: str) -> dict[str, str]:
    list_match = re.search(
        rf"/\* Build configuration list for {re.escape(owner_kind)} \"{re.escape(owner_name)}\" \*/ = \{{(.*?)\n\t\t\}};",
        pbxproj,
        re.DOTALL,
    )
    if not list_match:
        raise AssertionError(f"Configuration list for {owner_kind} {owner_name!r} not found")
    configs: dict[str, str] = {}
    for cfg_id, cfg_name in re.findall(r"([0-9A-F]{24}) /\* (Debug|Release) \*/", list_match.group(1)):
        cfg_match = re.search(
            rf"{cfg_id} /\* {cfg_name} \*/ = \{{.*?buildSettings = \{{(.*?)\n\t\t\t\}};",
            pbxproj,
            re.DOTALL,
        )
        if not cfg_match:
            raise AssertionError(f"Build configuration {cfg_id} ({cfg_name}) not found")
        configs[cfg_name] = cfg_match.group(1)
    return configs


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

        base = (self.root / "Configuration" / "Base.xcconfig").read_text(encoding="utf-8")
        self.assertIn("TARGETED_DEVICE_FAMILY = 1,2\n", base)
        self.assertIn("SUPPORTS_MACCATALYST = YES\n", base)
        self.assertNotIn("CODE_SIGN_ENTITLEMENTS", base)

        entitlements = self.root / "App" / "Resources" / "MacCatalyst.entitlements"
        self.assertTrue(entitlements.is_file())
        self.assertIn("<key>com.apple.security.app-sandbox</key>", entitlements.read_text(encoding="utf-8"))

        pbxproj = (self.root / "App.xcodeproj" / "project.pbxproj").read_text(encoding="utf-8")
        app_configs = build_settings_by_owner(pbxproj, "PBXNativeTarget", "App")
        self.assertEqual(set(app_configs), {"Debug", "Release"})
        for name, settings in app_configs.items():
            with self.subTest(target="App", config=name):
                self.assertIn(
                    '"CODE_SIGN_ENTITLEMENTS[sdk=macosx*]" = App/Resources/MacCatalyst.entitlements;',
                    settings,
                )
                self.assertIn('"ENABLE_HARDENED_RUNTIME[sdk=macosx*]" = YES;', settings)

        for owner_kind, owner_name in (("PBXNativeTarget", "AppTests"), ("PBXProject", "App")):
            for name, settings in build_settings_by_owner(pbxproj, owner_kind, owner_name).items():
                with self.subTest(owner=f"{owner_kind}:{owner_name}", config=name):
                    self.assertNotIn("CODE_SIGN_ENTITLEMENTS", settings)
                    self.assertNotIn("ENABLE_HARDENED_RUNTIME", settings)

    def test_default_omits_catalyst_entitlements_and_file_headers(self) -> None:
        create_project.configure(self.root, "Mottai", "Mottai", "org.zaxh.Mottai", "")

        self.assertFalse((self.root / "App" / "Resources" / "MacCatalyst.entitlements").exists())
        self.assertNotIn(
            "CODE_SIGN_ENTITLEMENTS",
            (self.root / "App.xcodeproj" / "project.pbxproj").read_text(encoding="utf-8"),
        )
        self.assertFalse((self.root / ".githooks").exists())
        self.assertNotIn("--header", (self.root / ".swiftformat").read_text(encoding="utf-8"))
        self.assertNotIn("[tasks.hooks]", (self.root / "mise.toml").read_text(encoding="utf-8"))

    def test_author_adds_file_header_config_and_pre_commit_hook(self) -> None:
        create_project.configure(self.root, "Kinako", "Kinako", "org.zaxh.kinako", "", author="Ren #1")

        swiftformat = (self.root / ".swiftformat").read_text(encoding="utf-8")
        self.assertIn('--header "\\n {file}\\n Kinako\\n\\n Created by Ren #1 on {created}.\\n"\n', swiftformat)
        self.assertIn("--date-format yyyy/MM/dd\n", swiftformat)
        self.assertNotIn("--timezone", swiftformat)

        hook = self.root / ".githooks" / "pre-commit"
        self.assertTrue(hook.is_file())
        self.assertTrue(hook.stat().st_mode & 0o111)
        self.assertIn("[tasks.hooks]", (self.root / "mise.toml").read_text(encoding="utf-8"))
        self.assertIn("mise hooks\n", (self.root / "README.md").read_text(encoding="utf-8"))
        self.assertIn("`mise hooks`", (self.root / "AGENTS.md").read_text(encoding="utf-8"))

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
    def run_main(self, *flags: str, which=lambda name: "/usr/bin/git" if name == "git" else None) -> str:
        parent = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, parent)
        argv = ["create_project.py", "--repo", "Mottai", "--bundle-id", "org.zaxh.Mottai",
                "--template-dir", str(TEMPLATE_DIR), "--parent-dir", str(parent), *flags]
        # Every command fails, so no real gh or git runs and gh auth status reports signed out.
        self.commands = []
        def run(command, **_):
            self.commands.append(command)
            return subprocess.CompletedProcess(command, 1, "", "")
        with mock.patch.object(sys, "argv", argv), mock.patch.object(create_project.shutil, "which", which), \
                mock.patch.object(create_project.subprocess, "run", run):
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
        self.assertEqual(self.commands, [])

    def test_signed_out_gh_stops_before_any_change(self) -> None:
        message = self.run_main(which=lambda name: f"/usr/bin/{name}")
        self.assertEqual(message, "gh is not signed in. Run gh auth login, or rerun with --no-remote.")
        self.assertEqual(self.commands, [["gh", "auth", "status"]])

    def test_invalid_empty_repo_stops_before_any_change(self) -> None:
        parent = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, parent)
        argv = [
            "create_project.py",
            "--repo",
            "///",
            "--bundle-id",
            "org.zaxh.Mottai",
            "--template-dir",
            str(TEMPLATE_DIR),
            "--parent-dir",
            str(parent),
            "--no-remote",
            "--verify",
            "none",
        ]
        with mock.patch.object(sys, "argv", argv):
            with self.assertRaises(SystemExit) as raised:
                create_project.main()
        self.assertIn("Invalid repository name", str(raised.exception.code))


    def test_invalid_author_stops_before_creating_destination(self) -> None:
        for bad_author in ("One\nTwo", "Ren\n", "Ren\\Li", "Bad{Name}"):
            with self.subTest(author=bad_author):
                parent = Path(tempfile.mkdtemp())
                self.addCleanup(shutil.rmtree, parent)
                argv = [
                    "create_project.py",
                    "--repo",
                    "Mottai",
                    "--bundle-id",
                    "org.zaxh.Mottai",
                    "--author",
                    bad_author,
                    "--template-dir",
                    str(TEMPLATE_DIR),
                    "--parent-dir",
                    str(parent),
                    "--no-remote",
                    "--verify",
                    "none",
                ]
                with mock.patch.object(sys, "argv", argv):
                    with self.assertRaises(SystemExit) as raised:
                        create_project.main()
                self.assertIn("Invalid --author value", str(raised.exception.code))
                self.assertFalse((parent / "Mottai").exists())


class PreCommitHookTests(unittest.TestCase):
    def make_repo_with_fake_tools(self) -> tuple[Path, Path, Path]:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        repo = root / "Repo"
        create_project.copy_template(TEMPLATE_DIR, repo)
        create_project.configure(repo, "Repo", "Repo", "org.example.Repo", "", author="Ren #1")
        subprocess.run(["git", "init", "--quiet"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)

        ambient_bin = root / "ambient"
        pinned_bin = root / "pinned"
        ambient_bin.mkdir()
        pinned_bin.mkdir()
        log_file = root / "tool.log"

        # Ambient swiftformat on PATH records its invocation and enforces leading-dash protection.
        ambient_sf = ambient_bin / "swiftformat"
        ambient_sf.write_text(
            f'#!/bin/sh\n'
            f'echo "AMBIENT $*" >> "{log_file}"\n'
            f'for arg in "$@"; do\n'
            f'  case "$arg" in\n'
            f'    --version|--rules|fileHeader|--quiet|stdin|--stdinpath|--lint) ;;\n'
            f'    -*) echo "Unknown flag $arg" >&2; exit 70 ;;\n'
            f'  esac\n'
            f'done\n',
            encoding="utf-8",
        )
        ambient_sf.chmod(0o755)

        # Pinned swiftformat returned by fake mise records args and verifies leading-dash paths are prefixed.
        pinned_sf = pinned_bin / "swiftformat"
        pinned_sf.write_text(
            f'#!/bin/sh\n'
            f'echo "PINNED $*" >> "{log_file}"\n'
            f'if [ "$1" = "stdin" ]; then cat >/dev/null; fi\n'
            f'for arg in "$@"; do\n'
            f'  case "$arg" in\n'
            f'    --version|--rules|fileHeader|--quiet|stdin|--stdinpath|--lint) ;;\n'
            f'    -*) echo "Unknown flag $arg" >&2; exit 70 ;;\n'
            f'  esac\n'
            f'done\n',
            encoding="utf-8",
        )
        pinned_sf.chmod(0o755)

        fake_mise = ambient_bin / "mise"
        fake_mise.write_text(
            f'#!/bin/sh\n'
            f'if [ "${{FAIL_MISE:-0}}" != "1" ] && [ "$1" = "which" ] && [ "$2" = "swiftformat" ]; then\n'
            f'  printf "%s\\n" "{pinned_sf}"\n'
            f'  exit 0\n'
            f'fi\n'
            f'exit 1\n',
            encoding="utf-8",
        )
        fake_mise.chmod(0o755)
        return repo, ambient_bin, log_file

    def test_prefers_mise_swiftformat_handles_leading_dash_and_literal_pathspecs(self) -> None:
        repo, ambient_bin, log_file = self.make_repo_with_fake_tools()
        # Track and then modify Part1.swift without staging, so git diff on Part[1].swift
        # would misclassify Part[1].swift as partially staged without --literal-pathspecs.
        (repo / "Part1.swift").write_text("let b = 1\n", encoding="utf-8")
        subprocess.run(["git", "add", "--", "Part1.swift"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "--no-verify", "--quiet", "-m", "init"], cwd=repo, check=True)
        (repo / "Part1.swift").write_text("let b = 2\n", encoding="utf-8")

        (repo / "Part[1].swift").write_text("let a = 1\n", encoding="utf-8")
        (repo / "-Note.swift").write_text("let c = 1\n", encoding="utf-8")
        subprocess.run(
            ["git", "--literal-pathspecs", "add", "--", "Part[1].swift", "-Note.swift"],
            cwd=repo,
            check=True,
        )
        # Partially stage -Note.swift by modifying the working tree copy after staging.
        (repo / "-Note.swift").write_text("let c = 2\n", encoding="utf-8")

        env = {
            **os.environ,
            "HOME": str(repo.parent / "empty-home"),
            "PATH": f"{ambient_bin}:/usr/bin:/bin",
        }
        result = subprocess.run(
            [str(repo / ".githooks" / "pre-commit")],
            cwd=repo,
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

        staged = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            cwd=repo,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.splitlines()
        self.assertEqual(sorted(staged), ["-Note.swift", "Part[1].swift"])
        self.assertEqual((repo / "-Note.swift").read_text(encoding="utf-8"), "let c = 2\n")

        invocations = log_file.read_text(encoding="utf-8")
        self.assertIn("PINNED --rules fileHeader --quiet ./Part[1].swift", invocations)
        self.assertIn("PINNED stdin --stdinpath ./-Note.swift --rules fileHeader --lint --quiet", invocations)
        self.assertNotIn("AMBIENT", invocations)

    def test_broken_shim_falls_back_to_ambient_path_before_homebrew(self) -> None:
        repo, ambient_bin, log_file = self.make_repo_with_fake_tools()
        fake_home = repo.parent / "fake-home"
        broken_shim = fake_home / ".local" / "share" / "mise" / "shims" / "swiftformat"
        broken_shim.parent.mkdir(parents=True)
        broken_shim.write_text("#!/bin/sh\nexit 1\n", encoding="utf-8")
        broken_shim.chmod(0o755)

        (repo / "Sample.swift").write_text("let x = 1\n", encoding="utf-8")
        subprocess.run(["git", "add", "--", "Sample.swift"], cwd=repo, check=True)

        env = {
            **os.environ,
            "HOME": str(fake_home),
            "FAIL_MISE": "1",
            "PATH": f"{ambient_bin}:/usr/bin:/bin",
        }
        result = subprocess.run(
            [str(repo / ".githooks" / "pre-commit")],
            cwd=repo,
            env=env,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

        invocations = log_file.read_text(encoding="utf-8")
        self.assertIn("AMBIENT --rules fileHeader --quiet ./Sample.swift", invocations)
        self.assertNotIn("PINNED", invocations)


if __name__ == "__main__":
    unittest.main()
