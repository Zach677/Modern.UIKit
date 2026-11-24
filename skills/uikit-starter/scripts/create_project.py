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
ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"
MAC_CATALYST_ENTITLEMENTS = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
\t<key>com.apple.security.app-sandbox</key>
\t<true/>
</dict>
</plist>
"""


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
        src = template_dir / name
        target = repo_root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if src.is_symlink():
            os.symlink(os.readlink(src), target)
        else:
            # Copy permissions without carrying over the template checkout's old timestamps.
            shutil.copy(src, target)


def set_xcconfig_value(path: Path, key: str, value: str) -> None:
    text = path.read_text(encoding="utf-8")
    pattern = re.compile(rf"^{re.escape(key)} =.*$", re.MULTILINE)
    if not pattern.search(text):
        raise SystemExit(f"{key} not found in {path}")
    path.write_text(pattern.sub(lambda _: f"{key} = {value}".rstrip(), text, count=1), encoding="utf-8")


def configure_mac_catalyst(repo_root: Path) -> None:
    entitlements = repo_root / "App" / "Resources" / "MacCatalyst.entitlements"
    entitlements.write_text(MAC_CATALYST_ENTITLEMENTS, encoding="utf-8")

    pbxproj = repo_root / "App.xcodeproj" / "project.pbxproj"
    text = pbxproj.read_text(encoding="utf-8")
    anchor = (
        "\t\t\t\tASSETCATALOG_COMPILER_GLOBAL_ACCENT_COLOR_NAME = AccentColor;\n"
        "\t\t\t\tINFOPLIST_FILE = App/Resources/Info.plist;\n"
    )
    if text.count(anchor) != 2:
        raise SystemExit(f"Expected 2 App build configurations in {pbxproj}, found {text.count(anchor)}")
    replacement = (
        "\t\t\t\tASSETCATALOG_COMPILER_GLOBAL_ACCENT_COLOR_NAME = AccentColor;\n"
        '\t\t\t\t"CODE_SIGN_ENTITLEMENTS[sdk=macosx*]" = App/Resources/MacCatalyst.entitlements;\n'
        '\t\t\t\t"ENABLE_HARDENED_RUNTIME[sdk=macosx*]" = YES;\n'
        "\t\t\t\tINFOPLIST_FILE = App/Resources/Info.plist;\n"
    )
    pbxproj.write_text(text.replace(anchor, replacement), encoding="utf-8")


def validate_author(author: str) -> None:
    if any(ch in author for ch in ("\n", "\r", "\\", "{", "}")):
        raise SystemExit(f"Invalid --author value: {author!r}")


def escape_swiftformat_quoted(value: str) -> str:
    return value.replace('"', '\\"')


def configure_file_headers(repo_root: Path, workspace_name: str, author: str) -> None:
    validate_author(author)

    escaped_workspace = escape_swiftformat_quoted(workspace_name)
    escaped_author = escape_swiftformat_quoted(author)
    swiftformat = repo_root / ".swiftformat"
    swiftformat_text = swiftformat.read_text(encoding="utf-8").rstrip("\n")
    swiftformat.write_text(
        f"{swiftformat_text}\n"
        f'--header "\\n {{file}}\\n {escaped_workspace}\\n\\n Created by {escaped_author} on {{created}}.\\n"\n'
        "--date-format yyyy/MM/dd\n",
        encoding="utf-8",
    )

    hook = repo_root / ".githooks" / "pre-commit"
    hook.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ASSETS_DIR / "pre-commit", hook)

    mise_path = repo_root / "mise.toml"
    mise_text = mise_path.read_text(encoding="utf-8")
    anchor = "[tasks.format]\n"
    if anchor not in mise_text:
        raise SystemExit(f"[tasks.format] not found in {mise_path}")
    hooks_task = (
        "[tasks.hooks]\n"
        'description = "Enable the repo\'s Git hooks (Swift file headers on commit)"\n'
        'run = "git config core.hooksPath .githooks"\n\n'
    )
    mise_path.write_text(mise_text.replace(anchor, hooks_task + anchor, 1), encoding="utf-8")

    agents_path = repo_root / "AGENTS.md"
    agents_text = agents_path.read_text(encoding="utf-8")
    old_install = "Run `mise install` once to get the pinned SwiftFormat and xcbeautify."
    new_install = (
        "Run `mise install` once to get the pinned SwiftFormat and xcbeautify, "
        "and `mise hooks` once so the pre-commit hook adds the Swift file header "
        "(`.swiftformat`) to staged Swift files."
    )
    old_format_row = "| `mise format` / `mise format-lint` |"
    new_format_row = (
        "| `mise hooks` | Enable the repo's Git hooks (`.githooks/pre-commit` adds Swift file headers on commit) |\n"
        "| `mise format` / `mise format-lint` |"
    )
    if old_install not in agents_text or old_format_row not in agents_text:
        raise SystemExit(f"Expected Build and Test entries not found in {agents_path}")
    agents_text = agents_text.replace(old_install, new_install, 1).replace(old_format_row, new_format_row, 1)
    agents_path.write_text(agents_text, encoding="utf-8")


def configure(
    repo_root: Path,
    workspace_name: str,
    display_name: str,
    bundle_id: str,
    team: str,
    ipad: bool = False,
    mac_catalyst: bool = False,
    author: str = "",
) -> None:
    base = repo_root / "Configuration" / "Base.xcconfig"
    set_xcconfig_value(base, "APP_DISPLAY_NAME", display_name)
    set_xcconfig_value(base, "APP_BUNDLE_IDENTIFIER", bundle_id)
    set_xcconfig_value(base, "DEVELOPMENT_TEAM", team)
    # Mac Catalyst builds the iPad app, so it needs the iPad family.
    set_xcconfig_value(base, "TARGETED_DEVICE_FAMILY", "1,2" if ipad or mac_catalyst else "1")
    set_xcconfig_value(base, "SUPPORTS_MACCATALYST", "YES" if mac_catalyst else "NO")

    if mac_catalyst:
        configure_mac_catalyst(repo_root)

    if author:
        configure_file_headers(repo_root, workspace_name, author)

    (workspace,) = repo_root.glob("*.xcworkspace")
    workspace.rename(repo_root / f"{workspace_name}.xcworkspace")

    hooks_line = "mise hooks\n" if author else ""
    (repo_root / "README.md").write_text(
        f"# {display_name}\n\n"
        "A programmatic UIKit app for iOS 26.\n\n"
        "## Development\n\n"
        f"Open `{workspace_name}.xcworkspace`, or use:\n\n"
        "```bash\n"
        "mise install\n"
        f"{hooks_line}"
        "mise run-ios\n"
        "mise check    # run before each commit\n"
        "```\n\n"
        "See [AGENTS.md](AGENTS.md) for the project rules.\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="GitHub repository name, for example Mottai")
    parser.add_argument("--display-name", help="Home screen name; defaults to the repo name")
    parser.add_argument("--bundle-id", required=True)
    parser.add_argument("--development-team", default="")
    parser.add_argument("--ipad", action="store_true", help="Target iPhone and iPad instead of iPhone only")
    parser.add_argument(
        "--mac-catalyst",
        action="store_true",
        help="Enable Mac Catalyst with App Sandbox entitlements and Hardened Runtime; implies --ipad",
    )
    parser.add_argument(
        "--author",
        default="",
        help="Author name for Swift file headers and the pre-commit hook (for example @Zach677); omitted by default",
    )
    parser.add_argument("--template-repo", default=DEFAULT_TEMPLATE_REPO, help="GitHub repo to clone template/ from")
    parser.add_argument("--template-dir", help="Local template/ directory to copy instead of cloning --template-repo")
    parser.add_argument("--parent-dir", default=".")
    parser.add_argument("--visibility", choices=["private", "public"], default="private")
    parser.add_argument("--no-remote", action="store_true", help="Do not create the GitHub repo or add origin")
    parser.add_argument("--verify", choices=["none", "build", "test", "check"], default="build")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_spec = args.repo.strip("/")
    repo_name = repo_spec.split("/")[-1]
    if not repo_name:
        raise SystemExit(f"Invalid repository name: {args.repo!r}")
    validate_author(args.author)
    author = args.author.strip()
    parent_dir = Path(args.parent_dir).expanduser().resolve()
    repo_root = parent_dir / repo_name
    if repo_root.exists():
        raise SystemExit(f"Local destination already exists: {repo_root}")

    # Check the commands and the gh sign-in before the script creates a directory or a GitHub repo.
    required = {"git": "https://git-scm.com"}
    if not args.no_remote:
        required["gh"] = "https://cli.github.com"
    if args.verify != "none":
        required["mise"] = "https://mise.jdx.dev"
    missing = [f"{name} not found. Install it from {url}, then rerun." for name, url in required.items() if not shutil.which(name)]
    if missing:
        raise SystemExit("\n".join(missing))
    if not args.no_remote and subprocess.run(["gh", "auth", "status"], capture_output=True, check=False).returncode != 0:
        raise SystemExit("gh is not signed in. Run gh auth login, or rerun with --no-remote.")

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
        author=author,
    )
    run(["git", "init", "--quiet"], cwd=repo_root)
    if author:
        run(["git", "config", "core.hooksPath", ".githooks"], cwd=repo_root)
    if not args.no_remote:
        # Creates the empty GitHub repo and adds it as origin. Nothing is pushed.
        run(["gh", "repo", "create", repo_spec, f"--{args.visibility}", "--source", ".", "--remote", "origin"], cwd=repo_root)

    if args.verify != "none":
        run(["mise", "trust", "mise.toml"], cwd=repo_root)
        run(["mise", "install"], cwd=repo_root)
        if author:
            run(["mise", "run", "format"], cwd=repo_root)
        run(["mise", args.verify], cwd=repo_root)

    print(f"Created project at: {repo_root}")
    print("Review the changes, then commit and push them.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
