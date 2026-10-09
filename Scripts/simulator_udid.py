#!/usr/bin/env python3
"""Print the UDID of an available iPhone simulator on the newest iOS runtime."""

import json
import subprocess
import sys


def runtime_version(identifier: str) -> list[int]:
    return [int(part) for part in identifier.rsplit("iOS-", 1)[1].split("-")]


def main() -> int:
    output = subprocess.check_output(["xcrun", "simctl", "list", "devices", "available", "-j"])
    devices = json.loads(output)["devices"]
    runtimes = sorted((key for key in devices if ".iOS-" in key), key=runtime_version, reverse=True)
    for runtime in runtimes:
        for device in devices[runtime]:
            if device["name"].startswith("iPhone"):
                print(device["udid"])
                return 0
    print("No available iPhone simulator. Install an iOS runtime in Xcode.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
