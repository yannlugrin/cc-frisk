# The development guard — the record

**Read before touching `.claude/settings.json`, `scripts/check-guard.sh`,
its `check-guard` hook, or anything under `.claude/hooks/`** — and before
designing any probe of a permission mechanism (see [Method](#method)).

## Restore, and the backup ref

Restore by redirection; never render the content into a session.

```sh
git show refs/backups/bash-guard:.claude/hooks/bash_guard.py > .claude/hooks/bash_guard.py
chmod +x .claude/hooks/bash_guard.py
```

Snapshots are chained **inside the isolated channel**, at instantiation
and after every `--selftest`-green edit, using a temporary index:

```sh
blob=$(git hash-object -w .claude/hooks/bash_guard.py)
idx=$(mktemp -u)
GIT_INDEX_FILE="$idx" git update-index --add \
    --cacheinfo 100755,"$blob",.claude/hooks/bash_guard.py
tree=$(GIT_INDEX_FILE="$idx" git write-tree)
rm -f "$idx"
parent=$(git rev-parse -q --verify refs/backups/bash-guard || true)
if [ -n "$parent" ]; then
    commit=$(git commit-tree "$tree" -p "$parent" -m "bash_guard: <what changed>")
else
    commit=$(git commit-tree "$tree" -m "bash_guard: clean base")
fi
git update-ref refs/backups/bash-guard "$commit"
```

No backup remote exists, so rule 6's step-close push reports its absence
and attempts nothing; `origin` is public and this ref never goes there.

## The commands

From the repository root, invoked by path — the executable bit is
load-bearing, since Claude Code runs the file directly.

| Command | Green |
|---|---|
| `--liveness` | `liveness: 18 gated tools, 76 rules and grants, 17 wrappers, ok`, exit 0 |
| `--selftest` | that line, then `248/248 registry cases passed`, `174/174 engine cases passed`, `87/87 rules and grants covered`, exit 0 |
| a payload on stdin | one line of JSON; `deny` carries a reason ending in a bracketed rule citation |

Failures: `DEAD …` lines ending `BROKEN`; `FAIL got X want Y '<cmd>'`;
`UNCOVERED no case reaches …`. **A free command prints nothing, exit 0** —
silence hands the call to the permission rules.

## Two gates, because a hook fails open

A dead, missing or non-executable hook is skipped **silently**, falling
through to the permission rules. So: `just check` / the commit hook →
`scripts/check-guard.sh` (liveness plus governance well-formedness);
`just test` → `--selftest`. Both key on **the backup ref, not the guard
file** (`D-012`).

`check-guard.sh` **executes the command line the settings register**,
with a force-push payload, and requires `deny` back; a registration that
merely names the right path fails there and nowhere else.

**Linked worktrees** are where the two facts separate: the ref is visible
(shared git dir) but the gitignored guard is not materialized — tracked
settings, no guard. Both gates name that state and print the fix:

```sh
mkdir -p .claude/hooks && ln -s <main-checkout>/.claude/hooks/bash_guard.py .claude/hooks/bash_guard.py
```

The registration is **self-guarding** — `[ -x "$g" ] && exec "$g" || exit 0`
— so the committed settings never reference a file that fails where it is
absent (CI, fresh clones). Verified in all four combinations at `001`.

## What is gated

**The guard file is the authority and `--selftest` enforces it.** Only
the non-obvious rulings are written down here:

- **Shape.** Rules (safe-by-default tool, named dangerous acts gate the
  line): `git`, `gh`, `claude`, `rm`/`rmdir`/`shred`, `find`, `just`,
  boundary-file writers. Grants (closed world, anything unproven asks):
  `pip`. Handoff-only: `python`, `sudo`.
- **The ordinary push asks and is never denied** — the close ritual
  attempts one, and a denied pattern cannot be approved in the exchange
  rule 9 relies on. Unrecoverable spellings deny however written.
- **Any `git -c`/`--config-env` asks** — the exec-capable key set is
  open. `git update-ref --stdin` denies (a `delete` line hides in the
  payload); the two-argument form the snapshot recipe uses is silent.
- **`just` is a rule, not a grant** (`D-013`): any recipe, arguments and
  redirection are silent, resting on rule 2's invariant that no recipe
  performs a gated act. What asks is a flag breaking the "our justfile"
  premise (`-f`, `-d`, `--shell*`, `--chooser`, `--choose`, `--init`,
  `--fmt`). Residue: a clustered short with attached value
  (`just -fOther/Justfile`) stays silent.
- **Deletes are judged by resolved operand**, not the verb: project
  artifacts free, anything outside asks, an unresolvable operand
  (`"$HOME"`, `${TMPDIR}/x`) treated as outside.
- **Boundary files** (`.claude/settings*`, `.claude/hooks/**`) ask —
  never deny, so maintenance keeps an unlock path — when passed as an
  argument to `tee`, `cp`/`mv`/`ln`/`install`, `sed`, `truncate`, or
  `chmod`/`chattr`/`chown`/`chgrp`. `chmod -x` on the guard *is* the
  disarm.
- Unpinned fetches (`curl`, `wget`, `npm`/`npx`, `brew`, `apt`) and
  usage-spending `claude` invocations ask on every spelling.

## Blind spots

- **Redirection is invisible to the guard**: the boundary rules match a
  path passed as an **argument**, and a `>` target is not one. It still
  prompts, but only via the platform's `.claude/` gating (P12) — the
  `ask` tier does not reach redirections at all. Treat that as a
  courtesy, not a control; `check-guard.sh` is the only redirection
  backstop we own.
- **Deletes from a substitution or pipe** — `rm -rf $(cat list)`,
  `ls | xargs rm -rf`. Nothing on the line names the paths.
- **An unknown runner is silent** — `myrunner git push --force`. Fix by
  adding runners deliberately, never guessing.
- **Program text in another language is data**: `python3 -c`, `node -e`,
  a heredoc fed to a non-shell.
- **Rules test presence, never value.** Only grants constrain a value.
- **A redirection defeats a grant, never a rule.** `pip install -r
  requirements.txt 2>&1` → `ask`. Fails closed, so friction not hole;
  **not being fixed** (`D-013`).

## The settings pairing

Shape, rationale and the backstop's two accepted limits are in `D-011`.
What belongs here: the gates above are what keep the hook — which has
neither limit — alive.

## The platform probes (`002`)

Measured on **Claude Code `2.1.237`, Linux (WSL2), 2026-08-20**, in a
session whose mode was read back from the transcript, not assumed.
Re-run after a Claude Code update: every property here fails silently.

### Method

**"It ran" is not a measurement.** A prompted-and-*approved* call returns
exactly what an ungated one returns. The session `.jsonl` records
`permissionMode` and no permission *decisions*, so an ambiguous probe
can only be re-run. Use either **the refusal protocol** (the operator
refuses every prompt for the duration, so success means no prompt — say
explicitly when it ends) or **a self-identifying message** (the guard's
bracketed rule citation; a settings deny's `Permission to use Bash with
command … has been denied`). **Change one variable per probe**, and never
probe a rule with a `.claude/` path — P12 masks whatever is under test.
Two of this campaign's findings were wrong on these two points.

| # | Question | Answer |
|---|---|---|
| P1 | Is the hook reached? | **Yes** — `git push origin main --force --dry-run`, a spelling no `deny` matches, came back in the guard's own words |
| P2 | Does a hook `ask` prompt? | **Yes.** Rule 6's close push rests on it |
| P3 | Does `Bash(git push --force:*)` bind? | **Yes**, as does `Bash(cmd *)` |
| P4 | Do `deny` prefixes match mid-line? | **No, only from the start.** So `git push origin main --force` matches nothing and only the guard catches it — the project's thesis, measured |
| P5 | Does the guard emit `allow`? | **No.** Only `deny`/`ask`; a grant is silence |
| P6 | `acceptEdits` + unmatched command? | **Prompts** when it has a side effect. Trivially read-only ones run (built-in carve-out). `D-011`'s `python3` cost is real |
| P7 | Does `ask` beat `acceptEdits`? | **Yes** (measured outside `.claude/`) |
| P8 | Does `Edit(…)` match `Write`? | **Yes**; `Write(…)` matches nothing |
| P9 | `$CLAUDE_PROJECT_DIR` in hooks? | **Exported**, = project root, as is the hook's `PWD` |
| P10 | `autoMemoryEnabled` honoured? | **Recognised** in the binary, no artifact anywhere. Presence+absence, not a behavioural test |
| P11 | Does `settings.local.json` need a restart? | **No.** Still restart before concluding a mechanism is *dead* |
| P12 | Are `.claude/` writes gated? | **Yes, by the platform**, via file tools and `>` alike; an explicit `allow` does **not** suppress it. **No setting removes the prompt on a working-memory edit** |

`auto` mode: `classifyAllShell` unset, so the allow list stood. The
classifier A/B `D-011` reserved `auto` for is **not** run here.

### Re-measure

```sh
git push origin main --force --dry-run   # P1: guard text + [rule …]
basename --colonstar /a/b/c              # P3: "Permission to use Bash…"
basename /a/b --colonstar                # P4: silent
printf '{"tool_name":"Bash","tool_input":{"command":"pip list"}}' \
    | .claude/hooks/bash_guard.py | wc -c    # P5: 0
python3 -c 'open("/tmp/p","w").write("x")'   # P6: must prompt (protocol)
```

P7/P8/P12 need `.claude/settings.local.json` with `ask: Edit(probe-ask/**)`
and `allow: Edit(.claude/docs/**)`; then under the protocol `Write` to
`probe-noask/x.txt` (silent), `probe-ask/x.txt` (prompt),
`.claude/docs/x.txt` (prompt, despite the allow), and
`echo probe > probe-ask/y.txt` (silent — rules miss redirections).
Delete the harness and every probe target afterwards.

## The liveness triple — for the `003` rituals

Three **live tool calls**, never piped to the guard by hand and **never
run with `!`** — that executes in the operator's shell, with no hook and
no permission check, so all three pass and prove nothing. The payload
above asks whether the file is correct; these ask whether anything calls
it.

| # | Command | Must do |
|---|---|---|
| 1 | `git status --short` | run, no prompt |
| 2 | `git push --dry-run origin main` | **prompt** — `pushing is an outward write [rule git push]` |
| 3 | `git push origin main --force --dry-run` | **refuse** — `… published state is never rewritten [rule git push: --force]` |

Answer 2 either way; both are dry runs. **Three carries the weight**: no
`deny` matches that spelling (P4), so a refusal can only be the hook. If
it merely prompts, the hook is not reached and only the backstop is left
— while `--selftest` and `--liveness` would still pass. If it runs, both
are gone. It is silent/ask/deny, not the silent/grant/deny `PLAN.md`
sketched: there is no observable grant (P5).
