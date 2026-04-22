# No-StoryBoard

`No-StoryBoard` is a small UIKit starter for new code-driven iOS projects.

It keeps the app shape intentionally light:

- `No-UIKit/Application/` contains lifecycle and bootstrap types
- `No-UIKit/Interface/Root/` contains the first root screen
- `Configuration/*.xcconfig` owns reusable build settings
- `Makefile` provides consistent shell entry points for local builds
- `AGENTS.md` documents the template's engineering contract for future agents
- `No-StoryBoardTests/` provides a minimal hosted unit test target

## Why this template exists

This starter is meant to preserve a few decisions that are easy to repeat poorly:

- no main storyboard
- programmatic app startup through `main.swift`
- a dedicated app context for future dependency wiring
- a root controller folder that can grow into a real app shell
- shared Xcode configuration files instead of hardcoded personal settings

It is not trying to be a full architecture framework.

## Agent Guidance

The template includes an [`AGENTS.md`](./AGENTS.md) file with the intended project shape, placement rules, and tooling defaults.

`CLAUDE.md` is a symlink to `AGENTS.md` so both agent conventions resolve to the same source of truth.

## Structure

```text
No-UIKit/
  Application/
  Interface/Root/
  Assets.xcassets/
  Base.lproj/
  Info.plist
No-StoryBoardTests/
Configuration/
  Base.xcconfig
  Development.xcconfig
  Release.xcconfig
  Test.xcconfig
  Version.xcconfig
scripts/
  resolve_test_destination.py
Makefile
```

## Local overrides

By default the template uses a placeholder bundle identifier:

```text
com.example.$(PRODUCT_NAME:rfc1034identifier)
```

If you want local signing overrides without committing them, create one or more of:

- `Configuration/Developer.xcconfig`
- `Configuration/DevelopmentDeveloper.xcconfig`
- `Configuration/DeveloperRelease.xcconfig`

Typical overrides look like:

```xcconfig
DEVELOPMENT_TEAM = YOURTEAMID
PRODUCT_BUNDLE_IDENTIFIER = com.yourcompany.yourapp
```

## Build

```bash
make build
make build-sim
make build-device
make test
make clean
```

`make build` defaults to the simulator path so the template can build cleanly before signing is configured.

`make test` automatically picks an available iPhone simulator on the current machine. You can still override it manually:

```bash
TEST_DESTINATION='platform=iOS Simulator,name=iPhone 17' make test
```
