---
name: add-guardrail
description: Turn a recurring agent or human mistake into a deterministic check (an API change, a lint rule, a dependency-boundary rule, a test). Only run when a human asks with /add-guardrail.
disable-model-invocation: true
---

# Add a guardrail

A human asked for this, so editing check configuration is in scope. Expect approval prompts on those files; that's intended.
Work on a separate branch, with nothing else in the change.

1. **Write down the failure.** Give a concrete bad example (file and line, or a snippet) and the rule it broke, in one sentence.
2. **Try design first.** Can an API or architecture change make the bad approach impossible or awkward (a restricted wrapper, a narrower type, a directory boundary)? If so, propose that and stop for agreement before building it.
3. **Otherwise pick the narrowest check** that catches the failure: a lint rule (built-in options like `no-restricted-*` before a custom rule), a dependency-graph rule, a type, or a test. See `examples/` for patterns. For a stateful flow or a critical algorithm, a property-based test, a TLA+ model or a Lean proof may fit better. Propose it and let the human decide whether it's worth the cost.
4. **Make the error message do the teaching.** It names the root-cause fix ("subscribe to X instead of polling"), not just the ban. Agents follow error messages more reliably than prose.
5. **Prove it works both ways.** Add a fixture or test showing the check rejects the bad example and accepts at least one legitimate use.
6. **Prove it runs.** Confirm the check runs in `FAST_CHECK_CMD` or `FULL_CHECK_CMD` and in CI. Show the command output.
7. **Count existing violations.** Report how many there are and where. Fix them only if the human says to; otherwise propose a follow-up.
8. **Record it** as one row in `.claude/rules/bans.md` (banned / enforced by / do instead).

Don't add the rule as prose anywhere else.
