#!/usr/bin/env bash
# Install the pinned toolchain into ./.venv and register the commit
# hooks. Idempotent: safe to re-run at any time.
set -euo pipefail

cd "$(dirname "$0")/.."

VENV=.venv

if [ ! -x "$VENV/bin/python" ]; then
    echo "creating $VENV"
    python3 -m venv "$VENV"
fi

# No `pip install --upgrade pip` here: it fetches an unpinned tool from
# the network on every run, which is exactly what the pinned-toolchain
# claim is meant to exclude. The pip that venv ships is sufficient.
"$VENV/bin/python" -m pip install --quiet -r requirements.txt

# The commit hooks run the same checks as `just check`, so the local
# runners cannot diverge.
"$VENV/bin/pre-commit" install

echo "setup complete: $("$VENV/bin/pre-commit" --version)"
