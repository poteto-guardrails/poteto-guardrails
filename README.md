# Claude Code Engineering Rules

**Guardrails that make Claude Code earn your trust instead of asking for it.**

This is a drop-in pack of hooks, permission rules, small tools and a short rulebook. It makes Claude Code work in a repository the way an experienced engineer does. It won't add lint or test suppressions, it can't finish a turn without passing your full check, it asks before touching your CI or lint config, and it keeps evidence for every claim that something works.

This repository also holds the pack's complete history, from a page of Markdown advice (v1) to a tested, fail-closed enforcement layer (v4.1.2). There is one commit and one tag per release, so you can see how each idea changed under review.

---

## What we built

Put simply, it's a **local enforcement layer for Claude Code**, built from Claude Code's own extension points: hooks, permission rules, skills and `CLAUDE.md`. You copy it into a repository, set three commands in one config file, and from then on every Claude session in that repository works under these rules:

| When | What happens | Mechanism |
|---|---|---|
| **Session starts** | Claude is told exactly which checks exist, the commands that run them, and which are switched off. The session's starting working tree is recorded as its baseline. | `SessionStart` hook: `session_start.py` |
| **Before every edit** | The edit is inspected. If it *adds* a suppression marker (lint-disable comments, type-checker ignore directives, unsafe casts to the any type, linter "no QA" comments), a skipped test or a focused test (`.only`, `fit`, `fdescribe`), it's blocked with the reason. Editing near an existing marker is fine. The guard **fails closed**: malformed input, an unknown tool, a crash or a missing interpreter all block. | `PreToolUse` hook: `block_suppressions.py` with `onFailure: "block"` |
| **After every edit** | Your fast check (lint plus format on that one file) runs, and any failures go straight back to Claude while the change is still fresh. | `PostToolUse` hook: `post_edit_check.py` |
| **Before the turn can end** | If the working tree changed, the turn can't end until your full check (lint, types, tests, build) has passed on *that exact tree*. Claude is sent back a limited number of times. After that the turn ends, and you're told plainly that the work is **NOT verified**. A broken gate never traps the session. | `Stop` hook: `stop_gate.py` |
| **Dangerous commands** | Force-push, `git reset --hard`, `git clean -f` and `rm -rf` are denied. Push, merge, rebase and package publishing ask first. So does any edit to `CLAUDE.md`, `.claude/`, CI workflows, or lint, format and type-check config. | `permissions` in `settings.json` |
| **"It works", on demand** | Claude runs the full check through a wrapper that records the result with provenance: tree fingerprint, command, exit code, time, runner and session. The stop gate reuses a valid record instead of running everything again. | `.claude/tools/check.py` |
| **Runtime verification** | Claude drives a named feature scenario through your app driver. The driver has to follow a strict contract (exit code, `result.json`, evidence files that really exist). If it breaks the contract, the result counts as not verified. | `.claude/tools/verify.py` plus the `verify-feature` skill |
| **A recurring mistake** | A human runs `/add-guardrail` to turn it into a real check (an API change, a lint rule or a test) with an error message that names the fix. | `add-guardrail` skill |

The written part is deliberately small. `CLAUDE.md` (about 500 words) covers only what needs judgment: state your assumptions, write the least code that solves the problem, fix root causes, don't touch the guardrails, and end with an honest report of what changed and what was checked. `bans.md` lists the banned patterns, and **every row has to name the check that enforces it**. Prose with nothing enforcing it doesn't belong in the rulebook.

### Engineering details

- **Content-addressed verification records.** Each result is stored under `.git/claude-guardrails/records/`, keyed by a fingerprint of HEAD's tree plus staged, unstaged and untracked content, and by the check command. So a commit, rename, deletion or new folder in the middle of a session all force a fresh run. Only generated evidence (`.claude/verification-runs/`) is excluded. If the check itself modifies files (a formatter, for example), its result isn't recorded.
- **Precise failure replay.** A saved failure is replayed only within the same session and the same stop chain that produced it, and timeouts are never replayed. A new turn, another session, or an explicit `check.py` run always gets a fresh result. So a fix made outside version control, such as installing a dependency or starting a service, is never hidden by a stale failure.
- **Per-session state.** Retry counters and baselines are kept per session and written atomically, so parallel sessions in one working tree never share retry budgets. The baseline survives context compaction, resume and clear.
- **Evidence you can trust.** Every driver run writes to its own run directory. Evidence paths are checked: absolute paths, `..` traversal, and symlinks that point outside the run directory are all rejected. Earlier evidence is never deleted.
- **Fails closed where that's safe, fails open where it isn't.** The edit guard blocks on any failure. The stop gate never does, because a fail-closed Stop hook with a broken Python would lock you out of your own session.
- **Tested, including the tests.** 48 tests run in about 19 seconds. The suite was mutation-tested: each fix was removed in turn to confirm a test fails without it.
- **Released through a gate.** `smoke-test/` builds a disposable repository and walks through 15 live scenarios (S0 to S14), each with an expected result: blocked suppressions, the stop-gate retry chain, denied force-pushes, broken-hook behaviour, and more.

