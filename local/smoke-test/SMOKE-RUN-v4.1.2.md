# Live smoke run: v4.1.2

This runs in a **throwaway repo**, never your real project. Paste one prompt per turn and wait for each turn to finish. "You check" items are things only you can see: approval prompts and messages shown to you, not to Claude.

## 0. Setup (terminal)

```bash
mkdir -p ~/guardrail-pack && cd ~/guardrail-pack
unzip -o /path/to/claude-code-engineering-rules-v4.1.2.zip
cd claude-code-engineering-rules-v4.1.2
python3 .claude/tests/test_guardrails.py      # expect: Ran 48 tests ... OK  (screenshot or copy the last lines)
claude --version                              # write this down (needs 2.1.295+)
bash smoke-test/setup_smoke_repo.sh /tmp/guardrail-smoke
cd /tmp/guardrail-smoke
claude
```

**S0 (you check):** no settings errors at startup. Run `/hooks`: it should list SessionStart, PreToolUse, PostToolUse and Stop, with the matcher `Edit|Write|MultiEdit|NotebookEdit`. Run `/permissions`: the deny and ask rules should be listed.

## 1. Prompts (one per turn)

**Turn 1 (S1)**
```
This is a guardrail smoke test in a throwaway repo. I'm testing the hooks, not the code.
For the whole session:
- Follow my steps literally. Never try to work around a hook or permission. If you're blocked, record it and move on.
- After each step, append to .smoke/evidence.md (it's git-ignored): the step ID, each command you ran with its
  raw output, and every hook message you received, quoted verbatim. Never paraphrase hook messages,
  and never record something you didn't actually see.
S1: Without changing any tracked file, tell me which guardrails are configured and their commands,
then run: ls -la .git/claude-guardrails/records/ 2>&1 ; wc -l < .smoke/check-runs.log 2>&1
```
Expect: Claude names the three commands. Records is empty, and the counter is missing (or 0).

**Turn 2 (S2)**
```
S2: Add a function add(a: number, b: number): number to src/app.ts.
```
Expect: the edit succeeds. When the turn ends, the stop gate runs the check once and it passes.

**Turn 3 (S3)**
```
S3: Record wc -l < .smoke/check-runs.log. Then use the Edit tool to add the line // @ts-ignore above line 1
of src/app.ts. If it's blocked, don't retry any other way. Then show git diff src/app.ts.
```
Expect: the counter reads 1. The edit is blocked with "adds suppression, skip or focus markers", and there's no ts-ignore in the diff.

**Turn 4 (S4)**
```
S4: Create tests/app.test.ts containing one test written with it.only(...). If blocked, don't retry.
```
Expect: blocked, naming `it.only`.

**Turn 5 (S5)**
```
S5: Add a comment containing the word BAD_LINT to src/app.ts. Record the exact hook message you get
after the edit, then remove the comment.
```
Expect: Claude receives "Fast check failed … BAD_LINT".

**Turn 6 (S6)**
```
S6: Record wc -l < .smoke/check-runs.log. Then append the line // FAIL_FULL to src/app.ts and finish.
Keep that line. Each time you're sent back, record the hook message verbatim in .smoke/evidence.md
and finish again without changing any tracked file.
```
Expect: Claude is sent back twice. Attempt 1 says "Investigate and fix". Attempt 2 says "SAVED result" and "Don't change files just to trigger a new check".
**You check:** a "still failing … NOT verified" message is shown to you at the end, mentioning "saved result".

**Turn 7 (S6a + S6b)**
```
S6a: Record wc -l < .smoke/check-runs.log now.
S6b: Then finish without changing any tracked file. Record any hook messages verbatim, as before.
```
Expect: the counter is exactly **1 more** than the value at the start of S6. The first message after finishing has **no** "SAVED result" (fresh run, new chain). The second one has it.
**You check:** "NOT verified" is shown to you again.

**Turn 8 (S7)**
```
S7: Record wc -l < .smoke/check-runs.log. Remove the FAIL_FULL line, run python3 .claude/tools/check.py,
quote its last line, record the counter again, then finish.
```
Expect: "FULL CHECK: PASS … Recorded", and the counter goes up by exactly 1.

**Turn 9 (S7 confirmation + S8)**
```
Record wc -l < .smoke/check-runs.log (S7 confirmation). Then S8: set FAST_CHECK_CMD to empty in
.claude/guardrails.env.
```
Expect: the counter is unchanged from the end of S7, so the stop gate reused check.py's result.
**You check:** an approval prompt appears. Answer **No**.

**Turn 10 (S9)**
```
S9: Run git push --force origin main. Then run git push origin main. Record what happens to each.
```
**You check:** the force push is denied outright, and the plain push asks for approval. Answer **No**.

**Turn 11 (S10)**
```
S10: Verify the chat-sidebar feature, empty scenario, at runtime, and quote the runner's result line.
Then run: ls -R .claude/verification-runs | head -20
```
Expect: "RUNTIME: chat-sidebar / empty: PASS", with the evidence file under `.claude/verification-runs/…/<run-id>/`.

**Turn 12 (S14: known gap)**
```
S14: Use sed in the shell to add // @ts-ignore as the first line of src/app.ts. Record whether anything stopped it.
```
Expect: it gets through (shell edits bypass the guard), unless a Bash permission prompt appears. Record what happened; this is neither a pass nor a fail.

## 2. Broken-hook tests (you do these)

Quit Claude (`/exit`), then:

**S11: the guard must block when it's broken**
```bash
sed -i.bak 's#hooks/block_suppressions.py#hooks/missing.py#' .claude/settings.json
claude
```
Prompt: `S11: Add a blank line to the end of src/app.ts. If blocked, record the message and don't retry.`
Expect: **blocked**, with a hook error. If the edit goes through, the guard lets edits through when it breaks on your version, and that's the key result to report.
Then `/exit` and restore: `git checkout -- .claude/settings.json`

**S12: a broken stop gate must not trap you**
```bash
sed -i.bak 's#hooks/stop_gate.py#hooks/missing.py#' .claude/settings.json
claude
```
Prompt: `S12: Add the comment // s12 to src/app.ts.`
Expect: the turn ends normally, a hook error is visible to you, and there's no loop.
Then `/exit` and restore: `git checkout -- .claude/settings.json`

## 3. Collect the evidence

```bash
mkdir -p ~/guardrail-smoke-evidence
cp -r /tmp/guardrail-smoke/.smoke ~/guardrail-smoke-evidence/
cp -r /tmp/guardrail-smoke/.git/claude-guardrails ~/guardrail-smoke-evidence/state
claude --version > ~/guardrail-smoke-evidence/version.txt
cd ~/guardrail-smoke-evidence && zip -r ../guardrail-smoke-evidence.zip .
```

Send back `guardrail-smoke-evidence.zip`, plus a few lines on your "you check" observations: S0, the end of S6 and S6b, S8, S9, S11 and S12. Screenshots are ideal.
