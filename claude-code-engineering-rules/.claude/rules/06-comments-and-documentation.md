---
description: Comments and Markdown are subordinate to code, types, tests, and enforced constraints.
---

# Comments and documentation

Comments, Markdown rules, and skills are useful for context and judgment. They are not enforceable safeguards. Agents can misinterpret them, over-generalize corrections, or even use comments to justify poor decisions.

- Prefer self-explanatory code, clear names, types, tests, and executable constraints over comments that tell future contributors what not to do.
- Comments should explain non-obvious intent, invariants, constraints, or trade-offs—not narrate the code.
- Keep comments accurate when code changes. Remove stale comments.
- Never use a comment to justify an avoidable workaround or to bypass an architectural constraint.
- Do not add long prose to compensate for an unclear API; improve the API or the surrounding design.
- Treat a one-off correction as context, not automatically as a universal standing rule. Confirm the general principle before applying it broadly.
- If an instruction is important enough that violating it would break the system or architecture, prefer enforcing it with a test, type, linter, or architecture check.

Repository comment policy is ultimately a local decision. Some teams heavily restrict comments and enforce the policy with linting; others allow them more freely. Follow the repository’s established policy and, when none exists, default to the principle that comments are subordinate to executable truth.
