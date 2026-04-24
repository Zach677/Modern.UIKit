# Project Overview

## App Shape

- This is a pure UIKit iOS starter with programmatic setup.
- Keep the entry path as `ModernUIKit/Application/main.swift` -> `AppDelegate.swift` -> `SceneDelegate.swift`.
- `SceneDelegate` owns window creation, bootstraps the shared `AppPreferences`, and installs the root navigation shell.
- `Interface/Root/RootViewController.swift` is the first screen and the seed of the future app shell.
- Do not introduce SwiftUI into the starter by default. If a real project later chooses SwiftUI, that should be an explicit project decision rather than template drift.
- LookInside is optional developer tooling. Do not link `LookInsideServer` in the committed app target by default; if a real project adopts it, keep the setup debug-only and out of feature code.

## Structure Rules

### Top Level

- `ModernUIKit/` contains the app target source and resources.
- `ModernUIKit.xcworkspace/` is the default Xcode entrypoint for the repository.
- `Configuration/` contains shared Xcode build configuration files (`Base.xcconfig`, `Development.xcconfig`, `Release.xcconfig`, `Version.xcconfig`).
- `Resources/DevKit/scripts/` contains reusable maintenance scripts for build/test log handling, scheme tidying, xcstrings hygiene, and license scanning.
- `Makefile` is the default shell entry point for local build workflows.
- `README.md` explains the template contract and local override flow.
- `ModernUIKitTests/` contains the hosted unit tests for the app target.

### Application Layer

- `Application/` contains only lifecycle, bootstrap, and app-wide configuration types.
- Keep `AppDelegate.swift`, `SceneDelegate.swift`, `AppPreferences.swift`, and `AppPreferences+Bootstrap.swift` in `Application/`.
- Do not move feature logic, view composition, or network/database code into `Application/`.

### Interface Layer

- `Interface/Root/` contains the root shell and the first view controller shown after boot.
- Future shared UIKit infrastructure can grow under `Interface/Common/`.
- Future reusable feature primitives can grow under `Interface/Collections/` or similarly scoped folders if the project reaches that size.
- Feature-specific UI should live under dedicated feature folders inside `Interface/`, not inside `Application/`.

### Backend Layer

- If the starter grows into a real app, create a top-level `Backend/` folder inside `ModernUIKit/` for domain services, persistence, API clients, state ownership, and cross-feature runtime logic.
- Keep UI state rendering in `Interface/`, but keep state ownership in `Backend/`.

### Resources Layer

- `ModernUIKit/Resources/` contains app-bundled resources that ship with the target, such as `Assets.xcassets`, `Info.plist`, `LaunchScreen.storyboard`, `Localizable.xcstrings`, and `OpenSourceLicenses.md`.
- `Resources/DevKit/scripts/` contains repository maintenance scripts that support the build/test workflow, localization hygiene, workspace management, and license aggregation.
- `Resources/AdditionalLicenses/` contains manually curated upstream license files that should override or supplement scanned dependency licenses when needed.

### Test Layer

- `ModernUIKitTests/` contains the app-level hosted tests for the main target.
- Organize tests by feature or subdomain under `ModernUIKitTests/`, for example `Application/`, future `Library/`, `Playback/`, or `Settings/`.
- Shared testing helpers should live in `ModernUIKitTests/TestSupport.swift` or `ModernUIKitTests/TestSupport/` once the helper surface justifies it.

## Placement Guide

- Thread starter-level preferences through `AppPreferences`.
- Do not introduce new singletons for feature work unless a platform API truly requires it.
- Do not thread optional LookInside or `LookInsideServer` setup through `AppPreferences`; local inspection tooling should stay developer-scoped unless the project explicitly adopts it.
- New app services should live under the closest future `Backend/*` subdomain, not directly inside view controllers.
- Shared UI goes into `Interface/Common/` only when it is clearly cross-feature infrastructure.
- If a UI type is only used by one feature, keep it inside that feature folder even if it looks reusable.
- New resource files that ship in the app belong under `ModernUIKit/Resources/`, not under the repo-root `Resources/` folder.
- New maintenance scripts belong under `Resources/DevKit/scripts/` and should be exposed through `Makefile` if they become part of the normal workflow.
- New manual license texts belong under `Resources/AdditionalLicenses/<PackageName>/LICENSE` or `COPYING`.
- New tests should mirror the app’s folder boundaries where practical, so the test tree stays readable as the app grows.

## Dependency Rules

- `AppPreferences` is the starter-level preferences/configuration surface.
- Prefer dependency injection and composition over inheritance and singleton access.
- UI types should depend on abstractions owned by the app, not construct global runtime state by themselves.
- Use `FileManager.default` directly for standard file operations. Do not pass `FileManager` around unless a test seam is genuinely needed.

## Workspace Rules

- Treat `ModernUIKit.xcworkspace/` as the default Xcode entrypoint for day-to-day work.
- Keep `ModernUIKit.xctestplan` attached to the shared `ModernUIKit` scheme.
- If the repository gains local packages or vendor packages, add them to the workspace explicitly so Xcode can surface them in the project navigator and Tests UI.
- Keep workspace and on-disk naming aligned with the template’s current base name.

## UIKit File Rules

