#!/usr/bin/env bash
# Is the implementation right?
#
# Fixtures and expectations proving the behaviour this repository itself
# ships — the cases that must fail included. A third-party tool is never
# retested here: that shellcheck reports SC2086 is its maintainers'
# problem, not this repository's.
set -euo pipefail

cd "$(dirname "$0")/.."

# This repository ships no behaviour of its own yet. Saying so is the
# correct state of this command, not a gap to fill: the engine, its
# suites and the guard's own selftest join at the steps that create
# them (PLAN.md 001 and 006 onward).
echo "test: this repository ships no behaviour of its own yet — nothing to prove."
echo "test: suites join with the artifacts they test (PLAN.md 001, 006 onward)."
