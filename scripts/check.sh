#!/usr/bin/env bash
# Is what is committed here well-formed?
#
# Usage: check.sh [all|changed]
#
#   all      (default) every file in the working tree, tracked or not
#   changed  only what differs from HEAD, for a fast pass while working
#
# One entry point taking a scope, never two recipes: two recipes hold two
# lists of checks and will eventually differ in *what* they look for, not
# only in how much they look at.
#
# The file list is passed explicitly rather than left to
# `pre-commit run --all-files`, which enumerates from git and so cannot
# see a file that exists but was never added to the index. A lint error
# in such a file must still fail this command. Never
# `git add --intent-to-add` to make git aware of it: that writes to the
# index as a side effect of a check, turns `?? file` into ` A file` in
# `git status --porcelain` — the output the handover and approve rituals
# read for their clean-tree preconditions — and lets the next
# `git commit -a` sweep the file into an unrelated commit.
#
# Path exclusions (.claude/spec-work/, .claude/refs/) live in
# .pre-commit-config.yaml, in one place, so this script holds no policy.
#
# This command asserts and never repairs. Some hooks are fixers, and the
# commit hook is where they are allowed to write; here their edits are
# reverted and reported as failures. A check that rewrites the working
# tree as a side effect is the --intent-to-add prohibition one step
# milder.
set -euo pipefail

cd "$(dirname "$0")/.."

SCOPE="${1:-all}"
PRE_COMMIT=.venv/bin/pre-commit

if [ ! -x "$PRE_COMMIT" ]; then
    echo "check: toolchain missing — run 'just setup' first" >&2
    exit 1
fi

case "$SCOPE" in
    all)
        mapfile -t candidates < <(git ls-files --cached --others --exclude-standard)
        ;;
    changed)
        mapfile -t candidates < <(
            { git diff --name-only HEAD
              git ls-files --others --exclude-standard
            } | sort -u
        )
        ;;
    *)
        echo "check: unknown scope '$SCOPE' (expected 'all' or 'changed')" >&2
        exit 2
        ;;
esac

# Deleted-but-still-in-index paths are listed by git and cannot be linted.
files=()
for f in "${candidates[@]}"; do
    [ -f "$f" ] && files+=("$f")
done

if [ "${#files[@]}" -eq 0 ]; then
    echo "check ($SCOPE): nothing to check"
    exit 0
fi

# Snapshot, so a fixer hook's edits can be reverted below.
snapshot="$(mktemp -d)"
trap 'rm -rf "$snapshot"' EXIT
for f in "${files[@]}"; do
    mkdir -p "$snapshot/$(dirname "$f")"
    cp -p "$f" "$snapshot/$f"
done

status=0
"$PRE_COMMIT" run --files "${files[@]}" || status=$?

repaired=()
for f in "${files[@]}"; do
    if ! cmp -s "$f" "$snapshot/$f"; then
        cp -p "$snapshot/$f" "$f"
        repaired+=("$f")
    fi
done

if [ "${#repaired[@]}" -gt 0 ]; then
    echo >&2
    echo "check: a fixer hook wanted to rewrite these files:" >&2
    printf '  %s\n' "${repaired[@]}" >&2
    echo "check reverted them and is failing instead — commit to apply the fix," >&2
    echo "or run '.venv/bin/pre-commit run --files <path>' to write it now." >&2
    status=1
fi

exit "$status"
