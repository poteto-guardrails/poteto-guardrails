"""Stop: run the full check before Claude may finish a turn that changed the working tree.

- Skips when nothing changed since the last passing run (Q&A turns cost nothing).
- Sends Claude back up to STOP_GATE_MAX_RETRIES times, then lets it stop and
  tells the user, so a stubborn failure can't loop forever.
"""
import hashlib
import json
import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _guardrails as g  # noqa: E402


def tree_fingerprint():
    """Hash of tracked changes plus untracked files; None if not a git repo."""
    try:
        diff = subprocess.run(["git", "diff", "HEAD", "--binary"], cwd=g.project_dir(),
                              capture_output=True, timeout=60)
        status = subprocess.run(["git", "status", "--porcelain", "--untracked-files=all"],
                                cwd=g.project_dir(), capture_output=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if status.returncode != 0:
        return None
    if not status.stdout.strip():
        return "clean"
    digest = hashlib.sha256(diff.stdout + status.stdout)
    for line in status.stdout.decode(errors="replace").splitlines():
        if line.startswith("??"):
            path = os.path.join(g.project_dir(), line[3:].strip().strip('"'))
            try:
                with open(path, "rb") as fh:
                    digest.update(fh.read())
            except OSError:
                pass
    return digest.hexdigest()


def state_path():
    key = hashlib.sha256(g.project_dir().encode()).hexdigest()[:16]
    folder = os.path.join(tempfile.gettempdir(), "claude-guardrails")
    os.makedirs(folder, exist_ok=True)
    return os.path.join(folder, key + ".json")


def load_state():
    try:
        with open(state_path(), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return {}


def save_state(state):
    with open(state_path(), "w", encoding="utf-8") as fh:
        json.dump(state, fh)


def main():
    event = g.read_event()
    if "--reset" in sys.argv:  # UserPromptSubmit: each new request gets fresh retries
        state = load_state()
        save_state({"last_pass": state.get("last_pass")})
        sys.exit(0)
    cfg = g.load_config()
    cmd = cfg.get("FULL_CHECK_CMD", "")
    if not cmd:
        sys.exit(0)

    fingerprint = tree_fingerprint()
    state = load_state()
    if fingerprint == "clean" or (fingerprint and fingerprint == state.get("last_pass")):
        sys.exit(0)

    timeout = int(cfg.get("FULL_CHECK_TIMEOUT") or 840)
    code, output = g.run(cmd, timeout)
    session = event.get("session_id", "")
    if code == 0:
        save_state({"last_pass": fingerprint})
        sys.exit(0)

    retries = state.get("retries", {}) if state.get("session") == session else {}
    count = retries.get("count", 0) + 1
    save_state({"last_pass": state.get("last_pass"), "session": session, "retries": {"count": count}})
    max_retries = int(cfg.get("STOP_GATE_MAX_RETRIES") or 2)

    if count <= max_retries:
        g.block(
            f"Stop gate: the full check failed (attempt {count} of {max_retries}).\n"
            f"Command: {cmd}\n{g.tail(output)}\n"
            "Fix the root cause. Don't add suppressions, skip tests or edit check configuration."
            " If the failure isn't caused by your change, or can't be fixed within the task,"
            " stop and explain it under 'Not passing' in your final report."
        )
    # Out of retries: let the turn end, but make sure the human sees it.
    print(json.dumps({
        "systemMessage": f"Stop gate: the full check is still failing after {max_retries} retries."
                         f" The work is NOT verified. Command: {cmd}"
    }))
    sys.exit(0)


main()
