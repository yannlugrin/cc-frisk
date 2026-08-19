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
  review and a memory-compaction pass (`CLAUDE.md`, rule 3).

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
| 9 | Enough of the scaffold and pairing guidance — even in guided-manual form — that adoption is possible without archaeology | Keep, at the guided-manual floor §13 itself grants: a scaffold command that writes the config directory, the starter registry, the starter cases and the API-generation declaration, plus written pairing guidance. The *skill* wrapping it (§10's full loop) stays 1.0. | keep |
| 10 | A minimal README and SECURITY.md, with the "in development, install only for testing" warning | Non-negotiable for a permission-path tool's first public tag; §12 already stages the other four documents at 1.0. | keep |

Two further placements, stated so the ruling is complete:

- **The starter registry's docker shape (§5.4)** is a *should* in the
  specification ("a small set of additional common tools… docker is the
  recommended candidate"), which would ordinarily invite deferral to
  shrink the pre-1.0 review surface. It cannot be deferred: the behavior
  corpus's context A is *git and docker*, and 109 of its rulings run
  against that registry. Deferring docker would make the parity bar
  unreachable by item 1. **Keep**, and the reason is worth recording:
  this is the one place where a specification *should* is pinned by a
  requirement elsewhere.
- **The once-per-session visibly-inert notice (§5.4)** is already staged
  at 1.0 by §13 itself, with the residue stated (a vanished config
  before 1.0 is caught only by the sentinel, where adopted). This plan
  carries that staging unchanged and names the residue in the interim
  honesty text. **No change proposed.**

**Net recommendation: the bar stands as §13 draws it.** Every accreted
item survives its own challenge, three of them (4, 5-class-two, 6)
because they are cheap riders on machinery the bar already owes, and one
apparent deferral candidate (docker) turns out to be pinned by the
parity yardstick. The operator's ruling on this table is logged as
`D-004`.

## 2. Milestone 1 — Repository foundation

Five steps, one milestone, drawn by what a working repository needs
rather than by cost class. The bootstrap instructions prescribe four
(`000` harness, `001` permission and hook baseline, `002` workflow
tooling, `003` CI); this plan **splits the prescribed `001` in two** —
the baseline proposal and its instantiation (`001`), then the probe
campaign and its record (`002`) — because the prescription itself notes
they are separately testable, because `001` otherwise carries a
mid-step session restart inside a single gate, and because the operator's
review of a settings proposal is a cheap text correction that should
land before a session is spent proving it. The workflow tooling and CI
shift to `003` and `004`; CI stays **last within the foundation**. The
repository is not bootstrapped until its CI has run green. This split is
`D-003`, put to the operator at this review.

### 000 — The harness, local only — `pending`

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
  downstream), and `CLAUDE.local.md`.
- `requirements.txt` at the root — the pinned toolchain, installable
  through one documented setup command.
- `justfile` at the root and `scripts/` beside it (`setup.sh`,
  `check.sh`, `test.sh`): `just setup`, `just check [scope]`,
  `just test`, `just verify`. **`check` takes a scope argument and is
  one entry point, never a second recipe** — the whole-tree gate is the
  default and the narrowed what-changed form is an argument to the same
  command, because two recipes hold two lists and will eventually differ
  in *what* they look for rather than only in how much.
- `check`'s file list is passed explicitly —
  `git ls-files --cached --others --exclude-standard` — so a lint error
  in a file that exists but was never added to the index still fails the
  gate. **Never `git add --intent-to-add`**: it writes to the index as a
  side effect of a check, turns `?? file` into ` A file` in
  `git status --porcelain`, and lets the next `git commit -a` sweep the
  file into an unrelated commit. Standing path exclusions, keyed on the
  path and not on tracked status: `.claude/spec-work/` (no session's
  reading material, rule 1) and `.claude/refs/` (the operator's supplied
  material, read-only, owned elsewhere — a lint finding there would have
  no legal resolution).
- `.pre-commit-config.yaml` at the root, wired to the **same** harness
  so the local runners cannot diverge, with the check families whose
  artifacts exist at this step and no others (rule 2's never-ahead
  rule): YAML lint (the hook runner's own configuration is the first
  artifact of that class), JSON parse (`.claude/settings.json` already
  exists), POSIX-shell lint over `scripts/` (shellcheck family),
  Markdown and prose lint over the governance documents, repository
  hygiene and security (large binaries, merge-conflict markers,
  secret/private-key scanning per rule 5) from the runner's stock
  collection, pinned, and whitespace/newline discipline. The **fixers**
  live in the commit hook; `check` asserts and never repairs.
- Linter configuration at the root (`.yamllint.yml`, the Markdown
  linter's config), shaped after `.claude/refs/infra-conventions/` —
  shape, not content.
- A lint bend for `SPECIFICATIONS.md` if one proves necessary: read-only
  under rule 1, so the lint bends to it, the bend is scoped to that file
  alone, and it is a logged decision rather than a quiet config line.
- Python's check family is **deliberately absent** here — no Python
  exists yet; it joins at `005` with the first engine file, pinned to
  the interpreter floor that step commits to. TOML joins with
  `pyproject.toml`. Governance frontmatter joins at `003` with the first
  skill. CI joins at `004`.
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
  and `CASES` blocks, and reports **outcomes** — what is gated, what the
  settings pairing requires, what the guard cannot see, whether its
  checks pass — never the file's text, parsing approach or API shapes.
  The file is executable and **untracked**: `.gitignore` already carries
  both guard paths.
- A tool inventory driving that registry: what this project actually
  runs — the harness, `just`, `pre-commit`, `git`, the language
  runtimes, everything the `justfile` shells out to — with each registry
  tool given the acts rule 9 gates **for this project**. The guard's
  `GIT` ground rules are the same in every project and are **added to,
  never weakened**. Every rule added gets a `CASES` entry: `--selftest`
  fails on a rule no case reaches, which is what keeps the intent
  executable rather than remembered.
- `refs/backups/bash-guard` — the backup ref of rule 1, created here,
  outside `refs/heads/` so no `push --all`, default refspec or clone
  carries it. The in-channel subagent chains a snapshot onto it at
  instantiation (a clean base, before any edit) and after every
  `--selftest`-green edit, using `git hash-object -w`, `mktree` and
  `commit-tree -p` — commands that print hashes, never content. The
  restore recipe
  (`git show refs/backups/bash-guard:.claude/hooks/bash_guard.py`
  redirected onto the path, content never rendered) is **proven once**
  at this step.

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
  installed version: the list is taken from the running version, not
  from any document, and the mode proposed is probed at `002`. The mode
  is *set* rather than worked around — if a mode auto-accepts file
  edits, that is what removes the need for a blanket edit allowance —
  and it decides whether the mode-disabling keys belong in the baseline
  at all.
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
and the guard's `--selftest` green. Local and free. Reviewing the
proposal is the gate; the mechanisms are proved at `002`.

### 002 — The probe campaign and the guard record — `pending`

**Objective.** Prove what each enforcement mechanism introduced at `001`
actually does in the version being run, and write down what was
measured — because a mechanism that turns out to enforce nothing is a
guard on paper, and the failure announces nothing.

**Spec sections.** None (workflow foundation).

**Deliverables.**

- The probe campaign for this step's mechanisms, assuming nothing —
  including nothing from the bootstrap instructions. At minimum: whether
  the settings keys set at `001` are honoured; which spelling of a
  file-path rule the file tools actually match; whether the hook is
  reached at all; what an unmatched command does under the proposed
  permission mode; and **whether a hook `ask` still prompts** under it —
  the close ritual attempts its push in reliance on that, and a gate
  that has stopped gating says nothing about it. Confirm too that this
  version honours `autoMemoryEnabled`, on the same reasoning: an
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
and the step's instructions say where. Local and free.

### 003 — The workflow tooling — `pending`

**Objective.** The rituals and reviewers this workflow runs on, existing
before the events they handle.

**Spec sections.** None (workflow foundation).

**Deliverables.** All nine remaining templates from
`.claude/spec-work/handoff/assets/`, instantiated and adapted — every
placeholder filled with this repository's real commands and paths,
including the governance set (`{{PLAN}}`, `{{DECISIONS}}`, `{{SPEC}}`,
`{{STEP_ID}}`, `{{VERIFY_COMMAND}}`, `{{CODE_PATHS}}`). A placeholder
whose referent does not exist yet is seeded from the specification's own
vocabulary and kept current under rule 6 as the system materializes. This
repository is single-track: where a template's body carries multi-track
guidance, that block is dropped rather than reconciled.

- Skills at `.claude/skills/<name>/SKILL.md`: `orient`, `resume-step`,
  `handover-step`, `approve-step`.
- Agents at `.claude/agents/<name>.md`: `step-reviewer`, and the two
  whose trigger is a certainty of this plan — `state-reviewer` and
  `optimize-memory` (the foundation is one milestone, so a milestone
  close arrives whatever later grouping applies, and both must exist
  before it arrives rather than be improvised at the boundary) — and
  rule 2's review pair, `code-reviewer` and `test-reviewer`, certainties
  from the engine's first step on.
- `code-reviewer` is adapted **twice**: to carry the three standing foci
  (security — permission-path code, the §5.1/§15 trust model must not
  weaken; performance — §4.5's per-call latency budget; code quality),
  and to swap its on-request, operator-named-files invocation contract
  for rule 2's **standing per-code-step gate**.
- `handover-step` gains the code-review step for code-bearing steps and
  the test-review step for suite-bearing ones: the standing gate's
  carrier is the ritual that performs handovers, and a mandated gate
  outside that ritual is a gate that silently skips.
- `approve-step`'s push step gains the backup ref's push to the backup
  remote, on every close — resolving the remote by name and reporting its
  absence rather than failing on a machine that lacks it — and its
  step 5 names the milestone pair directly.
- `optimize-memory`'s plan-compaction section reduces to verifying each
  closed entry is compacted and reporting any that is not, since
  `approve-step` compacts at every close; its whole-carry protections
  (never-compress, budget-yield) extend to rule 1's quarantine text
  beside rule 9's boundary enumeration, for as long as that block lives.
- `code-reviewer`'s `{{CODE_PATHS}}` and `state-reviewer`'s inspection
  scope both exclude `.claude/hooks/bash_guard.py` **unconditionally** —
  they read files, not diffs; these are the quarantine's step-`003`
  mechanisms, symmetric across every file-reading agent.
- An instantiated file must never name a skill or agent that was not
  adopted: trim the reference or adopt it, because a dangling name is a
  ritual that silently skips a step.
- **In the same commit**: `.claude/spec-work/handoff/assets/` is deleted
  and every pointer and exception referring to it — `CLAUDE.md`'s
  temporary tooling-templates block among them — goes with it. All nine
  adopt here, so no not-yet-adopted list is needed. Git history keeps the
  templates. Rule 1's `bash_guard.py` quarantine text **survives** this
  deletion, attached to `.claude/hooks/bash_guard.py`, and leaves only at
  the retirement step.
- The probes for this step's mechanisms: an agent's `tools:` frontmatter,
  and whether `CLAUDE.md` reaches a subagent's context at all — one
  exchange with the first agent this step spawns ("quote rule 9's opening
  line"), never the bootstrap cold reviewer, whose context must stay
  confined. Every reviewer agent's boundary rests on it.
  **Pre-committed unfavourable branch**: if `CLAUDE.md` does not reach a
  subagent's context, each agent's body carries the gated set inlined — a
  logged decision naming the single-source-of-truth cost — never a
  citation to a rule the agent cannot read. Results land in
  `.claude/docs/`, version-stamped, with the re-measure recipe.

**How the operator tests it.** Invoke each ritual and watch it do what it
claims: real invocations of the session-start, resume and handover
rituals; the close ritual proves itself at this very step's close, its
trigger being any step approval and `003`'s the first after it exists.
For the agents whose true trigger arrives later, a smoke test — spawn,
report shape, the model-override plumbing — with their real proof
deferred to that trigger and the instructions saying so. A new skill or
agent may only be picked up at session start, so the instructions state
where the restart falls. Local and free.

### 004 — The same harness on the forge — `pending`

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
  pieces; `004` ships only what exists at `004`.
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

Pure-local from here to Milestone 5: the engine, its suites and the CLI
cost nothing but time. Every step in this milestone is code-bearing, so
each ends with the standing cold code review before handover, and every
suite-bearing one with the test review. The behavior corpus
(`.claude/refs/behavior-corpus.md`) is read before designing any suite in
this milestone and before declaring any §4 behaviour done.

### 005 — Package, interpreter floor, CLI skeleton — `pending`

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
  console entry point, making the repository-installable engine+CLI door
  of §8.2/§11 real from the start.
- **Open-fact inventory item 12 settled**: the §3.1 table of OS-shipped
  interpreters re-verified before the floor is committed. The floor
  should be 3.9; the implementation may move it with reason. A floor
  guessed too high fails in the worst direction — an engine the shipped
  interpreter cannot parse fails open.
- Python's check family joins the harness at `000`'s entry points,
  **pinned to the committed floor** — syntax and type checking — so the
  floor is checked, not asserted. TOML's parse check joins with
  `pyproject.toml`.
- `frisk --version` and a `frisk explain <command>` that parses nothing
  yet and says so.
- `tests/` created with the first unit suite; `just test` stops reporting
  an empty repository.

**How the operator tests it.** `just verify` green; `frisk --version` and
`frisk explain 'ls'` run from a plain shell with no Claude Code involved;
the floor interpreter runs the checks. Local and free. **External
prerequisite**: an interpreter at the committed floor on this machine.

### 006 — Reading the line — `pending`

**Objective.** Turn a command string into the set of invocations it
contains, correctly, with everything that binds to each one.

**Spec sections.** §4.1 (all of it), §4.2 (assignments, pre-subcommand
options, flag arities, tool recognition by basename and by
project-relative path, dynamic tokens, interpreter-run tools), §3.3 (fail
directions), §4.5 (the latency budget).

**Deliverables.** Tokenization that resolves quoting rather than
pattern-matching raw strings; splitting at every separator including
newlines, runs of them and blank lines, with separators inside quotes
treated as data; backslash-line continuations joined before splitting;
comments excluded; the unparseable-line fallback (§4.1) with its
rule-bearing-name raw scan compared **by basename**. Leading environment
assignments bound as conditions in their own right (`FOO=bar`, `FOO+=bar`,
quoted values, lower-case names, case-sensitive matching), with
assignment-shaped tokens after the command name read as operands. The
three flag arities — bare, value-required, value-optional — with the
asymmetric fail directions of §4.2 (**within a gated tool's accounted
flags, arity must be declared complete**). Tool recognition on the whole
basename, never a prefix or substring, with aliases and
project-relative-path declarations. Dynamic tokens (`$FOO`, `${FOO}`) and
the wider unreadable-token rule on gated invocations. `frisk explain`
begins showing the invocations it found. Unit suites at `tests/`,
including the path matcher's own tests once §3.2's matchers land at
`007`.

**How the operator tests it.** `frisk explain` on a handful of lines from
the corpus and from the operator's own shell history — multiline strings,
continuations, quoted separators, `git -C dir push` — and read the
invocation list. `just verify` green. Local and free.

### 007 — Declarations, matchers, layering — `pending`

**Objective.** The config-facing API: what an operator writes, how it
composes, and how a value is matched.

**Spec sections.** §3.4 (composition and layering, replace and
update-with-removal), §3.5 (the compatibility contract's layers 1 and 2),
§5.2 (the expressible surface — designed against the whole of it), §5.3
(legibility), §3.2 (matchers, three-valued evaluation, quantifiers).

**Deliverables.** The declaration constructors for registering tools
(names, aliases, project-relative paths), rules, grants, per-tool default
verdicts, accounted flags and assignments, arities, pre-subcommand
options, handoffs and redirection-target rules — the API designed against
**all** of §5.2 even where §13 stages the behaviour later, so nothing is
precluded. Matchers: patterns, path matchers resolving `..` and `~`
**before** comparing with §3.2's fixed cross-form semantics and its
lexical `cd` poisoning, predicates, and operand quantifiers where "every
operand" requires at least one. **Three-valued evaluation** —
satisfied, unsatisfied, unproven — with unproven moving stricter by role:
failing a grant condition, firing a deny/ask rule's condition at ask
strength, never reading as a plain false. Per-name shadowing with both
override forms. The engine's default layers as declarations like any
other: shell wrappers, baseline read tools, walked interpreters —
enumerated, shadowable, and carrying **no rules and no grants**, so they
stand outside the coverage gate. Collection imports as composable units
with an explicit total order, the operator's own declarations last and
always winning. The API-generation declaration the scaffold will write,
and the fail-closed check when a config declares a generation outside the
accepted range.

**How the operator tests it.** Write a small config by hand in a scratch
project — the legibility test is the operator reading it — and run
`frisk explain` against it. Unit suites cover the path matcher's
traversal guarantees in their own right (§8.1). Local and free.

### 008 — Judging and combining — `pending`

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
`013`. Exhaustive evaluation — no short-circuit at the first deciding
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

### 009 — Wrappers, interpreters, shells and eval — `pending`

**Objective.** Walk through the programs whose job is to run other
programs.

**Spec sections.** §4.3 (wrappers, shells and eval), §4.2's
interpreter-run tools, §3.4's wrapper default layer.

**Deliverables.** Registered wrappers contributing their own verdict and
the walk continuing to what they run; value-taking options and kept
positional operands stepped over per declaration; wrappers stacking;
assignments still binding along the walk and **accounted against the
declaration of the consuming command**, with the citation attributed
there and naming the assignment. The two asymmetric failure modes:
inside a wrapper an undeclared option is presumed bare and the walk
continues; the walk is *lost* only when the command position resolves to
nothing, and there the inside-handoff discriminator applies — ask if a
rule-bearing name appears among the remaining tokens, silence otherwise.
**Outside** any wrapper an unrecognized leading word is silence, and
scanning the rest of a parsed line for registered names is **not**
attempted. A shell's `-c` argument re-analysed in full, combined-flag
spellings included; a registered shell or walked interpreter with no
`-c`/`-e` payload and no file operand **asks**; `eval`'s joined arguments
re-analysed; other languages' interpreters never read as shell. Depth
bounding, with a line cut short by the bound treated as §4.1's
unparseable line.

**How the operator tests it.** `frisk explain 'sudo git push --force'`,
`'sudo --unknown-flag git push -f'`, `'curl url | sh'`,
`'eval "git push -f"'` and the corpus's wrapper rulings. Local and free.

### 010 — Substitutions, subshells and heredocs — `pending`

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

### 011 — Handoffs and redirections — `pending`

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
matching to ship after parity, but **recognition** is owed the moment any
allow exists, because hedge six cannot function without it).

**How the operator tests it.** `frisk explain` on
`docker run alpine/curl -sL https://example.com` versus
`docker run alpine/curl -o git https://example.com`, on
`docker run org/rm -rf`, and on `echo x > .claude/settings.json`. Local
and free.

### 012 — Control structures, and the corpus's first full pass — `pending`

**Objective.** The parity minimum for shell keywords, and the first
end-to-end reproduction of the behavior corpus.

**Spec sections.** §4.3 (control structures — the pre-1.0 routing
minimum), §8.1 (gate one, behavior cases and the corpus).

**Deliverables.** The routing minimum: a segment led by a control-flow
keyword is treated as **unparsed**, never silently misread as a command
named `do`. The full treatment — keywords stepped past, bodies judged,
loop and case headers contributing nothing, function bodies judged at
definition — is staged at 1.0 (`029`), and the interim is named in the
honesty text. A control-structure case family in the engine suite. Then
the corpus's three policy contexts reproduced as test fixtures — context
B's stub tools, context A's git and docker starter policy, context C's
infra tools — against **test-only declarations**, never against real
starter rules, so policy changes can never break engine tests. Any
ruling the specification contradicts is **reported, not implemented**:
the specification wins.

**How the operator tests it.** `just test` reproduces the corpus, with
the run reporting how many of its rulings are asserted and which are
knowingly outstanding (the allow rulings wait on `013`/`014`). Local and
free.

## 5. Milestone 4 — Platform truth

### 013 — The verification pass, part one — `pending`

**Objective.** Settle the open facts that decide requirements, measured
on the running platform rather than asserted, and record what was found
where an operator can read it.

**Spec sections.** §2.1 (open facts (a)–(d) and inventory items 5, 9, 10,
11, 13), §6.1 (the mode taxonomy, absorbed into (d)), §12 (the platform
verification record).

**Deliverables.**

- **(a)** whether a hook `allow` lifts the bash safety heuristics and the
  working-directory sandbox. Pre-committed: the specification assumes the
  stronger consequence either way.
- **(b)** whether settings `deny`/`ask` are evaluated regardless of a
  hook's decision. Unfavourable branch **comes back to the operator**: it
  demotes §6.1's pairing rule 2 from requirement to hygiene guidance.
- **(c)** the substitution-prompt trigger — **the go/no-go for §6.3's
  entire allow machinery**, measured *before* any of it is built.
  Retirement is a documented-capability change and **comes back to the
  operator** whatever the outcome.
- **(d)** hook `deny`/`ask` survival per permission mode, both
  directions, absorbing the mode-taxonomy check. The per-mode secure-mode
  claims **come back to the operator**.
- **item 5** the platform hook-timeout default, sizing the engine's
  internal budget at `015`.
- **item 9** settings deny/ask enforcement under each permissive mode. A
  mode found to skip deny rules **empties §7.5's backstop row for that
  mode** — a documented limitation, so it **comes back**.
- **item 10** prefix-rule word-boundary behaviour. The one item of the
  thirteen the specification pre-commits no response for, so it **comes
  back whatever the outcome**.
- **item 11** the platform's built-in read-only command handling.
- **item 13** whether the Bash tool persists shell state across tool
  calls — it **extends the blind-spot documentation**, so it **comes
  back**.
- A fact that cannot be measured is **recorded as unmeasured and treated
  at the stricter branch** of its pre-committed response.
- Each resolution lands in **two places**: `SPECIFICATIONS.md` is amended
  so its facts stay true — the `DECISIONS.md` entry written *before* the
  amendment, both in one commit, code excluded — and the operator-facing
  consequence goes into `docs/verification-record.md` (§12), created
  here, with the platform version recorded against every measurement.

**How the operator tests it.** Read the record and the amendment commits.
**Crosses the boundary**: measuring these requires driving live Claude
Code sessions, several of them in permissive modes, which spends usage
and needs the operator's consent in that exchange. **External
prerequisites**: that consent, a scratch area outside the working
directory for fact (a)'s write attempt, and the platform version to
record. Cleanup: delete the scratch area and the throwaway projects the
probes ran in.

## 6. Milestone 5 — The release valve

### 014 — The allow verdict and its hedges — `pending`

**Objective.** The one exceptional verdict, built only if `013` says it
has a purpose.

**Spec sections.** §6.3 (the allow doctrine and all seven hedges), §6.1's
allow rows of the combination table, §3.4's baseline read tools.

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
baseline read tools default layer as examined-silent. The semantic
precondition is **operator doctrine, not an engine check** — carried by
documentation and pressed by the skill, never verified by code.

**If `013` retires the allow verdict** (open fact (c) unfavourable), this
step becomes the retirement instead: the verdict retires to silence,
starter allow declaration and hedge machinery idling with it, the
combination table's allow rows collapse, and the corpus's allow rulings
count as satisfied by the superseding behaviour (§13). The plan does not
pre-judge which; `013` decides and the operator rules.

**How the operator tests it.** `frisk explain` on
`git commit -m "$(date)"` (allowed), `sudo git commit -m "$(date)"`,
`git -C /elsewhere commit -m "$(…)"`,
`touch $(cat x) && git commit -m "$(cat m)"`,
`echo x > ~/.bashrc && git commit -m "$(date)"` and
`rm -rf build && git commit -m "$(date)"` — each withheld, each for its
own hedge, each saying which. Local and free.

## 7. Milestone 6 — The hook and the gates

### 015 — The hook and fail-closed runtime — `pending`

**Objective.** The engine reached by Claude Code, and every failure it
can see converted into a loud deny.

**Spec sections.** §7.1 (fail closed at runtime, the layered failure
policy), §2.1 (the hook contract, the internal time budget, non-blocking
output), §2.2 (plugin configuration as the machine-level dial's carrier).

**Deliverables.** The PreToolUse entry point at `hooks/` in the plugin
tree: payload in, verdict out, with reasons and citations flowing to the
model. Any failure while loading the configuration or reaching a decision
produces **deny**, naming what broke as precisely as possible, stating
that no safe verdict can be produced, and pointing at the CLI's liveness
diagnostics. The engine's own internal time budget, sized far below the
platform limit measured at `013`, covering **all** hook work — per-command
decisions and validation runs alike — converting an overrun into a deny
that names the overrun. Validation state at least session-scoped, so an
overrunning validation run does not become a standing deny storm. The
machine-level failure-policy dial carried by plugin user configuration
(machine-wide by construction, and organizationally pinnable since
managed settings outrank the user's); if `013`'s item 7 finds no carrier,
the engine default (deny) stands unrelaxed. The non-blocking
user-visible channel the once-per-session notices ride on.

**How the operator tests it.** In a throwaway project outside the working
directory: a deliberately broken config, then a Bash call, and observe
the deny naming the breakage. **Crosses the boundary**: needs the hook
registered in a live session. Cleanup: delete the throwaway project.

### 016 — Gate two: liveness, selftest, coverage, status — `pending`

**Objective.** The project-facing checks, invocable from pre-commit and
CI, identical to what the hook runs.

**Spec sections.** §8.2 (both checks and the coverage gate), §9
(`liveness`, `selftest`, `status`).

**Deliverables.** **Liveness**: the config loads, every declaration is
structurally valid, reasons are non-empty, a hook payload comes back as a
well-formed verdict, plus the boundary-nullifying shapes — an
unconditional allow on a tool with no grants, a grant with no conditions,
and a declaration shadowing a wrapper without re-declaring its handoff.
No behaviour cases: it stays lint-fast. **Selftest**: liveness, then the
project's cases, then **coverage** — every rule and grant in the
*effective* registry reached by at least one case, *reached* meaning the
rule matched or the grant held, supplied by the project or by the source
that contributed the rule. The engine's default layers stand outside the
gate as shipped; the moment a config shadows one into a rule-bearing
tool, the config owes the cases. **Status**: config presence, engine and
API generation, secure mode, last validation and outcome, the kill
switches when the process environment carries them, and the
visibly-inert statement when the plugin is enabled but the project
unconfigured. Exit statuses usable from scripts; a JSON output option as
the cheap way to keep the stability promise. Derived cases are supported
as a complement, never a replacement for the hand-written corpus.

**How the operator tests it.** In a scratch project with a hand-written
config: `frisk liveness`, `frisk selftest` (green, then break a rule's
spelling and watch coverage fail), `frisk status`. Local and free.

### 017 — Validation on change — `pending`

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
the boundary** for the in-session halves; the CLI halves are local.
Cleanup: delete the scratch project.

## 8. Milestone 7 — Distribution, adoption and the boundary's own files

### 018 — The plugin, the marketplace and engine resolution — `pending`

**Objective.** One codebase, two doors, at the same version — and a CLI
that can never answer with an engine the hook does not run.

**Spec sections.** §2.2, §11, §9 (the resolution requirement and
same-configuration), §8.2 (the CI pin).

**Deliverables.** `.claude-plugin/plugin.json` and the marketplace
manifest making the repository its own marketplace; the hook declared by
the plugin; `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_PROJECT_DIR}` used only
where Claude Code supplies them, never by anything runnable from a
terminal or CI. Plugin code treats its own location as read-only and
version-unstable. The resolution rule keyed to the observable condition:
wherever an installed plugin is resolvable its engine answers, wherever
none is the project's recorded pin does, and in **every** context the CLI
states which engine version answered — never a refusal, never an
unattributed answer. Resolution must expose **which door answered**,
because §7.4's sentinel requires a plugin-resolved engine specifically.
Same-configuration alongside same-engine: the CLI and the hook resolve
the *same* config for a given project, failing loudly when the resolution
is ambiguous. The engine version the project pins for CI, recorded beside
the configuration. JSON parse checks extend to both manifests.

**How the operator tests it.** Install the plugin from the local
repository into a throwaway project and run `frisk status` and
`frisk explain` from both doors, reading which engine answered each time.
**Crosses the boundary**: installing a plugin or a marketplace into the
operator's live Claude Code needs explicit authorisation in that
exchange. Cleanup: uninstall the plugin and the marketplace, delete the
throwaway project.

### 019 — The verification pass, part two — `pending`

**Objective.** The three open facts that need an installed plugin to
measure.

**Spec sections.** §2.2 (inventory items 6, 7, 8), §12 (the record).

**Deliverables.** **item 6** the per-plugin persistent data directory —
if none exists, durable state degrades to session scope: a documented
limitation, so it **comes back to the operator**. **item 7**
plugin-configuration delivery to hooks as environment variables — if
values do not reach hooks, `015`'s machine-level dial simply has no
carrier and the engine default stands unrelaxed. **item 8**
project-recommended-plugin prompting — a prompt, if one exists, softens
the sentinel's rationale without replacing it. Amendments and record
entries per `013`'s two-places rule.

**How the operator tests it.** Read the record additions and the
amendment commits. **Crosses the boundary**: needs the plugin installed
in a live Claude Code and spends usage. Cleanup as `018`.

### 020 — The starter registry — `pending`

**Objective.** The boundary a freshly scaffolded project gets on day one.

**Spec sections.** §5.4 (the starter registry and its two deliberate
acceptances), §8.2 (starter cases from day one).

**Deliverables.** The **git ground rules**, required and identical across
projects: deny on forced, mirror and delete pushes however spelled,
history rewriting, and destruction of git's recovery data; ask on any
push, commit amendment, rebase, hard/merge resets, clean, restore, the
work-discarding forms of checkout and switch, stash dropping and
clearing, branch and tag deletion or forced movement, worktree removal
and pruning, and the presence of a config-override option (`-c`,
`--config-env`) — the sibling spelling of the assignment danger, since a
boundary that gates one spelling and not the other gates neither. Allow:
exactly §6.3's commit-message shape with its hedges, if `014` kept the
verdict. **docker** with its drop-in equivalents as aliases, shaped per
§5.4. Starter cases covering **every** starter rule, so the coverage gate
passes from day one. The two deliberate acceptances stated where an
operator reads them: host mounts on `docker run` stay silent, and `rm` is
not in the starter registry. The starter registry is the first
**collection** — a unit the config adopts and may trim — so §3.4's
composition mechanism has its day-one consumer.

**How the operator tests it.** `frisk selftest` against a scaffolded
project (once `021` lands, or against the starter set directly here) and
`frisk explain` on each ground rule's dangerous spellings. Local and
free.

### 021 — The scaffold and the pairing guidance — `pending`

**Objective.** Adoption possible without archaeology — the parity floor
of §13's item 9.

**Spec sections.** §5.1 (location, lifecycle, trust), §5.4 (the
scaffold), §6.1 (the pairing guidance, mode-aware and honest about what
rule 1 trades), §3.5 (the API-generation declaration).

**Deliverables.** The scaffold creating the configuration directory
inside the target project's `.claude/` — the name carries the plugin's
name — pre-filled with the starter registry, the API-generation
declaration, and the starter cases. Created **only** on the operator's
request, and **never touched by an unattended write afterwards**: the two
write paths are the scaffold at creation and the skill applying a change
the operator has just approved. The **one-pass review** is what makes
scaffold-time writing legitimate. The pairing guidance produced in
written, guided-manual form: rule 1's broad allows scoped to the tools
whose configuration can return silence or allow — never a
deny-everything tool, never the engine's default layers, so generated
guidance never suggests `Bash(sudo:*)` or an allow for `cat`; rules 2–5,
each with the silent failure it prevents; the deny backstop as a package
with the broad allows; the mode-aware picture with §6.1's scoped claims,
carrying whatever `013` measured about each mode rather than the
comfortable misreading. **Explicit approval before every settings edit
the tooling performs, scaffold time included.**

**How the operator tests it.** Scaffold a throwaway project, read the
generated config in one pass (the legibility requirement is this test),
run its selftest green, and read the pairing guidance. Local and free
except where the operator chooses to apply the settings edits.

### 022 — The sentinel and the kill switches — `pending`

**Objective.** The deaths the plugin cannot see because it is absent or
inert.

**Spec sections.** §7.4 (the sentinel, its probe, its standing state, the
kill switches), §2.3 (why it is shell), §7.5 (the coverage map's rows).

**Deliverables.** A tiny, self-contained POSIX-shell PreToolUse hook,
**offered and never imposed**, committed to the target project's
settings. Once per session, keyed by the payload's session identifier, it
**probes by execution** — running the engine's liveness entry through the
same project entry point and resolution the CLI uses — and requires
success **from a plugin-resolved engine specifically**: a pin-answered
probe is a *failure* for its purpose, because a working engine with no
installed plugin means no hook is running. It further requires that the
project's configuration loads. On failure it denies Bash with a message
naming the exits appropriate to what it observed — install and enable the
plugin; fix or install `python3`; a **distinct** message when the engine
is installed but cannot be located; and always, remove the sentinel if
this clone genuinely does not want the guard. A failed probe is the
session's **standing state**, not a one-shot message: every subsequent
Bash call is denied while the failure stands, and the cache remembers a
*success*, never a failure. In a sentinel-adopted project a broken config
denies **regardless** of §7.1's machine-level relaxation. Both kill
switches — the sentinel's and the wholesale one, which silences the
sentinel too — read from the hook's **own** process environment, so an
`export` inside a tool call can never reach them; both announce
themselves once per session through the non-blocking channel, the
sentinel-only switch included. The shell check family already exists from
`000`.

**How the operator tests it.** In a throwaway project: adopt the
sentinel, then disable the plugin and watch Bash deny with the install
message; restore it and watch the deny lift mid-session; set each kill
switch when launching and watch the announcement. **Crosses the
boundary**: needs live sessions and plugin enable/disable. Cleanup:
re-enable the plugin, delete the throwaway project.

### 023 — Gate three: the reachability probe — `pending`

**Objective.** The one check that exercises the whole chain.

**Spec sections.** §8.3, §10 (the skill guiding it).

**Deliverables.** The documented procedure for direct use: issue a
command the config refuses and verify it comes back refused **by the
guard, citing its rule** — merely prompting means the hook is not
reaching the tool call and only the deny backstop is left. Documented for
running at adoption, after settings changes, and whenever §7's layers
report nothing but doubt remains.

**How the operator tests it.** Run the probe in a scaffolded throwaway
project and read the citation. **Crosses the boundary**: a live session.
Cleanup: delete the throwaway project.

## 9. Milestone 8 — Parity

### 024 — The corpus parity audit — `pending`

**Objective.** Declare parity against the yardstick, or name exactly what
is missing.

**Spec sections.** §8.1 (the corpus as the parity yardstick), §13 (the
pre-1.0 bar).

**Deliverables.** Every corpus ruling reproduced or accounted for:
asserted, superseded by a verification-pass outcome (the allow rulings if
open fact (c) retired the verdict — these **count as satisfied** and do
not block the declaration), or reported as a specification conflict where
a ruling and the specification disagree — the specification wins and the
conflict is reported, never silently implemented. A written parity
statement against §13's bar, item by item, with anything outstanding
named.

**How the operator tests it.** Read the parity statement; `just test`
green with the corpus fully asserted. Local and free.

### 025 — The dev guard retires — `pending`

**Objective.** frisk takes over guarding its own repository; the
prototype apparatus of rule 1 ends whole.

**Spec sections.** §5.4, §6.1 (this repository's own pairing), §8.3.

**Deliverables.** The first dogfood install: scaffold this repository,
write its configuration, and pair its settings per frisk's own §6.1 — put
to the operator for review as `001`'s baseline was — ending with the
reachability probe. Then the **sweep of every committed reference to the
apparatus** — the sweep, not this list, carries the completeness claim,
and these are the named anchors: `.claude/hooks/bash_guard.py`; the
backup ref (the remote copy's fate proposed to the operator in this
step); the gitignore entries; the `--liveness`/`--selftest` harness
wiring; the hook registration in `.claude/settings.json`;
`approve-step`'s backup-ref push step; the `code-reviewer` and
`state-reviewer` path exclusions; `optimize-memory`'s whole-carry
extension; `.claude/docs/guard-record.md`; and rule 1's quarantine text
in `CLAUDE.md`. Nothing of the apparatus outlives its purpose.

**How the operator tests it.** Review the pairing proposal, run the
reachability probe in this repository, and confirm the sweep leaves no
reference behind (`git grep` for each anchor). **Crosses the boundary**:
installs frisk into the operator's live Claude Code for this project.
Cleanup: none intended — this is the intended end state.

### 026 — Minimal README and SECURITY.md — `pending`

**Objective.** The trust statement a permission-path tool must not ship
without.

**Spec sections.** §12 (README, SECURITY.md), §13 (what the first public
tag owes), §1 (the scope statements), §5.1 and §15 (the trust model).

**Deliverables.** `README.md` at the repository root: what frisk is and
is not, installation, the scaffold quickstart, the settings pairing with
§6.1's reasoning and its scoped claims, and pointers to the rest — with
**"in development, install only for testing"** stated prominently, a
warning removed at 1.0. Formatting quality is an explicit requirement,
not a nicety. `SECURITY.md` at the root: the trust model (the config is
operator-owned code, at exactly the trust level of a hand-written hook),
what the guard is and is not a defense against, the fail-open residue and
its mitigations, and how to report vulnerabilities. **This step resolves
the scheduled `README.md` collision**: the workflow entry-point content
written at bootstrap migrates to a home proposed as a logged decision,
and every template naming `README.md` — reviewer frames and staleness
sweeps alike — is re-pointed in the same commit.

**How the operator tests it.** Read both documents and answer "do I want
this in my permission path?" from the README alone. Local and free.

### 027 — CI for release, and the first public tag — `pending`

**Objective.** The plugin's own CI proving what §11 requires, and the
first release.

**Spec sections.** §11 (packaging, distribution, versioning), §8.1 (gate
one across an interpreter matrix).

**Deliverables.** CI extended on `004`'s workflow: gate one across an
interpreter matrix — the floor version and a current one at minimum,
before any release — plus packaging validation, which **includes proving
the shipped starter content**: scaffold into a throwaway project and run
its selftest, so the starter registry's spellings (the force-push denies
above all) are demonstrated before release rather than by the first
adopter, without weakening §8.1's engine/policy test separation. A
changelog, carrying every behavior-visible change. Semver on the plugin,
with the API generation moving on **any** breaking release during 0.x.
The release itself: a GitHub release with a zip archive carrying an
explicit pin in the marketplace entry, so what users install is
attestable. MIT license.

**How the operator tests it.** Watch the matrix run green, then authorise
the release. **Crosses the boundary**: a release publishes to the plugin's
install channel. **External prerequisite**: GitHub release capability.
Cleanup: a release can be deleted but not un-fetched — this is a
deliberate one-way step.

## 10. Milestone 9 — Toward 1.0

Staged per §13's second bullet: the full surface of the specification at
requirement tier. These steps are stated at coarser grain than the
milestones above and are refined when the milestone is reached — the
plan's early steps are where precision earns its cost.

### 028 — Export modeling — `pending`

§4.2's `export NAME=value` segment establishing assignments for every
subsequent invocation in the same tool call, entering §3.2's accounting.
The family's edges (`declare -x`, `unset`, valueless `export NAME`) stay
declared blind spots rather than half-modeled. Removes one line from the
honesty document.

### 029 — Control structures in full — `pending`

§4.3's full treatment: keywords in command position stepped past so
bodies are judged, headers contributing nothing, function bodies judged
at **definition** so a later bare call cannot launder what they contain,
and anything the walk cannot follow routed to §4.1's fallback. Replaces
`012`'s routing minimum.

### 030 — The remaining declaration shapes — `pending`

§4.3's two command-running shapes: the option-introduced,
terminator-bounded handoff (`find -exec … +`) and the stdin-fed runner
(`xargs`), whose inner command is judged on its visible parts with
operand-requiring conditions unprovable. Plus §4.3's rule-based
**redirection target matching**, which lets §6.1 rule 5 stop riding on
the native file-tool path rules alone.

### 031 — Secure mode operational — `pending`

§3.2's configurable global default verdict exposed as the config switch
with its reason, off by default, with the operator guidance §6.1's
mode-aware section owes and whatever `013` measured per mode.

### 032 — The compatibility contract in full — `pending`

§3.5's contiguous generation range with supported → deprecated → dropped
handling, internal fallbacks and migrations where a change permits, and
the visible nudge on a deprecated generation.

### 033 — The maintenance skill — `pending`

§10 in full, shipped at `skills/frisk/SKILL.md` in the plugin tree:
adoption (scaffold, pairing walkthrough with explicit approval before
every settings edit, sentinel offer, closing with the reachability
probe); teaching the model the boundary, optionally; **the surprise
loop** — explain, draft the most precise rule change, draft the
reproducing case, present both stating what would newly be allowed and
what newly gated, and wait; migration, working on the configuration **as
text**; and doctrine enforcement in dialogue — the allow doctrine's
argument demanded, a git ground rule's weakening treated as reportable,
and **shapes over lists** when drafting grants. Every rule change is the
operator's call; the skill never edits the configuration on its own
initiative.

### 034 — The CLI in full — `pending`

§9's complete surface: `explain` **showing its work** — which invocations
were found through which walls of §4.3 — the JSON output option, and
`status` complete. Plus §12's working **status-line sample** consuming
the CLI's output.

### 035 — The once-per-session visibly-inert notice — `pending`

§5.4's notice through the non-blocking channel, making no distinction
between never-scaffolded and a config that stopped existing — the second
being the sharper danger. Owed at 1.0 per §13; closes the residue that
step named.

### 036 — The remaining documentation — `pending`

§12's four outstanding deliverables at `docs/`: the **operator
configuration reference** (every declaration, its conditions, its fail
direction, and **every engine default layer enumerated in full** —
wrappers, baseline read tools, walked interpreters); the **honesty
document** (§4.4's blind spots and §7.5's residue map, stated as plainly
as in the specification); the **platform verification record** completed;
and **CONTRIBUTING.md** at the root (engine changes come with corpus
cases, behavior changes are changelog-visible, and the specification's
doctrine sections are the review bar). The README grows to its full §12
shape and the "install only for testing" warning is removed.

### 037 — End-to-end checks, explored — `pending`

§8.1's third level, a **should**: driving a real Claude Code session in
CI and observing the hook decide, and exercising the skill if the
platform's plugin-evaluation tooling permits. This depends on facilities
outside the project's control; **declining it is an expected outcome the
specification allows**, logged with what was found. Never a substitute
for the two layers above it. **Conditional external prerequisite**: a
CI-drivable Claude Code environment and its credential.

### 038 — 1.0 — `pending`

The stability promise: from here the config-facing API moves only by
§3.5's rules. Release per `027`'s machinery.

## 11. Open facts — the settling ledger

Each item of §2.1's inventory, and each lettered fact, named with the
step that settles it. A section-level "verified along the way" is not a
mapping.

| Item | What | Settled at |
|---|---|---|
| (a) | Hook allow's sandbox waiver | `013` |
| (b) | Settings deny/ask precedence over hook decisions | `013` |
| (c) | The substitution-prompt trigger — the go/no-go | `013`, before `014` |
| (d) | Hook deny/ask survival per permission mode | `013` |
| 5 | The platform hook-timeout default, sizing the internal budget | `013`, consumed at `015` |
| 6 | The per-plugin persistent data directory | `019` |
| 7 | Plugin-configuration delivery to hooks as environment variables | `019` |
| 8 | Project-recommended-plugin prompting behaviour | `019` |
| 9 | Settings deny/ask enforcement under each permissive mode | `013` |
| 10 | Prefix-rule word-boundary behaviour | `013` |
| 11 | The platform's built-in read-only command handling | `013` |
| 12 | The Python-floor table of OS-shipped interpreters | `005` |
| 13 | Whether the Bash tool persists shell state across tool calls | `013` |

Items 6, 7 and 8 are at `019` rather than `013` because each needs an
installed plugin to measure, which `018` delivers.

## 12. Specification coverage

Every section of `SPECIFICATIONS.md`, mapped.

| Section | Steps |
|---|---|
| §1 Goal | `026` (README scope statements), `036` |
| §2.1 The hook contract | `013`, `015` |
| §2.2 The plugin system | `018`, `019` |
| §2.3 Runtime | `005` (floor), `022` (why the sentinel is shell) |
| §2.4 Prior art | Informational; positions the README at `026`. No implementation deliverable. |
| §3.1 Three parts, one trust split | `005`, and the architecture across `006`–`021` |
| §3.2 The decision model | `008`, with matchers at `007` and secure mode operational at `031` |
| §3.3 Fail directions | `006`, `008`, and asserted throughout the engine suites |
| §3.4 Composition and layering | `007`, first consumer at `020` |
| §3.5 The compatibility contract | `007` (layers 1–2), `017` (layer 3), `032` (the full range) |
| §4.1 Reading the line | `006` |
| §4.2 What binds to an invocation | `006`, export modeling at `028` |
| §4.3 Seeing through | `009`, `010`, `011`, `012`; full control structures at `029`; the two runner shapes and redirection target matching at `030` |
| §4.4 Declared blind spots | `036` (the honesty document); interim gaps named at `012` and `026` |
| §4.5 Proportion | `006`, `008`, and a standing focus of every code review |
| §5.1 Location, lifecycle, trust | `021`, `026` (SECURITY.md) |
| §5.2 What the configuration must express | `007` (API against the whole surface), staged behaviour across `008`–`011`, `030` |
| §5.3 Legibility | `007`, `036` (the operator reference) |
| §5.4 The scaffold | `020`, `021`; the visibly-inert notice at `035` |
| §6.1 Pairing | `013` (the facts), `021` (the guidance), `026` (the README section) |
| §6.2 Reasons and citations | `008` |
| §6.3 The allow doctrine | `014` |
| §7.1 Fail closed at runtime | `015` |
| §7.2 Validation on configuration change | `017` |
| §7.3 Validation on engine change | `017` |
| §7.4 The sentinel | `022` |
| §7.5 The coverage map | `022`, `036` |
| §8.1 Gate one | Suites in every engine step; the corpus at `012` and `024`; the end-to-end should at `037` |
| §8.2 Gate two | `016` |
| §8.3 Gate three | `023` |
| §9 The CLI | `005`, `008`, `016`, `018`; complete at `034` |
| §10 The maintenance skill | `021` (adoption, guided-manual), `033` (the full loop) |
| §11 Packaging, distribution, versioning | `018`, `027` |
| §12 Documentation deliverables | `026` (README, SECURITY.md), `013`/`019` (the verification record), `036` (the rest) |
| §13 Release path | This plan's structure and §1's re-inventory |
| §14 Future Considerations | **Excluded from this pass**, by the specification's own staging: rule collections beyond the project, the declarative configuration layer, transcript mining, the guard-internal decision log, user-global configuration, and native Windows support. §3.4's composition, §2.2's data directory and §3.5's stability keep each adoptable later. |
| §15 Non-Goals | **Excluded by definition**; stated in SECURITY.md at `026` and the honesty document at `036`. |

## 13. External prerequisites

Things only the operator can prepare, each with the step that first needs
it.

| Prerequisite | First needed |
|---|---|
| `just` installed on this machine | `000` |
| A private backup remote for rule 1's backup ref | `001` |
| The forge, the remote, and authorisation of the first push (the public repository is also the plugin's install source, so adoption testing waits on it) | `004` |
| A second strong model for the milestone passes — the state review and the memory compaction must not run on the model that wrote the work | the foundation-milestone close, after `004` |
| An interpreter at the committed floor (rule 2's floor-pinned checks need it) | `005` |
| The verification-pass trio: consent to drive sessions in the permissive modes, a scratch area outside the working directory, and the platform version recorded with every measurement | `013` |
| Authorisation for any install into the live Claude Code — plugin or marketplace | `018` |
| GitHub release capability | `027` |
| *Conditional*: a CI-drivable Claude Code environment and its credential, for §8.1's end-to-end should — declining it is an expected outcome | `037` |

The behavior corpus is already delivered at
`.claude/refs/behavior-corpus.md`; nothing waits on it.

## 14. Open questions

Underspecified, risky, or worth reordering — for the operator, never
silent assumptions.

1. **The `001` split (`D-003`).** This plan turns the prescribed `001`
   into two gates. If the operator would rather review the baseline and
   its probes together, `001` and `002` merge back and the numbering
   shifts down by one.
2. **The §13 re-inventory ruling (`D-004`).** Section 1 recommends the
   bar stands as drawn. The operator rules; a "move" on any row
   re-stages that item into Milestone 9.
3. **Milestone 4's placement.** The verification pass sits after the
   engine's spine rather than before it, because none of the parsing work
   depends on its outcomes and the cheap-first rule applies. The risk is
   that a surprising outcome — (b) demoting pairing rule 2, (d) finding a
   mode that swallows `ask` — arrives after four engine steps are
   written. Nothing in `006`–`012` would change; only `014`, `021` and
   the documentation would. Confirm the trade is the one the operator
   wants.
4. **`014` may become a retirement.** If open fact (c) says the platform
   no longer prompts on substitutions, §6.3's whole apparatus retires to
   silence. The plan does not pre-judge, but the operator should know
   that one measurement can delete a milestone.
5. **Milestone 9's grain.** Steps `028`–`038` are coarser than the rest
   deliberately: refining them now would be planning against a system
   whose earlier half does not exist. They are refined when Milestone 8
   closes. If the operator wants them sized now, say so.
6. **The config directory's name.** §5.1 leaves it to the implementation
   and says it "should carry the plugin's name". This plan assumes
   `.claude/frisk/` in a target project and will log it at `021`.
7. **Two conditional documentation obligations.** §4.3 and §4.4 require
   interim gaps to be *named in the honesty documentation* — but that
   document is a 1.0 deliverable (`036`), while the gaps exist from
   parity. This plan names them in the pre-1.0 README (`026`) instead. If
   the operator would rather a minimal honesty document ship at parity,
   that is a small step to add before `026`.
8. **Packaging shape.** Rule 4 leaves it to the implementer; this plan
   assumes `pyproject.toml` with a `src/frisk/` layout and a `frisk`
   console entry point, logged at `005`. Flagged because it decides how
   the CI matrix and the repository-installable door look.
