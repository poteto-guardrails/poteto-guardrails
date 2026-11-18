---
name: setup-checks
description: Sets up a project's quality checks. Surveys linting, formatting, type-checking and tests, shows a plain-English health card, recommends only what the project needs from its stack's standard tools, and sets it up after the user approves. Use when the user runs /setup-checks, or agrees to set up checks after Claude recommended it (the session start lists checks as NOT CONFIGURED, or a change needs a test and the project has no test runner).
---

# Setup checks

Goal: give the project the checks it actually needs, and wire them into the guardrails so they run automatically. That means a linter and a formatter, a type-checker where the code has types, and tests where there's logic worth testing. Not every project needs all four.

**Who you're talking to.** Assume the user isn't familiar with testing tooling. Explain each tool in one plain sentence the first time you mention it. Recommend; don't quiz them on choices they can't judge.

**Separate approvals.** Setting up tools (step 3), changing the project's existing code (step 5) and changing CI (step 6) each need their own yes. A yes covers only what you listed. It never covers changing existing source files, weakening a check, or anything outside the plan.

**Stay on setup.** This skill sets up checks. It doesn't refactor, restructure or "improve" the project.

## 0. Before you start

- **Git is required for setup.** It's how the user can undo the whole setup in one step, and outside git the stop gate runs the full check on every turn, even turns that change nothing. If the folder isn't a git repository, recommend `git init` and a first commit, and stop until the user decides. If it stays outside git, do steps 1 and 2 only.
- **Start from a clean tree.** If there are uncommitted changes, ask the user to commit them first, so setup lands as its own reviewable change. You may offer to make that commit. If they want you to:
  - list every file it would include;
  - flag anything that looks like a secret (`.env` files, keys, tokens, credentials) or generated output, and leave those out unless the user says otherwise;
  - commit only on its own yes, separate from any setup approval.
- **Unattended runs.** If nobody can answer, do steps 1 and 2 only, and put the health card under **Not passing / not run**.

## 1. Survey (read-only)

Change nothing in this step.

- **Stack**: the main languages (by file count), the package manager (npm, pnpm, Yarn, Bun, pip, Poetry, uv, Cargo, Go modules, Gradle…, from lockfiles and config), and whether it's a monorepo or workspace. In a monorepo, ask which package or packages to set up.
- **Kind of code**:
  - Does it have logic worth testing: code that calculates, parses, transforms or decides?
  - Is it only docs or config?
  - Does it run inside another program or on a device (a plugin loaded by a host app, MicroPython or other firmware)? If so, its imports won't resolve on this machine.
- **Existing tools**: config files for linters, formatters, type-checkers and test runners, plus the scripts in `package.json`, `pyproject.toml`, a `Makefile`, `build.gradle` and so on.
- **Tests**: how many test files there are and which runner they use.
- **CI**: any system, not only GitHub and GitLab: `.github/workflows/`, `.gitlab-ci.yml`, `bitbucket-pipelines.yml`, `azure-pipelines.yml`, `.circleci/`, a `Jenkinsfile` and so on.
- **Guardrails**: the current values in `.claude/guardrails.env`, if the file exists.
- **Baseline**: if check commands already exist, first read what each one runs. Run it only if it's safe, without fixing anything. Safe means:
  - it needs no network, database, credentials or running service;
  - it writes nothing outside the project;
  - it has no `--fix`, `--write`, migrate or deploy step.

  Note pass or fail, with error counts. Mark anything you didn't run as "not run", with the reason. This tells everyone which failures were already there.

## 2. Health card

Show it like this, with one plain line per row:

```
Project: <name> (<stack>, <package manager>)

Undo point   ✓ git, all committed   lets you undo the whole setup in one step
Linter       ✗ none                 finds likely bugs and bad patterns
Formatter    ✗ none                 keeps code layout consistent automatically
Type-check   ✓ tsc (not run)        catches wrong-kind-of-data mistakes before running
Tests        ✗ none                 prove the code does what it should, and keeps doing it
CI           ✗ none                 runs the checks on every push, even without Claude
Guardrails   ✗ not wired            makes Claude run these checks on every change

Today's code: type-check FAILS with 3 errors (already there before this session)
```

Mark a row "— not needed" when the project doesn't need it (see step 3), with the reason.

If every needed row is ✓ and the baseline passes, say so. Make sure the guardrails are wired (step 6), then stop.

## 3. Recommend (first approval)

Fill **only the gaps**. Never replace or remove a tool the project already uses. An existing Biome, Jest, mypy, Black, Flake8 or ktlint setup stays. Use the project's existing config locations and formats before creating new files (for example, Ruff settings go in `pyproject.toml` if it exists).

What the project needs depends on its code:

