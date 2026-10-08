---
name: uikit-starter
description: Create a new programmatic UIKit app repository for iOS 26 from the `Zach677/Modern.UIKit` GitHub template. Use when the user wants to start a new UIKit app. Not for migrating existing repositories.
---

# UIKit Starter

## Outcome

A new GitHub repository, cloned locally, that builds with `mise build`. The app identity (display name, bundle identifier, team) is set, and template-only files are removed. Nothing is committed or pushed until the user reviews the result.

## Inputs

Ask only for missing values:

- `repo`: GitHub repository name, for example `Mottai`.
- `bundle-id`: for example `org.zaxh.Mottai`.
- `display-name`: optional; defaults to the repo name. Can be non-ASCII, for example `趁鲜`.
- `development-team`: optional Apple Developer Team ID.
- Platforms: iPhone and iPad by default. Pass `--iphone-only` for iPhone only and `--mac-catalyst` to enable Mac Catalyst.
- `verify`: `build` (default), `test`, or `none`.

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

1. Runs `gh repo create --template` and clones the new repo.
2. Sets the identity and platform values in `Configuration/Base.xcconfig`, and renames the workspace to `<repo>.xcworkspace`.
3. Removes the template's community files, CI workflow, skill files, and the `test-tooling` task, and writes a short README. The new repo has no CI; add a workflow when the project needs one.
4. Runs the selected `mise` verification.

The project, target, and scheme keep the fixed name `App`. Do not rename them.

## Report

- The local path and GitHub URL.
- The verification command that ran and its result.
- Next step for the user: review `git status`, then commit and push.

If `gh` is not signed in, the repo already exists, or verification fails, stop and report the error. Do not retry with different names.
