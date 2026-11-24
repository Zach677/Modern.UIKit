#!/usr/bin/env python3
"""Resolve SwiftPM packages and write App/Resources/OpenSourceLicenses.md.

Licenses come from the resolved package checkouts, from Vendor/, and from
Licenses/<Package>/ (manual files override scanned ones).
The script fails when a license is GPL, LGPL, or AGPL.

Env: ALLOW_DIRTY=1 lets the script run on a dirty Git tree.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CHECKOUTS = ROOT / ".build" / "license-scanner"
MANUAL_DIR = ROOT / "Licenses"
OUTPUT = ROOT / "App" / "Resources" / "OpenSourceLicenses.md"
LICENSE_PREFIXES = ("LICENSE", "COPYING")
INCOMPATIBLE = (
    "GNU General Public License",
    "GNU Lesser General Public License",
    "GNU Affero General Public License",
)


def workspace() -> Path:
    found = list(ROOT.glob("*.xcworkspace"))
    if len(found) != 1:
        sys.exit(f"error: expected exactly one .xcworkspace in {ROOT}")
    return found[0]


def resolve_packages(workspace_path: Path) -> None:
    command = [
        "xcodebuild", "-resolvePackageDependencies",
        "-workspace", str(workspace_path), "-scheme", "App",
        "-clonedSourcePackagesDirPath", str(CHECKOUTS),
    ]
    for _ in range(3):
        if subprocess.run(command, cwd=ROOT).returncode == 0:
            return
    sys.exit("error: package resolution failed three times")


def display_names(workspace_path: Path) -> dict[str, str]:
    """Map lowercase package identities and repo names to their repository names."""
    resolved = workspace_path / "xcshareddata" / "swiftpm" / "Package.resolved"
    if not resolved.exists():
        return {}
    data = json.loads(resolved.read_text(encoding="utf-8"))
    if isinstance(data.get("pins"), list):
        pins = data["pins"]
    elif isinstance((data.get("object") or {}).get("pins"), list):
        pins = data["object"]["pins"]
    else:
        sys.exit(f"error: unsupported Package.resolved format in {resolved}")
    names = {}
    for pin in pins:
        if not isinstance(pin, dict):
            sys.exit(f"error: unsupported pin entry in {resolved}")
        identity = pin.get("identity") or pin.get("package") or ""
        if pin.get("kind") == "registry":
            if not isinstance(identity, str) or not identity:
                sys.exit(f"error: unsupported pin entry in {resolved}: {pin!r}")
            names[identity.lower()] = identity
            continue
        location = pin.get("location") or pin.get("repositoryURL") or ""
        name = Path(urlparse(location).path).name.removesuffix(".git")
        if not (isinstance(identity, str) and identity and name):
            sys.exit(f"error: unsupported pin entry in {resolved}: {pin!r}")
        names[identity.lower()] = name
        names[name.lower()] = name
    return names


def license_files(directory: Path) -> dict[str, Path]:
    """Return {package folder name: license file} for each direct child folder."""
    if not directory.is_dir():
        return {}
    files = {}
    for package in sorted(p for p in directory.iterdir() if p.is_dir()):
        for candidate in sorted(package.iterdir()):
            if candidate.is_file() and candidate.name.upper().startswith(LICENSE_PREFIXES):
                files.setdefault(package.name, candidate)
    return files


def collect_licenses(
    checkouts_dir: Path,
    vendor_dir: Path,
    manual_dir: Path,
    resolved_names: dict[str, str],
) -> dict[str, Path]:
    """Collect license files; ignore stale checkouts absent from Package.resolved."""
    licenses: dict[str, Path] = {}
    for folder, path in license_files(checkouts_dir).items():
        name = resolved_names.get(folder.lower())
        if name is not None:
            licenses[name] = path
    for directory in (vendor_dir, manual_dir):
        for folder, path in license_files(directory).items():
            licenses[resolved_names.get(folder.lower(), folder)] = path
    return licenses


def render_licenses(licenses: dict[str, Path]) -> str:
    sections = ["# Open Source License"]
    for name, path in sorted(licenses.items(), key=lambda item: item[0].lower()):
        text = path.read_text(encoding="utf-8", errors="replace").strip()
        lowered = text.lower()
        for keyword in INCOMPATIBLE:
            if keyword.lower() in lowered:
                sys.exit(f"error: incompatible license in {name}: {keyword}")
        sections.append(f"## {name}\n\n{text}")
    return "\n\n".join(sections) + "\n"


def main() -> int:
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout
    if dirty and os.environ.get("ALLOW_DIRTY") != "1":
        sys.exit("error: Git tree is not clean (set ALLOW_DIRTY=1 to continue)")

    workspace_path = workspace()
    resolve_packages(workspace_path)
    names = display_names(workspace_path)

    licenses = collect_licenses(CHECKOUTS / "checkouts", ROOT / "Vendor", MANUAL_DIR, names)
    OUTPUT.write_text(render_licenses(licenses), encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)} ({len(licenses)} packages)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
