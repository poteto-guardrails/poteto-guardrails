---
description: Keep the repository a high-quality source of context for future agents and engineers.
---

# Codebase hygiene

The codebase is one of the most important inputs to future agent work. Existing patterns are not automatically good patterns.

- Before adopting a pattern, check whether it is intentional, current, and consistent with the architecture.
- Do not reproduce workarounds, anti-patterns, obsolete code, duplicated logic, stale abstractions, or known technical debt simply because nearby code does so.
- When modifying legacy code, improve the local quality where practical without expanding the task unnecessarily.
- Remove dead code only when its lack of use is established; do not delete apparently unused code based on guesswork.
- Prefer one clear source of truth over parallel implementations or duplicated configuration.
- Avoid adding compatibility layers, fallback paths, caches, retries, timers, or indirection without a demonstrated requirement.
- Do not preserve a workaround by copying its explanatory comment. Investigate and fix the underlying cause.
- If a recurring defect is discovered, consider cleaning up existing instances and preventing new ones with a deterministic check.

When uncertain whether an established pattern is intentional, inspect its history, callers, tests, and architecture before changing or extending it.
