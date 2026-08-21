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

# The engine's own suite. Run with the interpreter on PATH rather than
# .venv's, and with src/ on PYTHONPATH rather than an installed copy,
# because both are how the floor gets exercised: CI runs this same
# command on an interpreter at the version floor, where nothing is
# installed and no virtualenv exists. `PYTHON=python3.9 just test` does
# the same on a workstation that has one.
#
# The engine has zero dependencies (SPECIFICATIONS.md §3.1), so the
# suite needs nothing installed to run — which is what makes that
# possible.
PYTHON="${PYTHON:-python3}"

echo "test: the engine's suite on $("$PYTHON" -V 2>&1)"
PYTHONPATH=src "$PYTHON" -m unittest discover \
    --start-directory tests --top-level-directory tests