- **Docs or config only**: no linter, type-checker or tests. Say it doesn't need them.
- **Runs inside a host program or on a device**: linter and formatter only. Explain that type-check and tests would fail here, because the host's modules don't exist on this machine. Test pure logic only if it already lives apart from the host's modules.
- **Type-checker**: only where the code has types: TypeScript, or Python with type hints. Not plain JavaScript. For untyped Python, mention it as an option for later.
- **Tests**: only where there's logic worth testing.

Standard choices:

| Stack | Linter | Formatter | Type-check | Tests |
|---|---|---|---|---|
| TypeScript / JavaScript | ESLint (`@eslint/js` + `typescript-eslint` recommended) | Prettier | `tsc --noEmit` (TypeScript only) | Vitest (keep Jest if the project uses it) |
| Python | Ruff | Ruff format | Pyright, basic mode (keep mypy if the project uses it; never both) | pytest |
| Go | `go vet` | `gofmt` | (compiler) | `go test` |
| Rust | Clippy | rustfmt | (compiler) | `cargo test` |
| Kotlin / Android | ktlint, plus Android Lint for Android apps | ktlint (no second formatter) | (compiler) | JUnit via Gradle |
| Shell scripts | ShellCheck | shfmt | — | bats, only if there's real logic |

If the project uses Biome, it is the linter and formatter; don't add ESLint or Prettier. For a stack that isn't listed, propose its standard tools and say you're less certain.

Then present the plan:

- what will be added, with one sentence each on what it does for them;
- every file that will be created or changed. Mark the ones that will trigger an approval prompt; the `ask` rules in `~/.claude/settings.json` say which (typically lint, format, type-check and CI config, and `.claude/**`). Tell the user: "If a prompt appears for a file that isn't on this list, something unplanned is happening. Answer no. Package installs and other shell commands change files without a prompt, so the final report also checks every change against this list.";
- the dev dependencies that will be installed (dev only; nothing ships with the app);
- the fast check that will run after each edit (a few seconds), and the full check that will run before a turn can finish;
- what this yes doesn't cover: changing existing code. That's a separate question after setup (step 5);
- a note to run setup in a normal permission mode, because in bypass-permissions mode the approval prompts don't appear.

End with: **"Set this up? (yes / only some of it / no)"**, then stop and wait.

On a no, or a no to part of it, offer to record that so you stop recommending it: in `.claude/guardrails.env`, leave each declined check empty with a comment saying the user declined it (format: step 6). Only those checks; the rest can still be recommended later.

## 4. Set up tooling (after a yes)

Change only the files the plan listed. Don't touch existing source files in this step. Do the steps in order, and verify each one before moving on.

1. **Install** the tools as dev dependencies with the project's own package manager, so the lockfile records exact versions. In a monorepo, install shared tools once at the workspace root, the way that workspace does it, not in every package. → verify: the lockfile changed and the tool runs (`<tool> --version`).
2. **Configure** each tool with its standard preset at a moderate level: ESLint and `typescript-eslint` `recommended`, Ruff's defaults, Pyright `basic`. Never a strict mode on an existing codebase. The only ignores allowed are build output, vendored and generated folders; list them. → verify: each tool runs on the project. Findings in existing code are expected; step 5 handles them.
3. **Add scripts** so a human can run everything with one command: `lint`, `format` (rewrites files; for humans and explicit requests only), `format:check` (reports only), `typecheck`, `test`, and `check`. `check` runs `lint`, `format:check`, `typecheck`, `test` and the project's existing build step if it has one, in that order, stopping at the first failure.

   **`check` must never change files**: use the formatter's check mode and the linter without `--fix`. The pack doesn't record a check that modifies files, and a check that rewrites code hides problems instead of reporting them. Put scripts where the ecosystem keeps them: `package.json` scripts, an existing `Makefile` or task runner. If the project has nowhere to put scripts, don't add a task runner just for this. Use the chained command directly in `FULL_CHECK_CMD` instead. → verify: `check` runs, and `git status` is the same before and after it.
4. **First real tests** (only if step 3 said the project needs tests and it has none):
   - Write as many tests as the project's most important existing logic needs. One meaningful test beats three shallow ones.
   - Each test feeds a real input and checks a specific expected result. Never write a test that can't fail ("doesn't crash", "is defined", "returns something").
   - Each test calls the logic it's named for directly, so the result can only come from that code, not from a mock, a default or a different path.
   - If nothing is testable in isolation, write one smoke test that loads the main module or starts the app and checks one visible result.
   - Show the user each test as one plain line: "given X, expect Y".

   → verify: the tests pass. Then, for each test, temporarily change the expected value in **your own new test**, run it, confirm it fails for that reason, restore it, and confirm it passes again. This proves the test runs and its check counts. Never edit the user's existing code to demonstrate a test.

## 5. Existing problems (second approval)

New tools usually find problems in code that was already there. The yes in step 3 didn't cover changing existing code, so ask again before touching any existing source file.

