from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "adopt_existing.py"
SPEC = importlib.util.spec_from_file_location("adopt_existing", SCRIPT_PATH)
adopt_existing = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["adopt_existing"] = adopt_existing
SPEC.loader.exec_module(adopt_existing)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def commit_all(repo_root: Path) -> None:
    subprocess.run(["git", "init"], cwd=repo_root, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=repo_root,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=repo_root,
        check=True,
    )
    subprocess.run(["git", "add", "."], cwd=repo_root, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial fixture"],
        cwd=repo_root,
        check=True,
        stdout=subprocess.DEVNULL,
    )


def template_fixture() -> Path:
    return Path(__file__).resolve().parents[3]


def make_ready_xcode_fixture(repo_root: Path) -> None:
    project_dir = repo_root / "Fixture.xcodeproj"
    project_dir.mkdir()
    write(
        project_dir / "project.pbxproj",
        "F829D09D2E252176005A7D1A /* FixtureTests */ = {isa = PBXNativeTarget; };\n",
    )
    write(repo_root / "Fixture" / "Resources" / "Info.plist", "<plist />")
    write(
        repo_root / "Fixture" / "AppDelegate.swift",
        "import UIKit\nfinal class AppDelegate: UIResponder, UIApplicationDelegate {}\n",
    )
    write(repo_root / "FixtureTests" / "FixtureTests.swift", "import Testing\n")


