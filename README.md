# Modern.UIKit

> Agent-native, programmatic UIKit starter for iOS 26 apps.

Modern.UIKit pairs a clean Xcode workspace template with a `uikit-starter` agent skill that scaffolds a new repository from `template/`. Each generated app ships with `AGENTS.md`, `mise` tasks, and CLI-friendly build, localization, and test scripts so coding agents can work without clicking through Xcode.

## Start with an AI Agent

Give this prompt to Codex, Claude Code, or another coding agent. Replace the app name and bundle ID:

```text
Create a new iOS app from https://github.com/Zach677/Modern.UIKit.
Clone it to a temporary directory and follow skills/uikit-starter/SKILL.md.
App name: <AppName>
Bundle ID: <com.example.AppName>
```

To use the skill again without the prompt, install it with `npx skills add Zach677/Modern.UIKit --skill uikit-starter -g -y`, or copy or symlink `skills/uikit-starter` into the skills folder of your agent. Then ask: `Use $uikit-starter to create a new UIKit app named MyApp with bundle ID com.example.MyApp.`

## Create a Project

The skill copies `template/` into a new local repository, creates the GitHub repository, and sets the app identity in `Configuration/Base.xcconfig`. The project, target, and scheme keep the fixed name `App`. Only the workspace file takes the repository name.

Without an agent, run the script from a local checkout:

```bash
python3 skills/uikit-starter/scripts/create_project.py \
    --repo MyApp --bundle-id com.example.MyApp --template-dir template --parent-dir ~/Developer
```

## What's included

- UIKit scene lifecycle through `@main AppDelegate` and `SceneDelegate`. No storyboards; the launch screen uses the `UILaunchScreen` key.
- iOS 26, Swift 6 with `MainActor` default isolation.
- iPhone only by default. Pass `--ipad` or `--mac-catalyst` when you create the app, or change `TARGETED_DEVICE_FAMILY` and `SUPPORTS_MACCATALYST` in `Base.xcconfig`. Mac Catalyst needs iPad.
- `Packages/Core` local package for UI-free logic, tested with `swift test` on macOS.
- Hosted Swift Testing target, shared test plan, and an Xcode workspace.
- Shared xcconfig files for identity, signing, and version.
- String catalog with `en` and `zh-Hans`, and a validator for missing or stale keys.

## Requirements

- Xcode with the iOS 26 SDK or later
- `mise`
- `gh` to create the GitHub repository; run `mise install` in `template/` or in the app for the pinned SwiftFormat and xcbeautify

## Development

Open `template/ModernUIKit.xcworkspace`, or use:

```bash
cd template
mise install    # pinned SwiftFormat and xcbeautify
mise tasks
mise run-ios
cd ..
mise check      # run before each commit: tooling tests, then a generated app's mise check
```

```text
template/                     the app; each generated app is a copy of it
  App/                        UIKit app: Application/, Interface/, Resources/
  AppTests/                   hosted Swift Testing tests
  Packages/Core/              UI-free logic, tested with swift test
  Configuration/              xcconfig: identity, platforms, signing, version
  Scripts/                    build, simulator, license, and localization scripts
  Licenses/                   manual license overrides
skills/uikit-starter/         the agent skill that creates new projects
Tests/Scripts/                tests for template/Scripts
```

See [template/AGENTS.md](template/AGENTS.md) for the app rules and [HACKING.md](HACKING.md) for template maintenance.

## Contributing

Bug reports and small, focused pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Acknowledgements

Modern.UIKit draws from [MuseAmp](https://github.com/Lakr233/MuseAmp), including its workspace-first Xcode workflow, maintenance scripts, test-plan setup, and log-aware build automation.

## License

Modern.UIKit is licensed under the MIT License. See [LICENSE](LICENSE).
