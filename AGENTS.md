# Project Rules

## App Shape

- Programmatic UIKit app for iOS 26 and later. Swift 6 language mode with `MainActor` default isolation.
- Entry path: `@main AppDelegate` -> `SceneDelegate` (set in `App/Resources/Info.plist`) -> `Interface/Root/RootViewController`.
- Do not add SwiftUI, `.xib` files, or storyboards unless the user asks. The launch screen comes from the `UILaunchScreen` Info.plist key.
- Set the app tint with the `AccentColor` asset, not `window.tintColor`.
- The project, target, and scheme use the fixed name `App`. Do not rename them. The workspace is the only `.xcworkspace` at the repository root, and scripts find it by that rule.
- `Configuration/Base.xcconfig` owns the app identity (display name, bundle identifier, team) and the platforms: `TARGETED_DEVICE_FAMILY` (`1` iPhone, `1,2` iPhone and iPad) and `SUPPORTS_MACCATALYST`. Change platforms there, not in the Xcode project.

## Layout

- `App/Application/`: lifecycle and app-wide composition only. No feature logic.
- `App/Interface/<Feature>/`: view controllers, views, and cells for one feature. Move a type to `Interface/Common/` only when two or more features use it.
- `App/Services/`: side effects such as notifications, camera, and network clients.
- `App/Resources/`: assets, `Info.plist`, `Localizable.xcstrings`, and other files that ship in the app.
- `Packages/Core/`: UI-free models and business logic. Do not import UIKit here. Put logic here when it can be tested without UIKit.
- `AppTests/`: hosted tests, one folder per feature, mirroring `App/`.
- `Configuration/`: xcconfig files. Local overrides go in the untracked `Developer.xcconfig`, `DevelopmentDeveloper.xcconfig`, and `DeveloperRelease.xcconfig`.
- `Scripts/`: build, simulator, license, and localization scripts. Expose new routine scripts through `mise.toml`.
- `Licenses/<Package>/LICENSE`: manual license texts. They override the licenses found in package checkouts.

Xcode uses file-system synchronized groups. Adding a file to a folder does not need a project file edit.

## Code

- 4-space indentation. Use `guard` and early returns.
- Prefer value types. Use a class when identity or the UIKit lifecycle requires it.
- Inject dependencies through initializers. Do not add singletons unless a platform API requires one.
- Add a type only together with its first production consumer.
- Do not store state that can be derived. Use computed properties.
- Prefer concrete defaults over optionals: `var onTap: () -> Void = {}`, `Date = .distantPast`, an `.idle` enum case.
- Add comments only when the reason is not obvious from the code.
- Check Apple documentation for new or changed APIs. Do not rely on memory for availability or signatures.

## UIKit

- Build views with Auto Layout in code. Install the view hierarchy in `viewDidLoad`.
- Keep lifecycle methods and action handlers small. Use explicit `apply`/`render` methods for state changes.
- Use diffable data sources for lists.
- Push for drill-in navigation. Present temporary flows modally, inside a `UINavigationController` when the flow can go deeper.
- Use semantic colors and Dynamic Type text styles.
- Split a large controller by responsibility with extensions such as `+Layout`, `+Actions`, or `+DataSource`.

## Localization

- All user-facing strings use `String(localized:)`. Keys are natural English sentences, and the `en` value mirrors the key.
- Keep `en` and `zh-Hans` complete in `App/Resources/Localizable.xcstrings`. Update the catalog in the same change as the code.
- Run `mise strip-xcstrings`, then `mise validate-xcstrings`. A key built at runtime is invisible to the validator, so also register it as a literal.

## Build and Test

Always use `mise`. Do not call `xcodebuild` or `swift test` directly. Run `mise install` once to get the pinned SwiftFormat and xcbeautify.

| Task | Purpose |
| --- | --- |
| `mise build` | Build for iOS Simulator |
| `mise build-catalyst` | Build for Mac Catalyst; `mise build` also runs it when `SUPPORTS_MACCATALYST = YES` |
| `mise build-device` | Build for a generic iOS device |
| `mise run-ios` | Build, install, and launch on the newest iPhone simulator |
| `mise test` | `test-core` (`swift test` on macOS) and then `test-app` (hosted tests on a simulator) |
| `mise test-core` | Core package tests only; use for fast TDD |
| `mise format` / `mise format-lint` | Format or check Swift sources with SwiftFormat (`.swiftformat`) |
| `mise package-resolve` | Resolve packages and refresh `OpenSourceLicenses.md` (alias: `scan-license`) |
| `mise chore` | Strip strings, refresh licenses, format |

- `run_xcodebuild.sh` fails on the exit code, compiler errors, and xcodebuild failure summaries. Still read the log: a passing run must have no compiler warnings and every test must pass.
- Override defaults with environment variables: `CONFIGURATION=Release mise build`, `SIMULATOR_ID=<udid> mise test`, `ALLOW_DIRTY=1 mise package-resolve`.
- Scripts: bash only for thin wrappers, Python 3 with the standard library for anything that parses files. Do not add other script languages.

## Tests

- Use Swift Testing.
- Test behavior and state changes, not titles, labels, or layout.
- Put most tests in `Packages/Core/Tests`. Hosted `AppTests` are for wiring that needs UIKit.
- Put shared helpers in `AppTests/TestSupport/` when two or more test files need them.

## Keep Docs Current

When the directory layout or a workflow changes, update this file in the same change. When a feature collects its second nontrivial convention, add it here as a rule.
