# Optional extra: `/setup-checks`

**An add-on for the [global variant](../../global/). Your agent notices when a project has no linting or tests, recommends fixing that, and sets it up for you once you say yes.**

The base guardrails *enforce* checks, but only once a project has them. On a project with no linter or tests, the per-edit check and the full-check gate have nothing to run, so they sit idle. That's usually the project that needs them most. This add-on closes the gap. It's written for people who don't want to become experts in testing tooling: the agent explains everything in plain words and recommends the standard choice instead of quizzing you.

## What it adds

| Part | File | What it does |
|---|---|---|
| **The `/setup-checks` skill** | `skills/setup-checks/SKILL.md` | A guided pre-flight. **Survey** the project without changing anything. Show a plain-English **health card** (linter, formatter, type-check, tests, CI, guardrails). **Recommend** only what's missing, from each stack's standard tools, and list every file it would touch. **Wait for your yes**, then install the tools, add a `check` command, write a few real first tests, and wire up `.claude/guardrails.env`. Changing existing code and changing CI each need their own separate yes |
| **Rule changes** | `CLAUDE.md.patch` | **Tests:** a bug fix or an observable behaviour change gets a test written first, if the project has a test runner. **Pre-flight:** before the first edit, run the full check and flag failures that were already there, keeping them separate from new ones. **Recommendation:** suggest `/setup-checks` once per session when a project lacks checks, but only during real code changes, never for questions |
| **Hook fixes and tests** | `guardrails.patch` | **Bug fix (recommended for everyone):** `FULL_CHECK_CMD= # note` used to count as a *passing* check, because the shell ran the comment as a no-op. Any `*_CMD` value starting with `#` is now treated as empty. **Nudge:** the "FULL_CHECK_CMD isn't configured" warning adds "Run /setup-checks to set it up", except in repos that deliberately left it empty. **Tests:** 6 new tests, so the suite goes from 53 to 59. **Version:** reports `4.1.2-global.1+setup-checks.1` at session start, so you can tell the extra is installed. Saved verification records from before are ignored once, and checks run fresh |

The stack defaults it recommends (it never replaces a tool you already use):

| Stack | Linter | Formatter | Type-check | Tests |
|---|---|---|---|---|
| TypeScript / JavaScript | ESLint (+ `typescript-eslint`) | Prettier | `tsc --noEmit` (TypeScript only) | Vitest (keeps Jest if present) |
| Python | Ruff | Ruff format | Pyright, basic mode (keeps mypy if present) | pytest |
| Go | `go vet` | `gofmt` | (compiler) | `go test` |
| Rust | Clippy | rustfmt | (compiler) | `cargo test` |
| Kotlin / Android | ktlint, plus Android Lint for apps | ktlint | (compiler) | JUnit via Gradle |
| Shell | ShellCheck | shfmt | — | bats, only for real logic |

It also skips checks a project doesn't need: no type-checker for plain JavaScript, and no tests for docs-only projects or code that only runs inside a host app or on a device.

## Requirements

- The **[global variant](../../global/)** installed first (`~/.claude/guardrails/`, `~/.claude/CLAUDE.md`). The add-on assumes those paths. It isn't packaged for the per-project `local/` pack.
- `patch` and `python3` on PATH.

## Install

### Ask Claude

Paste this into Claude Code:

```text
Install the optional /setup-checks extra from
https://github.com/poteto-guardrails/poteto-guardrails
(folder extras/setup-checks). The global variant is already installed.

1. Clone the repository to a temporary folder.
2. Back up ~/.claude/CLAUDE.md to ~/.claude/CLAUDE.md.bak-setup-checks and
   ~/.claude/guardrails/ to ~/.claude/guardrails.bak-setup-checks/.
3. Apply extras/setup-checks/CLAUDE.md.patch to ~/.claude/CLAUDE.md (patch -p1
   from ~/.claude). My file may contain extra sections of my own: keep them
   exactly as they are. If a hunk doesn't apply cleanly, stop and show me why.
   Show me the merged file before saving.
4. Copy extras/setup-checks/skills/setup-checks/SKILL.md to
   ~/.claude/skills/setup-checks/SKILL.md. Don't overwrite an existing file
   without showing me the diff.
5. Apply extras/setup-checks/guardrails.patch inside ~/.claude/guardrails/
   (patch -p1). Stop if it doesn't apply cleanly, and show me each change
   before saving.
6. Run python3 ~/.claude/guardrails/tests/test_guardrails.py and quote the
   last line. It must say "Ran 59 tests" and end with OK. If anything fails,
   restore both backups and tell me.
7. Tell me to restart Claude Code and check that /setup-checks is listed.
```

