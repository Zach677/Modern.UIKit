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
- `Configuration/` contains shared Xcode build configuration files (`Base.xcconfig`, `Development.xcconfig`, `Release.xcconfig`, `Version.xcconfig`) used by the app target.
- `Resources/DevKit/scripts/` contains reusable maintenance scripts for build/test log handling, scheme tidying, xcstrings hygiene, and license scanning.
- `mise.toml` is the default task entrypoint for local build workflows.
- `.gitattributes` keeps GitHub Linguist language statistics focused on Swift app source by excluding repository automation, DevKit scripts, and agent skill tooling.
- `README.md` explains the template contract and local override flow.
- `CONTRIBUTING.md`, `AI_POLICY.md`, and `HACKING.md` define the public contribution process, AI usage policy, and developer guide entrypoint.
- `.github/` contains discussion-first community templates, the vouch automation workflows for contributor trust management, and the CI workflow that builds the app and runs the test gates on every push and pull request.
- `.agents/` contains optional agent-facing commands and skills that mirror project workflow preferences for compatible agent runtimes.
- `ModernUIKitTests/` contains the hosted unit tests for the app target.
- `skills/uikit-starter/scripts/adopt_existing.py` is the read-only inspection and planning entry point for adopting this starter into an existing iOS repository.

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
- Organize tests by feature or subdomain under `ModernUIKitTests/`, for example `Application/` today and one folder per future feature area.
- Shared testing helpers should live in `ModernUIKitTests/TestSupport.swift` or `ModernUIKitTests/TestSupport/` once the helper surface justifies it.

## Placement Guide

- Thread starter-level preferences through `AppPreferences`.
- Do not introduce new singletons for feature work unless a platform API truly requires it.
- Do not thread optional LookInside or `LookInsideServer` setup through `AppPreferences`; local inspection tooling should stay developer-scoped unless the project explicitly adopts it.
- New app services should live under the closest future `Backend/*` subdomain, not directly inside view controllers.
- Shared UI goes into `Interface/Common/` only when it is clearly cross-feature infrastructure.
- If a UI type is only used by one feature, keep it inside that feature folder even if it looks reusable.
- New resource files that ship in the app belong under `ModernUIKit/Resources/`, not under the repo-root `Resources/` folder.
- New maintenance scripts belong under `Resources/DevKit/scripts/` and should be exposed through `mise.toml` if they become part of the normal workflow.
- New manual license texts belong under `Resources/AdditionalLicenses/<PackageName>/LICENSE` or `COPYING`.
- New tests should mirror the app’s folder boundaries where practical, so the test tree stays readable as the app grows.
- `SceneDelegate` owns only `window` today. When a second scene-lifecycle callback needs app state, store the bootstrapped instance as `private var preferences: AppPreferences?` assigned in `scene(_:willConnectTo:options:)`. Do not bootstrap `AppPreferences` a second time and do not introduce a singleton to reach it.
- Adopt reference-project patterns as rules in this file, not as pre-created types; a new type must ship with at least one production consumer in the same change.
- When a feature area accumulates its second nontrivial convention, capture it as a rules section in this file in the same change.

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

- Keep `Configuration/Base.xcconfig` narrow and benchmark-aligned: it should include `Version.xcconfig` and own signing/provisioning plus the app bundle identifier.
- Keep the template itself team-neutral by leaving `DEVELOPMENT_TEAM` empty in `Configuration/Base.xcconfig`.
- For generated personal or single-team app projects, prefer committing the shared Apple Developer Team ID in the generated app's `Configuration/Base.xcconfig`, so Xcode's Signing & Capabilities view resolves the Team from build settings.
- For generated reusable templates, forks, or projects that intentionally avoid a shared signing identity, keep `DEVELOPMENT_TEAM` empty in committed files and use the untracked developer override files below.
- Keep version values in `Configuration/Version.xcconfig`.
- Keep target/platform settings that Xcode already owns, such as `PRODUCT_NAME`, `SWIFT_VERSION`, deployment targets, supported platforms, and Info.plist wiring, in `project.pbxproj`.
- Local signing and bundle overrides should go into untracked developer override files:
  - `Configuration/Developer.xcconfig`
  - `Configuration/DevelopmentDeveloper.xcconfig`
  - `Configuration/DeveloperRelease.xcconfig`
- Do not hardcode personal team IDs, company bundle identifiers, or machine-specific paths into the committed template.

## Localization Rules

- All user-facing strings in the app target use `String(localized:)`.
- Catalog keys are the natural English sentence, and the `en` value mirrors the key; `mise strip-xcstrings` enforces the mirroring. Do not use dot-namespaced identifier keys.
- Every target that contains user-facing strings must keep them in a `Localizable.xcstrings` under its `Resources/` directory, currently `ModernUIKit/Resources/Localizable.xcstrings`.
- When adding or modifying any localized key, update the corresponding `.xcstrings` file in the same change.
- Each key should include complete localizations for the locales already used by the catalog. For the starter catalog, keep `en` and `zh-Hans` entries complete and preserve positional format specifiers such as `%1$@` or `%2$lld`.
- Do not leave empty entries, untranslated keys, or orphaned keys in checked-in `.xcstrings` files.
- Run `mise strip-xcstrings` before committing xcstrings edits and `mise validate-xcstrings` to gate release-oriented changes. The validator cross-references each catalog against its owning target's Swift sources: keys with no `String(localized:)` or `NSLocalizedString` reference fail as orphaned, and referenced keys missing from the catalog fail as unregistered. Keys built from variables at runtime are invisible to this gate; register such a key with an explicit literal alongside the dynamic call site.
- Required locales beyond those already in the catalog are project policy set in `mise.toml` via `--require-locale`; the starter requires `zh-Hans`.

