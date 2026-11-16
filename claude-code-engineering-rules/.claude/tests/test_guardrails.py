"""Self-test for the guardrail hooks and tools.

  python3 .claude/tests/test_guardrails.py        (from the repository root)

Each test builds a throwaway git repo, feeds hooks the JSON Claude Code would send (or runs
the tools the way Claude would), and checks exit codes, output and recorded state.
This proves the scripts behave as designed. It does NOT prove Claude Code registers and calls
them as intended: that's what smoke-test/SMOKE-TEST.md is for.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

PACK = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
HOOKS = os.path.join(PACK, "hooks")
TOOLS = os.path.join(PACK, "tools")
STUB = os.path.abspath(os.path.join(PACK, "..", "examples", "driver_stub.py"))
PY = sys.executable


class Repo:
    def __init__(self, env_text=""):
        self.root = tempfile.mkdtemp(prefix="guardrail test ")  # space in path on purpose
        os.makedirs(os.path.join(self.root, ".claude"))
        self.git("init", "-q")
        self.set_env(env_text)
        self.write("README", "x\n")
        self.git("add", "-A")
        self.commit("init")

    def set_env(self, text):
        with open(os.path.join(self.root, ".claude", "guardrails.env"), "w") as fh:
            fh.write(text)
        # keep config out of the fingerprint so tests control exactly what "changed" means
        exclude = os.path.join(self.root, ".git", "info", "exclude")
        os.makedirs(os.path.dirname(exclude), exist_ok=True)
        with open(exclude, "a") as fh:
            fh.write(".claude/\n")

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True)

    def commit(self, msg):
        self.git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", msg)

    def path(self, *parts):
        return os.path.join(self.root, *parts)

    def write(self, name, text):
        p = self.path(name)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as fh:
            fh.write(text)
        return p

    def hook(self, name, event, raw=None):
        env = dict(os.environ, CLAUDE_PROJECT_DIR=self.root)
        data = raw if raw is not None else json.dumps(event)
        p = subprocess.run([PY, os.path.join(HOOKS, name)], input=data, capture_output=True,
                           text=True, env=env, cwd=self.root)
        return p.returncode, p.stdout, p.stderr

    def tool(self, name, *args):
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}  # cwd fallback
        p = subprocess.run([PY, os.path.join(TOOLS, name), *args], capture_output=True,
                           text=True, env=env, cwd=self.root)
        return p.returncode, p.stdout + p.stderr

    def cleanup(self):
        shutil.rmtree(self.root, ignore_errors=True)


def edit(path, old, new, **extra):
    return {"hook_event_name": "PreToolUse", "tool_name": "Edit",
            "tool_input": {"file_path": path, "old_string": old, "new_string": new, **extra}}


class SuppressionGuard(unittest.TestCase):
    def setUp(self):
        self.r = Repo("SUPPRESSION_EXEMPT_GLOBS=.claude/**,vendor/**\n")
        self.f = self.r.path("src", "a file.ts")

    def tearDown(self):
        self.r.cleanup()

    def code(self, event=None, raw=None):
        return self.r.hook("block_suppressions.py", event, raw)[0]

    def test_blocks_added_markers(self):
        cases = ["// eslint-disable-next-line\nx()", "// @ts-ignore\na", "y as any", "it.skip('a', f)",
                 "xit('a', f)", "it.only('a', f)", "test.only('a', f)", "describe.only('s', f)",
                 "test.describe.only('s', f)", "fit('a', f)", "fdescribe('s', f)", "@pytest.mark.skip\ndef t(): 1",
                 "import os  # noqa", "x = 1  # type: ignore", "t.Skip(\"later\")", "// biome-ignore lint: x"]
        for new in cases:
            with self.subTest(new=new):
                self.assertEqual(self.code(edit(self.f, "a", new)), 2)

    def test_allows_legitimate_code(self):
        cases = ["b", "has many items", "model.fit(X, y)", "profit(1)", "results.only_valid()",
                 "describe('s', () => it('a', f))", "skipped = 0", "const xitem = 1"]
        for new in cases:
            with self.subTest(new=new):
                self.assertEqual(self.code(edit(self.f, "a", new)), 0)

    def test_editing_next_to_existing_suppression_is_allowed(self):
        self.assertEqual(self.code(edit(self.f, "// @ts-ignore\nfoo(1)", "// @ts-ignore\nfoo(2)")), 0)

    def test_exempt_paths(self):
        self.assertEqual(self.code(edit(self.r.path("vendor", "x.ts"), "a", "// @ts-ignore")), 0)
        self.assertEqual(self.code(edit(self.r.path(".claude", "hooks", "x.py"), "a", "# noqa")), 0)
        win = self.r.root.replace("/", "\\") + "\\vendor\\y.ts"
        self.assertEqual(self.code(edit(win, "a", "// @ts-ignore")), 0, "backslash paths are normalised")

    def test_write_compares_with_file_on_disk(self):
        p = self.r.write("w.ts", "// @ts-ignore\nold()\n")
        w = lambda c: {"hook_event_name": "PreToolUse", "tool_name": "Write",
                       "tool_input": {"file_path": p, "content": c}}
        self.assertEqual(self.code(w("// @ts-ignore\nnew()\n")), 0)
        self.assertEqual(self.code(w("// @ts-ignore\nnew()\n// @ts-ignore\nz()\n")), 2)
        new_file = {"hook_event_name": "PreToolUse", "tool_name": "Write",
                    "tool_input": {"file_path": self.r.path("n.ts"), "content": "it.only('a')"}}
        self.assertEqual(self.code(new_file), 2)

    def test_multiedit(self):
        ev = {"hook_event_name": "PreToolUse", "tool_name": "MultiEdit", "tool_input": {
            "file_path": self.f, "edits": [{"old_string": "a", "new_string": "b"},
                                           {"old_string": "test('x'", "new_string": "test.skip('x'"}]}}
        self.assertEqual(self.code(ev), 2)
        ev["tool_input"]["edits"] = [{"old_string": "a", "new_string": "b"}]
        self.assertEqual(self.code(ev), 0)

    def test_notebook_edit(self):
        nb = self.r.write("n.ipynb", json.dumps({"cells": [
            {"id": "c1", "cell_type": "code", "source": ["import os  # noqa\n"]}]}))
        ev = lambda **ti: {"hook_event_name": "PreToolUse", "tool_name": "NotebookEdit",
                           "tool_input": {"notebook_path": nb, **ti}}
        self.assertEqual(self.code(ev(cell_id="c1", new_source="import os  # noqa\nimport re\n")), 0)
        self.assertEqual(self.code(ev(cell_id="c1", new_source="import os  # noqa\nx=1  # noqa\n")), 2)
        self.assertEqual(self.code(ev(edit_mode="insert", new_source="pytest.skip('x')")), 2)
        self.assertEqual(self.code(ev(cell_id="c1", edit_mode="delete")), 0)

    def test_custom_regex_with_capture_groups_counts_whole_matches(self):
        self.r.set_env("SUPPRESSION_REGEX=(TODO)-(HACK)\n")
        self.assertEqual(self.code(edit(self.f, "a", "TODO-HACK")), 2)
        self.assertEqual(self.code(edit(self.f, "TODO-HACK x", "TODO-HACK y")), 0)
        self.assertEqual(self.code(edit(self.f, "a", "// @ts-ignore")), 0, "custom regex replaces defaults")

    def test_fails_closed(self):
        cases = {
            "malformed JSON": dict(raw="{not json"),
            "empty input": dict(raw=""),
            "JSON array": dict(raw="[]"),
            "no tool_input": dict(event={"hook_event_name": "PreToolUse", "tool_name": "Edit"}),
            "missing new_string": dict(event={"hook_event_name": "PreToolUse", "tool_name": "Edit",
                                              "tool_input": {"file_path": self.f, "old_string": "a"}}),
            "empty file_path": dict(event=edit("", "a", "b")),
            "unknown tool": dict(event={"hook_event_name": "PreToolUse", "tool_name": "Frobnicate",
                                        "tool_input": {"file_path": self.f}}),
            "wrong event": dict(event={**edit(self.f, "a", "b"), "hook_event_name": "PostToolUse"}),
            "empty MultiEdit": dict(event={"hook_event_name": "PreToolUse", "tool_name": "MultiEdit",
                                           "tool_input": {"file_path": self.f, "edits": []}}),
            "bad notebook mode": dict(event={"hook_event_name": "PreToolUse", "tool_name": "NotebookEdit",
                                             "tool_input": {"notebook_path": self.f, "edit_mode": "x",
                                                            "new_source": ""}}),
        }
        for label, kw in cases.items():
            with self.subTest(label):
                self.assertEqual(self.code(**kw), 2)

    def test_malformed_json_reports_why(self):
        code, _, err = self.r.hook("block_suppressions.py", None, raw="{not json")
        self.assertEqual(code, 2)
        self.assertIn("not valid JSON", err)

    def test_invalid_custom_regex_blocks(self):
        self.r.set_env("SUPPRESSION_REGEX=([unclosed\n")
        code, _, err = self.r.hook("block_suppressions.py", edit(self.f, "a", "b"))
        self.assertEqual(code, 2)
        self.assertIn("SUPPRESSION_REGEX", err)

    def test_internal_crash_blocks(self):
        os.remove(self.r.path(".claude", "guardrails.env"))
        os.makedirs(self.r.path(".claude", "guardrails.env"))  # reading it now raises
        code, _, err = self.r.hook("block_suppressions.py", edit(self.f, "a", "b"))
        self.assertEqual(code, 2)
        self.assertIn("fail closed", err)


class PostEditCheck(unittest.TestCase):
    def setUp(self):
        self.r = Repo("FAST_CHECK_CMD=grep -q BAD {file} && exit 1 || exit 0\nFAST_CHECK_GLOBS=*.ts,*.ipynb\n")

    def tearDown(self):
        self.r.cleanup()

    def run_on(self, path, key="file_path"):
        return self.r.hook("post_edit_check.py", {"tool_input": {key: path}})[0]

    def test_pass_fail_and_spaces_in_names(self):
        self.assertEqual(self.run_on(self.r.write("good file.ts", "ok")), 0)
        self.assertEqual(self.run_on(self.r.write("bad file.ts", "BAD")), 2)

    def test_glob_filter_deleted_file_and_notebooks(self):
        self.assertEqual(self.run_on(self.r.write("bad.md", "BAD")), 0)
        self.assertEqual(self.run_on(self.r.path("gone.ts")), 0)
        self.assertEqual(self.run_on(self.r.write("nb.ipynb", "BAD"), key="notebook_path"), 2)

    def test_unconfigured(self):
        self.r.set_env("")
        self.assertEqual(self.run_on(self.r.write("bad.ts", "BAD")), 0)


class StopGateAndCheck(unittest.TestCase):
    def setUp(self):
        self.ran = tempfile.mktemp(prefix="ran-")  # outside the repo, so counting runs doesn't change the tree
        self.r = Repo(f"FULL_CHECK_CMD=echo run >> '{self.ran}'; test ! -e broken\nSTOP_GATE_MAX_RETRIES=2\n"
                      "FULL_CHECK_TIMEOUT=20\n")

    def tearDown(self):
        self.r.cleanup()
        if os.path.exists(self.ran):
            os.remove(self.ran)

    def runs(self):
        if not os.path.exists(self.ran):
            return 0
        with open(self.ran) as fh:
            return fh.read().count("run")

    def start(self, sid="A"):
        return self.r.hook("session_start.py", {"session_id": sid, "source": "startup"})

    def stop(self, sid="A", active=False):
        return self.r.hook("stop_gate.py", {"hook_event_name": "Stop", "session_id": sid,
                                            "stop_hook_active": active})

    def test_unchanged_tree_skips_without_running(self):
        self.r.write("preexisting-uncommitted.txt", "from before the session")
        self.start()
        self.assertEqual(self.stop()[0], 0)
        self.assertEqual(self.runs(), 0)

    def test_compaction_preserves_original_baseline(self):
        self.start("compact-session")
        self.r.write("broken", "")
        # SessionStart fires again after context compaction; this must not bless the edit.
        self.r.hook("session_start.py", {"session_id": "compact-session", "source": "compact"})
        code, _, err = self.stop("compact-session")
        self.assertEqual(code, 2)
        self.assertIn("full check failed", err)
        self.assertEqual(self.runs(), 1)

    def test_retry_chain_then_warn_then_new_chain(self):
        self.start()
        self.r.write("broken", "")
        self.assertEqual(self.stop()[0], 2)
        self.assertEqual(self.stop(active=True)[0], 2)
        code, out, _ = self.stop(active=True)
        self.assertEqual(code, 0)
        self.assertIn("NOT verified", out)
        self.assertEqual(self.stop(active=False)[0], 2, "a new stop chain gets fresh retries")

    def test_sessions_do_not_share_retries(self):
        self.start("A")
        self.start("B")
        self.r.write("broken", "")
        self.assertEqual(self.stop("A")[0], 2)
        self.assertEqual(self.stop("A", True)[0], 2)          # A: attempt 2
        self.assertIn("attempt 1", self.stop("B")[2])         # B unaffected by A
        code, out, _ = self.stop("A", True)                   # A: retries used up
        self.assertEqual(code, 0)
        self.assertIn("NOT verified", out)
        self.assertIn("attempt 2", self.stop("B", True)[2])   # B unaffected by A's warning

    def test_failed_check_record_is_reused_until_tree_changes(self):
        self.start()
        self.r.write("broken", "")
        self.assertEqual(self.stop()[0], 2)
        self.assertEqual(self.runs(), 1)
        # Same tree: reuse the original failure and diagnostics, don't rerun.
        code, _, err = self.stop(active=True)
        self.assertEqual(code, 2)
        self.assertIn("full check failed", err)
        self.assertEqual(self.runs(), 1)
        # A changed tree invalidates the failed record and triggers a fresh check.
        os.remove(self.r.path("broken"))
        self.r.write("fixed.txt", "the tree has changed")
        self.assertEqual(self.stop(active=True)[0], 0)
        self.assertEqual(self.runs(), 2)

    def test_replayed_failure_is_labelled_and_check_py_refreshes_it(self):
        # A fix outside version control (e.g. npm install into ignored node_modules/)
        # leaves the fingerprint unchanged. The replay must say so and point at check.py.
        self.r.set_env("FULL_CHECK_CMD=test -f node_modules/dep\nSTOP_GATE_MAX_RETRIES=2\n")
        with open(self.r.path(".gitignore"), "w") as fh:
            fh.write("node_modules/\n")
        self.r.git("add", ".gitignore")
        self.r.commit("ignore deps")
        self.start()
        self.r.write("feature.txt", "v1")
        code, _, err = self.stop()
        self.assertEqual(code, 2)
        self.assertNotIn("SAVED result", err, "a fresh run isn't labelled as saved")
        self.r.write("node_modules/dep", "")              # the environment fix
        code, _, err = self.stop(active=True)
        self.assertEqual(code, 2)
        self.assertIn("SAVED result", err)
        self.assertIn("python3 .claude/tools/check.py", err)
        self.assertEqual(self.r.tool("check.py")[0], 0)   # fresh run replaces the saved failure
        self.assertEqual(self.stop(active=True)[0], 0)

    def test_timeouts_are_never_replayed(self):
        flag = tempfile.mktemp()
        self.r.set_env(f"FULL_CHECK_CMD=echo run >> '{self.ran}'; if [ -f '{flag}' ]; then sleep 5; fi; true\n"
                       "FULL_CHECK_TIMEOUT=1\n")
        self.start()
        self.r.write("feature.txt", "v1")
        open(flag, "w").close()
        self.assertEqual(self.stop()[0], 2)               # one slow moment
        os.remove(flag)
        self.assertEqual(self.stop(active=True)[0], 0, "same tree, but the timeout is re-run, not replayed")
        self.assertEqual(self.runs(), 2)

    def test_records_from_another_pack_version_are_ignored(self):
        self.start()
        self.r.write("feature.txt", "v1")
        self.assertEqual(self.r.tool("check.py")[0], 0)
        self.assertEqual(self.r.tool("check.py", "--status")[0], 0)
        records = self.r.path(".git", "claude-guardrails", "records")
        for name in os.listdir(records):
            path = os.path.join(records, name)
            with open(path) as fh:
                rec = json.load(fh)
            rec["pack_version"] = "0.0.0"
            with open(path, "w") as fh:
                json.dump(rec, fh)
        self.assertEqual(self.r.tool("check.py", "--status")[0], 5)
        self.assertEqual(self.stop()[0], 0)
        self.assertEqual(self.runs(), 2, "the old-version record was ignored and the check re-ran")

    def test_check_py_record_is_reused_then_invalidated(self):
        self.start()
        self.r.write("feature.txt", "v1")
        code, out = self.r.tool("check.py")
        self.assertEqual(code, 0)
        self.assertIn("FULL CHECK: PASS", out)
        self.assertEqual(self.r.tool("check.py", "--status")[0], 0)
        self.assertEqual(self.stop()[0], 0)
        self.assertEqual(self.runs(), 1, "stop gate reused check.py's record")
        self.r.write("feature.txt", "v2")
        self.assertEqual(self.r.tool("check.py", "--status")[0], 5)
        self.assertEqual(self.stop()[0], 0)
        self.assertEqual(self.runs(), 2, "tree changed, so the gate ran the check again")

    def test_only_generated_artifacts_are_excluded(self):
        self.start()
        self.r.write("feature.txt", "v1")
        self.assertEqual(self.r.tool("check.py")[0], 0)
        self.r.write(".claude/verification-runs/t1/shot.txt", "generated evidence")
        self.assertEqual(self.r.tool("check.py", "--status")[0], 0)
        self.r.write("verification/real-test-helper.py", "print('project-owned')")
        self.assertEqual(self.r.tool("check.py", "--status")[0], 5)

    def test_record_bound_to_command(self):
        self.start()
        self.r.write("feature.txt", "v1")
        self.r.tool("check.py")
        self.r.set_env(f"FULL_CHECK_CMD=echo run >> '{self.ran}'; true\n")
        self.assertEqual(self.r.tool("check.py", "--status")[0], 5, "a different command needs a new run")

    def test_committing_broken_code_is_still_caught(self):
        self.start()
        self.r.write("broken", "")
        self.r.git("add", "-A")
        self.r.commit("agent commit")  # tree is clean, but HEAD moved
        self.assertEqual(self.stop()[0], 2)

    def test_fingerprint_sees_staged_unstaged_deleted_renamed_untracked(self):
        self.r.write("a.txt", "1")
        self.r.git("add", "-A")
        self.r.commit("base")
        self.start()
        steps = [
            ("staged", lambda: (self.r.write("a.txt", "2"), self.r.git("add", "a.txt"))),
            ("unstaged on top", lambda: self.r.write("a.txt", "3")),
            ("renamed", lambda: self.r.git("mv", "a.txt", "b.txt")),
            ("deleted", lambda: os.remove(self.r.path("README"))),
            ("untracked dir", lambda: self.r.write("newdir/deep/c.txt", "x")),
            ("untracked content", lambda: self.r.write("newdir/deep/c.txt", "y")),
        ]
        for label, change in steps:
            with self.subTest(label):
                self.assertEqual(self.r.tool("check.py")[0], 0)
                change()
                self.assertEqual(self.r.tool("check.py", "--status")[0], 5, f"{label} must invalidate")

    def test_check_that_modifies_tree_is_not_recorded(self):
        self.r.set_env("FULL_CHECK_CMD=echo formatted >> fmt.txt\n")
        code, out = self.r.tool("check.py")
        self.assertEqual(code, 4)
        self.assertIn("NOT recorded", out)

    def test_timeouts(self):
        self.r.set_env("FULL_CHECK_CMD=sleep 5\nFULL_CHECK_TIMEOUT=1\n")
        self.start()
        self.r.write("x.txt", "1")
        code, out = self.r.tool("check.py")
        self.assertEqual(code, 124)
        self.assertIn("TIMEOUT", out)
        code, _, err = self.stop()
        self.assertEqual(code, 2)
        self.assertIn("TIMED OUT", err)

    def test_unconfigured(self):
        self.r.set_env("")
        self.start()
        self.assertEqual(self.stop()[0:2], (0, ""), "nothing changed: silent")
        self.r.write("x.txt", "1")
        code, out, _ = self.stop()
        self.assertEqual(code, 0)
        self.assertIn("unverified", out)
        self.assertEqual(self.r.tool("check.py")[0], 3)

    def test_stop_gate_crash_never_traps_session(self):
        os.remove(self.r.path(".claude", "guardrails.env"))
        os.makedirs(self.r.path(".claude", "guardrails.env"))
        code, out, _ = self.stop()
        self.assertEqual(code, 0)
        self.assertIn("crashed", out)

    def test_outside_git_still_checks_but_does_not_record(self):
        plain = tempfile.mkdtemp()
        os.makedirs(os.path.join(plain, ".claude"))
        with open(os.path.join(plain, ".claude", "guardrails.env"), "w") as fh:
            fh.write("FULL_CHECK_CMD=true\n")
        p = subprocess.run([PY, os.path.join(TOOLS, "check.py")], cwd=plain, capture_output=True, text=True,
                           env={k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"})
        shutil.rmtree(plain)
        self.assertEqual(p.returncode, 0)
        self.assertIn("Not recorded: not a git repository", p.stdout)

    def test_session_start_reports_config(self):
        _, out, _ = self.start()
        self.assertIn("check.py", out)
        self.assertIn("NOT CONFIGURED: FAST_CHECK_CMD, DRIVER_CMD", out)


class VerifyDriver(unittest.TestCase):
    def setUp(self):
        self.r = Repo(f"DRIVER_CMD={PY} '{STUB}'\nDRIVER_TIMEOUT=20\n")
        os.makedirs(self.r.path("docs"))
        shutil.copy(os.path.join(PACK, "..", "docs", "feature-map.md"), self.r.path("docs", "feature-map.md"))

    def tearDown(self):
        self.r.cleanup()

    def verify(self, feature="chat-sidebar", scenario="empty", task="t1"):
        return self.r.tool("verify.py", "--feature", feature, "--scenario", scenario, "--task", task)

    def fake_driver(self, body):
        p = self.r.write("drv.py", "import sys,os,json\n"
                         "a=sys.argv; out=a[a.index('--out')+1]; f=a[a.index('--feature')+1];"
                         " s=a[a.index('--scenario')+1]\n" + body)
        self.r.set_env(f"DRIVER_CMD={PY} '{p}'\nDRIVER_TIMEOUT=3\n")

    def test_pass_writes_evidence_and_log(self):
        code, out = self.verify()
        self.assertEqual(code, 0)
        self.assertIn("RUNTIME: chat-sidebar / empty: PASS", out)
        run_root = self.r.path(".claude", "verification-runs", "t1", "chat-sidebar", "empty")
        run_dirs = [os.path.join(run_root, d) for d in os.listdir(run_root)]
        self.assertEqual(len(run_dirs), 1)
        self.assertTrue(os.path.isfile(os.path.join(run_dirs[0], "sidebar-empty.txt")))
        with open(self.r.path(".claude", "verification-runs", "t1", "log.jsonl")) as fh:
            log = [json.loads(line) for line in fh]
        self.assertEqual(log[-1]["status"], "pass")

    def test_evidence_path_traversal_rejected(self):
        self.fake_driver("open(os.path.join(out,'e'),'w').write('not evidence');"
                         "json.dump({'feature':f,'scenario':s,'status':'pass','summary':'',"
                         "'evidence':['../README']},open(os.path.join(out,'result.json'),'w'))")
        code, out = self.verify()
        self.assertEqual(code, 4)
        self.assertIn("escape the output directory", out)

    def test_evidence_symlink_escape_rejected(self):
        self.fake_driver("os.symlink(os.path.join(os.getcwd(),'README'),os.path.join(out,'e'));"
                         "json.dump({'feature':f,'scenario':s,'status':'pass','summary':'',"
                         "'evidence':['e']},open(os.path.join(out,'result.json'),'w'))")
        code, out = self.verify()
        self.assertEqual(code, 4)
        self.assertIn("escape the output directory", out)

    def test_repeated_runs_preserve_separate_evidence(self):
        self.assertEqual(self.verify()[0], 0)
        self.assertEqual(self.verify()[0], 0)
        run_root = self.r.path(".claude", "verification-runs", "t1", "chat-sidebar", "empty")
        run_dirs = os.listdir(run_root)
        self.assertEqual(len(run_dirs), 2)
        for run_dir in run_dirs:
            self.assertTrue(os.path.isfile(os.path.join(run_root, run_dir, "sidebar-empty.txt")))

    def test_unsupported_and_unlisted(self):
        code, out = self.verify(scenario="offline")
        self.assertEqual(code, 3)
        self.assertIn("NOT RUN", out)
        self.assertIn("not listed", self.verify(scenario="weird")[1])

    def test_unknown_feature_bad_id_unconfigured(self):
        self.assertEqual(self.verify(feature="nope")[0], 2)
        self.assertEqual(self.verify(feature="../etc")[0], 2)
        self.r.set_env("")
        self.assertEqual(self.verify()[0], 3)

    def test_contract_violations(self):
        bodies = {
            "no result.json": "sys.exit(0)",
            "status/exit mismatch": "json.dump({'feature':f,'scenario':s,'status':'pass','summary':'',"
                                    "'evidence':['e']},open(os.path.join(out,'result.json'),'w'));"
                                    "open(os.path.join(out,'e'),'w');sys.exit(1)",
            "missing evidence": "json.dump({'feature':f,'scenario':s,'status':'pass','summary':'',"
                                "'evidence':['nope.png']},open(os.path.join(out,'result.json'),'w'))",
            "pass without evidence": "json.dump({'feature':f,'scenario':s,'status':'pass','summary':'',"
                                     "'evidence':[]},open(os.path.join(out,'result.json'),'w'))",
            "wrong feature echoed": "json.dump({'feature':'x','scenario':s,'status':'fail','summary':'',"
                                    "'evidence':[]},open(os.path.join(out,'result.json'),'w'));sys.exit(1)",
            "invalid JSON": "open(os.path.join(out,'result.json'),'w').write('{');sys.exit(0)",
            "timeout": "import time; time.sleep(10)",
            "crash": "raise SystemExit(7)",
        }
        for label, body in bodies.items():
            with self.subTest(label):
                self.fake_driver(body)
                code, out = self.verify()
                self.assertEqual(code, 4)
                self.assertIn("contract violation", out)

    def test_real_fail(self):
        self.fake_driver("json.dump({'feature':f,'scenario':s,'status':'fail','summary':'button missing',"
                         "'evidence':[]},open(os.path.join(out,'result.json'),'w'));sys.exit(1)")
        code, out = self.verify()
        self.assertEqual(code, 1)
        self.assertIn("FAIL. button missing", out)


class Settings(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(PACK, "settings.json")) as fh:
            self.s = json.load(fh)

    def test_fail_closed_only_on_the_edit_guard(self):
        for event, groups in self.s["hooks"].items():
            for grp in groups:
                for h in grp["hooks"]:
                    fail_closed = h.get("onFailure") == "block"
                    self.assertEqual(fail_closed, "block_suppressions" in h["command"], f"{event}: {h['command']}")

    def test_matchers_cover_notebooks_and_scripts_exist(self):
        for event in ("PreToolUse", "PostToolUse"):
            self.assertIn("NotebookEdit", self.s["hooks"][event][0]["matcher"])
        for groups in self.s["hooks"].values():
            for grp in groups:
                for h in grp["hooks"]:
                    script = h["command"].split('"')[1].replace("$CLAUDE_PROJECT_DIR/.claude", PACK)
                    self.assertTrue(os.path.isfile(script), script)


if __name__ == "__main__":
    unittest.main(verbosity=2)
