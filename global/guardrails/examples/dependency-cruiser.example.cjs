// Example only: makes the Electron main/renderer boundary from the talk mechanical.
// Run with: npx depcruise src --config .dependency-cruiser.cjs
module.exports = {
  forbidden: [
    {
      name: "renderer-must-not-import-main",
      severity: "error",
      comment: "Main-process code in the renderer causes long tasks and jank. Talk to main through the typed IPC client in src/electron-renderer/ipc.",
      from: { path: "^src/electron-renderer" },
      to: { path: "^src/electron-main" },
    },
    {
      name: "main-must-not-import-renderer",
      severity: "error",
      comment: "Main must not depend on UI code. Put shared types in src/shared.",
      from: { path: "^src/electron-main" },
      to: { path: "^src/electron-renderer" },
    },
  ],
};
