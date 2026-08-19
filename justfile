# Entry points for the toolchain:
#
#   just setup            install the pinned toolchain into ./.venv and
#                         register the commit hooks (idempotent)
#   just check            is what is committed here well-formed? Lint and
#                         formatting over the whole working tree,
#                         untracked files included and gitignored paths
#                         excluded
#   just check changed    the same checks over what differs from HEAD,
#                         for a fast pass while working
#   just test             is the implementation right? The behaviour this
#                         repository itself ships, the cases that must
#                         fail included. It takes no arguments yet; it
#                         gains them with the first suite that needs one
#   just verify           both — what CI runs, and what a step passes
#                         before it is handed over
#
# setup and check pass their arguments to their script unchanged, so the
# two surfaces cannot drift: what `just check` accepts is what
# scripts/check.sh documents. Running those scripts directly is
# equivalent; verify has no script of its own, it runs check then test.
#
# `just` itself is a system tool, installed per workstation like python3
# and git rather than pinned in requirements.txt — so `just setup` is the
# entry point with nothing before it.
#
# No recipe here ever performs an act CLAUDE.md rule 9 gates. A
# PreToolUse guard judges the command it is given — `just release`, never
# the push inside it — so a gated act behind a recipe name would bypass
# the gate unseen. Gated acts live in CI, or in a command the operator
# invokes directly.

# install the pinned toolchain into ./.venv (idempotent)
setup:
    bash scripts/setup.sh

# is what is committed here well-formed? (scope: all | changed)
check scope="all":
    bash scripts/check.sh {{ scope }}

# is the implementation right?
test:
    bash scripts/test.sh

# both — what CI runs, and what a step passes before it is handed over
verify: check test
