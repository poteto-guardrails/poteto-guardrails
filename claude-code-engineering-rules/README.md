# Claude Code engineering rules — v4.1.2

A Claude Code setup based on Lauren Tan's talk **"All Code Is Slop (Except Mine)"** (AI Engineer, Nov 2026) and the **Karpathy guidelines** for LLM coding.

v4.1.2 limits saved-failure reuse to the stop chain that produced it. v4.1.1 fixed how saved failure results are reused (see CHANGELOG.md). v4.1 kept v4's architecture and closed defects found in the V4 review. It preserves session baselines across context compaction, confines evidence to unique run directories, narrows generated-artifact exclusions, and avoids rerunning an unchanged failing check.

> **To the reviewer:** "What changed from v3" maps each review point to the change and its test. "Open questions" at the end is where your next round of feedback would help most.

---

## Read this first: mechanisms vs enforcement

**The pack provides enforcement mechanisms. A repository is only enforced once they're configured, loaded and smoke-tested.** Straight after install:

| Control | Works out of the box? | Needs |
|---|---|---|
| Blocking new suppressions, skipped and focused tests | **Yes**, once Claude Code loads the settings | Claude Code **2.1.295+** for fail-closed on hook crash (`onFailure`). Confirm with smoke test S11 |
| Permission rules (force-push denied; push, merge and config edits ask) | Yes | Nothing. Best effort for shell commands (see limitations) |
| Per-edit lint feedback | **No** | `FAST_CHECK_CMD` |
| Full-check gate before finishing | **No** | `FULL_CHECK_CMD` |
| Runtime verification | **No** | `DRIVER_CMD` implementing the driver contract, plus `docs/feature-map.md` |
| Final authority on what merges | **Not this pack** | CI and server-side branch protection |

Until a check is configured, Claude is told at every session start that it doesn't exist, and the stop gate warns you whenever files changed without a full check.

## The idea in one paragraph

The talk ranks the ways to make agents trustworthy: (1) architecture and API design, (2) deterministic checks, (3) runtime and formal verification, and last (4) written instructions, for judgment calls. The pack follows that order. Hooks and permissions do the enforcing, small tools make checks and verification repeatable, and the Markdown (under 600 words loaded per session) covers only judgment.

## What's in the pack

| Path | What it does |
|---|---|
| `.claude/settings.json` | Registers the hooks; permission deny and ask rules |
| `.claude/guardrails.env` | Human-owned config: the commands the hooks and tools run |
| `.claude/hooks/block_suppressions.py` | **PreToolUse, fails closed.** Blocks edits that *add* suppressions (`eslint-disable`, `@ts-ignore`, `as any`, `# noqa`…), skipped tests (`.skip`, `xit`, `@pytest.mark.skip`…) or focused tests (`.only`, `fit`, `fdescribe`). Validates its input; anything it can't interpret is blocked |
| `.claude/hooks/post_edit_check.py` | PostToolUse: runs `FAST_CHECK_CMD` on the edited file and sends failures back to Claude |
| `.claude/hooks/stop_gate.py` | Stop: a turn that changed the tree can't end until the full check has passed on *that exact tree*. Limited retries per stop chain, then it warns you. Never traps the session |
| `.claude/hooks/session_start.py` | Records the session's baseline tree; tells Claude which checks exist and how to run them |
| `.claude/tools/check.py` | Claude runs the full check once, sees the result, and the result is **recorded with provenance**. The stop gate reuses the result (pass or fail) for the identical tree and command |
| `.claude/tools/verify.py` | Runs one feature scenario through the **driver contract** and rejects drivers that break it |
| `.claude/tests/test_guardrails.py` | 48 tests, run in about 19 seconds; each recent fix has been removed in turn to confirm a test fails |
| `smoke-test/` | Disposable-repo builder plus the **live smoke test checklist (release gate)** |
| `CLAUDE.md` | Judgment rules (Karpathy merged with the talk) and the final report format |
| `.claude/rules/bans.md` | Banned patterns. Each row must name its enforcing check |
| `.claude/skills/verify-feature/` | Runtime verification procedure using `verify.py` |
| `.claude/skills/add-guardrail/` | Human-invoked (`/add-guardrail`): turn a recurring mistake into a check |
| `docs/feature-map.md` | Feature IDs and scenario IDs: the shared vocabulary `verify.py` validates against |
| `examples/` | ESLint, dependency-cruiser and ruff ban examples, plus `driver_stub.py` (a reference driver) |

