"""Run the full check once, show the result, and record what was verified.

  python3 ~/.claude/guardrails/tools/check.py            run FULL_CHECK_CMD and record the result
  python3 ~/.claude/guardrails/tools/check.py --status   is there a valid passing record for the tree as it is now?

The last line of output is a one-line summary to quote in the final report. The stop gate
accepts a passing record for the identical tree and command, so the check isn't run twice.

Exit codes: the check's own exit code; 3 = not configured; 4 = the check changed files while
running (result not recorded); 5 = --status found no valid record.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hooks"))
import _guardrails as g  # noqa: E402


EVIDENCE_EXTS = {".json", ".jsonl", ".log", ".txt", ".md", ".png", ".jpg", ".jpeg", ".gif", ".webp",
                 ".svg", ".html", ".har", ".webm", ".mp4", ".zip", ".trace", ".csv"}


def excluded_non_evidence(cfg):
    """Changed files under FINGERPRINT_EXCLUDE paths that don't look like verification evidence.

    Those paths are invisible to the fingerprint, so code placed there would skip the gate.
    """
    excludes = [p.strip() for p in cfg.get("FINGERPRINT_EXCLUDE", ".claude/verification-runs").split(",") if p.strip()]
    if not excludes or g.git_dir() is None:
        return []
    out = g._git("status", "--porcelain", "-z", "--untracked-files=all", "--", *excludes) or ""
    names = [entry[3:] for entry in out.split("\0") if len(entry) > 3]
    return sorted(n for n in names if os.path.splitext(n)[1].lower() not in EVIDENCE_EXTS)


def status(cfg):
    cmd = cfg.get("FULL_CHECK_CMD", "")
    fp = g.fingerprint()
    rec = g.find_record(fp, cmd)
    if g.record_is_valid(rec, fp, cmd):
        print(f"FULL CHECK STATUS: VERIFIED. Passed at {rec['ran_at']} by {rec['runner']}"
              f" on this exact working tree ({fp[:12]}).")
        return 0
    why = "no git repository" if fp is None else ("last run failed" if rec else "no run for this tree")
    print(f"FULL CHECK STATUS: NOT VERIFIED ({why}). Run: python3 ~/.claude/guardrails/tools/check.py")
    return 5


def main():
    cfg = g.load_config()
    if "--status" in sys.argv:
        return status(cfg)
    cmd = cfg.get("FULL_CHECK_CMD", "")
    if not cmd:
        print("FULL CHECK: NOT CONFIGURED (FULL_CHECK_CMD is empty in ~/.claude/guardrails.env and <repo>/.claude/guardrails.env).")
        return 3

    fp = g.fingerprint()
    code, output, seconds = g.run(cmd, g.int_setting(cfg, "FULL_CHECK_TIMEOUT", 840))
    print(g.tail(output, 200))
    print("-" * 60)
    result = "PASS" if code == 0 else ("TIMEOUT" if code == 124 else "FAIL")
    if fp is None:
        print(f"FULL CHECK: {result} (exit {code}, {seconds}s). Not recorded: not a git repository. `{cmd}`")
        return code
    if g.fingerprint() != fp:
        print(f"FULL CHECK: {result} (exit {code}), but the check modified files while running,"
              f" so the result was NOT recorded. Review the changes and run it again. `{cmd}`")
        return 4
    hidden = excluded_non_evidence(cfg)
    if hidden:
        shown = ", ".join(hidden[:10]) + (f" (+{len(hidden) - 10} more)" if len(hidden) > 10 else "")
        print(f"WARNING: changed files under FINGERPRINT_EXCLUDE don't look like evidence and are NOT"
              f" covered by the stop gate: {shown}. Move code out of excluded paths.")
    g.write_record(fp, cmd, code, seconds, "check.py", os.environ.get("CLAUDE_SESSION_ID") or os.environ.get("CLAUDE_CODE_SESSION_ID"), output)
    print(f"FULL CHECK: {result} (exit {code}, {seconds}s). Recorded for working tree {fp[:12]}. `{cmd}`")
    return code


if __name__ == "__main__":
    sys.exit(main())
