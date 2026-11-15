# Engineering operating principles

These instructions turn the engineering principles in Lauren Tan's presentation, **“All Code Is Slop (Except Mine)”**, into practical Claude Code defaults.

## Primary objective

Increase engineering throughput without reducing software quality. Trust is earned through the repository, deterministic constraints, and verification—not assumed from an agent's confidence.

## Order of preference

When addressing a recurring failure or quality problem, prefer the strongest enforceable solution:

1. **Architecture/API design** that makes the incorrect approach impossible or unnatural.
2. **Deterministic enforcement**: compiler/type checker, linter, formatter, dependency-boundary check, tests, or CI.
3. **Runtime and formal verification** appropriate to the risk.
4. **These written instructions** for decisions that genuinely require judgment.

Do not solve a problem with another paragraph of instructions if it can be prevented or detected reliably in code. If you encounter a repeated agent mistake, recommend a deterministic guardrail and, when within scope, implement it.

## Working in this repository

- Inspect the existing architecture, conventions, scripts, and tests before changing code.
- Treat existing code as input to future agents. Do not copy a workaround, anti-pattern, obsolete implementation, or technical debt merely because it appears established.
- Follow the intended architecture and the narrowest relevant module boundary.
- Prefer simple, explicit, maintainable designs over cleverness or hidden behavior.
- Keep changes focused. Avoid unrelated cleanup unless it is necessary to make the requested change correct.
- Do not invent repository conventions, APIs, commands, or verification results. Discover them first.
- Preserve existing behavior unless the task explicitly changes it. Identify compatibility and migration implications.

## Verification is part of implementation

- Define the expected behavior and important invariants before making a risky change.
- Run the most relevant available deterministic checks: targeted tests, type checking, linting, formatting, compilation/build, and broader tests as appropriate.
- For user-visible behavior, run the application or relevant runtime and exercise the changed flow where feasible.
- Use available debugging/inspection tools rather than relying only on static reading.
- Provide concrete evidence: commands run, pass/fail results, and relevant screenshots, recordings, traces, diagrams, or test output when useful and available.
- Never claim a check passed unless it was actually run and passed. Clearly identify checks not run and why.
- Use formal methods, model checking, or property-based testing when the system's risk and complexity justify them; do not add them ceremonially.

## Autonomy and safety

- Autonomy must be supported by reliable guardrails and verification.
- Never bypass a failing check, weaken a test, suppress a diagnostic, or add a lint exemption merely to make a change pass.
- Do not merge, deploy, publish, or perform destructive operations unless the user/task explicitly authorizes that action and repository policy permits it.
- If verification exposes an invariant violation or unclear product intent, stop and resolve the issue rather than guessing.

## Detailed rules

The files under `.claude/rules/` provide focused guidance. Follow the rules relevant to the files being changed.
