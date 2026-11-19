# Template Repository Rules

- The app template is in `template/`. When you work on the app, follow `template/AGENTS.md`.
- Every file in `template/` that git tracks goes into each generated app. Template-only files stay at the repository root.
- The root holds the generator (`skills/uikit-starter/`), the tooling tests (`Tests/Scripts/`), and the template docs.
- Run `mise check` at the root before each commit. It runs `mise test-tooling`, generates an app from `template/` into a temporary directory, and runs `mise check` in that app.
- See [HACKING.md](HACKING.md) for template maintenance.
