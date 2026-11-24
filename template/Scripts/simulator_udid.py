#!/usr/bin/env python3
"""Print the UDID of an available iPhone simulator on the newest iOS runtime."""

from __future__ import annotations

import itertools
import json
import subprocess
import sys


def runtime_version(identifier: str) -> tuple[list[int], bool]:
    # Device-specific runtimes such as iOS-27-2-iPhone19-4 rank below the generic runtime of the same version.
    parts = identifier.rsplit("iOS-", 1)[1].split("-")
    numbers = [int(part) for part in itertools.takewhile(str.isdigit, parts)]
    return numbers, len(parts) == len(numbers)


def main() -> int:
    output = subprocess.check_output(["xcrun", "simctl", "list", "devices", "available", "-j"])
    devices = json.loads(output)["devices"]
    runtimes = sorted((key for key in devices if ".iOS-" in key), key=runtime_version, reverse=True)
    for runtime in runtimes:
        iphones = [device for device in devices[runtime] if device["name"].startswith("iPhone")]
        if iphones:
            booted = next((device for device in iphones if device.get("state") == "Booted"), None)
            print((booted or iphones[0])["udid"])
            return 0
    print("No available iPhone simulator. Install an iOS runtime in Xcode.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