class AnalyzeRepositoryTests(unittest.TestCase):
    def test_detects_ready_uikit_xcode_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / "Fixture.xcodeproj").mkdir()
            write(repo_root / "Fixture" / "Resources" / "Info.plist", "<plist />")
            write(
                repo_root / "Fixture" / "AppDelegate.swift",
                "import UIKit\nfinal class AppDelegate: UIResponder, UIApplicationDelegate {}\n",
            )
            write(
                repo_root / "Configuration" / "Base.xcconfig",
                "PRODUCT_BUNDLE_IDENTIFIER = com.example.fixture\n",
            )
            commit_all(repo_root)

            profile = adopt_existing.analyze_repository(repo_root)
            plan = adopt_existing.build_plan(profile)

        self.assertEqual(plan.mode, "xcode-adopt")
        self.assertEqual(plan.scenario, "xcode-uikit-baseline-adoption")
        self.assertEqual(plan.status, "ready")
        self.assertEqual(plan.goal_supported_level, "apply-ready")
        self.assertTrue(plan.can_apply)
        self.assertTrue(plan.can_dry_run)
        self.assertFalse(plan.requires_confirmation)
        self.assertTrue(any("--apply" in action for action in plan.recommended_next_actions))
        self.assertEqual(profile.app_targets, ["Fixture"])
        self.assertEqual(profile.bundle_identifiers, ["com.example.fixture"])

    def test_dirty_worktree_blocks_adoption(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / "Fixture.xcodeproj").mkdir()
            write(repo_root / "Fixture" / "Resources" / "Info.plist", "<plist />")
            write(
                repo_root / "Fixture" / "AppDelegate.swift",
                "import UIKit\nfinal class AppDelegate: UIResponder, UIApplicationDelegate {}\n",
            )
            commit_all(repo_root)
            write(repo_root / "README.md", "# Dirty fixture\n")

            profile = adopt_existing.analyze_repository(repo_root)
            plan = adopt_existing.build_plan(profile)

        self.assertEqual(plan.status, "blocked")
        self.assertFalse(plan.can_apply)
        self.assertIn("clean worktree", " ".join(plan.blockers))
        self.assertTrue(any("Resolve blockers" in action for action in plan.recommended_next_actions))

    def test_non_git_repo_is_discovery_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / "Fixture.xcodeproj").mkdir()
            write(repo_root / "Fixture" / "Resources" / "Info.plist", "<plist />")
            write(
                repo_root / "Fixture" / "AppDelegate.swift",
                "import UIKit\nfinal class AppDelegate: UIResponder, UIApplicationDelegate {}\n",
            )

            profile = adopt_existing.analyze_repository(repo_root)
            plan = adopt_existing.build_plan(profile)

        self.assertFalse(profile.is_git_repo)
        self.assertEqual(plan.status, "blocked")
        self.assertTrue(any("Initialize git" in blocker for blocker in plan.blockers))

    def test_tuist_repo_asks_source_of_truth_question(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            write(repo_root / "Project.swift", "import ProjectDescription\n")
            commit_all(repo_root)

            profile = adopt_existing.analyze_repository(repo_root)
            plan = adopt_existing.build_plan(profile)

        self.assertEqual(plan.mode, "tuist-migration-assisted")
        self.assertEqual(plan.scenario, "tuist-source-preserving-baseline")
        self.assertEqual(plan.status, "needs-confirmation")
        self.assertTrue(any("Tuist remain" in question for question in plan.recommended_questions))

    def test_tuist_manifest_targets_and_guidance_shape_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            write(
                repo_root / "AGENTS.md",
                "Use SwiftUI first.\nUse Tuist as the source of truth for project generation.\n",
            )
            write(repo_root / "mise.toml", "[tasks.test-ios]\nrun = \"bash scripts/test-ios.sh\"\n")
            write(
                repo_root / "Project.swift",
                """
import ProjectDescription

let project = Project(
    name: "SubPanda",
    targets: [
        .target(
            name: "SubPanda",
            product: .app,
            bundleId: "org.zaxh.SubPanda"
        ),
        .target(
            name: "SubPandaTests",
            product: .unitTests,
            bundleId: "org.zaxh.SubPandaTests"
        ),
    ]
)
""",
            )
            write(
                repo_root / "SubPanda" / "Sources" / "App" / "SubPandaApp.swift",
                "import SwiftUI\n@main\nstruct SubPandaApp: App {}\n",
            )
            commit_all(repo_root)

            profile = adopt_existing.analyze_repository(repo_root)
            plan = adopt_existing.build_plan(profile)

        self.assertEqual(profile.app_targets, ["SubPanda"])
        self.assertEqual(profile.test_targets, ["SubPandaTests"])
        self.assertEqual(
            profile.bundle_identifiers,
            ["org.zaxh.SubPanda", "org.zaxh.SubPandaTests"],
        )
        self.assertTrue(profile.has_mise_tasks)
        self.assertTrue(profile.has_swiftui_first_guidance)
        self.assertTrue(profile.has_tuist_source_guidance)
        self.assertEqual(plan.scenario, "tuist-swiftui-guided-decision")
        self.assertEqual(plan.goal_supported_level, "plan-only")
        self.assertTrue(any("mise tasks" in change for change in plan.proposed_changes))
        self.assertFalse(
            any("Add a top-level Makefile" in change for change in plan.proposed_changes)
        )
        self.assertTrue(any("SwiftUI first" in question for question in plan.recommended_questions))
        self.assertTrue(
            any("SwiftUI-first guidance" in action for action in plan.recommended_next_actions)
        )
        self.assertEqual(
            plan.preserve_or_replace["tuist"],
            "preserve as source of truth by default",
        )
        self.assertTrue(any("Project.swift" in action for action in plan.forbidden_actions))
        self.assertTrue(any("Tuist/mise" in step for step in plan.verification))

    def test_full_template_intent_on_tuist_swiftui_is_plan_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            write(
                repo_root / "Project.swift",
                """
import ProjectDescription

let project = Project(
    name: "SubPanda",
    targets: [
        .target(name: "SubPanda", product: .app, bundleId: "org.zaxh.SubPanda"),
    ]
)
""",
            )
            write(
                repo_root / "SubPanda" / "Sources" / "App" / "SubPandaApp.swift",
                "import SwiftUI\n@main\nstruct SubPandaApp: App {}\n",
            )
            commit_all(repo_root)

            profile = adopt_existing.analyze_repository(repo_root)
            plan = adopt_existing.build_plan(profile, "full-template-conversion")

        self.assertEqual(plan.scenario, "tuist-swiftui-full-uikit-conversion-requested")
        self.assertEqual(plan.status, "needs-confirmation")
        self.assertEqual(
            plan.goal_supported_level,
            "unsupported-without-new-migration-tooling",
        )
        self.assertTrue(any("Stop at this plan" in action for action in plan.recommended_next_actions))
        self.assertTrue(
            any("Full template conversion" in question for question in plan.recommended_questions)
        )

    def test_swiftui_repo_asks_entry_strategy_question(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / "Fixture.xcodeproj").mkdir()
            write(repo_root / "Fixture" / "Resources" / "Info.plist", "<plist />")
            write(
                repo_root / "Fixture" / "FixtureApp.swift",
                "import SwiftUI\n@main\nstruct FixtureApp: App {}\n",
            )
            commit_all(repo_root)

            profile = adopt_existing.analyze_repository(repo_root)
            plan = adopt_existing.build_plan(profile)

        self.assertEqual(plan.mode, "swiftui-migration-assisted")
        self.assertEqual(plan.scenario, "xcode-swiftui-entry-migration")
        self.assertEqual(plan.status, "needs-confirmation")
        self.assertTrue(any("SwiftUI root" in question for question in plan.recommended_questions))
        self.assertTrue(any("shell migration" in action for action in plan.recommended_next_actions))

    def test_swiftui_app_with_delegate_adaptor_is_not_ready_xcode_adopt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / "Fixture.xcodeproj").mkdir()
            write(repo_root / "Fixture" / "Resources" / "Info.plist", "<plist />")
            write(
                repo_root / "Fixture" / "AppDelegate.swift",
                "import UIKit\nfinal class AppDelegate: UIResponder, UIApplicationDelegate {}\n",
            )
            write(
                repo_root / "Fixture" / "FixtureApp.swift",
                """
import SwiftUI

@main
struct FixtureApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    var body: some Scene { WindowGroup { Text("Hi") } }
}
""",
            )
            commit_all(repo_root)

            profile = adopt_existing.analyze_repository(repo_root)
            plan = adopt_existing.build_plan(profile)

        self.assertTrue(profile.has_swiftui_entry)
        self.assertTrue(profile.has_uikit_lifecycle)
        self.assertEqual(plan.mode, "swiftui-migration-assisted")
        self.assertEqual(plan.scenario, "xcode-swiftui-entry-migration")
        self.assertFalse(plan.can_apply)

    def test_baseline_comparison_intent_on_swiftui_repo_is_safe_to_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / "Fixture.xcodeproj").mkdir()
            write(repo_root / "Fixture" / "Resources" / "Info.plist", "<plist />")
            write(
                repo_root / "Fixture" / "FixtureApp.swift",
                "import SwiftUI\n@main\nstruct FixtureApp: App {}\n",
            )
            commit_all(repo_root)

            profile = adopt_existing.analyze_repository(repo_root)
            plan = adopt_existing.build_plan(profile, "baseline-comparison")

        self.assertEqual(plan.scenario, "xcode-swiftui-entry-migration")
        self.assertEqual(plan.goal_supported_level, "safe-to-plan-now")
        self.assertFalse(plan.can_apply)
        self.assertFalse(plan.can_dry_run)
        self.assertEqual(
            plan.preserve_or_replace["swiftui_entry"],
            "preserve for comparison or workflow hardening",
        )

    def test_architecture_migration_intent_on_swiftui_repo_requires_first_slice(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / "Fixture.xcodeproj").mkdir()
            write(repo_root / "Fixture" / "Resources" / "Info.plist", "<plist />")
            write(
                repo_root / "Fixture" / "FixtureApp.swift",
                "import SwiftUI\n@main\nstruct FixtureApp: App {}\n",
            )
            commit_all(repo_root)

            profile = adopt_existing.analyze_repository(repo_root)
            plan = adopt_existing.build_plan(profile, "architecture-migration")

        self.assertEqual(plan.scenario, "xcode-swiftui-entry-migration")
        self.assertEqual(plan.goal_supported_level, "plan-only")
        self.assertFalse(plan.can_apply)
        self.assertTrue(any("architecture boundary" in question for question in plan.recommended_questions))
        self.assertEqual(
            plan.preserve_or_replace["swiftui_entry"],
            "replace only after explicit architecture migration approval",
        )

    def test_cocoapods_workspace_is_preserved_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / "Fixture.xcodeproj").mkdir()
            (repo_root / "Fixture.xcworkspace").mkdir()
            write(repo_root / "Podfile", "target 'Fixture' do\nend\n")
            write(repo_root / "Fixture" / "Resources" / "Info.plist", "<plist />")
            write(
                repo_root / "Fixture" / "AppDelegate.swift",
                "import UIKit\nfinal class AppDelegate: UIResponder, UIApplicationDelegate {}\n",
            )
            commit_all(repo_root)

            profile = adopt_existing.analyze_repository(repo_root)
            plan = adopt_existing.build_plan(profile)

        self.assertTrue(profile.has_cocoapods)
        self.assertEqual(plan.mode, "workspace-preserving-assisted")
        self.assertEqual(plan.scenario, "cocoapods-workspace-guided-decision")
        self.assertEqual(plan.status, "needs-confirmation")
        self.assertEqual(
            plan.preserve_or_replace["cocoapods"],
            "preserve Podfile and workspace dependency flow",
        )
        self.assertTrue(any("Podfile" in action for action in plan.forbidden_actions))

    def test_full_template_intent_on_cocoapods_workspace_is_not_apply_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / "Fixture.xcodeproj").mkdir()
            (repo_root / "Fixture.xcworkspace").mkdir()
            write(repo_root / "Podfile", "target 'Fixture' do\nend\n")
            write(repo_root / "Fixture" / "Resources" / "Info.plist", "<plist />")
            write(
                repo_root / "Fixture" / "AppDelegate.swift",
                "import UIKit\nfinal class AppDelegate: UIResponder, UIApplicationDelegate {}\n",
            )
            commit_all(repo_root)

            profile = adopt_existing.analyze_repository(repo_root)
            plan = adopt_existing.build_plan(profile, "full-template-conversion")

        self.assertEqual(plan.scenario, "cocoapods-workspace-guided-decision")
        self.assertEqual(
            plan.goal_supported_level,
            "unsupported-without-new-migration-tooling",
        )
        self.assertTrue(any("Stop at this plan" in action for action in plan.recommended_next_actions))

    def test_full_template_intent_on_workspace_only_repo_is_unsupported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            write(
                repo_root / "Fixture.xcworkspace" / "contents.xcworkspacedata",
                "<Workspace version=\"1.0\"></Workspace>\n",
            )
            commit_all(repo_root)

            profile = adopt_existing.analyze_repository(repo_root)
            plan = adopt_existing.build_plan(profile, "full-template-conversion")

        self.assertEqual(plan.scenario, "workspace-only-guided-decision")
        self.assertEqual(
            plan.goal_supported_level,
            "unsupported-without-new-migration-tooling",
        )
        self.assertFalse(plan.can_apply)
        self.assertEqual(
            plan.unsupported_reason,
            "Workspace-only repositories need app project discovery before conversion.",
        )

    def test_workspace_only_repo_is_guided_decision_not_unsupported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            write(
                repo_root / "Fixture.xcworkspace" / "contents.xcworkspacedata",
                "<Workspace version=\"1.0\"></Workspace>\n",
            )
            commit_all(repo_root)

            profile = adopt_existing.analyze_repository(repo_root)
            plan = adopt_existing.build_plan(profile)

        self.assertEqual(profile.xcode_projects, [])
        self.assertEqual(profile.xcode_workspaces, ["Fixture.xcworkspace"])
        self.assertEqual(plan.mode, "workspace-preserving-assisted")
        self.assertEqual(plan.scenario, "workspace-only-guided-decision")
        self.assertEqual(plan.status, "needs-confirmation")
        self.assertFalse(plan.can_apply)
        self.assertTrue(any("workspace contents" in action for action in plan.recommended_next_actions))

    def test_swiftpm_nested_app_project_is_plan_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            write(repo_root / "Package.swift", "// swift-tools-version: 5.10\n")
            (repo_root / "App" / "iOS" / "Fixture.xcodeproj").mkdir(parents=True)
            write(
                repo_root / "App" / "iOS" / "Fixture" / "FixtureApp.swift",
                "import SwiftUI\n@main\nstruct FixtureApp: App {}\n",
            )
            commit_all(repo_root)

            profile = adopt_existing.analyze_repository(repo_root)
            plan = adopt_existing.build_plan(profile)

        self.assertEqual(profile.xcode_projects, [])
        self.assertEqual(profile.nested_xcode_projects, ["App/iOS/Fixture.xcodeproj"])
        self.assertEqual(plan.mode, "swiftpm-app-assisted")
        self.assertEqual(plan.scenario, "swiftpm-nested-app-guided-decision")
        self.assertEqual(plan.status, "needs-confirmation")
        self.assertTrue(
            any("nested iOS app project" in action for action in plan.recommended_next_actions)
        )

    def test_xcode_project_without_detected_app_target_requires_confirmation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / "Fixture.xcodeproj").mkdir()
            write(
                repo_root / "Fixture" / "AppDelegate.swift",
                "import UIKit\nfinal class AppDelegate: UIResponder, UIApplicationDelegate {}\n",
            )
            commit_all(repo_root)

            profile = adopt_existing.analyze_repository(repo_root)
            plan = adopt_existing.build_plan(profile)

        self.assertEqual(profile.app_targets, [])
        self.assertEqual(plan.scenario, "xcode-uikit-baseline-adoption")
        self.assertEqual(plan.status, "needs-confirmation")
        self.assertFalse(plan.can_apply)
        self.assertTrue(any("Which app target" in question for question in plan.recommended_questions))

    def test_full_template_intent_without_app_target_is_unsupported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / "Fixture.xcodeproj").mkdir()
            write(
                repo_root / "Fixture" / "AppDelegate.swift",
                "import UIKit\nfinal class AppDelegate: UIResponder, UIApplicationDelegate {}\n",
            )
            commit_all(repo_root)

            profile = adopt_existing.analyze_repository(repo_root)
            plan = adopt_existing.build_plan(profile, "full-template-conversion")

        self.assertEqual(plan.scenario, "xcode-uikit-baseline-adoption")
        self.assertEqual(
            plan.goal_supported_level,
            "unsupported-without-new-migration-tooling",
        )
        self.assertFalse(plan.can_apply)
        self.assertEqual(plan.unsupported_reason, "No clear app target was detected for conversion.")

    def test_preserve_existing_workflow_with_fastlane_requires_translation_choice(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            make_ready_xcode_fixture(repo_root)
            write(repo_root / "fastlane" / "Fastfile", "lane :test do\nend\n")
            commit_all(repo_root)

            profile = adopt_existing.analyze_repository(repo_root)
            plan = adopt_existing.build_plan(profile, "preserve-existing-workflow")

        self.assertEqual(profile.existing_command_surfaces, ["fastlane"])
        self.assertEqual(plan.status, "needs-confirmation")
        self.assertEqual(plan.goal_supported_level, "safe-to-plan-now")
        self.assertFalse(plan.can_apply)
        self.assertTrue(
            any("translated into them" in question for question in plan.recommended_questions)
        )

    def test_direct_apply_respects_plan_permissions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            make_ready_xcode_fixture(repo_root)
            commit_all(repo_root)

            profile = adopt_existing.analyze_repository(repo_root)
            plan = adopt_existing.build_plan(profile, "baseline-comparison")

            with self.assertRaises(SystemExit):
                adopt_existing.apply_adoption(profile, plan, template_fixture())

    def test_swiftui_view_inside_uikit_lifecycle_stays_xcode_adopt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            make_ready_xcode_fixture(repo_root)
            write(
                repo_root / "Fixture" / "MarketingView.swift",
                "import SwiftUI\nstruct MarketingView: View { var body: some View { Text(\"Hi\") } }\n",
            )
            commit_all(repo_root)

            profile = adopt_existing.analyze_repository(repo_root)
            plan = adopt_existing.build_plan(profile)

        self.assertFalse(profile.has_swiftui_entry)
        self.assertTrue(profile.has_uikit_lifecycle)
        self.assertEqual(plan.scenario, "xcode-uikit-baseline-adoption")
        self.assertEqual(plan.status, "ready")

    def test_multi_target_xcode_repo_requires_target_choice(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / "Fixture.xcodeproj").mkdir()
            write(repo_root / "Alpha" / "Resources" / "Info.plist", "<plist />")
            write(repo_root / "Beta" / "Resources" / "Info.plist", "<plist />")
            write(
                repo_root / "Alpha" / "AppDelegate.swift",
                "import UIKit\nfinal class AppDelegate: UIResponder, UIApplicationDelegate {}\n",
            )
            commit_all(repo_root)

            profile = adopt_existing.analyze_repository(repo_root)
            plan = adopt_existing.build_plan(profile)

        self.assertEqual(profile.app_targets, ["Alpha", "Beta"])
        self.assertEqual(plan.status, "needs-confirmation")
        self.assertTrue(any("Which app target" in question for question in plan.recommended_questions))
        self.assertTrue(
            any("recommended questions" in action for action in plan.recommended_next_actions)
        )

    def test_apply_adds_missing_baseline_without_overwriting_existing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            make_ready_xcode_fixture(repo_root)
            write(repo_root / "README.md", "# Product README\n")
            commit_all(repo_root)

            profile = adopt_existing.analyze_repository(repo_root)
            plan = adopt_existing.build_plan(profile)
            result = adopt_existing.apply_adoption(profile, plan, template_fixture())

            makefile = (repo_root / "Makefile").read_text(encoding="utf-8")
            base_config = (repo_root / "Configuration" / "Base.xcconfig").read_text(
                encoding="utf-8"
            )
            readme = (repo_root / "README.md").read_text(encoding="utf-8")
            workspace = (
                repo_root / "Fixture.xcworkspace" / "contents.xcworkspacedata"
            ).read_text(encoding="utf-8")

        self.assertTrue(result.applied)
        self.assertIn("Makefile", result.created_files)
        self.assertIn("Fixture.xcworkspace/contents.xcworkspacedata", result.created_files)
        self.assertIn("Fixture.xctestplan", result.created_files)
        self.assertIn("Fixture.xcworkspace", makefile)
        self.assertIn("IOS_SCHEME      := Fixture", makefile)
        self.assertIn("group:Fixture.xcodeproj", workspace)
        self.assertIn("PRODUCT_BUNDLE_IDENTIFIER", base_config)
        self.assertEqual(readme, "# Product README\n")

    def test_dry_run_reports_changes_without_writing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            make_ready_xcode_fixture(repo_root)
            commit_all(repo_root)

            profile = adopt_existing.analyze_repository(repo_root)
            plan = adopt_existing.build_plan(profile)
            result = adopt_existing.apply_adoption(
                profile,
                plan,
                template_fixture(),
                dry_run=True,
            )
            makefile_exists = (repo_root / "Makefile").exists()
            workspace_exists = (repo_root / "Fixture.xcworkspace").exists()
            testplan_exists = (repo_root / "Fixture.xctestplan").exists()

        self.assertFalse(result.applied)
        self.assertTrue(result.dry_run)
        self.assertIn("Makefile", result.would_create_files)
        self.assertIn("Fixture.xcworkspace/contents.xcworkspacedata", result.would_create_files)
        self.assertIn("Fixture.xctestplan", result.would_create_files)
        self.assertFalse(makefile_exists)
        self.assertFalse(workspace_exists)
        self.assertFalse(testplan_exists)

    def test_apply_preserves_existing_makefile_and_devkit_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            make_ready_xcode_fixture(repo_root)
            write(repo_root / "Makefile", "custom:\n\t@echo custom\n")
            write(
                repo_root / "Resources" / "DevKit" / "scripts" / "run_xcodebuild.sh",
                "#!/usr/bin/env bash\necho custom\n",
            )
            commit_all(repo_root)

            profile = adopt_existing.analyze_repository(repo_root)
            plan = adopt_existing.build_plan(profile)
            result = adopt_existing.apply_adoption(profile, plan, template_fixture())

            makefile = (repo_root / "Makefile").read_text(encoding="utf-8")
            run_script = (
                repo_root / "Resources" / "DevKit" / "scripts" / "run_xcodebuild.sh"
            ).read_text(encoding="utf-8")

        self.assertTrue(result.applied)
        self.assertIn("Makefile", result.skipped_files)
        self.assertIn("Resources/DevKit/scripts/run_xcodebuild.sh", result.skipped_files)
        self.assertEqual(makefile, "custom:\n\t@echo custom\n")
        self.assertEqual(run_script, "#!/usr/bin/env bash\necho custom\n")

    def test_partial_devkit_reports_missing_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            make_ready_xcode_fixture(repo_root)
            write(
                repo_root / "Resources" / "DevKit" / "scripts" / "run_xcodebuild.sh",
                "#!/usr/bin/env bash\n",
            )
            commit_all(repo_root)

            profile = adopt_existing.analyze_repository(repo_root)
            plan = adopt_existing.build_plan(profile)

        self.assertFalse(profile.has_modern_uikit_devkit)
        self.assertIn(
            "Resources/DevKit/scripts/scan.license.sh",
            profile.devkit_missing_files,
        )
        self.assertTrue(any("scan.license.sh" in change for change in plan.proposed_changes))

    def test_json_payload_contains_schema_and_exit_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            make_ready_xcode_fixture(repo_root)
            commit_all(repo_root)

            profile = adopt_existing.analyze_repository(repo_root)
            plan = adopt_existing.build_plan(profile)
            payload = adopt_existing.build_json_payload(profile, plan, None)

        self.assertEqual(payload["schema_version"], "1.0")
        self.assertIn("0", payload["exit_code_contract"])
        self.assertIn("2", payload["exit_code_contract"])
        self.assertIn("profile", payload)
        self.assertIn("plan", payload)
        self.assertIn("adoption_intent", payload["plan"])
        self.assertTrue(payload["plan"]["can_apply"])
        self.assertTrue(payload["plan"]["can_dry_run"])
        self.assertFalse(payload["plan"]["requires_confirmation"])
        self.assertEqual(payload["plan"]["source_of_truth"], "xcode-project")
        self.assertIn("missing Makefile", payload["plan"]["write_scope"])
        self.assertIn("preserve_or_replace", payload["plan"])

    def test_cli_dry_run_unavailable_exits_with_contract_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            (repo_root / "Fixture.xcodeproj").mkdir()
            write(repo_root / "Fixture" / "Resources" / "Info.plist", "<plist />")
            write(
                repo_root / "Fixture" / "AppDelegate.swift",
                "import UIKit\nfinal class AppDelegate: UIResponder, UIApplicationDelegate {}\n",
            )
            commit_all(repo_root)
            write(repo_root / "README.md", "# Dirty fixture\n")

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--repo-path",
                    str(repo_root),
                    "--dry-run",
                    "--format",
                    "json",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 2)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["schema_version"], "1.0")
        self.assertEqual(payload["plan"]["status"], "blocked")

    def test_cli_apply_json_reports_created_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo_root = Path(tmp)
            make_ready_xcode_fixture(repo_root)
            commit_all(repo_root)

            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT_PATH),
                    "--repo-path",
                    str(repo_root),
                    "--apply",
                    "--format",
                    "json",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertTrue(payload["apply"]["applied"])
        self.assertIn("Makefile", payload["apply"]["created_files"])


if __name__ == "__main__":
    unittest.main()