## Install

Requirements: Claude Code **2.1.295 or later**, `python3` on PATH, and git.

```bash
# 1. Prove the scripts work on your machine
python3 /path/to/pack/.claude/tests/test_guardrails.py

# 2. Live smoke test in a throwaway repo (release gate; about 20 minutes)
bash /path/to/pack/smoke-test/setup_smoke_repo.sh /tmp/guardrail-smoke
#    then follow smoke-test/SMOKE-TEST.md

# 3. Install into the real repository (cp -n won't overwrite existing files)
cd /path/to/your/repo
cp -rn /path/to/pack/{CLAUDE.md,.claude,docs} .
# Add the generated evidence directory to your existing .gitignore (without replacing it)
grep -qxF '.claude/verification-runs/' .gitignore 2>/dev/null || printf '\n# Generated Claude runtime-verification evidence\n.claude/verification-runs/\n' >> .gitignore
grep -qxF '__pycache__/' .gitignore 2>/dev/null || printf '\n# Python bytecode\n__pycache__/\n*.py[cod]\n' >> .gitignore
rm -rf .claude/tests          # optional: tests are for the pack, not your repo
```

Then fill in `.claude/guardrails.env`, replace the example rows in `bans.md` and `feature-map.md`, keep `.claude/verification-runs/` as generated output (it is excluded from fingerprints), and run `/hooks` to confirm. Merge any existing `CLAUDE.md` or `settings.json` by hand. On Windows, change `python3` to `python` or `py` in `settings.json` (untested; see limitations).

## How the main pieces work

**Fail-closed guard.** It exits 0 only after inspecting a well-formed edit from a supported tool (Edit, Write, MultiEdit, NotebookEdit). Malformed JSON, missing fields, unknown tools, a wrong event, an invalid custom regex or any internal exception: blocked, with a reason. `onFailure: "block"` covers what the script can't catch itself: it failing to start, timing out, or the interpreter being missing. It's set **only** on this hook. A fail-closed Stop hook would trap the session if Python broke.

**Verification records.** Each full-check run is stored in `.git/claude-guardrails/records/`, keyed by (working-tree fingerprint, command). Each record holds the fingerprint, command, exit code, bounded diagnostic output, time, duration, runner (`check.py` or `stop_gate`) and session. A record is current only when its pack version, command and fingerprint match. A current passing record allows the turn to finish; a failing record is replayed, labelled as a saved result, only within the same session and stop chain that produced it; a new turn, another session, or a `check.py` failure gets a fresh run. Timeouts are never replayed. Any tree or command change requires a fresh run, and `check.py` always runs fresh, which is how Claude recovers after fixing something outside version control (installed dependencies, a started service).

The fingerprint covers HEAD's tree plus staged, unstaged and untracked content. So committing in the middle of a session, renames, deletions and new folders all invalidate it. Only `.claude/verification-runs/` is excluded (`FINGERPRINT_EXCLUDE`), so generated evidence doesn't force a re-run while project-owned files under `verification/` remain fingerprinted. If the check itself modifies files (a formatter, say), the result isn't recorded.

*Why a record from another session is accepted:* the record is bound to the tree's content, not to whoever ran it. If two sessions share one working tree, the check really did run on their combined work, so it verifies exactly what exists. What sessions must not share is **retry state**, and that's now per session.

**Stop gate.** In order:
1. The tree matches this session's baseline → nothing to check.
2. A valid record exists → done.
3. Otherwise, use a recorded result for this exact tree and command, or run the check and record it. If it fails, Claude is sent back up to `STOP_GATE_MAX_RETRIES` times per stop chain (a new chain starts when `stop_hook_active` is false). An unchanged failure reuses its saved diagnostics; a changed tree triggers a fresh check. After the retry limit, the turn ends with a user-visible **NOT verified** warning.

