# Feature map

The app's features as a user sees them, with the names everyone (people and agents) should use.
Keep the names stable. Add rows when features ship. The `verify-feature` skill relies on this file.

| Feature name | Where it lives (screen / command / endpoint) | Key states to check | Driver entry point |
|---|---|---|---|
| _(example, replace it)_ Chat sidebar | Main window, left panel | empty, many chats, rename, delete, offline | `npx playwright test sidebar.spec.ts` |
