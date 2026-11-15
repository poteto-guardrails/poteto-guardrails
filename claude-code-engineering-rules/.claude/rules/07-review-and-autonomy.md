---
description: Review changes using verification evidence and increase agent autonomy only when guardrails support it.
---

# Review and autonomy

The goal is not to review every line forever. The goal is to make correctness increasingly true by default.

- Review the design, changed contracts, invariants, risk, and verification evidence—not just whether the diff looks plausible.
- Use tests, type/lint/build results, runtime evidence, screenshots, recordings, traces, and formal artifacts to support review.
- Investigate failures and unexpected behavior at the root cause.
- Treat a green check as evidence only for what that check actually covers.
- Keep human review for product intent, ambiguous requirements, high-impact design choices, security-sensitive changes, data migrations, and consequential operations.
- Do not infer permission to merge or deploy from the fact that checks pass.

Increase autonomy gradually:
1. Start with the agent proposing changes and a human reviewing them.
2. Add deterministic checks and runtime verification.
3. Allow low-risk, well-bounded changes to proceed with less line-by-line review when evidence is strong.
4. Automate merge/deployment only when explicitly authorized and when branch protection, CI, rollback, monitoring, and ownership controls are appropriate.

Stop and escalate when:
- requirements or expected behavior are ambiguous;
- a key invariant cannot be verified;
- checks are missing, flaky, or bypassed;
- the change crosses an unclear architectural boundary;
- runtime evidence contradicts the implementation's claims;
- the operation is destructive, externally visible, or outside granted authorization.
