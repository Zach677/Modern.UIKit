# Developing Modern.UIKit

Read ["Contributing to Modern.UIKit"](CONTRIBUTING.md) before you open a pull
request.

## Template Maintenance

- `template/` is the app. The generator copies every file in it that git
  tracks or that is untracked and not ignored. Put template-only files at the
  repository root, not in `template/`.
- `template/AGENTS.md` is copied into every generated app. Keep it about the
  app, not about this template repository.
- When the contribution flow changes, keep `CONTRIBUTING.md` and
  `AI_POLICY.md` aligned.
- Generated apps start without CI, because private repos pay for macOS runner
  minutes. This repository has no CI either; run `mise check` locally.
- Run `mise test-tooling` after you change `template/Scripts/` or the skill
  scripts. Their tests live in `Tests/Scripts/` and
  `skills/uikit-starter/tests/`.

## Checks

Run `mise check` at the repository root before each commit. It runs
`mise test-tooling`, generates an app from the working tree of `template/`
into a temporary directory, and runs `mise check` in that app. That proves a
clean copy of the template builds and passes its tests.

`cd template && mise check` runs only the app checks. mise also loads the root
`mise.toml` there, so `mise tasks` in `template/` also shows `test-tooling`.