- Keep `main.swift` as the entry point. Do not switch the starter to `@main`.
- No `Main.storyboard`; keep only `LaunchScreen.storyboard` under `ModernUIKit/Resources/`.
- Keep Xcode groups aligned with on-disk folders.
- Keep the first app shell under `Interface/Root/` rather than embedding root composition in `SceneDelegate`.
- Split large controllers by responsibility using focused extensions such as `+Layout`, `+Actions`, `+Table`, or `+State` when the app grows.
- Split by responsibility, not by arbitrary line count.
- If the app later gains feature-specific resources, keep them under the closest feature folder or the app `Resources/` folder, not next to unrelated code.
- Push for feature drilling; present temporary flows modally.
- Modal presentation should usually wrap content in a `UINavigationController`.

## View Lifecycle Rules

- Prefer installing static view hierarchy and initial visual state in `viewDidLoad`.
- Avoid doing first-load data setup in `viewWillAppear` unless the behavior truly depends on every appearance.
- Prefer explicit render/apply methods over scattered state mutation across multiple lifecycle callbacks.
- When list UIs arrive, prefer diffable data sources and update snapshots from clear rendering boundaries.

## Navigation Rules

- Push for feature drill-in and in-app navigation.
- Use modal presentation for temporary flows, confirmation flows, import/export surfaces, and setup wizards.
- If a modal flow can branch or push deeper, wrap it in a `UINavigationController`.

## Configuration Rules

- Shared build settings belong in `Configuration/*.xcconfig`, not hardcoded directly into the project file unless Xcode requires it.
- Local signing and bundle overrides should go into untracked developer override files:
  - `Configuration/Developer.xcconfig`
  - `Configuration/DevelopmentDeveloper.xcconfig`
  - `Configuration/DeveloperRelease.xcconfig`
- Do not hardcode personal team IDs, company bundle identifiers, or machine-specific paths into the committed template.

## Code Style

- Indentation: 4 spaces.
- Use early returns and `guard` to reduce nesting.
- Prefer value types unless identity or UIKit lifecycle requires a class.
- Keep comments rare and only where they remove real ambiguity.
- Avoid unnecessary optionals. If a property has a meaningful default value, use it.
- Callback closures that are always assigned before use should usually be non-optional with empty defaults.
- If Combine is introduced, store subscriptions in a single `var cancellables: Set<AnyCancellable> = []` per owner.

## Build & Tooling Rules

- Use the top-level `Makefile` for routine build flows instead of invoking `xcodebuild` directly.
- Current supported targets:
  - `make build`
  - `make build-ios`
  - `make build-sim`
  - `make build-device`
  - `make build-catalyst`
  - `make test`
  - `make test-unit`
  - `make package-resolve`
  - `make strip-xcstrings`
  - `make validate-xcstrings`
  - `make tidy-schemes`
  - `make chore`
  - `make clean`
- `make build` should cover the primary development paths, currently iOS Simulator and Mac Catalyst.
- `make test` / `make test-unit` should run on the Mac Catalyst destination by default.
- `Resources/DevKit/scripts/run_xcodebuild.sh` is the expected execution path for build and test commands because it validates the log output, not just the shell exit code.
- `scan.license.sh`, `strip_stale_xcstrings.py`, `validate_xcstrings.py`, and `tidy_workspace_schemes.py` are part of the repository contract, not optional side scripts.
- `ModernUIKit.xcworkspace` is the expected Xcode entrypoint for interactive work. Do not silently drift back to a project-only workflow.
- `scan.license.sh` skips optional LookInside debug-tool packages so local inspection checkouts do not pollute app license notices.
- If a new workflow becomes standard for the template, add a Makefile target for it instead of relying on ad-hoc shell commands.
- A successful shell exit code is not enough; always read the build log and verify the build actually succeeded without real errors.

## Testing Rules

- The starter ships with a minimal hosted unit test target.
- `ModernUIKit.xctestplan` is part of the template contract; keep the shared scheme attached to it so Xcode's Tests UI stays useful from day one.
- Prefer Swift Testing for new starter tests unless a concrete XCTest-only need exists.
- Organize tests by feature or subdomain (`Application/`, future `Library/`, `Playback/`, etc.) instead of letting test files pile up at the target root.
- New tests should cover app behavior and dependency wiring before drifting into brittle presentation assertions.
- Prefer stable Catalyst-oriented `test-unit` execution over simulator-only convenience paths for the default automated test workflow.
- Keep tests lightweight enough that the template still feels like a starter rather than a framework.
- Prefer behavior-focused tests over UI-structure tests.
- Avoid fragile assertions that only verify titles, tab order, or navigation chrome unless that presentation detail is the actual behavior under test.

## DevKit Rules

- `run_xcodebuild.sh` owns log-aware Xcode execution and should remain the shared wrapper behind Makefile build/test targets.
- `scan.license.sh` owns SwiftPM package resolution and `OpenSourceLicenses.md` refresh. If its behavior changes, keep the Makefile target contract stable.
- `strip_stale_xcstrings.py` and `validate_xcstrings.py` own string-catalog hygiene for the repository.
- `tidy_workspace_schemes.py` owns the workspace scheme visibility/order experience inside Xcode.
- If a new repository-maintenance workflow becomes reusable, prefer adding it under `Resources/DevKit/scripts/` and exposing it through `Makefile`.

## Documentation Sync

- Structural directory or workflow changes must update this `AGENTS.md` in the same change.
- If `README.md` stops matching the actual workspace, DevKit, or test workflow, update it immediately rather than leaving stale starter instructions behind.
