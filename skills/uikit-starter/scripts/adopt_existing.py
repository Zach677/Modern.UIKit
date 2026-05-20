#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path


SKIP_DIR_NAMES = {
    ".build",
    ".git",
    ".swiftpm",
    "DerivedData",
    "Vendor",
    "xcuserdata",
}


@dataclass(frozen=True)
class RepositoryProfile:
    repo_path: str
    is_git_repo: bool
    has_dirty_worktree: bool
    xcode_projects: list[str]
    xcode_workspaces: list[str]
    has_tuist: bool
    has_swiftui_entry: bool
    has_uikit_lifecycle: bool
    app_targets: list[str]
    test_targets: list[str]
    bundle_identifiers: list[str]
    has_makefile: bool
    has_modern_uikit_devkit: bool
    has_configuration_dir: bool
    has_test_plan: bool


@dataclass(frozen=True)
class AdoptionPlan:
    mode: str
    status: str
    summary: str
    recommended_questions: list[str]
    proposed_changes: list[str]
    preserved_by_default: list[str]
    blockers: list[str]
    warnings: list[str]
    verification: list[str]


@dataclass(frozen=True)
class AdoptionNames:
    project_name: str
    scheme_name: str
    source_dir_name: str
    tests_name: str
    bundle_identifier: str


@dataclass(frozen=True)
class ApplyResult:
    applied: bool
    created_files: list[str]
    skipped_files: list[str]
    message: str


