"""Shared library for the guardrail hooks and tools. Python 3.8+, standard library only.

State lives in <git-dir>/claude-guardrails/ (never committed, separate per worktree):
  sessions/<session_id>.json   per-session: baseline fingerprint, stop-gate retries
  records/<key>.json           full-check results, keyed by (working-tree fingerprint, command)
"""
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time

PACK_VERSION = "4.1.1"


class GuardError(Exception):
    """Raised for malformed input or anything a guard can't safely interpret."""


# --- paths & config -------------------------------------------------------------

def project_dir():
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def load_config():
    """Read .claude/guardrails.env as plain KEY=VALUE lines (never shell-sourced)."""
    cfg = {}
    path = os.path.join(project_dir(), ".claude", "guardrails.env")
    if not os.path.exists(path):
        return cfg
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            cfg[key.strip()] = value.strip()
    return cfg


def int_setting(cfg, key, default):
    try:
        return int(cfg.get(key) or default)
    except ValueError:
        return default


def rel_path(path):
    if not path:
        return ""
    path = str(path).replace("\\", "/")
    root = project_dir().replace("\\", "/")
    try:
        rel = os.path.relpath(os.path.abspath(path), os.path.abspath(root))
    except ValueError:  # different drive on Windows
        return path
    return rel.replace("\\", "/")


def matches_any(rel, globs_csv):
    rel = (rel or "").replace("\\", "/")
    name = rel.rsplit("/", 1)[-1]
    for g in (x.strip() for x in (globs_csv or "").split(",")):
        if not g:
            continue
        if fnmatch.fnmatch(rel, g) or fnmatch.fnmatch(name, g):
            return True
        if g.endswith("/**") and (rel == g[:-3] or rel.startswith(g[:-2])):
            return True
    return False


# --- events -----------------------------------------------------------------------

def read_event_strict():
    """Parse the hook event; raise GuardError instead of guessing."""
    raw = sys.stdin.read()
    try:
        event = json.loads(raw)
    except ValueError as exc:
        raise GuardError(f"hook input is not valid JSON ({exc})")
    if not isinstance(event, dict):
        raise GuardError("hook input is not a JSON object")
    return event


def read_event_lenient():
    """For hooks that must never stop the session from ending (Stop, SessionStart)."""
    try:
        event = json.loads(sys.stdin.read() or "{}")
        return event if isinstance(event, dict) else {}
    except ValueError:
        return {}


def safe_id(value):
    value = str(value or "unknown")
    return re.sub(r"[^A-Za-z0-9_.-]", "_", value)[:100] or "unknown"


# --- running commands ---------------------------------------------------------------

def run(cmd, timeout):
    """Run a human-authored command from the repo root. Returns (exit_code, output, seconds)."""
    start = time.time()
    try:
        proc = subprocess.run(cmd, shell=True, cwd=project_dir(), capture_output=True,
                              text=True, timeout=timeout)
        out = (proc.stdout or "") + (proc.stderr or "")
        return proc.returncode, out, round(time.time() - start, 1)
    except subprocess.TimeoutExpired:
        return 124, f"TIMED OUT after {timeout}s: {cmd}", round(time.time() - start, 1)


def tail(text, lines=60):
    parts = text.rstrip().splitlines()
    if len(parts) <= lines:
        return "\n".join(parts)
    return "...(earlier output trimmed)\n" + "\n".join(parts[-lines:])


def block(message):
    """Exit 2: blocks where the event allows it; stderr is shown to Claude."""
    sys.stderr.write(message.rstrip() + "\n")
    sys.exit(2)


# --- git fingerprint -----------------------------------------------------------------

def _git(*args, binary=False):
    proc = subprocess.run(["git", *args], cwd=project_dir(), capture_output=True, timeout=120)
    if proc.returncode != 0:
        return None
    return proc.stdout if binary else proc.stdout.decode("utf-8", "replace")


def git_dir():
    try:
        out = _git("rev-parse", "--absolute-git-dir")
    except (OSError, subprocess.TimeoutExpired):
        return None
    return out.strip() if out else None


