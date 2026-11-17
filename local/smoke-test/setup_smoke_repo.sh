#!/usr/bin/env bash
# Build a disposable repository with the pack installed and deterministic fake checks,
# for the live smoke test in SMOKE-TEST.md. Never point this at a real project.
#   bash smoke-test/setup_smoke_repo.sh /tmp/guardrail-smoke
set -euo pipefail

DEST="${1:?usage: setup_smoke_repo.sh <new-empty-directory>}"
PACK="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [ -e "$DEST" ] && [ -n "$(ls -A "$DEST" 2>/dev/null)" ]; then
  echo "Refusing: $DEST exists and isn't empty." >&2
  exit 1
fi
mkdir -p "$DEST"
cd "$DEST"
git init -q

cp -R "$PACK/.claude" "$PACK/CLAUDE.md" "$PACK/docs" "$PACK/examples" .
printf '\n# Python bytecode\n__pycache__/\n*.py[cod]\n\n# Generated Claude runtime-verification evidence\n.claude/verification-runs/\n\n# Smoke test: full-check invocation counter\n.smoke/\n' >> .gitignore
rm -rf .claude/tests

mkdir -p src
cat > src/app.ts <<'EOF'
export function greet(name: string): string {
  return `Hello, ${name}`;
}
EOF

# Deterministic fake checks:
#   fast check fails if an edited file contains BAD_LINT
#   full check fails if any file under src/ contains FAIL_FULL, and appends a line to
#   .smoke/check-runs.log (git-ignored) every time it really runs
cat > .claude/guardrails.env <<'EOF'
FAST_CHECK_CMD=grep -q BAD_LINT {file} && echo "lint: BAD_LINT is not allowed in {file}" && exit 1 || exit 0
FAST_CHECK_GLOBS=*.ts
FAST_CHECK_TIMEOUT=30
FULL_CHECK_CMD=mkdir -p .smoke && echo run >> .smoke/check-runs.log && ! grep -rn FAIL_FULL src
FULL_CHECK_TIMEOUT=60
STOP_GATE_MAX_RETRIES=2
DRIVER_CMD=python3 examples/driver_stub.py
DRIVER_TIMEOUT=60
SUPPRESSION_REGEX=
SUPPRESSION_EXEMPT_GLOBS=.claude/**
EOF

git add -A
git -c user.email=smoke@test -c user.name=smoke commit -qm "smoke test baseline"

echo "Smoke repository ready: $DEST"
echo "Next: cd \"$DEST\" && claude    then follow $PACK/smoke-test/SMOKE-TEST.md"
