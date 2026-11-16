# Changelog

## 4.1.2 — scope failure replay to the stop chain

From review of 4.1.1:

- **Saved failures are reused only within the stop chain that produced them.** That means the same session, the same chain (`stop_hook_active=false` starts a new one), written by the stop gate, tracked files unchanged, and not a timeout. A new user turn, another session, or a failure recorded by `check.py` always gets a fresh run. Passing records keep their fingerprint-based reuse. A bounded retry chain replaces any need for a time-based expiry.
- **The saved-failure message no longer says "fix the root cause".** A replay now says not to change files just to trigger a new check. It points to `check.py` for a fresh run after untracked or transient changes, and says to report honestly if the failure persists. Fresh failures keep the "investigate and fix" guidance.
- **Smoke test:** S6, S6a (replay within the chain), S6b (a new turn runs fresh) and S7 now count real check runs with an invocation counter in a git-ignored `.smoke/check-runs.log`. Record files can't be used for this, because a re-run overwrites them.
- **Tests:** 48 pass in a single run (about 19 s). The new tests are `test_saved_failure_message_does_not_say_fix_root_cause`, `test_saved_failure_only_replays_within_its_stop_chain`, `test_saved_failure_is_not_replayed_in_another_session` and `test_check_py_failure_is_not_replayed_by_stop_gate`.
- **Mutation testing:** removing the chain binding, the chain renewal, the timeout exclusion or the conditional message each fails the suite. Removing only the session or runner condition doesn't change behaviour: chain IDs are random per session, and `check.py` records carry no chain. So those two conditions are a backstop, not separately testable.
- The smoke sequence S6 to S7 was simulated by calling the hooks directly in a disposable repo. Counts: S6 chain = 1 run, S6b = +1, S7 = +1 (check.py only).

Code freeze: no further changes until the live smoke test (S0 to S12) has been run on a real Claude Code install.

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
