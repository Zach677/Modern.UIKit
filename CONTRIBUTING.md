# Contributing to Modern.UIKit

This document describes the process of contributing to Modern.UIKit. It is
intended for anyone considering opening an **issue**, **discussion**, or
**pull request**.

Modern.UIKit is a personal open-source project and a reusable UIKit starter.
It is intentionally small, workflow-heavy, and agent-oriented. If you want to
request changes, report problems, or submit code, please spend a few minutes
reading this first so the issue tracker stays useful.

## AI Assistance Notice

Modern.UIKit is built for agent-assisted development, so AI-assisted
contributions are welcome. The human submitter still owns the work.

If you materially use AI assistance for a pull request, disclose that in the
pull request and describe the scope, such as documentation cleanup, code
generation, test drafting, or code review.

You are responsible for understanding the submitted change, testing the
affected workflow, and answering follow-up questions without relying on an
agent to explain the work for you. Contributions that look generated but are
not understood, tested, or maintainable may be closed.

Community interactions should be written in your own voice. It is fine to use
tools for spelling or translation help, but do not outsource discussions,
issue reports, or review replies to an agent.

## Quick Guide

### I would like to contribute

The issue tracker is intended to contain actionable work. Pick an open issue
that is already scoped, comment if you need clarification, and open a pull
request when the change is ready.

If you want to work on something that is not already tracked, start with a
discussion first.

### I found a bug or unexpected behavior

First, search existing issues and discussions, including closed ones. Your
problem may already have a workaround, an accepted fix, or a known limitation.

If there is an open issue or discussion that matches your problem, avoid adding
noise such as "+1". Use reactions unless you have new technical evidence,
reproduction steps, logs, or a smaller failing example.

If the problem has not been reported, open an
["Issue Triage" discussion](https://github.com/Zach677/Modern.UIKit/discussions/new?category=issue-triage)
and fill in the template completely. This is the preferred starting point for
starter creation bugs, existing-repo adoption problems, build/test failures,
script issues, and documentation mismatches.

### I have an idea for a feature

Open a
["Feature Requests, Ideas" discussion](https://github.com/Zach677/Modern.UIKit/discussions/new?category=feature-requests-ideas)
before opening an issue or pull request.

Feature ideas often affect the starter contract, generated project shape,
agent workflow, or long-term adoption path. Those trade-offs should be
discussed before implementation.

### I have a question

Open a
["Q&A" discussion](https://github.com/Zach677/Modern.UIKit/discussions/new?category=q-a)
if your topic is not clearly a bug report or feature request.

For example, use Q&A for questions about whether Modern.UIKit fits a specific
repo, how to interpret analyzer output, or how to use the starter with a
particular agent runtime.

### I have already implemented a change

1. If there is an accepted issue for the change, open a pull request and link
   the issue.
2. If there is no issue, open a discussion and link to your branch or patch.
3. Small documentation fixes may be submitted directly, but behavior changes,
   workflow changes, public template contract changes, and migration behavior
   should be discussed first.

## General Patterns

### Issues are Actionable

The Modern.UIKit
[issue tracker](https://github.com/Zach677/Modern.UIKit/issues) is for
actionable items.

Modern.UIKit does not use issues for open-ended support, early feature design,
or migration brainstorming. Use
[discussions](https://github.com/Zach677/Modern.UIKit/discussions) for those
topics. Once a discussion identifies a clear and accepted task, it can become
an issue.

This keeps every issue ready for a maintainer or contributor to work on.

### Pull Requests Implement Accepted Work

Pull requests should normally implement an accepted issue or a clearly
maintainer-approved discussion.

If you open a pull request for a non-trivial behavior change that was not
previously discussed, it may be closed or remain stale. Pull requests are not
the right place to debate starter architecture or migration policy.

### Preserve the Starter Contract

Modern.UIKit is a starter template, not a finished product app. Contributions
should preserve that boundary.

Good changes usually improve one of these areas:

- fresh UIKit app creation;
- existing-repo analysis and adoption safety;
- generated project correctness;
- DevKit build, test, formatting, localization, and license workflows;
- documentation that helps agents and maintainers make safer decisions.

Be careful with changes that make the starter product-specific, add optional
platform complexity by default, introduce personal signing settings, or make a
generated app advertise Modern.UIKit internals after creation.

## Developer Guide

### Local Workflow

Use the top-level Makefile for routine workflows:

```bash
make build
make test
make format-lint
make validate-xcstrings
make scan-license
```

When testing skill behavior, prefer the scripts under
`skills/uikit-starter/scripts/` and include the exact command in the pull
request:

```bash
python3 skills/uikit-starter/scripts/create_project.py \
    --project-name ExampleApp \
    --repo example-app \
    --bundle-id com.example.ExampleApp \
    --verify build
python3 skills/uikit-starter/scripts/adopt_existing.py --repo-path <path>
```

### Pull Request Checklist

Before opening a pull request, make sure the PR includes:

- a short summary of the change;
- a linked issue or discussion for non-trivial work;
- the commands you ran and their results;
- screenshots or before/after notes for UI changes;
- documentation updates when behavior, structure, or workflow changes;
- localization notes when user-facing strings change;
- license or dependency notes when packages or bundled resources change;
- AI assistance disclosure when applicable.

### Documentation Sync

Structural changes must update the relevant docs in the same pull request.
Depending on the change, that may include `README.md`, `AGENTS.md`,
`skills/uikit-starter/SKILL.md`, or tests under `skills/uikit-starter/tests/`.

If the repository behavior changes but the agent-facing contract is left stale,
the contribution is incomplete.

This contribution guide is inspired by the discussion-first flow used by
SubZen and Ghostty.
