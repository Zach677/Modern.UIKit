# Project Overview

## App Shape

- This is a pure UIKit iOS starter with programmatic setup.
- Keep the entry path as `No-UIKit/Application/main.swift` -> `AppDelegate.swift` -> `SceneDelegate.swift`.
- `SceneDelegate` owns window creation, bootstraps the shared `AppContext`, and installs the root navigation shell.
- `Interface/Root/RootViewController.swift` is the first screen and the seed of the future app shell.
- Do not introduce SwiftUI into the starter by default. If a real project later chooses SwiftUI, that should be an explicit project decision rather than template drift.

## Structure Rules

### Top Level

- `No-UIKit/` contains the app target source and resources.
- `Configuration/` contains shared Xcode build configuration files (`Base.xcconfig`, `Development.xcconfig`, `Release.xcconfig`, `Version.xcconfig`).
- `Makefile` is the default shell entry point for local build workflows.
- `README.md` explains the template contract and local override flow.
- `No-StoryBoardTests/` contains the hosted unit tests for the app target.

### Application Layer

- `Application/` contains only lifecycle, bootstrap, and app-wide configuration types.
- Keep `AppDelegate.swift`, `SceneDelegate.swift`, `AppContext.swift`, and `AppContext+Bootstrap.swift` in `Application/`.
- Do not move feature logic, view composition, or network/database code into `Application/`.

### Interface Layer

- `Interface/Root/` contains the root shell and the first view controller shown after boot.
- Future shared UIKit infrastructure can grow under `Interface/Common/`.
- Feature-specific UI should live under dedicated feature folders inside `Interface/`, not inside `Application/`.

### Backend Layer

- If the starter grows into a real app, create a top-level `Backend/` folder inside `No-UIKit/` for domain services, persistence, API clients, state ownership, and cross-feature runtime logic.
- Keep UI state rendering in `Interface/`, but keep state ownership in `Backend/`.

## Placement Guide

- Thread shared dependencies through `AppContext`.
- Do not introduce new singletons for feature work unless a platform API truly requires it.
- New app services should live under the closest future `Backend/*` subdomain, not directly inside view controllers.
- Shared UI goes into `Interface/Common/` only when it is clearly cross-feature infrastructure.
- If a UI type is only used by one feature, keep it inside that feature folder even if it looks reusable.

## Dependency Rules

- `AppContext` is the app-level dependency container for this starter.
- Prefer dependency injection and composition over inheritance and singleton access.
- UI types should depend on abstractions owned by the app, not construct global runtime state by themselves.
- Use `FileManager.default` directly for standard file operations. Do not pass `FileManager` around unless a test seam is genuinely needed.

## UIKit File Rules

- Keep `main.swift` as the entry point. Do not switch the starter to `@main`.
- No `Main.storyboard`; keep only `LaunchScreen.storyboard`.
- Keep Xcode groups aligned with on-disk folders.
- Split large controllers by responsibility using focused extensions such as `+Layout`, `+Actions`, `+Table`, or `+State` when the app grows.
- Push for feature drilling; present temporary flows modally.
- Modal presentation should usually wrap content in a `UINavigationController`.

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
  - `make build-sim`
  - `make build-device`
  - `make test`
  - `make clean`
- The simulator build path is the default because it should work before signing is configured.
- `make test` should resolve a real iPhone simulator destination automatically, but callers may override `TEST_DESTINATION` when needed.
- If a new workflow becomes standard for the template, add a Makefile target for it instead of relying on ad-hoc shell commands.
- A successful shell exit code is not enough; always read the build log and verify the build actually succeeded without real errors.

## Testing Rules

- The starter ships with a minimal hosted unit test target.
- New tests should cover app behavior and dependency wiring before drifting into brittle presentation assertions.
- Keep tests lightweight enough that the template still feels like a starter rather than a framework.
- Prefer behavior-focused tests over UI-structure tests.
- Avoid fragile assertions that only verify titles, tab order, or navigation chrome unless that presentation detail is the actual behavior under test.
