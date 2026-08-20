# The development guard — the record

**Read this before touching `.claude/settings.json`, `.pre-commit-config.yaml`'s
`check-guard` hook, `scripts/check-guard.sh`, or anything under
`.claude/hooks/`.** It is the durable half of `CLAUDE.md` rule 1's
quarantine: everything about the guard that a later session needs and
cannot get by reading the file, because reading the file is forbidden.

Written at step `001` (2026-08-20). Step `002` added
[the platform probes](#the-platform-probes-002) — what the installed
Claude Code version actually does with the permission rules and the hook
registered here — and
[the liveness triple](#the-liveness-triple--for-the-003-session-rituals)
the session rituals run. Nothing here is an assumption carried over from
the bootstrap instructions or from `CLAUDE.md`.

**Before designing a probe of your own, read that section's method
note.** A tool call that was prompted and approved is indistinguishable
from one that was never gated, and the mistake reports a live gate as
dead.

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
(`82336abee4f32fe2d019f9637d784deeb8dd688b`). `just` became a rule after
that close, in the same channel
(`44be6c4a8a2bf1708b3bdf03bac341a79be5c39d`).

## The commands

All run from the repository root, invoked by path — the shebang resolves
`python3`, and the executable bit is load-bearing because Claude Code
runs the file directly.

| Command | Asks | Green looks like |
|---|---|---|
| `.claude/hooks/bash_guard.py --liveness` | is it structurally alive? | one line, `liveness: 18 gated tools, 76 rules and grants, 17 wrappers, ok`, exit 0 |
| `.claude/hooks/bash_guard.py --selftest` | is it right? | the liveness line, then `248/248 registry cases passed`, `174/174 engine cases passed`, `87/87 rules and grants covered`, exit 0 |
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
`claude`, `rm`/`rmdir`/`shred`, `find`, `just`, and the boundary-file
writers.
**Grants** (dangerous-by-default tool, small proven-safe set — closed
world, anything unproven asks): `pip`. **Handoff-only**:
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
- **just.** Silent by default — any recipe, any arguments, any
  redirection, whatever the spelling, including a recipe added after the
  registry was written. The justfile is ours, tracked and reviewed, and
  carries the invariant that no recipe performs a gated act; the guard
  judges `just release`, never the push inside it. **What asks is a flag
  that breaks the "our justfile, our project" premise**: `-f`/
  `--justfile`, `-d`/`--working-directory`, `--shell`, `--shell-arg`,
  `--clear-shell-args`, `--chooser`, `--choose`, `--init`, `--fmt` —
  another justfile, another directory, another interpreter, or a just
  that writes one. Keyed on the flag's presence, never its value, in
  both the `--flag value` and `--flag=value` spellings; it asks, never
  denies. It was a grant until 2026-08-20 and the operator ruled it out:
  the closed world charged a prompt for ordinary work — a redirection
  was enough — against no matching risk. One residue: a clustered short
  with an attached value (`just -fOther/Justfile`) is a single unknown
  token to the parser and stays **silent**. Nobody writes it here, and
  closing it would need parser work on scaffolding retired at `027`.
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

- **Shell redirection into a file is invisible *to the guard*.** `echo
  '{}' > .claude/settings.json` gets no verdict: the boundary-file rules
  only catch a path passed as an **argument**, and a `>` target is not
  one. It still prompts — but by the platform's `.claude/` gating, not by
  anything here, and the `ask` tier does not reach redirections at all
  ([the probes](#the-platform-probes-002), P12). `001` claimed nothing
  *prevents* a redirection; that was reasoned, and the truth is narrower
  than either the claim or its first correction. Treat the gating as a
  courtesy, not a control. `check-guard.sh` is the only redirection
  backstop we own, and it also catches an edit that was **approved** or
  made with no session watching: it asserts the invariants a loosening
  would have to break — an emptied `deny` list, a switched mode, a
  removed bypass lock, a hook that no longer answers — so such an edit
  survives at most until the next `just check` or commit.
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
- **A redirection defeats a grant, never a rule.**
  `pip install -r requirements.txt 2>&1` comes back **ask**: the
  redirection token is counted as an argument, so the closed-world grant
  sees a shape it cannot prove. Rules are untouched — `git push --force
  2>/dev/null` still denies, `rm -rf ~/x 2>&1` still asks — because they
  test for a named act's presence, not for a whole shape. It fails
  closed, so this is friction, not a hole. **`just` used to be the
  painful case and no longer is**: it became a rule on 2026-08-20, so
  `just check changed 2>&1 | tail -20` is silent. `pip` keeps the flaw;
  avoid the spelling there. Measured 2026-08-20 against the ref's tip
  `44be6c4`, by feeding each spelling to the guard in the payload shape
  of the third command above and reading back
  `.hookSpecificOutput.permissionDecision`. **It is not being fixed, and
  `002` does not revisit it** (operator, 2026-08-20): the guard is
  scaffolding retired at `027`, so parser work on it is effort spent on
  the very thing frisk replaces — and §4.3 already requires the product
  to parse redirections off the command line and to treat a pure
  fd-duplication like `2>&1` as no obstacle to an allow.
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

## The platform probes (`002`)

Measured on **Claude Code `2.1.237`, Linux (WSL2), 2026-08-20**, in a
session whose mode was read back from the transcript rather than assumed
(`grep -ao '"permissionMode":"[a-zA-Z]*"' ~/.claude/projects/<slug>/<id>.jsonl | tail -1`).
Re-run after a Claude Code update: every property here fails silently.

**Method — "it ran" is not a measurement.** A tool call that was prompted
and *approved* returns exactly what an ungated one returns: plain
success. The session `.jsonl` records `permissionMode` and no permission
*decisions*, so an ambiguous probe cannot be reinterpreted later, only
re-run. Two of this campaign's findings were wrong this way. So either

- **the refusal protocol** — the operator agrees to refuse every prompt
  for the duration, making success mean "no prompt appeared"; say
  explicitly when it ends, or the next real command gets refused too; or
- **a self-identifying message** — the guard's refusals carry a bracketed
  rule citation, a settings `deny` reads `Permission to use Bash with
  command … has been denied`, and neither can be a user rejection.

And **change one variable per probe**: a control differing in two ways
produced this record's other wrong finding. Never probe a rule with a
`.claude/` path — P12's gating masks whatever is under test.

### What was measured

| # | Question | Answer |
|---|---|---|
| P1 | Is the hook reached at all? | **Yes.** `git push origin main --force --dry-run` — a spelling no `deny` entry matches — came back refused carrying the guard's own text |
| P2 | Does a hook `ask` still prompt? | **Yes.** The dry-run push prompted. Rule 6's close push rests on this |
| P3 | Does `Bash(git push --force:*)` bind? | **Yes**, as does the `Bash(cmd *)` form |
| P4 | Do `deny` prefixes match mid-line? | **No** — only from the **start**. `basename --colonstar x` denied, `basename /a/b --colonstar` silent. So `git push origin main --force` matches nothing and only the guard catches it: this project's thesis, measured |
| P5 | Does the guard ever emit `allow`? | **No.** Only `deny` and `ask`; a proven grant is silence, indistinguishable from an unknown command |
| P6 | `acceptEdits` + unmatched command? | **Prompts** when it has a side effect (`python3 -c` writing a file). Trivially read-only ones (`basename`, `dirname`) run — a built-in carve-out, not our allow list. `D-011`'s accepted `python3` cost is real |
| P7 | Does an `ask` rule beat `acceptEdits`? | **Yes**, measured outside `.claude/`: `Write` to `probe-noask/x.txt` silent, to `probe-ask/x.txt` prompted |
| P8 | Does `Edit(…)` match a `Write` call? | **Yes** — same probe. Confirms the operator's 2026-08-20 ruling; `Write(…)` rules match nothing |
| P9 | `$CLAUDE_PROJECT_DIR` in `PreToolUse` hooks? | **Exported**, = project root; the hook's `PWD` is too, so the registry's boundary rules resolve correctly by both roads |
| P10 | Is `autoMemoryEnabled` honoured? | **Recognised** — a live string in the binary, with no memory artifact anywhere. Presence plus absence, not a positive behavioural test |
| P11 | Does `settings.local.json` need a restart? | **No** — `deny` rules and `PreToolUse` hooks took effect in the session that wrote it. Keep restarting before concluding a mechanism is *dead*; the error runs one way |
| P12 | Are `.claude/` writes gated? | **Yes, by the platform**, through file tools and `>` alike, and an explicit `allow` does **not** suppress it. Verified with `allow: Edit(.claude/docs/**)` loaded and proven live. **No setting removes the prompt on a working-memory edit** (operator asked, 2026-08-20) |

`auto` mode: `classifyAllShell` is unset, so the allow list stood and the
guard ran ahead of it (P1 and P2 were taken in that mode; both paths are
mode-independent and P2 was re-confirmed under `acceptEdits`). The
classifier A/B `D-011` reserved `auto` for is **not** run here — it needs
`classifyAllShell` on and is not this step's deliverable.

**Nothing needed changing.** Every pre-committed unfavourable branch —
re-spelling the backstop, moving the `ask` tier to `deny` — went unused.

### One `001` claim corrected

`001` reasoned that a `>` into a boundary file was invisible to both
gates, so "nothing **prevents** a shell redirection". Measured, the truth
is narrower and does not favour us:

- the **guard** is blind to redirection — confirmed, it returns silence
  for `echo probe > .claude/settings.json` and every sibling spelling;
- **file-path rules never match a `>` target** — an `ask` rule on
  `probe-ask/**` is silent for `echo probe > probe-ask/y.txt` while
  firing for a `Write` to the same directory;
- but **P12 gates it anyway**, and every boundary file is under
  `.claude/`, so the command does prompt.

So it is prevented — by a platform behaviour this repository neither
configures nor can rely on across updates, **not** by the `ask` tier.
`check-guard.sh` is the only redirection backstop we own. If P12 ever
comes back silent, redirections into the settings go silent with it.

### Re-measure

Agree the refusal protocol first. Expect a prompt where marked.

```sh
# P1, P3, P4 — self-identifying, no protocol needed
git push origin main --force --dry-run          # guard text + [rule …]
basename --colonstar /a/b/c                     # "Permission to use Bash…"
basename /a/b --colonstar                       # silent  ← P4

# P5 — guard verdicts, out of band
printf '{"tool_name":"Bash","tool_input":{"command":"pip list"}}' \
    | .claude/hooks/bash_guard.py | wc -c       # 0

# P6 — needs the protocol
python3 -c 'open("/tmp/p","w").write("x")'      # must prompt

# P7, P8, P12 — need .claude/settings.local.json carrying
#   ask:   Edit(probe-ask/**)
#   allow: Edit(.claude/docs/**)
# then, under the protocol, Write to:
#   probe-noask/x.txt   silent        probe-ask/x.txt      prompt
#   .claude/docs/x.txt  prompt (P12, despite the allow)
# and  echo probe > probe-ask/y.txt   silent (rules miss redirections)

# P9
cat /tmp/frisk-probe-hookenv.txt   # with a hook echoing $CLAUDE_PROJECT_DIR

# P10
grep -ac autoMemoryEnabled "$(readlink -f "$(which claude)")"
find ~/.claude -maxdepth 2 -iname '*memor*'     # nothing
```

Delete `.claude/settings.local.json` and every probe target afterwards.

## The liveness triple — for the `003` session rituals

Three **live tool calls**, never piped to the guard by hand: the payload
in [The commands](#the-commands) asks whether the file is correct, these
ask whether Claude Code is calling it.

| # | Command | Must do |
|---|---|---|
| 1 | `git status --short` | run, no prompt |
| 2 | `git push --dry-run origin main` | **prompt** — `pushing is an outward write [rule git push]` |
| 3 | `git push origin main --force --dry-run` | **refuse** — `history is linear here and published state is never rewritten [rule git push: --force]` |

Answer 2 either way; both pushes are dry runs.

**Three carries the weight.** No `deny` entry matches that spelling (P4),
so a refusal can only have come from the hook. If it merely **prompts**,
the hook is not reached and the backstop is all that is left — while
`--selftest` and `--liveness` would both still pass. If it **runs**, both
are gone.

It is silent / ask / deny, not the silent / grant / deny `PLAN.md`
sketched: there is no observable grant to put in the middle (P5), and an
`ask` is the better probe anyway — it is the path rule 6 depends on.
