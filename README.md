# Modern.UIKit

A GitHub template repository for starting new UIKit iOS apps with a small, opinionated engineering baseline.

![Platform](https://img.shields.io/badge/platform-iOS%2017%2B%20%7C%20Mac%20Catalyst-blue)
![Swift](https://img.shields.io/badge/Swift-5.0%20default%20%7C%206.0%20optional-orange)
![Xcode](https://img.shields.io/badge/Xcode-iOS%2017%20SDK%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

It is intentionally not a framework-heavy architecture preset. The goal is simpler: keep the repetitive setup decisions that usually get re-done poorly, and leave the real app architecture free to grow from there.

## Requirements

- iOS 17.0 or later
- Xcode with iOS 17 SDK and Swift Testing support
- Swift 5.0 language mode by default, with Swift 6.0 available when scaffolding a new project

Maintainer validation currently runs with Xcode 26.4.1, Build 17E202.

## What You Get

Core:

- Programmatic UIKit startup through `main.swift`
- No main storyboard, only `LaunchScreen.storyboard`
- A dedicated `Application/` layer for lifecycle and bootstrap
- A root `Interface/Root/` shell ready to become the first real screen
- Shared `xcconfig` signing, bundle, and version files instead of hardcoded personal values
- A small hosted unit test target, `ModernUIKit.xctestplan`, and `make test`
- A `Makefile` + log-aware DevKit scripts as uniform build/test entry points

Optional extras:

- A reusable scaffold skill, `uikit-starter`, for creating fresh apps from this template
- LookInside inspection guidance for local debug workflows
- `AGENTS.md` / `CLAUDE.md` files for agent-driven workflows

## Recommended Ways To Start

### 1. Use the skill

This is the best path when you want AI to create a fresh project end-to-end instead of manually cloning and renaming files.

Install the skill:

```bash
npx skills add Zach677/Modern.UIKit --skill uikit-starter -g -y
```

What it does:

- creates a new repo from the GitHub template
- clones it locally
- renames the Xcode project, workspace, schemes, xctestplan, source folders, and test target
- updates bundle identifiers and display name
- lets you choose Swift 5.0 or Swift 6.0 language mode
- runs `make build` or `make test` for verification

### 2. Use the GitHub template directly

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

## Local Signing Overrides

By default the template uses a placeholder bundle identifier:

```text
com.example.$(PRODUCT_NAME:rfc1034identifier)
```

`Configuration/Base.xcconfig` is intentionally narrow. It includes `Configuration/Version.xcconfig`, owns signing/provisioning and the app bundle identifier, and leaves target/platform settings such as `PRODUCT_NAME`, `SWIFT_VERSION`, deployment targets, supported platforms, and Info.plist wiring in the Xcode project.

If you need local signing values without committing them, create one or more of:

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
