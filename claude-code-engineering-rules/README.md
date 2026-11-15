# Claude Code engineering rules

This pack translates the engineering principles in Lauren Tan's presentation, “All Code Is Slop (Except Mine),” into Claude Code project instructions.

## Install

Copy `CLAUDE.md` and the `.claude/` directory into the root of the repository:

```bash
cp -r CLAUDE.md .claude /path/to/your/repository/
```

If the repository already has a `CLAUDE.md`, merge the contents rather than overwriting existing project instructions. If `.claude/rules/` already exists, add these rule files alongside the existing ones.

Claude Code loads the root `CLAUDE.md` and the Markdown rule files in `.claude/rules/`. The rule files are deliberately general; repository-specific lint commands, test commands, directory scopes, and architecture boundaries should be added after inspecting the target codebase.

## Files

- `CLAUDE.md` — short project-wide operating principles and precedence.
- `.claude/rules/01-codebase-hygiene.md` — avoid copying technical debt and bad patterns.
- `.claude/rules/02-architecture-and-boundaries.md` — APIs, layering, dependency constraints.
- `.claude/rules/03-implementation-and-patterns.md` — root-cause fixes and implementation choices.
- `.claude/rules/04-deterministic-quality-gates.md` — turn recurring mistakes into enforceable checks.
- `.claude/rules/05-verification.md` — test, runtime, evidence, property-based and formal verification.
- `.claude/rules/06-comments-and-documentation.md` — accurate, useful documentation without prose loopholes.
- `.claude/rules/07-review-and-autonomy.md` — evidence-based review and graduated autonomy.

## Important distinction

The presentation's central point is that trust should come primarily from the engineering environment: good architecture, deterministic checks, and verification. These Markdown rules provide judgment guidance; they do not replace implementation-specific lint rules, tests, CI, permissions, or human authorization.

The presentation's examples (including restrictions on particular React APIs, timers, and comments) are specific to the speaker's codebases. This pack captures the underlying principles and does not impose those bans universally.
