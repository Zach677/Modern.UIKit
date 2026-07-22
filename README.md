# Modern.UIKit

> Agent-native, programmatic UIKit starter for iOS and Mac Catalyst apps.

## Create or Adopt a Project

Install the skill for Codex, Claude Code, or another skill-aware Agent:

```bash
npx skills add Zach677/Modern.UIKit --skill uikit-starter -g -y
```

Then ask the Agent to use `$uikit-starter`:

- `Use $uikit-starter to create a new private UIKit app repo named ShelfMusic.`
- `Use $uikit-starter to inspect this repo and tell me whether it can adopt Modern.UIKit safely.`
- `Use $uikit-starter to plan a migration for this SwiftUI or Tuist repo without changing files.`

## Scope

- Create fresh programmatic UIKit apps from this starter.
- Inspect existing repositories without writing files.
- Add missing baseline files only when the analyzer returns `can_apply: true`.
- Produce migration plans for SwiftUI, Tuist, CocoaPods, SwiftPM, and custom workflows.

Write-enabled adoption is limited to a clean UIKit repository with one root Xcode project and one unambiguous app target. Apply rechecks the reviewed Git revision and repository profile, refuses overwrites and symlink escapes, and leaves unsupported repository shapes in plan-only mode.

## Starter

- UIKit lifecycle through `main.swift`, `AppDelegate`, and `SceneDelegate`.
- Programmatic UI with no main storyboard.
- `Application/`, `Interface/Root/`, and app `Resources/` boundaries.
- Shared Xcode configuration files for signing, bundle, and version settings.
- An Xcode workspace, shared test plan, and hosted Swift Testing target.
- iOS Simulator and Mac Catalyst build paths through `mise`.

Swift 6.0 is the default language mode. Fresh projects can opt into Swift 5.0 when required.

## Development

Open `ModernUIKit.xcworkspace`, or use:

```bash
mise tasks
mise build
mise test
mise format-lint
mise validate-xcstrings
mise test-tooling
```

See [HACKING.md](HACKING.md) for the full workflow, [skills/uikit-starter/SKILL.md](skills/uikit-starter/SKILL.md) for the Agent contract, and [AGENTS.md](AGENTS.md) for repository rules.

## Contributing

Start with [GitHub Discussions](https://github.com/Zach677/Modern.UIKit/discussions) for bug triage, ideas, and questions. The issue tracker is reserved for accepted work. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Requirements

- Xcode with the iOS 17 SDK or later
- `mise`
- Node.js with `npx`, GitHub CLI (`gh`), Prettier, SwiftFormat, and `xcbeautify` for the full Agent workflow

## Acknowledgements

Modern.UIKit draws from [MuseAmp](https://github.com/Lakr233/MuseAmp), including its workspace-first Xcode workflow, DevKit maintenance scripts, test-plan setup, and log-aware build automation.

## License

Modern.UIKit is licensed under the MIT License. See [LICENSE](LICENSE).
