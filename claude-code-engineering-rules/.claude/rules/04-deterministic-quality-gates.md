---
description: Prefer enforceable code-level guardrails over repeated natural-language reminders.
---

# Deterministic quality gates

When a rule can be checked mechanically, use a deterministic tool rather than relying solely on agent instructions.

Use the repository's existing tools first:
- Compiler and type system for invalid states and interface mismatches.
- Linter and formatter for language and framework conventions.
- Unit, integration, and end-to-end tests for behavioral requirements.
- Dependency graph or architecture checks for forbidden imports and layer violations.
- Build/CI checks for reproducible integration validation.

When a recurring mistake is found:

1. Identify the underlying cause and the exact invariant that was violated.
2. Determine whether API design or architecture can eliminate the invalid approach.
3. Otherwise, add or improve a deterministic check with a clear, actionable diagnostic.
4. Add tests for the guardrail itself where practical.
5. Apply the rule to existing code when safe and in scope.
6. Verify that the check catches the bad pattern and accepts valid code.

Do not:
- Add a lint suppression, `any`/unsafe cast, ignored test, skipped check, or broad exception to silence a failure without a justified and reviewed reason.
- create a rule that merely bans syntax without understanding valid use cases;
- add a check that is noisy, ambiguous, or impossible to follow;
- claim a guardrail exists until it is implemented and exercised.

A targeted deterministic check is generally more reproducible and trustworthy than another paragraph in `CLAUDE.md`.
