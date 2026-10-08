# Modern.UIKit

> Agent-native, programmatic UIKit starter for iOS 26 iPhone apps.

## Create a Project

Install the skill for Codex, Claude Code, or another skill-aware agent:

```bash
npx skills add Zach677/Modern.UIKit --skill uikit-starter -g -y
```

Then ask the agent:

- `Use $uikit-starter to create a new private UIKit app repo named Mottai with bundle ID org.zaxh.Mottai.`

The skill creates a repository from this GitHub template and sets the app identity in `Configuration/Base.xcconfig`. The project, target, scheme, and workspace keep the fixed name `App`, so nothing else is renamed.

## Starter

- UIKit lifecycle through `main.swift`, `AppDelegate`, and `SceneDelegate`. No main storyboard.
- iOS 26, iPhone only, Swift 6 with `MainActor` default isolation.
- `Packages/Core` local package for UI-free logic, tested with `swift test` on macOS.
- Hosted Swift Testing target, shared test plan, and an Xcode workspace.
- Shared xcconfig files for identity, signing, and version.
- String catalog with `en` and `zh-Hans`, and a validator for missing or stale keys.

## Development

Open `App.xcworkspace`, or use:

```bash
mise tasks
mise build
mise test
mise run-ios
mise test-tooling
```

See [AGENTS.md](AGENTS.md) for the project rules and [HACKING.md](HACKING.md) for template maintenance.

## Contributing

Start with [GitHub Discussions](https://github.com/Zach677/Modern.UIKit/discussions) for bug triage, ideas, and questions. The issue tracker is reserved for accepted work. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Requirements

- Xcode with the iOS 26 SDK or later
- `mise`
- `gh`, Node.js with `npx` (Prettier), SwiftFormat, and `xcbeautify` for the full workflow

## Acknowledgements

Modern.UIKit draws from [MuseAmp](https://github.com/Lakr233/MuseAmp), including its workspace-first Xcode workflow, DevKit maintenance scripts, test-plan setup, and log-aware build automation.

## License

Modern.UIKit is licensed under the MIT License. See [LICENSE](LICENSE).
