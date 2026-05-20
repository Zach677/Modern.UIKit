---
name: uikit-starter
description: Agent-native workflow for creating fresh UIKit apps from `Zach677/Modern.UIKit` or safely inspecting and adopting the Modern.UIKit baseline in existing iOS repos. Use from Codex, Claude Code, or another coding agent when the user wants a new UIKit app, an existing repo adoption review, or a SwiftUI/Tuist migration plan.
---

# UIKit Starter

## Agent Contract

This skill is the user-facing entrypoint. The scripts under `scripts/` are backend execution tools for the agent; do not present them as the primary user interface.

Primary responsibility:

- Create fresh UIKit apps when the user wants a new project.
- Inspect existing iOS repos before changing them.
- Choose fresh-create, adopt-existing, or migration-assisted mode from real repo state.
- Ask only the questions that block correctness.
- Preserve existing repo identity unless the user explicitly asks to change it.
- Report unsupported repo shapes honestly instead of forcing a migration.

## Workflow

1. Determine the target shape:
   - If the target GitHub repo does not exist, use fresh-create mode.
   - If the target GitHub repo exists but is not local, clone the existing repo first, then use adopt-existing mode.
   - If a local repo already exists, use adopt-existing mode.
   - If the repo uses SwiftUI or Tuist, use migration-assisted mode and treat existing repo guidance as binding until the user overrides it.
2. Fresh-create mode:
   - Collect only the missing inputs: internal project name, optional display name, repo name, bundle identifier when needed, optional Apple Developer Team ID, Swift language mode, and verification level.
   - Run the backend creation script.
   - Verify with the generated repo's own Makefile workflow.
3. Adopt-existing mode:
   - Run the backend analyzer before asking migration questions.
   - Read `Scenario`, `Adoption Intent`, `Goal Supported Level`, `Recommended Questions`, `Recommended Next Actions`, `Warnings`, `Blockers`, `Preserve Or Replace`, and `Forbidden Actions`.
   - Ask only the listed blocking questions.
   - Use dry-run before apply when additive baseline adoption is possible.
   - Apply only when the plan is `Status: ready` and `Mode: xcode-adopt`.
4. Migration-assisted mode:
   - Treat SwiftUI and Tuist repos as planning cases unless the user explicitly asks for an architecture migration.
   - Preserve Tuist as source of truth when repo guidance says so.
   - Map compatible baseline ideas into existing repo workflows instead of adding parallel build surfaces by default.
5. Final report:
   - State what mode and scenario were used.
   - State what changed or why nothing changed.
   - State validation commands actually run and their result.
   - State unsupported or deferred migration work clearly.

## Backend Tools

- `scripts/create_project.py`: creates a GitHub-template app, renames project-specific surfaces, rewrites generated docs, and runs verification when requested.
- `scripts/adopt_existing.py`: analyzes existing repos, emits adoption plans, previews additive changes, and applies the first safe UIKit/Xcode adoption slice.

Backend output contract:

- Use `--format json` when another agent or script needs stable output.
- Use `--intent` when the user's goal is clear: `baseline-comparison`, `preserve-existing-workflow`, `full-template-conversion`, or `architecture-migration`.
- JSON payloads include `schema_version`.
- Plans include `goal_supported_level`, `preserve_or_replace`, and `forbidden_actions`.
- Exit code `0`: analysis completed, or apply/dry-run completed when requested and available.
- Exit code `2`: apply/dry-run was requested, but the plan is not ready xcode-adopt.
- Dry-run must not write files.
- Apply must be additive and must not overwrite existing files.

## Scenario Guidance

- `xcode-uikit-baseline-adoption`: if the user wants adoption, preview then apply the additive baseline.
- `xcode-swiftui-entry-migration`: clarify whether UIKit is the new architecture direction before changing app entry code.
- `tuist-source-preserving-baseline`: keep Tuist as source of truth and port compatible ideas into existing commands.
- `tuist-swiftui-guided-decision`: respect SwiftUI-first and Tuist-source repo guidance until the user explicitly overrides it.
- `tuist-swiftui-full-uikit-conversion-requested`: stop at planning because full conversion needs dedicated migration tooling.
- `cocoapods-workspace-guided-decision`: preserve `Podfile`, workspace dependency flow, and existing validation commands by default.
- `workspace-only-guided-decision`: inspect workspace contents and identify the app project before applying starter files.
- `swiftpm-nested-app-guided-decision`: select the nested app project before applying any starter surface.
- `unsupported-repo-shape`: treat analyzer output as discovery only.

## Preservation Rules

Preserve by default:

- Git history and remotes.
- Existing bundle identifiers.
- Existing signing settings.
- Existing app source and resources.
- Product-specific documentation that does not conflict with the adopted workflow.
- Tuist manifests and existing `mise` commands when the repo already owns them.
- CocoaPods `Podfile` and workspace dependency flow when present.
- SwiftPM package-first boundaries and nested app project layout when present.

Do not automatically:

- Replace SwiftUI app entry with UIKit.
- Convert Tuist to Xcode or Xcode to Tuist.
- Add a parallel Makefile to a Tuist repo that already has repo-scoped commands.
- Delete `Podfile` or assume a nested Xcode project is the main app.
- Overwrite existing files during adoption.
- Commit LookInside or `LookInsideServer` wiring unless the user explicitly adopts shared debug tooling.

## Fresh-Create Inputs

- `project-name`: internal Xcode-facing name, identifier-safe, for example `ShelfMusic`.
- `display-name`: optional; when omitted, keep the display name exactly equal to `project-name`.
- `repo`: GitHub repository name.
- `bundle-id`: optional; defaults to a generated `com.example.*` value.
- `development-team`: optional; use only when the generated app should commit a shared signing identity.
- `swift-version`: `5.0` by default, `6.0` when stricter compiler diagnostics are desired.
- `verify`: `build` by default, `test` when stronger validation is worth the extra time.

## Notes

- The template repository is `Zach677/Modern.UIKit` unless the caller overrides it.
- Generated repos should not keep `skills/uikit-starter` or advertise template internals as app features.
- Generated repos expect agent-accessible `gh`, Xcode, `xcbeautify`, `npx`/Prettier, and `swiftformat` for the full workflow.
- If the user wants this skill to be auto-discoverable on the current machine, install it under the agent runtime's skill directory, preferably via symlink to the repo copy.
