import re
import subprocess
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "run_xcodebuild.sh"
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


if __name__ == "__main__":
    unittest.main()
