#!/usr/bin/env bash
# Is the permission boundary intact?
#
# Two questions, because a PreToolUse hook fails *open*: when it crashes,
# is missing, or loses its executable bit, Claude Code logs the failure
# and falls through to the permission rules. Every one of those deaths is
# silent from inside a session, so they are asserted here instead.
#
#   1. Governance well-formedness, everywhere. The settings files parse,
#      hooks are not globally disabled, auto memory is still off
#      (CLAUDE.md rule 3), the permission invariants D-011 commits to are
#      still true — the deny backstop is not empty, the mode is not a
#      permissive one, the bypass lock is still set — and a PreToolUse
#      hook still names the guard. A settings file that loads, lints
#      green and has quietly stopped protecting anything is the failure
#      this catches, and one silent well-formed edit is exactly how it
#      would happen.
#
#   2. The guard answers, only where the guard belongs. It exists, is
#      executable, its registry builds — and the command line the
#      settings actually register still returns a deny verdict for a
#      command that must never be allowed. Executing the registered line
#      rather than pattern-matching it is what distinguishes a working
#      hook from a string that merely mentions the right path.
#
# The second question is asked only on a machine that instantiated the
# guard, because the guard is machine-local and never tracked (CLAUDE.md
# rule 1): CI and fresh clones never have it, and a check that failed
# there would be a committed reference to an absent file. The marker is
# `refs/backups/bash-guard`, the backup ref the instantiation creates —
# it exists exactly on machines where the guard is expected, and it is
# outside `refs/heads/`, so no clone or default refspec carries it.
# Keying on the guard file itself would be worthless: a deleted guard
# would make its own gate inert, which is the silent death being hunted.
#
# Linked worktrees are the one place those two facts come apart: refs
# live in the common git directory, so the marker is visible, while the
# gitignored guard is not materialized there. That combination — tracked
# settings granting broad allows, no guard behind them — is the worst
# state this file knows about, so it is named loudly rather than skipped.
#
# Behaviour cases live in the guard's own `--selftest`, wired into
# `just test`. This stays a lint: structure, contract, and one verdict.
#
# Portable to bash 3.2 (stock macOS): no mapfile, no associative arrays.
set -euo pipefail

cd "$(dirname "$0")/.."

SETTINGS=.claude/settings.json
LOCAL_SETTINGS=.claude/settings.local.json
GUARD=.claude/hooks/bash_guard.py
MARKER=refs/backups/bash-guard

fail() {
    printf 'check-guard: %s\n' "$*" >&2
    exit 1
}

[ -f "$SETTINGS" ] || fail "$SETTINGS is missing — it is the boundary itself"

# 1. Governance well-formedness. python3 is already a workstation
# prerequisite (scripts/setup.sh builds the venv with it). The hook
# assertion is that a registration *names* the guard, not that the path
# resolves: on a machine without the guard the path cannot resolve, and a
# typo or a rename is what this half is looking for. Question 2 below is
# what proves the line actually works. The registered command line is
# printed on stdout for it.
guard_command="$(python3 - "$SETTINGS" "$LOCAL_SETTINGS" "$GUARD" <<'PY'
import json
import sys

settings_path, local_path, guard = sys.argv[1], sys.argv[2], sys.argv[3]
problems = []


def load(path, required):
    try:
        with open(path, encoding="utf-8") as handle:
            loaded = json.load(handle)
    except FileNotFoundError:
        if required:
            problems.append("%s is missing" % path)
        return {}
    except (OSError, ValueError) as exc:
        problems.append("%s does not load: %s" % (path, exc))
        return {}
    if not isinstance(loaded, dict):
        problems.append("%s is not a JSON object" % path)
        return {}
    return loaded


settings = load(settings_path, required=True)
local = load(local_path, required=False)

# Local settings override project ones, so a loosening hidden in the
# gitignored file counts. Both are checked; the effective value wins.
for path, loaded in ((settings_path, settings), (local_path, local)):
    if loaded.get("disableAllHooks"):
        problems.append("%s sets disableAllHooks — every hook is off, the guard included" % path)
    if loaded.get("autoMemoryEnabled", False):
        problems.append("%s enables auto memory — CLAUDE.md rule 3 keeps it off" % path)

