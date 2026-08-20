# The development guard — the record

**Read this before touching `.claude/settings.json`, `.pre-commit-config.yaml`'s
`check-guard` hook, `scripts/check-guard.sh`, or anything under
`.claude/hooks/`.** It is the durable half of `CLAUDE.md` rule 1's
quarantine: everything about the guard that a later session needs and
cannot get by reading the file, because reading the file is forbidden.

Written at step `001` (2026-08-20). Step `002` adds
[the platform probes](#the-platform-probes) — what the installed Claude
Code version actually does with the permission rules and the hook
registered here. Round A of that campaign is measured and recorded;
[Round B](#still-open--round-b) is still open, and each of its four
entries names the response already committed to if it comes back wrong.

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

## The platform probes

Every claim here is a measurement, not an inference. **Taken on Claude
Code `2.1.237`, Linux (WSL2), 2026-08-20**, unless a line says otherwise.
Re-run the lot after a Claude Code update: each of these is a property
that fails silently — the mechanism stops enforcing and announces
nothing.

**The restart is part of the method.** Settings and hook changes are read
at session start, so a probe run in the session that made the edit can
report a false "not enforced". Every recipe below that touches a settings
file says where its restart falls. The `001` baseline was written in the
previous session, so the probes below that read it were measured against
a session that loaded it cleanly.

**Round A** (below) was measured in a session running **`auto` mode**,
not the `acceptEdits` baseline. That is stated per probe, because it is a
confound for anything mode-sensitive; the mode-sensitive probes are
Round B's and are still open.

### A1. The hook is reached, and a refusal names its rule

**Why it matters.** `--selftest` and `--liveness` answer whether the file
is correct, never whether anything calls it. If a denied command merely
prompts, the hook is not reaching the tool call and only the `deny`
backstop is live. No local command can detect this.

**Method.** Fire a command the guard denies and **no settings `deny`
prefix matches**. `git push origin main --force --dry-run` is that
command: the backstop entries match from the start of the line, so
`Bash(git push --force:*)` does not reach this spelling, while the guard
keys on the flag's presence. `--dry-run` makes the fall-through harmless
if the hook turns out to be dead.

**Measured.** The call came back refused, carrying the guard's own text
verbatim: `history is linear here and published state is never rewritten
[rule git push: --force]`. Feeding the same command to the guard by hand
returns that identical string. **The hook is reached and its `deny` is
honoured.** Measured in `auto` mode; the hook path is documented as
mode-independent, and Round B re-confirms it under `acceptEdits`.

**Re-measure.**

```sh
# expected verdict, out of band:
printf '{"tool_name":"Bash","tool_input":{"command":"git push origin main --force --dry-run"}}' \
    | .claude/hooks/bash_guard.py | jq -r '.hookSpecificOutput.permissionDecision'   # deny
# then, as a live tool call in a session started after the settings landed:
git push origin main --force --dry-run
# must be refused, naming [rule git push: --force]. A prompt, or an
# actual dry-run, means the hook is not reached.
```

### A2. A hook `ask` still prompts

**Why it matters.** Rule 6's close ritual attempts a push at every step
close and relies on being able to approve it in that exchange. A gate
that has stopped gating says nothing about itself.

**Method.** `git push --dry-run origin main` — the guard returns `ask`
(`pushing is an outward write [rule git push]`), and `--dry-run` makes it
harmless whichever way the operator answers.

**Measured.** It prompted. The operator declined, and the tool call was
rejected. **The `ask` path reaches the operator.** Measured in `auto`
mode; Round B re-confirms under `acceptEdits`, which is the mode the
close ritual actually runs in.

**Re-measure.** Run `git push --dry-run origin main` in a fresh session
and answer the prompt either way. Silence — the push simply running — is
the failure.

### A3. The guard has no `allow` verdict: a grant is silence

**Why it matters.** `PLAN.md`'s `002` entry asked the liveness triple to
include "one the guard *grants*". It cannot, as a distinct observable:
a proven grant and a command the guard never heard of both produce **no
output at all**, and both then fall to the permission rules. The triple
is designed around that below.

**Measured.** `pip install -r requirements.txt` (the one proven `pip`
shape), `pip list`, `just check changed` and `git status --short` all
return empty output, exit 0. Only `deny` and `ask` produce a verdict:
`pip install requests` → `ask`, `gh pr create` → `ask`, `sudo ls` →
`ask`, `git push --force` → `deny`. Mode-independent: the guard is a
process reading stdin.

**Re-measure.**

```sh
for c in "pip install -r requirements.txt" "pip list" "git status --short"; do
    printf '{"tool_name":"Bash","tool_input":{"command":"%s"}}' "$c" \
        | .claude/hooks/bash_guard.py | wc -c    # must be 0
done
```

### A4. A shell redirection into a boundary file is ungated — observed

**Why it matters.** The blind spot was reasoned at `001`. It is now
observed live, which is a stronger claim.

**Measured.** Writing `.claude/settings.local.json` from a Bash heredoc
redirection produced **no prompt and no verdict**. Both gates miss it for
different reasons, and both are working as designed: the settings `ask`
tier names the *native file tools* (`Edit(…)`), which a Bash call is not,
and the guard's boundary-file rules only match a path passed **as an
argument** to a named writer, which a `>` redirection does not do. So a
well-formed settings edit by redirection is silent, and `check-guard.sh`
is what catches it afterwards. Detective, not preventive — as stated.

**Re-measure.** Any `cat > .claude/settings.local.json <<'JSON' … JSON`
in a session. A prompt would mean the coverage improved; note it.

### A5. `autoMemoryEnabled` is a key this version knows

**Why it matters.** An unrecognised setting is ignored in silence, and
auto memory is machine-local, unversioned state outside rule 3's files.

**Method.** Two halves, because no command prints the effective value.
First, whether the shipped binary knows the string at all — an unknown
key would not appear in it. Second, whether any auto-memory artifact
exists.

**Measured.** All five keys this repository sets or relies on are present
as strings in the `2.1.237` binary: `CLAUDE_PROJECT_DIR` (26),
`disableAutoMode` (13), `disableBypassPermissionsMode` (8),
`autoMemoryEnabled` (6), `classifyAllShell` (4). No auto-memory file or
directory exists under `~/.claude/` or the project's `.claude/`, and no
`CLAUDE.local.md` exists. **Recognised, and consistent with being
honoured.** This is a presence measurement plus an absence one; it is
not a positive behavioural test, and is recorded at that strength.

**Re-measure.**

```sh
b=$(readlink -f "$(which claude)")
grep -aoE 'autoMemoryEnabled|disableAutoMode|disableBypassPermissionsMode|classifyAllShell|CLAUDE_PROJECT_DIR' "$b" \
    | sort | uniq -c
find ~/.claude -maxdepth 2 -iname '*memor*'    # must print nothing
```

### A6. `auto` mode leaves the allow rules standing

**Why it matters.** `auto` stays reachable deliberately (`D-011`) so a
classifier can be A/B'd against the guard. `autoMode.classifyAllShell`
suspends every Bash allow rule — the knob that makes the comparison
meaningful — and it is **not set** here.

**Measured.** `claude auto-mode config` reports the effective
configuration with keys `allow`, `environment`, `hard_deny`, `soft_deny`;
`classifyAllShell` reads `null`. So in this session's `auto` mode the
baseline's allow list still applied, and the guard still ran ahead of it
— A1 and A2 were both measured in that mode. The A/B comparison the
decision reserved `auto` for has **not** been run; it needs
`classifyAllShell` on, and it is not this step's deliverable.

**Re-measure.** `claude auto-mode config | jq '.classifyAllShell'`.

### Still open — Round B

Each needs a session in the **`acceptEdits`** baseline mode, and the two
settings-dependent ones need a restart after the probe harness lands.
The harness is `.claude/settings.local.json` (machine-local, gitignored),
carrying two synthetic `deny` entries on `basename` — a command the guard
leaves silent, so the two mechanisms cannot confound each other — and a
second `PreToolUse` hook that appends `$CLAUDE_PROJECT_DIR` and `$PWD` to
`/tmp/frisk-probe-hookenv.txt` and exits 0.

1. **Does `Bash(git push --force:*)` actually match?** The colon-star
   form is what the pairing prescribes; the CLI's own `--allowedTools`
   help documents a `Bash(git *)` prefix form as well, so both spellings
   are live in the documentation and one of them may bind nothing. Probed
   through the synthetic pair `Bash(basename --colonstar:*)` and
   `Bash(basename --prefixform *)`. **If the colon-star form does not
   bind, the backstop is decoration — re-spell it.**
2. **What does `acceptEdits` do with an unmatched Bash command?** The
   guard's silence is only as safe as that behaviour.
3. **Does an explicit `ask` rule beat `acceptEdits` for the file tools?**
   If not, the boundary's own files are unprotected against a silent,
   well-formed settings edit and the tier must be `deny` with a named
   unlock path. Half is already answered: **`Write(…)` rules match
   nothing** — the file tools, `Write` included, are matched by `Edit(…)`
   rules (operator, 2026-08-20). Confirm that mapping with a live `Write`
   at a boundary path.
4. **Is `$CLAUDE_PROJECT_DIR` exported to `PreToolUse` hooks?** The
   registry's boundary rules resolve against it, falling back to the
   guard process's working directory — under a hook, wherever Claude Code
   launches it. Absent variable *and* a working directory that is not the
   project root means those rules resolve against the wrong tree. The
   harness hook records both.

**Cleanup owed at the end of Round B:** delete
`.claude/settings.local.json` and `/tmp/frisk-probe-hookenv.txt`, and
restart once more so the baseline alone is in force.
