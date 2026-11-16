"""Stop: Claude may not finish a turn that changed the working tree until the full check
has passed on exactly that tree.

Decision order:
  1. Tree matches this session's baseline         -> nothing changed, allow.
  2. A valid record exists for (tree, command)     -> already verified (usually by check.py), allow.
  3. Otherwise run the full check now and record the result.
     - pass                                        -> allow.
     - fail, retries left in this stop chain       -> block (exit 2), output goes to Claude.
     - fail, retries used up                       -> allow, but warn the user: NOT verified.

Retries are per session and per stop chain: stop_hook_active=false starts a new chain.
Never fails closed: a broken stop gate must not trap the session. Failures are made
visible to the user instead.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _guardrails as g  # noqa: E402


def warn_user(message):
    print(json.dumps({"systemMessage": message}))
    sys.exit(0)


def main():
    event = g.read_event_lenient()
    session = event.get("session_id") or "unknown"
    cfg = g.load_config()
    cmd = cfg.get("FULL_CHECK_CMD", "")
    state = g.load_session(session)
    fp = g.fingerprint()
    changed = fp is None or fp != state.get("baseline")

    if not cmd:
        if changed and fp is not None:
            warn_user("Guardrails: files changed but FULL_CHECK_CMD isn't configured. This work is unverified.")
        sys.exit(0)
    if not changed:
        sys.exit(0)
    record = g.find_record(fp, cmd)
    if g.record_is_valid(record, fp, cmd):
        sys.exit(0)

    # Reuse a failure for the identical tree and command too. Claude is sent back
    # with the original diagnostics; a changed tree gets a new fingerprint and run.
    if g.record_is_current(record, fp, cmd):
        code = record.get("exit_code", 1)
        output = record.get("output_tail", "")
    else:
        timeout = g.int_setting(cfg, "FULL_CHECK_TIMEOUT", 840)
        code, output, seconds = g.run(cmd, timeout)
        fp_after = g.fingerprint()
        if fp is not None and fp_after == fp:
            g.write_record(fp, cmd, code, seconds, "stop_gate", session, output)
        elif code == 0:
            warn_user("Guardrails: the full check passed but modified files while running"
                      " (formatter?). Re-run it, or review the changes it made.")
    if code == 0:
        state.pop("retries", None)
        g.save_session(session, state)
        sys.exit(0)

    retries = state.get("retries", 0) + 1 if event.get("stop_hook_active") else 1
    state["retries"] = retries
    g.save_session(session, state)
    max_retries = g.int_setting(cfg, "STOP_GATE_MAX_RETRIES", 2)
    if retries <= max_retries:
        g.block(
            f"Stop gate: the full check failed (attempt {retries} of {max_retries}).\n"
            f"Command: {cmd}\n{g.tail(output)}\n"
            "Fix the root cause. Don't add suppressions, skip tests or edit check configuration."
            " If the failure isn't caused by your change, or can't be fixed within the task,"
            " stop and explain it under 'Not passing' in your final report."
        )
    warn_user(f"Guardrails: the full check is still failing after {max_retries} retries."
              f" This work is NOT verified. Command: {cmd}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:  # visible, but never traps the session
        warn_user(f"Guardrails: the stop gate crashed ({type(exc).__name__}: {exc})."
                  " This work is NOT verified.")
