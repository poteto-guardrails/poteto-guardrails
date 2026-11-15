# Claude Code engineering rules — v3

A Claude Code setup based on Lauren Tan's talk **"All Code Is Slop (Except Mine)"** (AI Engineer, Nov 2026), merged with the **Karpathy guidelines** for LLM coding. It replaces v2.

> **To the v2 author:** v3 came out of an adversarial review of v2 against the talk transcript. The section "What changed from v2, and why" lists each criticism and how v3 answers it. "Questions for the reviewer" at the end is where your feedback would help most. Please push back where you think v3 got the talk wrong.

---

## The idea in one paragraph

The talk ranks the ways to make agents trustworthy: (1) architecture and API design, (2) deterministic checks such as types, linters, dependency rules and tests, (3) runtime and formal verification, and only last (4) written instructions, for things that need judgment. **v3 is built in that order.** The enforceable rules live in Claude Code hooks and permissions, which run whether or not the model reads them. The Markdown is limited to judgment calls and is about a fifth the size of v2's.

## What's in the pack

| Path | Layer | What it does |
|---|---|---|
| `.claude/settings.json` | Deterministic | Registers the hooks; **denies** force-push, hard reset and `rm -rf`; **asks** before push, merge, publish, and before any edit to lint, type-check, CI, hook or settings config |
| `.claude/guardrails.env` | Config (human-owned) | The commands the hooks run: fast per-file check, full check, app driver |
| `.claude/hooks/block_suppressions.py` | Deterministic | **Blocks** any edit that *adds* `eslint-disable`, `@ts-ignore`, `as any`, `# noqa`, `.skip(`, `@pytest.mark.skip` and similar. Editing near an existing marker is allowed |
| `.claude/hooks/post_edit_check.py` | Deterministic | Runs the fast lint/format check on each edited file and sends failures straight back to Claude |
| `.claude/hooks/stop_gate.py` | Deterministic | Claude can't finish a turn that changed files until the full check passes. It retries a limited number of times, then lets the turn end and tells you the work is **not verified** |
| `.claude/hooks/session_start.py` | Context | Tells Claude the exact check commands, and says loudly when a check isn't configured |
| `.claude/hooks/test_hooks.py` | Verification | Self-test for the hooks (27 cases). Checks the checks |
| `CLAUDE.md` | Judgment | About 400 words: Karpathy's four principles reconciled with the talk, plus the final report format |
| `.claude/rules/bans.md` | Judgment → pointer | A table of banned patterns. **Each row must name the check that enforces it** |
| `.claude/skills/verify-feature/` | Verification | Runtime verification with the feature map, the app driver and saved evidence (the talk's "runtime verification skills") |
| `.claude/skills/add-guardrail/` | Process | Human-invoked only (`/add-guardrail`). Turns a recurring mistake into a check: design first, then lint or test, with an error message that names the fix |
| `docs/feature-map.md` | Shared vocabulary | Template for the user-facing feature inventory the talk describes |
| `examples/` | Reference | ESLint bans with root-cause messages, a dependency-cruiser rule for the Electron main/renderer split, and a ruff banned-API list |

## Install

```bash
# from the root of the target repository; refuses to overwrite existing files
cp -rn /path/to/pack/{CLAUDE.md,.claude,docs} .
cp -rn /path/to/pack/examples ./claude-guardrail-examples   # optional, reference only
python3 .claude/hooks/test_hooks.py                          # should print ALL PASSED
```

If you already have a `CLAUDE.md` or `.claude/settings.json`, `cp -n` skips them. Merge by hand. Then:

1. **Fill in `.claude/guardrails.env`.** Until `FAST_CHECK_CMD` and `FULL_CHECK_CMD` are set, the hooks do nothing (and Claude is told so at the start of every session). This is the step that matters most.
2. Replace the example rows in `.claude/rules/bans.md` and `docs/feature-map.md`.
3. Decide whether runtime evidence in `verification/` should be committed or added to `.gitignore`.
4. Optionally set `DRIVER_CMD` (a Playwright project, a CLI script, or similar) so `verify-feature` can run the app.
5. Run `/hooks` and `/permissions` in Claude Code to confirm everything loaded.

Requirements: `python3` on PATH and git. On Windows, change `python3` to `python` or `py` in `settings.json`.

## What changed from v2, and why

| v2 problem found in review | v3 response |
|---|---|
| **No enforcement at all.** About 20 KB of Markdown telling the agent that Markdown is the weakest control | Hard rules moved into hooks and permissions. Suppressions, check failures and protected config are enforced, not requested |
| **Everything loaded every session.** `description:` frontmatter isn't a field Claude Code reads, so all 7 rule files loaded unconditionally | Always-loaded text cut from about 2,500 words to about 500. Procedures moved into skills, which load only when used |
| **The human's job given to the agent.** "When the environment is incomplete, improve the environment", and the agent writing its own checks | Guardrails belong to humans. The agent *proposes* checks under "Guardrail candidates". `/add-guardrail` is human-invoked (`disable-model-invocation: true`), and config edits need approval |
| **Written excuses.** "Document the workaround", "suppress with a justified reason", plus many "where practical" hedges | Suppressions are blocked by a hook. Justification comments are banned. The only escape route is *stop and report*, which costs the agent nothing to take and is visible to you |
| **The talk's bans softened into "scrutinise timers"** | `bans.md` holds hard bans, each backed by a named check. The examples show the talk's own bans (timers, `useEffect`, main/renderer imports) as lint rules with root-cause messages |
| **Contradictory scope** ("keep focused" vs "improve local quality" vs "bring code into compliance") | Karpathy's *surgical changes* decides it: every line traces to the request, and debt goes under **Noticed, not touched**. The talk's "don't copy debt" survives as: match the *style*, not banned *patterns* |
| **"More verification" read as "more tests"** | Verification means evidence: the stop gate, runtime scenarios with saved artefacts, and a report that separates *ran* from *not run* |
| **Feature map and driver were prose** | Feature map template, `DRIVER_CMD` config, and a `verify-feature` skill that uses both |
| **The talk's outer "software factory" loop** | Left out on purpose. The talk presents it as what you get *after* the foundation exists, and it's partly a product pitch. v3 is the foundation. Auto-merge belongs in CI and branch protection, not agent instructions |
| **No plan for unattended runs** ("ask" with nobody there) | Most conservative reading, written under **Assumptions**, nothing irreversible. The stop gate's retry cap stops endless loops |
| **`cp -r` silently overwrote CLAUDE.md** | `cp -rn` |

### How the Karpathy guidelines were merged

| Karpathy | Where it went | Change |
|---|---|---|
| Think before coding | CLAUDE.md "Before coding" | Added the unattended-run fallback |
| Simplicity first | CLAUDE.md "Writing code" | Unchanged in substance |
| Surgical changes | CLAUDE.md "Writing code" | Kept as the scope rule. "Match existing style" is narrowed so it can't be used to copy banned patterns (the talk's weeds-in-the-garden point) |
| Goal-driven execution | CLAUDE.md "Before coding" plus the stop gate | "Loop until verified" is now *enforced* by the stop gate rather than only requested |

