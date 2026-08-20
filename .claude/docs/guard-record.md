# The development guard — the record

**Read this before touching `.claude/settings.json`, `.pre-commit-config.yaml`'s
`check-guard` hook, `scripts/check-guard.sh`, or anything under
`.claude/hooks/`.** It is the durable half of `CLAUDE.md` rule 1's
quarantine: everything about the guard that a later session needs and
cannot get by reading the file, because reading the file is forbidden.

Written at step `001` (2026-08-20). Step `002` adds the platform probe
results — what the installed Claude Code version actually does with the
permission rules and the hook registered here. Until it does, the
[open questions](#what-002-must-still-measure) at the end are open.

## The quarantine, in one paragraph

`.claude/hooks/bash_guard.py` is prototype-generation tooling for *this
repository's own development*. It is not the product, and §3.1 of the
specification deliberately excludes the prototype's code and API shapes
as inputs to the product. So the file never enters an implementing
session's context: any task needing its contents — registry edits, later
maintenance — runs in an **isolated subagent** that reads and edits it
and reports outcomes only. Executing it is fine; its output is verdicts,
not code. It is **never tracked** (both guard paths are gitignored),
because this repository is the plugin's public install channel.

## Restore, and the backup ref

Versioning lives on **`refs/backups/bash-guard`**, outside `refs/heads/`
so no `push --all`, default refspec or clone carries it.

```sh
git show refs/backups/bash-guard:.claude/hooks/bash_guard.py > .claude/hooks/bash_guard.py
chmod +x .claude/hooks/bash_guard.py
```

Redirect it; never render the content into a session.

A new snapshot is chained on **inside the isolated channel**, at
instantiation and after every `--selftest`-green edit. It uses a
temporary index, never the repository's own:

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

Every command there prints hashes, never content.

**The backup remote: none is configured** (operator, 2026-08-20). Only
`origin` exists, and `origin` is **public** — the one thing that must
stay true is that this ref never goes there; `git push --mirror` is the
spelling that would carry it, and it is denied in both the guard and the
settings backstop. Until a private backup remote exists, rule 6's
step-close push attempt reports "the remote does not exist" and attempts
nothing. The ref is local-only in the meantime, and that is accepted: it
uniquely carries this project's registry work, while the pristine
template is recoverable from the operator.

At the close of `001` the ref carried five links: clean base → the frisk
registry → three in-channel gap fixes → docker removed → the cold
review's three holes closed
(`82336abee4f32fe2d019f9637d784deeb8dd688b`).

## The commands

All run from the repository root, invoked by path — the shebang resolves
`python3`, and the executable bit is load-bearing because Claude Code
runs the file directly.

| Command | Asks | Green looks like |
|---|---|---|
| `.claude/hooks/bash_guard.py --liveness` | is it structurally alive? | one line, `liveness: 18 gated tools, 81 rules and grants, 17 wrappers, ok`, exit 0 |
| `.claude/hooks/bash_guard.py --selftest` | is it right? | the liveness line, then `228/228 registry cases passed`, `174/174 engine cases passed`, `92/92 rules and grants covered`, exit 0 |
| `printf '{"tool_name":"Bash","tool_input":{"command":"git push --force"}}' \| .claude/hooks/bash_guard.py` | does a payload still come back as a verdict? | one line of JSON carrying `permissionDecision: deny` and a reason ending in a bracketed rule citation, exit 0 |

Failure shapes: liveness prints one `DEAD …` line per problem and ends
`BROKEN`, exit 1. The selftest prints `FAIL got X want Y '<command>'` for
a wrong verdict and `UNCOVERED no case reaches …` for a rule no case
exercises, exit 1. **A free command prints nothing and exits 0** —
silence hands the call back to the permission rules, which is why the
third command proves the guard answers at all but proves nothing about
whether Claude Code is actually calling it.

## Where the guard is gated, and why twice

A `PreToolUse` hook **fails open**: when it crashes, is missing, or has
lost its executable bit, Claude Code logs it and falls through to the
permission rules. Every one of those deaths is silent from inside a
session, so two gates ask the two different questions:

- **`just check` / the commit hook** → `scripts/check-guard.sh` (the
  `check-guard` local hook). Governance well-formedness everywhere plus
  liveness where the guard belongs. A lint, so no behaviour cases.
- **`just test`** → `--selftest`. Liveness, every case, then coverage.

Both are inert where the guard is absent, keyed on **the backup ref, not
the guard file** — a gate keyed on the file it guards goes inert exactly
when the file disappears, which is the silent death being hunted. The
ref exists on machines that instantiated the guard and is carried by no
clone. See `D-012`.

`check-guard.sh` does not pattern-match the registered hook: on a
guard-bearing machine it **executes the command line the settings
actually register**, with the payload of a force push, and requires a
`deny` back. A registration that merely mentions the right path — or one
whose one-liner was mangled, lost its `exec`, or resolves elsewhere —
fails there and nowhere else.

**Linked worktrees are the one state where the two facts come apart.**
Refs live in the shared git directory, so the marker is visible from a
worktree, while the gitignored guard is not materialized in it: tracked
settings granting the whole allow list, no guard behind them. Both gates
name that state loudly rather than skipping it, and print the fix:

```sh
mkdir -p .claude/hooks && ln -s <main-checkout>/.claude/hooks/bash_guard.py .claude/hooks/bash_guard.py
```

`.gitignore` puts isolated-subagent worktrees under `.claude/worktrees/`,
so this is reachable in ordinary work, not a curiosity.

The hook registration in `.claude/settings.json` is **self-guarding** for
the same reason: `[ -x "$g" ] && exec "$g" || exit 0`. `exec` means a
present guard's stdout and exit code pass through untouched; an absent
one exits 0 silently, so the committed settings file never references a
file that fails where it is absent (CI, fresh clones, anyone who clones
the public repository). Verified in all four combinations at `001`.

## What is gated, and what stays free

The registry says what *this project* runs. Reported out of the isolated
channel; the file itself is the authority.

**Rules** (safe-by-default tool, finite set of dangerous acts — any named
act gates the line, everything else falls through silent): `git`, `gh`,
`claude`, `rm`/`rmdir`/`shred`, `find`, and the boundary-file writers.
**Grants** (dangerous-by-default tool, small proven-safe set — closed
world, anything unproven asks): `pip`, `just`. **Handoff-only**:
`python` (so it cannot hide `pip`) and `sudo` (which also asks on its
own).

- **git.** The template's ground rules are byte-identical and were only
  added to: deny on a push carrying `--prune` or a `:`/`+` refspec, deny
  on `git add -N`/`--intent-to-add` (no authorised use here — rule 2),
  ask on `remote add`/`set-url`/`remove` and on a `fetch`/`clone` whose
  operand is a URL. **The ordinary push asks and is never denied** — the
  close ritual attempts one, and a denied pattern cannot be approved in
  the very exchange rule 9 relies on. The unrecoverable spellings are
  denied however written, `git -C dir push --force` and
  `sudo git push -f` included. **Any `-c` or `--config-env` asks**, keyed
  on the flag and not on the key: `git -c alias.p='!git push --force' p`,
  `-c core.pager=…`, `-c uploadpack.packObjectsHook=…` make git a command
  runner, and the exec-capable key set is open. `git update-ref --stdin`
  is denied — a `delete` line hides in a payload nothing on the line
  shows, and one of the refs it could delete is the backup ref both
  harness gates key on. The two-argument `update-ref` the snapshot recipe
  uses stays silent.
- **gh.** Reads free; every forge write asks. `gh api` asks whenever an
  explicit method flag is present — keying on presence is the only thing
  that catches `--method=POST`, at the cost of an explicit `GET` asking
  too.
- **pip.** Only `pip install -r requirements.txt` and the read
  subcommands are silent. **Any upgrade flag asks**, deliberately.
- **just.** Only this repository's six documented recipe spellings are
  silent; a new or unknown recipe asks. That is the registry-side
  expression of the justfile invariant that no recipe performs a gated
  act — the guard judges `just release`, never the push inside it.
- **Deletes** are judged by resolved operands, not by the verb: project
  artifacts by name are free, anything resolving outside the project
  asks, and an operand the guard cannot resolve (`"$HOME"`,
  `${TMPDIR}/x`) is treated as outside — the one direction that must not
  fail.
- **The boundary's own files** (`.claude/settings*`, `.claude/hooks/**`)
  ask — never deny, so the guard's own maintenance keeps an unlock path
  — when passed as an argument to `tee`, `cp`/`mv`/`ln`/`install`, `sed`,
  `truncate`, or `chmod`/`chattr`/`chown`/`chgrp`. The mode change is in
  that list because `chmod -x` on the guard *is* the disarm: the
  registration tests `[ -x … ]` and would exit 0 in silence on every
  later call.
- Unpinned fetches (`curl`, `wget`, `npm`/`npx`, `brew`, `apt`) and
  usage-spending `claude` invocations ask on every spelling.

## Blind spots — stated as consequences

- **Shell redirection into a file is invisible.** `echo '{}' >
  .claude/settings.json` is silent. The boundary-file rules only catch
  spellings that pass the path as an argument. What covers the rest is
  the `ask` tier on the *native* file tools in `.claude/settings.json`.
  Nothing **prevents** a shell redirection. What catches one after the
  fact is `check-guard.sh`, which asserts the invariants a loosening
  would have to break — an emptied `deny` list, a switched mode, a
  removed bypass lock, a hook that no longer answers — so the edit
  survives at most until the next `just check` or commit. Detective,
  not preventive, and named as such.
- **A delete whose targets come from a substitution or a pipe is
  silent** — `rm -rf $(cat list)`, `ls | xargs rm -rf`. Nothing on the
  line names the paths.
- **An unknown runner is silent.** `myrunner git push --force` names
  nothing recognised. The fix is adding the runner deliberately, never
  guessing — an earlier guessing pass gated `ls ../docker`.
- **Program text in another language is data**: `python3 -c`, `node -e`,
  a heredoc fed to a non-shell.
- **Rules test presence, never value.** Only grants constrain a value,
  and they yield ask rather than deny.
- **The guard cannot tell whether it is reached at all.** Only a live
  session can, which is `002`'s job.

## The settings pairing, and what a dead guard leaves open

The settings take their shape from the guard, not the reverse. The
pairing rules, and how `.claude/settings.json` answers them, are in
`D-011`. The honest summary:

**A broad allow plus a dead hook is a wider surface than a narrow allow
list ever was.** `Bash(git:*)`, `Bash(rm:*)`, `Bash(sed:*)` and their
kin exist so the guard can be the thing that judges; the moment it stops
running, they allow everything those tools can do. The `deny` backstop is
the answer exactly there — it binds without the hook — and it is
deliberately confined to acts that **cannot be undone**: force, mirror,
delete and prune pushes, `filter-branch`/`filter-repo`, `reflog expire`,
`update-ref -d` and `update-ref --stdin`.

Two limits on it, both measured, both accepted knowingly:

- **It covers canonical spellings only.** Prefix rules match from the
  start of the command line, so `git push origin main --force` — the
  commoner spelling from muscle memory — matches no entry at all, though
  the guard denies it. There is no fix for that inside prefix rules.
  That gap *is* this project's thesis, which is why the product exists.
- **It does not cover destructive deletes.** Their spellings are an open
  set a prefix rule cannot enumerate, and a couple of literal entries
  would buy false comfort rather than cover.

The gates above are the answer to both: they are what keep the hook —
which does not have either limit — alive.

## What `002` must still measure

Nothing below is assumed anywhere in this repository; each is a probe
`002` owes, with the pre-committed response if it comes back wrong.

1. **Does `Bash(git push --force:*)` actually match?** The colon-star
   form is what the guard's own pairing prescribes; the settings schema
   documents a `Bash(git *)` prefix form as well. If the backstop's
   spelling does not bind, the backstop is decoration — re-spell it.
2. **What does `acceptEdits` do with an unmatched Bash command?** The
   guard's silence is only as safe as that behaviour, and its `ask`
   verdicts may be the only gate left in a permissive mode.
3. **Does an explicit `ask` rule beat `acceptEdits` for `Edit`/`Write`?**
   If not, the boundary's own files are unprotected against a silent,
   well-formed settings edit and the tier must be `deny` with a named
   unlock path instead.
4. **Is `$CLAUDE_PROJECT_DIR` exported to `PreToolUse` hooks?** The
   registry's boundary rules resolve against it, falling back to the
   guard process's working directory — which under a hook is wherever
   Claude Code launches it. If the variable is absent *and* the working
   directory is not the project root, those rules resolve against the
   wrong tree.
5. **Is the hook reached at all, and does a refusal come back naming a
   rule?** If a denied command merely prompts, the hook is not reaching
   the tool call and only the backstop is live. This is the one failure
   no local command can detect.
6. **What does `auto` mode do here?** It stays reachable deliberately
   (`disableAutoMode` was not set) so `002` can A/B a classifier against
   the guard. `claude auto-mode` inspects its configuration, and
   `autoMode.classifyAllShell` suspends every Bash allow rule — the
   knob that makes the comparison meaningful.
