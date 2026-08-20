# The harness

**Read before changing `justfile`, `scripts/`, `.pre-commit-config.yaml`
or any linter config.**

Measured 2026-08-19 on `just` 1.45.0, `pre-commit` 4.4.0, Python 3.14.4
(system), git 2.53.0, Linux 6.18 (WSL2).

## Entry points

| Command | Runs |
|---|---|
| `just setup` | `scripts/setup.sh` — `./.venv`, `requirements.txt`, `pre-commit install` |
| `just check [all\|changed]` | `scripts/check.sh`, scope as argument |
| `just test` | `scripts/test.sh` |
| `just verify` | `check` then `test`; no script of its own |

`just` is a system tool, unpinned, so `just setup` has nothing before it.
Only `pre-commit` is pinned in `requirements.txt`; every linter is pinned
by `rev`. Pre-commit's transitive dependencies float.

## Invariants — each breaks silently

They were measured, not assumed. **Re-run 1–4 after touching
`scripts/check.sh` or the fixer hooks, 5–6 after touching
`scripts/check-guard.sh` or its hook.** When one breaks, the check keeps
passing and simply stops seeing things.

**1. `check` sees untracked files.** `pre-commit run --all-files`
enumerates from git and cannot see them, so `scripts/check.sh` passes the
list explicitly: `git ls-files --cached --others --exclude-standard`.
Keep `-z` and `core.quotePath=false` — without them git C-quotes
non-ASCII paths (`café.md` → `"caf\303\251.md"`), which then fail every
existence test and are dropped with no message. Enumeration failure is
caught explicitly by writing to a file and checking its status: a process
substitution's status is invisible to `set -euo pipefail`, and an unborn
`HEAD` would report "nothing to check", exit 0.

**2. `check` asserts, never repairs.** Fixer hooks
(`trailing-whitespace`, `end-of-file-fixer`, `mixed-line-ending`) may
write only in the commit hook. `check.sh` snapshots the file list to a
temp directory, compares afterwards, restores what was rewritten, names
it and fails. No git operation is involved.

**3. An interrupt mid-run restores the tree too.** The revert is a
function called from an `EXIT` trap; `INT`/`TERM`/`HUP` simply `exit`,
which runs it. Keep it idempotent — the main path calls it to report and
the trap then finds nothing to do. If a restore fails, the snapshot is
**kept** and its path printed. Straight-line revert code loses untracked
files' only copy on Ctrl-C.

**4. Broken symlinks reach `check-symlinks`.** The file-list filter drops
non-existent paths, which is right for deleted-but-indexed files and
wrong for broken symlinks. **Do not test `-f` alone** — that makes the
hook unreachable from `just check`.

**5. A `local` hook runs even when the file list excludes it.**
`check-guard` must run on every invocation, `just check changed`
included: the guard is gitignored so never appears in a file list, and a
settings file that stopped pointing at it is *unchanged* on the commit
where that matters. Requires `always_run: true` and
`pass_filenames: false` (confirmed on pre-commit 4.4.0).

**6. The guard gate fails on each silent death.** A `PreToolUse` hook
fails open, so each death is exercised rather than assumed. Verified at
`001` across twelve states plus a linked worktree. Exit 0: no marker and
no guard; marker with a working guard; matcher `*` or `Bash|Read`.
Exit 1, each naming its cause: guard with no marker; a hook that only
*mentions* the guard; emptied `deny`; removed bypass lock;
`disableAllHooks` in the gitignored local settings; a top-level JSON
array; `defaultMode: bypassPermissions`; a guard stripped of `+x`.

Portability: `scripts/check.sh` targets bash 3.2 (stock macOS) — no
`mapfile`, no associative arrays. One scoped suppression: `SC2329` on
`cleanup`, which shellcheck cannot see is invoked through a `trap`.

## Re-measure

```sh
# 1 — untracked file is seen
printf 'x=1\necho $x\n' > scripts/untracked_probe.sh   # SC2148
just check                        # must be 1, naming shellcheck
rm -f scripts/untracked_probe.sh

# 2 — fixer wants to rewrite, file survives byte-identical
printf '# probe   \n' > probe.md && md5sum probe.md
just check                        # must be 1, naming probe.md
md5sum probe.md                   # unchanged
rm -f probe.md

# 3 — interrupt restores
printf '# probe   \n' > int-probe.md && md5sum int-probe.md
setsid bash scripts/check.sh >/dev/null 2>&1 & pid=$!
sleep 1.2; kill -TERM -"$pid"; sleep 2
md5sum int-probe.md               # unchanged
rm -f int-probe.md

# 4 — broken symlink fails
ln -s ./does-not-exist.md broken-probe.md
just check                        # must be 1
rm -f broken-probe.md
```

**5.** A `local` hook with `always_run: true`, `pass_filenames: false`,
`entry: "bash -c 'echo PROBE-RAN args=$*; exit 3' --"`, run through
`.venv/bin/pre-commit run -c <config> --files README.md`: exit 1,
`PROBE-RAN` printed, `args=` empty.

**6.** `git init` a scratch repo outside this one; copy
`scripts/check-guard.sh` and a minimal `.claude/settings.json` in; stub
the guard as a script echoing a liveness line for `--liveness` and
`"permissionDecision": "deny"` when stdin mentions `--force`; mark it
with `git update-ref refs/backups/bash-guard HEAD`; walk the states
above, mutating settings between runs. Worktree case:
`git worktree add` a second checkout, run from inside it.

## Path exclusions

`.claude/spec-work/` and `.claude/refs/` are excluded in
`.pre-commit-config.yaml`, keyed on path not tracked status — one place,
so `scripts/check.sh` holds no policy. Gitignored paths are excluded for
free by `--others --exclude-standard`, which is also what keeps
`.claude/hooks/bash_guard.py` out of every file list (rule 1).

`check-added-large-files` needs `--enforce-all`: without it the hook
intersects its list with what is *staged*, so outside a commit it checks
nothing and always passes — inert exactly in `just check` and CI.
`detect-aws-credentials` was dropped at the operator's instruction;
broader scanning is a pinned hook away (`gitleaks`, `detect-secrets`).

## Check families

`.pre-commit-config.yaml`'s header comment carries the families and the
step each arrives at; the hooks below it name their tools and pins. Not
in that file: `scripts/check-guard.sh` is one hook carrying two families
— guard liveness and governance well-formedness — and gains frontmatter
parsing at `003`.
