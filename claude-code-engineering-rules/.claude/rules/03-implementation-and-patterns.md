---
description: Choose simple, idiomatic implementations and avoid fragile workarounds.
---

# Implementation quality

- Follow the language and framework's established declarative or imperative model. Do not mix paradigms casually.
- Do not use timers, deferred callbacks, polling, animation frames, idle callbacks, or scheduling tricks to conceal an architectural mismatch. First identify the underlying ownership, lifecycle, or synchronization problem.
- Use asynchronous work and state/effect mechanisms only where their semantics are understood and justified by the existing architecture.
- Avoid APIs or techniques that are known to be subtle or easy to misuse when a simpler abstraction exists.
- Keep control flow, state transitions, resource ownership, and error handling explicit.
- Handle cancellation, cleanup, concurrency, and lifecycle boundaries deliberately.
- Do not add comments to rationalize fragile code or explain away a violation of architecture.
- Prefer a root-cause fix over a local patch. If a workaround is genuinely unavoidable, document the constraint briefly and create a follow-up path to remove it.
- Do not add abstractions for hypothetical future needs. Keep the implementation proportionate to the actual requirement.