### By hand

```bash
git clone https://github.com/poteto-guardrails/poteto-guardrails.git
X="$PWD/poteto-guardrails/extras/setup-checks"

# Back up
cp -p ~/.claude/CLAUDE.md ~/.claude/CLAUDE.md.bak-setup-checks
cp -rp ~/.claude/guardrails ~/.claude/guardrails.bak-setup-checks

# Dry run first: both must apply cleanly
(cd ~/.claude && patch -p1 --dry-run < "$X/CLAUDE.md.patch")
(cd ~/.claude/guardrails && patch -p1 --dry-run < "$X/guardrails.patch")

# Apply
(cd ~/.claude && patch -p1 < "$X/CLAUDE.md.patch")
(cd ~/.claude/guardrails && patch -p1 < "$X/guardrails.patch")
mkdir -p ~/.claude/skills/setup-checks
cp -n "$X/skills/setup-checks/SKILL.md" ~/.claude/skills/setup-checks/

# Verify
python3 ~/.claude/guardrails/tests/test_guardrails.py      # expect: Ran 59 tests ... OK
```

Restart Claude Code. `/setup-checks` should be listed.

**If `CLAUDE.md.patch` doesn't apply cleanly**, your `~/.claude/CLAUDE.md` has drifted from the published one: sections of your own, or earlier edits. The patch makes three changes:
- it replaces the "Bug fix" bullet under *Before coding*;
- it adds a sentence to the first bullet of *Guardrails belong to humans*;
- it rewrites *Project checks*.

Make them by hand, or ask Claude to merge them while keeping your own sections. A "succeeded … with fuzz" message means the change applied, but the lines around it didn't match exactly; check the result before you keep it.

**If you only want the bug fix**, apply `guardrails.patch` without the rest. The comment fix works on its own. The warning will then mention `/setup-checks` even though you don't have it, so install the skill too, or ignore that sentence.

## Using it

- **Automatically:** in a project with no checks, the agent mentions `/setup-checks` in a line or two the first time you ask for a code change, then gets on with your task.
- **On demand:** type `/setup-checks` in any project.

Run it in a normal permission mode. In bypass-permissions mode, the approval prompts for config files don't appear. Read the plan it shows you. If an approval prompt appears for a file that isn't on that plan, answer **no**.

**Try it first on throwaway projects:**

| Project | What should happen |
|---|---|
| No checks at all (a small script with a few functions) | Health card, then a plan listing every file, then a wait for your yes. It ends with the full check passing, and `/setup-checks` isn't recommended again |
| A linter but no tests | Keeps the linter and adds only what's missing |
| Existing checks that already fail | The failures are reported as already there, and it asks separately before touching existing code. If you decline, `FULL_CHECK_CMD=` stays empty, with the reason on its own line above it |
| An established toolchain (e.g. Biome and Jest) | Nothing replaced; at most it wires up the guardrails |
| A folder that isn't a git repository | Recommends `git init`, and shows the survey and health card only |
| Code that runs inside a host app | Linter and formatter only; type-check and tests are marked "not needed", with the reason recorded |

## Removing it

```bash
mv ~/.claude/CLAUDE.md.bak-setup-checks ~/.claude/CLAUDE.md
rm -r ~/.claude/guardrails && mv ~/.claude/guardrails.bak-setup-checks ~/.claude/guardrails
rm -r ~/.claude/skills/setup-checks
```

Or reverse just the patches: `patch -p1 -R` with the same file in the same folder.

## Status

- **Review:** drafted with Claude and refined over several external review rounds.
- **Tests:** checked against the real hooks. Behaviour tests failed on the old hooks and pass on the patched ones, and the full suite passes (59 tests).
- **Not yet done:** the throwaway-project trials above, and the pack's live smoke test (S0–S12).
