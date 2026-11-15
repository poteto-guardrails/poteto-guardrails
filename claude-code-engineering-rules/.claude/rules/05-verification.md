---
description: Verify behavior and invariants with executable evidence; invest in reusable drivers and feature vocabulary.
---

# Verification strategy

Verification is a core part of implementation, not an optional final step. Agents dramatically lower the cost of writing code; that shift makes investing more heavily in verification economically rational. Prefer comprehensive, cost-effective confidence over the smallest possible test suite.

## Before implementation

- Translate the request into observable expected behavior.
- Identify important invariants, edge cases, failure modes, and compatibility requirements.
- If desired behavior is ambiguous, ask a focused question or state the assumption before making a consequential choice.
- Choose checks that can demonstrate the behavior, not merely exercise code paths.

## Deterministic checks

Run the most relevant available checks, selecting commands from repository scripts and documentation rather than guessing:

- focused unit tests;
- integration and end-to-end tests;
- type checking and static analysis;
- linting and formatting;
- compilation and production build;
- regression tests for previously observed failures.

Start focused, then broaden scope in proportion to change size and risk.

## Runtime verification

For UI, client, service, or integration changes, run the actual system when feasible.

- Exercise the feature as a real user or consumer would.
- Prefer the repository’s established CLI, application driver, or test harness over inventing a new manual procedure for every run. Those drivers should themselves be reliable and, where practical, tested.
- Capture useful evidence: screenshots, short recordings, traces, logs, or reproducible test output.
- Verify loading, success, empty, error, cancellation, retry, and boundary states where relevant.
- Do not infer success from a page rendering or a process starting; verify the requested behavior.

## Feature vocabulary

Maintain or use a feature map: a user-facing inventory of features, screens, controls, and flows. Use the application’s established names in plans, tests, and reports. Vague descriptions force agents (and reviewers) to guess.

## Higher-assurance techniques

Use stronger techniques when risk justifies the cost:

- Property-based tests for broad input spaces and invariants.
- Fuzzing for parsers, protocol boundaries, stateful flows, and robustness.
- Model or state-machine checking for complex workflows, concurrency, and transition systems.
- Formal verification for critical algorithms and properties where the investment is warranted.

These are additional layers, not substitutes for ordinary tests and runtime verification.

## Reporting

Report:

- exactly which commands and checks were run;
- whether each passed or failed;
- what runtime scenarios were exercised;
- evidence produced and where it lives;
- checks not run, with the reason;
- remaining uncertainty or known limitations.

Never fabricate test output, screenshots, recordings, coverage, or verification results.
