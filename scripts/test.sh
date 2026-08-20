#!/usr/bin/env bash
# Is the implementation right?
#
# Fixtures and expectations proving the behaviour this repository itself
# ships — the cases that must fail included. A third-party tool is never
# retested here: that shellcheck reports SC2086 is its maintainers'
# problem, not this repository's.
set -euo pipefail

cd "$(dirname "$0")/.."

# The development guard's own selftest: liveness, then every case, then
# coverage — a rule or grant no case reaches fails it, which is what
# keeps the registry's intent executable rather than remembered.
#
# Skipped where the guard is absent, keyed on the backup ref rather than
# on the guard file, for the reasons scripts/check-guard.sh sets out: the
# guard is machine-local and never tracked (CLAUDE.md rule 1), and a
# gate keyed on the file it guards goes inert exactly when the file
# disappears.
GUARD=.claude/hooks/bash_guard.py
MARKER=refs/backups/bash-guard

if git rev-parse --verify -q "$MARKER" >/dev/null 2>&1; then
    if [ ! -x "$GUARD" ]; then
        echo "test: $MARKER exists but $GUARD is missing or not executable." >&2
        echo "test: restore it — .claude/docs/guard-record.md carries the recipe." >&2
        exit 1
    fi
    echo "test: the development guard's selftest"
    "$GUARD" --selftest
else
    echo "test: no $MARKER here — the development guard is absent by design (skipped)."
fi

# Beyond that guard, this repository ships no behaviour of its own yet.
# Saying so is the correct state of this command, not a gap to fill: the
# engine and its suites join at the steps that create them (PLAN.md 006
# onward).
echo "test: no product behaviour to prove yet — the engine's suites join at PLAN.md 006."
