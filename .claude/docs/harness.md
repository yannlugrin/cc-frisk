# The harness

**Read before changing `justfile`, `scripts/`, `.pre-commit-config.yaml`,
`.github/workflows/` or any linter config.**

Measured 2026-08-19 on `just` 1.45.0, `pre-commit` 4.4.0, Python 3.14.4
(system), git 2.53.0, Linux 6.18 (WSL2).

## Entry points

| Command | Runs |
|---|---|
| `just setup` | `scripts/setup.sh` — `./.venv`, `requirements.txt`, an editable install of this repository, `pre-commit install` |
| `just check [all\|changed]` | `scripts/check.sh`, scope as argument |
| `just test` | `scripts/test.sh`; `PYTHON=… just test` picks the interpreter |
| `just verify` | `check` then `test`; no script of its own |

`just` is a system tool, unpinned, so `just setup` has nothing before it.
`requirements.txt` pins `pre-commit`, `PyYAML` and `setuptools`; every
linter is pinned by `rev`. Pre-commit's transitive dependencies float.

The editable install (`pip install --no-build-isolation -e .`) is why
`setuptools` is pinned there: it is the build backend `pyproject.toml`
names, and with build isolation on, pip would fetch an unpinned copy on
every setup. It gives `.venv/bin/frisk`, the console script of §8.2's
repository-installable door — installed at every setup so that the door
is exercised rather than asserted. The *engine* still has zero
dependencies; `tests/test_packaging.py` fails if an import escapes the
standard library.

## Invariants — each breaks silently

They were measured, not assumed. **Re-run 1–5 after touching
`scripts/check.sh` or the fixer hooks, 5–6 after touching either local
hook (`scripts/check-guard.sh`, `scripts/check_frontmatter.py`) or its
registration.** When one breaks, the check keeps
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

**5. A `local` hook runs even when the file list excludes it — and
even when the list is empty.** Both local hooks must run on every
invocation, `just check changed` on a clean tree included: the guard is
gitignored so never appears in a file list, a settings file that stopped
pointing at it is *unchanged* on the commit where that matters, and a
skill directory with no `SKILL.md` is an absence no list contains.
Requires `always_run: true` and `pass_filenames: false` (confirmed on
pre-commit 4.4.0) **and** that `scripts/check.sh` still invokes
pre-commit when its file list comes out empty.

*Corrected at `003`.* This invariant was recorded as measured at `001`
and was false at the boundary that mattered. The probe below ran
`pre-commit` directly with `--files README.md`, so it measured
pre-commit and never exercised `scripts/check.sh`, which returned early
with "nothing to check" before pre-commit was reached. `just check
changed` on a clean tree therefore ran **no hooks at all** and reported
green, asserting nothing about the permission boundary. `scripts/check.sh`
now runs `"$PRE_COMMIT" run --files` — an explicitly empty list, which
skips every file-scoped hook and fires the always_run pair. `--files
/dev/null` does not work: `destroyed-symlinks` asks git about a path
outside the repository and crashes. **The lesson generalises: a probe
that bypasses the entry point measures the tool, not the harness.**

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

**5.** Two halves, and the second is the one that was missed.
*Pre-commit's behaviour:* a `local` hook with `always_run: true`,
`pass_filenames: false`, `entry: "bash -c 'echo PROBE-RAN args=$*; exit
3' --"`, run through `.venv/bin/pre-commit run -c <config> --files
README.md`: exit 1, `PROBE-RAN` printed, `args=` empty. *The harness's
behaviour — through the entry point, never around it:* on a **clean
tree**, `just check changed` must print the always_run gates as
`Passed`, not `nothing to check`. Sabotage `.claude/settings.json`
(empty the `deny` list), commit it, run `just check changed`: it must go
red. Restore afterwards.

**6.** `git init` a scratch repo outside this one; copy
`scripts/check-guard.sh` and a minimal `.claude/settings.json` in; stub
the guard as a script echoing a liveness line for `--liveness` and
`"permissionDecision": "deny"` when stdin mentions `--force`; mark it
with `git update-ref refs/backups/bash-guard HEAD`; walk the states
above, mutating settings between runs. Worktree case:
`git worktree add` a second checkout, run from inside it.

## On the forge

`.github/workflows/ci.yml` (step `005`) runs the same entry points as
two jobs, plus the `floor` job added at `006` — `just test` on a bare
3.9 with no `just setup`, no venv and no caches, which is possible only
because the engine has no dependencies and the suite needs nothing
installed. Three facts about it are the harness's business:

**Bumping a tool locally without bumping the workflow is the drift the
pins exist to prevent.** `rust-just==1.45.0` tracks *this workstation*,
not the newest release (1.58.0 at `005`); `python-version: "3.14"`
tracks its interpreter. The three `actions/*` uses are pinned by commit
SHA with the release in a trailing comment, and
`.github/dependabot.yml` — not a session — is what bumps them (`D-027`).
By hand, if one is ever needed before the bot gets to it:
`gh api repos/<owner>/<repo>/git/ref/tags/<tag>`, following an
annotated-tag object through `git/tags/<sha>` to its commit.