**Driver contract** (full text at the top of `verify.py`). The driver is called as `DRIVER_CMD --feature ID --scenario ID --out DIR` and must exit 0 (pass), 1 (fail) or 3 (unsupported). It must write `DIR/result.json` with the requested feature and scenario, a status that matches the exit code, a summary, and evidence files that exist; a pass needs at least one. Anything else is a contract violation and counts as **not verified**. Every run gets a unique directory under `.claude/verification-runs/<task>/<feature>/<scenario>/<run-id>/`; a task-level `log.jsonl` is appended without deleting earlier evidence.

## What changed from v3

| Review point | Change | Proven by |
|---|---|---|
| Hook failures pass silently | `onFailure: "block"` on the edit guard only | `Settings.test_fail_closed_only_on_the_edit_guard`, smoke S11 |
| Malformed input made the guard exit 0, which `onFailure` can't see *(found in counter-review)* | Strict input validation; any exception blocks | `test_fails_closed` (10 cases), `test_malformed_json_reports_why`, `test_internal_crash_blocks` |
| No fail-closed on the Stop hook *(found in counter-review)* | Stop gate never fails closed; a crash shows the user "NOT verified" | `test_stop_gate_crash_never_traps_session`, smoke S12 |
| Focused tests missed | `.only`, `fit`, `fdescribe`, `test.describe.only` added; `model.fit(` not flagged | `test_blocks_added_markers`, `test_allows_legitimate_code` |
| `findall` broke custom regexes with capture groups | `finditer` and whole-match counts; an invalid regex blocks | `test_custom_regex_with_capture_groups…`, `test_invalid_custom_regex_blocks` |
| Shared state across sessions | Per-session state files; retries tied to the stop chain via `stop_hook_active`; the separate reset hook removed; atomic writes | `test_sessions_do_not_share_retries`, `test_retry_chain_then_warn_then_new_chain` |
| Agent couldn't see check results; risk of running checks twice | `check.py` wrapper plus content-addressed records; the stop gate reuses them | `test_check_py_record_is_reused_then_invalidated`, smoke S7 |
| Verification provenance *(reviewer addition)* | Record: session, command, fingerprint, exit, time, runner; validity computed when read | `test_record_bound_to_command`, `test_fingerprint_sees_…` |
| Committing broken code skipped the gate (new) | HEAD's tree is in the fingerprint; the session baseline replaces "clean tree" | `test_committing_broken_code_is_still_caught` |
| Driver contract undefined | Executable contract in `verify.py`; reference driver; feature map holds IDs, not driver commands | `VerifyDriver` (8 violation types) |
| Compaction could reset the session baseline | Baseline is initialised only once per session and preserved across every SessionStart source | `test_compaction_preserves_original_baseline` |
| Driver evidence could escape its output directory | Reject absolute paths, traversal and symlinks resolving outside the run directory | `test_evidence_path_traversal_rejected`, `test_evidence_symlink_escape_rejected` |
| Concurrent driver runs could delete each other's evidence | Unique run directory per execution; previous evidence is retained | `test_repeated_runs_preserve_separate_evidence` |
| Fingerprint exclusion hid project-owned `verification/` files | Exclude only `.claude/verification-runs/` | `test_only_generated_artifacts_are_excluded` |
| Failed full checks could run repeatedly on unchanged trees | Stop gate reuses current failed record and original diagnostics until the tree changes | `test_failed_check_record_is_reused_until_tree_changes` |
| *(4.1.1)* Replayed failures hid fixes made outside version control | Replays are labelled `SAVED result` and point to `check.py` for a fresh run | `test_replayed_failure_is_labelled_and_check_py_refreshes_it` |
| *(4.1.1)* One slow run became a sticky timeout | Timeouts (exit 124) are never replayed | `test_timeouts_are_never_replayed` |
| *(4.1.1)* Pack-version binding of records untested | Test added | `test_records_from_another_pack_version_are_ignored` |
| *(4.1.2)* Saved failures could be replayed in later turns or other sessions | Replay scoped to the same session and stop chain | `test_saved_failure_only_replays_within_its_stop_chain`, `…_not_replayed_in_another_session`, `test_check_py_failure_is_not_replayed_by_stop_gate` |
| *(4.1.2)* Replay still said "fix the root cause" | Separate guidance for saved and fresh failures | `test_saved_failure_message_does_not_say_fix_root_cause` |
| Timer rule too broad | Reworded: legitimate when it's the design, banned as a symptom mask | — |
| Notebook edits uncovered | NotebookEdit in both matchers; compared against the cell's current source | `test_notebook_edit` |
| No live test | `smoke-test/`: disposable repo plus a 15-step checklist with expected results | Run it: see below |
| README overstated enforcement | "Mechanisms vs enforcement" table | — |

