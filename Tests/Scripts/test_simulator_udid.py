import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "template" / "Scripts" / "simulator_udid.py"


def iphone(udid: str, state: str = "Shutdown") -> dict:
    return {"name": "iPhone 17", "udid": udid, "state": state}


class SimulatorUDIDTests(unittest.TestCase):
    def udid(self, devices: dict) -> str:
        root = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, root)
        # A fake xcrun on PATH prints the simctl JSON.
        (root / "devices.json").write_text(json.dumps({"devices": devices}))
        fake = root / "xcrun"
        fake.write_text(f'#!/bin/sh\ncat "{root / "devices.json"}"\n')
        fake.chmod(0o755)
        env = {**os.environ, "PATH": f"{root}:{os.environ['PATH']}"}
        return subprocess.run([SCRIPT], env=env, check=True, capture_output=True, text=True).stdout.strip()

    def test_prefers_generic_runtime_over_device_specific_runtime(self) -> None:
        devices = {
            "com.apple.CoreSimulator.SimRuntime.iOS-27-2-iPhone19-4": [iphone("SPECIFIC")],
            "com.apple.CoreSimulator.SimRuntime.iOS-27-2": [iphone("GENERIC")],
            "com.apple.CoreSimulator.SimRuntime.iOS-26-4": [iphone("OLD")],
        }
        self.assertEqual(self.udid(devices), "GENERIC")

    def test_prefers_newest_version(self) -> None:
        devices = {
            "com.apple.CoreSimulator.SimRuntime.iOS-26-10": [iphone("NEW")],
            "com.apple.CoreSimulator.SimRuntime.iOS-26-9": [iphone("OLD", state="Booted")],
        }
        self.assertEqual(self.udid(devices), "NEW")

    def test_prefers_booted_iphone_on_newest_runtime(self) -> None:
        devices = {
            "com.apple.CoreSimulator.SimRuntime.iOS-27-0": [
                iphone("SHUTDOWN"),
                iphone("BOOTED", state="Booted"),
            ],
        }
        self.assertEqual(self.udid(devices), "BOOTED")


if __name__ == "__main__":
    unittest.main()