**The clone probe is the local proxy for a runner**, and the only proof
of a from-nothing setup there is. With no scheduled run, a cold `just
setup` happens on a dependency edit or after GitHub evicts a cache
unused for seven days — so through a busy week in which neither cache
key changes, a setup that no longer works from nothing stays hidden.
Run the probe when that matters; a clone receives no backup ref, no
guard, and nothing gitignored.

```sh
git clone -q . /path/to/scratch/ci-probe   # scratch, outside this repo
cd /path/to/scratch/ci-probe && just setup && just verify
```

Measured green at `005`: `check` reports the boundary intact with no
guard present — invariant 6's exit-0 row, and note that only
`check-guard.sh`'s *second* question is skipped there, the governance
half runs on every machine — and `test` skips the guard's selftest.

## Path exclusions

`.claude/refs/` is excluded in `.pre-commit-config.yaml`, keyed on path
not tracked status — one place, so `scripts/check.sh` holds no policy.
Gitignored paths are excluded for free by `--others --exclude-standard`,
which is what keeps `.claude/hooks/bash_guard.py` out of every file list
(rule 1) and, since `005`, `.claude/spec-work/` and
`.claude/refs/infra-conventions/` too — both left the repository at
`D-025`/`D-026` and are ignored rather than excluded. The exclusion that
remains covers `behavior-corpus.md`, which is still tracked.

`check-added-large-files` needs `--enforce-all`: without it the hook
intersects its list with what is *staged*, so outside a commit it checks
nothing and always passes — inert exactly in `just check` and CI.
`detect-aws-credentials` was dropped at the operator's instruction;
broader scanning is a pinned hook away (`gitleaks`, `detect-secrets`).

## Check families

`.pre-commit-config.yaml`'s header comment carries the families and the
step each arrives at; the hooks below it name their tools and pins.

### The Python family and the interpreter floor (`006`)

ruff (`v0.16.4`: `ruff-check`, and `ruff-format` with `--check` so it
asserts instead of writing) and mypy (`mirrors-mypy v2.3.1`, `strict`,
`pass_filenames: false`), both configured in `pyproject.toml`, plus
`check-toml`. Three things about them are not obvious from the config:

**The floor is checked in four places and they must move together.**
`requires-python`, `[tool.ruff] target-version`, `[tool.mypy]
python_version`, and `.github/workflows/ci.yml`'s `floor` job. mypy is
the one that catches a standard-library name that arrived after 3.9 —
`tomllib`, `str.removeprefix` — on a workstation running 3.14. The
table of what each platform ships, its date and its sources are in
`docs/verification-record.md`, not here: it is operator-facing, and a
second copy would age out of sight.

**Static targeting is not execution, and one gap is known.**
`ruff-format` emits parenthesized context managers at `target-version =
"py39"` — official 3.10 grammar that 3.9's parser accepts in practice.
The formatter is therefore trusted about the floor only as far as the
`floor` CI job confirms; if that job ever fails on syntax the formatter
produced, the fix is `target-version = "py38"` for the formatter, not a
hand-formatted file. The suite's own
`ast.parse(..., feature_version=(3, 9))` catches the loud classes
(a `match` statement above all) on any interpreter, and does not catch
this one.

**mypy sees `src/` and `tests/`, never `scripts/`.** The harness
scripts have no callers, so there is no type error there to have. If a
script ever grows an importable module, that changes.

The workflow family (`005`) is schema validation, not a workflow linter:
`check-github-workflows` and `check-dependabot` from `check-jsonschema`,
pinned by `rev` like
every other third-party hook, pure Python against a vendored SchemaStore
copy with no network at run time. `actionlint` is the tool that would
say more, and it was rejected here because its pre-commit hook builds
from Go or runs in Docker — a new system prerequisite for `just setup`,
on a workstation and on a runner both (`D-027`). Measured at `005`: a
workflow whose `steps:` key is spelled `step:` is valid YAML, passes
yamllint, and fails this hook naming the job — which is the class it
exists for, since GitHub answers a malformed workflow by declining to
run it rather than by failing. `check-dependabot` answers the same
question for the bot's own config: `github-action` for `github-actions`
fails the hook, and would otherwise show up only as updates that never
arrive.

Two of them are local scripts rather than pinned third-party hooks, both
`always_run` with `pass_filenames: false`, because what each hunts is
invisible to a changed-file list. `scripts/check-guard.sh` asks whether
the permission boundary is intact — the settings files' invariants, and
one executed verdict from the command line they register.
`scripts/check_frontmatter.py` asks whether every skill and agent
definition still loads: frontmatter parses, and `name` agrees with the
path the loader finds it at (`D-018` — a separate script and hook, not a
third family bolted onto `check-guard.sh`; it imports PyYAML from
`.venv`, pinned in `requirements.txt`, where `check-guard.sh` is
stdlib-only).

