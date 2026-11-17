# Banned patterns in this repository

Each row must name the check that enforces it. Prose without a check doesn't belong here; add the check first (`/add-guardrail`).
If a ban blocks the right fix, stop and report it. Don't work around it.

| Banned | Enforced by | Do instead |
|---|---|---|
| _(example, delete it)_ `setTimeout` / `requestAnimationFrame` / `requestIdleCallback` in `src/renderer/**` | ESLint `no-restricted-globals` | Fix ownership: subscribe to the store or lifecycle hook that owns the state |
