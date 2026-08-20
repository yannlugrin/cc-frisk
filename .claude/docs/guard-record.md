# The development guard — the record

**Read this before touching `.claude/settings.json`, `.pre-commit-config.yaml`'s
`check-guard` hook, `scripts/check-guard.sh`, or anything under
`.claude/hooks/`.** It is the durable half of `CLAUDE.md` rule 1's
quarantine: everything about the guard that a later session needs and
cannot get by reading the file, because reading the file is forbidden.

Written at step `001` (2026-08-20). Step `002` added
[the platform probes](#the-platform-probes) — what the installed Claude
Code version actually does with the permission rules and the hook
registered here — and
[the liveness triple](#the-liveness-triple--for-the-003-session-rituals)
the session rituals run. **All six measurements `002` owed are taken**;
nothing in this file is an assumption carried over from the bootstrap
instructions or from `CLAUDE.md`.

Before designing a probe of your own, read
[the method trap](#the-method-trap-it-ran-is-not-a-measurement): a tool
call that was prompted and approved is indistinguishable from one that
was never gated, and the mistake reports a live gate as dead.

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
  '{}' > .claude/settings.json` gets no verdict from it: the
  boundary-file rules only catch spellings that pass the path as an
  argument, and a redirection target is not one. **In practice the
  command still prompts, but not for any reason this repository
  controls**: `002` measured that file-path rules do not match a `>`
  target at all — an `ask` rule on the path is silent for a redirection —
  while Claude Code gates writes under `.claude/` on its own, and every
  boundary file lives there
  ([A4](#a4-a-redirection-is-matched-by-no-file-rule--the-platform-gates-claude-anyway),
  [B6](#b6-writes-under-claude-are-gated-by-the-platform-and-allow-does-not-override)).
  `001` recorded that nothing *prevents* a shell redirection; that was
  reasoned, never measured, and the truth is narrower than either the
  claim or its first correction. **Treat the platform's behaviour as a
  courtesy, not a control** — it is unconfigured here and can change with
  an update, and the `ask` tier will not catch redirections if it does.
  `check-guard.sh` is the only redirection backstop the repository owns,
  and it also catches an edit that was **approved** or made with no
  session watching: it asserts the invariants a loosening would have to
  break — an emptied `deny` list, a switched mode, a removed bypass lock,
  a hook that no longer answers — so such an edit survives at most until
  the next `just check` or commit. Detective, and load-bearing.
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
confound for anything mode-sensitive. Round B was measured after
switching the same session to `acceptEdits`; the mode was **read back
from the session transcript**, not assumed —
`grep -ao '"permissionMode":"[a-zA-Z]*"' ~/.claude/projects/<slug>/<id>.jsonl | tail -1`.

### The method trap: "it ran" is not a measurement

**Read this before designing any probe of a permission mechanism, here or
at `003`.** It invalidated two of this campaign's probes on the first
attempt and the operator caught it, not the checks.

From inside the session, **a tool call that was prompted and approved and
a tool call that was never gated at all return the identical result:
plain success.** The transcript shows the tool output and nothing about
whether a prompt intervened. So "I ran it and it worked, therefore
nothing gated it" is not an inference the evidence supports — and it
fails in the dangerous direction, reporting a live gate as dead.

**The transcript cannot rescue you afterwards.** The session `.jsonl`
under `~/.claude/projects/<slug>/` records `permissionMode` and nothing
about permission *decisions* — no allow, no deny, no record that a prompt
was shown. Measured by grepping it for every plausible key. So a probe
that was run ambiguously cannot be reinterpreted later; it has to be run
again.

Two ways out, and a probe must use one of them:

- **The refusal protocol.** The operator agrees in advance to **refuse
  every prompt** for the duration. Success then means no prompt appeared;
  `The user doesn't want to proceed…` means one did. Unambiguous in both
  directions. The cost is that each refusal interrupts the run, so batch
  the probes into separate calls and expect to be stopped. **Say
  explicitly that the protocol has ended**, or the next real command gets
  refused too.
- **A distinguishable message.** Some outcomes identify their own source
  and need no protocol: the guard's refusals carry its own sentence and a
  bracketed rule citation, and a settings `deny` reads `Permission to use
  Bash with command … has been denied`. Neither can be confused with a
  user rejection. Probes A1, A2 and B1's first two rows rest on this and
  were never in doubt.

The corollary for the record: **every "ran without a prompt" claim below
was taken under the refusal protocol**, and any that could not be is
marked as the weaker claim it is.

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

### A4. A redirection is matched by no file rule — the platform gates `.claude/` anyway

**This overturns a limitation `001` recorded**, in the safe direction.
`001` reasoned that a `>` redirection into a boundary file was invisible
to both gates and concluded "nothing **prevents** a shell redirection".
The first half is true and the conclusion is false.

**The guard is blind to redirection — confirmed.** Fed directly, it
returns silence for every spelling, including into its own settings:

| Payload | Guard |
|---|---|
| `echo probe > .claude/hooks/redir-probe.txt` | silent |
| `echo probe > .claude/settings.json` | silent |
| `cat > .claude/settings.local.json` | silent |

Its boundary-file rules match a path passed **as an argument** to a named
writer, and a redirection target is not an argument. That is unchanged.

**A redirection is matched against no file rule at all.** Neither `ask`
nor `allow` reaches one. Measured under the refusal protocol with a
machine-local `ask` rule on a path **outside `.claude/`**, which is the
only way to see the tier without the platform gating below masking it:

| Command | Rule in force | Result |
|---|---|---|
| `echo probe > probe-ask/y.txt` | `ask: Edit(probe-ask/**)` | **ran**, silent |
| `echo probe > control-probe.txt` | none | **ran**, silent |

The same `ask` rule **did** fire for a `Write` tool call to the same
directory ([B5](#b5-the-ask-tier-beats-acceptedits-and-edit-matches-write)),
so the rule was loaded and live. File-path rules govern the **file
tools**; a `>` target is not seen by them.

**What does gate a redirection into a boundary file is the platform, not
this repository.** Writes under `.claude/` prompt regardless of the rules
— see
[B6](#b6-writes-under-claude-are-gated-by-the-platform-and-allow-does-not-override).
Every boundary file lives under `.claude/`, so in practice
`echo '{}' > .claude/settings.json` **does** prompt:

| Command | Result |
|---|---|
| `echo probe > .claude/hooks/redir-probe.txt` | **prompted** |
| `echo probe > .claude/docs/redir-control.txt` (no `ask` rule) | **prompted** |
| `echo probe > control-probe.txt` (outside `.claude/`) | **ran**, silent |

**So `001`'s conclusion was wrong, and the correction is narrower than it
first looked.** A shell redirection into a boundary file is prevented —
but by a Claude Code behaviour this repository does not configure and
cannot rely on across updates, **not** by the `ask` tier, which does not
apply to redirections at all. `check-guard.sh` therefore keeps its full
weight: it is the only redirection backstop the repository itself owns.
Re-measure B6 after every Claude Code update; if the platform stops
gating `.claude/`, redirections into the settings become silent again
and nothing in `.claude/settings.json` will catch them.

**Still uncovered by anyone:** a redirection used to defeat a **grant**
(`pip install -r requirements.txt 2>&1` → `ask`), the separate flaw under
[Blind spots](#blind-spots--stated-as-consequences), ruled not-fixed.

**Re-measure.** Under the refusal protocol, the three `echo` commands in
the second table: prompt, prompt, silence.

**Method note — this entry was wrong twice.** Its first draft claimed
redirections were ungated, on a heredoc write that had in fact been
**prompted and approved** ([the method trap](#the-method-trap-it-ran-is-not-a-measurement)).
Its second draft claimed the `ask` tier caught them, on a control
(`control-probe.txt`) that differed from the test in **two** variables at
once — not a boundary path *and* not under `.claude/`. Only a control
holding one variable fixed settled it. Change one thing per probe.

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

### B1. Both rule spellings bind — and only from the start of the line

**Why it matters.** `Bash(git push --force:*)` is what the backstop is
written in. If that spelling binds nothing, the backstop is decoration.
The CLI's own `--allowedTools` help documents a `Bash(git *)` prefix form
as well, so both were live in the documentation and untested here.

**Method.** Synthetic `deny` entries in the machine-local harness, on
`basename` — a command the guard leaves silent, so the hook cannot be
mistaken for the permission rules. A settings refusal reads
`Permission to use Bash with command … has been denied`; the guard's
reads as its own sentence with a bracketed rule citation. The two are
told apart by their text.

**Measured.** With `Bash(basename --colonstar:*)` and
`Bash(basename --prefixform *)` in force:

| Command | Result |
|---|---|
| `basename --colonstar /a/b/c` | **denied**, generic permission text |
| `basename --prefixform /a/b/c` | **denied**, generic permission text |
| `basename /a/b --prefixform` | **ran**, no prompt, printed `b` |

The first two rows identify their own source by their text. The third was
re-measured **under the refusal protocol**, with a spelling that had not
run earlier in the session, because its first measurement rested on "it
ran" and was worthless — see [the method trap](#the-method-trap-it-ran-is-not-a-measurement).

**Both spellings bind, so the backstop is real.** The third line is the
one worth keeping: the same flag, in the same command, moved past the
first argument, matches nothing. Prefix rules match from the **start of
the command line** and there is no fix for that inside them.

This closes the attribution of [A1](#a1-the-hook-is-reached-and-a-refusal-names-its-rule)
as well: `git push origin main --force --dry-run` matches no `deny`
entry, so the refusal there came from the hook and from nothing else.
It is also this project's thesis, now measured rather than asserted —
`Bash(git push --force:*)` denies `git push --force …` and says nothing
about `git push origin main --force`, the commoner spelling from muscle
memory. The guard catches the second; the permission rules cannot.

**Re-measure.** Restore the two synthetic entries in
`.claude/settings.local.json` and run the three commands above.

### B2. `$CLAUDE_PROJECT_DIR` is exported to `PreToolUse` hooks

**Why it matters.** The registry's boundary-file rules resolve against
it, falling back to the guard process's working directory — under a
hook, wherever Claude Code chooses to launch it. An absent variable
*and* a working directory that is not the project root would resolve
those rules against the wrong tree, silently.

**Method.** A second `PreToolUse` hook in the machine-local harness,
appending both values to a file and exiting 0.

**Measured.** Every invocation recorded
`CLAUDE_PROJECT_DIR=[/home/yann/projects/claude/frisk]` and
`PWD=[/home/yann/projects/claude/frisk]`. **The variable is exported and
correct, and the fallback would have been correct too** — both roads
lead to the project root here. The rules resolve against the right tree.

**Re-measure.**

```sh
cat /tmp/frisk-probe-hookenv.txt    # while the harness hook is registered
```

### B3. A `settings.local.json` change is picked up **without** a restart

**Why it matters.** `PLAN.md`'s `002` entry states the restart as
method — a probe run in the session that made the edit can report a
false "not enforced". On `2.1.237` that is **stricter than necessary for
this file**, and knowing which way the error runs matters: the recorded
recipes are safe either way, but a session that assumes a restart is
needed will misread a rule that is already live.

**Measured.** `.claude/settings.local.json` was created mid-session, and
both its synthetic `deny` entries and its extra `PreToolUse` hook took
effect in that same session, with no restart — the hook's first line is
timestamped seconds after the file was written.

**The conservative reading stands as the method.** This was measured for
one file, on one version, for `deny` rules and `PreToolUse` hooks; it is
not a licence to assume hot reload for `defaultMode`, for
`.claude/settings.json`, or for anything else. **Restart before
concluding that a mechanism does not enforce**; a live one may simply be
believed dead the other way round.

**Re-measure.** Write a synthetic `deny` into
`.claude/settings.local.json` and run the matching command in the same
session.

## The liveness triple — for the `003` session rituals

Three live tool calls, run **as tool calls in a session**, never piped to
the guard by hand. The hand-fed payload in
[The commands](#the-commands) asks whether the file is correct; these ask
whether Claude Code is calling it. Both questions are real and only the
second one can catch the silent death.

| # | Command | Must do | Proves |
|---|---|---|---|
| 1 | `git status --short` | run, no prompt | the loop is not blocked: guard silent, allow rule carries it |
| 2 | `git push --dry-run origin main` | **prompt**, `pushing is an outward write [rule git push]` | the hook's `ask` path still reaches the operator — what rule 6's close push rests on |
| 3 | `git push origin main --force --dry-run` | **refuse**, `history is linear here and published state is never rewritten [rule git push: --force]` | the hook is reached at all |

Answer 2 either way; `--dry-run` makes both harmless.

**Three is the load-bearing one.** It is the only command here that no
`deny` entry matches ([B1](#b1-both-rule-spellings-bind--and-only-from-the-start-of-the-line)),
so a refusal can only have come from the hook. If it merely **prompts**,
the hook is not reaching the tool call, the backstop is all that is
left — and `--selftest` and `--liveness` would both still pass, because
they answer whether the file is correct, not whether anything calls it.
If it **runs**, both are gone.

**The triple is silent / ask / deny, not silent / grant / deny** as
`PLAN.md`'s `002` entry sketched it. There is no observable "grant": the
guard emits only `deny` and `ask`, and a proven grant is plain silence,
indistinguishable from a command it never heard of
([A3](#a3-the-guard-has-no-allow-verdict-a-grant-is-silence)). An `ask`
in that slot is strictly more informative anyway — it is the one path
the close ritual depends on, and the one no local command can test.

### B4. `acceptEdits` prompts for an unmatched command with a side effect

**Why it matters.** The guard's silence is only as safe as what the mode
does with a command it never judged. If `acceptEdits` ran everything
unmatched, the allow list would be decoration and the guard's `ask`
verdicts would be the only gate left in the loop.

**Method.** Under the **refusal protocol**, two unmatched commands — no
allow rule covers `basename`, `dirname` or `python3`, the guard is silent
on all three, and no `deny` entry matches — with fresh spellings that had
not run earlier in the session.

**Measured.**

| Command | Prompt? |
|---|---|
| `basename /a/b --prefixform` (pure computation) | **no** — ran |
| `dirname /x/y/z` (pure computation) | **no** — ran |
| `python3 -c 'open("…","w").write("…")'` (writes a file) | **yes** — prompted, refused |

**The mode prompts for unmatched commands; it does not wave them
through.** What ran unprompted was trivially read-only, which points at a
built-in safe-command carve-out rather than at anything in
`.claude/settings.json` — this repository's allow list does not name
`basename` or `dirname`. The moment a side effect is involved, the prompt
appears.

**`D-011`'s prediction holds and is now verified**: it accepted as a real
cost that `python3` would prompt, since rule 9's free list names it and
no broad allow for a runner was granted. It does prompt. The same
reasoning covers the documented direct equivalents
(`bash scripts/check.sh`, `.venv/bin/pre-commit run`), which are not
separately measured.

**This claim was wrong in this record's first draft** and said the
opposite, on a `python3 -c` call that had in fact been prompted and
approved. That is the method trap above, and the reason the protocol
exists.

**Re-measure.** Agree the refusal protocol, then run a `python3 -c` that
writes to a scratch path, with a spelling not used earlier in the
session. A success means the mode stopped gating; investigate before
trusting the loop.

### B5. The `ask` tier beats `acceptEdits`, and `Edit(…)` matches `Write`

**Why it matters.** Two questions in one call. If an explicit `ask` rule
loses to the mode, the boundary's own files are unprotected against a
silent, well-formed edit, and **the pre-committed response was to move
the tier to `deny` with a named unlock path**. And if `Edit(…)` rules do
not reach `Write` tool calls, the tier has a `Write`-shaped hole in it
whatever its verdict.

**Method.** A `Write` is the sharper test than an `Edit`, because it
tests the rule and the tool mapping at once. It must be aimed **outside
`.claude/`**: a `Write` under `.claude/hooks/` prompts whether or not any
rule names it ([B6](#b6-writes-under-claude-are-gated-by-the-platform-and-allow-does-not-override)),
so the baseline's own paths cannot answer this question. A machine-local
`ask` rule on `probe-ask/**` supplies a path where the tier is the only
variable. Refusal protocol throughout.

**Measured.** Same tool, same session, same mode, one variable:

| `Write` target | Rule in force | Result |
|---|---|---|
| `probe-noask/x.txt` | none | **ran**, silent |
| `probe-ask/x.txt` | `ask: Edit(probe-ask/**)` | **prompted** |

**Both halves hold.** An explicit `ask` rule beats `acceptEdits`, and an
`Edit(…)` rule matches a `Write` tool call — confirming the operator's
ruling of 2026-08-20 that the file tools, `Write` included, are matched
by `Edit(…)` rules and that `Write(…)` rules match nothing. The control
also pins `acceptEdits` itself: an unruled `Write` is auto-accepted, so
the prompt in row two is the rule and nothing else.

**No change to the baseline.** The pre-committed `deny` fallback is not
triggered; `.claude/settings.json`'s `ask` tier stands as written, and
the guard's own maintenance keeps its unlock path.

**Re-measure.** Recreate the `probe-ask/**` rule in
`.claude/settings.local.json` and run the two `Write`s above. Silence on
the second means the tier has stopped binding — the `deny` fallback
becomes live again. Never aim a probe at `bash_guard.py`.

**Method note.** This was first measured against
`.claude/hooks/probe-target2.txt`, which prompted — but B6 means that
prompt proves nothing about the tier. Re-measured outside `.claude/`.

### B6. Writes under `.claude/` are gated by the platform, and `allow` does not override

**Why it matters.** It explains a prompt this repository does not
configure, it is the real reason a redirection into a boundary file is
stopped ([A4](#a4-a-redirection-is-matched-by-no-file-rule--the-platform-gates-claude-anyway)),
and it invalidates any probe that uses a `.claude/` path to test a rule —
two of this campaign's did, and both had to be redone.

**Measured.** Under the refusal protocol, with
`allow: ["Edit(.claude/docs/**)"]` machine-local and **proven loaded**
(the `ask` rule from the same file fired for B5):

| Action | Target | Result |
|---|---|---|
| `Write` tool | `.claude/docs/probe.txt`, explicitly **allowed** | **prompted** |
| `>` redirection | `.claude/docs/redir-control.txt`, no rule | **prompted** |
| `>` redirection | `control-probe.txt`, outside `.claude/` | **ran**, silent |
| `Write` tool | `probe-noask/x.txt`, outside `.claude/` | **ran**, silent |

**Claude Code gates writes under `.claude/` on its own, in `acceptEdits`,
through both the file tools and shell redirection, and an explicit
`allow` rule does not suppress it.** There is no setting in this
repository that removes the prompt.

**Consequences.**

- **Every edit to `.claude/docs/` prompts**, including this file. That is
  the platform, not the baseline and not a tooling choice; the operator
  asked whether an allow-list entry would stop it and the measured answer
  is **no** (2026-08-20). Sessions should expect an approval per
  working-memory write and not go hunting for a misconfiguration.
- **It is not ours and may change.** Nothing in `.claude/settings.json`
  depends on it, and A4 says plainly what is lost if it goes away.
- **Never probe a permission rule with a `.claude/` path.** The gating
  masks the rule under test.

**Re-measure.** Put `allow: ["Edit(.claude/docs/**)"]` in
`.claude/settings.local.json`, then `Write` a disposable file under
`.claude/docs/` under the refusal protocol. A silent success means the
platform stopped gating `.claude/` — re-read A4 immediately, because the
redirection backstop went with it.

### Nothing is open

All six measurements `002` owed are taken, plus three the campaign turned
up on its own: the guard has no `allow` verdict
([A3](#a3-the-guard-has-no-allow-verdict-a-grant-is-silence)),
`.claude/settings.local.json` hot-loads
([B3](#b3-a-settingslocaljson-change-is-picked-up-without-a-restart)),
and the platform gates `.claude/` writes
([B6](#b6-writes-under-claude-are-gated-by-the-platform-and-allow-does-not-override)).
One limitation `001` recorded was overturned and one was rewritten twice
before it was right ([A4](#a4-a-redirection-is-matched-by-no-file-rule--the-platform-gates-claude-anyway)).
**No change to `.claude/settings.json` is needed**: every pre-committed
unfavourable branch — re-spelling the backstop, moving the `ask` tier to
`deny` — went unused, because each spelling measured correct.

What remains deliberately unmeasured, and is **not** owed here: the
`auto`-mode classifier A/B against the guard
([A6](#a6-auto-mode-leaves-the-allow-rules-standing)), which needs
`classifyAllShell` on and is not this step's deliverable; and a positive
behavioural test of `autoMemoryEnabled`
([A5](#a5-automemoryenabled-is-a-key-this-version-knows)), recorded at
presence-plus-absence strength instead.

The probe harness is **removed**: no `.claude/settings.local.json`, no
probe targets under `.claude/hooks/`, no `/tmp/frisk-probe-*`. The
baseline in `.claude/settings.json` is what is in force.
