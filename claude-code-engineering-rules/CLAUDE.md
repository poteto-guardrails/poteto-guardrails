# Engineering operating principles

These instructions translate Lauren Tan’s presentation **“All Code Is Slop (Except Mine)”** into Claude Code defaults. The central claim is that trust comes from investing in the agent environment—not from more elaborate natural-language rules.

## Primary objective

Increase throughput while maintaining or improving quality. Quality and productivity are not traded off; the environment makes the right thing the easy/default thing.

## Order of preference (inverted pyramid)

When a quality or correctness problem appears, prefer the strongest enforceable solution:

1. **Architecture and API design** that makes the incorrect approach impossible or unnatural.
2. **Deterministic enforcement** (types, compiler, linters, formatters, dependency-boundary checks, tests, CI).
3. **Runtime and formal verification** appropriate to risk.
4. **Written judgment guidance** (these files, skills, agents.md) only for decisions that genuinely require judgment.

Do not solve a problem that can be prevented or detected mechanically by adding another paragraph of instructions. Markdown is the weakest control.

## Working posture

- The codebase is the primary input to future agents. Treat it as a garden that must stay healthy under high-volume contribution.
- Inspect architecture, conventions, scripts, tests, and existing guardrails before changing code.
- Do not copy workarounds, anti-patterns, technical debt, or obsolete patterns simply because they already exist.
- Prefer simple, explicit, maintainable designs. Avoid cleverness and hidden behavior.
- Keep changes focused. Unrelated cleanup is in scope only when it is required for correctness or to prevent immediate recurrence of a defect.
- Discover repository tools and conventions; do not invent them.
- Preserve existing behavior unless the task explicitly changes it.

## Verification is part of implementation

- Define expected behavior and important invariants before risky changes.
- Run the most relevant deterministic checks that exist.
- For user-visible or integration changes, exercise the real system and collect concrete evidence.
- Never claim a check passed unless it was run and passed. State what was not run and why.
- With agents, the cost of producing code falls dramatically. Investing substantially more effort in verification becomes economically rational. Prefer comprehensive, cost-effective verification over minimizing the number of tests.

## Autonomy and safety

- Autonomy is earned by the strength of the environment, not declared.
- Never bypass, weaken, or suppress a failing check merely to make a change pass.
- Do not merge, deploy, or perform destructive operations unless the task and repository policy explicitly authorize it.
- When the environment is sufficiently strong, low-risk changes and certain automated remediation loops can proceed with reduced line-by-line human review.

## Detailed guidance

Files under `.claude/rules/` expand the principles above. Prefer the repository’s actual guardrails over the prose in these files. When the environment is incomplete, improve the environment.
