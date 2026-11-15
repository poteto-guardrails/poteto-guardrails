"""PreToolUse guard (Edit|Write|MultiEdit|NotebookEdit): block edits that ADD suppression,
skip or focus markers.

FAILS CLOSED. It exits 0 only after it has inspected a well-formed edit of a supported
tool. Malformed input, unknown tools, a bad custom regex or any internal error all exit 2
(block). settings.json also sets onFailure: "block", so crashes, timeouts and a missing
interpreter block too (Claude Code 2.1.295+).

Markers are counted in the new text and in the text it replaces, so editing next to an
existing suppression is fine; adding a new one is not.
"""
import collections
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _guardrails as g  # noqa: E402

DEFAULT_PATTERNS = [
    # lint / type suppressions
    r"eslint-disable", r"@ts-ignore", r"@ts-expect-error", r"@ts-nocheck", r"biome-ignore",
    r"\bas\s+any\b", r"\bas\s+unknown\s+as\b",
    r"#\s*noqa", r"#\s*type:\s*ignore", r"#\s*pyright:\s*ignore", r"#\s*pylint:\s*disable",
    r"//\s*nolint", r"#\[allow\(", r"@SuppressWarnings",
    # skipped tests
    r"\b(?:it|test|describe|context|suite)\.skip\b", r"(?<![.\w])x(?:it|describe|test|context)\s*\(",
    r"\b(?:it|test)\.todo\s*\(", r"@pytest\.mark\.(?:skip|skipif|xfail)\b", r"@unittest\.skip",
    r"\bpytest\.skip\s*\(", r"\bt\.Skip(?:Now|f)?\s*\(", r"@Disabled\b", r"#\[ignore\]",
    # focused tests: silently shrink the suite to a subset
    r"\b(?:it|test|describe|context|suite)\.only\b", r"(?<![.\w])f(?:it|describe|context)\s*\(",
]
DEFAULT_REGEX = "|".join(DEFAULT_PATTERNS)
SUPPORTED = ("Edit", "Write", "MultiEdit", "NotebookEdit")


def require_str(obj, key, label, allow_empty=True):
    value = obj.get(key)
    if not isinstance(value, str) or (not allow_empty and not value):
        raise g.GuardError(f"{label}: '{key}' is missing or not a string")
    return value


def notebook_cell_source(path, cell_id):
    """Current source of a notebook cell, or '' if it can't be found (strictest comparison)."""
    try:
        with open(path, encoding="utf-8") as fh:
            nb = json.load(fh)
        for cell in nb.get("cells", []):
            if cell.get("id") == cell_id:
                src = cell.get("source", "")
                return "".join(src) if isinstance(src, list) else str(src)
    except (OSError, ValueError, AttributeError):
        pass
    return ""


def edit_pairs(tool_name, ti):
    """Validate the tool input and return (path, [(old_text, new_text), ...])."""
    if tool_name == "Edit":
        path = require_str(ti, "file_path", "Edit", allow_empty=False)
        return path, [(require_str(ti, "old_string", "Edit"), require_str(ti, "new_string", "Edit"))]
    if tool_name == "Write":
        path = require_str(ti, "file_path", "Write", allow_empty=False)
        new = require_str(ti, "content", "Write")
        old = ""
        if os.path.isfile(path):
            with open(path, encoding="utf-8", errors="replace") as fh:
                old = fh.read()
        return path, [(old, new)]
    if tool_name == "MultiEdit":
        path = require_str(ti, "file_path", "MultiEdit", allow_empty=False)
        edits = ti.get("edits")
        if not isinstance(edits, list) or not edits:
            raise g.GuardError("MultiEdit: 'edits' is missing or empty")
        pairs = []
        for i, e in enumerate(edits):
            if not isinstance(e, dict):
                raise g.GuardError(f"MultiEdit: edit {i} is not an object")
            pairs.append((require_str(e, "old_string", f"MultiEdit edit {i}"),
                          require_str(e, "new_string", f"MultiEdit edit {i}")))
        return path, pairs
    if tool_name == "NotebookEdit":
        path = require_str(ti, "notebook_path", "NotebookEdit", allow_empty=False)
        mode = ti.get("edit_mode") or "replace"
        if mode not in ("replace", "insert", "delete"):
            raise g.GuardError(f"NotebookEdit: unknown edit_mode {mode!r}")
        if mode == "delete":
            return path, []
        new = require_str(ti, "new_source", "NotebookEdit")
        old = notebook_cell_source(path, ti.get("cell_id")) if mode == "replace" else ""
        return path, [(old, new)]
    raise g.GuardError(f"tool {tool_name!r} is not one this guard understands ({', '.join(SUPPORTED)})")


def added_markers(pattern, pairs):
    added = set()
    for old, new in pairs:
        old_counts = collections.Counter(m.group(0) for m in pattern.finditer(old))
        new_counts = collections.Counter(m.group(0) for m in pattern.finditer(new))
        added.update(hit for hit, n in new_counts.items() if n > old_counts[hit])
    return sorted(added)


def main():
    event = g.read_event_strict()
    hook_event = event.get("hook_event_name")
    if hook_event is not None and hook_event != "PreToolUse":
        raise g.GuardError(f"registered on the wrong event ({hook_event!r}); expected PreToolUse")
    tool_name = event.get("tool_name")
    tool_input = event.get("tool_input")
    if not isinstance(tool_name, str) or not isinstance(tool_input, dict):
        raise g.GuardError("event has no tool_name/tool_input")

    path, pairs = edit_pairs(tool_name, tool_input)
    cfg = g.load_config()
    if g.matches_any(g.rel_path(path), cfg.get("SUPPRESSION_EXEMPT_GLOBS", ".claude/**")):
        sys.exit(0)
    try:
        pattern = re.compile(cfg.get("SUPPRESSION_REGEX") or DEFAULT_REGEX)
    except re.error as exc:
        raise g.GuardError(f"SUPPRESSION_REGEX in guardrails.env is invalid: {exc}")

    added = added_markers(pattern, pairs)
    if added:
        g.block(
            f"Blocked: this edit to {g.rel_path(path)} adds suppression, skip or focus markers: "
            + ", ".join(added)
            + ".\nSuppressions and skipped or focused tests are a human decision. Fix the underlying"
            " problem instead. If the check is wrong, or the fix is out of scope, leave the code"
            " as it is and explain under 'Not passing' in your final report."
        )
    sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except g.GuardError as exc:
        g.block(f"Suppression guard could not verify this edit, so it is blocked (fail closed): {exc}."
                " If this keeps happening, tell the user; the guard may need updating for this"
                " Claude Code version.")
    except Exception as exc:  # any bug in the guard must block, not pass
        g.block(f"Suppression guard crashed, so the edit is blocked (fail closed): "
                f"{type(exc).__name__}: {exc}. Tell the user.")
