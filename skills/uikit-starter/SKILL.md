---
name: uikit-starter
description: Create a new programmatic UIKit iOS 26 app repository from the Modern.UIKit template (github.com/Zach677/Modern.UIKit). Use when the user wants to start a new UIKit or iOS app from scratch. Not for migrating, upgrading, or restyling an existing app.
---

# UIKit Starter

## Inputs

Ask only for these. Ask both in one message:

- `--repo`: GitHub repository name, for example `Mottai`.
- `--bundle-id`: for example `org.zaxh.Mottai`.

Use these defaults without asking. Change one only when the user asks:

| Option | Default | Change |
| --- | --- | --- |
| Display name | The repo name | `--display-name 趁鲜` |
| Devices | iPhone only | `--ipad` adds iPad |
| Mac Catalyst | Off | `--mac-catalyst` (also adds iPad, App Sandbox entitlements, and Hardened Runtime) |
| Development team | Empty | `--development-team ABCDE12345` |
| Swift file header | Off | `--author @Zach677` (adds `.swiftformat` header and `.githooks/pre-commit`) |
| GitHub repo | Private | `--visibility public`, or `--no-remote` for no GitHub repo |
| Verification | `mise build` | `--verify test`, `check`, or `none` |
| Parent directory | The user's working directory | `--parent-dir <path>` |

The GitHub repo goes to the account that `gh` is signed in to. To create it in an organization, use `--repo <owner>/<name>`. The local directory is then `<name>`.

## Run

Prerequisites: `git`, `gh` (not necessary with `--no-remote`), `mise` (not necessary with `--verify none`), and Xcode with an iOS simulator runtime. The script checks these commands and the `gh` sign-in before it creates anything. If mise is missing, ask the user to install it (https://mise.jdx.dev). After `curl https://mise.run | sh`, the user must add `~/.local/bin` to `PATH` (or run `mise activate`) before you run the script again.

If this skill is installed, the script clones the template from GitHub:

```bash
python3 <skill-dir>/scripts/create_project.py \
    --repo Mottai --bundle-id org.zaxh.Mottai --parent-dir <parent-dir>
```

If you have only the repository URL, clone it to a temporary directory, read this file there, and run the script from that clone with its local template:

```bash
git clone --depth 1 https://github.com/Zach677/Modern.UIKit.git <tmp>/Modern.UIKit
python3 <tmp>/Modern.UIKit/skills/uikit-starter/scripts/create_project.py \
    --repo Mottai --bundle-id org.zaxh.Mottai \
    --template-dir <tmp>/Modern.UIKit/template --parent-dir <parent-dir>
```

When the script ends, delete `<tmp>/Modern.UIKit`. Do this also when the script fails.

The script:

1. Copies the files of `template/` that git tracks, or that are untracked and not ignored, into `<parent-dir>/<repo>`. Build output and local `Developer*.xcconfig` files stay out.
2. Sets the identity and platforms in `Configuration/Base.xcconfig`, renames the workspace to `<repo>.xcworkspace`, and writes a short README. The project, target, and scheme keep the name `App`. Do not rename them.
3. Runs `git init`. Unless `--no-remote`, it creates an empty GitHub repo and adds it as `origin`.
4. Unless `--verify none`, runs `mise install` and the selected `mise` verification. It makes no commit and no push.

The script exits non-zero on any build error, test failure, or warning. Exit code 0 means that the verification passed.

## After Creation

1. Tell the user the local path, the GitHub URL, and the verification result.
2. Before you change code, read `AGENTS.md` in the new app. It holds the project rules.
3. For the first feature, replace the `Root` placeholder in `App/Interface/Root/` and `AppTests/Interface/Root/`. Do not add the feature next to it.
4. Run `mise check` before each commit.
5. Leave the first commit and the push to the user.

## Failures

Stop and report the error. Do not retry with a different name.

- Local destination exists: ask for a different repo name or parent directory. Do not delete or overwrite the directory.
- `gh is not signed in`: ask the user to run `gh auth login`, or ask if they want `--no-remote`. Nothing was created.
- The GitHub repo exists: ask for a different repo name.
- No iOS simulator runtime: ask the user to install one with `xcodebuild -downloadPlatform iOS` or in Xcode > Settings > Components. Then run the verification in the new app, for example `mise build`. Do not create the app again.

If the script stops after it creates the local directory, that directory holds only the new copy. Ask the user before you remove it and run the script again.