permissions = settings.get("permissions", {})
if not isinstance(permissions, dict):
    permissions = {}
    problems.append("%s: permissions is not an object" % settings_path)
local_permissions = local.get("permissions", {})
if not isinstance(local_permissions, dict):
    local_permissions = {}


def effective(key):
    return local_permissions.get(key, permissions.get(key))


# The invariants D-011 commits to. A well-formed edit that empties the
# backstop or switches the mode passes JSON parsing, lints green, and
# leaves nothing behind — which is why they are asserted and not trusted.
mode = effective("defaultMode")
if mode in ("bypassPermissions", "dontAsk"):
    problems.append("defaultMode is %r — the guard's ask verdicts would never be seen" % mode)
if effective("disableBypassPermissionsMode") != "disable":
    problems.append("the bypassPermissions lock is gone (D-011)")
if not effective("deny"):
    problems.append("the deny backstop is empty — nothing binds when the hook is dead (D-011)")


def matches_bash(matcher):
    if matcher in (None, "", "*"):
        return True
    return "Bash" in [part.strip() for part in str(matcher).split("|")]


commands = [
    hook.get("command", "")
    for source in (settings, local)
    for group in source.get("hooks", {}).get("PreToolUse", [])
    if matches_bash(group.get("matcher"))
    for hook in group.get("hooks", [])
    if hook.get("type") == "command"
]

naming = [command for command in commands if guard in command]
if not commands:
    problems.append("no PreToolUse hook matching Bash is registered")
elif not naming:
    problems.append("no PreToolUse/Bash hook names %s" % guard)

for problem in problems:
    sys.stderr.write("check-guard: %s\n" % problem)

if problems:
    raise SystemExit(1)

sys.stdout.write(naming[0])
PY
)" || exit 1

# 2. The guard answers, on a machine that has it.
git_dir="$(cd "$(git rev-parse --git-dir)" && pwd -P)"
git_common_dir="$(cd "$(git rev-parse --git-common-dir)" && pwd -P)"

if ! git rev-parse --verify -q "$MARKER" >/dev/null 2>&1; then
    if [ -e "$GUARD" ]; then
        fail "$GUARD exists but $MARKER does not — the guard is unversioned and both gates are inert here; snapshot it (.claude/docs/guard-record.md)"
    fi
    echo "check-guard: no $MARKER here — the guard is absent by design on this machine"
    exit 0
fi

if [ ! -e "$GUARD" ] && [ "$git_dir" != "$git_common_dir" ]; then
    main_checkout="$(cd "$git_common_dir/.." && pwd -P)"
    printf 'check-guard: this is a linked worktree. The marker lives in the shared git\n' >&2
    printf 'directory so it is visible here, but %s is gitignored and was\n' "$GUARD" >&2
    printf 'never materialized — the tracked settings grant their allow list with no\n' >&2
    printf 'guard behind them, which is the widest state this repository has. Link it:\n' >&2
    printf '\n    mkdir -p %s && ln -s %s/%s %s\n\n' \
        "$(dirname "$GUARD")" "$main_checkout" "$GUARD" "$GUARD" >&2
    exit 1
fi

[ -e "$GUARD" ] || fail "$MARKER exists but $GUARD does not — restore it (.claude/docs/guard-record.md)"
[ -x "$GUARD" ] || fail "$GUARD lost its executable bit — Claude Code runs it by path"
"$GUARD" --liveness || fail "the guard is registered but not alive"

# The registered line, executed the way Claude Code executes it. This is
# what a substring test cannot do: it catches a mangled one-liner, a lost
# `exec`, a path that resolves somewhere else, and a registration that
# merely mentions the guard without running it.
verdict="$(printf '%s' '{"tool_name":"Bash","tool_input":{"command":"git push --force"}}' \
    | CLAUDE_PROJECT_DIR="$PWD" bash -c "$guard_command" 2>/dev/null || true)"
case "$verdict" in
    *permissionDecision*deny*) ;;
    *) fail "the registered hook command did not deny a force push — the boundary is not wired up" ;;
esac