def run_capture(command: list[str], cwd: Path) -> tuple[int, str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return result.returncode, result.stdout.strip()


def relative_paths(repo_root: Path, pattern: str) -> list[str]:
    return sorted(
        str(path.relative_to(repo_root))
        for path in repo_root.glob(pattern)
        if not should_skip(path, repo_root)
    )


def should_skip(path: Path, repo_root: Path) -> bool:
    try:
        parts = path.relative_to(repo_root).parts
    except ValueError:
        return True
    return any(part in SKIP_DIR_NAMES for part in parts)


def text_files(repo_root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(repo_root.rglob("*")):
        if not path.is_file() or path.is_symlink() or should_skip(path, repo_root):
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if b"\0" in data:
            continue
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            continue
        files.append(path)
    return files


def swift_files(repo_root: Path) -> list[Path]:
    return [
        path
        for path in text_files(repo_root)
        if path.suffix == ".swift"
    ]


def contains_any(paths: list[Path], needles: list[str]) -> bool:
    for path in paths:
        content = path.read_text(encoding="utf-8")
        if any(needle in content for needle in needles):
            return True
    return False


def has_swiftui_entry(repo_root: Path) -> bool:
    for path in swift_files(repo_root):
        content = path.read_text(encoding="utf-8")
        if "import SwiftUI" in content and ("@main" in content or ": App" in content):
            return True
    return False


def lines_containing(repo_root: Path, suffix: str, marker: str) -> list[str]:
    values: set[str] = set()
    for path in sorted(repo_root.rglob(f"*{suffix}")):
        if should_skip(path, repo_root):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for line in content.splitlines():
            stripped = line.strip()
            if marker in stripped:
                values.add(stripped)
    return sorted(values)


def detect_git_status(repo_root: Path) -> tuple[bool, bool]:
    code, _ = run_capture(["git", "rev-parse", "--is-inside-work-tree"], cwd=repo_root)
    if code != 0:
        return False, False
    _, output = run_capture(["git", "status", "--porcelain"], cwd=repo_root)
    return True, bool(output)


def infer_app_targets(repo_root: Path) -> list[str]:
    targets: set[str] = set()
    for path in sorted(repo_root.glob("*/Resources/Info.plist")):
        if should_skip(path, repo_root):
            continue
        targets.add(path.relative_to(repo_root).parts[0])
    return sorted(targets)


def infer_test_targets(repo_root: Path) -> list[str]:
    return sorted(
        path.name
        for path in repo_root.iterdir()
        if path.is_dir() and path.name.endswith("Tests")
    )


def infer_bundle_identifiers(repo_root: Path) -> list[str]:
    lines = lines_containing(repo_root, ".xcconfig", "PRODUCT_BUNDLE_IDENTIFIER")
    lines.extend(lines_containing(repo_root, ".pbxproj", "PRODUCT_BUNDLE_IDENTIFIER"))
    identifiers: set[str] = set()
    for line in lines:
        if "=" not in line:
            continue
        value = line.split("=", 1)[1].strip().rstrip(";").strip('"')
        if value:
            identifiers.add(value)
    return sorted(identifiers)


def infer_native_target_id(project_file: Path, target_name: str) -> str | None:
    if not project_file.exists():
        return None
    content = project_file.read_text(encoding="utf-8", errors="ignore")
    pattern = rf"\b([A-F0-9]{{24}}) /\* {re.escape(target_name)} \*/ = \{{isa = PBXNativeTarget;"
    match = re.search(pattern, content)
    if match:
        return match.group(1)
    return None


def analyze_repository(repo_root: Path) -> RepositoryProfile:
    repo_root = repo_root.expanduser().resolve()
    if not repo_root.exists():
        raise SystemExit(f"Repository path does not exist: {repo_root}")
    if not repo_root.is_dir():
        raise SystemExit(f"Repository path is not a directory: {repo_root}")

    is_git_repo, has_dirty_worktree = detect_git_status(repo_root)
    return RepositoryProfile(
        repo_path=str(repo_root),
        is_git_repo=is_git_repo,
        has_dirty_worktree=has_dirty_worktree,
        xcode_projects=relative_paths(repo_root, "*.xcodeproj"),
        xcode_workspaces=relative_paths(repo_root, "*.xcworkspace"),
        has_tuist=(repo_root / "Project.swift").exists()
        or (repo_root / "Workspace.swift").exists()
        or (repo_root / "Tuist").exists(),
        has_swiftui_entry=has_swiftui_entry(repo_root),
        has_uikit_lifecycle=contains_any(
            swift_files(repo_root),
            ["UIApplicationDelegate", "UISceneDelegate", "UIWindowScene"],
        ),
        app_targets=infer_app_targets(repo_root),
        test_targets=infer_test_targets(repo_root),
        bundle_identifiers=infer_bundle_identifiers(repo_root),
        has_makefile=(repo_root / "Makefile").exists(),
        has_modern_uikit_devkit=(
            repo_root / "Resources" / "DevKit" / "scripts" / "run_xcodebuild.sh"
        ).exists(),
        has_configuration_dir=(repo_root / "Configuration").is_dir(),
        has_test_plan=bool(relative_paths(repo_root, "*.xctestplan")),
    )


def build_plan(profile: RepositoryProfile) -> AdoptionPlan:
    blockers: list[str] = []
    warnings: list[str] = []
    questions: list[str] = []
    proposed_changes: list[str] = []

    if not profile.is_git_repo:
        blockers.append("Initialize git or run adoption from an existing git checkout.")
    if profile.has_dirty_worktree:
        blockers.append("Start from a clean worktree or create a backup branch first.")
    if not profile.xcode_projects and not profile.has_tuist:
        blockers.append("No root Xcode project or Tuist manifest was detected.")
    if len(profile.xcode_projects) > 1:
        questions.append("Which root .xcodeproj is the main app project?")
    if len(profile.app_targets) > 1:
        questions.append("Which app target should receive the UIKit starter baseline?")
    if profile.has_tuist:
        questions.append(
            "Should Tuist remain the source of truth, or should this repo migrate to the Xcode workspace baseline?"
        )
        warnings.append("Tuist adoption is plan-only in this first slice.")
    if profile.has_swiftui_entry and not profile.has_uikit_lifecycle:
        questions.append(
            "Should the first migration keep the SwiftUI root behind a UIKit shell, or replace the app entry directly?"
        )
        warnings.append("SwiftUI entry migration is plan-only in this first slice.")

    if not profile.has_configuration_dir:
        proposed_changes.append("Add the Modern.UIKit Configuration/*.xcconfig baseline.")
    if not profile.has_modern_uikit_devkit:
        proposed_changes.append("Add Resources/DevKit/scripts for log-aware build, test, localization, and license workflows.")
    if not profile.has_makefile:
        proposed_changes.append("Add a top-level Makefile that drives the adopted repo through shared targets.")
    if not profile.has_test_plan:
        proposed_changes.append("Add an app-level .xctestplan attached to the shared scheme.")

    proposed_changes.extend(
        [
            "Refresh README.md and AGENTS.md with the adopted repo's actual workflow.",
            "Preserve app source, resources, target names, signing identity, bundle identifiers, git history, and remotes by default.",
        ]
    )

    if profile.has_tuist:
        mode = "tuist-migration-assisted"
    elif profile.has_swiftui_entry and not profile.has_uikit_lifecycle:
        mode = "swiftui-migration-assisted"
    elif profile.xcode_projects:
        mode = "xcode-adopt"
    else:
        mode = "unsupported"

    status = "blocked" if blockers else "needs-confirmation" if questions else "ready"
    summary = {
        "blocked": "Adoption needs repo setup cleanup before changes are safe.",
        "needs-confirmation": "Adoption can proceed after the agent resolves the listed decisions.",
        "ready": "Adoption can proceed with the conservative Xcode/UIKit baseline plan.",
    }[status]

    return AdoptionPlan(
        mode=mode,
        status=status,
        summary=summary,
        recommended_questions=questions,
        proposed_changes=proposed_changes,
        preserved_by_default=[
            "git history and remotes",
            "existing bundle identifiers",
            "existing signing settings unless explicitly overridden",
            "existing app source and resources",
            "existing product-specific documentation that does not conflict with the starter workflow",
        ],
        blockers=blockers,
        warnings=warnings,
        verification=[
            "Review the generated adoption plan before applying changes.",
            "Run make build for baseline adoption.",
            "Run make test when test files, xctestplan, or shared build settings change.",
        ],
    )


def template_root_from_script() -> Path:
    return Path(__file__).resolve().parents[3]


def infer_names(profile: RepositoryProfile) -> AdoptionNames:
    if len(profile.xcode_projects) == 1:
        project_name = Path(profile.xcode_projects[0]).stem
    elif len(profile.app_targets) == 1:
        project_name = profile.app_targets[0]
    else:
        raise SystemExit("Unable to infer project name for adoption.")

    source_dir_name = profile.app_targets[0] if len(profile.app_targets) == 1 else project_name
    tests_name = profile.test_targets[0] if len(profile.test_targets) == 1 else f"{project_name}Tests"
    concrete_identifiers = [
        value
        for value in profile.bundle_identifiers
        if "$(" not in value and not value.endswith(".tests")
    ]
    bundle_identifier = concrete_identifiers[0] if concrete_identifiers else profile.bundle_identifiers[0] if profile.bundle_identifiers else "com.example.$(PRODUCT_NAME:rfc1034identifier)"

    return AdoptionNames(
        project_name=project_name,
        scheme_name=project_name,
        source_dir_name=source_dir_name,
        tests_name=tests_name,
        bundle_identifier=bundle_identifier,
    )


def rendered_text(source_path: Path, names: AdoptionNames) -> str:
    content = source_path.read_text(encoding="utf-8")
    replacements = [
        ("ModernUIKitTests", names.tests_name),
        ("ModernUIKit", names.project_name),
        ("modern-uikit", names.project_name.lower()),
        ("com.example.$(PRODUCT_NAME:rfc1034identifier)", names.bundle_identifier),
    ]
    for old, new in replacements:
        content = content.replace(old, new)
    return content


def write_rendered_file(
    template_root: Path,
    repo_root: Path,
    relative_path: str,
    names: AdoptionNames,
) -> tuple[str, bool]:
    source_path = template_root / relative_path
    target_path = repo_root / relative_path
    if target_path.exists():
        return relative_path, False

    target_path.parent.mkdir(parents=True, exist_ok=True)
    if source_path.suffix in {".sh", ".py", ".xcconfig"} or source_path.name == "Makefile":
        target_path.write_text(rendered_text(source_path, names), encoding="utf-8")
        shutil.copymode(source_path, target_path)
    else:
        shutil.copy2(source_path, target_path)
    return relative_path, True


def write_test_plan_if_missing(
    repo_root: Path,
    names: AdoptionNames,
    profile: RepositoryProfile,
) -> tuple[str, bool] | None:
    if profile.has_test_plan or not profile.xcode_projects or not profile.test_targets:
        return None

    project_file = repo_root / profile.xcode_projects[0] / "project.pbxproj"
    target_id = infer_native_target_id(project_file, names.tests_name)
    if target_id is None:
        return None

    relative_path = f"{names.project_name}.xctestplan"
    target_path = repo_root / relative_path
    if target_path.exists():
        return relative_path, False

    payload = {
        "configurations": [
            {
                "id": "1A3B5C7D-9E10-4A11-8B12-13C14D15E16F",
                "name": "Default",
                "options": {},
            }
        ],
        "defaultOptions": {"testTimeoutsEnabled": True},
        "testTargets": [
            {
                "target": {
                    "containerPath": f"container:{names.project_name}.xcodeproj",
                    "identifier": target_id,
                    "name": names.tests_name,
                }
            }
        ],
        "version": 1,
    }
    target_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return relative_path, True


def apply_adoption(
    profile: RepositoryProfile,
    plan: AdoptionPlan,
    template_root: Path,
) -> ApplyResult:
    if plan.status != "ready" or plan.mode != "xcode-adopt":
        raise SystemExit("Adoption apply is only available for ready xcode-adopt plans.")

    repo_root = Path(profile.repo_path)
    template_root = template_root.expanduser().resolve()
    if not template_root.exists():
        raise SystemExit(f"Template root does not exist: {template_root}")

    names = infer_names(profile)
    baseline_files = [
        "Configuration/Base.xcconfig",
        "Configuration/Development.xcconfig",
        "Configuration/Release.xcconfig",
        "Configuration/Version.xcconfig",
        "Resources/DevKit/scripts/run_xcodebuild.sh",
        "Resources/DevKit/scripts/scan.license.sh",
        "Resources/DevKit/scripts/strip_stale_xcstrings.py",
        "Resources/DevKit/scripts/tidy_workspace_schemes.py",
        "Resources/DevKit/scripts/validate_xcstrings.py",
        "Makefile",
    ]

    created_files: list[str] = []
    skipped_files: list[str] = []
    for relative_path in baseline_files:
        path, created = write_rendered_file(template_root, repo_root, relative_path, names)
        if created:
            created_files.append(path)
        else:
            skipped_files.append(path)

    test_plan_result = write_test_plan_if_missing(repo_root, names, profile)
    if test_plan_result is not None:
        path, created = test_plan_result
        if created:
            created_files.append(path)
        else:
            skipped_files.append(path)

    return ApplyResult(
        applied=True,
        created_files=created_files,
        skipped_files=skipped_files,
        message="Applied conservative Modern.UIKit baseline files without overwriting existing files.",
    )


def format_text(profile: RepositoryProfile, plan: AdoptionPlan) -> str:
    lines = [
        "# UIKit Starter Adoption Plan",
        "",
        f"Repository: {profile.repo_path}",
        f"Mode: {plan.mode}",
        f"Status: {plan.status}",
        f"Summary: {plan.summary}",
        "",
        "Detected:",
        f"- Git repo: {'yes' if profile.is_git_repo else 'no'}",
        f"- Dirty worktree: {'yes' if profile.has_dirty_worktree else 'no'}",
        f"- Xcode projects: {', '.join(profile.xcode_projects) or '(none)'}",
        f"- Xcode workspaces: {', '.join(profile.xcode_workspaces) or '(none)'}",
        f"- Tuist: {'yes' if profile.has_tuist else 'no'}",
        f"- SwiftUI entry: {'yes' if profile.has_swiftui_entry else 'no'}",
        f"- UIKit lifecycle: {'yes' if profile.has_uikit_lifecycle else 'no'}",
        f"- App targets: {', '.join(profile.app_targets) or '(none)'}",
        f"- Test targets: {', '.join(profile.test_targets) or '(none)'}",
        f"- Bundle identifiers: {', '.join(profile.bundle_identifiers) or '(none)'}",
        "",
    ]
    sections = [
        ("Blockers", plan.blockers),
        ("Recommended Questions", plan.recommended_questions),
        ("Warnings", plan.warnings),
        ("Proposed Changes", plan.proposed_changes),
        ("Preserved By Default", plan.preserved_by_default),
        ("Verification", plan.verification),
    ]
    for title, values in sections:
        lines.append(f"{title}:")
        if values:
            lines.extend(f"- {value}" for value in values)
        else:
            lines.append("- (none)")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-path", default=".")
    parser.add_argument("--template-root", default=str(template_root_from_script()))
    parser.add_argument("--apply", action="store_true")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    profile = analyze_repository(Path(args.repo_path))
    plan = build_plan(profile)
    apply_result = (
        apply_adoption(profile, plan, Path(args.template_root)) if args.apply else None
    )
    if args.format == "json":
        payload = {"profile": asdict(profile), "plan": asdict(plan)}
        if apply_result is not None:
            payload["apply"] = asdict(apply_result)
        print(json.dumps(payload, indent=2))
    else:
        print(format_text(profile, plan), end="")
        if apply_result is not None:
            print("Apply Result:")
            print(f"- {apply_result.message}")
            print(
                f"- Created: {', '.join(apply_result.created_files) if apply_result.created_files else '(none)'}"
            )
            print(
                f"- Skipped existing: {', '.join(apply_result.skipped_files) if apply_result.skipped_files else '(none)'}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
