# Global variant: one install for every project

This is the same guardrail pack as [`../local/`](../local/) (v4.1.2), ported to install once into `~/.claude/` so it applies to **every project you open in Claude Code**. Its version is `4.1.2-global.1`.

Choose this variant if you want the same standards everywhere without copying files into each repository. Choose [`local/`](../local/) if you want the rules committed with one repository, shared with your team, and enforced only there.

> **Don't run both.** A repository that has the local pack in its `.claude/settings.json` on a machine with the global variant installed runs both sets of hooks. Pick one per machine, or remove the local copy from that repository.

## What's different from the local pack

| Area | Local pack | Global variant |
|---|---|---|
| Install location | `<repo>/CLAUDE.md`, `<repo>/.claude/` | `~/.claude/CLAUDE.md`, `~/.claude/guardrails/`, `~/.claude/skills/`, merged into `~/.claude/settings.json` |
| Config | `<repo>/.claude/guardrails.env` only | **Layered**: `~/.claude/guardrails.env` holds defaults, and `<repo>/.claude/guardrails.env` overrides them key by key. An empty value in the repo file switches a global check off |
| Work-destroying commands (force-push, `reset --hard`, `clean -f`, `rm -rf`…) | **Denied** | **Ask** every time. `CLAUDE.md` tells Claude never to run one on its own initiative and to hand you the command instead. It runs one only when you explicitly ask, with a one-off approval. The list also covers `find -delete`, `checkout -- .`, `restore`, `switch --discard-changes`, `stash drop`/`clear` and `branch -D` |
| Protected config | `CLAUDE.md`, `.claude/**`, CI, lint and type-check config | All of that in every repo, plus `~/.claude/CLAUDE.md`, `~/.claude/settings*.json`, `~/.claude/guardrails.env`, `~/.claude/guardrails/**` and `~/.claude/skills/**` |
| Claude Code version | Documented requirement | Session start **warns you and Claude** when Claude Code is older than 2.1.295, because older versions ignore `onFailure` and the guard could let edits through when it breaks |
| Driver exit 3 ("unsupported") | Open question | Reported as **not run**; it doesn't block finishing |
| Excluded fingerprint paths | Open question | `check.py` **warns** when `FINGERPRINT_EXCLUDE` paths hold changed files that don't look like evidence (code hidden there would skip the gate) |
| Project checks | Configured by hand | `CLAUDE.md` tells Claude to offer, once per session, to set up `FAST_CHECK_CMD` and `FULL_CHECK_CMD` from the project's own tooling, and to change nothing until you agree |
| Tests | 48 | **53**: the pack's 48 plus 5 for layered config, the version warning and the excluded-path warning. They're isolated from your real `~/.claude/guardrails.env` |

Everything else is identical: the fail-closed suppression guard, per-edit fast check, stop gate, verification records, failure-replay rules, driver contract and evidence handling.

## Layout

This folder mirrors `~/.claude/`:

```
global/
├── CLAUDE.md                  → merge into ~/.claude/CLAUDE.md
├── guardrails.env             → ~/.claude/guardrails.env (global defaults; check commands stay per repo)
├── skills/
│   ├── verify-feature/        → ~/.claude/skills/verify-feature/
│   └── add-guardrail/         → ~/.claude/skills/add-guardrail/
└── guardrails/                → ~/.claude/guardrails/
    ├── settings.fragment.json   hooks + permissions to merge into ~/.claude/settings.json
    ├── hooks/                   session_start, block_suppressions, post_edit_check, stop_gate
    ├── tools/                   check.py, verify.py
    ├── templates/               per-repo guardrails.env, bans.md, feature-map.md
    ├── examples/                ESLint, dependency-cruiser and ruff bans; reference driver
    ├── smoke-test/              disposable-repo builder + live checklist
    └── tests/                   53-test self-test
```

## Install

Requirements: Claude Code **2.1.295 or later**, `python3` on PATH, and git.

### Ask Claude

Paste this into Claude Code:

