import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "template" / "Scripts" / "run_xcodebuild.sh"
PATTERN = re.search(r"^error_pattern='(.*)'$", SCRIPT.read_text(), re.MULTILINE).group(1)


def matches(line: str) -> bool:
    return subprocess.run(["grep", "-E", PATTERN], input=line, text=True, capture_output=True).returncode == 0


class ErrorPatternTests(unittest.TestCase):
    def test_matches_compiler_and_package_diagnostics(self) -> None:
        for line in (
            "/src/App/View.swift:12:5: error: cannot find 'x' in scope",
            "/src/App/View.swift:12: error: bad",
            "/checkouts/pkg/Package.swift:PACKAGE-TARGET:Macros: error: Macro \"Macros\" must be enabled",
            "xcodebuild: error: Unable to find a destination",
            "error: plain",
            "** BUILD FAILED **",
        ):
            with self.subTest(line=line):
                self.assertTrue(matches(line))

    def test_ignores_errors_inside_system_logs(self) -> None:
        for line in (
            "2026-10-10 12:00:00.000 App[1:2] [AXLoading] ScreenTimeUI error: noise",
            "/usr/lib/libfoo.dylib something error: noise",
        ):
            with self.subTest(line=line):
                self.assertFalse(matches(line))


class SigningTests(unittest.TestCase):
    def xcodebuild_args(self, sign: str = "") -> list[str]:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        (root / "App.xcworkspace").mkdir()
        # A fake xcodebuild on PATH records the arguments that the script passes.
        fake = root / "bin" / "xcodebuild"
        fake.parent.mkdir()
        fake.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$ARGS_FILE"\n')
        fake.chmod(0o755)
        args_file = root / "args"
        env = {**os.environ, "PATH": f"{fake.parent}:{os.environ['PATH']}", "ARGS_FILE": str(args_file), "SIGN": sign}
        subprocess.run([SCRIPT, "build", "generic/platform=iOS"], cwd=root, env=env, check=True, capture_output=True)
        return args_file.read_text().splitlines()

    def test_disables_signing_by_default(self) -> None:
        args = self.xcodebuild_args()
        self.assertIn("CODE_SIGNING_ALLOWED=NO", args)
        self.assertNotIn("-allowProvisioningUpdates", args)

    def test_sign_allows_signing_and_provisioning_updates(self) -> None:
        args = self.xcodebuild_args(sign="1")
        self.assertIn("-allowProvisioningUpdates", args)
        self.assertNotIn("CODE_SIGNING_ALLOWED=NO", args)


class WarningTests(unittest.TestCase):
    def run_script(self, output: str) -> subprocess.CompletedProcess:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        (root / "App.xcworkspace").mkdir()
        # A fake xcodebuild on PATH prints the log and exits 0.
        (root / "output").write_text(output)
        fake = root / "bin" / "xcodebuild"
        fake.parent.mkdir()
        fake.write_text(f'#!/bin/sh\ncat "{root / "output"}"\n')
        fake.chmod(0o755)
        env = {**os.environ, "PATH": f"{fake.parent}:{os.environ['PATH']}"}
        return subprocess.run([SCRIPT, "build", "generic/platform=iOS"], cwd=root, env=env, capture_output=True, text=True)

    def test_warnings_fail_the_run(self) -> None:
        for line in (
            "/src/App/View.swift:12:5: warning: variable 'x' was never used",
            "/src/App.xcodeproj: warning: The iOS Simulator deployment target is set to 12.0",
            "/src/App.xcodeproj: App: ld: warning: ignoring duplicate libraries: '-lc++'",
            "ld: warning: ignoring duplicate libraries: '-lc++'",
        ):
            with self.subTest(line=line):
                result = self.run_script(f"** BUILD START **\n{line}\n** BUILD SUCCEEDED **\n")
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(line, result.stderr)

    def test_clean_log_and_known_noise_pass(self) -> None:
        result = self.run_script(
            "2026-11-19 16:15:05.470 appintentsmetadataprocessor[80865:6657897] warning: Metadata extraction skipped,"
            " no AppIntents.framework dependency found\n"
            "/src/App.xcodeproj: App: ld: warning: search path '/var/run/com.apple.security.cryptexd/mnt/"
            "com.apple.MobileAsset.MetalToolchain-v27.2.47.0.KtC3oC/Metal.xctoolchain/usr/lib/swift/maccatalyst' not found\n"
            "** BUILD SUCCEEDED **\n"
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
