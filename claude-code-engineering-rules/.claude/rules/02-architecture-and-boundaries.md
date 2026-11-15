---
description: Make architecture visible in directory structure and APIs; enforce boundaries mechanically.
---

# Architecture and boundaries

Repository structure is itself an agent-control mechanism. Directory layout, module ownership, and dependency direction communicate context and constrain what is easy to do.

- Understand the intended architecture and ownership model before adding or moving code.
- Prefer APIs that make valid behavior easy and invalid behavior difficult or impossible.
- Encode architectural decisions in module structure, types, APIs, and dependency constraints—not only in prose.
- Organize code so that process, thread, runtime, platform, and layer boundaries are obvious from location. Agents (and humans) should be able to infer ownership and allowed dependencies from the path.
- Keep dependencies flowing in the direction established by the repository. Use dependency-graph tooling, boundary tests, or lint rules when available; prefer making forbidden imports mechanically detectable or impossible.
- A recurring boundary violation should usually become a static dependency or architecture check rather than another reminder in documentation.
- Avoid introducing cross-layer coupling, hidden side effects, or circular dependencies.
- Before changing a public or shared API, identify callers and assess compatibility, migration, and error-handling implications.
- If a low-level mechanism is routinely misused, prefer a well-designed wrapper or restricted API surface over relying on comments that warn people not to misuse it.

The goal is not merely “respect boundaries.” The goal is an environment in which the architecture is both visible and enforced, so that high-volume agent contribution does not erode it.
