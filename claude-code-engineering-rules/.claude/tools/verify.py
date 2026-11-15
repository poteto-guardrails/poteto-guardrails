"""Run one runtime-verification scenario through the project's driver and enforce the contract.

  python3 .claude/tools/verify.py --feature <ID> --scenario <ID> [--task <name>]

DRIVER CONTRACT (any language; DRIVER_CMD in .claude/guardrails.env is the entry point):
  invoked as:   <DRIVER_CMD> --feature <ID> --scenario <ID> --out <DIR>
  exit code:    0 = pass, 1 = fail, 3 = scenario not supported by the driver
  must write:   <DIR>/result.json
                {"feature": "<ID>", "scenario": "<ID>", "status": "pass" | "fail" | "unsupported",
                 "summary": "<one line>", "evidence": ["<file in DIR>", ...]}
  evidence:     every listed file must exist in DIR; a "pass" needs at least one.

Anything else (missing or invalid result.json, status not matching the exit code, missing
evidence, a crash or a timeout) is a CONTRACT VIOLATION and counts as not verified.
Results are appended to verification/<task>/log.jsonl.

Exit codes: 0 pass, 1 fail, 2 unknown feature, 3 not configured or unsupported, 4 violation.
"""
import argparse
import json
import os
import re
import shlex
import shutil
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "hooks"))
import _guardrails as g  # noqa: E402

ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
STATUS_FOR_EXIT = {0: "pass", 1: "fail", 3: "unsupported"}


def feature_map():
    """Feature ID -> set of scenario IDs, from the table in docs/feature-map.md."""
    path = os.path.join(g.project_dir(), "docs", "feature-map.md")
    features = {}
    if not os.path.exists(path):
        return features
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            cells = [c.strip().strip("`") for c in line.strip().strip("|").split("|")]
            if len(cells) < 4 or not ID_RE.match(cells[0]) or cells[0].lower() == "feature id":
                continue
            features[cells[0]] = {s.strip().strip("`") for s in cells[3].split(",") if s.strip()}
    return features


def violation(reason):
    return {"status": "violation", "summary": reason, "evidence": []}


def check_contract(out_dir, feature, scenario, code):
    path = os.path.join(out_dir, "result.json")
    if code == 124:
        return violation("driver timed out")
    if not os.path.isfile(path):
        return violation(f"driver exited {code} without writing result.json")
    try:
        with open(path, encoding="utf-8") as fh:
            res = json.load(fh)
    except ValueError as exc:
        return violation(f"result.json is not valid JSON ({exc})")
    if not isinstance(res, dict):
        return violation("result.json is not an object")
    if res.get("feature") != feature or res.get("scenario") != scenario:
        return violation("result.json feature/scenario don't match the request")
    status = res.get("status")
    if status not in ("pass", "fail", "unsupported"):
        return violation(f"invalid status {status!r}")
    if STATUS_FOR_EXIT.get(code) != status:
        return violation(f"status {status!r} doesn't match exit code {code}")
    evidence = res.get("evidence")
    if not isinstance(evidence, list) or not all(isinstance(e, str) for e in evidence):
        return violation("evidence must be a list of file names")
    missing = [e for e in evidence if not os.path.isfile(os.path.join(out_dir, e))]
    if missing:
        return violation(f"evidence files missing: {missing}")
    if status == "pass" and not evidence:
        return violation("a pass must include at least one evidence file")
    if not isinstance(res.get("summary", ""), str):
        return violation("summary must be a string")
    return {"status": status, "summary": res.get("summary", ""), "evidence": evidence}


def main():
    ap = argparse.ArgumentParser(description="Run one verification scenario via the driver contract.")
    ap.add_argument("--feature", required=True)
    ap.add_argument("--scenario", required=True)
    ap.add_argument("--task", default="adhoc")
    args = ap.parse_args()
    for label, value in (("feature", args.feature), ("scenario", args.scenario), ("task", args.task)):
        if not ID_RE.match(value):
            print(f"RUNTIME: invalid {label} id {value!r} (letters, digits, . _ - only)")
            return 2

    cfg = g.load_config()
    driver = cfg.get("DRIVER_CMD", "")
    if not driver:
        print("RUNTIME: NOT CONFIGURED (DRIVER_CMD is empty). Report this behaviour as unverified at runtime.")
        return 3
    features = feature_map()
    if args.feature not in features:
        print(f"RUNTIME: unknown feature {args.feature!r}; it isn't in docs/feature-map.md."
              " Report it as unverified and propose the map entry under 'Guardrail candidates'.")
        return 2
    note = "" if args.scenario in features[args.feature] else \
        " (note: scenario not listed in docs/feature-map.md; propose adding it)"

    task_dir = os.path.join(g.project_dir(), "verification", args.task)
    out_dir = os.path.join(task_dir, args.feature, args.scenario)
    shutil.rmtree(out_dir, ignore_errors=True)
    os.makedirs(out_dir)
    cmd = (f"{driver} --feature {shlex.quote(args.feature)} --scenario {shlex.quote(args.scenario)}"
           f" --out {shlex.quote(out_dir)}")
    code, output, seconds = g.run(cmd, g.int_setting(cfg, "DRIVER_TIMEOUT", 300))
    with open(os.path.join(out_dir, "driver-output.log"), "w", encoding="utf-8") as fh:
        fh.write(output)
    result = check_contract(out_dir, args.feature, args.scenario, code)

    rel_out = g.rel_path(out_dir)
    with open(os.path.join(task_dir, "log.jsonl"), "a", encoding="utf-8") as fh:
        fh.write(json.dumps({
            "feature": args.feature, "scenario": args.scenario, "status": result["status"],
            "summary": result["summary"], "evidence": [f"{rel_out}/{e}" for e in result["evidence"]],
            "driver_exit": code, "duration_s": seconds, "ran_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "tree": (g.fingerprint() or "no-git")[:12], "command": cmd,
        }) + "\n")

    label = {"pass": "PASS", "fail": "FAIL", "unsupported": "NOT RUN (driver doesn't support this scenario)",
             "violation": "NOT VERIFIED (driver contract violation)"}[result["status"]]
    evidence = ", ".join(f"{rel_out}/{e}" for e in result["evidence"]) or "none"
    if result["status"] != "pass":
        print(g.tail(output, 40))
    summary = result["summary"].strip()
    if summary and summary[-1] not in ".!?":
        summary += "."
    print(f"RUNTIME: {args.feature} / {args.scenario}: {label}. {summary}"
          f" Evidence: {evidence}{note}".replace(". .", "."))
    return {"pass": 0, "fail": 1, "unsupported": 3, "violation": 4}[result["status"]]


if __name__ == "__main__":
    sys.exit(main())
