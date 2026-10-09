#!/usr/bin/env python3
"""Create a new app repository from the Modern.UIKit GitHub template."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path

DEFAULT_TEMPLATE_REPO = "Zach677/Modern.UIKit"

# Files that describe the template project itself, not the generated app.
TEMPLATE_ONLY_PATHS = [
    "skills",
    # Tests for the DevKit scripts run in the template, like the skill tests.
    "Resources/DevKit/tests",
    "CONTRIBUTING.md",
    "AI_POLICY.md",
    "HACKING.md",
    "LICENSE",
    # Community templates, vouch workflows, and CI. A private app repo adds
    # its own CI when it needs one; macOS runners are billed for private repos.
    ".github",
]


def run(command: list[str], cwd: Path | None = None) -> None:
    result = subprocess.run(command, cwd=cwd, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def set_xcconfig_value(path: Path, key: str, value: str) -> None:
    text = path.read_text()
    pattern = re.compile(rf"^{re.escape(key)} =.*$", re.MULTILINE)
    if not pattern.search(text):
        raise SystemExit(f"{key} not found in {path}")
    path.write_text(pattern.sub(lambda _: f"{key} = {value}".rstrip(), text, count=1))


def configure(
    repo_root: Path,
    workspace_name: str,
    display_name: str,
    bundle_id: str,
    team: str,
    iphone_only: bool = False,
    mac_catalyst: bool = False,
) -> None:
    base = repo_root / "Configuration" / "Base.xcconfig"
    set_xcconfig_value(base, "APP_DISPLAY_NAME", display_name)
    set_xcconfig_value(base, "APP_BUNDLE_IDENTIFIER", bundle_id)
    set_xcconfig_value(base, "DEVELOPMENT_TEAM", team)
    set_xcconfig_value(base, "TARGETED_DEVICE_FAMILY", "1" if iphone_only else "1,2")
    set_xcconfig_value(base, "SUPPORTS_MACCATALYST", "YES" if mac_catalyst else "NO")

    (workspace,) = repo_root.glob("*.xcworkspace")
    workspace.rename(repo_root / f"{workspace_name}.xcworkspace")

    mise = repo_root / "mise.toml"
    mise.write_text(re.sub(r"\[tasks\.test-tooling\]\n(?:.+\n)*\n", "", mise.read_text()))

    for relative in TEMPLATE_ONLY_PATHS:
        path = repo_root / relative
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()

    (repo_root / "README.md").write_text(
        f"# {display_name}\n\n"
        "A programmatic UIKit app for iOS 26.\n\n"
        "## Development\n\n"
        f"Open `{workspace_name}.xcworkspace`, or use:\n\n"
        "```bash\n"
        "mise install\n"
        "mise build\n"
        "mise test\n"
        "mise run-ios\n"
        "```\n\n"
        "See [AGENTS.md](AGENTS.md) for the project rules.\n"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="GitHub repository name, for example Mottai")
    parser.add_argument("--display-name", help="Home screen name; defaults to the repo name")
    parser.add_argument("--bundle-id", required=True)
    parser.add_argument("--development-team", default="")
    parser.add_argument("--iphone-only", action="store_true", help="Target iPhone only instead of iPhone and iPad")
    parser.add_argument("--mac-catalyst", action="store_true", help="Enable Mac Catalyst")
    parser.add_argument("--template-repo", default=DEFAULT_TEMPLATE_REPO)
    parser.add_argument("--parent-dir", default=".")
    parser.add_argument("--visibility", choices=["private", "public"], default="private")
    parser.add_argument("--verify", choices=["none", "build", "test"], default="build")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_name = args.repo.split("/")[-1]
    parent_dir = Path(args.parent_dir).expanduser().resolve()
    repo_root = parent_dir / repo_name
    if repo_root.exists():
        raise SystemExit(f"Local destination already exists: {repo_root}")

    run(["gh", "repo", "create", args.repo, f"--{args.visibility}", "--template", args.template_repo, "--clone"], cwd=parent_dir)
    configure(
        repo_root,
        workspace_name=repo_name,
        display_name=args.display_name or repo_name,
        bundle_id=args.bundle_id,
        team=args.development_team.strip(),
        iphone_only=args.iphone_only,
        mac_catalyst=args.mac_catalyst,
    )

    if args.verify != "none":
        run(["mise", "trust", "mise.toml"], cwd=repo_root)
        run(["mise", args.verify], cwd=repo_root)

    print(f"Created project at: {repo_root}")
    print("Review the changes, then commit and push them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
