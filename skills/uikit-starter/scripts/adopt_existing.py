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

SCHEMA_VERSION = "1.0"
EXIT_OK = 0
EXIT_APPLY_NOT_READY = 2
ADOPTION_INTENTS = {
    "auto",
    "baseline-comparison",
    "preserve-existing-workflow",
    "full-template-conversion",
    "architecture-migration",
}
DEVKIT_BASELINE_FILES = [
    "Resources/DevKit/scripts/run_xcodebuild.sh",
    "Resources/DevKit/scripts/scan.license.sh",
    "Resources/DevKit/scripts/strip_stale_xcstrings.py",
    "Resources/DevKit/scripts/tidy_workspace_schemes.py",
    "Resources/DevKit/scripts/validate_xcstrings.py",
]


@dataclass(frozen=True)
class RepositoryProfile:
    repo_path: str
    is_git_repo: bool
    has_dirty_worktree: bool
    xcode_projects: list[str]
    nested_xcode_projects: list[str]
    xcode_workspaces: list[str]
    has_tuist: bool
    has_cocoapods: bool
    has_swift_package: bool
    has_swiftui_entry: bool
    has_uikit_lifecycle: bool
    app_targets: list[str]
    test_targets: list[str]
    bundle_identifiers: list[str]
    has_mise_tasks: bool
    has_swiftui_first_guidance: bool
    has_tuist_source_guidance: bool
    has_makefile: bool
    has_modern_uikit_devkit: bool
    devkit_missing_files: list[str]
    has_configuration_dir: bool
    has_test_plan: bool


@dataclass(frozen=True)
class AdoptionPlan:
    adoption_intent: str
    mode: str
    scenario: str
    status: str
    goal_supported_level: str
    summary: str
    recommended_questions: list[str]
    recommended_next_actions: list[str]
    proposed_changes: list[str]
    preserve_or_replace: dict[str, str]
    preserved_by_default: list[str]
    forbidden_actions: list[str]
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
    dry_run: bool
    created_files: list[str]
    skipped_files: list[str]
    would_create_files: list[str]
    would_skip_files: list[str]
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