**Test quality:** the suite was checked by deliberately breaking the code (mutation testing). Nine breakages were tried: removing the `fit` lookbehind, failing open on bad JSON, reverting to `findall`, ignoring `stop_hook_active`, shared session state, dropping HEAD from the fingerprint, unbinding records from commands, skipping the driver's exit/status check, and removing `.only`. The suite catches 8 of them. The ninth (unbinding the record from its command) is covered by the record's storage key, so behaviour doesn't change. The explicit check stays as a second layer.

## Status of the live test

**Not yet run.** Claude Code 2.1.325 was installed in the build environment, but it needs an authenticated account to run a session. What *was* confirmed there: the installed binary contains the `onFailure: "block"` handling for command hooks, including a notice that it's ignored on some events (which is why it's set only on PreToolUse). The setup script was also exercised end to end without Claude: guard blocks, check records, the driver passes, and it refuses to overwrite a non-empty folder.

**v4.1.2 should be called "hardened" only after `smoke-test/SMOKE-TEST.md` S0 to S12 pass on a real install.**

## Known limitations

- **Shell commands bypass the edit hooks.** `sed`, `tee`, scripts and `git apply` aren't seen by the guard or the per-file check. The stop gate still runs the full check over the tree, but a suppression added by shell gets through (smoke S14 records this). Permission rules on Bash are prefix matches, so they're best effort.
- **Records resist accidents, not a determined adversary.** They live in `.git/claude-guardrails/`, and edits there are denied via `Edit(/.git/**)` and `Bash(*claude-guardrails*)`. A determined agent could still forge one through an indirect shell command. CI is the final authority; treat local records as a convenience.
- **Outside git:** checks still run, but nothing can be recorded or compared to a baseline, so the stop gate runs the full check on every turn.
- **Windows:** path handling normalises backslashes and that's tested, but nothing has been run on Windows.
- **Notebook replace edits** are compared with the cell's current source. If the cell can't be found, the comparison is against empty, so it's stricter, never looser.
- **The default suppression list is opinionated** (`as any`, `as unknown as`, `@pytest.mark.xfail`). Tune `SUPPRESSION_REGEX` and `SUPPRESSION_EXEMPT_GLOBS` per repo. Only Claude's edits are checked, never human ones.

## Open questions for the reviewer

1. **Accepting records across sessions:** is content-binding sufficient, or do you see a case where a valid record for an identical tree should still be rejected?
2. **Exit code 3 ("unsupported") in the driver contract:** should unsupported scenarios block the final report, or is "report as not run" enough?
3. **Minimum version policy:** if S11 passes on 2.1.295 but older versions ignore `onFailure` silently, should `session_start.py` detect the version and warn?

## Credits

- Lauren Tan, *All Code Is Slop (Except Mine)*, AI Engineer, November 2026.
- Andrej Karpathy's observations on LLM coding pitfalls, via the `karpathy-guidelines` skill ([multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills), MIT). Paraphrased, not copied.
- v2 by the original author. v3, v4 and v4.1 by adversarial review rounds between the author's reviewer and Claude.
