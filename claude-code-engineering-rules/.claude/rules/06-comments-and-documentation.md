---
description: Keep comments, docs, and agent instructions accurate, concise, and subordinate to executable truth.
---

# Comments and documentation

Comments, Markdown, rules, and skills are useful for context and judgment, but they are not enforceable safeguards.

- Prefer self-explanatory code, clear names, types, tests, and executable constraints over comments that tell future contributors what not to do.
- Comments must explain non-obvious intent, invariants, constraints, or trade-offs—not narrate the code line by line.
- Keep comments accurate when code changes. Remove stale comments rather than preserving historical explanations.
- Never use a comment to justify an avoidable workaround or bypass an architectural constraint.
- Do not add blanket comments or long prose to compensate for an unclear API.
- Keep documentation aligned with actual behavior and the current implementation.
- Treat a one-off correction as context, not automatically as a universal rule. Confirm the general principle before applying it elsewhere.
- Do not turn every code-review suggestion into a permanent prohibition. Record durable conventions only when they are genuinely general.
- If a documented instruction is important enough that violating it would break the system, consider enforcing it with a test, type, linter, or architecture check.

The presentation describes one team's decision to ban most comments in its own codebase. That is not a universal requirement: use comments when they materially preserve otherwise hard-to-understand intent.
