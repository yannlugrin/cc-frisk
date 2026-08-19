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
# index as a side effect of a check, turning an untracked `??` line into
# an added `A` one in `git status --porcelain` — the output the handover
# and approve rituals read for their clean-tree preconditions — and
# letting the next `git commit -a` sweep the file into an unrelated
# commit.
#
# Path exclusions (.claude/spec-work/, .claude/refs/) live in
# .pre-commit-config.yaml, in one place, so this script holds no policy.
#
# This command asserts and never repairs. Some hooks are fixers, and the
# commit hook is where they are allowed to write; here their edits are
# reverted and reported as failures. A check that rewrites the working
# tree as a side effect is the --intent-to-add prohibition one step
# milder. The revert runs from an EXIT trap, so an interrupt part-way
# through a slow run restores the tree too — without it, Ctrl-C would
# leave every fixer edit on disk and delete the only copy of an
# untracked file's original content.
#
# Nothing here runs a git write. Enumeration and `rev-parse` are reads;
# every restore is a plain `cp` from a temporary snapshot.
#
# Portable to bash 3.2 (stock macOS): no mapfile, no associative arrays.
set -euo pipefail

cd "$(dirname "$0")/.."

SCOPE="${1:-all}"
PRE_COMMIT=.venv/bin/pre-commit

case "$SCOPE" in
    all|changed) ;;
    *)
        echo "check: unknown scope '$SCOPE' (expected 'all' or 'changed')" >&2
        exit 2
        ;;
esac

if [ ! -x "$PRE_COMMIT" ]; then
    echo "check: toolchain missing — run 'just setup' first" >&2
    exit 1
fi

# NUL-separated, and core.quotePath=false so a non-ASCII path arrives as
# itself rather than as a C-quoted string that would fail every test
# below and be dropped in silence. The two sources of each scope are
# disjoint by construction — `--cached` never overlaps `--others`, and a
# file modified against HEAD is by definition tracked — so nothing needs
# de-duplicating.
enumerate() {
    case "$SCOPE" in
        all)
            git -c core.quotePath=false ls-files -z \
                --cached --others --exclude-standard || return 1
            ;;
        changed)
            if git rev-parse --verify -q HEAD >/dev/null 2>&1; then
                git -c core.quotePath=false diff -z --name-only HEAD || return 1
            fi
            git -c core.quotePath=false ls-files -z \
                --others --exclude-standard || return 1
            ;;
    esac
}

snapshot=""
list_file=""
files=()
repaired=()
unrestored=0

# Restore anything a fixer hook rewrote. Idempotent: the main path calls
# it to report, and the EXIT trap calls it again to catch interrupts.
revert() {
    [ -n "$snapshot" ] || return 0
    [ "${#files[@]}" -gt 0 ] || return 0
    repaired=()
    local f
    for f in "${files[@]}"; do
        [ -e "$snapshot/$f" ] || continue
        if cmp -s -- "$f" "$snapshot/$f"; then
            continue
        fi
        if cp -p -- "$snapshot/$f" "$f"; then
            repaired+=("$f")
        else
            echo "check: FAILED TO RESTORE $f" >&2
            unrestored=1
        fi
    done
}

# Invoked through the traps below; shellcheck cannot see that (SC2329).
# shellcheck disable=SC2329
cleanup() {
    revert
    [ -n "$list_file" ] && rm -f "$list_file"
    if [ -n "$snapshot" ]; then
        if [ "$unrestored" -eq 1 ]; then
            echo "check: keeping the snapshot of unrestored files at $snapshot" >&2
        else
            rm -rf "$snapshot"
        fi
    fi
    return 0
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
trap 'exit 129' HUP

list_file="$(mktemp)"
if ! enumerate >"$list_file"; then
    echo "check: could not enumerate files to check" >&2
    exit 1
fi

# Deleted-but-still-indexed paths cannot be linted. Broken symlinks can:
# check-symlinks exists for exactly them, so -L must be tested too.
while IFS= read -r -d '' f; do
    if [ -f "$f" ] || [ -L "$f" ]; then
        files+=("$f")
    fi
done <"$list_file"

if [ "${#files[@]}" -eq 0 ]; then
    echo "check ($SCOPE): nothing to check"
    exit 0
fi

# Snapshot, so a fixer hook's edits can be reverted below.
snapshot="$(mktemp -d)"
for f in "${files[@]}"; do
    mkdir -p "$snapshot/$(dirname -- "$f")"
    cp -p -- "$f" "$snapshot/$f"
done

# pre-commit takes its file list positionally and accepts no `--`
# terminator, so a leading-dash path would be read as an option. Say so
# clearly rather than letting argparse dump its usage.
for f in "${files[@]}"; do
    case "$f" in
        -*)
            echo "check: cannot check '$f' — a leading dash reads as an option" >&2
            echo "check: rename it, or place it in a subdirectory" >&2
            exit 2
            ;;
    esac
done

status=0
"$PRE_COMMIT" run --files "${files[@]}" || status=$?

revert

if [ "${#repaired[@]}" -gt 0 ]; then
    echo >&2
    echo "check: a fixer hook wanted to rewrite these files:" >&2
    printf '  %s\n' "${repaired[@]}" >&2
    echo "check reverted them and is failing instead — commit to apply the fix," >&2
    echo "or run '.venv/bin/pre-commit run --files <path>' to write it now." >&2
    status=1
fi

if [ "$unrestored" -eq 1 ]; then
    status=1
fi

exit "$status"
