---
description: Treat the codebase as high-quality input for future agents; remediate rather than copy technical debt.
---

# Codebase hygiene

The codebase is one of the largest sources of context for agents. Existing patterns are not automatically good patterns.

- Before adopting a pattern, determine whether it is intentional, current, and consistent with the intended architecture.
- Do not reproduce workarounds, anti-patterns, obsolete code, duplicated logic, stale abstractions, or known technical debt merely because nearby code does so.
- When modifying legacy areas, improve local quality where practical without expanding the task beyond what is needed for correctness or to stop immediate recurrence.
- Prefer one clear source of truth over parallel implementations or duplicated configuration.
- Do not preserve a workaround by copying its explanatory comment. Investigate and fix the underlying cause when feasible.
- Sequencing matters: introduce lint or other deterministic rules that prevent *new* instances of an anti-pattern, then clean up existing instances, then scale agent throughput. Automating a loop that produces garbage only produces more garbage, at higher token cost.

If a recurring defect or anti-pattern is discovered, treat it as a candidate for the deterministic-quality-gates process rather than a permanent prose warning.