### What `claude plugin validate` covers, and what it misses

Measured on **Claude Code 2.1.238**, 2026-08-21 — the table re-measured
in full at step `004`, every row from its own fixture. Exit codes are
captured without a pipe (a pipeline reports the *last* command's status,
which is how the 2.1.237 reading in `D-021` went partly wrong). One
fixture tree per class, each `<root>/skills/<name>/SKILL.md`, run as
`claude plugin validate --strict <root>`:

| Failure class                                  | validator | our script |
| ---------------------------------------------- | --------- | ---------- |
| No frontmatter block                            | 1 (warn)  | caught     |
| Unparseable YAML — bad indentation              | 1 (error) | caught     |
| Unparseable YAML — colon inside a plain scalar  | **0**     | caught     |
| Malformation swallows the closing `---`         | **0**     | caught     |
| `name` disagrees with the path it loads from    | **0**     | caught     |
| Skill directory with no `SKILL.md`              | **0**     | uncovered  |
| Close fence is `----` or `--- x`                | **0**     | caught     |
| `description` key absent                        | 1 (warn)  | caught     |
| `description:` present but null                 | **0**     | caught     |
| `description` present but not a string           | 1 (warn)  | caught     |

The six zeros are silent: the validator prints `Validation passed` and,
for the swallowed-delimiter case, never lists the file at all — the flow
scalar consumes the delimiter, so nothing recognises the block as
frontmatter. That is the whole argument for `D-021`'s "both exist": what
the ecosystem tool misses is exactly what this family exists to catch.

Two rows split under measurement, and both splits were found by tools
this repository already had. **Unparseable YAML** is two rows: the
validator catches an indentation error and misses `name: case: colon`,
which PyYAML rejects and it accepts — the single row `D-021` and `D-023`
argued over was measured on the catching half only. **`description`** is
three: an absent key and a non-string both fail `--strict`, while
`description:` with nothing after it passes *both* tools until step
`004` fixed ours, because `str(None).strip()` is truthy. That is the
likeliest way to reach an empty description and it was the last one
either tool saw.

A CRLF definition is not a class: `Path.read_text` does universal-newline
translation, so `\r\n` never reaches either the fence match or the parser.

Two traps when re-measuring — a tree holding **no** valid component falls
back to *manifest* validation and fails on a missing manifest, which
reads as a catch and is not one; and `--strict` is what turns the warning
classes into failures.

Re-measure — one tree per class, each carrying a valid sibling so the
manifest fallback cannot fire. `mktemp -d` rather than a variable you
must remember to set: an unset `$S` in an `rm -rf "$S/t"` is an unscoped
delete outside the project, which is rule 9's gated side. Run as written;
the expectations are the table's:

```sh
S=$(mktemp -d) || exit 1
mk() {   # $1 class, $2 the case skill's body — empty means omit the file
  rm -rf "$S/t"; mkdir -p "$S/t/skills/good" "$S/t/skills/case"
  printf -- '---\nname: good\ndescription: valid\n---\nbody\n' > "$S/t/skills/good/SKILL.md"
  [ -n "$2" ] && printf -- "$2" > "$S/t/skills/case/SKILL.md"
  claude plugin validate --strict "$S/t" >/dev/null 2>&1; echo "$1 rc=$?"
}
mk no-frontmatter  '<body only>\n'                                          # rc=1
mk unparseable     '---\nname: case\n  stray: 1\ndescription: x\n---\nb\n'  # rc=1
mk unparseable-2   '---\nname: case: colon\ndescription: x\n---\nb\n'        # rc=0
mk swallowed       '---\nname: case\ndescription: [x\n---\nb\n'              # rc=0
mk name-mismatch   '---\nname: other\ndescription: x\n---\nb\n'              # rc=0
mk no-skill-md     ''                                                       # rc=0
mk desc-absent     '---\nname: case\n---\nb\n'                               # rc=1
mk desc-null       '---\nname: case\ndescription:\n---\nb\n'                 # rc=0
mk desc-not-string '---\nname: case\ndescription: [a, b]\n---\nb\n'          # rc=1
mk bad-fence       '---\nname: case\ndescription: x\n----\nb\n'                # rc=0
claude --version                                                            # stamp the reading
rm -rf "$S"
```

For the right-hand column, our script fixes `ROOT` to the repository
(`D-022` removed its root argument), so the fixture tree must imitate one:
the same bodies under `$S/u/.claude/skills/case/SKILL.md`, the script
copied to `$S/u/scripts/`, and **a valid sibling in each of
`.claude/skills/` and `.claude/agents/`** — without them the empty-glob
arm fires and every row reads as caught for the wrong reason, including
`no-skill-md`, which is the one row it genuinely does not see.

A version that starts failing this retires part of the check — the
`021` revisit in `D-021` is where that is decided, on a fresh reading.