The Karpathy text is paraphrased, not copied verbatim. Source: [multica-ai/andrej-karpathy-skills](https://github.com/multica-ai/andrej-karpathy-skills) (MIT, per the skill's frontmatter).

## Known limitations (please challenge these)

- **Bash permission rules are prefix matches, so they're best effort.** `git push` buried in a script, or `sed -i` on a lint config, gets past them. Real protection for main belongs in **server-side branch protection** and CI, which the pack can't configure.
- **Bash edits skip the hooks.** The hooks watch Edit/Write/MultiEdit. A file changed with `sed`, `tee` or a script isn't seen by the suppression or per-file checks. The stop gate still runs the full check over the working tree, so failures are caught there, but a new suppression added that way isn't.
- **The suppression regex is a blunt instrument.** `as any` and `xit(` patterns could flag strings or docs. Tune `SUPPRESSION_REGEX` and `SUPPRESSION_EXEMPT_GLOBS` per repository. Human-written suppressions are unaffected; only Claude's edits are checked.
- **`pyproject.toml` and `package.json`.** `pyproject.toml` is protected (ask) because it holds lint config, so adding a dependency prompts too. `package.json` is *not* protected, which means an inline `eslintConfig` there could be edited freely.
- **The stop gate runs the full check** on every turn that leaves changes since the last pass. On a slow test suite, keep `FULL_CHECK_CMD` to what a merge requires, and push heavy suites (fuzzing, formal checks) to CI.
- **Hook behaviour was checked against documentation and the self-test, not yet in a live Claude Code session.** Event names, exit-code-2 semantics, `stop_hook_active` and `systemMessage` follow the hooks reference as of late 2026. Run `/hooks` after installing.

## Questions for the reviewer

1. **Banning `as any` and test skips outright:** too strict for your codebases, or is that the point?
2. **Should the stop gate run the full suite, or only tests affected by the diff?** The second is faster but needs per-stack tooling.
3. **Is cutting the outer-loop section the right call?** Or is there a minimal, safe version worth keeping (for example, a scheduled fuzzing run that opens PRs but never merges)?
4. **Anything from the talk v3 dropped that you think is essential?** Formal verification (TLA+/Lean) appears only as an option inside the human-invoked `/add-guardrail` skill. That's deliberate.
5. **Did the review misread the talk anywhere?** The source transcript is a machine translation (the product name appears as Grokbot, Graph Bot and Grabot).

## Credits

- Lauren Tan, *All Code Is Slop (Except Mine)*, AI Engineer, November 2026.
- Andrej Karpathy's observations on LLM coding pitfalls, via the `karpathy-guidelines` skill (MIT).
- v2 by the original author. v3 by adversarial review and rework.