```text
Install the global variant of the Claude Code engineering rules from
https://github.com/poteto-guardrails/poteto-guardrails

1. Clone it to a temporary folder and run
   python3 global/guardrails/tests/test_guardrails.py
   Stop if it doesn't end with OK.
2. Copy global/guardrails/ to ~/.claude/guardrails/ and global/skills/* to
   ~/.claude/skills/. Don't overwrite existing files without showing me the diff.
3. Copy global/guardrails.env to ~/.claude/guardrails.env if it doesn't exist.
4. Merge global/guardrails/settings.fragment.json into ~/.claude/settings.json:
   add its permissions and hooks to mine, keep everything I already have,
   and show me the merged file before saving.
5. Merge global/CLAUDE.md into ~/.claude/CLAUDE.md and show me the result.
6. Run python3 ~/.claude/guardrails/tests/test_guardrails.py and quote the last line.
7. Tell me to restart Claude Code and run /hooks to confirm the hooks loaded.
```

### By hand

```bash
git clone https://github.com/poteto-guardrails/poteto-guardrails.git
cd poteto-guardrails/global

python3 guardrails/tests/test_guardrails.py      # expect: Ran 53 tests ... OK

mkdir -p ~/.claude/skills
cp -rn guardrails ~/.claude/
cp -rn skills/verify-feature skills/add-guardrail ~/.claude/skills/
cp -n guardrails.env ~/.claude/guardrails.env
```

Then merge by hand:

1. **`~/.claude/settings.json`**: add the `permissions` and `hooks` from `~/.claude/guardrails/settings.fragment.json`. If you have no settings file yet, copy the fragment in as `~/.claude/settings.json`.
2. **`~/.claude/CLAUDE.md`**: append `CLAUDE.md` from this folder, or merge it with what you already have.

Restart Claude Code and run `/hooks`. You should see SessionStart, PreToolUse, PostToolUse and Stop.

### Per repository

The hooks now run everywhere, but the per-edit check and the full-check gate need commands, and those belong to each project. Claude offers to set them up the first time you open a repository. To do it yourself:

```bash
mkdir -p .claude/rules docs
cp ~/.claude/guardrails/templates/guardrails.env .claude/guardrails.env          # fill in FAST/FULL_CHECK_CMD
cp ~/.claude/guardrails/templates/bans.md .claude/rules/bans.md                  # optional
cp ~/.claude/guardrails/templates/feature-map.md docs/feature-map.md             # optional, for runtime verification
printf '\n.claude/verification-runs/\n' >> .gitignore
```

## Verify

```bash
python3 ~/.claude/guardrails/tests/test_guardrails.py          # Ran 53 tests ... OK
bash ~/.claude/guardrails/smoke-test/setup_smoke_repo.sh /tmp/guardrail-smoke
# then follow ~/.claude/guardrails/smoke-test/SMOKE-TEST.md
```

The smoke test is adapted for the global install. S9 expects force-push to **ask** rather than be denied. S11 and S12 break the hooks through a temporary `--settings` file, so your real `~/.claude/settings.json` is never edited.

## Limits added by going global

- **Bypass-permissions mode.** Permission `ask` rules don't prompt in bypass-permissions ("full access") mode. There, the rule against destructive commands rests on `CLAUDE.md` alone. Deny rules still apply.
- **Prefix matching.** Bash permission rules are prefix matches: `rm -rf` is covered, `rm -r -f` isn't. They're best effort, as in the local pack.
- **Hooks everywhere.** The hooks run in every directory you open Claude Code in, including folders that aren't git repositories. Outside git there's nothing to fingerprint, so the stop gate runs the full check on every turn (if one is configured) and records nothing.
- **Double install.** A repository with the local pack installed runs both sets of hooks. Remove one.

All the local pack's [known limitations](../local/README.md#known-limitations) still apply.

## Optional extra: `/setup-checks`

Out of the box, this variant only *enforces* checks a project already has, and Claude only offers to wire up tools that already exist. If you'd like your agent to recommend and set up linting, formatting, type-checks and tests where they're missing, add the **[`/setup-checks` extra](../extras/setup-checks/)**. It also writes tests with behaviour changes, flags check failures that were already there, and fixes a bug where `FULL_CHECK_CMD= # note` counted as a passing check. It installs as one skill and two patches on top of this folder, and reports version `4.1.2-global.1+setup-checks.1`.

## Uninstall

1. Remove the `hooks` entries and the guardrail permission rules from `~/.claude/settings.json`. They're listed in `~/.claude/guardrails/settings.fragment.json`.
2. Remove the guardrail sections from `~/.claude/CLAUDE.md`.
3. Delete `~/.claude/guardrails/`, `~/.claude/guardrails.env`, `~/.claude/skills/verify-feature/` and `~/.claude/skills/add-guardrail/`.

Saved verification records live in each repository's `.git/claude-guardrails/` and can be deleted along with them.
