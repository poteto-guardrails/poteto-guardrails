---
description: Review with evidence; increase autonomy only as the environment earns trust; support the outer automation loop.
---

# Review and autonomy

The goal is not to review every line forever. The goal is to make correctness increasingly true by default so that high volume does not produce chaos.

## Review posture

- Review design, changed contracts, invariants, risk, and verification evidence—not merely whether the diff looks plausible.
- Use tests, type/lint/build results, runtime evidence, screenshots, recordings, traces, and formal artefacts.
- Treat a green check as evidence only for what that check actually covers.
- Keep human judgment for product intent, ambiguous requirements, high-impact design, security-sensitive changes, data migrations, and other consequential operations.
- Do not infer permission to merge or deploy solely from the fact that checks pass.

## Graduated autonomy

Increase autonomy only as the environment supports it:

1. Agent proposes; human reviews.
2. Deterministic checks and runtime verification become reliable and comprehensive.
3. Low-risk, well-bounded changes can proceed with less line-by-line review when evidence is strong.
4. Automated merge or deployment only when explicitly authorized and when branch protection, CI, rollback, monitoring, and ownership controls are appropriate.

Stop and escalate when requirements are ambiguous, a key invariant cannot be verified, checks are missing or bypassed, an architectural boundary is unclear, runtime evidence contradicts claims, or the operation exceeds granted authorization.

## Outer automation loop (software factory)

Beyond a single task, the presentation describes automated projects that can:

- start after a release or on a schedule,
- exercise the application (including as a real user),
- find defects,
- open pull requests with fixes,
- and, when the foundation is strong enough, merge those fixes automatically.

Support this loop by:

- keeping the codebase and verification infrastructure healthy so that agent-generated changes succeed by default,
- providing reusable drivers and feature maps that automated projects can rely on,
- ensuring deterministic gates and evidence collection are reliable enough that many remediation PRs do not require deep human review,
- never weakening those gates merely to increase merge rate.

Autonomy is a property of the system, not a flag that is flipped once.