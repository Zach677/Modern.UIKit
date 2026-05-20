---
name: uikit-starter
description: Create a new GitHub repository and local workspace from the `Zach677/Modern.UIKit` template, or inspect an existing iOS repo and guide adoption of the Modern.UIKit baseline with minimal user burden. Use when starting a new UIKit iOS project, bootstrapping through `gh`, or evaluating whether an existing SwiftUI/Tuist/Xcode repo can adopt this UIKit starter.
---

# UIKit Starter

## Workflow

1. Decide the mode with as little user burden as possible:
   - If the target GitHub repo does not exist, use fresh-create mode.
   - If the target GitHub repo exists but is not local, clone it first, then use adopt-existing mode.
   - If a local repo already exists, use adopt-existing mode.
   - If the repo uses SwiftUI or Tuist, use migration-assisted mode and ask only the blocking questions surfaced by the adoption plan.
2. Collect the minimum inputs for fresh-create mode:
   - internal project name, for example `ShelfMusic`
   - optional display name, for example `Shelf Music`
   - GitHub repo name (`owner/repo` or `repo`)
   - bundle identifier if the default `com.example.*` value is not acceptable
   - Apple Developer Team ID if the generated app should commit a shared signing identity
   - Swift language mode: `5.0` by default, or `6.0` for projects that want stricter compiler checks from day one
   - verification level: `build` by default, `test` for stronger validation
3. Run `scripts/create_project.py` for fresh repos, or `scripts/adopt_existing.py` for existing repos.
4. Review the resulting path, adoption plan, and verification output before claiming success.

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
  --development-team S56VW4D8X4 \
  --swift-version 6.0 \
  --visibility private \
  --parent-dir ~/Developer \
  --verify build
```

### Adopt-existing mode

- Use this mode when the repo already exists locally or on GitHub.
- Start by cloning the existing repo if there is no local checkout yet; do not recreate it from the template.
- Run the adoption analyzer before asking the user migration questions:

```bash
python3 scripts/adopt_existing.py \
  --repo-path ~/Developer/CapArt \
  --format text
```

- The analyzer is read-only unless `--apply` is passed. It detects Xcode projects, workspaces, Tuist manifests, SwiftUI entry points, UIKit lifecycle files, app targets, test targets, bundle identifiers, dirty worktrees, and existing Modern.UIKit DevKit surfaces.
- Ask only the questions listed in `Recommended Questions`; do not ask for values that can be preserved from the existing repo.
- Use `Scenario` and `Recommended Next Actions` to adapt to the user's actual goal; do not force every repo toward the same end state.
- Preserve git history, remotes, bundle identifiers, signing settings, app source, resources, and product-specific docs by default.
- First-slice automation focuses on existing UIKit/Xcode repos. SwiftUI and Tuist repos are migration-assisted: generate the plan, resolve the blocking decisions, and avoid pretending the migration is a simple scaffold rename.
- For Tuist repos, preserve the manifest as source of truth when repo guidance says so; map compatible baseline ideas into existing Tuist/mise commands instead of adding a parallel Makefile by default.
- Only run `--apply` when the plan is `Status: ready` and `Mode: xcode-adopt`; it adds missing baseline files without overwriting existing files.

Example apply:

```bash
python3 scripts/adopt_existing.py \
  --repo-path ~/Developer/CapArt \
  --apply
```

Scenario guidance:

- `xcode-uikit-baseline-adoption`: apply the additive baseline when the user wants adoption.
- `xcode-swiftui-entry-migration`: clarify whether UIKit is the new architecture direction before changing app entry code.
- `tuist-source-preserving-baseline`: keep Tuist as source of truth and port compatible ideas into existing commands.
- `tuist-swiftui-guided-decision`: respect SwiftUI-first / Tuist-source repo guidance until the user explicitly overrides it.
- `unsupported-repo-shape`: treat the analyzer as discovery output only.

## Input Rules

- `--project-name` is the internal Xcode-facing name. Keep it identifier-safe, for example `ShelfMusic` or `Shelf-Music`.
- `--display-name` is optional. When omitted, the app display name stays exactly the same as `--project-name`; pass it only when the user wants a different marketing name such as a spaced name.
- `--bundle-id` defaults to `com.example.<sanitized-name>` when omitted.
- `--development-team` is optional. Use it for personal or single-team apps that should commit the shared Apple Developer Team ID in `Configuration/Base.xcconfig`; omit it when the generated repo should stay team-neutral and rely on local developer overrides.
- `--swift-version` defaults to `5.0`; use `6.0` when the new project should start in Swift 6 language mode.
- `--verify` defaults to `build`. Use `test` when the user wants stronger validation and the extra runtime is acceptable.
- `--repo` is required and selects the GitHub repository to create.

### scripts/

- `scripts/create_project.py` is the source of truth for scaffold execution.
- `scripts/adopt_existing.py` is the source of truth for existing-repo inspection and adoption planning.
- Do not hand-rename the cloned template first. Let the script perform the rename pass so project paths, schemes, targets, test bundle names, docs, and config files stay aligned.

## Notes

- The skill assumes the template repository is `Zach677/Modern.UIKit` unless the caller overrides it.
- The script rewrites the template placeholder names automatically and removes template-only scaffolding from the generated repo, so the skill should not rely on the checked-in internal names in user-facing conversation.
- Generated repos do not keep fallback branches for missing `xcbeautify` / `prettier`; install those tools as part of the local setup.
- Generated README files include a LookInside setup section for both manual setup and coding-agent setup; treat it as optional developer tooling, not app architecture.
- If the user wants this skill to be auto-discoverable on the current machine, install it under `~/.codex/skills`, preferably via symlink to the repo copy.
