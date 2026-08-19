# The harness — measured behaviour

**Read this before changing `justfile`, `scripts/`, `.pre-commit-config.yaml`
or any linter config.** It records what the harness's mechanisms were
*observed* to do, not what they are assumed to do. Standing instructions
carry no staleness discipline, which is why these values live here and
not in `CLAUDE.md`.

Measured 2026-08-19 on: `just` 1.45.0, `pre-commit` 4.4.0, Python 3.14.4
(system interpreter; the engine's floor interpreter arrives at step
`006`), git 2.53.0, Linux 6.18 (WSL2).

## Entry points

| Command | Runs |
|---|---|
| `just setup` | `scripts/setup.sh` — creates `./.venv`, installs `requirements.txt`, runs `pre-commit install` |
| `just check [all\|changed]` | `scripts/check.sh` — one entry point, scope as argument |
| `just test` | `scripts/test.sh` |
| `just verify` | `check` then `test`; no script of its own |

`just` is a system tool, not pinned in `requirements.txt`, so `just setup`
is the entry point with nothing before it. Every linter is a pre-commit
hook pinned by `rev`; only `pre-commit` itself is pinned in
`requirements.txt`.

## Two probes that decide the design

Both were run at step `000`. Both must be re-run after any change to
`scripts/check.sh` or to the fixer hooks, because both properties are
silent when they break: the check keeps passing and simply stops seeing
things.

### 1. `check` sees untracked files

**Why it matters.** `pre-commit run --all-files` enumerates from git and
therefore cannot see a file that exists but was never added to the index.
A lint error in such a file must still fail. `scripts/check.sh` passes the
file list explicitly (`git ls-files --cached --others --exclude-standard`)
for exactly this reason.

**Measured.** An untracked `scripts/*.sh` with a shellcheck error (no
shebang, SC2148) failed `just check` with exit code 1. Confirmed.

**Re-measure.**

```sh
printf 'x=1\necho $x\n' > scripts/untracked_probe.sh
git status --porcelain scripts/untracked_probe.sh   # must show '??'
just check; echo "exit: $?"                          # must be 1, naming shellcheck
rm -f scripts/untracked_probe.sh
```

**Never** `git add --intent-to-add` as a way to make git aware of such a
file: it writes to the index as a side effect of a check, turns the
untracked `??` line into an added `A` one in `git status --porcelain` —
the output the handover and approve rituals read for their clean-tree
preconditions — and lets the next `git commit -a` sweep the file into an
unrelated commit.

### 2. `check` asserts and never repairs

**Why it matters.** Some hooks are fixers (`trailing-whitespace`,
`end-of-file-fixer`, `mixed-line-ending`). The commit hook is where they
are allowed to write. A `check` that rewrites the working tree as a side
effect is the `--intent-to-add` prohibition one step milder, and the
rituals that read `git status --porcelain` for a clean tree sit
downstream of it.

**Mechanism.** `scripts/check.sh` copies the file list to a temporary
directory before running pre-commit, then compares each file afterwards,
restores any the hooks rewrote, names them, and fails. No git operation is
involved — nothing touches the index, the working tree's git state, or
history.

**Measured.** A file with trailing whitespace made `just check` exit 1
while leaving the file byte-identical, printing "a fixer hook wanted to
rewrite these files". Confirmed.

**Re-measure.**

```sh
printf '# probe   \n' > probe.md
md5sum probe.md
just check; echo "exit: $?"    # must be 1, naming probe.md as wanted-rewritten
md5sum probe.md                # must be unchanged
rm -f probe.md
```

## Path exclusions

`.claude/spec-work/` and `.claude/refs/` are excluded in
`.pre-commit-config.yaml`, keyed on the path and not on tracked status —
one place, so `scripts/check.sh` holds no policy. `spec-work/` because
rule 1 makes it no session's reading material; `refs/` because it is the
operator's supplied material, read-only under rule 3 and owned elsewhere,
so a finding inside one would have no legal resolution.

Gitignored paths are excluded for free: `git ls-files --others
--exclude-standard` never lists them, which is also what keeps
`.claude/hooks/bash_guard.py` out of every check file list (rule 1).

## Check families present, and what is still owed

Families arrive with the first artifact of their class, never ahead of it,
so a green gate never says anything about files that are not there.

| Family | Since | Tool |
|---|---|---|
| Whitespace / newline | `000` | pre-commit-hooks (fixers) |
| Hygiene, secrets | `000` | pre-commit-hooks (`detect-private-key`, `detect-aws-credentials`, large files, merge conflicts, symlinks, case conflicts) |
| JSON parse | `000` | `check-json` |
| YAML | `000` | `check-yaml`, yamllint `--strict` |
| POSIX shell | `000` | shellcheck-py (ships its own pinned binary — not a system prerequisite) |
| Markdown / prose | `000` | pymarkdown |
| Guard liveness | `001` | `bash_guard.py --liveness`, machine-local, inert where absent |
| Governance frontmatter | `003` | a few-line custom check (rule 11 sanctions it; no ecosystem tool parses skill frontmatter) |
| Python, TOML | `006` | pinned to the interpreter floor that step commits to |

`SPECIFICATIONS.md` passes pymarkdown unmodified, so **no lint bend was
needed for it** — the escape rule 2 reserves for the read-only
specification stays unused. If a future rule does flag it, the bend is
scoped to that file alone and is a logged decision, never a quiet config
line or a global loosening.
