---
description: Verify behavior, invariants, and user intent with executable evidence.
---

# Verification strategy

Verification is a core part of implementation, not an optional final step.

## Before implementation

- Translate the request into observable expected behavior.
- Identify important invariants, edge cases, failure modes, and compatibility requirements.
- If the desired behavior is ambiguous, ask a focused question or state the assumption before making a consequential choice.
- Choose checks that can demonstrate the behavior, not merely exercise code paths.

## Deterministic checks

Run the most relevant available checks, selecting commands from repository scripts and documentation rather than guessing:

- focused unit tests;
- integration and end-to-end tests;
- type checking and static analysis;
- linting and formatting;
- compilation and production build;
- regression tests for previously observed failures.

Start with focused checks, then broaden the verification scope in proportion to the change and risk.

## Runtime verification

For UI, client, service, or integration changes, run the actual system when feasible.

- Exercise the feature as a real user or consumer would.
- Use the available browser, application driver, CLI, debugger, logs, and runtime inspection tools.
- Reuse the repository's established CLI/driver instead of inventing a new manual procedure for every run.
- Capture useful evidence such as screenshots, short recordings, traces, logs, or reproducible test output.
- Verify loading, success, empty, error, cancellation, retry, and boundary states where relevant.
- Do not infer success from a page rendering or a process starting; verify the requested behavior.

## Feature vocabulary

When the application is large, use or maintain a feature map: a user-facing inventory of features, screens, controls, and flows. Use the application's established names in plans, tests, and reports rather than vague descriptions such as "the thing on the left."

## Higher-assurance verification

Use stronger techniques when warranted by risk:

- Property-based tests for broad input spaces and invariants.
- Fuzzing for parsers, protocol boundaries, stateful flows, and robustness.
- Model/state-machine checking for complex workflows, concurrency, cross-device behavior, and transition systems.
- Formal verification or proofs for critical algorithms and properties where the cost is justified.

Formal methods are an additional layer, not a substitute for ordinary tests and runtime verification.

## Reporting

Report:
- exactly which commands/checks were run;
- whether each passed or failed;
- what runtime scenarios were exercised;
- evidence produced and where it is located;
- checks not run, with the reason;
- remaining uncertainty or known limitations.

Never fabricate test output, screenshots, recordings, coverage, or verification.