1. **Report** what the checks found, grouped by tool and rule, with the files that have the most. Say in plain words which findings are layout only and which may be real bugs.
2. **Offer the format pass on its own**: run the formatter and the linter's safe auto-fixes. The formatter changes layout only; safe fixes make small mechanical edits (such as removing unused imports) that aren't meant to change behaviour. Say how many files it will touch, and recommend committing it separately (for example "style: apply formatter") so it doesn't mix with real changes. Run it only on a yes. Don't commit unless asked. If they decline, leave `format:check` out of the `check` script and `FAST_CHECK_CMD` for now, and list it as a to-do. Otherwise every later edit would reformat whole files.
3. **For what's left**, recommend based on what the findings are, not how many:
   - **Fix them**, as a separate approved change. Recommend this for anything that may be a real bug.
   - **Relax a specific rule** in the config (never per line), for style-only rules, each with its own approval. For each rule, tell the user:
     - its exact name;
     - what it detects;
     - whether it can catch bugs or security problems;
     - what relaxing it means in practice;
     - the exact config change.

     For example: "Turn off Ruff `E741`: it only flags confusing variable names like `l`, so no bug or security checks are lost." "It causes too many errors" is not a reason. If you can't say confidently that a rule is style-only, don't offer to relax it. List each relaxed rule in the report as a to-do. Rules that catch security problems, likely bugs or type errors get fixed or reported, never relaxed.
   - **Leave them for now**: the full check stays unwired (step 6).

   Never add per-line suppressions or skip tests. The guardrails block most of these anyway.
4. **Pre-existing type errors and failing tests**: report them. Don't fix them without asking; they may be real bugs that need the user's judgment.

## 6. Wire the guardrails

Create or update `.claude/guardrails.env` from `~/.claude/guardrails/templates/guardrails.env`. Before the approval prompt appears, tell the user it lets Claude run these checks automatically. Do these in order. The repo's `guardrails.env` is part of the tree the stop gate checks, so `check.py` must be the last thing you do.

**Comments go on their own line**, above the key they explain. Never put a note after `=` (`FULL_CHECK_CMD= # reason`): the hooks take everything after `=` as the command, and the shell runs `# reason` as a no-op that always passes, so the check would look verified when it isn't. An empty check is written as `KEY=` with nothing after it.

1. Add `.claude/verification-runs/` to `.gitignore`.
2. Set the fast check, even if the full check can't pass yet, so feedback after each edit starts now:
   - `FAST_CHECK_CMD`: lint plus format check on one `{file}`, using the package manager's runner. For example, `npx eslint --max-warnings=0 {file} && npx prettier --check {file}`, or `uv run ruff check {file} && uv run ruff format --check {file}`.
   - `FAST_CHECK_GLOBS`: the source file types (for example `*.ts,*.tsx` or `*.py`). Required: without it the fast check never runs.
   - Don't put quotes around `{file}`; the hook quotes it.
   - For any check marked "not needed" in step 3, add a comment saying so and why (for example `# No tests: code runs inside a host app`), so later sessions don't keep recommending it.
3. Run the `check` command directly.
   - If it passes, set `FULL_CHECK_CMD` to it.
   - If it fails, leave `FULL_CHECK_CMD` empty, with a comment saying why (for example `# FULL_CHECK_CMD left empty: 3 existing test failures to fix first`). Tell the user plainly that the full check isn't enforced yet and why: otherwise the stop gate would send every future turn back to fix old problems. Also tell them that until it's wired, every turn that changes files will end with "files changed but FULL_CHECK_CMD isn't configured. This work is unverified." That's expected, not a new problem.
4. **CI (ask separately).** Explain that CI is the final safety net, because it runs even when nobody uses Claude. If the project already has CI, offer to add the `check` command to it; never create a second pipeline. If it has none and the remote is GitHub or GitLab, offer a workflow that runs `check` on every push and pull request. Change CI only on a yes.
5. If `FULL_CHECK_CMD` is set, run `python3 ~/.claude/guardrails/tools/check.py` and quote its last line.

## 7. Report

- Run `git status --porcelain` and compare every changed or new file with the plan's list. Name any file that wasn't on the list and ask the user whether to keep it. Don't revert anything yourself.
- The health card again, now showing what's ✓ and what's "not needed".
- What was added, and the one command the user can run themselves (for example `npm run check`, or `python3 ~/.claude/guardrails/tools/check.py`).
- What happens automatically from now on: the fast check after every edit, the full check before a turn can finish (if wired), and a test for every behaviour change.
- What's left to do:
  - relaxed rules;
  - if the format pass was declined: formatting isn't enforced, that's why, and it can be turned on after a format pass;
  - pre-existing failures;
  - a full check left unwired, and why, and that the "unverified" warning will appear until it's wired;
  - checks skipped as not needed, and why;
  - CI, if it was declined.
