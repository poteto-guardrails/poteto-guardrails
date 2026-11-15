"""SessionStart: record this session's baseline tree and tell Claude exactly which checks exist.

Stdout from a SessionStart hook is added to Claude's context.
"""
import os
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
    if not (event.get("source") == "resume" and state.get("baseline")):
        state["baseline"] = g.fingerprint()
    g.save_session(session, state)

lines = [f"Guardrails v{g.PACK_VERSION} for this repository (.claude/guardrails.env):"]
items = [
    ("FAST_CHECK_CMD", "After each edit (automatic)"),
    ("FULL_CHECK_CMD", "Full check: run `python3 .claude/tools/check.py` before your final report;"
                       " the stop gate re-runs it if the tree changed since"),
    ("DRIVER_CMD", "Runtime verification: `python3 .claude/tools/verify.py --feature ID --scenario ID`"),
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
print("\n".join(lines))