def _pathspec():
    """Paths left out of the fingerprint: evidence folders etc. (FINGERPRINT_EXCLUDE, comma-separated)."""
    excludes = load_config().get("FINGERPRINT_EXCLUDE", ".claude/verification-runs")
    return ["--", "."] + [f":(exclude){p.strip()}" for p in excludes.split(",") if p.strip()]


def fingerprint():
    """Content hash of what a check would see: HEAD's tree + staged + unstaged + untracked files.

    Covers committed-in-session work too, because HEAD's tree is part of the hash.
    Returns None outside a git repository.
    """
    try:
        if git_dir() is None:
            return None
        spec = _pathspec()
        h = hashlib.sha256()
        tree = _git("rev-parse", "--verify", "-q", "HEAD^{tree}")
        h.update(b"tree:" + (tree or "no-commits").strip().encode())
        h.update(b"\0staged:" + (_git("diff", "--cached", "--binary", "--no-color", *spec, binary=True) or b""))
        h.update(b"\0unstaged:" + (_git("diff", "--binary", "--no-color", *spec, binary=True) or b""))
        untracked = _git("ls-files", "--others", "--exclude-standard", "-z", *spec, binary=True) or b""
        for name in sorted(p for p in untracked.split(b"\0") if p):
            h.update(b"\0untracked:" + name + b"\0")
            path = os.path.join(project_dir(), name.decode("utf-8", "replace"))
            try:
                with open(path, "rb") as fh:
                    for chunk in iter(lambda: fh.read(1 << 20), b""):
                        h.update(chunk)
            except OSError:
                h.update(b"<unreadable>")
        return h.hexdigest()
    except (OSError, subprocess.TimeoutExpired):
        return None


# --- state -----------------------------------------------------------------------------

def state_root():
    gd = git_dir()
    if gd:
        root = os.path.join(gd, "claude-guardrails")
    else:
        key = hashlib.sha256(project_dir().encode()).hexdigest()[:16]
        root = os.path.join(tempfile.gettempdir(), "claude-guardrails", key)
    os.makedirs(os.path.join(root, "sessions"), exist_ok=True)
    os.makedirs(os.path.join(root, "records"), exist_ok=True)
    return root


def _read_json(path):
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
            return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _write_json(path, data):
    """Atomic write so concurrent sessions never see a half-written file."""
    folder = os.path.dirname(path)
    fd, tmp = tempfile.mkstemp(dir=folder, prefix=".tmp-")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=1)
    os.replace(tmp, path)


def session_path(session_id):
    return os.path.join(state_root(), "sessions", safe_id(session_id) + ".json")


def load_session(session_id):
    return _read_json(session_path(session_id))


def save_session(session_id, data):
    _write_json(session_path(session_id), data)


def _record_path(fp, command):
    key = hashlib.sha256(f"{fp}\0{command}".encode()).hexdigest()[:32]
    return os.path.join(state_root(), "records", key + ".json")


def write_record(fp, command, exit_code, seconds, runner, session, output=""):
    """Store provenance and bounded output for a check on an unchanged tree."""
    if fp is None:
        return None
    record = {
        "pack_version": PACK_VERSION,
        "fingerprint": fp,
        "command": command,
        "exit_code": exit_code,
        "passed": exit_code == 0,
        "ran_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "duration_s": seconds,
        "runner": runner,
        "session": session or "unknown",
        "output_tail": tail(output, 80),
    }
    _write_json(_record_path(fp, command), record)
    return record


def find_record(fp, command):
    if fp is None:
        return None
    rec = _read_json(_record_path(fp, command))
    return rec or None


def record_is_current(rec, fp, command):
    """A current result (pass or fail) for exactly this command and working tree."""
    return bool(rec) and rec.get("pack_version") == PACK_VERSION \
        and rec.get("fingerprint") == fp and rec.get("command") == command


def record_is_valid(rec, fp, command):
    """A current passing result for exactly this command and working tree."""
    return record_is_current(rec, fp, command) and rec.get("passed") is True
