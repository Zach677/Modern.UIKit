---
name: writing-commit-messages
description: >-
  Writes Git commit messages. Activates when the user asks to write
  a commit message, draft a commit message, or similar.
---

# Writing Commit Messages

Write commit messages that follow commit style guidelines for the project.

## Format

```
<type>: <summary>

<reference issues/PRs/etc.>

<long form description>
```

## Rules

### Subject line

- **Type prefix**: Use exactly one Conventional Commits type:
  `feat`, `fix`, `docs`, `test`, `build`, `ci`, `chore`, `refactor`,
  `perf`, `style`.
- **Type selection**: Choose the type from the actual diff, not the
  branch name or issue title. Use `docs` for documentation-only
  changes, `ci` for GitHub Actions and workflow changes, `build` for
  build-system changes, `chore` for maintenance that is not user-facing,
  `feat` for user-visible functionality, and `fix` for bug fixes.
- **Scope**: Omit scope by default. Use a scope only when it is clearly
  helpful and supported by the diff, such as `docs(readme)` or
  `ci(vouch)`.
- **Summary**: Use imperative mood, no trailing period. Keep the full
  subject line concise, ideally under 72 characters.

### References

- If the change relates to a GitHub issue, PR, or discussion, list
  the relevant numbers on their own lines after the subject, separated
  by a blank line. E.g. `#1234`
- If there are no references, omit this section entirely (no blank
  line).

### Long form description

- Describe **what changed**, **what the previous behavior was**,
  and **how the new behavior works** at a high level.
- Use plain prose, not bullet points. Wrap lines at ~72 characters.
- Focus on the _why_ and _how_ rather than restating the diff.
- Keep the tone direct and technical without no filler phrases.
- Don't exceed a handful of paragraphs; less is more.

## Workflow

- If `.jj` is present, use `jj` instead of `git` for all commands.
- Run a diff to see what changes are present since the last commit.
- Identify the Conventional Commit type from the changed file paths
  and behavior.
- Identify any referenced issues/PRs from the diff context or
  branch name.
- Draft the commit message following the format above.
- Apply the commit
- Don't push the commit; leave that to the user.