def recursive_relative_paths(repo_root: Path, pattern: str) -> list[str]:
    return sorted(
        str(path.relative_to(repo_root))
        for path in repo_root.rglob(pattern)
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
    targets.update(name for name, product, _ in infer_tuist_targets(repo_root) if product == "app")
    return sorted(targets)


def infer_test_targets(repo_root: Path) -> list[str]:
    targets = {
        path.name
        for path in repo_root.iterdir()
        if path.is_dir() and path.name.endswith("Tests")
    }
    targets.update(
        name for name, product, _ in infer_tuist_targets(repo_root) if product == "unitTests"
    )
    return sorted(targets)


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
    identifiers.update(bundle_id for _, _, bundle_id in infer_tuist_targets(repo_root))
    return sorted(identifiers)


def infer_tuist_targets(repo_root: Path) -> list[tuple[str, str, str]]:
    manifest = repo_root / "Project.swift"
    if not manifest.exists():
        return []
    content = manifest.read_text(encoding="utf-8")
    matches = re.finditer(
        r"\.target\(\s*name:\s*\"([^\"]+)\".*?"
        r"product:\s*\.(app|unitTests).*?"
        r"bundleId:\s*\"([^\"]+)\"",
        content,
        flags=re.DOTALL,
    )
    return [(match.group(1), match.group(2), match.group(3)) for match in matches]


def has_guidance(repo_root: Path, needles: list[str]) -> bool:
    guidance_paths = [
        path
        for path in repo_root.rglob("AGENTS.md")
        if not should_skip(path, repo_root)
    ]
    for path in guidance_paths:
        content = path.read_text(encoding="utf-8")
        if any(needle in content for needle in needles):
            return True
    return False


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
    root_xcode_projects = relative_paths(repo_root, "*.xcodeproj")
    all_xcode_projects = recursive_relative_paths(repo_root, "*.xcodeproj")
    nested_xcode_projects = [
        path for path in all_xcode_projects if path not in root_xcode_projects
    ]
    devkit_missing_files = [
        relative_path
        for relative_path in DEVKIT_BASELINE_FILES
        if not (repo_root / relative_path).exists()
    ]
    return RepositoryProfile(
        repo_path=str(repo_root),
        is_git_repo=is_git_repo,
        has_dirty_worktree=has_dirty_worktree,
        xcode_projects=root_xcode_projects,
        nested_xcode_projects=nested_xcode_projects,
        xcode_workspaces=relative_paths(repo_root, "*.xcworkspace"),
        has_tuist=(repo_root / "Project.swift").exists()
        or (repo_root / "Workspace.swift").exists()
        or (repo_root / "Tuist").exists(),
        has_cocoapods=(repo_root / "Podfile").exists(),
        has_swift_package=(repo_root / "Package.swift").exists(),
        has_swiftui_entry=has_swiftui_entry(repo_root),
        has_uikit_lifecycle=contains_any(
            swift_files(repo_root),
            ["UIApplicationDelegate", "UISceneDelegate", "UIWindowScene"],
        ),
        app_targets=infer_app_targets(repo_root),
        test_targets=infer_test_targets(repo_root),
        bundle_identifiers=infer_bundle_identifiers(repo_root),
        has_mise_tasks=(repo_root / "mise.toml").exists(),
        has_swiftui_first_guidance=has_guidance(
            repo_root,
            ["Use SwiftUI first", "Do not introduce UIKit"],
        ),
        has_tuist_source_guidance=has_guidance(
            repo_root,
            ["Tuist as the source of truth", "Use Tuist as the source of truth"],
        ),
        has_makefile=(repo_root / "Makefile").exists(),
        has_modern_uikit_devkit=not devkit_missing_files,
        devkit_missing_files=devkit_missing_files,
        has_configuration_dir=(repo_root / "Configuration").is_dir(),
        has_test_plan=bool(relative_paths(repo_root, "*.xctestplan")),
    )


def build_plan(profile: RepositoryProfile, adoption_intent: str = "auto") -> AdoptionPlan:
    if adoption_intent not in ADOPTION_INTENTS:
        raise ValueError(f"Unsupported adoption intent: {adoption_intent}")

    blockers: list[str] = []
    warnings: list[str] = []
    questions: list[str] = []
    proposed_changes: list[str] = []

    if not profile.is_git_repo:
        blockers.append("Initialize git or run adoption from an existing git checkout.")
    if profile.has_dirty_worktree:
        blockers.append("Start from a clean worktree or create a backup branch first.")
    if (
        not profile.xcode_projects
        and not profile.nested_xcode_projects
        and not profile.xcode_workspaces
        and not profile.has_tuist
    ):
        blockers.append("No Xcode project or Tuist manifest was detected.")
    if profile.xcode_workspaces and not profile.xcode_projects and not profile.has_tuist:
        questions.append("Which project inside the workspace owns the app target?")
        warnings.append(
            "Workspace-only adoption is plan-only until the app project and dependency source of truth are explicit."
        )
    if not profile.xcode_projects and profile.nested_xcode_projects and not profile.has_tuist:
        warnings.append(
            "Only nested Xcode projects were detected; adoption must first choose the app project path."
        )
    if profile.xcode_projects and not profile.app_targets and not profile.has_tuist:
        questions.append("Which app target should receive the UIKit starter baseline?")
    if len(profile.xcode_projects) > 1:
        questions.append("Which root .xcodeproj is the main app project?")
    if len(profile.app_targets) > 1:
        questions.append("Which app target should receive the UIKit starter baseline?")
    if profile.has_cocoapods:
        questions.append(
            "Should CocoaPods and the existing workspace remain the dependency source of truth?"
        )
        warnings.append("CocoaPods workspace adoption is plan-only in this first slice.")
    if profile.has_swift_package and profile.nested_xcode_projects and not profile.xcode_projects:
        questions.append("Which nested app project should be treated as the iOS app surface?")
        warnings.append("SwiftPM package-first adoption is plan-only until the app project is selected.")
    if profile.has_tuist:
        if profile.has_tuist_source_guidance:
            warnings.append("Repo guidance says Tuist should remain the source of truth.")
        else:
            questions.append(
                "Should Tuist remain the source of truth, or should this repo migrate to the Xcode workspace baseline?"
            )
        warnings.append("Tuist adoption is plan-only in this first slice.")
    if profile.has_swiftui_entry and not profile.has_uikit_lifecycle:
        if profile.has_swiftui_first_guidance:
            questions.append(
                "This repo says SwiftUI first; confirm whether UIKit adoption is an architecture change or only a baseline comparison."
            )
            warnings.append("Repo guidance says not to introduce UIKit by default.")
        else:
            questions.append(
                "Should the first migration keep the SwiftUI root behind a UIKit shell, or replace the app entry directly?"
            )
        warnings.append("SwiftUI entry migration is plan-only in this first slice.")
    if adoption_intent == "full-template-conversion":
        if profile.has_tuist or profile.has_swiftui_entry or profile.has_cocoapods:
            questions.append(
                "Full template conversion would replace core project architecture; confirm the exact source-of-truth changes before any code edits."
            )
            warnings.append("Full template conversion is plan-only unless the repo is already a simple UIKit/Xcode app.")
    elif adoption_intent == "preserve-existing-workflow":
        warnings.append(
            "Preserve-existing-workflow intent forbids parallel build systems unless the user explicitly asks for them."
        )
    elif adoption_intent == "architecture-migration":
        questions.append(
            "Which architecture boundary should migrate first: lifecycle shell, folder structure, build workflow, or Agent contract?"
        )
        warnings.append("Architecture migration is plan-only until the first migration slice is selected.")

    if profile.has_tuist:
        proposed_changes.append(
            "Keep Tuist manifests and existing repo-scoped commands as the source of truth by default."
        )
        if profile.has_mise_tasks:
            proposed_changes.append(
                "Map any adopted build/test ideas into existing mise tasks instead of adding a parallel Makefile."
            )
        if not profile.has_modern_uikit_devkit:
            proposed_changes.append(
                "Port only compatible DevKit ideas into the Tuist/mise workflow after the migration decision is explicit."
            )
    elif profile.has_cocoapods:
        proposed_changes.append(
            "Preserve Podfile, existing workspace entrypoint, and dependency workflow by default."
        )
        proposed_changes.append(
            "Map compatible DevKit checks into the existing workspace instead of regenerating dependency state."
        )
    elif profile.has_swift_package and profile.nested_xcode_projects and not profile.xcode_projects:
        proposed_changes.append(
            "Preserve the package-first layout and select the nested iOS app project before applying starter surfaces."
        )
    else:
        if not profile.has_configuration_dir:
            proposed_changes.append("Add the Modern.UIKit Configuration/*.xcconfig baseline.")
        if not profile.has_modern_uikit_devkit:
            missing = ", ".join(profile.devkit_missing_files)
            proposed_changes.append(
                f"Add missing Resources/DevKit/scripts for log-aware workflows: {missing}."
            )
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

    if (
        adoption_intent == "full-template-conversion"
        and profile.has_tuist
        and profile.has_swiftui_entry
    ):
        mode = "tuist-full-conversion-plan"
        scenario = "tuist-swiftui-full-uikit-conversion-requested"
    elif profile.has_tuist:
        mode = "tuist-migration-assisted"
        if profile.has_swiftui_entry:
            scenario = "tuist-swiftui-guided-decision"
        else:
            scenario = "tuist-source-preserving-baseline"
    elif profile.has_cocoapods:
        mode = "workspace-preserving-assisted"
        scenario = "cocoapods-workspace-guided-decision"
    elif profile.xcode_workspaces and not profile.xcode_projects:
        mode = "workspace-preserving-assisted"
        scenario = "workspace-only-guided-decision"
    elif profile.has_swift_package and profile.nested_xcode_projects and not profile.xcode_projects:
        mode = "swiftpm-app-assisted"
        scenario = "swiftpm-nested-app-guided-decision"
    elif profile.has_swiftui_entry and not profile.has_uikit_lifecycle:
        mode = "swiftui-migration-assisted"
        scenario = "xcode-swiftui-entry-migration"
    elif profile.xcode_projects:
        mode = "xcode-adopt"
        scenario = "xcode-uikit-baseline-adoption"
    else:
        mode = "unsupported"
        scenario = "unsupported-repo-shape"

    status = "blocked" if blockers else "needs-confirmation" if questions else "ready"
    summary = {
        "blocked": "Adoption needs repo setup cleanup before changes are safe.",
        "needs-confirmation": "Adoption can proceed after the agent resolves the listed decisions.",
        "ready": "Adoption can proceed with the conservative Xcode/UIKit baseline plan.",
    }[status]

    if profile.has_tuist:
        verification = [
            "Review the generated migration-assisted plan before applying changes.",
            "Use the repo's existing Tuist/mise commands for validation.",
            "Do not add a parallel Makefile or xctestplan unless the migration decision explicitly changes the source of truth.",
        ]
    elif profile.has_cocoapods:
        verification = [
            "Review the generated workspace-preserving plan before applying changes.",
            "Use the existing workspace and dependency commands for validation.",
            "Do not delete Podfile, Pods workspace state, or generated workspace settings in an automated adoption pass.",
        ]
    elif profile.xcode_workspaces and not profile.xcode_projects:
        verification = [
            "Review the workspace-only plan before applying changes.",
            "Inspect the workspace contents and identify the app project before adopting starter surfaces.",
            "Do not assume workspace ownership from the repository root alone.",
        ]
    elif profile.has_swift_package and profile.nested_xcode_projects and not profile.xcode_projects:
        verification = [
            "Review the nested app selection before applying changes.",
            "Use the existing SwiftPM and app-project commands for validation.",
            "Do not assume the repository root is the app project root.",
        ]
    else:
        verification = [
            "Review the generated adoption plan before applying changes.",
            "Run make build for baseline adoption.",
            "Run make test when test files, xctestplan, or shared build settings change.",
        ]

    goal_supported_level = infer_goal_supported_level(
        profile,
        mode,
        scenario,
        status,
        adoption_intent,
    )
    next_actions = recommended_next_actions(
        profile,
        mode,
        scenario,
        blockers,
        questions,
        adoption_intent,
        goal_supported_level,
    )

    return AdoptionPlan(
        adoption_intent=adoption_intent,
        mode=mode,
        scenario=scenario,
        status=status,
        goal_supported_level=goal_supported_level,
        summary=summary,
        recommended_questions=questions,
        recommended_next_actions=next_actions,
        proposed_changes=proposed_changes,
        preserve_or_replace=preserve_or_replace_matrix(profile, scenario, adoption_intent),
        preserved_by_default=[
            "git history and remotes",
            "existing bundle identifiers",
            "existing signing settings unless explicitly overridden",
            "existing app source and resources",
            "existing product-specific documentation that does not conflict with the starter workflow",
        ],
        forbidden_actions=forbidden_actions(profile),
        blockers=blockers,
        warnings=warnings,
        verification=verification,
    )


def infer_goal_supported_level(
    profile: RepositoryProfile,
    mode: str,
    scenario: str,
    status: str,
    adoption_intent: str,
) -> str:
    if status == "blocked":
        return "blocked"
    if adoption_intent in {"baseline-comparison", "preserve-existing-workflow"}:
        return "safe-now"
    if mode == "xcode-adopt" and scenario == "xcode-uikit-baseline-adoption":
        return "safe-now"
    if adoption_intent == "full-template-conversion":
        if profile.has_tuist or profile.has_swiftui_entry or profile.has_cocoapods:
            return "unsupported-without-new-migration-tooling"
        return "safe-now"
    return "plan-only"


def preserve_or_replace_matrix(
    profile: RepositoryProfile,
    scenario: str,
    adoption_intent: str,
) -> dict[str, str]:
    matrix = {
        "git_history": "preserve",
        "remotes": "preserve",
        "bundle_identifiers": "preserve unless the user explicitly requests a rename",
        "signing": "preserve existing team and provisioning settings",
        "app_source": "preserve; additive adoption must not overwrite product code",
        "documentation": "preserve product-specific docs; update only stale workflow claims",
    }
    if profile.has_tuist:
        matrix["tuist"] = "preserve as source of truth by default"
    if profile.has_mise_tasks:
        matrix["mise"] = "preserve; map adopted commands into existing tasks"
    if profile.has_cocoapods:
        matrix["cocoapods"] = "preserve Podfile and workspace dependency flow"
    if profile.has_swift_package:
        matrix["swift_package"] = "preserve package-first boundaries"
    if profile.has_swiftui_entry:
        matrix["swiftui_entry"] = (
            "replace only after explicit architecture migration approval"
            if adoption_intent in {"full-template-conversion", "architecture-migration"}
            else "preserve for comparison or workflow hardening"
        )
    matrix["workspace"] = (
        "add or update only for ready xcode-adopt plans"
        if scenario == "xcode-uikit-baseline-adoption"
        else "preserve existing project/workspace entrypoints"
    )
    matrix["makefile"] = (
        "add if missing for ready Xcode/UIKit adoption"
        if scenario == "xcode-uikit-baseline-adoption" and not profile.has_makefile
        else "preserve existing command surface"
    )
    matrix["devkit"] = (
        "complete missing baseline files"
        if scenario == "xcode-uikit-baseline-adoption" and profile.devkit_missing_files
        else "port compatible checks into the existing workflow"
    )
    matrix["test_plan"] = (
        "add if missing and a test target can be identified"
        if scenario == "xcode-uikit-baseline-adoption" and not profile.has_test_plan
        else "preserve existing test entrypoints"
    )
    return matrix


def forbidden_actions(profile: RepositoryProfile) -> list[str]:
    actions = [
        "Do not overwrite existing source, project, configuration, or documentation files during automated adoption.",
        "Do not rewrite git history, remotes, bundle identifiers, or signing settings by default.",
        "Do not treat --dry-run output as permission to edit files.",
    ]
    if profile.has_tuist:
        actions.append(
            "Do not replace Project.swift, Workspace.swift, or Tuist-generated source of truth without explicit approval."
        )
    if profile.has_mise_tasks:
        actions.append(
            "Do not add a parallel command surface that conflicts with existing mise tasks."
        )
    if profile.has_swiftui_entry and not profile.has_uikit_lifecycle:
        actions.append(
            "Do not replace the SwiftUI @main entry or root architecture until the user confirms a UIKit migration."
        )
    if profile.has_cocoapods:
        actions.append(
            "Do not delete Podfile or regenerate dependency workspace state in an automated adoption pass."
        )
    if profile.nested_xcode_projects and not profile.xcode_projects:
        actions.append(
            "Do not assume a nested Xcode project is the main app without selecting it first."
        )
    return actions


def recommended_next_actions(
    profile: RepositoryProfile,
    mode: str,
    scenario: str,
    blockers: list[str],
    questions: list[str],
    adoption_intent: str,
    goal_supported_level: str,
) -> list[str]:
    if blockers:
        return [
            "Resolve blockers first; do not apply starter changes while repository state is unsafe.",
            "Re-run the analyzer after the worktree and project shape are ready.",
        ]

    if goal_supported_level == "unsupported-without-new-migration-tooling":
        return [
            "Stop at this plan; this goal needs dedicated migration tooling before code changes.",
            "Write a migration plan that names what will replace the existing source of truth and what remains preserved.",
            "Run a comparison pass first if the user only needs reusable Modern.UIKit practices.",
        ]

    if scenario == "xcode-uikit-baseline-adoption":
        actions = [
            "If the user wants baseline adoption, run the analyzer with --apply.",
            "If the user only wants a comparison, stop at the plan and summarize the missing baseline surfaces.",
        ]
        if adoption_intent == "preserve-existing-workflow":
            actions = [
                "Keep existing commands and apply only missing additive baseline files that do not conflict.",
                "Summarize any Modern.UIKit ideas that should be translated into current repo conventions.",
            ]
        if questions:
            actions.insert(0, "Answer the recommended questions before applying changes.")
        return actions

    if scenario == "xcode-swiftui-entry-migration":
        return [
            "Clarify whether UIKit is the desired architecture direction or only a starter-baseline comparison.",
            "If UIKit is the direction, plan the smallest shell migration before touching app entry code.",
            "If comparison is enough, preserve SwiftUI entry and only document reusable baseline ideas.",
        ]

    if scenario == "tuist-swiftui-guided-decision":
        actions = [
            "Ask whether the user wants baseline comparison, Tuist workflow hardening, or a real UIKit architecture migration.",
            "Keep Tuist and existing repo-scoped commands as source of truth unless the user explicitly chooses migration away from them.",
            "If the goal is UIKit migration, create a dedicated migration plan before code changes.",
        ]
        if profile.has_swiftui_first_guidance:
            actions.insert(0, "Treat SwiftUI-first guidance as binding until the user explicitly overrides it.")
        return actions

    if scenario == "tuist-swiftui-full-uikit-conversion-requested":
        return [
            "Stop at planning; full conversion from Tuist + SwiftUI is not an automated apply path yet.",
            "Decide whether Tuist, mise tasks, and SwiftUI entry are preserved, wrapped, or replaced.",
            "Create a staged migration plan before any source, manifest, or command-surface edits.",
        ]

    if scenario == "tuist-source-preserving-baseline":
        return [
            "Preserve Tuist manifests as source of truth by default.",
            "Map compatible baseline ideas into existing Tuist or mise workflows instead of adding parallel Xcode/Makefile surfaces.",
        ]

    if scenario == "cocoapods-workspace-guided-decision":
        return [
            "Preserve Podfile and the existing workspace while comparing reusable Modern.UIKit practices.",
            "Do not apply baseline files until the main workspace, app target, and dependency workflow are confirmed.",
            "If a full template conversion is requested, plan dependency migration separately before code edits.",
        ]

    if scenario == "workspace-only-guided-decision":
        return [
            "Inspect the workspace contents before applying any starter files.",
            "Identify the app project, app target, and dependency source of truth.",
            "Use this as a discovery report until workspace ownership is explicit.",
        ]

    if scenario == "swiftpm-nested-app-guided-decision":
        return [
            "Select the nested iOS app project before applying any starter surface.",
            "Preserve SwiftPM package boundaries and app-specific commands by default.",
            "Use the plan as a comparison report until app project ownership is explicit.",
        ]

    if mode == "unsupported":
        return [
            "Use the analyzer output as a discovery report only.",
            "Add support for this repo shape before attempting apply.",
        ]

    return ["Review the plan and choose the least disruptive path for the user's goal."]


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
    planned = planned_test_plan_if_missing(repo_root, names, profile)
    if planned is None:
        return None
    relative_path, created = planned
    if not created:
        return planned

    project_file = repo_root / profile.xcode_projects[0] / "project.pbxproj"
    target_id = infer_native_target_id(project_file, names.tests_name)
    if target_id is None:
        return None

    target_path = repo_root / relative_path
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
    return planned


def planned_test_plan_if_missing(
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

    return relative_path, True


def apply_adoption(
    profile: RepositoryProfile,
    plan: AdoptionPlan,
    template_root: Path,
    *,
    dry_run: bool = False,
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
        *DEVKIT_BASELINE_FILES,
        "Makefile",
    ]

    created_files: list[str] = []
    skipped_files: list[str] = []
    would_create_files: list[str] = []
    would_skip_files: list[str] = []
    for relative_path in baseline_files:
        if dry_run:
            target_path = repo_root / relative_path
            if target_path.exists():
                would_skip_files.append(relative_path)
            else:
                would_create_files.append(relative_path)
            continue
        path, created = write_rendered_file(template_root, repo_root, relative_path, names)
        if created:
            created_files.append(path)
        else:
            skipped_files.append(path)

    if dry_run:
        test_plan_result = planned_test_plan_if_missing(repo_root, names, profile)
        if test_plan_result is not None:
            path, created = test_plan_result
            if created:
                would_create_files.append(path)
            else:
                would_skip_files.append(path)
    else:
        test_plan_result = write_test_plan_if_missing(repo_root, names, profile)
        if test_plan_result is not None:
            path, created = test_plan_result
            if created:
                created_files.append(path)
            else:
                skipped_files.append(path)

    if dry_run:
        return ApplyResult(
            applied=False,
            dry_run=True,
            created_files=[],
            skipped_files=[],
            would_create_files=would_create_files,
            would_skip_files=would_skip_files,
            message="Dry run only; no files were changed.",
        )

    return ApplyResult(
        applied=True,
        dry_run=False,
        created_files=created_files,
        skipped_files=skipped_files,
        would_create_files=[],
        would_skip_files=[],
        message="Applied conservative Modern.UIKit baseline files without overwriting existing files.",
    )


def format_text(profile: RepositoryProfile, plan: AdoptionPlan) -> str:
    lines = [
        "# UIKit Starter Adoption Plan",
        "",
        f"Repository: {profile.repo_path}",
        f"Adoption intent: {plan.adoption_intent}",
        f"Mode: {plan.mode}",
        f"Scenario: {plan.scenario}",
        f"Status: {plan.status}",
        f"Goal supported level: {plan.goal_supported_level}",
        f"Summary: {plan.summary}",
        "",
        "Detected:",
        f"- Git repo: {'yes' if profile.is_git_repo else 'no'}",
        f"- Dirty worktree: {'yes' if profile.has_dirty_worktree else 'no'}",
        f"- Xcode projects: {', '.join(profile.xcode_projects) or '(none)'}",
        f"- Nested Xcode projects: {', '.join(profile.nested_xcode_projects) or '(none)'}",
        f"- Xcode workspaces: {', '.join(profile.xcode_workspaces) or '(none)'}",
        f"- Tuist: {'yes' if profile.has_tuist else 'no'}",
        f"- CocoaPods: {'yes' if profile.has_cocoapods else 'no'}",
        f"- Swift package: {'yes' if profile.has_swift_package else 'no'}",
        f"- SwiftUI entry: {'yes' if profile.has_swiftui_entry else 'no'}",
        f"- UIKit lifecycle: {'yes' if profile.has_uikit_lifecycle else 'no'}",
        f"- App targets: {', '.join(profile.app_targets) or '(none)'}",
        f"- Test targets: {', '.join(profile.test_targets) or '(none)'}",
        f"- Bundle identifiers: {', '.join(profile.bundle_identifiers) or '(none)'}",
        f"- mise tasks: {'yes' if profile.has_mise_tasks else 'no'}",
        f"- SwiftUI-first guidance: {'yes' if profile.has_swiftui_first_guidance else 'no'}",
        f"- Tuist source guidance: {'yes' if profile.has_tuist_source_guidance else 'no'}",
        f"- Modern.UIKit DevKit complete: {'yes' if profile.has_modern_uikit_devkit else 'no'}",
        f"- Missing DevKit files: {', '.join(profile.devkit_missing_files) or '(none)'}",
        "",
    ]
    sections = [
        ("Blockers", plan.blockers),
        ("Recommended Questions", plan.recommended_questions),
        ("Recommended Next Actions", plan.recommended_next_actions),
        ("Warnings", plan.warnings),
        ("Proposed Changes", plan.proposed_changes),
        ("Preserved By Default", plan.preserved_by_default),
        ("Forbidden Actions", plan.forbidden_actions),
        ("Verification", plan.verification),
    ]
    for title, values in sections:
        lines.append(f"{title}:")
        if values:
            lines.extend(f"- {value}" for value in values)
        else:
            lines.append("- (none)")
        lines.append("")
    lines.append("Preserve Or Replace:")
    if plan.preserve_or_replace:
        lines.extend(f"- {key}: {value}" for key, value in plan.preserve_or_replace.items())
    else:
        lines.append("- (none)")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-path", default=".")
    parser.add_argument("--template-root", default=str(template_root_from_script()))
    parser.add_argument("--intent", choices=sorted(ADOPTION_INTENTS), default="auto")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.apply and args.dry_run:
        raise SystemExit("--apply and --dry-run cannot be used together.")

    profile = analyze_repository(Path(args.repo_path))
    plan = build_plan(profile, args.intent)
    apply_result = None
    should_preview_or_apply = args.apply or args.dry_run
    if should_preview_or_apply:
        if plan.status != "ready" or plan.mode != "xcode-adopt":
            if args.format == "json":
                payload = build_json_payload(profile, plan, None)
                print(json.dumps(payload, indent=2))
            else:
                print(format_text(profile, plan), end="")
                action = "Apply" if args.apply else "Dry run"
                print(
                    f"{action} unavailable: adoption apply is only available for ready xcode-adopt plans."
                )
            return EXIT_APPLY_NOT_READY
        apply_result = apply_adoption(
            profile,
            plan,
            Path(args.template_root),
            dry_run=args.dry_run,
        )

    if args.format == "json":
        payload = build_json_payload(profile, plan, apply_result)
        print(json.dumps(payload, indent=2))
    else:
        print(format_text(profile, plan), end="")
        if apply_result is not None:
            print("Apply Result:")
            print(f"- {apply_result.message}")
            if apply_result.dry_run:
                print(
                    f"- Would create: {', '.join(apply_result.would_create_files) if apply_result.would_create_files else '(none)'}"
                )
                print(
                    f"- Would skip existing: {', '.join(apply_result.would_skip_files) if apply_result.would_skip_files else '(none)'}"
                )
            else:
                print(
                    f"- Created: {', '.join(apply_result.created_files) if apply_result.created_files else '(none)'}"
                )
                print(
                    f"- Skipped existing: {', '.join(apply_result.skipped_files) if apply_result.skipped_files else '(none)'}"
                )
    return EXIT_OK


def build_json_payload(
    profile: RepositoryProfile,
    plan: AdoptionPlan,
    apply_result: ApplyResult | None,
) -> dict:
    payload = {
        "schema_version": SCHEMA_VERSION,
        "exit_code_contract": {
            str(EXIT_OK): "analysis completed; apply or dry-run completed when requested and available",
            str(EXIT_APPLY_NOT_READY): "--apply or --dry-run was requested but the plan is not ready xcode-adopt",
        },
        "profile": asdict(profile),
        "plan": asdict(plan),
    }
    if apply_result is not None:
        payload["apply"] = asdict(apply_result)
    return payload


if __name__ == "__main__":
    raise SystemExit(main())
