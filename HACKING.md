# Developing Modern.UIKit

Read ["Contributing to Modern.UIKit"](CONTRIBUTING.md) before you open a pull
request.

## Template Maintenance

- `AGENTS.md` is copied into every generated app. Keep it about the app, not
  about this template repository.
- Files that describe only the template are listed in `TEMPLATE_ONLY_PATHS`
  in `skills/uikit-starter/scripts/create_project.py`. When you add such a
  file, add it to that list.
- When the contribution flow changes, keep `CONTRIBUTING.md`, `AI_POLICY.md`,
  and `.github/` aligned.
- Run `mise test-tooling` after you change the skill scripts.

## Checks

```bash
mise build
mise test
mise test-tooling
mise validate-xcstrings
```
