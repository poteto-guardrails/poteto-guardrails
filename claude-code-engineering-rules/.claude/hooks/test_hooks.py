"""Self-test for the guardrail hooks: python3 .claude/hooks/test_hooks.py

Builds a throwaway git repo, feeds each hook the JSON Claude Code would send,
and checks the exit codes. Run it after changing any hook or guardrails.env defaults.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HOOKS = os.path.dirname(os.path.abspath(__file__))
failures = []


def hook(name, event, root, *args):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=root)
    proc = subprocess.run([sys.executable, os.path.join(HOOKS, name), *args],
                          input=json.dumps(event), capture_output=True, text=True, env=env)
    return proc.returncode, proc.stdout, proc.stderr


def check(label, got, want):
    status = "ok  " if got == want else "FAIL"
    print(f"{status} {label} (exit {got}, want {want})")
    if got != want:
        failures.append(label)


def setup(env_text):
    root = tempfile.mkdtemp(prefix="guardrail-test-")
    os.makedirs(os.path.join(root, ".claude"))
    with open(os.path.join(root, ".claude", "guardrails.env"), "w") as fh:
        fh.write(env_text)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q",
                    "--allow-empty", "-m", "init"], cwd=root, check=True)
    return root


def edit(path, old, new):
    return {"tool_name": "Edit", "tool_input": {"file_path": path, "old_string": old, "new_string": new}}


# --- block_suppressions -------------------------------------------------------
root = setup("SUPPRESSION_EXEMPT_GLOBS=.claude/**,vendor/**\n")
f = os.path.join(root, "src", "a.ts")
check("adds eslint-disable -> blocked",
      hook("block_suppressions.py", edit(f, "x()", "// eslint-disable-next-line\nx()"), root)[0], 2)
check("adds @ts-ignore -> blocked",
      hook("block_suppressions.py", edit(f, "a", "// @ts-ignore\na"), root)[0], 2)
check("adds 'as any' cast -> blocked",
      hook("block_suppressions.py", edit(f, "y", "y as any"), root)[0], 2)
check("adds it.skip -> blocked",
      hook("block_suppressions.py", edit(f, "it('a'", "it.skip('a'"), root)[0], 2)
check("python noqa -> blocked",
      hook("block_suppressions.py", edit(os.path.join(root, "m.py"), "import os", "import os  # noqa"), root)[0], 2)
check("edit near an EXISTING suppression -> allowed",
      hook("block_suppressions.py",
           edit(f, "// eslint-disable-next-line\nfoo(1)", "// eslint-disable-next-line\nfoo(2)"), root)[0], 0)
check("plain edit -> allowed", hook("block_suppressions.py", edit(f, "a", "b"), root)[0], 0)
check("'many' (not 'as any') -> allowed",
      hook("block_suppressions.py", edit(f, "a", "has many items"), root)[0], 0)
check("exempt path vendor/** -> allowed",
      hook("block_suppressions.py", edit(os.path.join(root, "vendor", "x.ts"), "a", "// @ts-ignore\na"), root)[0], 0)
check("hook's own files under .claude -> allowed",
      hook("block_suppressions.py", edit(os.path.join(root, ".claude", "hooks", "x.py"), "a", "# noqa"), root)[0], 0)
existing = os.path.join(root, "w.ts")
with open(existing, "w") as fh:
    fh.write("// @ts-ignore\nold()\n")
check("Write keeping existing suppression -> allowed",
      hook("block_suppressions.py", {"tool_name": "Write", "tool_input": {
          "file_path": existing, "content": "// @ts-ignore\nnew()\n"}}, root)[0], 0)
check("Write adding a second suppression -> blocked",
      hook("block_suppressions.py", {"tool_name": "Write", "tool_input": {
          "file_path": existing, "content": "// @ts-ignore\nnew()\n// @ts-ignore\nz()\n"}}, root)[0], 2)
check("MultiEdit adding skip -> blocked",
      hook("block_suppressions.py", {"tool_name": "MultiEdit", "tool_input": {"file_path": f, "edits": [
          {"old_string": "a", "new_string": "b"}, {"old_string": "test('x'", "new_string": "test.skip('x'"}]}},
           root)[0], 2)
shutil.rmtree(root)

# --- post_edit_check ----------------------------------------------------------
root = setup("FAST_CHECK_CMD=grep -q BAD {file} && exit 1 || exit 0\nFAST_CHECK_GLOBS=*.ts\n")
good, bad, other = (os.path.join(root, n) for n in ("good.ts", "bad.ts", "bad.md"))
for path, text in ((good, "ok"), (bad, "BAD"), (other, "BAD")):
    with open(path, "w") as fh:
        fh.write(text)
check("fast check passes -> 0", hook("post_edit_check.py", edit(good, "", ""), root)[0], 0)
check("fast check fails -> 2 (fed back)", hook("post_edit_check.py", edit(bad, "", ""), root)[0], 2)
check("non-matching glob -> skipped", hook("post_edit_check.py", edit(other, "", ""), root)[0], 0)
shutil.rmtree(root)

root = setup("FAST_CHECK_CMD=\n")
check("unconfigured fast check -> 0", hook("post_edit_check.py", edit(os.path.join(root, "a.ts"), "", ""), root)[0], 0)
shutil.rmtree(root)

# --- stop_gate ----------------------------------------------------------------
root = setup("FULL_CHECK_CMD=test ! -f broken\nSTOP_GATE_MAX_RETRIES=2\n")
stop = {"hook_event_name": "Stop", "session_id": "s1", "stop_hook_active": False}
check("nothing failing yet -> 0", hook("stop_gate.py", stop, root)[0], 0)
open(os.path.join(root, "broken"), "w").close()
check("failing check, retry 1 -> blocked", hook("stop_gate.py", stop, root)[0], 2)
check("failing check, retry 2 -> blocked", hook("stop_gate.py", stop, root)[0], 2)
code, out, _ = hook("stop_gate.py", stop, root)
check("failing check, retries used -> lets stop", code, 0)
check("...and warns the user via systemMessage", "NOT verified" in out, True)
hook("stop_gate.py", {"hook_event_name": "UserPromptSubmit", "session_id": "s1"}, root, "--reset")
check("new prompt resets retries -> blocked again", hook("stop_gate.py", stop, root)[0], 2)
os.remove(os.path.join(root, "broken"))
with open(os.path.join(root, "fixed.txt"), "w") as fh:
    fh.write("x")
check("check passes -> 0", hook("stop_gate.py", stop, root)[0], 0)
check("unchanged since last pass -> skipped", hook("stop_gate.py", stop, root)[0], 0)
shutil.rmtree(root)

root = setup("FULL_CHECK_CMD=\n")
open(os.path.join(root, "x"), "w").close()
check("unconfigured stop gate -> 0", hook("stop_gate.py", stop, root)[0], 0)
code, out, _ = hook("session_start.py", {}, root)
check("session start reports NOT CONFIGURED", "NOT CONFIGURED" in out, True)
shutil.rmtree(root)

print("\nALL PASSED" if not failures else f"\n{len(failures)} FAILED: {failures}")
sys.exit(1 if failures else 0)
