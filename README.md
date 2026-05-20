# Modern.UIKit

> Start or adopt a programmatic UIKit app with a small engineering baseline: workspace-first Xcode entrypoints, Makefile-driven build/test flows, starter-safe signing config, and agent-readable project rules.

![Platform](https://img.shields.io/badge/platform-iOS%2017%2B%20%7C%20Mac%20Catalyst-blue)
![Swift](https://img.shields.io/badge/Swift-5.0%20default%20%7C%206.0%20optional-orange)
![Xcode](https://img.shields.io/badge/Xcode-iOS%2017%20SDK%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Modern.UIKit is intentionally not a full app architecture or framework preset. It keeps the repetitive setup decisions that are expensive to redo later, then leaves product architecture free to grow from the real app.

Use it in two situations:

- Create a fresh UIKit app from the GitHub template.
- Inspect an existing iOS repo and adopt the starter baseline without discarding repo history, bundle identifiers, signing settings, or app source.

## Quick Start

### 1. Install the skill

```bash
npx skills add Zach677/Modern.UIKit --skill uikit-starter -g -y
```

### 2. Create a fresh app

Ask your agent to use `$uikit-starter`, or run the scaffold script from this repo:

```bash
python3 skills/uikit-starter/scripts/create_project.py \
  --project-name ShelfMusic \
  --display-name "Shelf Music" \
  --repo Zach677/shelf-music \
  --bundle-id com.zach.shelfmusic \
  --swift-version 6.0 \
  --visibility private \
  --parent-dir ~/Developer \
  --verify build
```

### 3. Adopt an existing app

Start with a read-only plan:

```bash
python3 skills/uikit-starter/scripts/adopt_existing.py \
  --repo-path /path/to/existing-app
```

Preview the additive changes without writing files:

```bash
python3 skills/uikit-starter/scripts/adopt_existing.py \
  --repo-path /path/to/existing-app \
  --dry-run
```

Apply the conservative first slice only when the plan says `Status: ready`:

```bash
python3 skills/uikit-starter/scripts/adopt_existing.py \
  --repo-path /path/to/existing-app \
  --apply
```

The first adoption slice supports clean UIKit/Xcode repos. SwiftUI and Tuist repos are detected as migration-assisted flows, so an agent can ask the few decisions that actually matter before changing code.

## Adoption Scenarios

Existing repos are not all trying to reach the same end state. The analyzer reports a `Scenario` and `Recommended Next Actions` so an agent can choose the least disruptive path.

| Scenario                           | Typical user goal                                                    | Default behavior                                                               |
| ---------------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `xcode-uikit-baseline-adoption`    | Bring a UIKit/Xcode repo onto the starter baseline                   | Add missing baseline files with `--apply`, without overwriting existing files  |
| `xcode-swiftui-entry-migration`    | Compare the starter or intentionally move a SwiftUI app toward UIKit | Ask whether UIKit is an architecture change before touching app entry code     |
| `tuist-source-preserving-baseline` | Reuse baseline ideas while keeping Tuist                             | Keep Tuist manifests as source of truth and map ideas into existing commands   |
| `tuist-swiftui-guided-decision`    | Evaluate a SwiftUI/Tuist app like SubPanda                           | Treat SwiftUI/Tuist guidance as binding until the user explicitly overrides it |
| `unsupported-repo-shape`           | Inspect an uncommon repo shape                                       | Use the output as discovery only; add support before applying changes          |

## Adoption Support Contract

Supported today:

- Fresh UIKit project creation from the GitHub template through `uikit-starter`.
- Read-only analysis for existing iOS repos.
- Additive baseline adoption for clean, git-backed UIKit/Xcode repos with a single clear app target.
- Migration-assisted planning for SwiftUI and Tuist repos.
- JSON output with `schema_version: "1.0"` for agent and script consumption.

Not yet supported as automatic migration:

- Arbitrary SwiftUI app entry replacement with UIKit.
- Tuist-to-Xcode or Xcode-to-Tuist source-of-truth conversion.
- Complex multi-workspace, multi-project, CocoaPods, or heavily customized build setups.
- Automatically wiring every generated `.xctestplan` into every shared scheme.
- Guaranteeing build success on another machine without matching Xcode, signing, GitHub, and local tooling.

Exit codes:

- `0`: analysis completed; apply or dry-run completed when requested and available.
- `2`: `--apply` or `--dry-run` was requested, but the plan is not `Status: ready` / `Mode: xcode-adopt`.

## What You Get

Core app baseline:

- Programmatic UIKit startup through `main.swift`
- No main storyboard, only `LaunchScreen.storyboard`
- A dedicated `Application/` layer for lifecycle and bootstrap
- A root `Interface/Root/` shell ready to become the first real screen
- Shared `xcconfig` signing, bundle, and version files instead of hardcoded personal values
- A small hosted unit test target, `ModernUIKit.xctestplan`, and `make test`
- A `Makefile` plus log-aware DevKit scripts as uniform build/test entry points

Agent workflow:

- `uikit-starter` chooses fresh-create, adopt-existing, or migration-assisted mode from repo state.
- Existing repo adoption preserves git history, remotes, bundle identifiers, signing settings, app source, and resources by default.
- The adoption analyzer asks only blocking migration questions, such as which target is primary or whether Tuist should remain the source of truth.
- Tuist repos keep their manifest and existing `mise` commands as the default source of truth when repo guidance already says so.
- Swift 5.0 is the default language mode; Swift 6.0 is available for fresh projects.

## Requirements

- iOS 17.0 or later
- Xcode with iOS 17 SDK and Swift Testing support
- Swift 5.0 language mode by default, with Swift 6.0 available when scaffolding a new project

Maintainer validation currently runs with Xcode 26.4.1, Build 17E202.

## Manual Template Path

If you do not need the skill workflow, use the template repo directly:

```bash
gh repo create <your-username>/<your-new-app> \
  --private \
  --template Zach677/Modern.UIKit \
  --clone
```

This gives you the raw template checkout. If you use this path, you still need to rename project-specific placeholders yourself unless you bring in the skill or your own automation.

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
- If you clone the template manually, those placeholder names are expected until you rename them.
- The Xcode Tests view comes from `ModernUIKit.xctestplan`, so the scheme has an explicit test plan instead of ad-hoc test target selection.
- App-bundled resources live under `ModernUIKit/Resources/`, not beside source files at the app root.
- Test target settings live in target build settings inside `project.pbxproj`, not in a separate test-only xcconfig file.

## Local Development

Prerequisites:

- Xcode with Swift Testing and iOS 17 SDK support (see [Requirements](#requirements)).
- GitHub CLI (`gh`) for template and skill workflows.
- Node.js with `npx`, plus Prettier for formatting DevKit output.
- `xcbeautify` for readable Xcode logs.
- `swiftformat` for `make format` and `make format-lint`.

Recommended setup:

```bash
brew install gh node xcbeautify swiftformat
npm install -g prettier
```

Build and test through the top-level `Makefile`:

```bash
make build
make build-ios
make build-sim
make build-device
make build-catalyst
make run-ios
make run-sim
make test
make test-unit
make format
make format-lint
make package-resolve
make scan-license
make strip-xcstrings
make validate-xcstrings
make tidy-schemes
make chore
make clean
```

Defaults:

- `make build` covers the primary app paths you actually care about: iOS Simulator plus Mac Catalyst.
- `make run-ios` / `make run-sim` build the simulator app, install it on the booted simulator, and launch it.
- `make test` / `make test-unit` run on the Mac Catalyst destination instead of relying on simulator discovery.
- `Resources/DevKit/scripts/run_xcodebuild.sh` treats the build log as the source of truth, so `make` stops on real build and test failures even when `xcodebuild` output is misleading.
- `ModernUIKit.xcworkspace` is the default Xcode entrypoint.

Tooling expectations:

- `xcbeautify` should be available on `PATH` for the Xcode and package-resolution workflows.
- `prettier` should be available for DevKit formatting flows; the repository invokes it through `npx --yes prettier ...`.

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

If the Homebrew tap version is fresh enough for your use case, `brew install Zach677/star/lookinside-cli` is a shorter CLI install path. Building from `LookInsideApp/LookInsideServer` is preferred when you want the CLI and embeddable runtime to match the current upstream checkout.

A target app only appears in `lookinside list` after it runs `LookinServer` or a compatible injected runtime. For this starter, keep that setup developer-local or debug-only unless the project explicitly adopts LookInside as shared tooling.

Common CLI commands after a debuggable target is running:

```bash
lookinside list --format json
lookinside inspect --target <id> --format json
lookinside hierarchy --target <id> --output /tmp/app-hierarchy.txt
lookinside export --target <id> --output /tmp/app.lookinside
```

When asking a coding agent to configure LookInside, point it at this section, `AGENTS.md`, and the `lookinside-cli` skill. The agent should install or verify the local app and CLI, then report clearly if no target is discoverable because the app has not opted into a debug server.

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
