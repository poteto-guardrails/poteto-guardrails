"""PostToolUse (Edit|Write|MultiEdit|NotebookEdit): run the fast per-file check and feed
failures back to Claude. The edit has already happened, so this informs; it can't undo."""
import os
import shlex
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _guardrails as g  # noqa: E402

event = g.read_event_lenient()
cfg = g.load_config()
cmd = cfg.get("FAST_CHECK_CMD", "")
ti = event.get("tool_input") if isinstance(event.get("tool_input"), dict) else {}
file_path = ti.get("file_path") or ti.get("notebook_path") or ""
rel = g.rel_path(file_path)
if not cmd or not rel or not g.matches_any(rel, cfg.get("FAST_CHECK_GLOBS", "")):
    sys.exit(0)
if not os.path.exists(os.path.join(g.project_dir(), rel)):
    sys.exit(0)  # deleted by the edit

timeout = g.int_setting(cfg, "FAST_CHECK_TIMEOUT", 60)
code, output, _ = g.run(cmd.replace("{file}", shlex.quote(rel)), timeout)
if code != 0:
    g.block(f"Fast check failed for {rel} (exit {code}):\n{g.tail(output)}\n"
            "Fix the cause the message points to. Don't suppress it.")
