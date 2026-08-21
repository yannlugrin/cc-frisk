# Standing instructions — frisk implementation

You are implementing frisk, an open-source Claude Code plugin: a
parsing-based guard for the Bash tool (repository `cc-frisk`; plugin,
CLI and skill namespace `frisk`). `SPECIFICATIONS.md` at the repository
root is the complete specification and defines its own reading rules —
requirements as "must", recommended defaults as "should", environment
constraints stated as facts.

Loaded on every run, this file holds what applies **always**; everything
context-specific lives in `.claude/docs/`, read at its trigger. Rule
numbers are permanent — tooling and decision entries cite them.

## Session start

Read this file, `PLAN.md`, `DECISIONS.md`, and the specification sections
the current step names. Find the last approved state by the **step
namespace**, never by the latest tag of any kind (other tags exist):
`git describe --tags --abbrev=0 --match 'step-*'`. `git log` and
`git diff` from that tag to `HEAD` are exactly the work in progress;
before the first step tag, the range is the whole history. Then tell the
operator where we are **before touching anything**. If the session was
resumed after an interruption, or the operator says the work was
interrupted, run `/resume-step` first — never trust the transcript.

## The rules

**1. `SPECIFICATIONS.md` is read-only for you.** Never edit it on your
own initiative. An ambiguity, a contradiction, or something that cannot
be implemented as written: stop and raise it with the operator. If a
change is agreed, the decision entry is written **before** the
amendment, and both land in **one commit** — the `DECISIONS.md` entry
and the specification text, nothing else, the subject naming the
decision (`step-012: spec amendment — D-007, …`). Code stays out, so
`git log -- SPECIFICATIONS.md` stays a readable history of amendments;
the implementing code, and any documentation the amendment makes stale,
follow in the step's later commits — for amendment commits this beats
rule 6's same-commit staleness sweep. The entry lands alone only when
the amendment belongs to a later step, and then it names that step.
Silent drift between spec and implementation is what this rule prevents.

*Open facts.* §2.1's four lettered facts and thirteen-item inventory are
the expected case of that channel — the specification ordered them
settled during implementation, and `PLAN.md` §11 maps each to its step.
Recording a *verified fact* is autonomous: entry and amendment in one
commit, reported in the step summary. **Any resolution that changes a
requirement, a tier, a documented limitation or the decision to ship
comes back to the operator before the amendment**; where both apply, the
escalation wins. Always coming back: (b), (c), (d), items 6, 9, 10, 13 —
that list names the certain ones; the general clause decides the rest.
A fact that cannot be measured is recorded as unmeasured and treated at
the stricter branch of its pre-committed response. Resolutions land in
two places: the specification, and §12's verification record.

*Of the phase that produced the specification, the specification itself
is your only input.* `.claude/spec-work/` is that phase's own history
and you never read anything in it — the tooling-template exception
expired at step `004`. When something seems missing, that is a question
for the operator, never something to excavate.

*The `bash_guard.py` quarantine.* **`.claude/hooks/bash_guard.py` never
enters your context, in this session or any later one.** It is the
prototype of the very product this specification describes, and §3.1
deliberately excludes the prototype's code and API shapes as inputs:
reading it would import the accidental design a fresh start exists to
avoid. Any task needing its contents — instantiation, registry and
`CASES` edits, later guard maintenance — runs in an **isolated
subagent** that reads and edits the file and reports outcomes (what is
gated, what the settings pairing requires, whether its checks pass),
never the file's text, parsing approach or API shapes. Executing it
(`--selftest`, `--liveness`) is fine: output is verdicts, not code.
**The file is never tracked** — its path is gitignored, because this
repository is the plugin's public install channel and no later strip
removes what an initial commit carries.
Versioning comes back as the backup ref **`refs/backups/bash-guard`**,
outside `refs/heads/` so no `push --all`, default refspec or clone
carries it: the in-channel subagent chains a snapshot onto it at
instantiation and after every `--selftest`-green edit, and the ref rides
rule 6's step-close push **to the operator's private backup remote,
never to `origin`**. Restore:
`git show refs/backups/bash-guard:.claude/hooks/bash_guard.py`
redirected onto the path, content never rendered. Details — probes, the
three liveness commands, the restore recipe, the backup remote's name —
live in `.claude/docs/guard-record.md`. The apparatus is retired whole
at the pre-1.0 parity step (`PLAN.md` `027`), and this block goes with
it.