### Scope

This pack covers **mechanisms**. A repository counts as enforced only once they're configured and smoke-tested. Out of the box, the suppression guard and the permission rules work immediately. The per-edit check, the full-check gate and runtime verification wait for you to set `FAST_CHECK_CMD`, `FULL_CHECK_CMD` and `DRIVER_CMD` in `.claude/guardrails.env`. Until you do, Claude is told at every session start that those checks don't exist.

Shell commands (`sed`, `tee`, scripts) aren't covered by the edit hooks. The full-check gate still sees the result, but a suppression added from the shell gets through. Local records protect against accidents, not against a determined adversary. **CI and server-side branch protection remain the final authority on what merges.** The pack has known limitations and open questions; both are written up in full in [`claude-code-engineering-rules/README.md`](claude-code-engineering-rules/README.md).

---

## Where it came from

### Lauren Tan: "All Code Is Slop (Except Mine)"

At AI Engineer in November 2026, Lauren Tan ([poteto](https://x.com/poteto)), a React core team member who has worked across codebases at Meta, Netflix and Cursor, made an argument that stuck with us. **You can't make an agent trustworthy by writing it longer instructions.** Trust comes from the environment it works in.

The talk ranks the levers, strongest first:

1. **Architecture and API design** that makes the wrong approach impossible or unnatural.
2. **Deterministic checks**: types, linters, dependency-boundary rules, tests and CI.
3. **Runtime and formal verification** appropriate to the risk.
4. **Written instructions**, last, and only for decisions that genuinely need judgment.

Behind that ranking is a loop. An agent makes a mistake. You find the root cause, design the mistake out or add a targeted check, verify the check, and every future run is constrained by default. Order matters too: clean up the codebase and the checks *before* you scale agent throughput, or you just produce slop faster. The codebase is the agent's biggest source of context, so existing patterns aren't automatically good ones.

### pstack

[pstack](https://github.com/cursor/plugins/tree/main/pstack) is Lauren's open-source (MIT) plugin of agent skills and workflows, built around the idea of *"if you want to go fast, go deep first"*. It puts the talk into practice: rigorous, verifiable agent work that lets you run agents in parallel with confidence, and less code but better code.

Watching pstack work raised the question this repository answers: **what would it take to make those principles hold in any Claude Code session, whether or not anyone invokes a skill?** pstack shapes *how an agent works* on a task. This pack shapes *what an agent is allowed to get away with* in a repository. The two complement each other. This pack doesn't include or modify any pstack code; it's an independent implementation of the same philosophy, built from Claude Code's native hooks and permissions.

We also borrowed from the Karpathy guidelines for LLM coding ([multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills), MIT): state your assumptions, keep changes minimal, and make every changed line trace to the request. Their wording is paraphrased here, not copied.

---

## How it evolved

Each release is a tagged commit. Check out a tag, or diff two of them, to see exactly what changed and why.

| Tag | Theme | What changed |
|---|---|---|
| [`v1`](../../tree/v1) | **Advice** | `CLAUDE.md` plus seven topic rule files that turn the talk into written guidance. Nothing is enforced. |
| [`v2`](../../tree/v2) | **Sharper advice** | Rewritten around the talk's core loop and the "inverted pyramid": directory structure as a control mechanism, feature maps and drivers, and sequencing before scaling. Still only Markdown. |
| [`v3`](../../tree/v3) | **Enforcement** | Adversarial review of v2 against the talk transcript. The pack now follows its own ranking: hooks and permissions do the enforcing, and the Markdown shrinks to about a fifth of v2 and merges with the Karpathy guidelines. `bans.md` arrives, along with the `verify-feature` and `add-guardrail` skills. |
| [`v4`](../../tree/v4) | **Hardening** | The edit guard fails closed and catches focused tests. Verification records with provenance (`check.py`), an executable driver contract (`verify.py`), per-session state, a fingerprint that includes HEAD, 36 mutation-tested tests, and a live smoke test as the release gate. |
| [`v4.1`](../../tree/v4.1) | **Targeted hardening** | Baselines survive compaction; evidence path traversal and symlink escapes are rejected; each run gets its own evidence directory; failed results are reused. |
| [`v4.1.1`](../../tree/v4.1.1) | **Fix: stale failures** | Replayed failures are labelled `SAVED result` and point to a fresh `check.py` run. Timeouts are never replayed. Records are bound to the pack version. |
| [`v4.1.2`](../../tree/v4.1.2) | **Fix: replay scope** | Saved failures are replayed only within their own stop chain, and the replay message no longer pushes for code changes. 48 tests. Code freeze pending the live smoke run. |

The last commit adds the operator script for that live smoke run: [`smoke-test/SMOKE-RUN-v4.1.2.md`](claude-code-engineering-rules/smoke-test/SMOKE-RUN-v4.1.2.md).

> **Status:** v4.1.2 has passed its unit and mutation tests and a simulated smoke sequence. The live smoke test on an authenticated Claude Code install (S0 to S12) is still outstanding, so treat the pack as release-candidate quality until it's done.

---

## Quick start

Requirements: Claude Code **2.1.295 or later** (for `onFailure` on hooks), `python3` on PATH, and git.

```bash
git clone <this-repo> && cd <this-repo>/claude-code-engineering-rules

# 1. Prove the pack works on your machine
python3 .claude/tests/test_guardrails.py          # expect: Ran 48 tests ... OK

# 2. Rehearse in a throwaway repo (about 20 minutes)
bash smoke-test/setup_smoke_repo.sh /tmp/guardrail-smoke
#    then follow smoke-test/SMOKE-TEST.md

# 3. Install into your repository (cp -n never overwrites existing files)
cd /path/to/your/repo
cp -rn /path/to/pack/{CLAUDE.md,.claude,docs} .
```

Then fill in `.claude/guardrails.env`:

```ini
FAST_CHECK_CMD=npx eslint --max-warnings=0 {file}
FULL_CHECK_CMD=npm run lint && npx tsc --noEmit && npm test
DRIVER_CMD=python3 examples/driver_stub.py
```

Replace the example rows in `.claude/rules/bans.md` and `docs/feature-map.md` with your own, then run `/hooks` in Claude Code to confirm everything loaded. The [pack README](claude-code-engineering-rules/README.md) covers merging with an existing `CLAUDE.md` or `settings.json`, the `.gitignore` entries, and Windows notes.

## Repository layout

```
.
├── README.md                          ← you are here
└── claude-code-engineering-rules/     ← the pack, as it stands at the latest tag
    ├── CLAUDE.md                      judgment rules + final-report format
    ├── .claude/
    │   ├── settings.json              hooks + permission deny/ask rules
    │   ├── guardrails.env             human-owned check commands
    │   ├── hooks/                     session_start, block_suppressions, post_edit_check, stop_gate
    │   ├── tools/                     check.py (recorded full check), verify.py (driver contract)
    │   ├── skills/                    verify-feature, add-guardrail
    │   ├── rules/bans.md              banned patterns, each tied to its enforcing check
    │   └── tests/                     the pack's own test suite
    ├── docs/feature-map.md            feature + scenario IDs for runtime verification
    ├── examples/                      ESLint, dependency-cruiser and ruff bans; reference driver
    └── smoke-test/                    disposable-repo builder + live release checklist
```

The pack sits in a subfolder on purpose. Its `.claude/` directory only takes effect once you copy it to the root of a repository, so browsing or contributing here won't switch the hooks on.

## Credits

- **Lauren Tan**, *All Code Is Slop (Except Mine)*, AI Engineer, November 2026, and [pstack](https://github.com/cursor/plugins/tree/main/pstack). This pack is an independent take on her ideas and isn't affiliated with or endorsed by her or Cursor.
- **Andrej Karpathy's** observations on LLM coding pitfalls, via [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) (MIT).
- v3 onward was shaped by adversarial review rounds between a human reviewer and Claude.
