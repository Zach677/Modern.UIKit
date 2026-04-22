---
name: uikit-starter
description: Create a new GitHub repository and local workspace from the `Zach677/Modern.UIKit` template, then rename the Xcode project, targets, schemes, source folders, test bundle, bundle identifiers, and template docs so the result is ready to build as a fresh UIKit app. Use when starting a new UIKit iOS project from the Modern.UIKit template, bootstrapping a repo without manual clone-and-rename work, or scaffolding a new app through `gh` and local project rewrites.
---

# UIKit Starter

## Workflow

1. Collect the minimum inputs:
   - internal project name, for example `ShelfMusic`
   - optional display name, for example `Shelf Music`
   - GitHub repo name (`owner/repo` or `repo`) if a remote repo should be created
   - bundle identifier if the default `com.example.*` value is not acceptable
   - verification level: `build` by default, `test` for stronger validation
2. Prefer GitHub-backed mode when `gh auth status` succeeds and the user wants a real repository.
3. Use local-copy mode only for smoke tests, dry runs, or when the user explicitly does not want GitHub repo creation.
4. Run `scripts/create_project.py` with the chosen arguments.
5. Review the resulting path and verification output before claiming success.

## Modes

### GitHub-backed mode

- Default mode.
- Uses `gh repo create --template Zach677/Modern.UIKit --clone`.
- Best when the user wants a new remote repo plus a local working copy.
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
  --visibility private \
  --parent-dir ~/Developer \
  --verify build
```

### Local-copy mode

- Uses the local template checkout directly.
- Best for smoke tests, offline iteration, or validating the scaffold logic without creating a remote GitHub repo.

Example:

```bash
python3 scripts/create_project.py \
  --project-name ShelfMusic \
  --display-name "Shelf Music" \
  --destination /tmp/shelf-music \
  --local-template-path /Users/star/Developer/zach-repo/No-StoryBoard \
  --verify test
```

## Input Rules

- `--project-name` is the internal Xcode-facing name. Keep it identifier-safe, for example `ShelfMusic` or `Shelf-Music`.
- `--display-name` is optional and should only be used when the user wants a spaced marketing name.
- `--bundle-id` defaults to `com.example.<sanitized-name>` when omitted.
- `--verify` defaults to `build`. Use `test` when the user wants stronger validation and the extra runtime is acceptable.
- `--repo` selects GitHub-backed mode.
- `--destination` plus `--local-template-path` selects local-copy mode.

### scripts/
- `scripts/create_project.py` is the source of truth for scaffold execution.
- Do not hand-rename the cloned template first. Let the script perform the rename pass so project paths, schemes, targets, test bundle names, and config files stay aligned.

## Notes

- The skill assumes the template repository is `Zach677/Modern.UIKit` unless the caller overrides it.
- The script rewrites the current template markers automatically, so the skill should not rely on the old `No-StoryBoard` name in user-facing conversation.
- If the user wants this skill to be auto-discoverable on the current machine, install it under `~/.codex/skills`, preferably via symlink to the repo copy.
