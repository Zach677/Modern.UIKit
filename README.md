# Modern.UIKit

`Modern.UIKit` is a GitHub template repository for starting new UIKit iOS apps with a small but opinionated engineering baseline.

It is intentionally not a framework-heavy architecture preset. The goal is simpler: keep the repetitive setup decisions that usually get re-done poorly, and leave the real app architecture free to grow from there.

## What You Get

- Programmatic UIKit startup through `main.swift`
- No main storyboard, only `LaunchScreen.storyboard`
- A dedicated `Application/` layer for lifecycle and bootstrap
- A root `Interface/Root/` shell ready to become the first real screen
- Shared `xcconfig` build settings instead of hardcoded personal values
- A small hosted unit test target with `make test`
- A reusable scaffold skill, `uikit-starter`, for creating fresh apps from this template
- Optional `AGENTS.md` / `CLAUDE.md` files for agent-driven workflows

## Recommended Ways To Start

### 1. Use the skill

This is the best path when you want AI to create a fresh project end-to-end instead of manually cloning and renaming files.

Install the skill:

```bash
npx skills add Zach677/Modern.UIKit --skill uikit-starter
```

Then use it with your agent:

```text
Use $uikit-starter to create a new app:
project name ShelfMusic,
display name Shelf Music,
repo Zach677/shelf-music,
bundle id com.zach.shelfmusic,
visibility private,
verify test.
```

What it does:

- creates a new repo from the GitHub template
- clones it locally
- renames the Xcode project, schemes, targets, source folders, and test target
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
  Assets.xcassets/
  Base.lproj/
  Info.plist
ModernUIKitTests/
Configuration/
  Base.xcconfig
  Development.xcconfig
  Release.xcconfig
  Test.xcconfig
  Version.xcconfig
skills/
  uikit-starter/
scripts/
  resolve_test_destination.py
Makefile
AGENTS.md
CLAUDE.md -> AGENTS.md
```

Notes:

- The checked-in template still uses placeholder on-disk names such as `ModernUIKit` and `ModernUIKitTests`.
- The `uikit-starter` skill rewrites those placeholders when it scaffolds a real project.
- If you clone the template manually, those placeholder names are expected until you rename them.

## Local Development

Build and test through the top-level `Makefile`:

```bash
make build
make build-sim
make build-device
make test
make clean
```

Defaults:

- `make build` targets the simulator path so the repo builds before signing is configured.
- `make test` automatically resolves an available iPhone simulator on the current machine.

Manual simulator override:

```bash
TEST_DESTINATION='platform=iOS Simulator,name=iPhone 17' make test
```

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
