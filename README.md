# Modern.UIKit

> Agent-native UIKit starter and adoption workflow for Codex, Claude Code, and other coding agents.

![Platform](https://img.shields.io/badge/platform-iOS%2017%2B%20%7C%20Mac%20Catalyst-blue)
![Swift](https://img.shields.io/badge/Swift-5.0%20default%20%7C%206.0%20optional-orange)
![Xcode](https://img.shields.io/badge/Xcode-iOS%2017%20SDK%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Modern.UIKit is not a manual CLI product and not a full app architecture preset. It is a project baseline plus an agent workflow: agents can create fresh UIKit apps, inspect existing iOS repos, and choose a safe adoption path without forcing every repo toward the same end state.

Use this repo when you want an agent to:

- Create a fresh programmatic UIKit app from a maintained starter baseline.
- Inspect an existing iOS repo before changing it.
- Adopt baseline engineering surfaces only when the repo shape and user goal make that safe.
- Treat SwiftUI and Tuist projects as guided migration scenarios, not automatic rewrites.

## Agent Entry

The intended entrypoint is the `uikit-starter` skill. In Codex, Claude Code, or another skill-aware coding agent, ask the agent to use `$uikit-starter` for either a new app or an existing repo adoption review.

Install the skill where your agent runtime can see it:

```bash
npx skills add Zach677/Modern.UIKit --skill uikit-starter -g -y
```

After that, users should describe the desired outcome in natural language. The agent should do the repo inspection, choose the mode, ask only blocking questions, run the backend scripts, and report the result.

Good agent prompts look like:

- `Use $uikit-starter to create a new private UIKit app repo named ShelfMusic.`
- `Use $uikit-starter to inspect this repo and tell me whether it can adopt Modern.UIKit safely.`
- `Use $uikit-starter on this SwiftUI/Tuist repo, but do not change files until you explain the migration path.`
- `Use $uikit-starter to preserve this repo's Tuist/mise workflow and only borrow compatible Modern.UIKit practices.`
- `Use $uikit-starter to evaluate a full UIKit template conversion, but stop if the current tooling cannot do that safely.`

## Agent Workflow

`uikit-starter` should follow this order:

1. Determine whether the target is a fresh repo, an existing GitHub repo, or an existing local checkout.
2. For fresh apps, create the GitHub template repo and let the backend rename project-specific surfaces.
3. For existing repos, run the adoption analyzer first and read its `Scenario`, `Recommended Questions`, and `Recommended Next Actions`.
4. Ask only questions that block correctness; preserve values that can be inferred from the repo.
5. Apply changes only when the plan is explicitly safe for additive adoption.
6. Verify through the repo's own workflow and report unsupported cases without pretending they were migrated.

The backend scripts exist for agent reliability. They provide deterministic file edits, JSON output, exit codes, and tests. They are not the primary user interface.

## What Agents Can Do

- Fresh UIKit project creation from the GitHub template.
- Project renaming for app source, tests, workspace, scheme, bundle identifiers, display name, README, and starter docs.
- Existing repo analysis without writing files.
- Additive baseline adoption for clean UIKit/Xcode repos with one clear app target.
- Scenario-guided planning for SwiftUI, Tuist, CocoaPods workspace, and SwiftPM package-first repos.
- Intent-aware output for baseline comparison, preserving existing workflows, full template conversion, and architecture migration.
- Stable JSON output with `schema_version: "1.0"` for multi-agent or scripted orchestration.

## Adoption Scenarios

Existing repos are not all trying to reach the same end state. The analyzer reports a `Scenario` and `Recommended Next Actions` so the agent can choose the least disruptive path.

| Scenario                                        | Typical user goal                                                    | Agent behavior                                                                 |
| ----------------------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `xcode-uikit-baseline-adoption`                 | Bring a UIKit/Xcode repo onto the starter baseline                   | Preview/apply additive baseline files only when the plan is ready              |
| `xcode-swiftui-entry-migration`                 | Compare the starter or intentionally move a SwiftUI app toward UIKit | Ask whether UIKit is an architecture change before touching app entry code     |
| `tuist-source-preserving-baseline`              | Reuse baseline ideas while keeping Tuist                             | Keep Tuist manifests as source of truth and map ideas into existing commands   |
| `tuist-swiftui-guided-decision`                 | Evaluate a SwiftUI/Tuist app like SubPanda                           | Treat SwiftUI/Tuist guidance as binding until the user explicitly overrides it |
| `tuist-swiftui-full-uikit-conversion-requested` | Fully replace a SwiftUI/Tuist app with the UIKit template shape      | Stop at planning; require dedicated migration tooling before edits             |
| `cocoapods-workspace-guided-decision`           | Reuse starter ideas in a CocoaPods workspace app                     | Preserve `Podfile` and workspace dependency flow by default                    |
| `swiftpm-nested-app-guided-decision`            | Evaluate package-first repos with nested iOS app projects            | Select the app project before any starter adoption                             |
| `unsupported-repo-shape`                        | Inspect an uncommon repo shape                                       | Use the output as discovery only; add support before applying changes          |

The analyzer also reports `adoption_intent`, `goal_supported_level`, `preserve_or_replace`, and `forbidden_actions`. Agents should treat those fields as the decision contract, especially when the user's goal is not a simple UIKit/Xcode baseline adoption.

## Safety Contract

Agents may promise these behaviors today:

- Fresh UIKit app creation through `uikit-starter`.
- Read-only analysis for existing iOS repos.
- Additive baseline adoption for clean, git-backed UIKit/Xcode repos with one clear app target.
- Migration-assisted planning for SwiftUI, Tuist, CocoaPods workspace, and SwiftPM package-first repos.
- Preservation of git history, remotes, bundle identifiers, signing settings, app source, resources, and product-specific docs by default.

Agents must not promise these as automatic migration:

- Arbitrary SwiftUI app entry replacement with UIKit.
- Tuist-to-Xcode or Xcode-to-Tuist source-of-truth conversion.
- Complex multi-workspace, multi-project, CocoaPods, SwiftPM package-first, or heavily customized build setup migration.
- Automatically wiring every generated `.xctestplan` into every shared scheme.
- Guaranteed build success on another machine without matching Xcode, signing, GitHub, and local tooling.

## Backend Contract

The skill is backed by two scripts:

- `skills/uikit-starter/scripts/create_project.py` creates fresh GitHub-template apps and rewrites starter placeholders.
- `skills/uikit-starter/scripts/adopt_existing.py` analyzes existing repos, emits adoption plans, previews additive changes, and applies the first safe UIKit/Xcode adoption slice.

The adoption backend contract is intentionally machine-readable:

- JSON payloads include `schema_version: "1.0"`.
- Plans include `adoption_intent`, `goal_supported_level`, `preserve_or_replace`, and `forbidden_actions`.
- Exit code `0` means analysis completed, or apply/dry-run completed when requested and available.
- Exit code `2` means apply/dry-run was requested, but the plan is not `Status: ready` / `Mode: xcode-adopt`.
- Dry-run must report planned file creation/skips without writing files.
- Apply must be additive and must not overwrite existing files.

## What The Baseline Contains

Core app baseline:

- Programmatic UIKit startup through `main.swift`.
- No main storyboard, only `LaunchScreen.storyboard`.
- A dedicated `Application/` layer for lifecycle and bootstrap.
- A root `Interface/Root/` shell ready to become the first real screen.
- Shared `xcconfig` signing, bundle, and version files instead of hardcoded personal values.
- A small hosted unit test target, `ModernUIKit.xctestplan`, and `make test`.
- A `Makefile` plus log-aware DevKit scripts as uniform build/test entry points.

## Requirements

- iOS 17.0 or later.
- Xcode with iOS 17 SDK and Swift Testing support.
- Swift 5.0 language mode by default, with Swift 6.0 available for generated apps.

Maintainer validation currently runs with Xcode 26.4.1, Build 17E202.

## Why This Exists

This repo is meant to preserve a few high-value decisions:

- UIKit stays code-driven from day one
- app lifecycle and UI composition are separated early
- config and signing overrides do not leak personal machine state into git
- build and test entry points are uniform

That is enough to make a new UIKit app feel engineered from the start, without forcing a full product architecture too early.

## Swift Language Mode

The checked-in template defaults to `SWIFT_VERSION = 5.0` for broad compatibility. When creating a new project through `uikit-starter`, choose `--swift-version 5.0` or `--swift-version 6.0` based on the app's tolerance for newer compiler diagnostics.

Swift 6.0 is a good choice when the project wants stricter language checks from the start. Swift 5.0 remains the conservative default for teams that want the widest Xcode compatibility and fewer migration decisions on day one.

## Repository Layout

```text
ModernUIKit/
  Application/
  Interface/Root/
  Resources/
    Assets.xcassets/
    Info.plist
    LaunchScreen.storyboard
    Localizable.xcstrings
    OpenSourceLicenses.md
ModernUIKitTests/
Configuration/
  Base.xcconfig
  Development.xcconfig
  Release.xcconfig
  Version.xcconfig
Resources/
  DevKit/scripts/
ModernUIKit.xctestplan
skills/
  uikit-starter/
Makefile
AGENTS.md
CLAUDE.md -> AGENTS.md
```

Notes:

- The checked-in template still uses placeholder on-disk names such as `ModernUIKit` and `ModernUIKitTests`.
- The `uikit-starter` skill rewrites those placeholders when it scaffolds a real project.
- The Xcode Tests view comes from `ModernUIKit.xctestplan`, so the scheme has an explicit test plan instead of ad-hoc test target selection.
- App-bundled resources live under `ModernUIKit/Resources/`, not beside source files at the app root.
- Test target settings live in target build settings inside `project.pbxproj`, not in a separate test-only xcconfig file.

## Agent Runtime Expectations

Agents working with this repo or a generated app should have access to:

- Xcode with Swift Testing and iOS 17 SDK support (see [Requirements](#requirements)).
- GitHub CLI (`gh`) for template and skill workflows.
- Node.js with `npx`, plus Prettier for formatting DevKit output.
- `xcbeautify` for readable Xcode logs.
- `swiftformat` for formatting checks.

Generated apps expose their build, run, test, formatting, package-resolution, license, localization, and scheme-tidying workflows through the top-level `Makefile`. Agents should use those repository-owned targets instead of ad-hoc `xcodebuild` commands.

Validation defaults:

- Primary build coverage is iOS Simulator plus Mac Catalyst.
- Simulator launch flows build, install, and launch on the booted simulator.
- Unit tests run on the Mac Catalyst destination by default.
- `Resources/DevKit/scripts/run_xcodebuild.sh` treats the build log as the source of truth, so automation fails on real build and test failures even when `xcodebuild` output is misleading.
- `ModernUIKit.xcworkspace` is the default Xcode entrypoint.

## Signing Configuration

By default the template is team-neutral and uses a placeholder bundle identifier:

```text
com.example.$(PRODUCT_NAME:rfc1034identifier)
```

`Configuration/Base.xcconfig` is intentionally narrow. It includes `Configuration/Version.xcconfig`, owns signing/provisioning and the app bundle identifier, and leaves target/platform settings such as `PRODUCT_NAME`, `SWIFT_VERSION`, deployment targets, supported platforms, and Info.plist wiring in the Xcode project.

For a generated personal or single-team app, commit the shared Apple Developer Team ID in the generated app's `Configuration/Base.xcconfig` so Xcode's Signing & Capabilities view resolves the Team from build settings. The `uikit-starter` script writes that value when `--development-team` is passed.

If a generated project should stay team-neutral, or if you need local signing values without committing them, create one or more of:

- `Configuration/Developer.xcconfig`
- `Configuration/DevelopmentDeveloper.xcconfig`
- `Configuration/DeveloperRelease.xcconfig`

Typical overrides:

```xcconfig
DEVELOPMENT_TEAM = YOURTEAMID
PRODUCT_BUNDLE_IDENTIFIER = com.yourcompany.yourapp
```

## Testing Notes

The sample app tests live under `ModernUIKitTests/Application/` and are written in the modern Swift Testing style, which gives you better test discovery inside Xcode and makes the `ModernUIKit.xctestplan` view more useful as the project grows.

## Optional Debug Inspection

LookInside is optional local developer tooling. The template does not link LookInside or `LookInsideServer` by default, so the checked-in app target stays free of debug-inspection dependencies.

When a user asks an agent to configure LookInside, the agent should follow `AGENTS.md` and the `lookinside-cli` skill, verify the local app and CLI, and avoid committing app-side `LookInsideServer` wiring unless the project explicitly adopts shared debug tooling.

A target app only appears after it runs `LookinServer` or a compatible injected runtime. For this starter, keep that setup developer-local or debug-only unless the project explicitly adopts LookInside as shared tooling.

## DevKit Scripts

The template ships with a small set of DevKit scripts:

- `run_xcodebuild.sh` for log-aware build and test execution
- `strip_stale_xcstrings.py` and `validate_xcstrings.py` for string catalog hygiene
- `tidy_workspace_schemes.py` for keeping the workspace scheme list sane
- `scan.license.sh` for package resolution and open source license aggregation

These are lightweight template utilities, not product-specific policy files.

## Acknowledgements

Modern.UIKit is inspired by the engineering discipline in [MuseAmp](https://github.com/Lakr233/MuseAmp), especially its workspace-first Xcode workflow, DevKit-style maintenance scripts, test-plan setup, and log-aware build/test automation. This template keeps those ideas lightweight for new UIKit apps and does not copy MuseAmp's product code or app-specific architecture.

## License

Modern.UIKit is licensed under the MIT License. See `LICENSE` for details.

---

© 2025-2026 @Zach677. Released under the MIT License.
