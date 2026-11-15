---
name: verify-feature
description: Run the app and check that a user-visible change actually works, collecting evidence through the project's verification driver. Use after changing UI, client behaviour, a CLI, an API or an integration, before reporting the task as done.
---

# Verify a feature at runtime

The goal is evidence that the requested behaviour happens. A page that renders or a process that starts isn't evidence.

1. **Pick the IDs.** Find the feature and scenario IDs in `docs/feature-map.md`. Use those exact IDs in your plan and report. If the feature is missing, report it as unverified and propose the map entry under "Guardrail candidates". Don't edit the map unless asked.
2. **Write the expected outcome for each scenario before running anything:** the happy path, plus each of these that applies: empty, error, loading, cancel/retry, boundary values.
3. **Run each scenario through the runner**, never the driver directly:
   ```
   python3 .claude/tools/verify.py --feature <ID> --scenario <ID> --task <short-task-name>
   ```
   The runner enforces the driver contract, stores evidence under `verification/<task>/` and prints a one-line result. Quote that line in your report.
4. **Read the evidence** the runner lists, and check that it shows *your* expected outcome. If it doesn't, the scenario hasn't passed, whatever the exit code says.
5. **Results that aren't a pass:**
   - `NOT CONFIGURED`, or the app can't run here: report the behaviour as **unverified at runtime** and say what a human should check.
   - `NOT RUN (driver doesn't support this scenario)`: report it, and propose the driver extension under "Guardrail candidates".
   - `NOT VERIFIED (driver contract violation)`: the driver is broken. Report it. Don't fix the driver unless asked.

## Report section

```
Runtime verification
- <feature> / <scenario>: <the runner's result line>
```
