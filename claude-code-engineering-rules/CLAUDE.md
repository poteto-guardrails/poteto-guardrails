# How to work in this repository

Hooks in `.claude/settings.json` enforce the hard rules (checks after edits, a test gate before you finish, no new suppressions, protected config). This file covers only what needs judgment.

## Before coding
- State your assumptions. If the request has more than one reasonable reading, name them and ask. Don't pick one silently.
- If no one is available to answer (an unattended or scheduled run), take the most conservative reading, write it down under **Assumptions**, and avoid anything that can't be undone.
- For multi-step work, write a short plan where each step has its own check: `1. <step> → verify: <command or observation>`.
- Bug fix: first write a test that reproduces the bug and fails, then make it pass.

## Writing code
- Write the least code that solves the request. No unrequested features, configurability, single-use abstractions or handling for impossible cases.
- Every changed line must trace to the request. Clean up only what your own change made unused.
- Match the existing style (formatting, naming, file layout). Don't match existing *patterns* that are listed in `.claude/rules/bans.md` or that the checks reject. New code follows the intended pattern, not the nearest example.
- Fix the root cause. Don't use timers, retries, polling, casts or fallbacks to make a symptom disappear.
- Don't write a comment that justifies a shortcut. If the right fix is out of reach, stop and report it.

## Guardrails belong to humans
- Don't edit lint, type-check, CI, hook or settings configuration. Edits there require approval for a reason.
- If a check seems wrong, or you can't pass it without a suppression, stop and explain under **Not passing**.
- If you see a mistake that a check could have caught (yours or the codebase's), propose the check under **Guardrail candidates**. Don't build it unless asked; humans use `/add-guardrail` for that.
- Never merge, deploy or force-push.

## Verifying
- User-visible change: use the `verify-feature` skill, refer to features by their names in `docs/feature-map.md`, and keep the evidence.
- Never say a check passed unless you ran it and saw it pass.

## Final report (every task that changed files)
- **Done**: what changed, in one or two lines.
- **Checks**: each command run and its result.
- **Not passing / not run**: with reasons.
- **Assumptions**
- **Noticed, not touched**: debt, dead code or bugs outside the task's scope.
- **Guardrail candidates**: a recurring mistake, plus the deterministic check that would prevent it.
