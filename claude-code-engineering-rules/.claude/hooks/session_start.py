"""SessionStart: tell Claude which checks exist, so it never has to guess the commands."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _guardrails as g  # noqa: E402

g.read_event()
cfg = g.load_config()
lines = ["Guardrails for this repository (from .claude/guardrails.env):"]
labels = {
    "FAST_CHECK_CMD": "After each edit",
    "FULL_CHECK_CMD": "Before finishing (stop gate)",
    "DRIVER_CMD": "App driver for runtime verification",
}
missing = []
for key, label in labels.items():
    value = cfg.get(key, "")
    if value:
        lines.append(f"- {label}: `{value}`")
    else:
        missing.append(label)
if missing:
    lines.append(
        "NOT CONFIGURED: " + "; ".join(missing)
        + ". Say so in your final report and don't claim these checks ran."
        + " Running the repo's own commands by hand is fine; report exactly what you ran."
    )
print("\n".join(lines))
