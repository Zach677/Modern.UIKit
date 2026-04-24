# Modern.UIKit

`Modern.UIKit` is a GitHub template repository for starting new UIKit iOS apps with a small but opinionated engineering baseline.

It is intentionally not a framework-heavy architecture preset. The goal is simpler: keep the repetitive setup decisions that usually get re-done poorly, and leave the real app architecture free to grow from there.

## What You Get

- Programmatic UIKit startup through `main.swift`
- No main storyboard, only `LaunchScreen.storyboard`
- A dedicated `Application/` layer for lifecycle and bootstrap
- A root `Interface/Root/` shell ready to become the first real screen
- Shared `xcconfig` build settings instead of hardcoded personal values
- A small hosted unit test target, `ModernUIKit.xctestplan`, and `make test`
- Optional LookInside inspection guidance for local debug workflows
- A reusable scaffold skill, `uikit-starter`, for creating fresh apps from this template
- Optional `AGENTS.md` / `CLAUDE.md` files for agent-driven workflows

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
- runs `make build` or `make test` for verification

### 2. Use the GitHub template directly

If you do not need the skill workflow, use the template repo directly:

```bash
gh repo create Zach677/shelf-music \
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
- App-bundled resources follow the MuseAmp pattern and live under `ModernUIKit/Resources/`, not beside source files at the app root.
- Test target settings follow the MuseAmp pattern too: they live in target build settings inside `project.pbxproj`, not in a separate test-only xcconfig file.

## Local Development

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

- `make build` now follows the MuseAmp idea: build the primary app paths you actually care about, here iOS Simulator plus Mac Catalyst.
- `make test` / `make test-unit` run on the Mac Catalyst destination instead of relying on simulator discovery.
- `Resources/DevKit/scripts/run_xcodebuild.sh` treats the build log as the source of truth, so `make` stops on real build and test failures even when `xcodebuild` output is misleading.
- `ModernUIKit.xcworkspace` is the default Xcode entrypoint, not just the `.xcodeproj`.

Tooling expectations:

- `xcbeautify` should be available on `PATH` for the Xcode and package-resolution workflows.
- `prettier` should be available for DevKit formatting flows; the repository invokes it through `npx --yes prettier ...`.

## Local Signing Overrides

By default the template uses a placeholder bundle identifier:

```text
com.example.$(PRODUCT_NAME:rfc1034identifier)
```

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

The sample app tests now live under `ModernUIKitTests/Application/` and are written in the modern Swift Testing style, which gives you better test discovery inside Xcode and makes the `ModernUIKit.xctestplan` view more useful as the project grows.

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

The template now ships with the same DevKit script categories that make MuseAmp useful:

- `run_xcodebuild.sh` for log-aware build and test execution
- `strip_stale_xcstrings.py` and `validate_xcstrings.py` for string catalog hygiene
- `tidy_workspace_schemes.py` for keeping the workspace scheme list sane
- `scan.license.sh` for package resolution and open source license aggregation

These are lightweight template adaptations, not product-specific policy files.
