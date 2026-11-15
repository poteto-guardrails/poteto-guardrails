"""Shared helpers for the guardrail hooks. Python 3.8+, standard library only."""
import fnmatch
import json
import os
import subprocess
import sys


def project_dir():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def load_config():
    """Read .claude/guardrails.env as plain KEY=VALUE lines (not shell-sourced)."""
    cfg = {}
    path = os.path.join(project_dir(), ".claude", "guardrails.env")
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                cfg[key.strip()] = value.strip()
    except FileNotFoundError:
        pass
    return cfg


def read_event():
    try:
        return json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return {}


def rel_path(path):
    if not path:
        return ""
    root = project_dir()
    try:
        rel = os.path.relpath(os.path.abspath(path), root)
    except ValueError:  # different drive on Windows
        return path.replace("\\", "/")
    return rel.replace("\\", "/")


def matches_any(rel, globs_csv):
    globs = [g.strip() for g in (globs_csv or "").split(",") if g.strip()]
    name = rel.rsplit("/", 1)[-1]
    for g in globs:
        if fnmatch.fnmatch(rel, g) or fnmatch.fnmatch(name, g):
            return True
        if g.endswith("/**") and (rel == g[:-3] or rel.startswith(g[:-2])):
            return True
    return False


def run(cmd, timeout):
    """Run a human-authored command from the repo root. Returns (exit_code, combined_output)."""
    try:
        proc = subprocess.run(
            cmd, shell=True, cwd=project_dir(), capture_output=True,
            text=True, timeout=timeout,
        )
        return proc.returncode, (proc.stdout or "") + (proc.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, f"Timed out after {timeout}s: {cmd}"


def tail(text, lines=60):
    parts = text.rstrip().splitlines()
    if len(parts) <= lines:
        return "\n".join(parts)
    return "...(earlier output trimmed)\n" + "\n".join(parts[-lines:])


def block(message):
    """Exit code 2: blocks where the event allows it; stderr goes to Claude."""
    sys.stderr.write(message.rstrip() + "\n")
    sys.exit(2)