## Code Style

- Indentation: 4 spaces.
- Use early returns and `guard` to reduce nesting.
- Prefer value types unless identity or UIKit lifecycle requires a class.
- Keep comments rare and only where they remove real ambiguity.
- Avoid unnecessary optionals. If a property can have a meaningful default value, use it instead of making the property optional.
- If Combine is introduced, store subscriptions in a single `var cancellables: Set<AnyCancellable> = []` per owner and use `.store(in: &cancellables)`.
- Callback closures that are always assigned before use should be non-optional with an empty default, such as `var onTap: () -> Void = {}`. Avoid optional chaining at call sites for these callbacks.
- For throttle or cooldown dates, use `Date = .distantPast` instead of `Date?` when a concrete default represents the inactive state.
- For enum state properties, prefer a concrete default case such as `.idle` over making the property optional.
- Properties whose values can be derived from other state should be computed properties, not stored.
- Do not introduce stored properties to track state that is already available from an existing source of truth.

## API Verification

- When using iOS/macOS APIs that are new, recently changed, or unfamiliar, check Apple Developer Documentation before writing the code.
- Verify availability annotations, parameter signatures, and deprecation status against official docs rather than relying on memory alone.

## Build & Tooling Rules

- Always drive build, test, and SwiftPM package-resolve operations through `mise` tasks. Do not invoke `xcodebuild`, `xcrun xcodebuild`, or `swift test` directly from the shell for routine workflows.
- Current supported targets:
  - `mise build`
  - `mise build-ios`
  - `mise build-sim`
  - `mise build-device`
  - `mise build-catalyst`
  - `mise run-ios`
  - `mise run-sim`
  - `mise test`
  - `mise test-unit`
  - `mise test-tooling`
  - `mise package-resolve`
  - `mise scan-license`
  - `mise format`
  - `mise format-lint`
  - `mise strip-xcstrings`
  - `mise validate-xcstrings`
  - `mise tidy-schemes`
  - `mise chore`
  - `mise clean`
- `mise build` should cover the primary development paths, currently iOS Simulator and Mac Catalyst.
- `mise run-ios` / `mise run-sim` should build the simulator app, install it on the booted simulator, and launch it without replacing the normal build/test gates.
- `mise test` / `mise test-unit` should run on the Mac Catalyst destination by default.
- `mise test-tooling` runs the `skills/uikit-starter` Python unit tests; run it whenever those scripts change.
- `mise build-ios` only compiles the app target. To verify test file changes, use `mise test`.
- `Resources/DevKit/scripts/run_xcodebuild.sh` is the expected execution path for build and test commands because it validates the log output, not just the shell exit code.
- `scan.license.sh`, `strip_stale_xcstrings.py`, `validate_xcstrings.py`, and `tidy_workspace_schemes.py` are part of the repository contract, not optional side scripts.
- `ModernUIKit.xcworkspace` is the expected Xcode entrypoint for interactive work. Do not silently drift back to a project-only workflow.
- Package resolution and license refresh use `mise package-resolve` or `mise scan-license`.
- Release flows that refresh licenses against an intentionally dirty tree must pass `dirty=1`, for example `mise package-resolve -- dirty=1`; this is forwarded by the mise task as `ALLOW_DIRTY=1` to the scan script.
- Existing-repo adoption starts with `python3 skills/uikit-starter/scripts/adopt_existing.py --repo-path <repo>`. Treat its output as the agent-facing decision plan; ask only the blocking questions it surfaces and preserve existing repo identity by default. Use `--apply` only for `Status: ready` / `Mode: xcode-adopt` plans; the first slice is additive and must not overwrite existing files.
- Keep additive baseline completion for a clean, plain UIKit repo with one root Xcode project as the only write-enabled migration slice. Reject unsafe rendered identifiers and any apply target that resolves outside the repository; keep SwiftUI, Tuist, CocoaPods, SwiftPM, and AppKit migration plan-only.
- Keep existing command surfaces plan-only until they are reconciled explicitly. Render adopted mise tasks from detected capabilities; include Mac Catalyst and test tasks only when the project already supports Catalyst and exposes a test target.
- Before any adoption write, require the analyzed Git HEAD and repository profile to still match the reviewed plan. Create missing files exclusively through repository-anchored, no-follow writes; never overwrite an intervening file. Keep adopted DerivedData under the system temporary directory so verification does not pollute the target worktree.
- Under `preserve-existing-workflow`, keep detected XcodeGen, Fastlane, mise, Make, and root `scripts/` validation entrypoints as the existing source of truth or command surface; translate compatible checks into them instead of proposing parallel mise or DevKit script workflows.
- Classify package-first repositories with only nested Xcode projects as `swiftpm-nested-app-guided-decision` before the workspace-only fallback, even when the repository also has a root workspace.
- Keep `.gitattributes` Linguist exclusions scoped to repository tooling and automation surfaces. Do not exclude app target source or Swift tests from language statistics.
- Manually collected upstream license texts belong under `Resources/AdditionalLicenses/<PackageName>/LICENSE` or `COPYING`. The scanner prefers these files over bundled dependency licenses when both exist.
- Format with `mise format` and check formatting with `mise format-lint`; submodules under `Vendor/` and build artifacts are excluded automatically.
- Localization hygiene uses `mise strip-xcstrings` to drop stale keys and sync source-language values, and `mise validate-xcstrings` to check stale, orphaned, or unregistered keys and missing translations across catalog locales plus the locales required in `mise.toml`.
- `scan.license.sh` skips optional LookInside debug-tool packages so local inspection checkouts do not pollute app license notices.
- If a new workflow becomes standard for the template, add a matching mise task instead of relying on ad-hoc shell commands.
- A shell exit code of `0` from `mise build*` or `mise test` is not proof of success. Always read the full log output and verify there are no compiler errors, no real compiler warnings, and for `mise test`, every test case reported as passed.

