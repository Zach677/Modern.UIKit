# Modern.UIKit

> Agent-native UIKit starter for Codex, Claude Code, and other coding agents.

![Platform](https://img.shields.io/badge/platform-iOS%2017%2B%20%7C%20Mac%20Catalyst-blue)
![Swift](https://img.shields.io/badge/Swift-5.0%20default%20%7C%206.0%20optional-orange)
![Xcode](https://img.shields.io/badge/Xcode-iOS%2017%20SDK%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Modern.UIKit is a programmatic UIKit starter plus an Agent workflow. It helps an Agent create a new UIKit app, inspect an existing iOS/macOS repo, and decide whether adoption is safe before touching files.

It is not a universal one-click migration tool. Complex SwiftUI, Tuist, CocoaPods, SwiftPM, or custom build setups are treated as planning cases first.

## Use With An Agent

Install the skill where your Agent runtime can see it:

```bash
npx skills add Zach677/Modern.UIKit --skill uikit-starter -g -y
```

Then ask Codex, Claude Code, or another skill-aware Agent to use `$uikit-starter`.

Good prompts:

- `Use $uikit-starter to create a new private UIKit app repo named ShelfMusic.`
- `Use $uikit-starter to inspect this repo and tell me whether it can adopt Modern.UIKit safely.`
- `Use $uikit-starter on this SwiftUI/Tuist repo, but do not change files until you explain the migration path.`
- `Use $uikit-starter to preserve this repo's existing workflow and only borrow compatible Modern.UIKit practices.`

The intended user experience is natural language first. The scripts under `skills/uikit-starter/scripts/` exist so Agents can do deterministic work; they are not the primary UI.

## What It Can Do

- Create fresh programmatic UIKit apps from this starter.
- Rename project, app source, tests, workspace, scheme, bundle identifier, and starter docs for generated apps.
- Analyze existing repos without writing files.
- Apply additive baseline files only when the analyzer returns `can_apply: true`.
- Produce migration plans for SwiftUI, Tuist, CocoaPods workspace, SwiftPM package-first, and SwiftPM package-only repos.
- Preserve git history, remotes, signing settings, bundle identifiers, product source, resources, and existing repo-specific workflows by default.

## What It Will Not Pretend To Do

- It will not automatically replace a SwiftUI app entry with UIKit.
- It will not automatically convert Tuist, CocoaPods, SwiftPM, XcodeGen, Bazel, Buck, Fastlane, or custom build systems.
- It will not overwrite existing files during adoption.
- It will not claim a repo can migrate just because it can be inspected.

## Starter Baseline

The template itself is intentionally small:

- UIKit app lifecycle through `main.swift`, `AppDelegate`, and `SceneDelegate`.
- Programmatic UI with no main storyboard.
- `Application/`, `Interface/Root/`, and app `Resources/` folders.
- Shared `Configuration/*.xcconfig` files for signing, bundle, and version settings.
- Hosted Swift Testing target with an `.xctestplan`.
- `Makefile` plus DevKit scripts for log-aware build/test, formatting, localization, scheme tidying, and license scanning.

## Roadmap

Current phase: **agent-native preview**.

- [x] Fresh UIKit app creation.
- [x] Existing repo analysis with a guarded `can_apply` path.
- [x] Planning mode for common SwiftUI, Tuist, CocoaPods, workspace-only, and SwiftPM repo shapes.
- [ ] Broaden real repo smoke coverage ([#1](https://github.com/Zach677/Modern.UIKit/issues/1)).
- [ ] Improve adoption accuracy ([#2](https://github.com/Zach677/Modern.UIKit/issues/2), [#3](https://github.com/Zach677/Modern.UIKit/issues/3)).
- [ ] Design migration tooling after analysis is reliable ([#4](https://github.com/Zach677/Modern.UIKit/issues/4)).

## Contributing

Modern.UIKit uses a discussion-first contribution flow. Start with
[Discussions](https://github.com/Zach677/Modern.UIKit/discussions) for bug
triage, feature ideas, and questions. The issue tracker is reserved for
accepted, actionable work.

See [CONTRIBUTING.md](CONTRIBUTING.md) for the full process.

## Agent Docs

Detailed rules live outside the README:

- [`skills/uikit-starter/SKILL.md`](skills/uikit-starter/SKILL.md) is the Agent-facing workflow contract.
- [`AGENTS.md`](AGENTS.md) is the repository working contract.
- `skills/uikit-starter/scripts/create_project.py` creates fresh projects.
- `skills/uikit-starter/scripts/adopt_existing.py` analyzes existing repos and gates adoption with `can_apply`.

## Requirements

- Xcode with iOS 17 SDK or later.
- Swift Testing support.
- GitHub CLI (`gh`) for repository workflows.
- Node.js / `npx`, Prettier, `swiftformat`, and `xcbeautify` for the full Agent workflow.

## Acknowledgements

Modern.UIKit is inspired by the engineering discipline in [MuseAmp](https://github.com/Lakr233/MuseAmp), especially its workspace-first Xcode workflow, DevKit-style maintenance scripts, test-plan setup, and log-aware build/test automation.

## License

Modern.UIKit is licensed under the MIT License. See `LICENSE` for details.

---

© 2026 @Zach677. Released under the MIT License.
