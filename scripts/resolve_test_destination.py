#!/usr/bin/env python3

import json
import subprocess
import sys


def runtime_sort_key(runtime_name: str) -> tuple[int, ...]:
    digits = []
    current = ""
    for character in runtime_name:
        if character.isdigit():
            current += character
        elif current:
            digits.append(int(current))
            current = ""
    if current:
        digits.append(int(current))
    return tuple(digits)


def main() -> int:
    result = subprocess.run(
        ["xcrun", "simctl", "list", "devices", "available", "--json"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        return result.returncode

    payload = json.loads(result.stdout)
    candidates_by_runtime: dict[tuple[int, ...], list[tuple[str, str]]] = {}

    for runtime_name, devices in payload.get("devices", {}).items():
        runtime_key = runtime_sort_key(runtime_name)
        for device in devices:
            if not device.get("isAvailable", False):
                continue
            name = device.get("name", "")
            udid = device.get("udid")
            if not udid or not name.startswith("iPhone"):
                continue
            candidates_by_runtime.setdefault(runtime_key, []).append((name, udid))

    if not candidates_by_runtime:
        sys.stderr.write("No available iPhone simulator destination found.\n")
        return 1

    latest_runtime = max(candidates_by_runtime)
    name, udid = sorted(candidates_by_runtime[latest_runtime], key=lambda item: item[0])[0]
    _ = name
    print(f"platform=iOS Simulator,id={udid}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