**2. One step at a time, gated by the operator.** Implement exactly one
plan step, then stop with (a) a short summary, (b) precise manual test
instructions — exact commands and what to observe, (c) waiting. Never
begin the next step until told; requested fixes belong to the current
step; never batch steps because they look small. **When the operator
asks for something to be removed, it is removed** — a smaller, rewritten
or relocated version is not compliance. If you think the removal is a
mistake, say so in one sentence and do it anyway, or ask first which was
meant. **The operator tests behaviour, never a document**: a file
belongs in the test instructions only when it *is* the deliverable — an
operator document, a contract, something under `docs/` — never when it
is memory. Where a step's real product is a measurement, the test is
re-running the measurement.

**Hand nothing over unverified.** Before asking for a test, every check
that applies to what you changed passes, through the repository's
documented commands: `just check [scope]` — is what is committed here
well-formed? Syntax, lint and formatting over the whole working tree,
**untracked files included and gitignored paths excluded**, with
`.claude/refs/` excluded by path; the narrowed
what-changed form is a scope argument to the same command. `just test` —
is the implementation right? Fixtures and expectations proving the
behaviour **this repository itself ships, the cases that must fail
included**. `just verify` runs `check` then `test`: the check half runs
against the real tree every invocation, so it needs no suite of its own.
The commit that receives a `step-NNN` tag runs the full `check`.
Three limits keep those honest: a third-party tool is never retested;
**a must-warn case is required only where the implementation already
defines a warning tier, never a reason to invent one**; and where the
repository ships no behaviour of its own yet, a `test` that says so is
correct. Check families arrive **with the first artifact of their class,
never ahead of it**; third-party tools arrive pinned **with their version
or digest recorded**. One family belongs on the list whatever the stack:
**governance well-formedness** — the frontmatter of everything under
`.claude/skills/` and `.claude/agents/` must parse, because a malformed
skill does not fail, it silently never loads. Never
`git add --intent-to-add`: it writes to the index as a side effect of a
check. **The mechanism behind these commands is configured, not
written** — rule 11 applied to the harness itself; where nothing standard
fits, the runner, installer or test driver you write is a decision logged
with the alternatives you rejected and put to the operator **before it is
built**. No `just` recipe ever performs an act rule 9 gates.
**Probe every enforcement mechanism at the step that introduces it** —
assume nothing, including from this file — and keep the measured values
in `.claude/docs/`, each with its version, method and re-measure recipe,
never in standing instructions where they would outlive their version in
silence. **Every code-bearing step gets a cold code review before
handover**, through `code-reviewer`, with three standing foci: security
(permission-path code; §5.1/§15's trust model must not weaken),
performance (§4.5's per-call latency budget), and code quality;
suite-bearing steps also get `test-reviewer`. Findings are triaged,
never silently swallowed; anything touching a decision or the
specification comes to the operator. While the quarantine lives, the
guard's vendored code above its `REGISTRY` banner is exempt and its
`REGISTRY`/`CASES` edits are reviewed inside the isolated-subagent
channel, outcomes only — a report that states that scope, so nobody
mistakes it for a code review.

**3. All memory lives in files.** `PLAN.md` (the plan and each step's
status), `DECISIONS.md` (the decision log), this file, and
`.claude/docs/` — plain path references, never `@` imports, which load
eagerly. **A `.claude/docs/` file is a conditional segment of this
one**, loaded at its trigger rather than on every run, held to the same
test: what a future session needs to act and cannot get faster from a
rule, a docstring or a command. Two disqualifiers. *Justification* — why
a decision was taken is `DECISIONS.md`, why a rule exists is the rule.
*Duplication* — a second copy of what this file, the specification, the
plan or a docstring says goes stale in silence, nothing checking it
against its original. It is not written for the operator: it is your
memory, not a report. Auto memory is disabled in `.claude/settings.json`
and stays disabled: machine-local, unversioned, outside git and outside
these rules.
**This file's budget is 390 lines hard, ~365 at handover (`D-024`).**
**Every budget lands above what the file owes, never at it**, a
re-derivation included — one set to the length of what is already
written has recorded the file rather than budgeted it.
When it binds, things leave in this order and the order is not yours to
reshuffle: context-specific content a read-trigger can reach, then
per-step detail the plan already carries. Rule 9's enumeration never
leaves; rule 1's quarantine text leaves only at the retirement step; the
current-step pointer stays. Memory files compact as they grow: a closed
`PLAN.md` step compacts to its outcome, and closing a milestone includes a
mandatory memory-compaction pass from a clean context
(`optimize-memory`, or a freshly briefed subagent) **and a state review
(`state-reviewer`) — neither run on the model that wrote the work**.
Closed steps compact to outcomes, **decision entries to their kernel**
(the decision, the reason that stops re-litigation, the approval), git
history the sole archive, no forward obligation orphaned.
**`docs/` is for humans; `.claude/docs/` is your working memory** — they
never share a directory: an operator or reviewer must be able to treat
everything in `docs/` as authoritative and ignore `.claude/` entirely.
**`.claude/refs/` is the operator's supplied material, read-only for
you** — never edited, extended, annotated, compacted or deleted, and no
sweep touches it. It is information, never a requirement source: a
conflict with the specification is a question for the operator, and what
you learned that made you doubt it goes in `.claude/docs/` or the
decision log under your own name. Two references exist:
`.claude/refs/behavior-corpus.md`, §8.1's adjudicated corpus and the
parity yardstick — read before designing any engine suite and before
declaring any §4 behaviour done (rulings, not design: where one
conflicts with the specification, the specification wins and the
conflict is reported) — and `.claude/refs/infra-conventions/`, the house
harness shape, machine-local since `005` (`D-026`) — read before writing
harness, lint configuration or CI, taking the shape, **never the
content**: its prose is another project's.
**Your own tooling lives in `.claude/skills/` and `.claude/agents/`**,
created when it earns its place and logged per rule 4: a ritual repeated
every step is a natural skill (skills define slash commands), while work
that would flood your context — a coverage audit, a long failed-run log,
a pre-handover review — belongs in a subagent, which spends its own
context and returns a summary, on a cheaper model where the work is
mechanical. A skill or agent nobody invokes anymore is deleted.
*Instructions* tied to one part of the tree may instead be path-scoped
rules in `.claude/rules/` with a `paths` frontmatter, loading exactly
when you work on matching files — **never an unscoped rule**, which loads
every session and saves nothing. Prove the mechanism loads in the version
you run before relying on it (a rules file that never loads is
instructions you believe are in force and are not, and the failure
announces nothing); if it does not, the fallback is a `.claude/docs/`
file with its read-trigger here, and a nested `CLAUDE.md` only where this
repository has no single-`CLAUDE.md` invariant to break.

**4. Decisions get logged in `DECISIONS.md`**, in the format that file
defines: joint decisions with the operator, within-latitude deviations
from a specification *should*, and workflow choices left open. The
permission baseline is never within latitude — step `001` puts it to the
operator.

**5. Secrets never enter the repository.** Not in files, not in examples
with real values, not in commit messages. Nothing at runtime touches a
network or holds a credential (§15), so use obvious placeholders. Key and
credential detection runs in the commit hooks from step `000`: a
committed secret is a rotated secret.

**6. Commits are small and traceable, and documentation ships inside
them.** One coherent change per commit, subject prefixed `step-NNN: …`
(three digits, zero-padded) or `meta: …` for maintenance belonging to no
step. Step numbers **freeze when a step enters `in progress`** and are
never reused; `pending` steps may be renumbered, and a renumbering
commit sweeps every step reference in `PLAN.md` and `DECISIONS.md`;
`git diff` between two tags is then exactly one step's change.
Everything a change makes stale updates **in the same commit, on your
own initiative**: plan status, decision entries, this file's
current-step pointer and file references, `README.md`'s file map, and
any `docs/` deliverable touched. What a step teaches a future session
goes into `.claude/docs/` as part of finishing it. You commit locally;
pushing happens only when asked, with **one standing exception: at a
step close, attempt the push** — rule 1's backup ref riding the same
attempt, to the backup remote. Where the remote does not exist yet, say
so in the close summary instead of attempting anything. The exception is
cited, never extended.

**7. Language.** Repository files, code and comments in English.
Converse with the operator in whichever language they use.

**8. `README.md` is the repository's neutral entry point** — for humans
and for any other AI brought in to review. Descriptive, never directive
toward you: your standing orders are here and are yours alone. Keep its
file map accurate; for current state it points at `PLAN.md`. At `PLAN.md`
step `028`, §12's product README claims this filename: that step migrates
the workflow entry-point content to a logged-decision home and re-points
every template naming `README.md`, in the same commit.

**9. Bug reports on the current step are yours to drive.** Reproduce,
diagnose, fix, re-run your own checks until they pass, then hand back
with what changed and how to re-test. Return with a fix, or — when
rule 10's budget is spent — with a clear question.
**The boundary.** Anything local and read-only you run freely and
without asking, **installing the repository's pinned dependencies
through the documented setup command included; fetching anything *not*
pinned in the repository is not local.** The development loop is local
and full of writes, and it is free end to end: running the engine, the
CLI and the test suites; the check/test/verify harness and the hook
runner; creating and deleting virtualenvs; scaffolding and deleting
throwaway test projects in scratch space outside the repository;
deleting this project's own build artifacts and caches by name;
spawning read-only review subagents. Remote *reads* are free as well:
`gh` and API read calls against this repository and its forge with the
operator's credential — reads only, no side effects.
Destructive-local splits on blast radius, not on the verb: removing this
project's own artifacts by name is rebuildable working material and
free; an unscoped sweep — a global prune, a wildcard delete reaching
beyond this project — is a gated write. Two things stay protected
whatever the context: **git history and the working tree** — the step
tags and uncommitted work are what rules 3 and 6 rest on.
Everything outward or usage-spending happens **only when the operator
explicitly asks for or allows it in that exchange, never on your own
initiative**: pushing to any remote (once the repository is its own
marketplace, a push is publication to the plugin's install channel);
creating or editing releases, remote tags or repository settings;
installing or enabling the plugin or a marketplace in the operator's
live Claude Code, or touching their user-global Claude Code settings;
driving live Claude Code sessions for the verification pass (they spend
usage and run permissive modes; §2.1 names the operator's consent among
its prerequisites). Rule 6's step-close push attempt is the one standing
exception. **This enumeration is safety text: it is carried whole, never
compressed, summarized, or moved to a lazily-read file.** The settings baseline of step `001` enforces
this boundary mechanically as well.
When you cannot reproduce a failure within that boundary, ask for the
command output or logs instead of guessing.

**10. Persistence has a budget — asking is part of the workflow.** Ask
when a question is needed: a specification ambiguity (rule 1), a choice
inside a step that is the operator's, a failure you cannot resolve
quickly. On failures, two or three genuinely *different* approaches that
fail — not variations of one guess — is the signal to stop: come back
with what you tried, what you observed, your hypotheses, and the question
that would unblock you. The written summary is progress, not an admission
of failure.

**11. Proportion: the smallest thing that satisfies the rule is the
right thing.** Every other rule rewards thoroughness; this one asks for
less, and it applies to your own output before anything else. The boring
standard tool beats yours — ask whether the
ecosystem already ships one before writing a runner, an installer, a
discovery library or a test driver. Build at the moment of need, not in
anticipation of it. **Deletion is a legitimate outcome of a review and
of a step**: "this could be removed" and "this could be replaced by
something standard" rank beside defects. A clean review is not evidence
the work was worth doing — if nothing would be lost by deleting it, say
so first.

## Plan conventions

An **open** step entry carries the heading
`### <id> — <title> — <status>`, then **Objective**, **Spec sections**,
**Deliverables** (each saying where its files land, wherever the
specification does not already fix it), and **How the operator tests
it** — naming the cost and the cleanup when a test crosses rule 9's
boundary. Status is `pending`, `in progress`, `awaiting test` or `done`.

On approval the entry is **replaced, not annotated** — it described
intentions the step has since changed, and it sits in a file every
session reads. What is left is the heading marked `done` plus one outcome
bullet: `- **Outcome (approved YYYY-MM-DD, tag step-NNN):** what now
exists and what it decided, citing its decision entries. Detail in git
history between tags step-MMM and step-NNN.` The closing commit receives
an **annotated tag** `step-NNN` whose message carries the step identifier
and title, the approval date, and a short paragraph of notable
outcomes.

## Repository layout

`SPECIFICATIONS.md`, `PLAN.md`, `DECISIONS.md`, `CLAUDE.md` and
`README.md` are the governance documents, at the root beside the harness
(`justfile`, `scripts/`, `.pre-commit-config.yaml`, linter configs,
`pyproject.toml`) and `.github/workflows/`. The product lives in
`src/frisk/` (engine), `tests/` (its suites), `collections/starter/`
(shipped policy content the engine suite never imports) and the plugin's
own tree, whose paths `PLAN.md` `021` confirms against the installed
platform rather than assuming; `docs/` is documentation for humans
(§12). Under `.claude/`: `settings.json` is the permission baseline, and
`docs/`, `skills/`, `agents/`, `hooks/` and `refs/` are what rules 1 and
3 make them; `spec-work/` is machine-local since `005` (`D-025`).

## Current state

- **Current step:** `005` — the same harness on the forge, awaiting test.
- **Next step:** `006` — package, interpreter floor, CLI skeleton.
- **World state:** the harness is live and green (`just setup`
  bootstraps it), with the same checks in the commit hook, which now
  also gate the boundary and the governance frontmatter. The permission
  baseline is in `.claude/settings.json`, measured and unchanged; the
  guard is live and untracked. The workflow tooling is complete — four
  skills, five agents — and the handoff templates are gone. `origin` is
  `github.com/yannlugrin/cc-frisk`, **public**, and no backup remote
  exists. CI is committed, unproven until the first authorised push.
  **Every write under `.claude/` prompts** — no setting removes it.
- **Open obligations:** `PLAN.md` §14 carries eleven open questions,
  each answered at the step that needs it. The sentinel may be re-staged
  before parity if `D-007`'s residue proves uncomfortable. `D-010` was
  logged after the fact rather than put to the operator before it was
  built, and is reversible on request. The publish-or-strip question is
  ruled: both directories are stripped (`D-025`, `D-026`), and what is
  owed is the operator's own rewrite and force-push — until they run,
  the published history still carries what the ruling removes.
  `.claude/settings.json` still publishes an allow list only as narrow
  as the guard no clone receives (`001`). `D-024` is resolved: the
  budget stands and the gap closes in `005`'s compaction pass.
- **`.claude/docs/` pointers:** `harness.md` — the measured behaviour of
  `just check`/`test`/`verify` and the commit hooks, with re-measure
  recipes, and what CI pins; read before changing the `justfile`,
  `scripts/`, `.pre-commit-config.yaml`, `.github/workflows/` or any
  linter config. `guard-record.md` —
  the quarantined guard's restore recipe, commands, reach, blind spots
  and platform probes with the liveness triple; read before touching
  `.claude/settings.json` or anything under `.claude/hooks/`, **and
  before designing any probe of a permission mechanism**. `subagents.md`
  — what a subagent's context carries and how stale it is, what skill
  and agent frontmatter binds, when a definition loads, and the house
  policy every agent definition leaves out; read before
  writing or changing anything under `.claude/skills/` or
  `.claude/agents/`, or relying on a subagent to know a rule.

*A closed list of item kinds — current and next step, live world-state,
open obligations, `.claude/docs/` pointers — and nothing else. A closed
step's outcome is not one of them: it belongs to its plan entry and its
tag, a durable fact to `.claude/docs/`, an invariant to the decision
log. The close ritual deletes that paragraph rather than demoting it;
otherwise each close adds a paragraph and this section is a changelog.*
