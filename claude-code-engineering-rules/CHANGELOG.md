# Changelog

## 4.1.1 — fix for reused failure results

4.1.0 started reusing a failed full-check result while the tracked files were unchanged. Review found three problems with that, each now fixed and tested:

- **Fixes outside version control were invisible.** Installing a dependency into an ignored folder (`node_modules/`, a virtualenv) or starting a service doesn't change the fingerprint, so the stop gate replayed the old failure until retries ran out, and the user saw "NOT verified" for work that would now pass. A replayed failure is now labelled `SAVED result`, with the time and runner, and tells Claude to run `python3 .claude/tools/check.py` for a fresh result. The final user warning says the same. (`test_replayed_failure_is_labelled_and_check_py_refreshes_it`)
- **Timeouts were replayed.** One slow moment became a sticky failure. Results with exit 124 are never reused. (`test_timeouts_are_never_replayed`)
- **The pack-version binding added in 4.1.0 had no test.** Removing it didn't fail anything. Now covered. (`test_records_from_another_pack_version_are_ignored`)

Validation: 44 tests pass in a single run (about 18 s). Each of the three fixes, and the 4.1.0 compaction fix, was removed in turn to confirm the suite fails without it. The live smoke test (S0 to S12) still hasn't been run.

Upgrade note: `PACK_VERSION` is now 4.1.1, so saved records from 4.1.0 are ignored and checks run fresh once.

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
