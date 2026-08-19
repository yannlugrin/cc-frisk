# Implementation plan — frisk

The ordered plan for implementing `SPECIFICATIONS.md`. It is derived from
the specification and from the operator's bootstrap instructions; where
the two speak, the specification governs the product and the operator's
instructions govern the workflow.

## How to read this plan

- **Steps** carry three-digit identifiers (`000`, `001`, …). A number
  freezes when the step enters `in progress`; `pending` steps may be
  renumbered. `PLAN.md`'s order, not the numbering, defines the
  sequence.
- **Status** is one of `pending`, `in progress`, `awaiting test`,
  `done`.
- Each open step states its **objective**, the **spec sections** it
  implements, its **deliverables** (with the directory each lands in),
  and **how the operator tests it**. Where a test crosses the boundary
  of rule 9 (usage, shared state, the operator's live Claude Code), the
  entry says so, what it costs, and how to clean up.
- On approval a step's entry is **replaced** by its heading and one
  outcome bullet. The detail lives in git history between tags.
- **Milestones** group steps. Closing a milestone triggers a state
  review and a memory-compaction pass (`CLAUDE.md`, rule 3), neither run
  on the model that wrote the work.

## 1. §13 re-inventory — the pre-1.0 parity bar

Required as this plan's first artifact (§13). §13's pre-1.0 bar has only
ever grown; each item below is assessed for whether its **placement at
parity** still earns it. The items themselves are requirements and stay
owed whatever the ruling — only the stage is challengeable. The operator
rules on this section at the plan review, before step `000`.

Recommendation shorthand: **keep** = stays at pre-1.0 parity; **move** =
proposed for 1.0.

| # | Bar item (§13) | Assessment | Recommendation |
|---|---|---|---|
| 1 | Engine behaviors of §4 to the extent the behavior corpus exercises them | This *is* parity: the corpus is the yardstick (§8.1) and without it parity cannot be declared at all. Nothing to challenge. | keep |
| 2 | A configuration able to express what the starter registry and the corpus's policies need (§5) | Same. The corpus's three policy contexts (git/docker starter, stub fixtures, infra tools) define the minimum expressible surface; a narrower config cannot reproduce the rulings. | keep |
| 3 | The hook with fail-closed runtime (§7.1) | The hook is the product. Fail-closed is a few lines around the decision call and is what makes a broken config loud instead of silently absent. | keep |
| 4 | Control-structure routing minimum of §4.3 (keyword-led segments treated as unparsed) | Accreted onto the bar, and it earns its place cheaply: it is one branch in the splitter, and without it `for f in *; do rm -rf "$f"; done` reads as a command named `do` — silent under §6.1's broad allows. The *full* treatment (bodies judged, function definitions) stays 1.0. | keep |
| 5 | Both classes of §7.2 — the unloadable-config deny and the cases-fail-on-config-change deny | Class one is §7.1 restated at load time and is inseparable from item 3. Class two is genuinely accreted, but §13's own argument holds: once item 6 runs the project suite inside the hook, the config-change trigger is a change-detection check in front of machinery that already exists. The dial and its warn-surfacing are the only real cost. | keep |
| 6 | §7.3's engine-version trigger | Accreted, and the strongest of the accretions: the prototype was project code that could not change without the operator editing it, while the plugin channel updates silently from day one. Deferring it would ship the one failure mode the plugin introduces and the prototype never had. | keep |
| 7 | Gates one and two runnable (engine suite in the plugin's CI; liveness and selftest reachable from the project) | Gate one is how the engine is proven at all (§3.1: users receive it proven). Gate two is the project-facing discipline the whole product rests on. Neither is deferrable without deferring the claim. | keep |
| 8 | The check/explain command in at least its verdict-and-citation form (§9) | Keep — and note a placement *gain* rather than a challenge: `explain` is also the only way the operator can hand-test each engine step, so this plan builds a minimal `explain` at the engine's first step rather than at the end. §9's "show its work" (the analysis display) is a *should* and is **not** on the parity bar; this plan stages it at 1.0. | keep |
| 9 | Enough of the scaffold and pairing guidance — even in guided-manual form — that adoption is possible without archaeology | Keep, at the guided-manual floor §13 itself grants: a scaffold command that writes the config directory, the project entry point, the starter registry, the starter cases and the API-generation declaration, plus written pairing guidance. The *skill* wrapping it (§10's full loop) stays 1.0. | keep |
| 10 | A minimal README and SECURITY.md, with the "in development, install only for testing" warning | Non-negotiable for a permission-path tool's first public tag; §12 already stages the other four documents at 1.0. This plan brings the warning and a minimal SECURITY.md *earlier* than the tag — see step `021`, which is where the repository first becomes installable. | keep |

Three further placements, stated so the ruling is complete:

- **The starter registry's docker shape (§5.4)** is a *should* in the
  specification ("a small set of additional common tools… docker is the
  recommended candidate"). **Move** — out of the shipped starter registry
  entirely (`D-009`, the operator's ruling). An earlier draft of this
  plan argued it was pinned by the corpus and could not be deferred.
  That argument confused two different things. The corpus's context A
  binds the **engine and the configuration surface**: docker's handoffs,
  aliases, publish-capable build flags and compose forms are exactly what
  bar items 1 and 2 owe, and they are reproduced as test fixtures under
  `tests/corpus/` against **test-only declarations** — which is not a
  choice but a requirement, §8.1 forbidding engine tests to run against
  real-tool starter rules at all. What the corpus never speaks to is what
  the *scaffold* writes into somebody's new project. A rule set that
  proves the engine can express docker policy is not a reason to gate
  docker in every project that adopts frisk on day one. The capability is
  owed at parity and stays; the default content is not, and does not.
- **The once-per-session visibly-inert notice (§5.4)** is already staged
  at 1.0 by §13 itself, with the residue stated (a vanished config
  before 1.0 is caught only by the sentinel, where adopted). This plan
  carries that staging unchanged and names the residue in the interim
  honesty text. **No change proposed.**
- **The sentinel (§7.4) and its kill switches are not on the pre-1.0 bar
  at all**; §13's 1.0 bullet names "the sentinel offer" explicitly. An
  earlier draft of this plan built them before parity. They are staged
  at 1.0 (step `035`), which is where §13 puts them — a correction to
  the plan, not a challenge to the specification. The consequence is
  stated in the honesty text and in the parity statement of step `026`:
  before 1.0, §7.5's "plugin absent on this machine" and "config absent
  where one existed" rows have no catcher.

**Net recommendation: the bar stands as §13 draws it.** Every accreted
item survives its own challenge, three of them (4, 5-class-two, 6)
because they are cheap riders on machinery the bar already owes, and one
apparent deferral candidate (docker) turns out to be pinned by the
parity yardstick. The operator's ruling on this table is logged as
`D-004`.

## 2. Milestone 1 — Repository foundation

Six steps, one milestone, drawn by what a working repository needs
rather than by cost class, and ordered by dependency: the tooling of
`003`/`004` cites the boundary that `001` enforces, all of it runs under
the harness of `000`, and `005` puts that same harness on the forge. The
bootstrap instructions prescribe four steps; this plan splits two of
them (`D-003`), and CI stays **last within the foundation**. The
repository is not bootstrapped until its CI has run green. ("Leaves this
machine" means shared, public state — the forge; rule 6's close-riding
backup-ref push to the operator's private backup remote is earlier and
does not count against this ordering.)

### 000 — The harness, local only — `in progress`

**Objective.** A repository that can say, in one documented command,
whether what it contains is well-formed — and can prove it from a fresh
clone.

**Spec sections.** None (workflow foundation). Constrains everything
later.

**Deliverables.**

- `.gitignore` at the repository root: the existing entries carried
  forward, not replaced (`.claude/worktrees/`, `__pycache__/`, both
  guard paths), plus test/type/lint caches (`.pytest_cache/`,
  `.mypy_cache/`, `.ruff_cache/`), virtualenvs (`.venv/`), build
  artifacts (`dist/`, `*.egg-info/`), coverage output,
  `.claude/reviews/` (the reviewer templates write there and an
  untracked report would block every clean-tree precondition
  downstream), and `CLAUDE.local.md`. `.claude/worktrees/` stays ignored
  for a reason worth keeping: an isolated worktree materializes inside
  the repository, and a commit made while one exists swallows the
  checkout — which has happened.
- `requirements.txt` at the root — the pinned toolchain, installable
  through one documented setup command. Third-party tools arrive
  pinned **with their version or digest recorded**; for a third-party
  binary that pin-and-record is the whole coverage obligation.
- `justfile` at the root and `scripts/` beside it (`setup.sh`,
  `check.sh`, `test.sh`): `just setup`, `just check [scope]`,
  `just test`, `just verify`. **`check` takes a scope argument and is
  one entry point, never a second recipe** — the whole-tree gate is the
  default and the narrowed what-changed form is an argument to the same
  command, because two recipes hold two lists and will eventually differ
  in *what* they look for rather than only in how much.
- **The mechanism behind those commands is configured, not written**
  (rule 11 applied to the harness itself): `scripts/check.sh` is a thin
  delegate that computes the file list and hands it to
  `pre-commit run --files …`. It is glue, not a runner: the hook
  definitions, their pins and the path exclusions all live in
  `.pre-commit-config.yaml`, in one place. The file list is
  `git ls-files --cached --others --exclude-standard` — passed
  explicitly because runners that enumerate from git,
  `pre-commit run --all-files` among them, see only what git already
  knows about, and **a lint error in a file that exists but was never
  added to the index must still fail `check`**. Never
  `git add --intent-to-add`: it writes to the index as a side effect of
  a check, turns `?? file` into ` A file` in `git status --porcelain` —
  the output the handover and approve rituals read for their clean-tree
  preconditions — and lets the next `git commit -a` sweep the file into
  an unrelated commit.
- Standing path exclusions, keyed on the path and not on tracked status:
  `.claude/spec-work/` (no session's reading material, rule 1) and
  `.claude/refs/` (the operator's supplied material, read-only and owned
  elsewhere — a lint finding there would have no legal resolution: the
  file cannot be edited, and the bend-the-config escape beside it is
  written for the specification alone).
- `.pre-commit-config.yaml` at the root, wired to the **same** harness so
  the local runners cannot diverge, carrying the check families whose
  artifacts exist at this step and no others (rule 2's never-ahead rule,
  **so this step's green gate says nothing about files that are not
  there**): YAML lint (the hook runner's own configuration is the first
  artifact of that class), JSON parse (`.claude/settings.json` already
  exists — and the settings file is the enforcement mechanism itself, so
  a malformed edit fails exactly as quietly as a skill that never
  loads), POSIX-shell lint over `scripts/`, Markdown and prose lint over
  the governance documents (in this repository documents are
  load-bearing), repository hygiene and security from the runner's stock
  collection, pinned — large binaries, merge-conflict markers, and
  secret/private-key scanning per rule 5 — and whitespace/newline
  discipline. The **fixers** live in the commit hook; `check` asserts and
  never repairs, because a check that rewrites the working tree as a side
  effect is the `--intent-to-add` prohibition one step milder.
- Linter configuration at the root (`.yamllint.yml`, the Markdown
  linter's config), shaped after `.claude/refs/infra-conventions/` —
  shape, not content.
- A lint bend for `SPECIFICATIONS.md` if one proves necessary: read-only
  under rule 1, so the lint bends to it, the bend is scoped to that file
  alone and never a global loosening, and **excluding a document from a
  rule is a logged decision, not a quiet config line**.
- Families deliberately absent here, each joining with its first
  artifact: Python and TOML at `006`; governance frontmatter
  well-formedness at `003`; **the CI workflow at `005`** — nothing local
  can exercise a workflow, and a tagged step must not carry an artifact
  its own gate never ran.
- `.claude/docs/` created with whatever this step learns.

**How the operator tests it.** Clone the repository into scratch space
outside the working directory, run the documented setup command, run
`just check` and `just test` (which correctly reports that this
repository ships no behaviour of its own yet), then make one trivial
commit in the working copy and watch the commit hooks run the same
checks. All green. Local and free; delete the scratch clone afterwards.

### 001 — The permission and hook baseline — `pending`

**Objective.** A boundary around this repository's own development: the
Bash guard live, the settings paired to it, and both gated so that a
guard which stops working fails a gate instead of failing quietly. The
whole is proposed for the operator's review as one piece.

**Spec sections.** None (workflow foundation). The guard instantiated
here is **prototype-generation tooling for this repository's own
development**; the product is specified solely by `SPECIFICATIONS.md`,
and nothing about this instantiation — its shapes, names or behaviour —
is an input to that implementation.

**Deliverables.**

*The guard first — the settings take their shape from it, not the
reverse.*

- `.claude/hooks/bash_guard.py`, instantiated from
  `.claude/spec-work/handoff/assets/bash_guard.py` **through the
  isolated-subagent channel of rule 1**: the file never enters the
  implementing session's context, in this session or any later one. The
  subagent reads the module docstring in full, edits only the `REGISTRY`
  and `CASES` blocks, and reports **outcomes** — how to choose between
  *rules* and *grants* per tool, what must land in
  `.claude/settings.json`, what the guard cannot see, and the rule that
  its `GIT` ground rules are the same in every project and are **added
  to, never weakened** — never the file's text, parsing approach or API
  shapes. The file is executable and **untracked**: `.gitignore` already
  carries both guard paths.
- A tool inventory driving that registry: what this project actually
  runs — the harness, `just`, `pre-commit`, `git`, the language
  runtimes, everything the `justfile` shells out to — with each registry
  tool given the acts rule 9 gates **for this project**. Every rule added
  gets a `CASES` entry: `--selftest` fails on a rule no case reaches,
  which is what keeps the intent executable rather than remembered.
- `refs/backups/bash-guard` — the backup ref of rule 1, created here,
  outside `refs/heads/` so no `push --all`, default refspec or clone
  carries it. The in-channel subagent chains a snapshot onto it at
  instantiation (a clean base, before any edit) and after every
  `--selftest`-green edit, using `git hash-object -w`, `mktree` and
  `commit-tree -p` — commands that print hashes, never content. The ref
  uniquely carries this project's `REGISTRY` and `CASES` work; the
  pristine template is recoverable from the operator on request, so no
  local-only window is load-bearing.
- **The step's review shape, which rule 1's quarantine reshapes.** The
  vendored guard code above its `REGISTRY` banner is **exempt** from the
  standing code review: it arrives proven by its own shipped selftest,
  and it is what the quarantine protects. The step's *authored* work —
  the `REGISTRY` and `CASES` edits — is reviewed **inside the
  isolated-subagent channel**, with an outcomes-only report: what is
  gated, what a rule misses, never the file's text. Such a report cannot
  see what reading code would — a mis-spelled rule pattern, the
  `Bash(git push:*)`-misses-`git -C dir push` class. The substitute is
  the mandatory `CASES` entry per rule plus `--selftest`'s coverage
  gate, **and the report states that scope**, so nobody later mistakes it
  for a code review.

*Then the settings*, per the docstring's pairing as the subagent reports
it, landing in `.claude/settings.json`:

- One broad allow per rule- or grant-bearing tool. **Never a wrapper** —
  a broad allow on a command-runner is a broad allow on everything it
  runs the moment the guard is dead — and **never a tool the registry
  denies wholesale**, whose broad allow buys nothing alive and is pure
  liability dead.
- **No `ask` rule for anything the guard gates**: a matching `ask`
  prompts even where the guard says allow, so it cancels every carve-out.
- **No prefix rule restating a guard decision**: a prefix is strictly
  weaker and gives two sources of truth. `git push` is **not** an
  exception — it is gated in the guard's ground rules, and a prefix
  restatement misses `git -C dir push`.
- **One deliberate exception**: a short `deny` backstop for the acts
  that cannot be undone — `git push --mirror` among them, which besides
  deleting remote refs wholesale is the one push that would carry the
  backup ref to `origin`. A hook fails open, and a prefix rule that
  binds without it is worth more than the duplication costs. Kept short
  enough that the exception stays visible as one.
- The **push tier**: the ordinary push — the one the close ritual
  attempts — **asks and is never denied**, wherever it is expressed,
  because a denied pattern cannot be approved in the very exchange
  rule 9 relies on. The unrecoverable spellings — force, mirror,
  ref-delete — are the *denied* set, in the guard's ground rules and the
  backstop alike. `deny` stays reserved for what has no authorised use at
  all, each named in the proposal.
- Settings' `ask` tier kept for tools the guard has no registry entry
  for (`curl`, whatever this project reaches for outside it).
- **The boundary protects its own files**: native file-tool rules at the
  **ask** tier gating edits to `.claude/settings.json` and
  `.claude/hooks/`, inside this same proposal. Ask, not deny — a deny
  would end the guard's own maintenance channel and the baseline's own
  evolution with no unlock path. Under a mode that auto-accepts file
  edits, one silent, well-formed settings edit that drops the push gate
  turns the close ritual's standing push attempt into an unprompted
  publish, and the governance family's parse and hook-path checks catch
  malformation, never a well-formed loosening.
- Auto memory is already off (`autoMemoryEnabled: false`) — **keep it
  off**.
- The **permission mode** the operator is expected to work in, named in
  the proposal as a committed setting rather than a per-session choice,
  because it decides how much the rest has to carry. The mode set and
  what each mode does to an unmatched command are properties of the
  installed version — modes exist that prompt, that auto-approve, and
  that judge by classifier and can deny outright, three different answers
  to what backs the guard's silence — so the list is taken from the
  running version, not from any document, and the mode proposed is probed
  at `002`. The key's spelling (`permissions.defaultMode` at last look)
  is illustrative like the mode list and is verified by the same probe.
  The mode is *set* rather than worked around — if a mode auto-accepts
  file edits, that is what removes the need for a blanket edit
  allowance — and it decides whether the mode-disabling keys belong in
  the baseline at all.
- Say plainly, in the proposal, **what a dead guard would leave open**: a
  broad allow plus a dead hook is a wider surface than a narrow allow
  list ever was, and the `deny` backstop exists exactly there.
- A rule of this baseline, recorded with it: **no `just` recipe ever
  performs an act rule 9 gates.** A `PreToolUse` guard judges the command
  it is given — `just release`, never the push inside it — so a gated act
  behind a recipe name bypasses the gate unseen. Gated acts live in CI or
  in a command the operator invokes directly.

*Then both gates on the guard*, because a hook fails open and the two
gates ask different questions:

- `bash_guard.py --liveness` in the pre-commit lint: the file is
  executable, the registry builds, every rule and grant is well-formed,
  a payload still comes back as a verdict. No behaviour cases, so a lint
  stays a lint, and the silent deaths — a syntax error from an edit, a
  lost `+x`, a rename — fail the commit. **One wiring constraint**: the
  guard is machine-local, so nothing *committed* may reference it in a
  way that fails where it is absent — CI and fresh clones never have it,
  this machine always should. The gate is loud locally and inert
  remotely; the mechanism is named in the proposal.
- `bash_guard.py --selftest` in the *test* entry point: liveness, then
  every case, then coverage — a rule or grant no case reaches fails it.
- The governance check family gains one assertion: **the hook path in the
  settings resolves.** A path naming a file that is not there leaves
  valid JSON, a settings file that loads, a green lint, and a guard that
  never runs.
- `.claude/docs/guard-record.md` created with what this step fixes: the
  restore recipe, the backup remote's name, and the tool inventory's
  outcome. `002` completes it with the probe results and the liveness
  commands.

**How the operator tests it.** Review the proposal as a whole — the
registry outcomes, the settings diff, the named `deny` set, the proposed
permission mode, and the dead-guard statement. Then `just verify` green
and the guard's `--selftest` green. Then prove the backup ref: run the
restore recipe
(`git show refs/backups/bash-guard:.claude/hooks/bash_guard.py`)
redirected onto a scratch path, confirm the file comes back byte-identical
and that its content was never rendered into the session.
**Crosses the boundary**, mildly: the settings edited here are the
operator's own working project's, and the hook registration takes effect
in their live Claude Code. Cost: the permission baseline changes under
them. Cleanup: revert `.claude/settings.json` if the proposal is
rejected; the guard file is untracked and is deleted by hand.

### 002 — The probe campaign and the guard record — `pending`

**Objective.** Prove what each enforcement mechanism introduced at `001`
actually does in the version being run, and write down what was
measured — because a mechanism that turns out to enforce nothing is a
guard on paper, and the failure announces nothing.

**Spec sections.** None (workflow foundation).

**Deliverables.**

- The probe campaign for this step's mechanisms, assuming nothing —
  including nothing from the bootstrap instructions or from `CLAUDE.md`.
  At minimum: whether the settings keys set at `001` are honoured; which
  spelling of a file-path rule the file tools actually match; whether the
  hook is reached at all; what an unmatched command does under the
  proposed permission mode; and **whether a hook `ask` still prompts**
  under it — the close ritual attempts its push in reliance on that, and
  a gate that has stopped gating says nothing about it. Confirm too that
  this version honours `autoMemoryEnabled`, on the same reasoning: an
  unrecognised setting is ignored in silence.
- **The restart is part of the method.** Settings and hook changes may be
  picked up only at session start, so a probe run in the session that
  made the edit can report a false "not enforced". The recorded
  re-measure recipe says so.
- `.claude/docs/guard-record.md` completed: every claim a measurement,
  each with **the version it was taken on, the method, and a short
  re-measure recipe** to re-run after a Claude Code update. The values
  measured live here and **not** in `CLAUDE.md` or any standing
  instruction — standing instructions have no staleness discipline, and a
  version-stamped fact restated there outlives its version in silence.
- A **liveness check the session rituals of `003` can run**: three
  commands — one that must run silently, one the guard *grants*, and one
  it must **refuse, naming the rule that read it**. The third is the only
  one that says the hook is reached at all: if it merely prompts, the
  hook is not wired and the deny backstop is all that is left, while the
  guard's own `--selftest` and `--liveness` would still pass — they
  answer whether the file is correct, not whether anything calls it.
- The step summary reports what each mechanism actually did, **including
  the ones that turned out to enforce nothing**.

**How the operator tests it.** Read the record, then run the three
liveness commands and observe: silence, a grant, and a refusal that names
its rule. A session restart falls between `001`'s edits and these probes
and the step's instructions say where.
**Crosses the boundary**: the probes run in the operator's own live
Claude Code, against their own working project's settings. Cost: session
restarts, and — if the proposed mode differs from the one in use — a
temporarily altered permission mode. Cleanup: restore the mode and any
probe-time settings change; the record itself is the deliverable and
stays.

### 003 — Workflow tooling, part one: the probes and the skills — `pending`

**Objective.** Measure what a subagent can actually see, then instantiate
the four session rituals under the answer.

**Spec sections.** None (workflow foundation).

**Deliverables.**

- The probes for this step's mechanisms: an agent's `tools:` frontmatter
  (does it restrict anything at all?), and **whether `CLAUDE.md` reaches
  a subagent's context at all** — one exchange with the first agent this
  step spawns ("quote rule 9's opening line"). Every reviewer agent's
  boundary rests on the answer, which is why it is measured before the
  agents are written. **Pre-committed unfavourable branch**: if
  `CLAUDE.md` does not reach a subagent's context, each agent's body
  carries the gated set inlined — a logged decision naming the
  single-source-of-truth cost — never a citation to a rule the agent
  cannot read. Results land in `.claude/docs/`, version-stamped, with
  the re-measure recipe.
- The four skills at `.claude/skills/<name>/SKILL.md`: `orient`,
  `resume-step`, `handover-step`, `approve-step` — instantiated from
  `.claude/spec-work/handoff/assets/`, every placeholder filled with this
  repository's real commands and paths, including the governance set
  (`{{PLAN}}`, `{{DECISIONS}}`, `{{SPEC}}`, `{{STEP_ID}}`,
  `{{VERIFY_COMMAND}}`). A template arrives with those as placeholders on
  purpose: a leftover one is visible, while a plausible wrong filename is
  not. A placeholder whose referent does not exist yet is seeded from the
  specification's own vocabulary and kept current under rule 6 as the
  system materializes — the standing examples being `resume-step`'s
  world-state checks and, at `004`, the state reviewer's architecture
  vocabulary and inspection commands.
- **Where a template's own enumeration of a routine is narrower than the
  rule it claims to execute, the rule wins and the enumeration is
  rewritten to match.** This repository is single-track: where a
  template's body carries multi-track guidance, that block is dropped
  rather than reconciled.
- `handover-step` gains rule 2's code-review step for code-bearing steps
  and the test-review step for suite-bearing ones — the standing gate's
  carrier is the ritual that performs handovers, and a mandated gate
  outside that ritual is a gate that silently skips — and names
  `step-reviewer` as its plan-and-spec-conformance pass, which is that
  agent's only trigger.
- `approve-step`'s push step gains the backup ref's push to the backup
  remote, on every close — resolving the remote by name and reporting its
  absence rather than failing on a machine that lacks it — and its
  step 5 names the milestone pair (`state-reviewer`, `optimize-memory`)
  directly.
- The governance well-formedness check family joins the harness here,
  with its first artifact: **the frontmatter of every file under
  `.claude/skills/` and `.claude/agents/` must parse.** A malformed skill
  does not fail, it silently never loads. The parse check has no standard
  ecosystem tool, so a few-line custom check is **sanctioned** by rule 11
  here, and it is the whole of what the rule requires. Two *shoulds* ride
  beside it, worth doing where they are exact: an agent name checked
  against `.claude/agents/` and a path checked against the tree; and,
  once `.claude/docs/` holds several files, a `§N` pointer with its
  section title checked against the target document's headings — in the
  instantiated skills and agents only, the one class where a pointer is
  followed by a session that will not re-read the target, with read-only
  documents outside its scope (a check that can go red inside a file
  nobody may edit is a check nobody can turn green) and one recognised
  citation shape, never prose. **Scanning prose for backticked tokens and
  asserting each one resolves is prohibited**: it has been built and
  regretted — a false-positive machine that grows worse as the repository
  does, and once mandated by a rule it cannot be deleted without amending
  the rule.
- An instantiated file must never name a skill or agent that was not
  adopted: trim the reference or adopt it, because a dangling name is a
  ritual that silently skips a step. The five agents arrive at `004`, so
  a reference to one of them is forward-looking by one step and is
  resolved there.

**How the operator tests it.** Invoke each of the four skills and watch
it do what it claims — real invocations of the session-start, resume and
handover rituals; the close ritual proves itself at this very step's
close, its trigger being any step approval and `003`'s the first after it
exists. Read the probe results. A new skill may only be picked up at
session start, so the instructions state where the restart falls.
**Crosses the boundary**: spawning the probe subagent spends usage, and
the restart is in the operator's live session. Cost: one short subagent
exchange. Cleanup: none.

### 004 — Workflow tooling, part two: the agents — `pending`

**Objective.** The five reviewer and maintenance agents, written under
`003`'s measured answer about what a subagent can read — and the end of
the templates directory.

**Spec sections.** None (workflow foundation).

**Deliverables.**

- Agents at `.claude/agents/<name>.md`: `step-reviewer` (whose trigger
  `003` wired into `handover-step`), the milestone pair `state-reviewer`
  and `optimize-memory` (the foundation is one milestone, so a milestone
  close arrives whatever later grouping applies, and both must exist
  before it arrives rather than be improvised at the boundary), and
  rule 2's review pair `code-reviewer` and `test-reviewer`, certainties
  from the engine's first step on. A recovery ritual created during the
  crisis it is needed for is too late.
- `code-reviewer` is adapted **twice**: to carry the three standing foci
  (security — permission-path code, the §5.1/§15 trust model must not
  weaken; performance — §4.5's per-call latency budget; code quality),
  and to swap its on-request, operator-named-files invocation contract
  for rule 2's **standing per-code-step gate**.
- `optimize-memory`'s plan-compaction section reduces to verifying each
  closed entry is compacted and reporting any that is not, since
  `approve-step` compacts at every close; its whole-carry protections —
  never-compress and budget-yield alike — extend to rule 1's quarantine
  text beside rule 9's boundary enumeration, for as long as that block
  lives. Its compaction targets are stated: closed steps to outcomes,
  **decision entries to their kernel** — the decision, the reason that
  stops re-litigation, the approval — with git history the sole archive
  and no forward obligation orphaned.
- `code-reviewer`'s `{{CODE_PATHS}}` and `state-reviewer`'s inspection
  scope both exclude `.claude/hooks/bash_guard.py` **unconditionally** —
  they read files, not diffs; these are the quarantine's tooling-step
  mechanisms, symmetric across every file-reading agent.
- **In the same commit**: `.claude/spec-work/handoff/assets/` is deleted
  and every pointer and exception referring to it — `CLAUDE.md`'s
  temporary tooling-templates block among them — goes with it. All nine
  templates have adopted by now, so no not-yet-adopted list is needed.
  Git history keeps the templates; the untracked guard template alone is
  not kept, and need not be — rule 1's restore story never rests on it.
  Rule 1's `bash_guard.py` quarantine text **survives** this deletion,
  attached to `.claude/hooks/bash_guard.py`, and leaves only at the
  retirement step.

**How the operator tests it.** For the agents whose true trigger arrives
later, a smoke test — spawn, report shape, the model-override plumbing —
with their real proof deferred to that trigger and the instructions
saying so, because **a test that waits on a trigger the step cannot fire
is not a test**. `just check` green over the now-instantiated tooling,
including the frontmatter parse. A restart is part of the test: a new
agent may only be picked up at session start.
**Crosses the boundary**: the smoke tests spawn subagents and spend
usage. Cleanup: none.

### 005 — The same harness on the forge — `pending`

**Objective.** CI running the repository's own entry points, green, on
GitHub. The step that finishes the bootstrap.

**Spec sections.** §11 in outline (the forge and the release channel);
the interpreter matrix and packaging validation arrive with the steps
that deliver what they validate.

**Deliverables.**

- `.github/workflows/ci.yml` — **reusing `000`'s entry points** rather
  than restating a single check, so CI and the local runners can never
  disagree about what "green" means. Step `001`'s machine-local guard
  gate is the one sanctioned exception: loud locally, inert remotely, by
  design.
- Check and test split into separate jobs once both exist; the toolchain
  cached; a way of proving a fresh setup still works kept alive. The
  specification requires no scheduled workflow, so this **rides the CI
  triggers that already exist**; a scheduled workflow of its own is built
  only if a real need appears, as a logged decision. Naming a schedule the
  specification never asked for would invent a requirement.
- Shape taken from `.claude/refs/infra-conventions/github-ci.yml` — shape,
  not content: that project's CI has none of this one's needs, and
  nothing in it decides anything here. This repository's CI will exceed
  that shape where the specification requires it (interpreter matrix,
  packaging validation, a release process) as later steps deliver those
  pieces; `005` ships only what exists at `005`.
- A one-line status banner in `README.md` saying the repository is public
  but not yet installable — the honest state between this push and `021`,
  where the install channel actually opens.
- **One deliverable is a decision, not an artifact**: whether
  `.claude/spec-work/` — the specification phase's history, its review
  reports, and anything still sitting in it — goes public with the
  repository or is stripped before the first push. The question is put
  **twice and ruled separately**, against the future public face of a
  repository that is also the plugin's install channel:
  `.claude/spec-work/` is a transparency question, while `.claude/refs/`
  is the operator's supplied material whose authority lives elsewhere —
  different questions, one answer each. Whatever is ruled for the rest of
  `.claude/refs/`, **`behavior-corpus.md` stays until parity is
  declared**: later steps consume it as §8.1's yardstick. Logged, put to
  the operator, and made before the push it becomes irreversible at.

**How the operator tests it.** Authorise the first push and watch the run.
**Crosses the boundary**: a push publishes to what will be the plugin's
install channel, and the workflow is **unverified until the operator
authorises that push and the run comes back green**. External
prerequisites needed *at bootstrap*, not late: the forge, the remote, and
that authorisation. Cleanup: none beyond deleting the remote repository
if the operator abandons it.

**Milestone close.** State review and memory compaction, both on a model
other than the one that wrote the work.

## 3. Milestone 2 — The engine's spine

Pure-local through Milestone 3, and again at Milestone 5; **Milestone 4
is the verification pass and crosses the boundary**. Every step in this
milestone is code-bearing, so each ends with the standing cold code
review before handover, and every suite-bearing one with the test
review. The behavior corpus (`.claude/refs/behavior-corpus.md`) is read
before designing any suite in this milestone and before declaring any §4
behaviour done.

### 006 — Package, interpreter floor, CLI skeleton — `pending`

**Objective.** A Python package that installs from the repository, a
committed interpreter floor that is a *checked* claim, and a CLI shell
the operator can run — so every later engine step has a hand-testable
surface.

**Spec sections.** §3.1 (Python, standard library only, zero
dependencies, conservative floor), §2.3, §9 (the CLI must run without
Claude Code), §11 (one codebase, two doors).

**Deliverables.**

- The engine package at `src/frisk/`, standard library only, zero
  dependencies.
- `pyproject.toml` at the root — packaging metadata and the `frisk`
  console entry point. **This is the repository-installable door only**
  (§8.2's CI case, §11's second door): §2.2 forbids the plugin from
  requiring dependency installation to function, so a console script
  created by `pip install` cannot be how the CLI is reached on a machine
  where the *plugin* is installed. The plugin-side invocation mechanism
  is decided and stated at `021`, must be build-free, and is flagged in
  §14 Q8.
- **Open-fact inventory item 12 settled**: the §3.1 table of OS-shipped
  interpreters re-verified before the floor is committed. The floor
  should be 3.9; the implementation may move it with reason. A floor
  guessed too high fails in the worst direction — an engine the shipped
  interpreter cannot parse fails open. **The method is named here because
  it is not local**: what current macOS command-line tools, RHEL 9 and
  the current LTS distributions ship cannot be measured from this
  machine. Either the operator authorises the distribution-data lookups,
  or the operator supplies the table and the implementation checks the
  floor against it. §2.1's global pre-commitment governs the failure:
  an unverifiable table is recorded as unmeasured and drives the floor
  **down**, never up.
- Python's check family joins the harness at `000`'s entry points,
  **pinned to the committed floor** — syntax and type checking — so the
  floor is checked, not asserted. The type checker is a toolchain
  addition the specification does not ask for; it is taken from the house
  conventions in `.claude/refs/infra-conventions/` and logged as a
  within-latitude workflow decision at this step. TOML's parse check
  joins with `pyproject.toml`.
- `frisk --version` and a `frisk explain <command>` that parses nothing
  yet and says so.
- `tests/` created with the first unit suite; `just test` stops reporting
  an empty repository.

**How the operator tests it.** `just verify` green; `frisk --version` and
`frisk explain 'ls'` run from a plain shell with no Claude Code involved;
the floor interpreter runs the checks. Local and free. **External
prerequisite**: an interpreter at the committed floor on this machine,
and the operator's answer on item 12's method.

### 007 — Declarations, matchers, layering — `pending`

**Objective.** The config-facing API: what an operator writes, how it
composes, and how a value is matched. **This comes before reading the
line**, because tool recognition, flag arities and the
gated/registered/rule-bearing distinction are all defined in terms of
declarations — an engine step that parsed first would be judging against
a model that did not exist yet.

**Spec sections.** §3.4 (composition and layering, replace and
update-with-removal), §3.5 (the compatibility contract's layers 1 and 2),
§5.2 (the expressible surface — designed against the whole of it,
including its final clause: the project's test cases beside the rules
they prove), §5.3 (legibility), §3.2 (matchers, three-valued evaluation,
quantifiers), §9 (the effective registry must be inspectable).

**Deliverables.**

- The declaration constructors for registering tools (names, aliases,
  project-relative paths), rules, grants, per-tool default verdicts,
  accounted flags and assignments, flag arities (bare, value-required,
  value-optional), pre-subcommand options, handoffs and
  redirection-target rules — the API designed against **all** of §5.2
  even where §13 stages the behaviour later, so nothing is precluded.
- **The case declaration form** — command → expected verdict, sited
  beside the rule it proves (§5.2's closing clause). `019` consumes it,
  `023` and `024` write starter ones; it is created here.
- Matchers: patterns, path matchers resolving `..` and `~` **before**
  comparing with §3.2's fixed cross-form semantics and its lexical `cd`
  poisoning, predicates, and operand quantifiers where "every operand"
  requires at least one. **Three-valued evaluation** — satisfied,
  unsatisfied, unproven — with unproven moving stricter by role: failing
  a grant condition, firing a deny/ask rule's condition at ask strength,
  never reading as a plain false.
- Per-name shadowing with both override forms. The engine's default
  layers as declarations like any other: **shell wrappers and walked
  interpreters** — enumerated, shadowable, and carrying no rules and no
  grants, so they stand outside the coverage gate. (The *baseline read
  tools* layer belongs to `017`, with the allow doctrine it exists to
  serve; building it here would build something open fact (c) could
  retire.)
- Collection imports as composable units with an explicit total order,
  the operator's own declarations last and always winning.
- The API-generation declaration the scaffold will write, and the
  fail-closed check when a config declares a generation outside the
  accepted range.
- **The configuration's location convention**, fixed here rather than at
  the scaffold: §5.1 puts the config in a dedicated directory inside the
  project's `.claude/`, whose name should carry the plugin's name. This
  plan assumes `.claude/frisk/` and logs it at this step, because every
  later step's test instructions say "write a config by hand in a scratch
  project", `018`'s hook must resolve it, and `021`'s same-configuration
  requirement presupposes it. The scaffold at `024` *creates* that
  directory; it does not get to invent where it goes.
- **The effective-registry inspection surface** (§3.4 requires it: "the
  effective registry must be inspectable (§9) so composition never hides
  a rule") — `frisk` prints the composed registry, each declaration's
  source, and each matcher's three-valued outcome against a given value.
  This is what makes this step testable before any verdict exists.

**How the operator tests it.** Write a small config by hand in a scratch
project — the legibility test is the operator reading it — then print the
effective registry and watch shadowing, collection order and
update-with-removal do what the config says; feed a few values to the
matchers and read satisfied / unsatisfied / **unproven** back. Unit
suites cover the path matcher's traversal guarantees in their own right
(§8.1). Local and free.

### 008 — Reading the line — `pending`

**Objective.** Turn a command string into the set of invocations it
contains, correctly, with everything that binds to each one.

**Spec sections.** §4.1 (all of it), §4.2 (assignments, pre-subcommand
options, flag arities in use, tool recognition by basename and by
project-relative path, dynamic tokens), §3.3 (fail directions), §4.5 (the
latency budget).

**Deliverables.** Tokenization that resolves quoting rather than
pattern-matching raw strings; splitting at every separator including
newlines, runs of them and blank lines, with separators inside quotes
treated as data; backslash-line continuations joined before splitting;
comments excluded; the unparseable-line fallback (§4.1) with its
rule-bearing-name raw scan compared **by basename**. Leading environment
assignments bound as conditions in their own right (`FOO=bar`, `FOO+=bar`,
quoted values, lower-case names, case-sensitive matching), with
assignment-shaped tokens after the command name read as operands. The
three declared arities parsed, with the asymmetric fail directions of
§4.2 — **within a gated tool's accounted flags, arity must be declared
complete**, because an accounted value-taking flag whose arity is
under-declared lets its value look operative and a safe-marker flag
swallowed as another flag's value falsely satisfies a grant. Tool
recognition on the whole basename, never a prefix or substring, with
aliases and project-relative-path declarations, and the interpreter-run
form deferred to `010` with the walked-interpreter layer. Dynamic tokens
(`$FOO`, `${FOO}`) and the wider unreadable-token rule on gated
invocations. `frisk explain` begins showing the invocations it found.

**How the operator tests it.** `frisk explain` on a handful of lines from
the corpus and from the operator's own shell history — multiline strings,
continuations, quoted separators, `git -C dir push` — and read the
invocation list. `just verify` green. Local and free.

### 009 — Judging and combining — `pending`

**Objective.** Verdicts: per invocation, then over the line.

**Spec sections.** §3.2 (the decision model, closed worlds, the
assignment closed world, secure mode's engine-level capability), §6.1's
combination table (every row except the allow rows), §6.2 (reasons and
citations), §3.3.

**Deliverables.** Rules checked existentially, grants checked universally
and closed-world, per-tool default verdicts, the gated/registered/
rule-bearing distinction, and the environment-assignment closed world for
**every** registered tool with the universal benign list as a shadowable
default layer. Each invocation judged alone: a safe command never vouches
for its neighbour. The strict ranking deny > ask > allow > silence, and
**order-freedom within one declaration source**. Line-level combination
per §6.1's table, minus the allow rows, which wait on open fact (c) at
`015`. Exhaustive evaluation — no short-circuit at the first deciding
match — with the citation naming **every** declaration at the deciding
rank across the whole line, embedded invocations included. Reasons
written as steering text: the objection *and* the acceptable path, since
the model reads them. Secure mode's engine-level plumbing — the global
default verdict replacing every implicit silence — built here because it
shapes the decision model and could not be retrofitted; the operator-
facing switch and its guidance are 1.0.

**How the operator tests it.** `frisk explain` on lines that should deny,
ask and stay silent under a hand-written config, reading the reason and
the citation each time; §4.5's budget observable in the command's own
timing. Local and free.

## 4. Milestone 3 — Seeing through

### 010 — Wrappers, interpreters, shells and eval — `pending`

**Objective.** Walk through the programs whose job is to run other
programs.

**Spec sections.** §4.3 (wrappers, shells and eval), §4.2's
interpreter-run tools, §3.4's wrapper and walked-interpreter layers.

**Deliverables.** Registered wrappers contributing their own verdict and
the walk continuing to what they run; value-taking options and kept
positional operands stepped over per declaration; wrappers stacking;
assignments still binding along the walk and **accounted against the
declaration of the consuming command**, with the citation attributed
there and naming the assignment (the wrapper's own accounting is an
additional acceptance path, never an attribution target). The two
asymmetric failure modes: inside a wrapper an undeclared option is
presumed bare and the walk continues; the walk is *lost* only when the
command position resolves to nothing, and there the inside-handoff
discriminator applies — ask if a rule-bearing name appears among the
remaining tokens, silence otherwise. **Outside** any wrapper an
unrecognized leading word is silence, and scanning the rest of a parsed
line for registered names is **not** attempted — a prototype tried it and
gated `ls ../docker`. A registered tool run through a walked interpreter
is still that tool. A shell's `-c` argument re-analysed in full,
combined-flag spellings included; a registered shell or walked
interpreter with no `-c`/`-e` payload and no file operand **asks**;
`eval`'s joined arguments re-analysed; other languages' interpreters
never read as shell. Depth bounding, with a line cut short by the bound
treated as §4.1's unparseable line.

**How the operator tests it.** `frisk explain 'sudo git push --force'`,
`'sudo --unknown-flag git push -f'`, `'curl url | sh'`,
`'eval "git push -f"'`, `'python3 tools/deploy.py'` and the corpus's
wrapper rulings. Local and free.

### 011 — Substitutions, subshells and heredocs — `pending`

**Objective.** The commands hidden inside data.

**Spec sections.** §4.3 (substitutions and subshells; heredocs).

**Deliverables.** Unquoted `$(…)`, `<(…)`, `>(…)` and bare `(…)` judged
as commands, with `>(…)` never misread as a redirection; double-quoted
substitutions and backticks judged even though tokenization hid them in a
single token; single-quoted substitution text **not** judged; nesting
resolved. Heredocs on both axes: who consumes the body (a shell's body is
its program whatever the delimiter's quoting; anything else's body is
data) and whether the delimiter is quoted (an unquoted delimiter expands,
so substitutions inside such bodies are found and judged even in bodies
otherwise dropped as data). The two consequences for the bare-runner
asks: a heredoc attached to a shell or interpreter means the program *is*
shown, and `-` with an attached heredoc counts as fed-by-heredoc rather
than a missing file operand.

**How the operator tests it.** `frisk explain` on
`git commit -m "$(git push --force)"`, on `bash <<'SH'` with a gated
command inside, on `cat > notes.md <<EOF` with a substitution in the
body, and on `python3 - <<'PY'`. Local and free.

### 012 — Handoffs and redirections — `pending`

**Objective.** Tools that stop describing themselves and run something
else, and the places a command's output lands.

**Spec sections.** §4.3 (declared handoffs; redirections), §5.2's
execution-context scoping.

**Deliverables.** Handoff declarations with the outer invocation judged
as itself, the inner command judged in full, and tokens past the handoff
belonging to the inner command only — an inner `--check` never satisfying
an outer grant. The kept operand (image, service, container) **never**
read as a program. Judgment scopable by execution context, so the same
tool may carry different rules on the host and inside a named handoff.
The one sanctioned exception to the no-scanning rule: a handoff's command
position holding a flag-shaped token is silence *unless* a rule-bearing
name appears among the remaining tokens, which asks — deliberately
asymmetric, a known wart costing a prompt and never a wrong deny.
Redirections recognized as structure, never read as operands or flags,
with write-capable forms (`>`, `>>`, `>|`, `<>`, `>&file`) distinguished
from input redirections and fd-duplications; default silence; targets
matchable by rules (§4.3's deferral boundary allows rule-based target
matching to ship after parity — staged at `032` — but **recognition** is
owed the moment any allow exists, because hedge six cannot function
without it).

**How the operator tests it.** `frisk explain` on
`docker run alpine/curl -sL https://example.com` versus
`docker run alpine/curl -o git https://example.com`, on
`docker run org/rm -rf`, and on `echo x > .claude/settings.json`. Local
and free.

### 013 — Control structures: the routing minimum — `pending`

**Objective.** Shell keywords stop being read as commands.

**Spec sections.** §4.3 (control structures — the pre-1.0 routing
minimum).

**Deliverables.** A segment led by a control-flow keyword is treated as
**unparsed**, never silently misread as a command named `do` — which
under §6.1's broad allows would be a silent force-push in
`for f in *.log; do rm -rf "$f"; done`. A control-structure case family
in the engine suite at `tests/`. The full treatment — keywords stepped
past, bodies judged, headers contributing nothing, function bodies judged
at definition — is staged at 1.0 (`031`), and the interim is named in the
honesty text. The behavior corpus is silent here (the prototype shared
the gap), which is why the requirement is implemented from the
specification rather than inherited from the corpus.

**How the operator tests it.** `frisk explain` on a `for` loop, an `if`
chain, a brace group and a function definition, each containing a gated
command, and confirm the fallback fires rather than a bogus `do`
invocation. Local and free.

### 014 — The corpus reproduction — `pending`

**Objective.** The parity yardstick, reproduced end to end for the first
time.

**Spec sections.** §8.1 (gate one: behavior cases against test-only
declarations, and the adjudicated corpus).

**Deliverables.** The corpus's three policy contexts reproduced as test
fixtures under `tests/corpus/` — context B's stub tools, context A's git
and docker starter policy, context C's infra tools — against
**test-only declarations** that live with the fixtures, never against the
shipped starter registry of `023`, so policy changes can never break
engine tests and the separation is enforceable by path. A run report
stating how many rulings are asserted and which are knowingly
outstanding — at this point only context A's allow rulings, which wait on
open fact (c) at `015` and are asserted by `017` itself, not deferred to
the parity audit. Any ruling the
specification contradicts is **reported, not implemented**: the
specification wins.

**How the operator tests it.** `just test` reproduces the corpus and
prints the coverage report. Local and free.

## 5. Milestone 4 — Platform truth

Both steps here cross rule 9's boundary. They are split by apparatus:
the cheap, mode-independent measurements and the go/no-go first, the
expensive permissive-mode matrix second. A three-way split — separating
the go/no-go from the cheap facts — was considered and rejected as
over-splitting: (c) is one measurement, and its *ruling* is a separate
operator decision either way.

### 015 — Verification pass one: the go/no-go and the mode-independent facts — `pending`

**Objective.** Settle open fact (c) — which decides whether §6.3's whole
apparatus gets built — and the four inventory items that need no
permissive mode.

**Spec sections.** §2.1 (open fact (c); inventory items 5, 10, 11, 13),
§6.1 (rule 1's two parenthetical platform facts), §4.4, §12 (the
verification record).

**Deliverables.**

- **(c)** the substitution-prompt trigger — **the go/no-go for §6.3's
  entire allow machinery**, measured *before* any of it is built, as
  §2.1 mandates: nothing should be built that its outcome would retire.
  Retirement is a documented-capability change and **comes back to the
  operator** whatever the outcome.
- **item 5** the platform hook-timeout default, sizing the engine's
  internal budget at `018`. Where sources disagree and it cannot be
  measured, the budget is sized against the *smallest* limit any
  consulted source claims.
- **item 10** prefix-rule word-boundary behaviour. The one item of the
  thirteen the specification pre-commits no response for, so it **comes
  back whatever the outcome**.
- **item 11** the platform's built-in read-only command handling. The
  failure direction is extra prompts, never a lost fence.
- **item 13** whether the Bash tool persists shell state across tool
  calls — it **extends the blind-spot documentation**, so it **comes
  back**.
- A throwaway PreToolUse probe hook, written in scratch space outside the
  repository and deleted with it — named as a deliverable so nothing of
  it survives into `018`'s design.
- `docs/verification-record.md` created (§12), with the platform version
  recorded against every measurement, plus the amendments: each
  resolution lands in **two places** — `SPECIFICATIONS.md` amended so its
  facts stay true, the `DECISIONS.md` entry written *before* the
  amendment and both in one commit carrying nothing else, and the
  operator-facing consequence in the record.
- A fact that cannot be measured is **recorded as unmeasured and treated
  at the stricter branch** of its pre-committed response.

**How the operator tests it.** Read the record and the amendment commits;
rule on (c). **Crosses the boundary**: driving live Claude Code sessions,
which spends usage. **External prerequisites**: the operator's consent, a
scratch area outside the working directory, and the platform version to
record. Cleanup: delete the scratch area, the throwaway projects and the
probe hook.

### 016 — Verification pass two: the permissive-mode matrix — `pending`

**Objective.** The facts that can only be read by running the permissive
modes — the most expensive measurement in the plan, on its own gate.

**Spec sections.** §2.1 (open facts (a), (b), (d); inventory item 9),
§6.1 (the mode taxonomy, absorbed into (d); the pairing guidance's
mode-aware section), §12.

**Deliverables.**

- **(a)** whether a hook `allow` lifts the bash safety heuristics and the
  working-directory sandbox — measured with a write attempt into the
  scratch area outside the working directory. Pre-committed: the
  specification assumes the stronger consequence either way.
- **(b)** whether settings `deny`/`ask` are evaluated regardless of a
  hook's decision. Unfavourable branch **comes back to the operator**: it
  demotes §6.1's pairing rule 2 from requirement to hygiene guidance.
- **(d)** hook `deny`/`ask` survival per permission mode, **both
  directions**, absorbing the mode-taxonomy check. The per-mode
  secure-mode claims **come back to the operator**.
- **item 9** settings deny/ask enforcement under each permissive mode. A
  mode found to skip deny rules **empties §7.5's backstop row for that
  mode** — a documented limitation, so it **comes back**.
- The mode taxonomy itself, taken from the running version rather than
  from any document, since it decides what the pairing guidance of `024`
  may claim.
- Record and amendment per `015`'s two-places rule.

**How the operator tests it.** Read the record and the amendment commits;
rule on the four escalations. **Crosses the boundary**, hardest in the
plan: several sessions in permissive modes, including one that approves
everything, each spending usage. **External prerequisites**: as `015`,
plus the operator's explicit consent to the permissive modes named.
Cleanup: delete the throwaway projects; confirm no permissive mode was
left set.

## 6. Milestone 5 — The release valve

### 017 — The allow verdict and its hedges — `pending`

**Objective.** The one exceptional verdict, built only if `015` says it
has a purpose.

**Spec sections.** §6.3 (the allow doctrine and all seven hedges), §6.1's
allow rows of the combination table, §3.4/§6.3's baseline read tools.

**Deliverables.** The allow verdict ranking below everything; the seven
mechanically enforced hedges — fully examined line; no unaccounted global
option; downgrade to silence where the line carries no substitution; no
dynamic token outside the value slots of the flags the granting rule
names, exhaustively; no unproven write-capable redirection; direct,
unwrapped command position, with a leading environment assignment
explicitly **not** a wrapper for this hedge; and the ranking hedge
itself. The allow rows of §6.1's combination table, with **examined** and
**placed** carrying exactly the meanings §6.1 gives them: unregistered-
tool silence is the absence of examination and withholds the allow. The
**baseline read tools** default layer (`cat`, `echo`, `printf`, `date`,
`head`, `basename` and kin) as examined-silent, registered here rather
than at `007` because it exists solely to make the examined-line release
work and idles with the verdict if (c) retired it; enumerated in the
operator documentation like every other default layer. The semantic
precondition is **operator doctrine, not an engine check** — carried by
documentation and pressed by the skill, never verified by code.

**The corpus's allow rulings are asserted here**, with the machinery they
exercise — context A's hedged `commit -m` shape and every withholding
case around it. They are the last of the corpus left outstanding by
`014`, so after this step the engine's corpus fidelity is complete and
demonstrable, whatever `026` later declares.

**If `015` retired the allow verdict** (open fact (c) unfavourable), this
step becomes the retirement instead: the verdict retires to silence,
starter allow declaration and hedge machinery idling with it, the
combination table's allow rows collapse, and the corpus's allow rulings
count as satisfied by the superseding behaviour (§13). The plan does not
pre-judge which; `015` decides and the operator rules.

**How the operator tests it.** `frisk explain` on
`git commit -m "$(date)"` (allowed), `sudo git commit -m "$(date)"`,
`git -C /elsewhere commit -m "$(…)"`,
`touch $(cat x) && git commit -m "$(cat m)"`,
`echo x > ~/.bashrc && git commit -m "$(date)"` and
`rm -rf build && git commit -m "$(date)"` — each withheld, each for its
own hedge, each saying which. Local and free.

## 7. Milestone 6 — The hook and the gates

### 018 — The hook and fail-closed runtime — `pending`

**Objective.** The engine reached by Claude Code, and every failure it
can see converted into a loud deny.

**Spec sections.** §7.1 (fail closed at runtime, the layered failure
policy), §2.1 (the hook contract, the internal time budget, non-blocking
output), §2.2 (plugin configuration as the machine-level dial's carrier).

**Deliverables.** The PreToolUse entry point: payload in, verdict out,
with reasons and citations flowing to the model. Its path inside the
plugin tree is **a claim to confirm, not an assumption** — §2.2 describes
the plugin system in capability terms and names no paths, so the hook
file's location and declaration shape are settled against the installed
version at `021` and recorded in `.claude/docs/` with version, method and
re-measure recipe; until then the hook is reached through a throwaway
project's own settings file, which is also how this step is tested. Any
failure while loading the configuration or reaching a decision produces
**deny**, naming what broke as precisely as possible, stating that no
safe verdict can be produced, and pointing at the CLI's liveness
diagnostics. The engine's own internal time budget, sized far below the
platform limit measured at `015`, covering **all** hook work — per-command
decisions and validation runs alike — converting an overrun into a deny
that names the overrun. Validation state at least session-scoped, so an
overrunning validation run does not become a standing deny storm. The
machine-level failure-policy dial, whose carrier — plugin user
configuration reaching hooks as environment variables — is **inventory
item 7, settled at `022`, not before**: the dial therefore ships behind
its own pre-committed unfavourable branch, with the engine default (deny)
standing unrelaxed until `022` confirms the carrier exists. The
non-blocking user-visible channel the once-per-session notices ride on.

**How the operator tests it.** In a throwaway project outside the working
directory, register the hook through that project's `.claude/settings.json`
(the plugin does not exist until `021`), point it at a deliberately broken
config, issue a Bash call, and observe the deny naming the breakage.
**Crosses the boundary**: a live session in a throwaway project. Cleanup:
delete the throwaway project.

### 019 — Gate two: liveness, selftest, coverage, status — `pending`

**Objective.** The project-facing checks, invocable from pre-commit and
CI, identical to what the hook runs.

**Spec sections.** §8.2 (both checks and the coverage gate), §9
(`liveness`, `selftest`, `status`).

**Deliverables.** **Liveness**: the config loads, every declaration is
structurally valid, reasons are non-empty, a hook payload comes back as a
well-formed verdict, plus the boundary-nullifying shapes — an
unconditional allow on a tool with no grants, a grant with no conditions,
and a declaration shadowing a wrapper without re-declaring its handoff.
No behaviour cases: it stays lint-fast, because it runs before every
commit. **Selftest**: liveness, then the project's cases, then
**coverage** — every rule and grant in the *effective* registry reached
by at least one case, *reached* meaning the rule matched or the grant
held, supplied by the project or by the source that contributed the rule.
The engine's default layers stand outside the gate as shipped; the moment
a config shadows one into a rule-bearing tool, the config owes the cases.
**Status** in text form: config presence, engine and API generation,
secure mode, last validation and outcome, the kill switches when the
process environment carries them, and the visibly-inert statement when
the plugin is enabled but the project unconfigured. Exit statuses usable
from scripts. (JSON output and the "which engine answered" field wait on
`021`'s resolution and land at `037`.)

§8.2's *derived cases* — a project harness deriving cases from project
structure — are a specification **may** with no consumer yet. Not built
here, and not scheduled: rule 11's build-at-the-moment-of-need. Nothing
in §3.4, §3.5 or §5.2 precludes adding them when a real project asks.

**How the operator tests it.** In a scratch project with a hand-written
config: `frisk liveness`, `frisk selftest` (green, then break a rule's
spelling and watch coverage fail), `frisk status`. Local and free.

### 020 — Validation on change — `pending`

**Objective.** A config edit or an engine update that moves a recorded
verdict stops the line instead of moving the boundary.

**Spec sections.** §7.2 (both classes, the dials, the warning's surface),
§7.3 (the engine-version trigger), §3.5 layer 3.

**Deliverables.** Change detection and caching for both triggers. Class
one — config does not load — denies every Bash call, unconditional with
respect to any *config* dial; only §7.1's machine-level relaxation
reaches it. Class two — config loads but liveness fails, cases fail or
coverage has gaps — denies with the failing check named, and the config's
own dial may relax it to warn-and-proceed **only when the trigger was a
config change**; a failure triggered by an engine-version change denies
whatever the dial says. When relaxed, the warning is reflected in
`status` as the last validation outcome **and** surfaces at least once in
the session itself — a warning with no surface is this specification's
own definition of a silent failure. The engine-version trigger re-runs the
project suite before anything is judged, and an API generation the engine
no longer speaks is a deny pointing at the skill's migration assistance.

**How the operator tests it.** In a scratch project: edit a rule without
its case and watch the next Bash call deny naming the uncovered rule;
flip the recorded engine version and watch the suite re-run. **Crosses
the boundary** for the in-session halves (a live session in a throwaway
project); the CLI halves are local. Cleanup: delete the scratch project.

## 8. Milestone 7 — Distribution and adoption

### 021 — The plugin, the marketplace and engine resolution — `pending`

**Objective.** One codebase, two doors, at the same version — and a CLI
that can never answer with an engine the hook does not run.

**Spec sections.** §2.2, §11, §9 (the resolution requirement and
same-configuration), §8.2 (the CI pin), §13 (what first exposure owes).

**Deliverables.**

- The plugin manifest and the marketplace manifest, making the repository
  its own marketplace. `.claude-plugin/plugin.json` and
  `.claude-plugin/marketplace.json` are this plan's **assumption, not a
  fact**: the specification names no paths, so the manifest locations and
  schemas, the hook declaration's shape and file, and the skill's path
  are all confirmed against the installed platform version here and
  recorded in `.claude/docs/` with version, method and re-measure recipe.
  `018`'s hook path is settled by the same probe. JSON parse checks
  extend to both manifests once their paths are known.
- **The plugin-side CLI invocation mechanism**, stated and confirmed
  build-free: §2.2 forbids the plugin from requiring dependency
  installation, so `006`'s console entry point cannot serve here. The
  candidates are a shipped wrapper script, a plugin command, or
  `python3 -m frisk` against a computed `${CLAUDE_PLUGIN_ROOT}`; the
  choice is a logged decision with the alternatives, made against what
  the probe finds.
- The resolution rule keyed to the observable condition: wherever an
  installed plugin is resolvable its engine answers, wherever none is the
  project's recorded pin does, and in **every** context the CLI states
  which engine version answered — never a refusal, never an unattributed
  answer. Resolution must expose **which door answered**, because §7.4's
  sentinel requires a plugin-resolved engine specifically.
- Same-configuration alongside same-engine: the CLI and the hook resolve
  the *same* config for a given project, failing loudly when the
  resolution is ambiguous — a nested-`.claude` or monorepo layout must
  not let a directory-walking CLI and a project-root-anchored hook answer
  from different configs.
- The engine version the project pins for CI, recorded beside the
  configuration.
- **This is the step at which an existing prototype-guarded project can
  switch.** Nothing after it is a precondition for that: `022` measures
  plugin-system facts whose unfavourable branches cost durability of
  validation state, a failure-policy dial and the sentinel's rationale —
  §2.2 calls item 6's bad outcome "a performance-and-reach cost, never a
  correctness or safety one" — while `023` and `024` supply starter
  content and a scaffold that a project bringing its own registry does
  not use.
- **The trust statement, brought forward from `028`.** This is the commit
  that makes the repository installable by anyone who finds it, and §13
  says the first public exposure of a permission-path tool must not lack
  one: the README gains the **"in development, install only for
  testing"** warning prominently, and a minimal `SECURITY.md` (the trust
  model and the vulnerability-reporting path) lands at the root in the
  same commit. `028` grows both to their full §12 shape. **These gate
  publication, not use**: they exist for a stranger who arrives at the
  repository, and nothing in them is a precondition for the operator
  installing frisk from their own clone.

**How the operator tests it.** Install the plugin from the local
repository into a throwaway project and run `frisk status` and
`frisk explain` from both doors, reading which engine answered each time.
**One premise to confirm first, cheaply**: whether a *local* directory or
clone can be registered as a marketplace at all. §2.2 says only that
plugins are installed from marketplaces and that a repository can be its
own; it does not say a local one works. If only remote sources do, the
throwaway installs pull from the pushed public repository instead and the
cost statements of `022`–`027` change from local to boundary-crossing —
which is why this is confirmed here, at the first step that needs it.
**Crosses the boundary**: installing a plugin or a marketplace into the
operator's live Claude Code needs explicit authorisation in that
exchange. Cleanup: uninstall the plugin and the marketplace, delete the
throwaway project.

### 022 — Verification pass three: the plugin-system facts — `pending`

**Objective.** The three open facts that need an installed plugin to
measure.

**Spec sections.** §2.2 (inventory items 6, 7, 8), §12 (the record).

**Deliverables.** **item 6** the per-plugin persistent data directory —
if none exists, durable state degrades to session scope (validation
re-runs once per session, `status`'s last-validation answer reaches back
only as far as the session): a documented limitation, so it **comes back
to the operator**. **item 7** plugin-configuration delivery to hooks as
environment variables — if values do not reach hooks, `018`'s
machine-level dial has no carrier and the engine default stands
unrelaxed, stricter and safe. **item 8** project-recommended-plugin
prompting — a prompt, if one exists, softens the sentinel's rationale
without replacing it. Amendments and record entries per `015`'s
two-places rule.

**How the operator tests it.** Read the record additions and the
amendment commits. **Crosses the boundary**: needs the plugin installed
in a live Claude Code and spends usage. Cleanup as `021`.

### 023 — The starter registry — `pending`

**Objective.** The boundary a freshly scaffolded project gets on day
one: git's ground rules, and nothing the project did not ask for.

**Spec sections.** §5.4 (the starter registry, its git ground rules and
its deliberate acceptances — deviating from its additional-tools
recommendation per `D-009`), §8.2 (starter cases from day one), §3.4
(the first collection).

**Deliverables.** Shipped policy content in its own tree —
`collections/starter/` inside the plugin, separate from `src/frisk/` and
from `tests/`, so §8.1's engine/policy test separation is enforceable by
path and the engine suite can be forbidden from importing it.

- The **git ground rules**, required and identical across projects: deny
  on forced, mirror and delete pushes however spelled, history rewriting,
  and destruction of git's recovery data; ask on any push, commit
  amendment, rebase, hard/merge resets, clean, restore, the
  work-discarding forms of checkout and switch, stash dropping and
  clearing, branch and tag deletion or forced movement, worktree removal
  and pruning, and the presence of a config-override option (`-c`,
  `--config-env`) — the sibling spelling of the assignment danger, since
  a boundary that gates one spelling and not the other gates neither.
  Allow: exactly §6.3's commit-message shape with its hedges, if `017`
  kept the verdict.
- **And nothing else** (`D-009`). §5.4 recommends "a small set of
  additional common tools" with docker as the candidate; this project
  ships none. A scaffolded project gets git's ground rules — the losses
  that are permanent or expensive — and writes its own policy for
  everything else. The docker shape §5.4 describes survives in two places
  that cost a new project nothing: the corpus fixtures of `014`, which
  prove the engine expresses it, and a **worked example** in the operator
  configuration reference (`039`), which is how an operator who wants
  docker gated writes it. This is a deviation from a specification
  *should*; `D-009` carries the reason, and §14 Q10 asks whether §5.4's
  text should be amended to match rather than merely deviated from.
- Starter cases covering **every** starter rule, beside the rules they
  prove, so the coverage gate passes from day one.
- §5.4's second deliberate acceptance stated where an operator reads it:
  `rm` is **not** in the starter registry — unregistered it still meets
  the default mode's native prompt, while registering it usefully would
  either over-prompt or under-protect. (The first acceptance, that the
  starter docker shape leaves `docker run` host mounts silent, has
  nothing left to apply to: with no shipped docker shape there is no
  silence to accept. Q10 covers it.)

**How the operator tests it.** `frisk selftest` against the starter set
and `frisk explain` on each ground rule's dangerous spellings, including
the ones a prefix rule would miss. Local and free.

### 024 — The scaffold, the project entry point and the pairing guidance — `pending`

**Objective.** Adoption possible without archaeology — the parity floor
of §13's item 9.

**Spec sections.** §5.1 (location, lifecycle, trust), §5.4 (the
scaffold), §6.1 (the pairing guidance, mode-aware and honest about what
rule 1 trades), §3.5 (the API-generation declaration), §9 (the
scaffold-created project entry point), §8.2 (gate two reachable from the
project).

**Deliverables.**

- The scaffold creating the configuration directory inside the target
  project's `.claude/`, at the location `007` fixed — pre-filled with the starter
  registry, the API-generation declaration, and the starter cases.
- **§9's stable scaffold-created entry point inside the project**, written
  into that same directory: the first of §9's three doors, and what
  `035`'s sentinel probes through. Its path is fixed here because a path
  no plan states is a path a later session invents.
- Created **only** on the operator's request, and **never touched by an
  unattended write afterwards**: the two write paths are the scaffold at
  creation and the skill applying a change the operator has just
  approved. The **one-pass review** is what makes scaffold-time writing
  legitimate.
- `docs/pairing.md` — the written pairing guidance in guided-manual form,
  a human document the README points at rather than restates: rule 1's
  broad allows scoped to the tools whose configuration can return silence
  or allow — never a deny-everything tool, never the engine's default
  layers, so generated guidance never suggests `Bash(sudo:*)` or an allow
  for `cat`; rules 2–5, each with the silent failure it prevents; the
  deny backstop as a package with the broad allows; and the mode-aware
  picture with §6.1's scoped claims, carrying whatever `016` measured per
  mode rather than the comfortable misreading. It also names the
  project-side wiring of gate two — liveness in the adopting project's
  pre-commit, selftest in its CI — so §13's "reachable from the project"
  is an instruction, not an inference.
- **Explicit approval before every settings edit the tooling performs,
  scaffold time included.**
- The sentinel offer of §5.4 is **not** part of this step: the sentinel
  is a 1.0 item (§13) and arrives at `035`. The scaffold gains the offer
  there.

**This step completes adoption for a project that has no boundary yet.**
A project *replacing* a prototype-generation hook does not need it, and
does not need `022` or `023` either: it brings its own registry and its
own cases, so the starter content, the scaffold that writes it and the
pairing guidance for settings it has already paired are all conveniences
rather than preconditions. **Replacement is possible from `021`** — the
engine is corpus-complete after `017`, the hook, both gates and the
validation triggers are in place by `020`, and `021` supplies the
supported install path, the resolution rule and both CLI doors. The proof
that *this project's* verdicts did not move is its own cases re-running
under `019`'s selftest, which is exactly the mechanism §3.5's third layer
and §8.2 exist for. Transcribing an existing prototype registry into
frisk's declaration form remains hand work; see §14 Q11.

**How the operator tests it.** Scaffold a throwaway project, read the
generated config in one pass (the legibility requirement is this test),
run its selftest green through the project entry point, and read
`docs/pairing.md`. Then the replacement case: point a project that
carries a prototype-generation hook at frisk instead, transcribe a
handful of its rules and its cases, and watch selftest reproduce the
verdicts the prototype gave. Local and free except where the operator
chooses to apply the settings edits.

### 025 — Gate three: the reachability probe — `pending`

**Objective.** The one check that exercises the whole chain.

**Spec sections.** §8.3.

**Deliverables.** The documented procedure at `docs/`, for direct use:
issue a command the config refuses and verify it comes back refused **by
the guard, citing its rule** — merely prompting means the hook is not
reaching the tool call and only the deny backstop is left. Documented for
running at adoption, after settings changes, and whenever §7's layers
report nothing but doubt remains. `027` consumes it; the skill guides it
from `036`.

**How the operator tests it.** Run the probe in a scaffolded throwaway
project and read the citation. **Crosses the boundary**: a live session
with the plugin installed. Cleanup: delete the throwaway project.

## 9. Milestone 8 — Parity

### 026 — The corpus parity audit — `pending`

**Objective.** Declare parity against the yardstick, or name exactly what
is missing. **This is the project's release claim, not a gate on anyone's
adoption**: an operator can replace a prototype hook from `021` onward,
and adopt frisk in a project with no boundary from `024`. What this step decides is whether the maintainer
may say *parity* in public and tag a release on it.

**Spec sections.** §8.1 (the corpus as the parity yardstick), §13 (the
pre-1.0 bar).

**Deliverables.** An audit, not new behaviour: the corpus is asserted by
`014` and `017` between them, and this step verifies that every ruling is
accounted for — asserted, superseded by a verification-pass outcome (the
allow rulings if open fact (c) retired the verdict — these **count as
satisfied** and do not block the declaration), or reported as a
specification conflict where a ruling and the specification disagree, the
specification winning and the conflict reported, never silently
implemented. If the audit finds nothing outstanding, its whole output is
the statement below; that is a correct result, not an empty step. A written parity
statement at `docs/` against §13's bar, item by item, with anything
outstanding named — including the residues this staging accepts: no
sentinel before 1.0, and no once-per-session visibly-inert notice.

**How the operator tests it.** Read the parity statement; `just test`
green with the corpus fully asserted. Local and free.

### 027 — The dev guard retires — `pending`

**Objective.** frisk takes over guarding its own repository; the
prototype apparatus of rule 1 ends whole.

**Spec sections.** §5.4, §6.1 (this repository's own pairing), §8.3.

**Deliverables.** The first dogfood install: scaffold this repository,
write its configuration, and pair its settings per frisk's own §6.1 — put
to the operator for review as `001`'s baseline was — ending with the
reachability probe of `025`. Then the **sweep of every committed
reference to the apparatus** — the sweep, not this list, carries the
completeness claim, and these are the named anchors:
`.claude/hooks/bash_guard.py`; the backup ref (the remote copy's fate
proposed to the operator in this step); the gitignore entries; the
`--liveness`/`--selftest` harness wiring; the hook registration in
`.claude/settings.json`; `approve-step`'s backup-ref push step; the
`code-reviewer` and `state-reviewer` path exclusions; `optimize-memory`'s
whole-carry extension; `.claude/docs/guard-record.md`; and rule 1's
quarantine text in `CLAUDE.md`. Nothing of the apparatus outlives its
purpose.

**How the operator tests it.** Review the pairing proposal, run the
reachability probe in this repository, and confirm the sweep leaves no
reference behind (`git grep` for each anchor). **Crosses the boundary**:
installs frisk into the operator's live Claude Code for this project.
Cleanup: none intended — this is the intended end state.

### 028 — README and SECURITY.md in full for the first tag — `pending`

**Objective.** The trust statement a permission-path tool must not ship
without, complete.

**Spec sections.** §12 (README, SECURITY.md), §13 (what the first public
tag owes), §1 (the scope statements), §5.1 and §15 (the trust model).

**Deliverables.** `README.md` at the repository root grown to its first-
tag shape: what frisk is and is not, installation, the scaffold
quickstart, the settings pairing pointing at `docs/pairing.md`, the
interim gaps §4.3 and §4.4 require naming while the honesty document is
still a 1.0 deliverable, and pointers to the rest — with **"in
development, install only for testing"** still prominent (it was added at
`021` and is removed at 1.0). Formatting quality is an explicit
requirement, not a nicety: this is where trust starts. `SECURITY.md`
grown from `021`'s minimum: the trust model (the config is
operator-owned code, at exactly the trust level of a hand-written hook),
what the guard is and is not a defense against (§15), the fail-open
residue and its mitigations, and how to report vulnerabilities.
**This step resolves the scheduled `README.md` collision**: the workflow
entry-point content written at bootstrap migrates to a home proposed as a
logged decision, and every template naming `README.md` — reviewer frames
and staleness sweeps alike — is re-pointed in the same commit.

**How the operator tests it.** Read both documents and answer "do I want
this in my permission path?" from the README alone. Local and free.

### 029 — CI for release, and the first public tag — `pending`

**Objective.** The plugin's own CI proving what §11 requires, and the
first release.

**Spec sections.** §11 (packaging, distribution, versioning), §8.1 (gate
one across an interpreter matrix).

**Deliverables.** CI extended on `005`'s workflow: gate one across an
interpreter matrix — the floor version and a current one at minimum,
before any release — plus packaging validation, which **includes proving
the shipped starter content**: scaffold into a throwaway project and run
its selftest, so the starter registry's spellings (the force-push denies
above all) are demonstrated before release rather than by the first
adopter, without weakening §8.1's engine/policy test separation.
`CHANGELOG.md` at the root, carrying every behavior-visible change —
any change that could move a verdict — and `LICENSE` (MIT) beside it.
Semver on the plugin, with the API generation moving on **any** breaking
release during 0.x. The release itself: a GitHub release with a zip
archive carrying an explicit pin in the marketplace entry, so what users
install is attestable.

**How the operator tests it.** Watch the matrix run green, then authorise
the release. **Crosses the boundary**: a release publishes to the plugin's
install channel. **External prerequisite**: GitHub release capability.
Cleanup: a release can be deleted but not un-fetched — this is a
deliberate one-way step.

## 10. Milestone 9 — Toward 1.0

Staged per §13's second bullet: the full surface of the specification at
requirement tier. **These entries are deliberately coarser than the rest**
— objective and deliverables only, without the spec-section list,
deliverable locations and test statement `CLAUDE.md`'s plan conventions
require of an open entry. Refining them now would be planning against a
system whose earlier half does not exist. Each is expanded to a full
entry when Milestone 8 closes, before any of them starts. The deviation
is logged as `D-008`.

### 030 — Export modeling — `pending`

§4.2's `export NAME=value` segment establishing assignments for every
subsequent invocation in the same tool call, entering §3.2's accounting —
benign list, per-tool accounted sets, otherwise ask at the consuming
registered command, unregistered consumers keeping their posture. The
family's edges (`declare -x`, `unset`, valueless `export NAME`) stay
declared blind spots rather than half-modeled. Removes one line from the
honesty document.

### 031 — Control structures in full — `pending`

§4.3's full treatment: keywords in command position stepped past so
bodies are judged, loop and case headers contributing nothing, function
bodies judged at **definition** so a later bare call cannot launder what
they contain, and anything the walk cannot follow routed to §4.1's
fallback. Replaces `013`'s routing minimum.

### 032 — The remaining declaration shapes — `pending`

§4.3's two command-running shapes: the option-introduced,
terminator-bounded handoff (`find -exec … +`) and the stdin-fed runner
(`xargs`), whose inner command is judged on its visible parts with
operand-requiring conditions unprovable. Plus §4.3's rule-based
**redirection target matching**, which lets §6.1 rule 5 stop riding on
the native file-tool path rules alone.

### 033 — Secure mode operational — `pending`

§3.2's configurable global default verdict exposed as the config switch
with its reason, off by default, with the operator guidance §6.1's
mode-aware section owes and whatever `016` measured per mode.

### 034 — The compatibility contract in full — `pending`

§3.5's contiguous generation range with supported → deprecated → dropped
handling, internal fallbacks and migrations where a change permits, and
the visible nudge on a deprecated generation.

### 035 — The sentinel and the kill switches — `pending`

§7.4 in full, staged here because §13 puts "the sentinel offer" at 1.0
and the pre-1.0 bar does not name it. A tiny, self-contained POSIX-shell
PreToolUse hook, **offered and never imposed**, whose shipping form is
this step's first decision: it is emitted by the scaffold into the target
project (under §5.1's scaffold write path) rather than referenced inside
the plugin, because §2.2 makes the plugin's own location a per-version
cache that a committed project settings file must not point into. Once
per session it **probes by execution** through §9's project entry point
and the CLI's resolution, requiring success from a **plugin-resolved**
engine specifically — a pin-answered probe is a failure for its purpose —
and requiring that the project's configuration loads. On failure it
denies Bash naming the exits appropriate to what it observed, with a
**distinct** message when the engine is installed but cannot be located.
A failed probe is the session's **standing state**, not a one-shot
message; the cache remembers a *success*, never a failure. In a
sentinel-adopted project a broken config denies **regardless** of §7.1's
machine-level relaxation. Both kill switches read from the hook's **own**
process environment, so an `export` inside a tool call can never reach
them; the wholesale switch silences the sentinel too; both announce
themselves once per session through the non-blocking channel, the
sentinel-only switch included. The scaffold of `024` gains the offer
here. The shell check family already exists from `000`.

### 036 — The maintenance skill — `pending`

§10 in full, shipped in the plugin tree at the skill path `021`
confirmed: adoption (scaffold, pairing walkthrough with explicit approval
before every settings edit, sentinel offer, closing with `025`'s
reachability probe); teaching the model the boundary, optionally; **the
surprise loop** — explain, draft the most precise rule change, draft the
reproducing case, present both stating what would newly be allowed and
what newly gated, and wait; migration, working on the configuration **as
text**; and doctrine enforcement in dialogue — the allow doctrine's
argument demanded, a git ground rule's weakening treated as reportable
(the two worktree asks the one pair a project may reasonably drop), and
**shapes over lists** when drafting grants. Every rule change is the
operator's call; the skill never edits the configuration on its own
initiative.

### 037 — The CLI in full — `pending`

§9's complete surface: `explain` **showing its work** — which invocations
were found through which walls of §4.3 — the JSON output option, and
`status` completed with the fields that need `021`'s resolution (which
engine answered).

### 038 — The once-per-session visibly-inert notice — `pending`

§5.4's notice through the non-blocking channel, making no distinction
between never-scaffolded and a config that stopped existing — the second
being the sharper danger. Owed at 1.0 per §13; closes the residue that
step named.

### 039 — The remaining documentation — `pending`

§12's outstanding deliverables at `docs/`: the **operator configuration
reference** (every declaration, its conditions, its fail direction, and
**every engine default layer enumerated in full** — wrappers, baseline
read tools, walked interpreters); the **honesty document** (§4.4's blind
spots and §7.5's residue map, stated as plainly as in the specification);
the **platform verification record** completed; and **CONTRIBUTING.md** at
the root (engine changes come with corpus cases, behavior changes are
changelog-visible, and the specification's doctrine sections are the
review bar). The README grows to its full §12 shape — including the
working **status-line sample** §12 asks it to carry, consuming `037`'s
CLI output — and the "install only for testing" warning is removed.

### 040 — End-to-end checks, explored — `pending`

§8.1's third level, a **should**: driving a real Claude Code session in
CI and observing the hook decide, and exercising the skill if the
platform's plugin-evaluation tooling permits. This depends on facilities
outside the project's control; **declining it is an expected outcome the
specification allows**, logged with what was found. Never a substitute
for the two layers above it. **Conditional external prerequisite**: a
CI-drivable Claude Code environment and its credential.

### 041 — 1.0 — `pending`

The stability promise: from here the config-facing API moves only by
§3.5's rules. Release per `029`'s machinery.

## 11. Open facts — the settling ledger

Each row of §2.1's thirteen-item inventory, named with the step that
settles it. Inventory items 1–4 **are** the four lettered open facts, so
the thirteen rows below are the whole of it. The ledger's scope is wider
than the consolidated list, deliberately: a size or cost the
specification says will be "measured at implementation" is an open fact
wherever it appears, and §2.1's inventory was assembled precisely because
such facts hide in prose. Every flag of that kind in the specification
resolves to a row below.

| Item | What | Settled at |
|---|---|---|
| 1 / (a) | Hook allow's sandbox waiver | `016` |
| 2 / (b) | Settings deny/ask precedence over hook decisions | `016` |
| 3 / (c) | The substitution-prompt trigger — the go/no-go | `015`, before `017` |
| 4 / (d) | Hook deny/ask survival per permission mode | `016` |
| 5 | The platform hook-timeout default, sizing the internal budget | `015`, consumed at `018` |
| 6 | The per-plugin persistent data directory | `022` |
| 7 | Plugin-configuration delivery to hooks as environment variables | `022`, consumed at `018` |
| 8 | Project-recommended-plugin prompting behaviour | `022` |
| 9 | Settings deny/ask enforcement under each permissive mode | `016` |
| 10 | Prefix-rule word-boundary behaviour | `015` |
| 11 | The platform's built-in read-only command handling | `015` |
| 12 | The Python-floor table of OS-shipped interpreters | `006` |
| 13 | Whether the Bash tool persists shell state across tool calls | `015` |

Items 6, 7 and 8 are at `022` rather than `015`/`016` because each needs
an installed plugin to measure, which `021` delivers. Item 7 is consumed
at `018`, before it is settled, which is why `018` ships the dial behind
its pre-committed unfavourable branch.

Three claims this plan makes that the specification does **not** state,
tracked here because they are premises, not facts: the plugin tree's
paths and manifest schemas (confirmed at `021`), the plugin-side CLI
invocation mechanism (decided at `021`), and whether a local directory
can serve as a marketplace (confirmed at `021`, with its cost consequence
pre-committed).

## 12. Specification coverage

Every section of `SPECIFICATIONS.md`, mapped.

| Section | Steps |
|---|---|
| §1 Goal | `028` (README scope statements), `039` |
| §2.1 The hook contract | `015`, `016`, `018` |
| §2.2 The plugin system | `021`, `022` |
| §2.3 Runtime | `006` (floor), `035` (why the sentinel is shell) |
| §2.4 Prior art | Informational; positions the README at `028`. No implementation deliverable. |
| §3.1 Three parts, one trust split | `006`, and the architecture across `007`–`024` |
| §3.2 The decision model | `009`, with matchers at `007` and secure mode operational at `033` |
| §3.3 Fail directions | `008`, `009`, and asserted throughout the engine suites |
| §3.4 Composition and layering | `007`, first consumer at `023` |
| §3.5 The compatibility contract | `007` (layers 1–2), `020` (layer 3), `034` (the full range) |
| §4.1 Reading the line | `008` |
| §4.2 What binds to an invocation | `008`, interpreter-run tools at `010`, export modeling at `030` |
| §4.3 Seeing through | `010`, `011`, `012`, `013`; full control structures at `031`; the two runner shapes and redirection target matching at `032` |
| §4.4 Declared blind spots | `039` (the honesty document); interim gaps named at `013` and `028` |
| §4.5 Proportion | `008`, `009`, and a standing focus of every code review |
| §5.1 Location, lifecycle, trust | `024`, `021`/`028` (SECURITY.md) |
| §5.2 What the configuration must express | `007` (API against the whole surface, cases included), staged behaviour across `009`–`012`, `032` |
| §5.3 Legibility | `007`, `039` (the operator reference) |
| §5.4 The scaffold | `023` (git ground rules only — `D-009` deviates from the additional-tools recommendation), `024`; the sentinel offer at `035`; the visibly-inert notice at `038` |
| §6.1 Pairing | `016` (the facts), `024` (`docs/pairing.md`), `028` (the README section) |
| §6.2 Reasons and citations | `009` |
| §6.3 The allow doctrine | `017` |
| §7.1 Fail closed at runtime | `018` |
| §7.2 Validation on configuration change | `020` |
| §7.3 Validation on engine change | `020` |
| §7.4 The sentinel | `035` |
| §7.5 The coverage map | `026` (the residues parity accepts), `039` |
| §8.1 Gate one | Suites in every engine step; the corpus at `014` and `026`; the end-to-end should at `040` |
| §8.2 Gate two | `019`; project-side wiring named at `024`. §8.2's derived-cases *may* is declined until a project needs it (rule 11), precluded by nothing. |
| §8.3 Gate three | `025` |
| §9 The CLI | `006`, `007` (registry inspection), `008`, `019`, `021` (resolution), `024` (the project entry point); complete at `037` |
| §10 The maintenance skill | `024` (adoption in guided-manual form), `036` (the full loop) |
| §11 Packaging, distribution, versioning | `021`, `029` |
| §12 Documentation deliverables | `021` (the minimum at first exposure), `028` (README, SECURITY.md), `015`/`016`/`022` (the verification record), `024` (`docs/pairing.md`), `039` (the rest, status-line sample included) |
| §13 Release path | This plan's structure and §1's re-inventory |
| §14 Future Considerations | **Excluded from this pass**, by the specification's own staging: rule collections beyond the project, the declarative configuration layer, transcript mining, the guard-internal decision log, user-global configuration, and native Windows support. §3.4's composition, §2.2's data directory and §3.5's stability keep each adoptable later. |
| §15 Non-Goals | **Excluded by definition**; stated in SECURITY.md at `021`/`028` and the honesty document at `039`. |

## 13. External prerequisites

Things only the operator can prepare, each with the step that first needs
it.

| Prerequisite | First needed |
|---|---|
| `just` installed on this machine | `000` |
| A working `python3` and `pip` (any version) for the pinned toolchain | `000` |
| A private backup remote for rule 1's backup ref | `001` |
| The forge, the remote, and authorisation of the first push (the public repository is also the plugin's install source, so adoption testing waits on it) | `005` |
| A second strong model for the milestone passes — the state review and the memory compaction must not run on the model that wrote the work | the foundation-milestone close, after `005` |
| An interpreter at the committed floor (rule 2's floor-pinned checks need it), and either authorisation for the distribution-data lookups item 12 needs or the operator's own table | `006` |
| The verification-pass trio: consent to drive sessions in the permissive modes, a scratch area outside the working directory, and the platform version recorded with every measurement | `015`, with the permissive modes first needed at `016` |
| Authorisation for any install into the live Claude Code — plugin or marketplace | `021` |
| GitHub release capability | `029` |
| *Conditional*: a CI-drivable Claude Code environment and its credential, for §8.1's end-to-end should — declining it is an expected outcome | `040` |

The behavior corpus is already delivered at
`.claude/refs/behavior-corpus.md`; nothing waits on it.

## 14. Open questions

Underspecified, risky, or worth reordering — for the operator, never
silent assumptions.

1. **The foundation splits (`D-003`).** This plan turns the prescribed
   `001` into two gates and the prescribed tooling step into two more, on
   the bootstrap instructions' own invitation to split what is too big.
   Six foundation steps instead of four. If the operator would rather
   review fewer, larger gates, they merge back and the numbering shifts.
2. **The §13 re-inventory ruling (`D-004`).** Section 1 recommends the
   bar stands as drawn. The operator rules; a "move" on any row
   re-stages that item into Milestone 9.
3. **Milestone 4's placement.** The verification pass sits after the
   engine's spine rather than before it, because none of the parsing work
   depends on its outcomes and the cheap-first rule applies. The risk is
   that a surprising outcome — (b) demoting pairing rule 2, (d) finding a
   mode that swallows `ask` — arrives after five engine steps are
   written. Nothing in `007`–`014` would change; only `017`, `024` and
   the documentation would. Confirm the trade is the one the operator
   wants.
4. **`017` may become a retirement.** If open fact (c) says the platform
   no longer prompts on substitutions, §6.3's whole apparatus retires to
   silence. The plan does not pre-judge, but the operator should know
   that one measurement can delete a milestone.
5. **Milestone 9's grain (`D-008`).** Steps `030`–`041` carry objective
   and deliverables only, without the spec-section list, locations and
   test statement an open entry owes. They are expanded when Milestone 8
   closes. If the operator wants them sized now, say so.
6. **The config directory's name.** §5.1 leaves it to the implementation
   and says it "should carry the plugin's name". This plan assumes
   `.claude/frisk/` in a target project and logs it at `007` — moved
   there from the scaffold step, because `018`'s hook must resolve the
   config, `021`'s same-configuration requirement presupposes a
   convention, and every engine step's test instructions already assume
   one. The scaffold creates the directory; it does not decide where it
   goes.
7. **The interim honesty obligations.** §4.3 and §4.4 require interim
   gaps to be *named in the honesty documentation* — a 1.0 deliverable
   (`039`) — while the gaps exist from parity. This plan names them in
   the pre-1.0 README (`028`). If the operator would rather a minimal
   honesty document ship at parity, that is a small step to add before
   `028`.
8. **Packaging shape and the plugin's second door.** This plan assumes
   `pyproject.toml` with a `src/frisk/` layout and a `frisk` console
   entry point for the repository-installable door — but §2.2 forbids the
   plugin from requiring an install, so the plugin-side door needs a
   different, build-free mechanism, decided at `021`. Flagged because it
   decides how the CI matrix, the sentinel's probe and the
   repository-installable door all look.
9. **The sentinel's restaging (`D-007`).** An earlier draft built the
   sentinel and its kill switches before parity. §13 names the sentinel
   offer as a 1.0 item and the pre-1.0 bar does not mention it, so this
   plan moves it to `035` — with the honest consequence that before 1.0,
   two rows of §7.5's coverage map have no catcher. If the operator wants
   the seatbelt earlier, it is a deliberate quick win under §13's
   "everything else may ship here as a quick win" and moves back.

10. **Should §5.4 be amended, or merely deviated from (`D-009`)?** The
   starter registry now ships git ground rules only. Two clauses of §5.4
   describe a world where it also ships docker: "a small set of
   additional common tools… docker is the recommended candidate", and the
   deliberate acceptance that "the starter docker shape leaves
   `docker run` host mounts silent" — the second of which now has no
   referent. A *should* may be deviated from with a logged reason and no
   amendment, which is what `D-009` does and what this plan assumes. But
   the acceptance paragraph is not a recommendation, it is a statement
   about what the product does, and it is now false. Rule 1 puts that to
   you rather than letting the implementation decide: **amend §5.4 at
   step `023`** (decision entry and specification text in one commit), or
   **leave it and let `D-009` carry the divergence**. I recommend
   amending — a specification that describes shipped content the product
   does not ship is the drift rule 1 exists to prevent, and the amendment
   is two sentences.

11. **A prototype-to-frisk migration aid — wanted, or hand work?** Parity
   proves the engine and the configuration API can *express* what a
   prototype-generation registry expressed; it does not transcribe one.
   §10's migration capability is engine-version migration inside frisk,
   and the specification never asked for a translator, so this is not a
   coverage gap. But if several prototype-guarded projects are to move,
   the transcription is the real cost of adoption and it lands entirely
   on the operator. Say so and it becomes a step with its own gate,
   placed after `024`; say nothing and the plan assumes hand work.