## LookInside Optional Tooling

- Treat LookInside as optional local developer capability, not starter architecture.
- Do not commit `LookInsideServer` package wiring, app startup calls, or generated `Package.resolved` entries unless Zach explicitly asks to adopt LookInside as shared project tooling.
- A coding agent asked to configure LookInside should verify the macOS app and CLI first:

```bash
brew install --cask Zach677/star/lookinside
git clone https://github.com/LookInsideApp/LookInsideServer.git ~/Developer/other-repo/LookInsideServer
cd ~/Developer/other-repo/LookInsideServer
swift build -c release --product lookinside
mkdir -p ~/.local/bin
ln -sfn "$PWD/.build/release/lookinside" ~/.local/bin/lookinside
lookinside --help
```

- `brew install Zach677/star/lookinside-cli` is acceptable when the tap version is fresh enough; source builds from `LookInsideApp/LookInsideServer` are preferred when matching the latest runtime and CLI matters.
- A target only appears in `lookinside list` after the app runs `LookinServer` or a compatible injected runtime. If no target appears, report that state instead of silently adding committed app dependencies.
- Use `lookinside list`, `lookinside inspect`, `lookinside hierarchy`, and `lookinside export` for agent-readable inspection artifacts.
- `scan.license.sh` intentionally skips optional LookInside debug-tool packages so local inspection checkouts do not pollute app license notices.

## Testing Rules

- The starter ships with a minimal hosted unit test target.
- The project has a Mac Catalyst destination. Tests can be built and run on Catalyst in addition to iOS simulators.
- `ModernUIKit.xctestplan` is part of the template contract; keep the shared scheme attached to it so Xcode's Tests UI stays useful from day one.
- Prefer Swift Testing for new starter tests unless a concrete XCTest-only need exists.
- Organize tests by feature or subdomain (`Application/` today, one folder per future feature area) instead of letting test files pile up at the target root.
- New tests should cover app behavior and dependency wiring before drifting into brittle presentation assertions.
- Prefer stable Catalyst-oriented `test-unit` execution over simulator-only convenience paths for the default automated test workflow.
- Keep tests lightweight enough that the template still feels like a starter rather than a framework.
- Prefer behavior-focused tests over UI-structure tests.
- New tests should validate app behavior, dependency wiring, localization, services, and future feature logic without depending on view titles, tab counts/order, selected tabs, or other presentation-only details.
- Avoid assertions such as `.title == ...`, `tabs.count == ...`, or similar checks that only verify UIKit configuration text or shell layout unless that presentation detail is the actual behavior under test.
- When testing UI-adjacent code, prefer asserting observable side effects or state changes rather than labels, tab wiring, or navigation chrome.

## DevKit Rules

- `run_xcodebuild.sh` owns log-aware Xcode execution, derived-data placement, and build cache isolation, and should remain the shared wrapper behind mise build/test targets.
- `scan.license.sh` owns SwiftPM package resolution and `OpenSourceLicenses.md` refresh. If its behavior changes, keep the mise task contract stable.
- `strip_stale_xcstrings.py` and `validate_xcstrings.py` own string-catalog hygiene for the repository.
- `tidy_workspace_schemes.py` owns the workspace scheme visibility/order experience inside Xcode.
- If a new repository-maintenance workflow becomes reusable, prefer adding it under `Resources/DevKit/scripts/` and exposing it through `mise.toml`.

## Documentation Sync

- Structural directory or workflow changes must update this `AGENTS.md` in the same change.
- Contribution workflow changes must keep `CONTRIBUTING.md`, `AI_POLICY.md`, `HACKING.md`, and `.github/` templates/workflows aligned.
- If `README.md` stops matching the actual workspace, DevKit, or test workflow, update it immediately rather than leaving stale starter instructions behind.
