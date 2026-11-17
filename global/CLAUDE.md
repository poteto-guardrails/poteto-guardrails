# How to work (global engineering rules)

Hooks in `~/.claude/settings.json` enforce the hard rules: checks after edits, a full-check gate before you finish, no new suppressions or skipped or focused tests, and protected config. Check commands come from `~/.claude/guardrails.env`, overridden per repo by `<repo>/.claude/guardrails.env`. The session start message lists which checks are configured. This file covers only what needs judgment. A repo's own `CLAUDE.md` adds to these rules.

## Before coding
- State your assumptions. If the request has more than one reasonable reading, name them and ask. Don't pick one silently.
- If no one is available to answer (an unattended or scheduled run), take the most conservative reading, write it down under **Assumptions**, and avoid anything that can't be undone.
- For multi-step work, write a short plan where each step has its own check: `1. <step> → verify: <command or observation>`.
- Bug fix: first write a test that reproduces the bug and fails, then make it pass.

## Writing code
- Write the least code that solves the request. No unrequested features, configurability, single-use abstractions or handling for impossible cases.
- Every changed line must trace to the request. Clean up only what your own change made unused.
- Match the existing style (formatting, naming, file layout). Don't match existing *patterns* that are listed in the repo's `.claude/rules/bans.md` or that the checks reject. New code follows the intended pattern, not the nearest example.
- Fix the root cause. Timers, retries, polling, casts and fallbacks are fine when they're the design: backoff after transient network failures, debouncing input, polling a system that has no events. They're not fine when they hide a problem you haven't understood. If you're reaching for one to make a symptom go away, find the cause first.
- Don't write a comment that justifies a shortcut. If the right fix is out of reach, stop and report it.

## Guardrails belong to humans
- Don't edit lint, type-check, CI, hook or settings configuration (including `guardrails.env` and anything under `~/.claude/guardrails/`). Edits there require approval for a reason.
- If a check seems wrong, or you can't pass it without a suppression, stop and explain under **Not passing**.
- If you see a mistake that a check could have caught (yours or the codebase's), propose the check under **Guardrail candidates**. Don't build it unless asked; humans use `/add-guardrail` for that.

## Destructive and outward-facing commands
- Never run a command that destroys work on your own initiative: recursive or forced `rm`, `find -delete`, `git reset --hard`, `git clean -f`, `git checkout -- <path>`/`git checkout .`/`git checkout -f`, `git restore`, `git switch --discard-changes`, `git stash drop`/`clear`, `git branch -D`, or a force-push (`--force`, `-f`, `--force-with-lease`). This covers any equivalent the list misses. When one is needed, stop and give the user the exact command to run themselves.
- Run one only when the user explicitly asks you to run that command in the current request. The approval covers that single run: it never carries over to later commands, requests or sessions.
- Merge, deploy or publish only when the user explicitly asks for it in the current request. Never as a step you decided on yourself.

## Project checks
- In a git repository, read the session start message. If it lists `FULL_CHECK_CMD` or `FAST_CHECK_CMD` under NOT CONFIGURED, offer once per session to set them up. Make the offer in one or two lines at the start of your first reply, then fully answer or do what was asked in that same reply. The offer never replaces the answer, and you don't wait for a reply to it. Don't offer if the repo's `.claude/guardrails.env` already exists and deliberately leaves a check empty.
- Before offering, look at what the project already uses: `package.json` scripts, `pyproject.toml`, `Makefile`, `Cargo.toml`, `go.mod`, CI workflows. Propose concrete commands (full check: lint, type-check, tests, build; fast check: lint plus format check on one `{file}`). Never invent tools the project doesn't have.
- If the user accepts, create `<repo>/.claude/guardrails.env` from `~/.claude/guardrails/templates/guardrails.env` with only the keys you're setting. Then run `python3 ~/.claude/guardrails/tools/check.py` and report its result. If it fails on existing code, report that rather than weakening the command.
- Unattended runs: don't set anything up. Note the missing checks under **Not passing / not run**.

## Verifying
- Before your final report, run `python3 ~/.claude/guardrails/tools/check.py` and quote its last line. The stop gate accepts that result if nothing changed afterwards. If it prints a WARNING about excluded paths, report it.
- User-visible change: use the `verify-feature` skill and quote the runner's result line for each scenario. A scenario the driver doesn't support (`NOT RUN`) goes under **Not passing / not run**; it doesn't block finishing.
- Never say a check passed unless you ran it and saw it pass.

## Final report (every task that changed files)
- **Done**: what changed, in one or two lines.
- **Checks**: the `check.py` summary line, plus any other command you ran and its result.
- **Not passing / not run**: with reasons.
- **Assumptions**
- **Noticed, not touched**: debt, dead code or bugs outside the task's scope.
- **Guardrail candidates**: a recurring mistake, plus the deterministic check that would prevent it.
