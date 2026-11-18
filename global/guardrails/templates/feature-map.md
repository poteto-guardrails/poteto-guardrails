# Feature map

The app's features as a user sees them, with stable IDs that everyone (people and agents) uses.
`~/.claude/guardrails/tools/verify.py` reads this table. The **Feature ID** and **Scenario IDs** columns are
what you pass to `--feature` and `--scenario`. Keep the IDs to letters, digits, `.`, `_` and `-`.

How to *drive* a feature isn't recorded here: that's the driver's job (`DRIVER_CMD`).
This file says *what* exists; the driver says *how* to exercise it.

| Feature ID | Name | Where it lives | Scenario IDs |
|---|---|---|---|
| chat-sidebar | Chat sidebar (example, replace it) | Main window, left panel | empty, rename, delete, offline |
