# Modern.UIKit

> Agent-native, programmatic UIKit starter for iOS 26 apps.

## Create a Project

Install the skill for Codex, Claude Code, or another skill-aware agent:

```bash
npx skills add Zach677/Modern.UIKit --skill uikit-starter -g -y
```

Then ask the agent:

- `Use $uikit-starter to create a new private UIKit app repo named Mottai with bundle ID org.zaxh.Mottai, iPhone only.`

The skill creates a repository from this GitHub template and sets the app identity in `Configuration/Base.xcconfig`. The project, target, and scheme keep the fixed name `App`. Only the workspace file takes the repository name.

## Starter

- UIKit scene lifecycle through `@main AppDelegate` and `SceneDelegate`. No storyboards; the launch screen uses the `UILaunchScreen` key.
- iOS 26, Swift 6 with `MainActor` default isolation.
- iPhone and iPad by default. iPhone-only and Mac Catalyst are one-line switches in `Base.xcconfig`.
- `Packages/Core` local package for UI-free logic, tested with `swift test` on macOS.
- Hosted Swift Testing target, shared test plan, and an Xcode workspace.
- Shared xcconfig files for identity, signing, and version.
- String catalog with `en` and `zh-Hans`, and a validator for missing or stale keys.

## Development

Open `ModernUIKit.xcworkspace`, or use:

```bash
mise install    # pinned SwiftFormat and xcbeautify
mise tasks
mise build
mise test
mise run-ios
mise test-tooling
```

```text
App/                 UIKit app: Application/, Interface/, Resources/
AppTests/            hosted Swift Testing tests
Packages/Core/       UI-free logic, tested with swift test
Configuration/       xcconfig: identity, platforms, signing, version
Scripts/             build, simulator, license, and localization scripts
Licenses/            manual license overrides
skills/uikit-starter the agent skill that creates new projects
```

See [AGENTS.md](AGENTS.md) for the project rules and [HACKING.md](HACKING.md) for template maintenance.

## Contributing

Start with [GitHub Discussions](https://github.com/Zach677/Modern.UIKit/discussions) for bug triage, ideas, and questions. The issue tracker is reserved for accepted work. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Requirements

- Xcode with the iOS 26 SDK or later
- `mise`
- `gh`; run `mise install` for the pinned SwiftFormat and xcbeautify

## Acknowledgements

Modern.UIKit draws from [MuseAmp](https://github.com/Lakr233/MuseAmp), including its workspace-first Xcode workflow, maintenance scripts, test-plan setup, and log-aware build automation.

## License

Modern.UIKit is licensed under the MIT License. See [LICENSE](LICENSE).
