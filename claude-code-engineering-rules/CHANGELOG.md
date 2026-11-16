# Changelog

## 4.1.0 — targeted hardening

- Preserve each session's original working-tree baseline across `SessionStart` events, including context compaction, resume and clear.
- Validate runtime evidence paths; reject absolute paths, parent traversal and symlinks that resolve outside the run directory.
- Give every driver invocation a unique output directory and retain prior evidence instead of deleting it.
- Move generated runtime evidence and logs to `.claude/verification-runs/`; exclude only that generated directory from the working-tree fingerprint.
- Reuse a recorded failing full-check result and its diagnostics when the command and tree are unchanged; a changed tree still triggers a fresh check.
- Add regression tests for the compaction bypass, evidence traversal and symlink escapes, repeated runs, narrow fingerprint exclusions and failed-check reuse.
- Update installation guidance, smoke-test paths and `.gitignore` handling.

## Validation

- Python syntax compilation: passed.
- `settings.json` JSON parse: passed.
- All 41 Python test cases passed across focused test runs. The suite was run in groups because the combined run exceeded the execution window; no test failure remains.
- Disposable smoke repository: setup passed; reference runtime driver returned PASS with evidence; configured full check returned PASS and recorded the working-tree fingerprint.
- Live authenticated Claude Code smoke test S0–S12: not run; must still be completed on the target Claude Code installation before describing the pack as fully hardened.
