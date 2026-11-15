---
description: Convert recurring agent mistakes into architecture improvements or automated checks; treat prose as the last resort.
---

# Deterministic quality gates

The presentation’s core operational loop is: an agent (or human) makes a mistake → identify the cause → eliminate the invalid approach via architecture/API design if possible → otherwise add a targeted deterministic check → verify the check → future work is constrained by default.

## Use existing tools first

- Compiler and type system for invalid states and interface mismatches.
- Linter and formatter for language and framework conventions.
- Unit, integration, and end-to-end tests for behavioral requirements.
- Dependency-graph or architecture checks for forbidden imports and layer violations.
- Build and CI checks for reproducible integration validation.

## When a recurring mistake is observed

1. Record the concrete failure mode and the invariant that was violated.
2. Ask whether better API design or architecture can make the incorrect approach impossible or unnatural.
3. If not, propose or implement a targeted deterministic check with a clear, actionable diagnostic.
4. Add tests or examples that demonstrate the check rejects the bad pattern and accepts legitimate uses.
5. Bring existing code into compliance when safe and in scope.
6. Confirm the check is actually running in the normal development and CI path.
7. Prefer this path over adding a permanent prose prohibition in rules or comments.

## Do not

- Silence a failure with a lint suppression, unsafe cast, skipped test, or broad exception without a justified, reviewed reason.
- Create a rule that merely bans syntax without understanding valid use cases.
- Add a check that is noisy, ambiguous, or impossible to follow consistently.
- Claim a guardrail exists until it is implemented and exercised.
- Default to writing another natural-language reminder when a mechanical check is feasible.

A targeted deterministic check is more reproducible and trustworthy than another paragraph of instructions. The long-term goal is that most product code can be reviewed primarily through evidence and that many low-risk changes succeed by default.
