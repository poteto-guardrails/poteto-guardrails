"""Reference driver that implements the contract in ~/.claude/guardrails/tools/verify.py.

Replace the bodies of the scenario functions with real automation (Playwright, a CLI,
HTTP calls). Keep the contract: arguments in, result.json plus evidence out, exit 0/1/3.

  DRIVER_CMD=python3 ~/.claude/guardrails/examples/driver_stub.py
"""
import argparse
import json
import os
import sys


def sidebar_empty(out):
    # Real driver: launch the app with an empty profile, screenshot the sidebar, assert the empty state.
    with open(os.path.join(out, "sidebar-empty.txt"), "w") as fh:
        fh.write("Stub evidence: the sidebar showed the 'No chats yet' empty state.\n")
    return True, "Empty state shown", ["sidebar-empty.txt"]


def sidebar_rename(out):
    with open(os.path.join(out, "sidebar-rename.txt"), "w") as fh:
        fh.write("Stub evidence: renamed 'Chat 1' to 'Plans'; the new title persisted after reload.\n")
    return True, "Rename persisted after reload", ["sidebar-rename.txt"]


SCENARIOS = {
    ("chat-sidebar", "empty"): sidebar_empty,
    ("chat-sidebar", "rename"): sidebar_rename,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--feature", required=True)
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    result = {"feature": a.feature, "scenario": a.scenario}
    fn = SCENARIOS.get((a.feature, a.scenario))
    if fn is None:
        result.update(status="unsupported", summary="No automation for this scenario yet", evidence=[])
        code = 3
    else:
        ok, summary, evidence = fn(a.out)
        result.update(status="pass" if ok else "fail", summary=summary, evidence=evidence)
        code = 0 if ok else 1
    with open(os.path.join(a.out, "result.json"), "w") as fh:
        json.dump(result, fh, indent=1)
    return code


if __name__ == "__main__":
    sys.exit(main())
