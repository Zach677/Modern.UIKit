---
name: uikit-starter
description: Create a new GitHub repository and local workspace from the `Zach677/Modern.UIKit` template, then rename the Xcode project, targets, schemes, source folders, test bundle, bundle identifiers, and starter docs so the result is ready to build as a fresh UIKit app. Use when starting a new UIKit iOS project from the Modern.UIKit template or bootstrapping a new app through `gh`.
---

# UIKit Starter

## Workflow

1. Collect the minimum inputs:
   - internal project name, for example `ShelfMusic`
   - optional display name, for example `Shelf Music`
   - GitHub repo name (`owner/repo` or `repo`)
   - bundle identifier if the default `com.example.*` value is not acceptable
   - Swift language mode: `5.0` by default, or `6.0` for projects that want stricter compiler checks from day one
   - verification level: `build` by default, `test` for stronger validation
2. Use GitHub-backed mode; local-copy mode is no longer a supported workflow.
3. Run `scripts/create_project.py` with the chosen arguments.
4. Review the resulting path and verification output before claiming success.

## Mode

### GitHub-backed mode

- Default mode.
- Uses `gh repo create --template Zach677/Modern.UIKit --clone`.
- Renames the root `.xcodeproj`, `.xcworkspace`, shared scheme, and `.xctestplan` along with the source and test folders.
- Rewrites the starter docs so the generated repo describes the new app instead of the template itself.
- The generated repo expects `xcbeautify` on `PATH` and `prettier` available through `npx` for the standard DevKit flows.
- The generated repo does not link LookInside by default; its docs describe LookInside as optional local developer tooling.
- If the user asks to configure LookInside, install or verify the local app and CLI, but do not add committed `LookInsideServer` runtime wiring unless they explicitly request shared debug tooling.
- Run a quick preflight first:

```bash
gh auth status
gh repo view Zach677/Modern.UIKit
```

Example:

```bash
python3 scripts/create_project.py \
  --project-name ShelfMusic \
  --display-name "Shelf Music" \
  --repo Zach677/shelf-music \
  --bundle-id com.zach.shelfmusic \
  --swift-version 6.0 \
  --visibility private \
  --parent-dir ~/Developer \
  --verify build
```

## Input Rules

- `--project-name` is the internal Xcode-facing name. Keep it identifier-safe, for example `ShelfMusic` or `Shelf-Music`.
- `--display-name` is optional and should only be used when the user wants a spaced marketing name.
- `--bundle-id` defaults to `com.example.<sanitized-name>` when omitted.
- `--swift-version` defaults to `5.0`; use `6.0` when the new project should start in Swift 6 language mode.
- `--verify` defaults to `build`. Use `test` when the user wants stronger validation and the extra runtime is acceptable.
- `--repo` is required and selects the GitHub repository to create.

### scripts/

- `scripts/create_project.py` is the source of truth for scaffold execution.
- Do not hand-rename the cloned template first. Let the script perform the rename pass so project paths, schemes, targets, test bundle names, docs, and config files stay aligned.

## Notes

- The skill assumes the template repository is `Zach677/Modern.UIKit` unless the caller overrides it.
- The script rewrites the template placeholder names automatically and removes template-only scaffolding from the generated repo, so the skill should not rely on the checked-in internal names in user-facing conversation.
- Generated repos do not keep fallback branches for missing `xcbeautify` / `prettier`; install those tools as part of the local setup.
- Generated README files include a LookInside setup section for both manual setup and coding-agent setup; treat it as optional developer tooling, not app architecture.
- If the user wants this skill to be auto-discoverable on the current machine, install it under `~/.codex/skills`, preferably via symlink to the repo copy.
