# Claude Code engineering rules (v2)

This pack translates the engineering principles in Lauren Tan’s presentation, “All Code Is Slop (Except Mine),” into Claude Code project instructions.

Version 2 strengthens the original pack by:

- Treating Markdown rules as thin operating policy, subordinate to architecture, deterministic checks, and verification.
- Making the agent-correction → deterministic-guardrail feedback loop operational.
- Emphasizing repository structure and directory layout as primary context and control mechanisms.
- Expanding runtime verification concepts (feature maps, reusable drivers, evidence artefacts).
- Explicitly stating the economics of verification under agentic development.
- Giving clearer sequencing: improve the codebase and verification foundation before scaling automation.
- Better covering the outer “software factory” loop (automated projects, post-release fuzzing, evidence-based autonomous PRs).

## Install

Copy `CLAUDE.md` and the `.claude/` directory into the root of the target repository:

```bash
cp -r CLAUDE.md .claude /path/to/your/repository/
```

If the repository already has a `CLAUDE.md` or `.claude/rules/`, merge rather than overwrite. These files are deliberately general; after inspection, add repository-specific lint commands, test commands, directory ownership, dependency boundaries, feature maps, and drivers.

## Files

- `CLAUDE.md` — short project-wide operating principles and precedence (inverted pyramid).
- `.claude/rules/01-codebase-hygiene.md` — treat the codebase as high-quality agent context; remediate rather than copy debt.
- `.claude/rules/02-architecture-and-boundaries.md` — structure, ownership, APIs, and enforced dependency direction.
- `.claude/rules/03-implementation-and-patterns.md` — root-cause fixes; avoid architectural workarounds.
- `.claude/rules/04-deterministic-quality-gates.md` — the operational feedback loop that turns recurring mistakes into checks.
- `.claude/rules/05-verification.md` — tests, runtime evidence, feature maps, reusable drivers, higher-assurance techniques.
- `.claude/rules/06-comments-and-documentation.md` — comments and prose are subordinate to executable truth.
- `.claude/rules/07-review-and-autonomy.md` — evidence-based review and graduated autonomy, including the outer automation loop.

## Important distinction

The presentation’s central point is that trust should come primarily from the engineering environment. These Markdown files provide judgment guidance and a process for improving that environment. They do not replace:

- architecture and directory structure,
- lint rules, type checks, dependency-boundary enforcement,
- tests and CI,
- feature maps and reusable application drivers,
- runtime and formal verification infrastructure,
- branch protection, ownership, and human authorization for high-impact actions.

Repository-specific examples in the talk (particular React APIs, timers, comment density) are not universal bans. Capture the underlying principle and enforce it with the repository’s own tools.
