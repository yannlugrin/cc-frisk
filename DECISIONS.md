# Decisions

The decision log for the implementation of frisk. It records **why** the
implementation looks the way it does, so that a later session — or a
reviewer, or the operator six months from now — can evaluate a choice
rather than rediscover it. `SPECIFICATIONS.md` says what to build;
this file says what was decided along the way and on whose authority.

## Entry format

Entries are appended in file order and numbered `D-NNN` from `D-001`.
**An id freezes when it is assigned and is never reused**, even if the
decision is later reversed — a reversal is a *new* entry citing the old
one. Every entry carries these fields, in this order:

```markdown
### D-NNN — <short title>

- **Date:** YYYY-MM-DD
- **Step:** <step id, or `—` for decisions belonging to no step>
- **Context:** what made a decision necessary.
- **Decision:** what was decided, stated so it can be checked against
  the code.
- **Alternatives considered:** what else was on the table and why it
  lost. An entry with no alternatives is a decision that was never
  really made.
- **Approved by:** `operator`, or `implementer (within latitude: …)`
  naming which latitude — the specification's *should* tier, or a
  workflow choice the bootstrap instructions left open. One transitional
  value is sanctioned: `*pending* — put to the operator at <event>`, for
  an entry written before the exchange that decides it. A later session
  resolves it to one of the two real values; it is not a format
  violation to be "fixed".
```

Three kinds of decision belong here (rule 4):

1. **Joint decisions** — specification changes, scope calls, step
   reordering. Approved by the operator.
2. **Within-latitude decisions** — the specification permits deviating
   from a recommended default *with reason*; the reason goes here.
   Approved by the implementer, naming the latitude.
3. **Workflow decisions** — what the bootstrap instructions left open:
   the harness's shape and names, `.gitignore` contents, which tooling
   templates are adopted. Approved by the implementer, naming the
   latitude. **The permission baseline is not in this latitude**: step
   `001` always puts it to the operator.

Two conventions the format depends on:

- **Specification amendments** (rule 1) are written *before* the
  amendment, never as a rationalisation after it, and the entry and the
  specification text land in **one commit** carrying nothing else, with
  the subject naming the decision
  (`step-NNN: spec amendment — D-NNN, …`). The entry lands alone only
  when the amendment belongs to a later step, and then it says so and
  names that step.
- **Steps not yet started are cited by number *and* title**, so a
  renumbering that misses a reference still leaves it decodable.

## Entries

### D-001 — Adopt the file-based, operator-gated implementation workflow

- **Date:** 2026-08-19
- **Step:** — (bootstrap)
- **Decision:** Adopted the operator's bootstrap workflow in full and
  permanently: `SPECIFICATIONS.md` read-only for the implementer, one
  operator-gated step at a time with nothing handed over unverified, all
  memory in `PLAN.md`/`DECISIONS.md`/`CLAUDE.md`/`.claude/docs/`,
  decisions logged here, secrets never committed, small step-prefixed
  commits carrying their own documentation, English, `README.md` as the
  neutral entry point, bug reports driven within a stated free-act
  boundary, and persistence with a budget. Without a memory that survives
  session boundaries, each session would re-derive project state from
  code and the decided/open boundary would erode silently — the failure
  mode this project exists to prevent one layer up. `CLAUDE.md` restates
  the rules under the bootstrap's own numbering, because tooling and
  later entries cite them by number.
- **Approved by:** operator (the bootstrap prompt is the approval).

Detail in git history.

### D-002 — `CLAUDE.md`'s size budget, derived rather than inherited

- **Date:** 2026-08-19
- **Step:** — (bootstrap)
- **Decision:** Set this project's `CLAUDE.md` budget at 390 lines hard /
  ~365 at first handover, replacing rule 3's generic 220/180 baseline —
  derived from the file's two whole-carry blocks (rule 9's boundary
  enumeration, rule 1's guard quarantine) plus the nine restated rules
  and the plan/tag-message carriers, because a repository whose rules
  carry long whole-carry text has a higher floor than the generic
  baseline assumes, and a budget first met by breaching it teaches the
  next session the budget is decorative. Two shrinks were scheduled on
  arrival — step `004` (tooling-templates block) and the parity
  retirement step (`PLAN.md` `027`, the quarantine) — each re-derived
  downward rather than kept as slack. **Superseded by `D-014` → `D-016`
  → `D-024`**, which is the number `CLAUDE.md` currently states.
- **Approved by:** implementer (within latitude: rule 3's derive-and-log
  clause).

Detail in git history.

### D-003 — Split two of the prescribed foundation steps

- **Date:** 2026-08-19
- **Step:** `000`–`005` (the foundation milestone)
- **Decision:** Split the bootstrap's four prescribed foundation steps
  into six: `001` (guard + settings baseline) split from `002` (the probe
  campaign), and the tooling step split into `003` (skills) and `004`
  (agents), with CI as `005`. The prescribed four would have put a
  settings proposal, a session restart and a probe campaign behind one
  operator gate, and would have written five agents against an
  unmeasured context assumption whose correction would only arrive after
  the session was already spent — the bootstrap instructions themselves
  invite this split for exactly this reason. All six stay one milestone;
  CI stays last, since the repository is not bootstrapped until its CI
  runs green.
- **Approved by:** operator (2026-08-19, at the plan review).

Detail in git history.

### D-004 — The §13 re-inventory ruling

