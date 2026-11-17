"""SessionStart: record this session's baseline tree and tell Claude exactly which checks exist.

Stdout from a SessionStart hook is added to Claude's context.
"""
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _guardrails as g  # noqa: E402

event = g.read_event_lenient()
session = event.get("session_id")
cfg = g.load_config()

# Baseline: what the tree looked like before this session touched anything. The stop gate
# skips turns where the tree still matches it (questions, reviews) and checks everything else.
if session:
    state = g.load_session(session)
    # SessionStart can fire for startup, resume, clear, and compact.  The baseline
    # belongs to the session, not to a particular context window: resetting it on
    # compaction would bless edits made earlier in the same session and let Stop skip.
    if not state.get("baseline"):
        state["baseline"] = g.fingerprint()
    g.save_session(session, state)

lines = [f"Guardrails v{g.PACK_VERSION} (config: ~/.claude/guardrails.env, overridden by"
         " <repo>/.claude/guardrails.env):"]
items = [
    ("FAST_CHECK_CMD", "After each edit (automatic)"),
    ("FULL_CHECK_CMD", "Full check: run `python3 ~/.claude/guardrails/tools/check.py` before your final report;"
                       " the stop gate re-runs it if the tree changed since"),
    ("DRIVER_CMD", "Runtime verification: `python3 ~/.claude/guardrails/tools/verify.py --feature ID --scenario ID`"),
]
missing = []
for key, label in items:
    if cfg.get(key):
        lines.append(f"- {label}. Command: `{cfg[key]}`")
    else:
        missing.append(key)
if missing:
    lines.append("NOT CONFIGURED: " + ", ".join(missing)
                 + ". Those checks don't exist here. Say so in your final report and never claim they ran.")


def claude_code_version():
    """Version of the running Claude Code binary, or None if it can't be determined."""
    exe = os.environ.get("CLAUDE_CODE_EXECPATH") or "claude"
    try:
        out = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", out or "")
    return tuple(int(x) for x in m.groups()) if m else None


version = claude_code_version()
warning = None
if version and version < g.MIN_CLAUDE_CODE:
    need = ".".join(map(str, g.MIN_CLAUDE_CODE))
    have = ".".join(map(str, version))
    warning = (f"Guardrails: Claude Code {have} is older than {need}. The suppression guard may fail"
               " OPEN here (onFailure is ignored), so a crashed guard lets edits through. Upgrade.")
    lines.append("WARNING: " + warning)

if warning:  # make it visible to the user as well as to Claude
    print(json.dumps({"systemMessage": warning, "hookSpecificOutput": {
        "hookEventName": "SessionStart", "additionalContext": "\n".join(lines)}}))
else:
    print("\n".join(lines))
