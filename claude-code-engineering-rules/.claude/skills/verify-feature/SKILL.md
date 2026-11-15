---
name: verify-feature
description: Run the app and check that a user-visible change actually works, collecting evidence (screenshots, recordings, logs, test output). Use after changing UI, client behaviour, a CLI, an API or an integration, before reporting the task as done.
---

# Verify a feature at runtime

The goal is evidence that the requested behaviour happens. A page that renders or a process that starts isn't evidence.

1. **Name the features.** Find them in `docs/feature-map.md` and use those exact names in your plan and report. If a feature is missing from the map, say so in the report and propose the entry under "Guardrail candidates". Don't edit the map unless asked.
2. **Write the scenarios before running anything:** the expected outcome for the happy path, plus each of these that applies: empty, error, loading, cancel/retry, boundary values.
3. **Drive the app with the driver.** Use `DRIVER_CMD` from `.claude/guardrails.env` (the session start message shows it). Reuse the driver; don't write one-off scripts for every run. If the driver can't express a scenario, note it as a guardrail candidate ("driver needs X") and do the step manually.
4. **Keep the evidence** in `verification/<short-task-name>/`: screenshots, recordings, trimmed logs, test output. Name each file after the scenario it shows.
5. **If there is no driver**, or the app can't run in this environment: don't guess. Mark the behaviour **unverified at runtime** in the report and say what a human should check.

## Report section

```
Runtime verification
- <Feature name> / <scenario>: PASS | FAIL | NOT RUN (reason) → verification/<task>/<file>
```
