---
name: uikit-starter
description: Create a new programmatic UIKit app repository for iOS 26 from the `template/` directory of `Zach677/Modern.UIKit`. Use when the user wants to start a new UIKit app. Not for migrating existing repositories.
---

# UIKit Starter

## Outcome

A new local repository with an empty GitHub repository as `origin`, that builds with `mise build`. The app identity (display name, bundle identifier, team) is set. Nothing is committed or pushed until the user reviews the result.

## Inputs

Ask only for missing values:

- `repo`: GitHub repository name, for example `Mottai`.
- `bundle-id`: for example `org.zaxh.Mottai`.
- `display-name`: optional; defaults to the repo name. Can be non-ASCII, for example `趁鲜`.
- `development-team`: optional Apple Developer Team ID.
- Platforms: iPhone and iPad by default. Pass `--iphone-only` for iPhone only and `--mac-catalyst` to enable Mac Catalyst.
- `verify`: `build` (default), `test`, `check`, or `none`.

## Run

```bash
python3 <skill-dir>/scripts/create_project.py \
    --repo Mottai \
    --bundle-id org.zaxh.Mottai \
    --display-name Mottai \
    --development-team ABCDE12345 \
    --iphone-only \
    --parent-dir ~/Developer \
    --verify build
```

The script:

1. Makes a shallow clone of `--template-repo` into a temporary directory, or uses `--template-dir <path-to-template/>` from a local checkout.
2. Copies the files in `template/` that git tracks or that are untracked and not ignored. Build output and local `Developer*.xcconfig` files stay out.
3. Sets the identity and platform values in `Configuration/Base.xcconfig`, renames the workspace to `<repo>.xcworkspace`, and writes a short README.
4. Runs `git init`, then `gh repo create --source . --remote origin` with the selected visibility. This adds `origin` and makes no commit and no push. `--no-remote` skips this step. The new repo has no CI; add a workflow when the project needs one.
5. Runs the selected `mise` verification.

The project, target, and scheme keep the fixed name `App`. Do not rename them.

## Report

- The local path and GitHub URL.
- The verification command that ran and its result.
- Next step for the user: review `git status`, then commit and push.

If `gh` is not signed in, the repo already exists, or verification fails, stop and report the error. Do not retry with different names.
