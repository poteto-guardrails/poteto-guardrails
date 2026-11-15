---
description: Prefer root-cause fixes and explicit designs; treat scheduling and subtle APIs as signals of possible architectural mismatch.
---

# Implementation quality

- Follow the language and framework’s established model. Do not mix paradigms casually.
- Prefer simple, explicit control flow, state transitions, resource ownership, and error handling.
- Handle cancellation, cleanup, concurrency, and lifecycle boundaries deliberately.
- Prefer a root-cause fix over a local patch. If a workaround is genuinely unavoidable, keep it minimal, document the constraint briefly, and leave a clear path to remove it.
- Do not add abstractions for hypothetical future needs. Keep the implementation proportionate to the actual requirement.
- Do not use comments to rationalize fragile code or to paper over an architectural violation.

## Patterns that often signal deeper problems

Certain techniques are frequently used to paper over ownership, lifecycle, or synchronization mismatches. They are not universally forbidden, but they require scrutiny:

- Timers, deferred callbacks, polling, animation frames, idle callbacks, and similar scheduling tricks used to “make something work” across an architectural boundary.
- Subtle or easy-to-misuse APIs when a simpler, supported abstraction already exists in the codebase.
- Compatibility layers, fallbacks, caches, or retries added without a demonstrated requirement and without consideration of failure modes.

When such a pattern appears (or is about to be introduced), first ask whether the underlying ownership, lifecycle, or data-flow problem can be fixed instead. If a repository has already identified particular APIs or patterns as high-risk, prefer the repository’s established alternatives and enforcement.
