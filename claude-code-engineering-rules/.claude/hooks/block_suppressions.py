"""PreToolUse (Edit|Write|MultiEdit): block edits that ADD suppression markers.

The marker count in the new text is compared with the text it replaces, so
editing near an existing suppression is fine; adding a new one is not.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _guardrails as g  # noqa: E402

DEFAULT_REGEX = "|".join([
    r"eslint-disable", r"@ts-ignore", r"@ts-expect-error", r"@ts-nocheck",
    r"\bas\s+any\b", r"\bas\s+unknown\s+as\b",
    r"#\s*noqa", r"#\s*type:\s*ignore", r"#\s*pyright:\s*ignore", r"#\s*pylint:\s*disable",
    r"//\s*nolint", r"#\[allow\(", r"@SuppressWarnings", r"#\[ignore\]",
    r"\b(?:it|test|describe)\.skip\(", r"\bx(?:it|describe|test)\(", r"\b(?:it|test)\.todo\(",
    r"@pytest\.mark\.(?:skip|xfail)", r"@unittest\.skip", r"\bt\.Skip\(", r"@Disabled\b",
])


def pairs(tool_name, tool_input, file_path):
    """Yield (old_text, new_text) pairs for the edit."""
    if tool_name == "Write":
        old = ""
        try:
            with open(file_path, encoding="utf-8", errors="replace") as fh:
                old = fh.read()
        except (FileNotFoundError, IsADirectoryError, TypeError):
            pass
        yield old, tool_input.get("content", "") or ""
    elif tool_name == "MultiEdit":
        for edit in tool_input.get("edits", []) or []:
            yield edit.get("old_string", "") or "", edit.get("new_string", "") or ""
    else:
        yield tool_input.get("old_string", "") or "", tool_input.get("new_string", "") or ""


def main():
    event = g.read_event()
    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path", "")
    cfg = g.load_config()
    if g.matches_any(g.rel_path(file_path), cfg.get("SUPPRESSION_EXEMPT_GLOBS", ".claude/**")):
        sys.exit(0)
    pattern = re.compile(cfg.get("SUPPRESSION_REGEX") or DEFAULT_REGEX)
    added = []
    for old, new in pairs(tool_name, tool_input, file_path):
        old_hits = pattern.findall(old)
        for hit in set(pattern.findall(new)):
            if pattern.findall(new).count(hit) > old_hits.count(hit):
                added.append(hit)
    if added:
        g.block(
            f"Blocked: this edit to {g.rel_path(file_path)} adds suppression or skip markers: "
            + ", ".join(sorted(set(added)))
            + ".\nSuppressions are a human decision. Fix the underlying problem instead."
            + " If the check itself is wrong, or the fix is out of scope, leave the code as it is"
            + " and explain under 'Not passing' in your final report."
        )
    sys.exit(0)


main()
