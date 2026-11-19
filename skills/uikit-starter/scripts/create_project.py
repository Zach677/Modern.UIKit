#!/usr/bin/env python3
"""Create a new app repository from the template/ directory of Modern.UIKit."""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

DEFAULT_TEMPLATE_REPO = "Zach677/Modern.UIKit"


def run(command: list[str], cwd: Path | None = None) -> None:
    result = subprocess.run(command, cwd=cwd, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def template_files(template_dir: Path) -> list[str]:
    """Tracked and untracked-but-not-ignored files, so build output and local overrides stay out."""
    output = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=template_dir,
        check=True,
        capture_output=True,
        text=True,
    ).stdout
    # A tracked file that was deleted in the working tree is still listed.
    return sorted({name for name in output.split("\0") if name and os.path.lexists(template_dir / name)})


def copy_template(template_dir: Path, repo_root: Path) -> None:
    for name in template_files(template_dir):
        target = repo_root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(template_dir / name, target, follow_symlinks=False)


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
    ipad: bool = False,
    mac_catalyst: bool = False,
) -> None:
    base = repo_root / "Configuration" / "Base.xcconfig"
    set_xcconfig_value(base, "APP_DISPLAY_NAME", display_name)
    set_xcconfig_value(base, "APP_BUNDLE_IDENTIFIER", bundle_id)
    set_xcconfig_value(base, "DEVELOPMENT_TEAM", team)
    # Mac Catalyst builds the iPad app, so it needs the iPad family.
    set_xcconfig_value(base, "TARGETED_DEVICE_FAMILY", "1,2" if ipad or mac_catalyst else "1")
    set_xcconfig_value(base, "SUPPORTS_MACCATALYST", "YES" if mac_catalyst else "NO")

    (workspace,) = repo_root.glob("*.xcworkspace")
    workspace.rename(repo_root / f"{workspace_name}.xcworkspace")

    (repo_root / "README.md").write_text(
        f"# {display_name}\n\n"
        "A programmatic UIKit app for iOS 26.\n\n"
        "## Development\n\n"
        f"Open `{workspace_name}.xcworkspace`, or use:\n\n"
        "```bash\n"
        "mise install\n"
        "mise run-ios\n"
        "mise check    # run before each commit\n"
        "```\n\n"
        "See [AGENTS.md](AGENTS.md) for the project rules.\n"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="GitHub repository name, for example Mottai")
    parser.add_argument("--display-name", help="Home screen name; defaults to the repo name")
    parser.add_argument("--bundle-id", required=True)
    parser.add_argument("--development-team", default="")
    parser.add_argument("--ipad", action="store_true", help="Target iPhone and iPad instead of iPhone only")
    parser.add_argument("--mac-catalyst", action="store_true", help="Enable Mac Catalyst; implies --ipad")
    parser.add_argument("--template-repo", default=DEFAULT_TEMPLATE_REPO, help="GitHub repo to clone template/ from")
    parser.add_argument("--template-dir", help="Local template/ directory to copy instead of cloning --template-repo")
    parser.add_argument("--parent-dir", default=".")
    parser.add_argument("--visibility", choices=["private", "public"], default="private")
    parser.add_argument("--no-remote", action="store_true", help="Do not create the GitHub repo or add origin")
    parser.add_argument("--verify", choices=["none", "build", "test", "check"], default="build")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_name = args.repo.split("/")[-1]
    parent_dir = Path(args.parent_dir).expanduser().resolve()
    repo_root = parent_dir / repo_name
    if repo_root.exists():
        raise SystemExit(f"Local destination already exists: {repo_root}")

    if args.template_dir:
        copy_template(Path(args.template_dir).expanduser().resolve(), repo_root)
    else:
        with tempfile.TemporaryDirectory() as clone:
            run(["git", "clone", "--quiet", "--depth", "1", f"https://github.com/{args.template_repo}.git", clone])
            copy_template(Path(clone) / "template", repo_root)
    configure(
        repo_root,
        workspace_name=repo_name,
        display_name=args.display_name or repo_name,
        bundle_id=args.bundle_id,
        team=args.development_team.strip(),
        ipad=args.ipad,
        mac_catalyst=args.mac_catalyst,
    )
    run(["git", "init", "--quiet"], cwd=repo_root)
    if not args.no_remote:
        # Creates the empty GitHub repo and adds it as origin. Nothing is pushed.
        run(["gh", "repo", "create", args.repo, f"--{args.visibility}", "--source", ".", "--remote", "origin"], cwd=repo_root)

    if args.verify != "none":
        run(["mise", "trust", "mise.toml"], cwd=repo_root)
        run(["mise", args.verify], cwd=repo_root)

    print(f"Created project at: {repo_root}")
    print("Review the changes, then commit and push them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