- **Date:** 2026-08-19
- **Step:** — (the plan's first artifact)
- **Decision:** §13's pre-1.0 parity bar stands as drawn — every accreted
  item survives its own placement challenge (`PLAN.md` §1), three of them
  as cheap riders on machinery the bar already owes and the starter
  registry's docker shape turning out to be pinned by the parity
  yardstick rather than deferrable. Two placements were noted rather than
  challenged: the once-per-session inert notice (already staged at 1.0 by
  §13) and the sentinel (returned to its 1.0 stage by `D-007`). The
  ruling and each item's assessment live in `PLAN.md` §1.
- **Approved by:** operator (2026-08-19, at the plan review).

Detail in git history.

### D-005 — Declarations before reading the line

- **Date:** 2026-08-19
- **Step:** `007` (declarations, matchers, layering) and `008` (reading
  the line)
- **Decision:** Build the declaration model, matchers and layering
  (`007`) before line reading (`008`), reversing the plan's first draft —
  declared flag arities, alias and path recognition and the
  gated/registered/rule-bearing distinction are all defined in terms of
  declarations, so a step whose gate cannot be reached without the next
  step's output is not a gate. `007` additionally ships the
  effective-registry inspection surface §3.4 requires, which is what
  makes it testable before any verdict exists.
- **Approved by:** operator (2026-08-19, at the plan review).

Detail in git history.

### D-006 — The verification pass split into two gates

- **Date:** 2026-08-19
- **Step:** `015` and `016`
- **Decision:** Split the verification pass by apparatus rather than by
  fact: `015` settles the go/no-go open fact (c) together with the
  mode-independent inventory items 5, 10, 11 and 13 — cheap, no
  permissive modes; `016` settles the permissive-mode matrix — open facts
  (a), (b), (d) and item 9. The plan's first draft settled all nine in
  one step, four escalating to the operator mid-step, making it the
  plan's most expensive step and the hardest to resume from mid-flight.
- **Approved by:** operator (2026-08-19, at the plan review).

Detail in git history.

### D-007 — The sentinel restaged to 1.0

- **Date:** 2026-08-19
- **Step:** `035` (was inside the pre-parity milestones)
- **Decision:** Move the sentinel and both kill switches to `035`
  (Milestone 9), restoring §13's own staging rather than challenging it —
  §13's pre-1.0 bar is a closed list that does not name them, and its 1.0
  bullet names "the sentinel offer" explicitly. Consequence stated rather
  than hidden: before 1.0, two rows of §7.5's coverage map ("plugin
  absent", "config absent") have no catcher, named again at `026`'s
  parity statement. Recorded as a live choice, not a formality: pulling
  the sentinel back before parity stays available if the residue proves
  uncomfortable in use (carried in `CLAUDE.md`'s open obligations).
- **Approved by:** operator (2026-08-19, at the plan review).

Detail in git history.

### D-008 — Milestone 9's entries are deliberately coarse

- **Date:** 2026-08-19
- **Step:** `030`–`041`
- **Decision:** Milestone 9's twelve entries carry objective and
  deliverables only, without the spec-section list, locations and test
  statement `CLAUDE.md`'s plan conventions otherwise require, staying
  that way until Milestone 8 closes — sizing test instructions against a
  system whose earlier half does not exist produces text rewritten
  before it is used. Surfaced in `PLAN.md` §14 for the operator to
  overrule.
- **Approved by:** implementer (within latitude: a workflow choice the
  bootstrap instructions left open).

Detail in git history.

### D-009 — The starter registry ships git ground rules only

- **Date:** 2026-08-19
- **Step:** `023` (the starter registry)
- **Context:** §5.4 requires the starter registry to carry git's ground
  rules and recommends, as a *should*, "a small set of additional common
  tools", naming docker as the candidate with a shape to match. This
  plan's first re-inventory argued docker could not be deferred because
  the behavior corpus's context A runs 109 rulings against a git-and-
  docker registry, so deferring it would make §13's parity item 1
  unreachable. **That argument was wrong**, and the operator identified
  why: the corpus's docker rulings demonstrate what the *engine and the
  configuration surface* must be able to express — handoffs, aliases,
  publish-capable build flags, compose forms — not what the *scaffold*
  should write into a project that has just adopted frisk. The two are
  not merely separable; §8.1 requires them separated, engine tests
  running "against test-only tool declarations, never against real-tool
  starter rules". The plan's own step `014` already said so, which is
  where the contradiction was visible.
- **Decision:** The shipped starter registry carries the git ground rules
  and nothing else. Docker's policy shape survives in two places that
  cost a new project nothing: the corpus fixtures of step `014`, which
  prove the engine expresses it, and a worked example in the operator
  configuration reference (step `039`), which is how an operator who
  wants docker gated writes it. The capability stays owed at parity; the
  default content does not. §13's bar is unaffected: item 1 is satisfied
  by the fixtures, item 2 by the expressible surface the corpus's
  policies define, and item 9 by a scaffold that still gives a meaningful
  day-one boundary.
- **Alternatives considered:** *Shipping docker in the starter registry
  as §5.4 recommends,* rejected by the operator: a rule set proving the
  engine can express docker policy is not a reason to gate docker in
  every adopting project by default, and the one-pass review is a poor
  moment to make somebody accept rules for a tool they may not use.
  *Shipping docker as an opt-in collection beside the starter registry,*
  which §3.4's composability would carry cheaply — rejected here as
  building ahead of need (rule 11): the operator asked to be able to
  write docker rules, not to be offered a ready-made set. It stays a
  §14 rule-collections item, precluded by nothing.
- **Approved by:** operator.

Detail in git history.

### D-010 — `check` snapshots and restores rather than repairing

- **Date:** 2026-08-19
- **Step:** `000` (the harness)
- **Decision:** `scripts/check.sh` snapshots the file list to a temp
  directory before running the fixer hooks, compares afterward, restores
  what was rewritten, names it and fails — because `check` must assert
  without repairing (fixer hooks like `trailing-whitespace` may write
  only in the commit hook), and no standard mechanism does this:
  `pre-commit` has no check-only mode, `git checkout --` is a
  protected-tree write and cannot restore untracked files at all. The
  revert runs from an `EXIT` trap so an interrupt restores too. No git
  operation is involved. Mechanism documented in `.claude/docs/harness.md`.
- **Approved by:** implementer (within latitude: a workflow choice the
  bootstrap instructions left open). **Process note:** rule 2 asks that a
  mechanism built because nothing standard fits be put to the operator
  before it is built; that step was skipped here. Reversible on request.

Detail in git history.

### D-011 — The permission baseline: broad allows, a guard, a short deny backstop *(amended; evolution in git history)*

- **Date:** 2026-08-20
- **Step:** `001` (the permission and hook baseline)
- **Decision:** `.claude/settings.json` is shaped around the guard rather
  than duplicating it (rule 9's boundary is never the implementer's to
  set): `acceptEdits` mode with the bypass lock, `auto` left reachable
  for `002`'s comparison; one broad allow per registry-bearing tool so
  the guard is what judges them, plus a short read-only-utility
  allowlist; no broad allow for any runner (a real, accepted friction
  cost — `python3` and its kin now prompt); an `ask` tier on the
  boundary's own files so guard maintenance keeps an unlock path; and an
  eleven-line `deny` backstop confined to unrecoverable acts, binding
  when the hook is dead. Native permission rules match command prefixes
  and cannot express "however spelled" — a parsing guard can, which is
  why the settings are built around it rather than restating it. `chmod`
  was removed from the trivial-write allow group because `chmod -x` on
  the guard is the disarm.
- **`just`'s treatment amended by `D-013`** (exact-match allows →
  `Bash(just:*)`, our own task runner judged safe-by-default). Two
  spellings verified live at `002`: the backstop's force-push pattern
  binds, and an explicit `ask` beats `acceptEdits` for file tools.
- **Approved by:** operator, 2026-08-20, reviewing the baseline and its
  gates as one piece at step `001`'s handover.

Detail in git history.

### D-012 — The boundary is inert exactly where the guard is absent

- **Date:** 2026-08-20
- **Step:** `001` (the permission and hook baseline)
- **Decision:** Two mechanisms, both keyed on the guard's absence being
  safe rather than silent. **(1)** hook registration is self-guarding
  (`exec` if the guard is present and executable, else exit 0 in silence)
  so a public clone with no guard costs nothing. **(2)** both check gates
  (`scripts/check-guard.sh` for `just check`/commit hook, `--selftest`
  for `just test`) key on `refs/backups/bash-guard` — the marker for "the
  guard is expected here" — rather than on the guard file itself, since
  keying on the file would make a deleted guard self-defeatingly quiet,
  and a second marker file would be a second thing to keep true. Linked
  worktrees are named explicitly: the marker is visible (shared git dir)
  while the gitignored guard is not, so both gates fail there and print
  the fix. Twelve states plus the worktree case were probed, not assumed
  (`.claude/docs/harness.md`).
- **Approved by:** implementer (within latitude: a workflow choice the
  bootstrap instructions left open).

Detail in git history.

### D-013 — `just` is safe-by-default: our own task runner is not a dangerous tool

- **Date:** 2026-08-20
- **Step:** none (`meta` — amends `D-011`, which is `001`'s)
- **Decision:** `just` becomes safe-by-default on both sides: in the
  guard's registry it is a rule rather than a closed-world grant (any
  recipe, arguments or redirection silent, a short set of flags that
  break the "our justfile" premise excepted), and in
  `.claude/settings.json` the six exact allows become one `Bash(just:*)`.
  `D-011`'s narrow-allow treatment produced prompts on ordinary work — a
  redirection was enough to leave the proven world — and an enforcement
  mechanism that asks about routine work trains the operator to approve
  without reading, which is the failure this whole project exists to
  prevent. This rests on `CLAUDE.md` rule 2's invariant that no `just`
  recipe ever performs an act rule 9 gates, now load-bearing rather than
  merely stated: the justfile is tracked, reviewed and written by us.
  `pip` stays a grant — its closed world is about network-fetched
  packages, a real risk not ours to vouch for.
- **Approved by:** operator, 2026-08-20, who identified the grant as the
  root cause. `D-011` stands otherwise.

Detail in git history.

### D-014 — `CLAUDE.md`'s budget re-derived at 400 for a rule that grew *(amended; evolution in git history)*

- **Date:** 2026-08-20
- **Step:** — (workflow maintenance, no step)
- **Decision:** Raised the budget to 400 hard / ~375 at handover (from
  `D-002`'s 390/365) after the U-063 doctrine update added ~12 lines
  across two of the nine restated rules (what a `.claude/docs/` file is
  and its disqualifiers; the operator tests behaviour never a document)
  — a budget first met by breaching it teaches the next session the
  budget is decorative, so the number moves rather than the rule getting
  trimmed to fit. `D-002`'s eviction order, never-leaves list and two
  scheduled shrinks (step `004`, `PLAN.md` `027`) stand unchanged.
  **Superseded by `D-016` → `D-024`.**
- **Approved by:** operator, 2026-08-20, ruling on the workflow-update
  triage.
- **Resolved (2026-08-20, `D-016`):** the deferred compaction landed in
  the U-065 pass instead of at `003`; the number was unchanged.

Detail in git history.

### D-015 — Doctrine adopted through U-064

- **Date:** 2026-08-20
- **Step:** — (workflow maintenance, no step)
- **Decision:** This repository is adopted through U-064 (the `specify`
  skill's doctrine changelog); a future update pass reads only entries
  above that id. Of nineteen audited running entries from U-022,
  seventeen came back already satisfied — several because this project's
  own 2026-08-19 handoff review banked them upstream as U-057–U-062. Two
  were behind and applied: U-063 (rule 3 states what a `.claude/docs/`
  file is; rule 2 states the operator tests behaviour never a document;
  the frozen agent templates gain the sweep's fourth question) and U-022
  (the `Current state` permission-mode claim reworded to a behavioural
  classification, version-stamped facts moved to
  `.claude/docs/guard-record.md`). No entry conflicted with a logged
  decision.
- **Approved by:** operator, 2026-08-20, ruling point by point on the
  audit triage.

Detail in git history.

### D-016 — Doctrine adopted through U-065, and the budget given headroom

- **Date:** 2026-08-20
- **Step:** — (workflow maintenance, no step)
- **Decision:** Adopted through U-065, which requires a budget to state
  its headroom explicitly — this repository had tripped the detection
  test twice (389/390, then 400/400). The cap stayed at 400 hard / ~375
  at handover; the headroom came from taking the compaction `D-014` had
  deferred rather than raising the cap again, moving `CLAUDE.md`
  400 → 394 by removing duplication of what rules already stated
  elsewhere (per-step detail the plan already carries, restated
  `.claude/` inventory). **Superseded by `D-024`.**
- **Approved by:** operator, 2026-08-20, ruling to keep the cap at 400
  and take the compaction.

Detail in git history.

### D-017 — The backup remote is named `backup`

- **Date:** 2026-08-20
- **Step:** `003`
- **Decision:** The private backup remote rule 1's `refs/backups/bash-guard`
  push targets is named `backup` — resolved by `/approve-step` via
  `git remote get-url backup`, reporting absence rather than failing when
  it does not exist. The name was left open by the bootstrap and needed
  settling before the first close that resolves a remote "by name" could
  avoid inventing it ad hoc. Recorded in `.claude/docs/guard-record.md`.
- **Approved by:** implementer (within latitude: a workflow choice the
  bootstrap instructions left open).

Detail in git history.

### D-018 — The governance check imports PyYAML from the project venv

- **Date:** 2026-08-20
- **Step:** `003`
- **Decision:** `scripts/check_frontmatter.py` imports PyYAML (pinned
  `PyYAML==6.0.3` in `requirements.txt`) and runs on the project
  interpreter, rather than hand-parsing frontmatter or relying on system
  Python — Claude Code's own YAML parser is what actually parses these
  files, and approximating it without a real parser (rule 11) risks
  missing constructs like folded scalars. `.venv` is guaranteed wherever
  the checks run, since pre-commit itself lives there.
- **Approved by:** implementer (within latitude: a workflow choice the
  bootstrap instructions left open).

Detail in git history.

### D-019 — Python well-formedness joins with the first `.py` file, style waits for `006`

- **Date:** 2026-08-20
- **Step:** `003`
- **Decision:** `scripts/check_frontmatter.py`, this repository's first
  `.py` file, brings the Python check family forward from `PLAN.md`
  `006` — but as well-formedness only (`check-ast`, `debug-statements`,
  already pinned), since a check family must arrive with its first
  artifact and pinning a style tool now would mean fetching an unpinned
  version outside rule 9's local boundary. Style and TOML still join at
  `006`, with the engine, where a body of code exists for a style to be
  about — mirrored in that step's deliverables.
- **Approved by:** implementer (within latitude: a workflow choice the
  bootstrap instructions left open).

Detail in git history.

### D-020 — The agent-name arm of the citation check, deferred then withdrawn

- **Date:** 2026-08-20
- **Step:** `003`
- **Decision:** Originally deferred the citation check's agent-name arm
  to `004` (the five reviewer agents did not exist yet at `003`). Moot:
  `D-022` removed the citation check entirely. Kept because ids freeze.
- **Approved by:** withdrawn, operator, 2026-08-20.

Detail in git history.

### D-021 — `check_frontmatter.py` beside `claude plugin validate`, not instead of it

- **Date:** 2026-08-20
- **Step:** `003`
- **Decision:** Both tools stay, neither folded into the other: `claude
  plugin validate --strict` covers about half the parse question and
  misses exactly the half that fails silently (measured and tabulated in
  `.claude/docs/harness.md`), while our own script is the harness's
  pinned, isolated gate and the validator is the operator's unpinned live
  CLI, wired into neither pre-commit nor CI. The false "nothing in the
  ecosystem asks this" claim (rule 11 skipped before the script was
  written) is struck from the script and the hook config.
- **Revisit at `PLAN.md` `021`**, where the plugin tree lands and the
  validator becomes necessary for the product's own manifest rather than
  optional dev tooling — re-measure and decide there whether the
  duplicated parse diagnostics retire; mirrored in that step's
  deliverables.
- **Approved by:** operator, 2026-08-21, ruling during the U-066 update
  pass.

Detail in git history.

### D-022 — The governance check is a parse check and nothing more

- **Date:** 2026-08-20
- **Step:** `003`
- **Decision:** Cut the governance check to the parse question alone
  (~53 lines): frontmatter present, closed, parses, is a mapping, `name`
  agrees with path, `description` non-empty. Deleted: the citation
  resolver, fenced-code pass, unicode normalisation, the 18-case suite.
  The reason, so this is not re-litigated: `just verify` runs `check`
  before `test` on every invocation against the real tree, so a check
  executed every time needs no suite proving it works — what earns the
  script's place is the one diagnostic no other tool provides, `name`
  against path (`D-021`).
- **Approved by:** operator, 2026-08-20, choosing "parse check only, no
  suite" from three options put to them. Two process failures are
  recorded: rule 11 was not asked before the script was built, and its
  size was never put up for a ruling either.

Detail in git history.

### D-023 — Doctrine adopted through U-066, less one contradicted fact *(amended; evolution in git history)*

- **Date:** 2026-08-21
- **Step:** — (workflow maintenance, no step)
- **Decision:** Adopted through U-066, drawn largely from this
  repository's own step `003`. Three repairs applied: rule 2 now states
  that `just verify` runs `check` before `test`, so the check half needs
  no suite; `D-018`'s false ecosystem claim is struck; the `claude plugin
  validate` measurement moved from `D-021` into `.claude/docs/harness.md`
  with version, method and re-measure recipe. One clause declined on
  measurement: U-066's claim that the validator "passes silently on
  frontmatter that does not parse" holds only for the narrower case where
  the malformation swallows the closing delimiter — measured on 2.1.238,
  corrected form in `harness.md`.
- **Approved by:** operator, 2026-08-21, approving the U-066 triage and
  the `D-021` amendment.
- **Refined (2026-08-21, `004`):** re-measured across all seven failure
  classes; the decision was unaffected and both rows now live in
  `harness.md`.

Detail in git history.

### D-024 — `CLAUDE.md`'s budget re-derived at 390, the shrink `D-002` scheduled *(amended ×2; evolution in git history)*

- **Date:** 2026-08-21
- **Step:** `004`
- **Decision:** Re-derived the budget to 390 hard / ~365 at handover
  (from `D-016`'s 400/375) after `004` deleted the tooling-templates
  block `D-002` had scheduled as a shrink — a budget left standing after
  the thing it measured is gone is slack, and slack makes the next
  number unbelievable. The deletion actually removed 17 lines, not the
  scheduled 10; only 10 were subtracted, since rule 3 requires a budget
  to land above what the file owes and never at it. This left
  `CLAUDE.md` at 382 lines, 17 over the ~365 handover figure, with the
  trim-or-raise choice put to the operator.
- **Approved by:** implementer (within latitude: rule 3's derive-and-log
  clause and `D-002`'s pre-committed arithmetic); the trim-or-raise
  question was the operator's.
- **Resolved (2026-08-21, `005`):** operator ruled trim at the milestone
  close, deferring the compaction to a model that did not write the
  work.
- **Executed (2026-08-21, Milestone 1 close):** the compaction ran on a
  model that did not write the work and took `CLAUDE.md` 389 → 381. The
  numbers stand unchanged and **the gap does not close**: 381 is 9 under
  the hard cap and 16 over the ~365 handover figure. The pass stopped
  there deliberately rather than compress normative rule text — `D-002`'s
  own history records trimming rule bodies as this project's documented
  failure mode, reversed by a fidelity review. So `006` begins with less
  room than the handover figure intends, and the trim-or-raise choice
  returns to the operator at `006`'s close with the same two remedies.

Detail in git history.

### D-025 — `.claude/spec-work/` is stripped from the published history

- **Date:** 2026-08-21
- **Step:** `005`
- **Decision:** Remove `.claude/spec-work/` (31 files: specification-phase
  working notes, cold-read reviews, the external review packet, handoff
  material) from the working tree's index, gitignore the path, and
  rewrite it out of the published history entirely — a normal deletion
  would leave every already-published object exactly where it was, which
  is not what the transparency ruling asked for. Nothing in the
  implementation depends on it being present: rule 1 forbids reading it,
  and its one sanctioned use (tooling templates) expired at `004`. The
  directory stays untouched on the operator's own disk. `git
  filter-branch` does the rewrite (deprecated but shipped with git 2.53;
  fetching the replacement would cross rule 9's boundary for a one-time
  act).
- **Approved by:** operator, 2026-08-21.
- **Executed (2026-08-21):** the operator ran the rewrite and both
  force-pushes; no session performed them, the guard having denied even
  the attempt to measure the tooling, working as `001` intended. Four
  commits carried the paths and none does now, across every branch and
  all six step tags, which were rewritten with their annotations intact;
  `refs/backups/bash-guard` shares no ancestry with `main` and was
  correctly skipped. **What this does not do:** the objects were public
  for the repository's whole life, so forks, existing clones and the
  forge's unreachable-object window keep them. Removal going forward,
  not retraction.

Detail in git history.

### D-026 — The house conventions go with it; the behavior corpus stays

- **Date:** 2026-08-21
- **Step:** `005`
- **Decision:** `.claude/refs/infra-conventions/` (another project's
  harness shape, read for shape only) leaves by `D-025`'s same route —
  untracked, gitignored, stripped from history in the same rewrite —
  because publishing another project's harness material in this one's
  install channel is what the transparency ruling removes.
  `behavior-corpus.md` stays tracked and published: it is this project's
  own yardstick, and a reader judging whether frisk decides correctly
  should be able to see what it is measured against. Rule 3's read
  triggers are unchanged; both stay readable on disk.
- **Approved by:** operator, 2026-08-21.

Detail in git history.

### D-027 — The workflow family is schema validation; the actions are pinned by commit

- **Date:** 2026-08-21
- **Step:** `005`
- **Decision:** `.github/workflows/ci.yml`'s check family is
  `check-github-workflows`/`check-dependabot` from `check-jsonschema`,
  pinned by `rev` like every other third-party hook (`actionlint`
  rejected on its Go/Docker build prerequisite, a new system requirement
  `just setup` should not carry); its three `actions/*` uses are pinned
  by commit SHA with the release in a trailing comment, moved to current
  majors, rather than the floating major tags the house conventions
  carried — a floating "pin" is worse than an honest one, since the
  publisher retargets it on every release with no diff in this
  repository. `.github/dependabot.yml` bumps those three SHAs (scoped to
  `github-actions` alone — `requirements.txt` and hook `rev:`s are
  measured versions whose bump belongs to a step, not a bot), because a
  digest nobody bumps ages into an action several releases behind a file
  that still looks deliberate. The `concurrency` block, deleted by review
  as arriving unneeded, was reinstated: Dependabot force-pushes to its
  own branches, making superseded runs a real case.
- **Approved by:** operator, 2026-08-21, for the pinning-and-Dependabot
  pairing and the `concurrency` block; implementer for the rest (within
  latitude: rule 2's check-family/pinning clauses, rule 11's
  boring-tool test).

Detail in git history.

### D-028 — The guard's backup is a branch on the public `origin`, reversing `D-017`

- **Date:** 2026-08-21
- **Step:** — (Milestone 1 close)
- **Context:** `D-017` named a private remote `backup` for
  `refs/backups/bash-guard`, and after four closes no such remote
  existed. Milestone 1's state review raised it as the milestone's one
  unheld obligation: `.claude/hooks/bash_guard.py` is gitignored and
  never tracked by design, so that ref is the guard's **only** copy, in
  one clone, on one machine — and the guard is what gates every Bash
  call in this project. A disk failure would leave
  `guard-record.md`'s restore recipe with nothing to restore from.
- **Decision:** the backup is **`origin`'s `backup/bash-guard` branch**,
  pushed at each step close as
  `git push origin refs/backups/bash-guard:refs/heads/backup/bash-guard`.
  The local ref keeps its name and its place outside `refs/heads/`,
  because both gates and `scripts/test.sh` key on it and `001`'s twelve
  measured states depend on that spelling — so nothing in the harness
  changes, no invariant needs re-measuring, and a clone still receives
  `backup/bash-guard` but never `refs/backups/bash-guard`, leaving CI
  reporting the guard absent by design.
- **What this costs, recorded because it is irreversible.** `origin` is
  public, so the branch publishes the prototype's source permanently and
  — a branch being carried by default clone, and the plugin's install
  channel being `git clone` of this repository — delivers it into every
  future user's checkout. `D-025` established this step that force-push
  removal is removal going forward, not retraction. Rule 1's quarantine
  is unaffected in its other half: the file still never enters a
  session's context, and it is still absent from every working tree.
- **Alternatives considered:** *a separate private repository as remote
  `backup`* — `D-017`'s shape, recommended by the implementer, nothing
  published, no amendment needed anywhere; rejected by the operator.
  *A separate public repository* — off the install channel, so users
  never receive it, still public; not chosen. *Pushing the ref to
  `origin` under `refs/backups/` rather than as a branch* — published
  but not clone-delivered; offered and not taken.
- **Approved by:** operator, 2026-08-21, choosing the branch after the
  publication and clone-delivery consequences were put to them twice.

### D-029 — The interpreter floor stands at 3.9; the 3.6 platforms are documented, not covered

- **Date:** 2026-08-21
- **Step:** `006`
- **Context:** open-fact inventory item 12 (§2.1, §3.1). The floor is a
  safety property, not a convenience one — an engine the shipped
  `python3` cannot parse fails open — and §3.1 ordered its table
  re-verified before the floor was committed. The table cannot be
  measured from this machine, so the operator authorised the
  distribution-data lookups.
- **Decision:** the floor is **3.9**. Verified 2026-08-21 from vendor
  documentation: macOS 26 / Xcode command-line tools 26.x ship 3.9.6;
  RHEL 9 ships 3.9 "for the whole life cycle of RHEL 9"; Amazon Linux
  2023's `/usr/bin/python3` is "always Python 3.9"; Ubuntu 22.04/24.04/
  26.04 ship 3.10/3.12/3.14; Debian 12/13 ship 3.11/3.13; SLES 16 ships
  3.13. §3.1's parenthetical claim — "every current LTS distribution" —
  was false: **SLES 15 SP7 / openSUSE Leap 15 and RHEL 8 ship 3.6** as
  the system `python3`, and RHEL 8 is in maintenance until May 2029. The
  amendment names them as a documented limitation instead: there the
  engine does not parse, the hook fails open, and only the sentinel
  (§7.4) says so.
- **Alternatives considered:** *dropping the floor to 3.6* to cover
  those two — rejected by the operator: §3.1 forbids a dual path, so it
  would cost the engine every 3.7–3.9 feature permanently, for two
  platforms the specification never named and whose vendors ship a
  newer Python beside the system one. *Narrowing the parenthetical to
  the platforms actually verified, with no limitation text* — smallest
  amendment, rejected because a reader cannot tell the claim shrank.
  *Recording the table unmeasured* — §2.1's pre-commitment would then
  have driven the floor down; not needed once the lookups were
  authorised.
- **Approved by:** operator, 2026-08-21, both for the lookups and for
  the floor-plus-limitation shape of the amendment.

### D-030 — Python's check family is ruff and mypy, both pinned to the floor

- **Date:** 2026-08-21
- **Step:** `006`
- **Context:** rule 2 requires a check family to arrive with the first
  artifact of its class, and `006` is where a body of Python arrives.
  The floor (`D-029`) has to be *checked* rather than asserted: this
  workstation has only 3.14, and an engine the operator's shipped
  interpreter cannot parse makes the hook fail open.
- **Decision:** two pinned pre-commit hooks, configured in
  `pyproject.toml` beside the packaging metadata.
  **ruff `v0.16.4`** — `ruff-check` with the house selection
  (`E`, `W`, `F`, `I`, `B`, `UP`, `SIM`), and `ruff-format --check`,
  which asserts the formatting instead of writing it, so the family
  behaves like every other check here rather than like the three fixer
  hooks. `target-version = "py39"`. **mypy, `mirrors-mypy v2.3.1`** —
  `strict`, `python_version = "3.9"`, `pass_filenames: false` with
  `files = ["src", "tests"]`, so a change in one module is judged
  against every caller. Both are static, so the floor is also
  **executed**: `.github/workflows/ci.yml` splits into a single-version
  `check` job and a `test` job whose matrix carries the floor and this
  workstation's version (§11's minimum, extended at `029`), and the
  suite is written to need nothing installed — so no matrix row runs
  `just setup`, and each installs the package the way an adopting
  project's CI would. The suite carries a third, cheap half —
  `ast.parse(..., feature_version=(3, 9))` over every module, which
  makes any interpreter refuse grammar the floor lacks, a `match`
  statement above all. `check-toml` joins from the collection already
  pinned.
- **What is deliberately not covered.** mypy sees `src/` and `tests/`,
  not `scripts/`: the harness scripts are glue with no callers, and
  annotating them would buy a type error nobody could have.
- **Alternatives considered:** *the floor checked statically only*,
  leaving execution to `029`'s release matrix — rejected by the
  operator: between `006` and `029` the floor would be a checkers'
  claim, and the failure it guards against is silent. *Installing a
  floor interpreter on this workstation* — a gated system install, and
  a lasting change to a machine, for what a runner does free.
  *flake8 + black + isort* — three pins and three configurations where
  ruff is one. *No type checker* — it is the only tool that reads
  `python_version` and so the only one that catches a 3.10 standard
  library name on a 3.14 machine.
- **Approved by:** operator, 2026-08-21, for the static-plus-CI-floor
  shape; implementer for the tool choices (within latitude: rule 2's
  check-family clause, a workflow choice the bootstrap left open).

### D-031 — The engine's suite is stdlib `unittest`, run against `src/`

- **Date:** 2026-08-21
- **Step:** `006`
- **Context:** §8.1's gate one needs a suite from this step onward, and
  the same suite is what proves the interpreter floor on a runner where
  nothing is installed.
- **Decision:** `unittest`, discovered from `tests/` by
  `scripts/test.sh` as
  `PYTHONPATH=src python3 -m unittest discover`. No test dependency, no
  installed package, no virtualenv: `PYTHON=python3.9 just test` and
  every row of CI's test matrix are then the same command as the local
  one. `PYTHON`
  defaults to `python3`, and `test.sh` prints which interpreter judged.
- **Alternatives considered:** *pytest* — the ecosystem's default, and
  the better tool for fixtures and parametrisation, which is what the
  engine steps will want; rejected here because it would have to be
  installed on every interpreter the matrix runs, turning a bare runner
  into a pinned-environment build and putting a dependency in front of
  the one suite that must run where nothing is installed. The
  choice is revisited if a later engine step needs what pytest gives —
  `unittest` fixtures and `subTest` cover what this step has.
  *Testing the installed console script instead of `src/`* — it would
  make the suite depend on `just setup` having run, which no row of the
  test matrix does.
- **Approved by:** implementer (within latitude: a workflow choice the
  bootstrap instructions left open; rule 11's smallest-thing test).

### D-032 — Behaviour-bearing steps write their tests first, gated by the operator

- **Date:** 2026-08-21
- **Step:** — (doctrine, adopted before `006`'s close)
- **Context:** the operator asked whether the project should work
  test-first, with the cases committed, reviewed and approved before any
  implementation. `006` is the argument for it: its suite was written
  after the code and encoded the code's behaviour rather than the
  contract — `run()` merged stdout and stderr, so every assertion about
  `explain`'s output passed whichever stream carried it, and the defect
  surfaced only because the operator read a terminal. A case written
  from §9 first would have had to name the channel.
- **Decision:** `CLAUDE.md` rule 2 gains a **test gate**. On steps that
  implement §4 behaviour or ship policy content — `007`–`014`, `017`,
  `023`, `030`–`035`, listed in `PLAN.md`'s reading rules — the cases
  are written, committed and approved before the implementation exists,
  transcribed from `SPECIFICATIONS.md` and
  `.claude/refs/behavior-corpus.md`. The gate hands over a **red** suite
  with `just check` green and the failing output quoted, so an import
  error or a suite that never ran cannot pass for a case, and
  `test-reviewer` judges the cases against spec and corpus rather than
  against code. **Approved cases are frozen**: implementation that shows
  a case wrong brings it back as a change, never a quiet edit — without
  that, tests-first degrades into writing the tests twice. Every other
  step keeps its single gate. `/handover-step` carries the phase and
  `test-reviewer`'s brief carries the changed question.
- **Alternatives considered:** *every step test-gated* — one uniform
  rule, rejected because the cases are ceremony on a packaging step, a
  measurement pass or a README, and a gate that gets rubber-stamped
  teaches the next one to be. *Behaviour steps plus opt-in elsewhere* —
  offered; not taken, since "is this test-gated?" then becomes a
  question at the start of every step instead of a property of the plan.
  *Leaving the workflow alone* — the `006` defect is the evidence
  against it.
- **What it cost.** `CLAUDE.md` was compressed from 380 to 350 lines to
  make room, `D-024`'s handover figure being 15 lines away at the time;
  the rule brought it to 361. Compression, not relocation: no operative
  content left the file, and what went was duplication of the close
  ritual, of `guard-record.md` and of `DECISIONS.md`'s own reasoning.
- **Approved by:** operator, 2026-08-21, choosing the behaviour-bearing
  scope and the trim-before-adding route.

### D-033 — The configuration lives at `.claude/frisk/config.py`

- **Date:** 2026-08-21
- **Step:** `007`
- **Context:** §5.1 requires a dedicated directory inside the project's
  `.claude/`, says its name should carry the plugin's name, and leaves
  the exact name and internal layout to the implementation. Every later
  step presupposes an answer: the manual tests say "write a config by
  hand in a scratch project", `018`'s hook must resolve it, `021`'s
  same-configuration requirement compares two resolutions of it, and
  `024`'s scaffold creates it.
- **Decision:** the directory is `.claude/frisk/`, and the file the
  engine executes is `config.py` in it. Collections adopted with
  `use("name")` are `name.py` beside it, and nothing outside that
  directory is ever executed. The scaffold creates the directory; it
  does not choose where it goes.
- **Alternatives considered:** *`.claude/frisk.py`, a single file* —
  fewer paths, rejected because §5.1 wants one directory the operator
  versions and the plugin promises about, with room for cases and a
  future declarative source. *A configurable location* — a setting to
  point elsewhere; rejected as the thing §9's same-configuration
  requirement exists to prevent: two resolvers that can disagree.
  *`config.py` versus `frisk.py` or `registry.py` inside the
  directory* — `config.py` says what the file is to an operator reading
  a directory listing, and the directory already carries the name.
- **Approved by:** implementer (within latitude: §5.1 delegates the
  name explicitly), put to the operator with the step.

### D-034 — The config-facing API is declarations with one `when=`

- **Date:** 2026-08-21
- **Step:** `007`
- **Context:** the API is the stability boundary of §3.5 and the
  document an operator reviews to know their boundary (§5.3), so its
  shape is a decision rather than a detail. It had to be designed
  against the whole of §5.2 at once — nothing may be precluded by a
  later staging — while staying readable to somebody who does not write
  Python.
- **Decision:** entities are declared by kind (`tool`, `wrapper`,
  `shell`, `interpreter`), each call registering rather than returning
  a value; verdicts are constructors (`deny`, `ask`, `allow`, `silent`,
  `grant`) taking a subcommand path as it is typed, a mandatory
  `reason`, and a single `when=` holding one condition or a sequence of
  them, all of which must hold. Or lives inside the value layer
  (`any_of`, `any_flag`, `at_least_one_operand`), never as a second
  boolean vocabulary over conditions: where a cross-kind or is wanted,
  two rules of the same verdict express it, which §3.2's order-free
  ranking makes equivalent. Flag arities are declared in named buckets
  (`bare`, `takes_value`, `may_take_value`) so a thirty-flag closed
  world reads as three lines; on a gated tool that same declaration
  *is* the accounted set, and `closed_world` says so without a grant —
  three-valued rather than a flag, so that unset reads as "closed
  exactly when grants are declared", an explicit `False` beside a grant
  is refused rather than ignored, and an amendment leaves a world
  someone closed on purpose alone. *Derived* is evaluated on the state
  a declaration leaves behind, so dropping a tool's last grant re-opens
  a world nobody closed explicitly — which is the operator's reading:
  the declared default stays and keeps doing what it says, and the
  amendment means "no shape bypasses the default here" rather than
  "this tool is unguarded". Removing granted behaviour altogether is a
  `tool()` redeclaration, which replaces. The alternative — refusing
  such an amendment until it says what the world becomes — was rejected
  because it cannot be stated as a rule about the resulting state (a
  derived closed world with no grants *is* a rules-only tool), so it
  would be the model's only history-dependent validation, and one that
  loses its meaning when a later layer replaces the declaration
  outright. A tool is named once, and the name says which of §4.2's two
  forms it is the way a shell already does: no separator is a
  basename, a separator is a project-relative path, and a script at the
  project root takes the `./` a shell needs there too. An absolute path
  is refused — the configuration is committed and travels with the
  project, where `/usr/bin/git` is `/opt/homebrew/bin/git` on the next
  machine, and accepting it would register something that reads like a
  gate on git and would not match `git push`.
  Shadowing is `tool()` again to replace and `amend()` to
  update, `amend` dropping by label — declared, or derived as
  `<name>:<verdict>:<subcommand>`, with `grant` in the verdict slot for
  a grant and a numeric suffix where two would collide, and printed by
  `frisk registry`, so what is dropped is what was read. Removals travel inside the list
  they act on, as `drop(…)`, so the list itself says whether a name is
  a flag, a label, an alias, a variable or a handoff position, and
  `tool()` accepting no `Drop` makes "remove from what does not exist
  yet" a type error rather than a runtime one. Secure mode
  and §7.2's failure dial are deliberately absent until the behaviour
  they configure ships; both are additive top-level declarations.
- **Alternatives considered:** *objects the config wires together* —
  `git = tool("git"); git.deny(…)`; rejected because it puts
  composition order in the operator's hands one call at a time where
  §3.4 wants it in one declared order, and because it reads as a
  program rather than a declaration. *A separate `path=` keyword* — the
  first draft, and explicit about which machinery matches; dropped
  because a basename can never contain a separator and a
  project-relative path always does, so the keyword restated what the
  value already said, at the cost of two validation errors nobody
  should have to meet. *A data-literal config (TOML,
  YAML)* — the most legible surface of all, and the one §5.1 rules out:
  the configuration is trusted *code* the hook executes, and predicates
  and matcher composition have no literal form. *Separate `rules=` and
  `conditions=` spellings per condition kind* — `operands=every(…)`
  beside `when=flag(…)`; rejected as two ways to say one thing.
- **Approved by:** operator, at the test gate of `007` (`D-032`): the
  cases are the API's first draft, so approving them approves this. The
  secure-mode deferral was put to them separately and explicitly, with
  §3.2's "could not be retrofitted" sentence beside it — the
  non-retrofittable half is the engine's decision model, which
  `008`–`010` carry; the keyword is additive. They confirmed the
  deferral.

### D-035 — Three matcher rulings the specification leaves open

- **Superseded in part by `D-037`:** ruling (4)'s consequence — that a
  mixed-form boundary set can never answer unsatisfied — no longer
  holds. The combination rule itself stands.
- **Date:** 2026-08-21
- **Step:** `007`
- **Context:** §3.2 fixes the hard parts of matching — resolution before
  comparison, cross-form unproven, lexical `cd` poisoning — and leaves
  three questions to the implementation that the corpus's rulings
  answer or constrain.
- **Decision:** (1) **`path_under` is a boundary and `path_matching` is
  not.** A path under a matched boundary is matched (glob boundaries
  included: `/home/*/scratch` accepts `/home/me/scratch/build`), while a
  regex constrains the resolved path itself (`^/mnt/\w+/build$` rejects
  `/mnt/data/build/sub`). Both readings are forced by context B's
  rulings, which is why the two forms are separate constructors rather
  than one with a flag. (2) **An empty operand list is unsatisfied, not
  unproven.** §3.2 requires "every operand" to need at least one, and
  on a grant either reading refuses; on a deny rule they differ, and
  nothing is uncertain about a list known to be empty — §3.3's stricter
  direction is for what cannot be decided. (3) **`~` is expanded from
  the environment's `HOME`, and `~other` is unproven.** Resolving
  another user's home means reading the password database, which §4.5
  forbids; an absent `HOME` is unproven for the same reason.
  (4) **Matchers combine by Kleene's rule, and a boundary set is an
  `any_of`.** `any_of` answers satisfied if any does, else unproven if
  any is unproven, else unsatisfied; `all_of` answers unsatisfied if any
  does, else unproven if any is unproven, else satisfied — a decision
  outranks an unknown, and an unknown outranks nothing. A `path_under`
  with several boundaries is that same `any_of` over its boundaries.
  The consequence is worth stating because it looks like a defect and
  is not: a boundary set mixing absolute and relative forms —
  `path_under("/tmp", ".scratch")` — can answer satisfied or unproven
  and **never** unsatisfied, since an absolute value is cross-form to
  the relative boundary and a relative one to the absolute boundary. On
  a grant that is invisible (neither releases); on a deny rule it costs
  a prompt for everything outside the set. The suite pins the property
  deliberately rather than leaving it to be rediscovered.
- **Alternatives considered:** for (1), *one `path` constructor with a
  `boundary=` switch* — one name, rejected because the two behaviours
  differ in what they accept, not in a setting, and a switch is where
  that difference would be misread. For (2), *unproven* — the safer
  reflex, rejected because it buys a prompt with a fiction. For (3),
  *leaving `~` literal* — rejected: §3.2 names it among what must be
  resolved before comparing. For (4), *treating a cross-form boundary
  as "not applicable" rather than unproven*, so a boundary set answers
  from the boundaries sharing the value's form alone — it would let a
  mixed set say a clean no, and it has a hole: `tmp/x` against
  `("/tmp", ".scratch")` would be a clean miss on `.scratch` and
  therefore unsatisfied, while the value may genuinely sit inside
  `/tmp` when the working directory is `/`. A deny rule going quiet on
  a value that may be in the gated location is the hole three-valued
  matching exists to close. A third reading — proving an absolute value
  outside a relative boundary by the absence of the boundary's
  component — is sound and is subtle machinery on the permission path
  for a case the corpus never exercises (rule 11).
- **Approved by:** operator, 2026-08-21, for (4) — the ruling was put
  to them at the test gate after the review found two cases
  contradicting each other. (1) to (3) are implementer, within latitude
  (§3.2 leaves them to the implementation; the corpus constrains two).

### D-036 — `frisk registry` ships text only; §9's JSON waits for a consumer

- **Date:** 2026-08-21
- **Step:** `007`
- **Context:** §9 says output is for humans first and that a
  machine-readable option (JSON) is *the recommended way* to make
  "stable enough to script against" cheap to keep. `registry` is the
  first command with structure worth serializing, so the deviation has
  to be a decision rather than an omission.
- **Decision:** `registry` prints text only, in the layout
  `Registry.describe` fixes and the suite pins. JSON is added at the
  step that gains a consumer for it — §9 names two, the status-line
  sample and whatever the maintenance skill needs programmatically, and
  neither exists yet. The pinned text layout is what keeps the promise
  in the meantime: it is stable by test, not by convention — and
  `--no-wrap` is the operator's addition for the interim, since the one
  thing a tool reading plain text cannot cope with is a record split
  across lines, while a reader wants exactly that for a long reason.
- **Alternatives considered:** *ship `--json` now* — cheap in isolation,
  rejected under rule 11: a second output format with no reader is a
  second thing every later step's changes have to keep true, and its
  shape would be guessed rather than fitted to a consumer. *Ship JSON
  instead of text* — rejected outright: §9 says humans first, and the
  registry is what the operator reads to know their boundary.
- **Approved by:** implementer (within latitude: §9's JSON is a
  *should*, and rule 4 asks that a within-latitude deviation be logged),
  reported with the step.

### D-037 — Cross-form path matching asks what the working directory could make true, superseding `D-035`'s fourth ruling

- **Date:** 2026-08-21
- **Step:** `007`
- **Context:** §3.2 fixed cross-form path semantics on **form**: one side
  absolute, one relative, therefore unproven. Reviewing the cases at
  the test gate, the operator observed that the rule is coarser than
  its own reasoning. `tmp/x` against `/tmp` is genuinely undecidable —
  a working directory of `/` puts it inside. `/etc/passwd` against
  `.scratch` is not: for the value to sit inside `<cwd>/.scratch` it
  would have to contain a `.scratch` component, and it contains none,
  so the answer is no for every working directory that exists.
  Reporting "cannot decide" there says something false about the world,
  and §3.2's own vocabulary has a word for what it is instead.
- **Decision:** the cross-form rule is keyed on decidability rather
  than on form, and §3.2 is amended to say so. Relative against
  relative and absolute against absolute compare textually, as before —
  the first because both hang off the *same* unknown base. A relative
  value against an absolute boundary is always unproven. An absolute
  value against a relative boundary is never satisfied — the working
  directory can never be proven right — and splits: **unsatisfied**
  where the boundary's components appear nowhere in the value,
  unproven where they do (`./etc` against `/etc/passwd`, true when the
  working directory is `/`). This supersedes `D-035`'s fourth ruling in
  one respect: a mixed-form boundary set *can* now answer no, so the
  property that entry recorded — and the case pinning it — go away. The
  combination rule itself (`any_of` over boundaries, unknowns winning)
  stands unchanged.
- **Alternatives considered:** *keeping the form rule* — what the
  specification said, and what I recommended: the cost today is zero,
  since the corpus's only mixed-form boundary set is a grant where
  unproven and unsatisfied both fail to release, and the change is a
  *relaxation* on the permission path (unproven fires a deny rule at
  ask strength; unsatisfied fires nothing), which is the direction
  deserving the most suspicion. The operator overruled it on the
  ground that matters more: this is engine semantics, and moving it
  after adoption changes verdicts in projects that already trust them,
  so the comfortable reading is the one to take while nothing depends
  on it. *Component-aware reasoning as an implementation refinement* —
  rejected by rule 1: it changes observable verdicts, so it is an
  amendment or it is nothing. *Deferring to §10's surprise loop* —
  rejected with the same argument: the loop is for policy that turned
  out wrong in use, not for semantics known to be wrong now.
- **What it buys beyond the case that prompted it.** The rule explains
  the `cd` poisoning instead of sitting beside it: relative against
  relative is decidable *because both share one unknown base*, and an
  in-line `cd` is exactly what stops them sharing it. One principle,
  one less special case. No corpus ruling moves — the four that touch
  these boundaries are grant conditions and keep their adjudicated
  verdicts. Soundness is textual, consistent with §4.4's standing
  symlink blind spot.
- **Approved by:** operator, 2026-08-21, wording included.

### D-038 — The walked shells and interpreters: the corpus is the floor, not the ceiling

- **Date:** 2026-08-22
- **Step:** `007`
- **Context:** §4.3 requires shells whose `-c` payload is re-analyzed
  and §4.2 requires interpreters walked to the file they run, and both
  say only that the set is "an engine default layer like the wrappers".
  The corpus adjudicates four programs — `sh`, `bash`, `eval`,
  `python3` — and nothing about the rest. The wrapper layer needed no
  decision because the corpus states it as an exact table; this layer
  is the implementation's to choose, so the choice belongs in the log
  rather than only in the cases that pin it.
- **Decision:** ship `sh`, `bash` and `eval` as shells, and `python3`,
  `node`, `ruby` and `perl` as interpreters. Each declares **the
  value-taking options that would shift the walk** and nothing else:
  `-c` and `-o` for the shells; `-c -m -W -X --check-hash-based-pycs`
  for python3; `-e --eval -p --print -r --require` for node; `-e -r -I
  -C -E -F` for ruby; `-e -E -I` for perl. Options whose argument is
  attached (`perl -Mstrict`) or optional (`ruby -i`) are deliberately
  absent: declaring them value-taking would swallow the token after
  them, and this layer declares only value-taking options because §4.3
  presumes an undeclared one bare. The corpus is the floor: an engine
  that walked only the four programs it adjudicates would leave `node
  tools/deploy.js` unwalked, and the ruling that a registered tool run
  through an interpreter is still that tool would hold for one language.
- **Alternatives considered:** *narrow the layer to the four the corpus
  names* — rule 11's build-at-the-moment-of-need, and the need is
  visible now rather than anticipated: a JavaScript or Ruby project
  registering a script by path gets nothing from a layer that walks
  only Python. *Declare each program's full option set* — rejected in
  the other direction: over-declaring swallows an operand, while
  under-declaring loses the walk and a lost walk asks (§4.3), so the
  conservative set errs toward the prompt and the surprise loop grows
  it.
- **Approved by:** operator, 2026-08-22 — "corpus is an example, and a
  floor, not a ceiling".

### D-039 — A value-optional flag declares what a bare use means

- **Date:** 2026-08-22
- **Step:** `007`
- **Context:** §4.2 requires the value-optional arity because reading
  such a flag as value-required "can swallow the very token that
  decides the verdict". It follows that the bare and valued spellings
  are not interchangeable — and the operator asked the question that
  exposes what was missing: how do you write a rule about a flag that
  may be used bare, used with the tool's default value, or used with
  one of a few others, when the first two mean the same thing?
- **Decision:** `may_take_value(*names, default=None)`. The default is
  what the *tool* does with a bare flag, declared once beside the
  arity, and the engine substitutes it when the flag is bare. With
  `may_take_value("--argument", default="check")`, the condition
  `flag("--argument", one_of("check"))` matches `--argument` and
  `--argument check` alike, and `one_of("full", "deep")` picks out the
  others. Undeclared, a bare use has no value to test, so a value
  condition on it is **unprovable** rather than false — §3.3's stricter
  side, and the same treatment a `$VAR` value gets, for the same
  reason: the value exists and the line does not show it.
- **Alternatives considered:** *unprovable always, with no way to
  declare a default* — the first ruling, and wrong: it makes the
  operator's case unwritable, since no condition could ever match the
  bare form. *A `no_value()` matcher*, so a rule says
  `any_of(no_value(), one_of("check"))` — expressible, but it restates
  the tool's default at every rule that touches the flag, and gets it
  wrong once. *Putting the default on the condition* — same objection,
  repeated per rule rather than per tool. The fact belongs to the tool,
  so it is declared with the tool.
- **Approved by:** operator, 2026-08-22, whose question defined the
  requirement.

### D-040 — The test tree is rooted at the repository, and `tests` is a package

- **Date:** 2026-08-22
- **Step:** `007`
- **Context:** `D-031` chose `unittest discover --start-directory tests
  --top-level-directory tests`, which makes each module a top-level one
  and needs no `__init__.py`. An editor's test explorer cannot run
  that: the Python extension sets `PROJECT_ROOT_PATH` from the project
  and then overrides `top_level_dir` with it unconditionally, so it
  always asks `unittest` to root the tree at the repository — and
  `unittest` refuses unless the start directory is importable. There is
  no setting for it; the code path was read to be sure.
- **Decision:** `tests/__init__.py` exists and the runner passes
  `--top-level-directory .`, so the tree is rooted at the repository in
  every context. Modules import each other by full path
  (`from tests.corpus import context_b`). `D-031`'s decision is
  untouched — stdlib `unittest`, no test dependency, nothing installed,
  `PYTHONPATH=src` — only where discovery starts counting.
- **Alternatives considered:** *leave it and use `just test`* — no repo
  change at all, and the honest fallback if this ever costs something;
  rejected because a suite the operator cannot run from their editor is
  a suite they run less often. *Relative imports inside the package* —
  equivalent, and it breaks the moment someone runs a module directly.
  *Making the extension behave* — there is no setting, and pinning an
  editor's version is not a thing this repository should do.
- **What it costs.** The repository root joins `sys.path` during a test
  run, where before only `tests/` and `src/` were on it. Nothing at the
  root shadows a standard-library or engine module today, and a name
  that did would be a name worth renaming anyway.
- **Approved by:** implementer (within latitude: a workflow choice, and
  `D-031`'s own note that the runner is revisited when a real need
  appears), reported with the step.

### D-041 — A relative boundary that climbs is unproven against an absolute value, not unsatisfied

- **Date:** 2026-08-23
- **Step:** `007`
- **Refines `D-037`,** whose principle it applies rather than changes.
- **Context:** `D-037` keyed cross-form path matching on decidability:
  an absolute value is unsatisfied against a relative boundary only
  where *no* working directory could place it inside. §3.2 glossed that
  test as "the boundary's components appearing nowhere in the value",
  and the implementation searched for the boundary's resolved
  components as a run. A boundary that climbs — `../shared` — resolves
  to `("..", "shared")`, and `..` appears in no resolved absolute path,
  so `/repo/shared/x` came back **unsatisfied** while a working
  directory anywhere in `/repo` makes it true. The review found it; the
  gloss and the principle disagreed.
- **Decision:** a leading `..` is not a component to look for. It is the
  boundary re-basing itself onto a directory the line does not name, so
  it is dropped before the search, and what remains decides:
  `../shared` against `/repo/shared/x` is **unproven**, `.scratch`
  against `/etc/passwd` stays **unsatisfied**. §3.2's gloss is amended
  to say so. Resolution already collects `..` at the front of a
  relative path, so there is no other position to handle.
- **Alternatives considered:** *leave it* — rejected by the operator:
  the answer is false about the world, and false in the releasing
  direction (unsatisfied fires nothing where unproven fires a deny rule
  at ask strength). *Read the gloss as normative and amend the
  principle instead* — rejected: the principle is the rule `D-037` was
  argued and approved on, and the gloss was written to illustrate it.
- **Approved by:** operator, 2026-08-23, who gave the reasoning: the
  working directory is the unknown, so `../shared` is satisfied when it
  is `/repo/shared` and unsatisfied otherwise — which is the definition
  of unproven.

### D-042 — §5.3's mandatory reason is §3.2's: every *non-silent* verdict

- **Date:** 2026-08-23
- **Step:** `007`
- **Context:** §5.3 said "every rule, grant and default verdict carries
  a human-readable reason"; §3.2 says "every **non-silent** verdict must
  carry a reason and a citation". A `silent()` rule is a rule, so the
  two clauses contradicted each other for exactly one construct. The
  test gate had already settled it in §3.2's favour — the approved case
  `test_silence_needs_none` requires `silent("status")` to construct
  without one — but nothing recorded the reconciliation, and `019`'s
  liveness pass would have met the same question.
- **Decision:** §5.3 is amended to "every non-silent rule, grant and
  default verdict", with the reason stated: a declared silence refuses
  nothing and so has nothing to explain. `silent()` is the one verdict
  constructor that takes no `reason`, and the liveness rule "reasons are
  non-empty" reads over the non-silent ones.
- **Alternatives considered:** *require a reason on `silent()` too* —
  §5.3's literal reading, and rejected because the reason exists to be
  shown to whoever meets a refusal, and nobody meets a silence; it would
  be ceremony collected for no reader. *Leave both sentences standing* —
  rejected under rule 1: a specification that says two things is one a
  later session resolves differently.
- **Approved by:** operator, 2026-08-23.

### D-043 — A name and an alias are one claim, decided by layer order

- **Date:** 2026-08-23
- **Step:** `007`
- **Context:** the cold review found that a cross-layer alias collision
  was decided by which map `lookup` consulted first: registered names
  before aliases, whatever layer each came from. A project declaring
  `tool("gamma", aliases=["sudo"])` over the engine's `wrapper("sudo")`
  got an alias that resolved nowhere, printed in `frisk registry` as
  though it worked. §3.4 makes the operator's layer the one that always
  wins and forbids a composition that hides what it decided; this did
  both wrongly.
- **Decision:** one resolution map, filled as each declaration is
  applied and therefore in layer order, with a name and an alias as the
  same kind of claim on the same word: the later layer wins, whichever
  form each side used. A full declaration releases what the name it
  replaces was reaching before claiming afresh, so a replacement cannot
  leave a stale alias behind; an amendment applies only its delta, so
  amending an entry for an unrelated reason cannot take back a word a
  later layer has since claimed. Within one source the collision stays
  refused — that is `_no_repeats`, and a source has no order to decide
  it with. **The entry that loses a word simply stops listing it**:
  `describe` prints an entry's *reaching* aliases, not its declared
  ones. Not printed is not deleted — the alias stays on the entry, or
  an operator trimming an adopted collection would be told docker has
  no alias to drop while their own file plainly declares one.
- **Alternatives considered:** *refuse the collision across layers* —
  my recommendation, and rejected by the operator: every other
  cross-layer conflict is settled by order, and a name is not special
  enough to be the exception. *Mark the loser `podman (shadowed)`* —
  also mine, on the ground that the loss was one nobody asked for;
  rejected by the operator, whose counter settles it: somebody did ask,
  by writing the declaration that claims the word, and the same
  reasoning would owe a shadow note to every `tool("sudo")` that
  replaces the engine's wrapper. The registry prints the effective
  state, and an overridden declaration is not part of it.
- **Deferred, and worth having.** Everything shadowed or dropped —
  aliases, replaced entries, rules an amendment removed — is invisible
  by design in a registry that prints what is effective. A `--shadowed`
  debug mode showing all of it with the source that lost it would
  answer "where did my `--force` rule go?" in one command. It is an
  enhancement, not a gap: `PLAN.md` `037` carries it.
- **Approved by:** operator, 2026-08-23 — "layer order decide, like any
  other override case", and, on the printing, "I rule on not print the
  shadowed aliases (but they are not deleted)".

### D-044 — A declared path may leave the project

- **Date:** 2026-08-23
- **Step:** `007`
- **Context:** `D-034` refuses an absolute path in a tool name because
  the configuration is committed and travels with the project, where
  `/usr/bin/git` is a different machine's file. The cold review asked
  whether `../shared/deploy.py` should be refused on the same argument:
  it names a file outside the project, what it points at depends on
  where the checkout sits, and it matches only a command line spelled
  with that same prefix.
- **Decision:** accepted, not refused. Two repositories checked out
  side by side is an ordinary layout and running the neighbour's tool
  is an ordinary thing to do. The form is narrow — it holds only while
  the two keep their relative positions, and a command line reaching
  the same file by another spelling is not matched — and that is the
  operator's trade to make. `declare.tool`'s docstring says both halves,
  and a case pins the acceptance so a later session does not tidy it
  into a refusal.
- **Alternatives considered:** *refuse it like an absolute path* — my
  recommendation, and rejected: the two are not alike. An absolute path
  is wrong on every machine but the author's, while a relative one is
  right on every checkout that keeps the layout, which is the whole
  team's. Refusing would remove a use that works for the sake of ones
  that were never promised. *Point the operator at the basename form
  instead* — not a substitute: `deploy.py` gates every file of that
  name anywhere, which is broader than what was asked for.
- **Approved by:** operator, 2026-08-23 — "developers often have 2
  projects with 2 different repos living beside, and using a tool in
  the other is ok… it's an edge case, but it's okay".

### D-045 — Every rule and grant prints where it was written

- **Date:** 2026-08-23
- **Step:** `007`
- **Context:** `Registry.describe`'s docstring is the layout contract
  (`D-036`), and one sentence in it made the rule-level `source:` line
  conditional: on the entry, "and again on any rule that came from
  elsewhere". The implementation prints it on every rule and grant,
  because an approved case requires a source line on a rule whose entry
  came from the same layer. The docstring was reworded to match what
  the cases pin; the ruling behind it was recorded only in a commit
  message, which is not one of the memory files.
- **Decision:** every rule and grant carries its own `source:` line,
  unconditionally. Three reasons. A rule **outlives the entry it was
  declared on** — an amendment is precisely what puts one layer's rule
  on another layer's entry, so "same layer as its entry" is not a
  property a reader may assume. A conditional column makes the reader
  interpret an *absence*: does no source mean "the entry's" or "not
  recorded"? And the line is what an operator opens to change the rule,
  which is what §3.4's inspection requirement is for.
- **Alternatives considered:** *print it only where the rule's layer
  differs from its entry's* — the docstring's original rule, and what
  it would save is three lines per rule in a large registry, paid for
  by making the reader compute the common case; it also contradicted an
  approved case. *Print no source on rules at all, entry-level only* —
  smaller still, and it loses exactly the case that matters: an
  amendment putting a project rule on a collection's entry, where
  nothing would then say where the rule came from.
- **Approved by:** operator, 2026-08-23. Filed as its own entry rather
  than a clause in `D-036`, whose kernel is the text-only output and
  the deferred JSON; if the operator meant that clause instead, this
  entry folds into it.

### D-046 — `registry --value` narrows to what can answer, and retires at `009`

- **Date:** 2026-08-23
- **Step:** `007`
- **Context:** the operator ran `frisk registry --value /tmp/build` on a
  small real project and read the top of the output, which is the
  engine's `bash` wrapper. The annotation was there — four of them, in
  142 lines across 26 entries, 23 of which were engine wrappers, shells
  and interpreters that carry no rules, no grants and no value
  matchers, and so can never be annotated at all. Answering "what does
  this value satisfy?" with 142 lines and a suggestion to `grep` is a
  tool that stopped one step short.
- **Decision:** two rulings. **A value narrows the output** to the
  declarations that could answer it — an entry with no matcher
  anywhere on it is skipped, and the benign layer prints only the
  assignments constrained by value. On the project above that is 39
  lines instead of 142, with the same four answers. Plain
  `frisk registry` remains the whole boundary; `--value` is the other
  question asked of the same registry. Where *nothing* answers, the
  output is empty and the CLI says so on stderr, because an empty page
  reads as a failure and this is a real answer.
  **And the flag retires at `009`,** where `explain` first returns a
  verdict with its reason and citation. `--value` exists because `007`
  has nothing that judges a command line, so the three-valued model
  would otherwise be invisible from outside until then — `PLAN.md`
  `007` names it as the step's own test instrument in those words. Its
  limits are what make it temporary: it feeds one string to *every*
  matcher regardless of what that matcher constrains, and evaluates
  with no line around it, so it can never show the `cd` poisoning. It
  answers "what would this matcher say about this string", never "what
  happens if I run this", and `explain` answers the second.
- **Alternatives considered:** *leave it and pipe through `grep`* — the
  smallest change, and rejected: four useful lines in 142 is not an
  output an operator reads, and "pipe it" is what a tool says when it
  has not finished. *Delete it now* — legitimate under rule 11, and
  rejected because it is this step's stated test instrument: without
  it the operator takes three-valued matching on the suite's word until
  `009`. *Keep it past `009` as a matcher-debugging tool* — its honest
  residual use, and rejected as the weaker version of a command that
  will answer the same question with the context it lacks.
- **Approved by:** operator, 2026-08-23 — narrow it now, "and we will
  delete it later when explain works".

### D-047 — `speaking` names what §4.1's raw scan looks for

- **Date:** 2026-08-24
- **Step:** `008`
- **Context:** §3.2 fixes three terms and says they are used with those
  meanings throughout: *registered* (known to the engine at all),
  *gated* (declares grants and/or closed worlds) and *rule-bearing*
  (carrying any rule). §4.1's unparseable-line fallback then borrows
  the third for a strictly larger set — "a *rule-bearing* tool's name
  — one with rules, grants or a non-silent default verdict". The two
  readings disagree exactly where it matters: a grants-only gated tool
  (`ansible-playbook`, `stubcli`) carries no rules, so under §3.2's
  definition `ansible-playbook 'unbalanced` would scan clean and come
  back silent — an unparseable line naming a deny-by-default tool,
  answered with silence. §4.3's two discriminators (the lost walk, the
  flag-shaped handoff command position) use the same word, so a reader
  could not tell which set was meant there either. `Entry.rule_bearing`
  in the engine implements §3.2's narrow reading and cites §4.3 for it.
- **Decision:** the word stays narrow and the fourth term is named. §3.2
  gains **speaking** — able to produce a non-silent verdict on its own:
  carrying rules, grants, or a non-silent default verdict — and §4.1's
  scan refers to it instead of glossing `rule-bearing` differently.
  Nothing about what the engine does changes: §4.1 scans the larger set
  it already described, §4.3's discriminators keep the narrow one, and
  `Entry.rule_bearing` keeps its meaning. Only the word §4.1 borrowed
  moves. The engine gains a second predicate beside `rule_bearing`, each
  with one meaning, so the code cannot inherit the ambiguity.
- **Alternatives considered:** *widen `rule-bearing` everywhere to
  rules-or-grants-or-non-silent-default* — one term with one meaning,
  and rejected because it silently changes §4.3: a grants-only tool
  named among the remaining tokens of a lost walk would begin to ask
  where it does not today, which is a behaviour change smuggled in as a
  vocabulary fix, and one the corpus does not adjudicate. *Leave both
  sentences standing and record the local reading in this log only* —
  cheapest, and rejected because the ambiguity survives in the document
  every future session reads as authoritative, and §4.3 is precisely
  where it would bite next (steps `010` and `012`).
- **Approved by:** operator, 2026-08-24 — rename §4.1's predicate,
  no behaviour change.

### D-048 — A newline is `\r\n`, `\n` or a lone `\r`

- **Date:** 2026-08-25
- **Step:** `008`
- **Context:** §4.1 lists the separators a compound command is split at
  and names "newlines" without saying which characters. The cases for
  the step exercised `\n` alone, which left two shapes unread. A `\r\n`
  split only at the `\n` leaves the carriage return on the last token of
  the preceding line, so `git push --force\r\ngit status` carries the
  flag `--force\r` — matching no declaration, firing no rule, and
  answering silence about a line that reads as a forced push. A lone
  `\r`, which bash treats as an ordinary character, hides a whole
  invocation: `git status\rgit push --force` is one `git status`.
  Neither is exotic — a command string is not always authored on the
  platform that runs it, and CRLF in a multiline string is a transport
  artifact far more often than an operand.
- **Decision:** all three spellings are line endings, and the engine's
  separator set is named (`reading.SEPARATORS`) so the suite can iterate
  what the engine actually uses rather than a copy of it. The lone `\r`
  is a deliberate over-read of the shell, and it is the only one:
  where bash would have treated the character as data, frisk splits and
  may produce an invocation bash would not run. That direction is
  §3.3's — the cost is a prompt on the rare line that meant the
  character, against a rule that would otherwise not fire.
- **Alternatives considered:** *`\r\n` and `\n` only, leaving a lone
  `\r` as data* — closer to the shell, and it fixes the common case;
  rejected because the lone-`\r` residue is the worse of the two (a
  hidden invocation, not a mangled flag) and because the resulting rule
  — "a carriage return is a line ending here and data there" — is one
  nobody could predict from the outside. *`\n` only, faithful to bash,
  with the gap named in §4.4's declared blind spots* — defensible, since
  bash and git would both error on `--force\r` rather than force-push,
  so nothing bad happens in the world; rejected because frisk's answer
  would be silence about a line that spells a forced push, and §4.4 is
  for gaps that cannot be closed cheaply, not for ones that cost a
  tuple entry.
- **Approved by:** operator, 2026-08-25 — all three spellings.

### D-049 — `speaking` is its enumeration, not a principle

- **Date:** 2026-08-26
- **Step:** `008`
- **Context:** `D-047` added §3.2's fourth term as "*speaking* (able to
  produce a non-silent verdict on its own: carrying rules, grants, or a
  non-silent default verdict)". The half before the colon does not
  describe the half after it, in both directions. **Too wide:** §3.2
  makes environment assignments closed-world for *every registered
  tool*, so any registered name can produce a non-silent verdict —
  wrappers included, which §4.1's scan excludes outright because
  scanning for them "would make the fallback fire constantly". **Too
  narrow:** a tool declaring only a closed world — no rules, no grants,
  silent default — asks on an unaccounted flag and is not speaking.
  The engine's own `Entry.speaking` docstring says the gloss is "both
  wrong and useless here"; the specification kept it, of a term the
  same sentence binds "throughout".
- **Decision:** the gloss is deleted. §3.2 defines *speaking* as the
  enumeration alone — rules, grants, or a non-silent default verdict —
  and says explicitly that it is not the wider property, naming the
  assignment world as the reason. No behaviour changes: the enumeration
  is what `D-047` decided and what the engine has always implemented.
- **Alternatives considered:** *keep the gloss and bend the docstrings
  to match* — rejected: §3.2 binds these terms throughout, so a gloss
  there is not informal, and it would leave the specification and the
  engine disagreeing about a word both use. *Widen the enumeration to
  match the gloss* — that is `D-047`'s rejected alternative arriving by
  the back door, and it changes §4.1's scan into one that fires on
  every registered name.
- **Approved by:** operator, 2026-08-26 — delete the gloss.

### D-050 — Short-flag bundling, declared per tool and on by default

- **Date:** 2026-08-26
- **Step:** `008`
- **Context:** §4.2 said nothing about a run of short flags behind one
  dash, and the engine read `-fu` as a single unknown flag. On a
  rules-only tool that is a **missed deny**, not a missed prompt:
  `git push -fu origin main` matches no rule naming `-f`, so a forced
  push answers silence. A first fix split any run whose letters were
  all declared, and two problems surfaced. It never asked whether the
  *token itself* was declared, so the corpus's own
  `ansible-playbook -vvv` split into `-v -v -v` and `java -cp lib.jar`
  lost its value — a straight bug. And a whole class of tools does not
  bundle at all: those whose long options carry one dash (`find -name`,
  `go -run`, `java -cp`), where splitting is simply wrong.
- **Decision:** three parts. A token that is itself a declared flag is
  never split. A run splits only where every letter is a declared flag,
  so no flag the operator never wrote is manufactured — a rule firing
  on an invented flag would be the wrong deny §4.3 forbids. And
  `tool(..., bundled=False)` turns it off for a tool that does not
  follow the convention. **The default is on**, because getopt bundling
  is the dominant convention and because the two failures differ in
  visibility: an over-split is a refusal the operator sees and corrects
  by declaring the flag, while an unsplit `-fu` is a rule that never
  fires and says nothing. The loosening on gated tools — split letters
  are accounted where the run was not, so a grant can hold — is
  accepted in the amendment's own words rather than left to be found.
- **Alternatives considered:** *default off, opt in* — over-splitting
  becomes impossible, and rejected because it leaves the missed deny in
  every configuration whose author never thought about bundling, which
  is most of them; a safe default that is only safe when someone
  remembers it is not one. *Infer it from the declaration* — a tool
  declaring any single-dash multi-character flag is not a getopt tool,
  which needs no API at all and uses a signal the operator already
  gives; rejected as action at a distance, since adding `-name` would
  silently change how every other flag on that tool is read. *Defer to
  `010`*, where `PLAN.md` already promises combined-flag spellings for
  a shell's `-c`; rejected because it leaves the hole open across
  `009`, the step where verdicts start being produced.
- **Approved by:** operator, 2026-08-26 — "`bundled=` on tool(),
  default True", after the single-dash long-flag class was raised by
  the operator and the `-vvv` bug demonstrated.

### D-051 — `allow` is earned per invocation and withheld at the line

- **Date:** 2026-08-26
- **Step:** `009`
- **Context:** §6.1's combination table has three allow rows and three
  withholding rows, and every one of them turns on conditions this
  build cannot evaluate: `examined` needs the baseline read tools
  (`017`), `placed` needs substitution analysis (`011`), and the
  release itself needs open fact (c) — whether Claude Code still
  prompts on substitutions — which `015` measures and which may retire
  the verdict altogether. `PLAN.md` `009` therefore names "§6.1's
  combination table (every row except the allow rows)". But `allow()`
  is already in the configuration vocabulary, so a rule can declare one
  today and the engine has to answer for it.
- **Decision:** an invocation earns `allow` exactly as it earns any
  other verdict — the rule fires, the per-invocation verdict is
  `ALLOW`, `frisk explain` shows it — and the **line** answers
  `SILENT`. That is not an interim invention: it is what §6.1's own
  withholding rows say ("the line falls back to genuine silence"), and
  every condition that would release the allow is unmeasured, so every
  row that could apply is a withholding one. Nothing has to be undone
  at `017`; the release is added.
- **Alternatives considered:** *refuse an `allow` declaration until
  `017`* — rejected: the vocabulary is the stability boundary of §3.5,
  and a constructor that raises is a breaking change to add and another
  to remove. *Return the allow at line level and let the hedges arrive
  later* — rejected outright: an allow is assumed to lift the
  working-directory sandbox (§6.3), so shipping the release before the
  hedges is shipping the one verdict whose failure direction is
  unrecoverable.
- **Approved by:** implementer (within latitude: `PLAN.md` `009` stages
  the allow rows at `017`; this entry records how the verdict behaves
  in the meantime).

### D-052 — the default verdict is what no grant released, not what no rule matched

- **Date:** 2026-08-26
- **Step:** `009`
- **Context:** §3.2 says a tool's default verdict is "the defined
  outcome for 'no rule matched, no grant held'". Read literally, a
  fired rule suppresses the default — so a gated tool with a `deny`
  default on which an `ask` rule matched and no grant held would answer
  **ask**, weaker than the same invocation with no rule at all. That
  inverts §3.3: a rule firing is not evidence of safety, and the only
  thing §3.2 gives that releases a gated tool is a grant.
- **Decision:** the invocation's base contribution is computed always:
  **silence where a grant holds, the tool's default verdict
  otherwise**. Rules combine on top of it by rank. The three worked
  corpus rulings agree with both readings, and this one additionally
  cannot answer weaker than the tool's declared posture. It also states
  §3.2's "rules hold even where a grant would otherwise release"
  directly: the grant sets the base to silence, and the rule outranks
  it (`stubtool touch --syntax-check` → ask).
- **Alternatives considered:** *the literal reading — no default where
  a rule fired* — rejected for the inversion above; the wording is
  describing the common case (a rules-only tool), not licensing a
  weaker answer on a gated one. *Make the default a floor only for
  gated tools* — same behaviour with a special case in it, and a
  rules-only tool's default is silence, which floors nothing.
- **Approved by:** implementer (within latitude: §3.3's stated
  principle decides a §3.2 wording ambiguity; no ruling separates the
  two readings).

### D-053 — a malformed invocation costs an ask on every tool

- **Date:** 2026-08-26
- **Step:** `009`
- **Context:** §4.2 states the malformed case flat — "a declared
  value-taking flag with nothing after it makes the invocation
  malformed, which is unproven, not safe" — not scoped to gated tools
  the way the unreadable-token rule beside it is. On a gated tool the
  cost is visible anyway: no grant can hold, so the default applies
  (corpus: `stubtool deploy.yml --limit` → ask). On a rules-only tool
  whose default is silence there is nothing for "unproven, not safe" to
  attach to, and `git -C` would answer silence — the direction §3.3
  forbids. No corpus ruling adjudicates it.
- **Decision:** a malformed invocation contributes an **ask** of its
  own, whatever the tool, and releases no grant. The citation names the
  flag that was left without a value.
- **Alternatives considered:** *scope it to gated tools, like the
  unreadable-token rule* — rejected: §4.2 scopes that rule explicitly
  and this one deliberately not, and the reading layer already records
  the two separately for exactly this reason (`008`). *Leave it silent
  on rules-only tools and document the gap* — a declared blind spot
  (§4.4) is for gaps that cannot be closed cheaply; this one costs a
  contribution.
- **Approved by:** implementer (within latitude: §3.3's principle
  applied where §4.2 states a fact without a cost).

### D-054 — an unproven tool identity caps the invocation at ask

- **Date:** 2026-08-26
- **Step:** `009`
- **Context:** §4.2: "After an in-line `cd`, a relative spelling of a
  path-declared tool is unproven and recognition degrades stricter,
  like any path match." The analogy is the instruction: an unproven
  path match releases no grant and fires a deny or ask rule at **ask**
  strength (§3.2). Applied to identity rather than to a value, that
  means the engine cannot prove this file *is* the declared tool.
- **Decision:** where reading recorded an unresolved path, the
  invocation releases no grant and its verdict is capped at **ask** — a
  deny it would otherwise have earned becomes an ask, and a silence
  stays a silence, since the tool is silent either way. Producing the
  deny would be the wrong deny §4.3 forbids: the command may well be a
  different file entirely.
- **Alternatives considered:** *treat the tool as recognized and let
  its rules fire in full* — rejected: it denies on a file the line does
  not identify. *Treat it as unregistered* — rejected the other way: it
  is the quieter direction, and §4.2 says recognition degrades
  *stricter*, not away.
- **Approved by:** implementer (within latitude: §4.2's own analogy to
  the path matchers of §3.2).

### D-055 — `explain`'s exit statuses, and what an unconfigured project answers

- **Date:** 2026-08-26
- **Step:** `009`
- **Context:** §9 requires an "exit status usable from scripts" and
  leaves the numbers free. `006` reserved 2 for argparse, 4 for "no
  configuration" and 5 for "configuration would not load", and used 3
  as the interim "nothing was judged".
- **Decision:** `0` silent, `1` ask, `2` usage, `3` deny, `4` no
  configuration, `5` configuration error. **Silence is 0** because
  silence is a real answer — frisk has no opinion and the permission
  rules decide (§3.2) — so `frisk explain "$cmd" || refuse` refuses
  exactly where frisk objected or could not answer. `allow` gets no
  status until `017`, since no line returns one (`D-051`). An
  **unconfigured project answers 4 from `explain` too**, not the
  verdict it reached against the engine's default layers: that verdict
  is real but it was reached against no boundary, and §5.4 requires the
  inertness be unmissable rather than inferable. The reading and the
  verdict are still printed; only the status says "no boundary
  answered".
- **Alternatives considered:** *silence non-zero, so any status but a
  hypothetical allow means "do not proceed"* — rejected: it makes every
  ordinary command a failure and the caller has to special-case the
  common answer. *`explain` returning the verdict on an unconfigured
  project* — rejected as above; it is the one case where the status
  would say "no opinion" about a project frisk has not been told
  anything about, which reads as a boundary having answered.
- **Approved by:** implementer (within latitude: §9 leaves the numbers
  to the implementation and requires only that they be usable).

### D-056 — what a closed world does, and what an ungranted tool defaults to

- **Date:** 2026-08-27
- **Step:** `009`
- **Context:** §3.2 enumerates the per-tool defaults as "silent for a
  rules-only tool, ask for a granted tool, or an explicit verdict", and
  says separately that an invocation failing a gated tool's closed
  world "gets the tool's default verdict". Between them sits a shape
  neither sentence names: a tool declaring `closed_world=True` with no
  grants and no default. `D-049` (step `008`) described exactly that
  shape as one that "asks on an unaccounted flag", and `tool()`'s own
  docstring says `closed_world` "closes the tool's flag list without
  granting anything" — both of which promise the flag list changes an
  outcome. Under the two sentences alone it cannot: nothing releases a
  tool with no grants, so every invocation reaches the default and the
  declared list is decorative.
- **Decision:** two parts, and the second is what makes the first
  meaningful. **(a)** The implicit default is §3.2's enumeration
  verbatim: **ask where the tool declares grants, silent otherwise** —
  `bool(entry.grants)`, not `entry.gated`. **(b)** A flag outside a
  gated tool's closed world defeats every grant *and contributes an
  **ask** of its own*, cited by name. The flag list is therefore an
  opt-in list an operator can steer by editing: taking a flag out of it
  makes that flag ask. On every gated tool §3.2 actually describes —
  ask-default (`stubtool --syntax-check deploy.yml --unknown` → ask)
  and deny-default (`osmp subnet set --gateway … default` → deny) —
  this answers exactly what the corpus adjudicates, because the breach
  ask is absorbed by a default at least as strong. It differs only on
  the silent-default shape §3.2 never contemplated, and there it gives
  `D-049`'s sentence.
- **Alternatives considered:** *ask for any gated tool (`entry.gated`),
  the breach reaching only the default* — the implementer's first
  draft, rejected by the operator at the case gate: a closed-world-only
  tool would then ask on **every** invocation, which is what
  `default=ask(...)` already spells, and the flag list would still
  change no verdict. *§3.2 to the letter, no breach contribution* —
  rejected: `closed_world=True` without grants becomes a keyword that
  does nothing, indistinguishable from `closed_world=False`, and
  `D-049`'s sentence would have to be struck as wrong.
- **Approved by:** operator, 2026-08-27 — "the more flexible and
  natural for the user; if the user wants an ask on `--check`, they
  remove it from the flags list (that is an opt-in list)".

### D-057 — secure mode meets the engine's default layers: deferred to `010`

- **Date:** 2026-08-27
- **Step:** `009`
- **Context:** §3.2 says secure mode's global default replaces the
  verdict of "registered tools whose default verdict was left unset",
  and the same paragraph says the engine's default layers "keep their
  declared default verdicts: `cat foo` stays silent". Every entry in
  `defaults.py` — every wrapper, shell and interpreter — is registered
  with **no** declared default, so the two sentences pull opposite ways
  on `sudo ls` in secure mode: the first makes it the global default,
  the second reads as an exemption. `test-reviewer` raised it at the
  case gate, because the cases freeze.
- **Decision:** `009` writes no case either way, and the suite's
  docstring names it as a scope boundary alongside the other four. A
  wrapper's own contribution to a line is designed at `010` ("Registered
  wrappers contributing their own verdict and the walk continuing to
  what they run"), and a case frozen here would pin wrapper behaviour
  against a build that does not walk one. The tool cases of secure mode
  stand as written; only the default-layer entries are unaddressed.
- **Alternatives considered:** *declare `silent()` on every
  default-layer entry now*, making §3.2's sentence true by construction
  — plausible, and still open at `010`, but it commits `007`'s
  deliverable to a claim about wrappers before the step that judges one.
  *Case it as "unset is unset"* — literal, but it makes every
  wrapper-led line carry a deny from the wrapper itself in secure mode,
  including where the wrapped command is registered and silent, and
  that is exactly the trade `010` should make with the walk in front of
  it.
- **Approved by:** operator, 2026-08-27 — defer to `010`.

### D-058 — `/review-step`, the file-by-file review loop

- **Date:** 2026-08-27
- **Step:** `009`
- **Context:** the handover rituals cover the two ends of a step —
  `/handover-step` puts it in front of the operator, `/approve-step`
  closes it — and nothing covered what happens between them when the
  operator wants to read the work themselves rather than only test its
  behaviour. Step `009` is the first where they did: a step with a
  1,000-line case file, six decision entries and a spec-reading
  question inside it is not reviewable in one pass. Improvised, the
  loop lost its own state — which files had been validated — the moment
  the conversation grew.
- **Decision:** a fourth ritual, `.claude/skills/review-step/`. One
  cycle per file the operator picks: they give feedback, we discuss and
  **nothing changes**, they say they are finished, everything agreed is
  implemented **without committing**, they validate, and only then does
  it commit. It holds a ledger of every file the step touched with four
  states, written to the session scratchpad as well as restated in the
  conversation, because a ledger held only in context does not survive
  a compaction and the operator would have to remember what they had
  validated. Validating a file is explicitly **not** approving the
  step: approval stays a separate act at the end of the whole review,
  and `/approve-step` is still what closes.
- **Alternatives considered:** *fold it into `/handover-step`* —
  rejected: that ritual is a sequence run once, this one is a loop run
  as many times as there are files, and the do-nothing-until-told rule
  at its centre contradicts a handover's job of arriving finished.
  *Keep it as prose in `CLAUDE.md`* — rejected under rule 3's budget
  and rule 11: it is a ritual invoked at a trigger, which is what a
  skill is for, and `CLAUDE.md` is at 366 of 390 lines. *Track the
  ledger in `.claude/docs/`* — rejected: it is per-step transient
  state, not a durable lesson a future session needs, and rule 3 keeps
  that directory for the latter.
- **Approved by:** operator, 2026-08-27 — requested during `009`'s case
  review, "to enable this mode easily on any step, that could also be
  for my final review of a non-code step".

### D-059 — the default verdict is a fallback, not a floor (reversing `D-052`)

- **Date:** 2026-08-27
- **Step:** `009`
- **Context:** `D-052` read §3.2's "a defined outcome for *no rule
  matched, no grant held*" as a floor: the base contribution was
  silence where a grant held and the tool's default otherwise, always,
  with rules combining on top. The argument was §3.3 — a fired rule is
  not evidence of safety, so a matching *ask* rule should not let a
  deny-default tool answer weaker than it would with no rule at all.
  The operator rejected it at the case gate: "default is for what is
  not matched by any rules/grants — else it's not a default, it's an
  enforcing minimal rule."
- **Decision:** the default is consulted **only** where no rule matched
  and no grant held. Two arguments carry it beyond the wording. First,
  the floor reading makes a declaration dead: on a tool with
  `default=deny(...)`, no rule weaker than deny could ever change an
  answer, so `ask("get", …)` — an operator's deliberate carve-out —
  would silently do nothing, which is the failure `D-056` rejected for
  `closed_world=True` an hour earlier. Second, **the model already has
  a floor and keeps it separate**: an unconditional `deny(reason=…)`
  rule fires on every invocation, which is exactly "an enforcing
  minimal rule". Reading `default=` as a floor collapses two constructs
  into one and deletes the fallback. §3.3 does not license it either:
  §3.3 is about *uncertainty* moving stricter, and an explicit weaker
  rule the operator wrote is not uncertainty.
  **The refinement that keeps it safe:** "no rule matched" means the
  rule's conditions were **satisfied**, never merely that the rule
  contributed. A deny or ask rule fired at ask strength by an
  *unproven* condition (§4.2) has not matched, so the default still
  applies and the two combine by rank — `stubcli server $VERB x`
  answers deny, not ask. Without that, uncertainty would soften a
  deny-default tool, which is the one direction §3.3 forbids and the
  real risk `D-052` was reaching for.
- **Alternatives considered:** `D-052`'s floor reading — rejected
  above. *A floor only for gated tools* — the same collapse with a
  special case in it, and it still kills the carve-out. *Keep the floor
  and add a separate "carve-out" construct* — a new declaration form
  for something `ask()` already spells, rejected under rule 11.
- **Approved by:** operator, 2026-08-27 — "default is for what is not
  matched by any rules/grants".

### D-060 — an undeclared token's arity is an ambiguity, not a guess to rest on

- **Date:** 2026-08-28
- **Step:** `009`
- **Context:** §4.2 stated the consequence of an undeclared option as a
  fact and offered declaration as the remedy: "undeclared, `git -C dir
  push` parses as operands `dir push` and no push rule matches." The
  operator met it while reviewing the cases —
  `aws --region eu-west-1 s3 rb s3://logs` answering ask against a
  declaration that denies `s3 rb` — and rejected the reasoning: the
  deny is lost because the tokenizer misplaced an operand, and that is
  a defect whatever the sentence says. On a **gated** tool the closed
  world degrades it to an ask; on a **rules-only** tool nothing catches
  it at all, so `git -C /repo push -f` with `-C` undeclared answers
  **silence** — a forced push, unremarked.
- **Decision:** amend §4.2. Reading still presumes an undeclared token
  bare — that guess is right, and it is what stops a dangerous operand
  hiding in a flag's value — but the presumption is one reading, not
  the only one the engine owes. An undeclared dashed token followed by
  another token leaves the operand alignment ambiguous; rules and
  grants are evaluated against every alignment the ambiguity admits,
  and the strictest verdict stands. The alternatives are bounded by the
  number of undeclared tokens, not by their combinations, so §4.5's
  budget holds.
  The alternative alignment fires at **full declared strength**, not at
  the ask strength §3.2 gives an unproven condition. The engine already
  fires full-strength denies on a guessed alignment — the presumed-bare
  one — so refusing the other guess was not caution, only a preference
  for one of two guesses. The accepted cost is stated in the amendment
  rather than left to be found: a flag whose value is literally a gated
  subcommand word (`tool --output push`) reaches that subcommand's
  verdict. That line already denies today under the bare reading, so
  this adds the mirror of an error the engine had, not a new class of
  one.
- **Alternatives considered:** *fire the alternative alignment at ask
  strength*, by analogy with §3.2's unproven conditions — defensible,
  and rejected because it leaves the hole half-open exactly where it is
  worst: on a rules-only tool an ask is all it could ever produce, so a
  forced push behind an undeclared `-C` would still never deny.
  *Record it as a §4.4 declared blind spot* and keep "declare your
  options" as the remedy — rejected by the operator: a blind spot is
  for a gap that cannot be closed cheaply, and this one costs an
  alternative alignment. *Leave §4.2 and record the question for later*
  — rejected for the same reason, and because `009` is the step where
  rules begin firing, so shipping it would ship the hole.
- **Approved by:** operator, 2026-08-28 — "§4.2 is no sense, of course
  we have to amend that", after proposing the both-hypotheses
  evaluation and the strictest-verdict rule.
