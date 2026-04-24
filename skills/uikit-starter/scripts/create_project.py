#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path
from xml.sax.saxutils import escape


DEFAULT_TEMPLATE_REPO = "Zach677/Modern.UIKit"
SKIP_DIR_NAMES = {
    ".git",
    ".DerivedData",
    "__pycache__",
    "xcuserdata",
}


def run(command: list[str], cwd: Path | None = None) -> None:
    result = subprocess.run(command, cwd=cwd, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def safe_project_name(value: str) -> str:
    trimmed = value.strip()
    if not trimmed:
        raise SystemExit("Project name cannot be empty.")
    if not re.fullmatch(r"[A-Za-z0-9_-]+", trimmed):
        raise SystemExit(
            "Project name must contain only letters, digits, hyphens, or underscores."
        )
    return trimmed


def repo_basename(repo_name: str) -> str:
    return repo_name.split("/")[-1]


def humanize_project_name(project_name: str) -> str:
    parts = re.sub(r"[_-]+", " ", project_name).strip()
    parts = re.sub(r"(?<!^)([A-Z])", r" \1", parts).strip()
    parts = re.sub(r"\s+", " ", parts)
    return " ".join(piece.capitalize() for piece in parts.split())


def swift_module_name(name: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_]", "_", name)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    if not normalized:
        raise SystemExit("Unable to derive Swift module name.")
    if normalized[0].isdigit():
        normalized = f"_{normalized}"
    return normalized


def bundle_component(value: str) -> str:
    component = re.sub(r"[^a-zA-Z0-9]+", "", value).lower()
    if not component:
        raise SystemExit("Unable to derive bundle identifier component.")
    return component


def derive_bundle_id(project_name: str, repo_name: str | None) -> str:
    seed = repo_basename(repo_name) if repo_name else project_name
    return f"com.example.{bundle_component(seed)}"


def infer_source_dir(repo_root: Path) -> str:
    info_plist_paths = sorted(repo_root.glob("*/Resources/Info.plist"))
    info_plist_paths = [
        path for path in info_plist_paths if not should_skip(path, repo_root)
    ]
    if len(info_plist_paths) != 1:
        raise SystemExit("Expected exactly one app Resources/Info.plist path.")
    return info_plist_paths[0].relative_to(repo_root).parts[0]


def detect_template_markers(repo_root: Path) -> dict[str, str]:
    project_paths = sorted(repo_root.glob("*.xcodeproj"))
    if len(project_paths) != 1:
        raise SystemExit("Expected exactly one .xcodeproj at the repository root.")

    project_path = project_paths[0]
    project_name = project_path.stem
    workspace_paths = sorted(repo_root.glob("*.xcworkspace"))
    workspace_name = workspace_paths[0].stem if len(workspace_paths) == 1 else None
    testplan_paths = sorted(repo_root.glob("*.xctestplan"))
    testplan_name = testplan_paths[0].stem if len(testplan_paths) == 1 else None

    source_dir = infer_source_dir(repo_root)

    tests_dirs = [
        path.name
        for path in repo_root.iterdir()
        if path.is_dir() and path.name.endswith("Tests")
    ]
    if len(tests_dirs) != 1:
        raise SystemExit("Expected exactly one root test directory ending with 'Tests'.")

    return {
        "project_name": project_name,
        "project_module": swift_module_name(project_name),
        "workspace_name": workspace_name,
        "testplan_name": testplan_name,
        "source_dir": source_dir,
        "tests_name": tests_dirs[0],
        "tests_module": swift_module_name(tests_dirs[0]),
    }


def should_skip(path: Path, repo_root: Path) -> bool:
    relative_parts = path.relative_to(repo_root).parts
    return any(part in SKIP_DIR_NAMES for part in relative_parts)


def is_text_file(path: Path) -> bool:
    if path.is_symlink():
        return False
    try:
        data = path.read_bytes()
    except OSError:
        return False
    if b"\0" in data:
        return False
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def replace_across_repo(repo_root: Path, replacements: list[tuple[str, str]]) -> None:
    for path in sorted(repo_root.rglob("*")):
        if not path.is_file() or should_skip(path, repo_root):
            continue
        if not is_text_file(path):
            continue
        original = path.read_text(encoding="utf-8")
        updated = original
        for old, new in replacements:
            updated = updated.replace(old, new)
        if updated != original:
            path.write_text(updated, encoding="utf-8")


def replace_assignment(path: Path, key: str, value: str) -> None:
    content = path.read_text(encoding="utf-8")
    pattern = rf"^{re.escape(key)}\s*=.*$"
    replacement = f"{key} = {value}"
    updated, count = re.subn(pattern, replacement, content, flags=re.MULTILINE)
    if count == 0:
        raise SystemExit(f"Failed to update {key} in {path}.")
    path.write_text(updated, encoding="utf-8")


def replace_literal(path: Path, old: str, new: str) -> None:
    content = path.read_text(encoding="utf-8")
    if old not in content:
        raise SystemExit(f"Failed to find expected text in {path}: {old}")
    path.write_text(content.replace(old, new), encoding="utf-8")


def remove_path_if_exists(path: Path) -> None:
    if not path.exists():
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
        return
    path.unlink()


def ensure_display_name(info_plist: Path, display_name: str) -> None:
    content = info_plist.read_text(encoding="utf-8")
    key_block = "<key>CFBundleDisplayName</key>"
    value_block = f"{key_block}\n\t<string>{escape(display_name)}</string>"
    if key_block in content:
        updated = re.sub(
            r"<key>CFBundleDisplayName</key>\s*<string>.*?</string>",
            value_block,
            content,
            count=1,
            flags=re.DOTALL,
        )
    else:
        updated = content.replace("</dict>", f"\t{value_block}\n</dict>", 1)
    info_plist.write_text(updated, encoding="utf-8")


def rename_path(path: Path, new_name: str) -> Path:
    if path.name == new_name:
        return path
    target = path.with_name(new_name)
    if target.exists():
        raise SystemExit(f"Cannot rename {path} to {target}; destination already exists.")
    path.rename(target)
    return target


def write_generated_readme(
    repo_root: Path,
    project_name: str,
    display_name: str,
    source_dir_name: str,
    tests_name: str,
) -> None:
    content = f"""# {display_name}

`{display_name}` is a programmatic UIKit iOS app with a code-driven starter baseline.

## Project Layout

- `{source_dir_name}/` — app target source and bundled resources
- `{tests_name}/` — hosted app tests
- `Configuration/` — shared Xcode build configuration
- `Resources/DevKit/scripts/` — reusable build, test, localization, and license-maintenance scripts
- `{project_name}.xcworkspace` — default Xcode entrypoint
- `{project_name}.xctestplan` — shared test plan attached to the app scheme

## Development

Build and test through the top-level `Makefile`:

```bash
make build
make build-ios
make build-sim
make build-device
make build-catalyst
make test
make test-unit
make package-resolve
make strip-xcstrings
make validate-xcstrings
make tidy-schemes
make clean
```

Defaults:

- `make build` covers the primary development paths: iOS Simulator plus Mac Catalyst
- `make test` / `make test-unit` run on the Mac Catalyst destination
- `Resources/DevKit/scripts/run_xcodebuild.sh` treats the build log as the source of truth instead of trusting exit codes alone

Tooling expectations:

- `xcbeautify` should be available on `PATH`
- `prettier` should be available for DevKit formatting flows; the repo invokes it through `npx --yes prettier ...`

## Optional Debug Inspection

LookInside is optional local developer tooling. This app does not link `LookInsideServer` by default.

Manual local setup:

```bash
brew install --cask Zach677/star/lookinside

git clone https://github.com/LookInsideApp/LookInsideServer.git ~/Developer/other-repo/LookInsideServer
cd ~/Developer/other-repo/LookInsideServer
swift build -c release --product lookinside
mkdir -p ~/.local/bin
ln -sfn "$PWD/.build/release/lookinside" ~/.local/bin/lookinside

lookinside --help
lookinside list --format json
```

A target only appears in `lookinside list` after the app runs `LookinServer` or a compatible injected runtime. Keep that setup developer-local or debug-only unless the project explicitly adopts LookInside as shared tooling.

If a coding agent configures LookInside, ask it to follow `AGENTS.md` and the `lookinside-cli` skill, verify the local app and CLI, and avoid committing `LookInsideServer` app wiring unless you explicitly request it.

## Local Signing Overrides

By default the app uses a placeholder bundle identifier:

```text
com.example.$(PRODUCT_NAME:rfc1034identifier)
```

The base configuration intentionally keeps signing and bundle overrides in `Configuration/*.xcconfig`; target and platform settings stay with the Xcode project unless they need a local override.

If you need local signing values without committing them, create one or more of:

- `Configuration/Developer.xcconfig`
- `Configuration/DevelopmentDeveloper.xcconfig`
- `Configuration/DeveloperRelease.xcconfig`

Typical overrides:

```xcconfig
DEVELOPMENT_TEAM = YOURTEAMID
PRODUCT_BUNDLE_IDENTIFIER = com.yourcompany.yourapp
```

## Notes

- Entry stays `main.swift` -> `AppDelegate` -> `SceneDelegate`
- `LaunchScreen.storyboard` is the only storyboard; there is no `Main.storyboard`
- App resources live under `{source_dir_name}/Resources/`
- LookInside is optional local developer tooling; the generated app does not link it by default
- If the app grows beyond starter scope, add runtime/domain logic under `{source_dir_name}/Backend/`
"""
    (repo_root / "README.md").write_text(content, encoding="utf-8")


def prune_template_only_files(repo_root: Path) -> None:
    remove_path_if_exists(repo_root / "skills" / "uikit-starter")
    skills_dir = repo_root / "skills"
    if skills_dir.exists() and not any(skills_dir.iterdir()):
        skills_dir.rmdir()


def create_from_github(
    repo_name: str,
    template_repo: str,
    visibility: str,
    parent_dir: Path,
) -> Path:
    parent_dir.mkdir(parents=True, exist_ok=True)
    local_dir = parent_dir / repo_basename(repo_name)
    if local_dir.exists():
        raise SystemExit(f"Local destination already exists: {local_dir}")

    run(["gh", "auth", "status"])
    run(["gh", "repo", "view", template_repo])
    run(
        [
            "gh",
            "repo",
            "create",
            repo_name,
            f"--{visibility}",
            "--template",
            template_repo,
            "--clone",
        ],
        cwd=parent_dir,
    )
    return local_dir


def verify_repo(repo_root: Path, mode: str) -> None:
    if mode == "none":
        return
    command = ["make", "build"] if mode == "build" else ["make", "test"]
    run(command, cwd=repo_root)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-name", required=True)
    parser.add_argument("--display-name")
    parser.add_argument("--repo", required=True)
    parser.add_argument("--template-repo", default=DEFAULT_TEMPLATE_REPO)
    parser.add_argument("--bundle-id")
    parser.add_argument("--source-dir-name")
    parser.add_argument("--parent-dir", default=".")
    parser.add_argument(
        "--visibility",
        choices=["private", "public", "internal"],
        default="private",
    )
    parser.add_argument(
        "--verify",
        choices=["none", "build", "test"],
        default="build",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    project_name = safe_project_name(args.project_name)
    display_name = args.display_name or humanize_project_name(project_name)
    bundle_id = args.bundle_id or derive_bundle_id(project_name, args.repo)
    tests_name = f"{project_name}Tests"
    tests_bundle_id = f"{bundle_id}.tests"

    local_repo_path = create_from_github(
        repo_name=args.repo,
        template_repo=args.template_repo,
        visibility=args.visibility,
        parent_dir=Path(args.parent_dir).expanduser().resolve(),
    )

    markers = detect_template_markers(local_repo_path)
    source_dir_name = args.source_dir_name or project_name

    replacements = sorted(
        [
            (markers["tests_module"], swift_module_name(tests_name)),
            (markers["tests_name"], tests_name),
            (markers["project_module"], swift_module_name(project_name)),
            (markers["project_name"], project_name),
            (markers["source_dir"], source_dir_name),
        ],
        key=lambda item: len(item[0]),
        reverse=True,
    )
    replace_across_repo(local_repo_path, replacements)

    replace_assignment(
        local_repo_path / "Configuration" / "Base.xcconfig",
        "PRODUCT_BUNDLE_IDENTIFIER",
        bundle_id,
    )

    source_dir = local_repo_path / markers["source_dir"]
    tests_dir = local_repo_path / markers["tests_name"]
    xcodeproj_dir = local_repo_path / f'{markers["project_name"]}.xcodeproj'
    workspace_dir = (
        local_repo_path / f'{markers["workspace_name"]}.xcworkspace'
        if markers["workspace_name"]
        else None
    )
    testplan_file = (
        local_repo_path / f'{markers["testplan_name"]}.xctestplan'
        if markers["testplan_name"]
        else None
    )

    renamed_source_dir = rename_path(source_dir, source_dir_name)
    rename_path(tests_dir, tests_name)
    ensure_display_name(renamed_source_dir / "Resources" / "Info.plist", display_name)
    prune_template_only_files(local_repo_path)
    write_generated_readme(
        repo_root=local_repo_path,
        project_name=project_name,
        display_name=display_name,
        source_dir_name=source_dir_name,
        tests_name=tests_name,
    )

    scheme_path = (
        xcodeproj_dir / "xcshareddata" / "xcschemes" / f'{markers["project_name"]}.xcscheme'
    )
    if scheme_path.exists():
        rename_path(scheme_path, f"{project_name}.xcscheme")

    renamed_project_dir = rename_path(xcodeproj_dir, f"{project_name}.xcodeproj")
    replace_literal(
        renamed_project_dir / "project.pbxproj",
        'PRODUCT_BUNDLE_IDENTIFIER = "com.example.$(PRODUCT_NAME:rfc1034identifier)";',
        f'PRODUCT_BUNDLE_IDENTIFIER = "{tests_bundle_id}";',
    )
    if workspace_dir and workspace_dir.exists():
        rename_path(workspace_dir, f"{project_name}.xcworkspace")
    if testplan_file and testplan_file.exists():
        rename_path(testplan_file, f"{project_name}.xctestplan")

    verify_repo(local_repo_path, args.verify)

    print(f"Created project at: {local_repo_path}")
    print(f"Project name: {project_name}")
    print(f"Display name: {display_name}")
    print(f"Bundle identifier: {bundle_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
