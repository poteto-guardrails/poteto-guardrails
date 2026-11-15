---
description: Preserve explicit architecture, API contracts, and dependency boundaries.
---

# Architecture and boundaries

- Understand the intended architecture before adding or moving code.
- Prefer APIs that make valid behavior easy and invalid behavior difficult or impossible.
- Encode architectural decisions in module structure, types, APIs, and dependency constraints—not only in prose.
- Respect process, thread, runtime, platform, and layer boundaries. Do not import implementation details across a boundary simply because it is convenient.
- Keep dependencies flowing in the direction established by the repository.
- Use the repository's dependency graph tooling, boundary tests, or lint rules when available.
- Avoid subtle APIs and patterns that require extensive caveats to use correctly. Prefer a simpler supported abstraction.
- If a low-level mechanism is unsafe or routinely misused, route callers through a well-designed wrapper/API and restrict direct use where feasible.
- Do not introduce cross-layer coupling, hidden side effects, or circular dependencies.
- Before changing an API, identify callers and assess compatibility, migration, and error-handling implications.

A recurring boundary violation should usually become a static dependency/lint check rather than a reminder in documentation.
