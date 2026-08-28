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
- **Decision:** The guard's only backup (`refs/backups/bash-guard`, its
  single off-machine copy) is pushed at every step close to `origin`'s
  public `backup/bash-guard` branch, reversing `D-017`'s private-remote
  plan — no such remote existed after four closes, leaving the guard
  that gates every Bash call in this project unbacked on one machine.
  The local ref keeps its name and place outside `refs/heads/`, so
  nothing the harness keys on needs re-measuring. **This is irreversible
  and costs something real**: `origin` is public and clone-delivered, so
  the branch publishes the prototype's source into every future clone —
  accepted because the alternative was no backup at all, and `D-025`
  already established that removal here is going-forward-only.
- **Approved by:** operator, 2026-08-21, choosing the public branch after
  the publication and clone-delivery consequences were put to them
  twice.

Detail in git history.

### D-029 — The interpreter floor stands at 3.9; the 3.6 platforms are documented, not covered

- **Date:** 2026-08-21
- **Step:** `006`
- **Decision:** The floor is **3.9**, re-verified against vendor
  documentation after §3.1's "every current LTS distribution" claim
  proved false: SLES 15 SP7 / openSUSE Leap 15 and RHEL 8 (in
  maintenance until 2029) ship 3.6 as the system `python3`. Those two
  are named as a documented limitation — the engine does not parse
  there, the hook fails open, only the sentinel (§7.4) says so — rather
  than dropping the floor, which §3.1 forbids splitting into a dual code
  path and would cost every 3.7–3.9 feature permanently for platforms
  the specification never named. The full table, its method and its
  re-measure recipe are in `docs/verification-record.md`.
- **Approved by:** operator, 2026-08-21, both for the vendor-documentation
  lookups and for the floor-plus-limitation shape of the amendment.

Detail in git history.

### D-030 — Python's check family is ruff and mypy, both pinned to the floor

- **Date:** 2026-08-21
- **Step:** `006`
- **Decision:** ruff (`v0.16.4`, check plus `--check`-only format) and
  mypy (`mirrors-mypy v2.3.1`, strict, `python_version = "3.9"`), both
  configured in `pyproject.toml`. Because both are static, the floor is
  also **executed**: CI's `test` job matrixes the floor and the current
  interpreter, and the suite needs nothing installed so every row runs
  the way a bare `python3` would. Static checking alone would have left
  the floor an unexecuted claim between `006` and `029`, and the failure
  it guards — a hook that fails open on an interpreter that cannot parse
  the engine — is silent.
- **Approved by:** operator, 2026-08-21, for the static-plus-CI-floor
  shape; implementer for the tool choices (within latitude: rule 2's
  check-family clause).

Detail in git history.

### D-031 — The engine's suite is stdlib `unittest`, run against `src/`

- **Date:** 2026-08-21
- **Step:** `006`
- **Decision:** stdlib `unittest`, discovered from `tests/`, no test
  dependency, no installed package — `PYTHON=python3.9 just test` and
  every row of CI's test matrix run the identical command. pytest was
  rejected here because it would have to be installed on every
  interpreter the matrix runs, turning a bare-runner suite into a
  pinned-environment build; revisited if a later engine step needs
  fixtures `unittest` cannot give.
- **Approved by:** implementer (within latitude: a workflow choice the
  bootstrap instructions left open; rule 11's smallest-thing test).

Detail in git history.

### D-032 — Behaviour-bearing steps write their tests first, gated by the operator

- **Date:** 2026-08-21
- **Step:** — (doctrine, adopted before `006`'s close)
- **Decision:** `CLAUDE.md` rule 2 gained the test gate: on
  §4-behaviour or policy-shipping steps (`007`–`014`, `017`, `023`,
  `030`–`035`), cases are transcribed from the specification and the
  corpus, committed and approved *before* implementation exists, handed
  over as a red suite with `just check` green, and frozen once approved.
  `006`'s own suite is the argument for it: written after the code, it
  encoded the code's behaviour rather than its contract — `run()`
  merged stdout and stderr, so every assertion about `explain`'s output
  passed whichever stream carried it, and the defect surfaced only
  because the operator read a terminal.
- **Approved by:** operator, 2026-08-21, choosing the behaviour-bearing
  scope over a uniform test-first rule.

Detail in git history.

### D-033 — The configuration lives at `.claude/frisk/config.py`

- **Date:** 2026-08-21
- **Step:** `007`
- **Decision:** the directory is `.claude/frisk/`, and the file the
  engine executes is `config.py`; adopted collections are `name.py`
  beside it. §5.1 leaves the exact name to the implementation, but every
  later step presupposes one fixed answer — the hook's resolution,
  `021`'s same-configuration requirement, `024`'s scaffold — so settling
  it here rather than letting it drift was the point.
- **Approved by:** implementer (within latitude: §5.1 delegates the name
  explicitly), put to the operator with the step.

Detail in git history.

### D-034 — The config-facing API is declarations with one `when=`

- **Date:** 2026-08-21
- **Step:** `007`
- **Decision:** entities are declared by kind (`tool`, `wrapper`,
  `shell`, `interpreter`); verdicts are constructors (`deny`, `ask`,
  `allow`, `silent`, `grant`) taking a subcommand path, a mandatory
  `reason` and one `when=`; or/any-of lives in the value layer, never as
  a second boolean vocabulary over conditions. Flag arities are declared
  in named buckets, and on a gated tool that declaration *is* the
  accounted set — `closed_world` is three-valued (unset derives from
  whether grants exist) rather than a flag an amendment could silently
  contradict. A tool is named once; a separator makes it a path, an
  absolute path is refused (the config travels with the project and an
  absolute path does not). Shadowing is `tool()` to replace, `amend()`
  with `drop(...)` by label to update. This is the API's whole shape,
  designed against §5.2 in one pass because it is §3.5's stability
  boundary and §5.3's legibility surface at once; it is documented where
  an operator reads it, in `declare.py`'s own docstrings.
- **Approved by:** operator, at `007`'s test gate (`D-032`): the cases
  are the API's first draft, so approving them approved this. The
  secure-mode deferral (additive, not retrofittable per §3.2) was
  confirmed separately.

Detail in git history.

### D-035 — Three matcher rulings the specification leaves open *(amended; evolution in git history)*

- **Date:** 2026-08-21
- **Step:** `007`
- **Decision:** (1) `path_under` is a boundary (a path beneath it
  matches), `path_matching` is not (it constrains the resolved path
  itself) — both readings forced by context B's corpus rulings. (2) An
  empty operand list is **unsatisfied**, not unproven — §3.2 requires
  "every operand" to need at least one, and nothing is uncertain about a
  list known to be empty. (3) `~` expands from `HOME`; `~other` is
  unproven, since resolving another user's home would read the password
  database (§4.5 forbids it). (4) Matchers combine by Kleene's rule, a
  boundary set is an `any_of` over its boundaries — **superseded in part
  by `D-037`**, which replaced ruling (4)'s form-keyed cross-form test
  with a decidability-keyed one; the combination rule itself is
  unchanged.
- **Approved by:** operator, for (4), at the test gate, after the review
  found two cases contradicting each other; implementer for (1)–(3)
  (within latitude: §3.2 leaves them to the implementation, the corpus
  constraining two).

Detail in git history.

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

Detail in git history.

### D-037 — Cross-form path matching asks what the working directory could make true, superseding `D-035`'s fourth ruling

- **Date:** 2026-08-21
- **Step:** `007`
- **Decision:** cross-form path matching keys on decidability, not form.
  Relative-vs-relative and absolute-vs-absolute compare textually; a
  relative value against an absolute boundary is always **unproven**; an
  absolute value against a relative boundary is never satisfied and
  splits — **unsatisfied** where the boundary's components appear
  nowhere in the value, **unproven** where they do (`./etc` against
  `/etc/passwd`, true when the working directory is `/`). §3.2 is
  amended to say so, and the `cd`-poisoning rule now follows from the
  same principle (relative-vs-relative is decidable only because both
  share one unknown base) rather than sitting beside it as a special
  case. The implementer recommended keeping the coarser form-keyed rule,
  since nothing in the corpus depended on the finer one and the change
  relaxes the permission-path direction most deserving suspicion; the
  operator overruled it because this is engine semantics, and moving it
  after adoption would change verdicts projects already trust — the
  correct reading is taken now, while nothing depends on it.
- **Approved by:** operator, 2026-08-21, wording included.

Detail in git history.

### D-038 — The walked shells and interpreters: the corpus is the floor, not the ceiling

- **Date:** 2026-08-22
- **Step:** `007`
- **Decision:** ships `sh`, `bash`, `eval` as shells and `python3`,
  `node`, `ruby`, `perl` as interpreters, each declaring only the
  value-taking options that would shift the walk (options whose
  argument is attached or optional are deliberately absent, since
  declaring them would swallow the next token). The corpus adjudicates
  only four programs and is a floor, not a ceiling: an engine walking
  only those four would leave e.g. `node tools/deploy.js` unwalked, and
  the ruling that a registered tool run through an interpreter is still
  that tool would then hold for one language alone.
- **Approved by:** operator, 2026-08-22 — "corpus is an example, and a
  floor, not a ceiling".

Detail in git history.

### D-039 — A value-optional flag declares what a bare use means

- **Date:** 2026-08-22
- **Step:** `007`
- **Decision:** `may_take_value(*names, default=None)` declares, once
  beside the arity, what the *tool* does with a bare flag; the engine
  substitutes it, so `flag("--argument", one_of("check"))` matches both
  `--argument` and `--argument check`. Undeclared, a bare flag's value
  is unprovable rather than false, for the same reason a `$VAR` value
  is — the value exists and the line does not show it. Without a
  declared default there was no way to write a rule treating the bare
  and default-valued spellings alike; putting the default on the tool
  rather than on each condition means it is stated once and cannot
  disagree with itself.
- **Approved by:** operator, 2026-08-22, whose question defined the
  requirement.

Detail in git history.

### D-040 — The test tree is rooted at the repository, and `tests` is a package

- **Date:** 2026-08-22
- **Step:** `007`
- **Decision:** `tests/__init__.py` exists and the runner passes
  `--top-level-directory .`, so the tree is rooted at the repository
  everywhere, including an editor's test explorer — which always sets
  `top_level_dir` to the project root and has no setting to override it,
  and `unittest` refuses to discover from an unimportable start
  directory otherwise. `D-031`'s decision (stdlib, no dependency,
  `PYTHONPATH=src`) is unchanged; only where discovery starts counting
  moved.
- **Approved by:** implementer (within latitude: a workflow choice),
  reported with the step.

Detail in git history.

### D-041 — A relative boundary that climbs is unproven against an absolute value, not unsatisfied

- **Date:** 2026-08-23
- **Step:** `007`
- **Refines `D-037`,** whose principle it applies rather than changes.
- **Decision:** a leading `..` in a relative boundary is not a
  component to search for — it re-bases the boundary onto a directory
  the line does not name, so it is dropped before the search:
  `../shared` against `/repo/shared/x` is **unproven**, `.scratch`
  against `/etc/passwd` stays **unsatisfied**. The review found `..`
  appearing in no resolved absolute path, so the literal "search for the
  boundary's components" gloss answered unsatisfied even where a working
  directory made the boundary true — false about the world, and in the
  releasing direction.
- **Approved by:** operator, 2026-08-23, with the reasoning: the working
  directory is the unknown, so a climbing boundary is satisfied for some
  values of it and not others — the definition of unproven.

Detail in git history.

### D-042 — §5.3's mandatory reason is §3.2's: every *non-silent* verdict

- **Date:** 2026-08-23
- **Step:** `007`
- **Decision:** §5.3 amended to "every non-silent rule, grant and
  default verdict carries a reason" — `silent()` is the one verdict
  constructor that takes none, since a declared silence refuses nothing
  and has nothing to explain. §5.3 and §3.2 literally contradicted each
  other over `silent()`; the test gate had already settled it in §3.2's
  favour (`test_silence_needs_none`) without anyone recording why.
- **Approved by:** operator, 2026-08-23.

Detail in git history.

### D-043 — A name and an alias are one claim, decided by layer order

- **Date:** 2026-08-23
- **Step:** `007`
- **Decision:** one resolution map, filled in layer order — a name and
  an alias are the same kind of claim on the same word, and the later
  layer wins whichever form each side used; a full declaration releases
  what it replaces, an amendment applies only its delta, and a collision
  within one source still refuses. `describe` prints only an entry's
  *reaching* aliases — not deleted, only shadowed. The cold review found
  alias resolution consulting names before aliases regardless of layer,
  which let a project's own `tool()` silently lose an alias to the
  engine's without saying so, exactly what §3.4 forbids.
- **Approved by:** operator, 2026-08-23 — "layer order decides, like any
  other override case", and, on printing, "I rule on not print the
  shadowed aliases (but they are not deleted)".

Detail in git history.

### D-044 — A declared path may leave the project

- **Date:** 2026-08-23
- **Step:** `007`
- **Decision:** a relative tool path may point outside the project
  (`../shared/deploy.py` accepted; an absolute path stays refused per
  `D-034`). Two repositories checked out side by side is an ordinary
  layout, and refusing would remove a use that works for every checkout
  keeping that layout, for the sake of one never promised — narrow
  because it holds only while the relative position holds, and matches
  only a command line spelled with the same prefix.
- **Approved by:** operator, 2026-08-23 — "developers often have 2
  projects with 2 different repos living beside, and using a tool in the
  other is ok… it's an edge case, but it's okay".

Detail in git history.

### D-045 — Every rule and grant prints where it was written

- **Date:** 2026-08-23
- **Step:** `007`
- **Decision:** every rule and grant carries its own `source:` line,
  unconditionally, not only where it differs from its entry's. A rule
  outlives the entry it was declared on — `amend()` is precisely what
  puts one layer's rule on another layer's entry — so "same layer as its
  entry" is not safe to assume, and a conditional column would make a
  reader interpret an absence rather than read a fact.
- **Approved by:** operator, 2026-08-23.

Detail in git history.

### D-046 — `registry --value` narrows to what can answer, and retires at `009`

- **Date:** 2026-08-23
- **Step:** `007`
- **Decision:** `--value` narrows its output to declarations that could
  actually answer the value (39 lines instead of 142 on a sample
  project, an empty match reported rather than silently blank), and
  retires entirely once `009` ships `explain` with a real verdict.
  `--value` existed only because `007` had nothing that judged a line;
  it evaluates one string against every matcher with no line around it,
  so it could never show the `cd` poisoning and answers "what would this
  matcher say", never "what happens if I run this" — `explain` answers
  the second. **Executed at `009`**: the flag, `describe`'s parameter
  and the machinery behind it are gone, confirmed by grep.
- **Approved by:** operator, 2026-08-23 — narrow it now, "and we will
  delete it later when explain works".

Detail in git history.

### D-047 — `speaking` names what §4.1's raw scan looks for

- **Date:** 2026-08-24
- **Step:** `008`
- **Decision:** §3.2 gains **speaking** — carrying rules, grants, or a
  non-silent default verdict — and §4.1's unparseable-line scan refers
  to it instead of borrowing *rule-bearing* (§3.2's narrower term) for a
  strictly larger set. The two readings disagreed exactly where it
  mattered: a grants-only gated tool has no rules, so under the narrow
  reading its unparseable line would scan clean and answer silent about
  a deny-by-default tool. No engine behaviour changes — only the word
  §4.1 had borrowed.
- **Approved by:** operator, 2026-08-24 — rename §4.1's predicate, no
  behaviour change.

Detail in git history.

### D-048 — A newline is `\r\n`, `\n` or a lone `\r`

- **Date:** 2026-08-25
- **Step:** `008`
- **Decision:** all three spellings are line endings frisk splits on.
  Splitting only at `\n` leaves a trailing `\r` on the preceding flag
  (matching nothing, firing nothing); treating a lone `\r` as data —
  closer to bash — hides a whole invocation instead of mangling one
  flag, the worse of the two residues. The lone-`\r` treatment is a
  deliberate over-read of the shell: the cost is a rare false prompt
  against a hidden forced push.
- **Approved by:** operator, 2026-08-25 — all three spellings.

Detail in git history.

### D-049 — `speaking` is its enumeration, not a principle

- **Date:** 2026-08-26
- **Step:** `008`
- **Decision:** deleted §3.2's gloss on *speaking* (`D-047`'s
  parenthetical description) — it was both too wide (matches any
  registered tool via the universal assignment world, wrappers included,
  which §4.1's scan deliberately excludes) and too narrow (misses a
  closed-world-only tool with no rules and a silent default). *Speaking*
  is now defined as its enumeration alone. No behaviour changes: the
  enumeration is what `D-047` decided and what the engine already
  implemented.
- **Approved by:** operator, 2026-08-26 — delete the gloss.

Detail in git history.

### D-050 — Short-flag bundling, declared per tool and on by default

- **Date:** 2026-08-26
- **Step:** `008`
- **Decision:** a run of short flags splits only where every letter is
  itself a declared flag (a token that is itself a declared flag is
  never split), and `tool(..., bundled=False)` turns splitting off for
  tools whose long options carry one dash (`find -name`, `java -cp`).
  **Default on**, because unsplit bundling is a missed deny that says
  nothing (`git push -fu origin main` matching no `-f` rule), while
  over-splitting is a visible, correctable refusal — a safe default only
  when remembered is not one.
- **Approved by:** operator, 2026-08-26 — "`bundled=` on `tool()`,
  default `True`", after the single-dash long-flag class was raised and
  an `ansible-playbook -vvv` bug demonstrated the naive fix's cost.

Detail in git history.

### D-051 — `allow` is earned per invocation and withheld at the line

- **Date:** 2026-08-26
- **Step:** `009`
- **Decision:** an invocation earns `allow` exactly as it earns any
  other verdict — the rule fires, the per-invocation verdict is `ALLOW`
  — and the **line** answers `SILENT`, since every condition that would
  release it (the baseline read tools of `017`, substitution analysis of
  `011`, open fact (c)) is still unmeasured or unbuilt. Nothing has to
  be undone at `017`; the release is added there. *(Corrected
  2026-08-28: this entry originally said `frisk explain` shows the
  earned allow. It does not — the report never prints a per-invocation
  verdict, so an operator debugging an `allow` rule sees nothing at all.
  That is a gap in the report, not a ruling against showing it, and
  `017` is where it closes.)*
- **Approved by:** implementer (within latitude: `PLAN.md` `009` stages
  the allow rows at `017`; this entry records how the verdict behaves in
  the meantime).

Detail in git history.

### D-052 — the default verdict is what no grant released, not what no rule matched *(reversed by `D-059`)*

- **Reversed by `D-059`:** read this entry as the position the operator
  overturned at the case gate, not as the engine's behaviour.
- **Date:** 2026-08-26
- **Step:** `009`
- **Decision:** proposed computing an invocation's base contribution
  always — silent where a grant holds, the tool's default otherwise —
  with rules layered on top by rank, reasoning from §3.3 that a fired
  rule is not evidence of safety. Rejected: it makes the default a floor
  rather than a fallback, so a deliberate carve-out rule weaker than the
  default (`ask("get", …)` on a deny-default tool) would silently do
  nothing — the same failure `D-056` had just rejected for
  `closed_world=True` an hour earlier.
- **Approved by:** implementer (within latitude), later reversed by the
  operator — see `D-059`.

Detail in git history.

### D-053 — a malformed invocation costs an ask on every tool

- **Date:** 2026-08-26
- **Step:** `009`
- **Decision:** a malformed invocation (a declared value-taking flag
  with nothing after it) contributes an **ask** of its own, on every
  tool, and releases no grant. §4.2 states the malformed case without
  scoping it to gated tools; on a rules-only tool with a silent default
  there would otherwise be nothing for "unproven, not safe" to attach
  to, and `git -C` would answer silence — the direction §3.3 forbids.
- **Approved by:** implementer (within latitude: §3.3's principle
  applied where §4.2 states a fact without a cost).

Detail in git history.

### D-054 — an unproven tool identity caps the invocation at ask

- **Date:** 2026-08-26
- **Step:** `009`
- **Decision:** an unresolved path (a relative spelling of a
  path-declared tool after an in-line `cd`) releases no grant and caps
  the verdict at **ask** — a would-be deny softens, a silence stays a
  silence — following §4.2's own analogy to an unproven path match.
  Producing the full deny would be the "wrong deny" §4.3 forbids: the
  command may be a different file entirely. Refined by `D-063`, which
  fixes how the doubt is *cited*.
- **Approved by:** implementer (within latitude: §4.2's own analogy).

Detail in git history.

### D-055 — `explain`'s exit statuses, and what an unconfigured project answers

- **Date:** 2026-08-26
- **Step:** `009`
- **Decision:** `0` silent, `1` ask, `2` usage, `3` deny, `4` no
  configuration, `5` configuration error (`allow` gets no status until
  `017`, since no line returns one — `D-051`). Silence is `0` because it
  is a real answer, so `frisk explain "$cmd" || refuse` refuses exactly
  where frisk objected or could not. An **unconfigured project answers
  4**, never the verdict reached against the engine's default layers
  alone — that verdict was reached against no boundary, and §5.4
  requires the inertness to be unmissable rather than inferable.
- **Approved by:** implementer (within latitude: §9 leaves the numbers
  to the implementation).

Detail in git history.

### D-056 — what a closed world does, and what an ungranted tool defaults to

- **Rewritten in place**, 2026-08-27, commit `3c60940`: an earlier draft
  under this id proposed ask for any gated tool, and the operator
  settled it differently at the case gate before the step was tagged.
  The format above freezes an id and makes a reversal a *new* entry
  citing the old, and that rule admits no exception for an untagged
  step — recorded here rather than undone, and not to be repeated.
- **Date:** 2026-08-27
- **Step:** `009`
- **Decision:** two parts. **(a)** the implicit default for a gated tool
  is §3.2's enumeration verbatim: ask where the tool declares grants,
  silent otherwise (`bool(entry.grants)`, not `entry.gated`). **(b)** a
  flag outside a gated tool's closed world defeats every grant **and**
  contributes its own ask, cited by name — making the declared flag list
  an opt-in list the operator steers by editing, rather than decorative.
  Without (b), `closed_world=True` with no grants changes no verdict at
  all.
- **Approved by:** operator, 2026-08-27 — "the more flexible and natural
  for the user; if the user wants an ask on `--check`, they remove it
  from the flags list (that is an opt-in list)".

Detail in git history.

### D-057 — secure mode meets the engine's default layers: deferred to `010`

- **Date:** 2026-08-27
- **Step:** `009`, resolved at `010`
- **Decision:** `009` writes no case, either way, for how secure mode
  treats the engine's default-layer entries (every wrapper, shell and
  interpreter in `defaults.py`, all registered with no declared default)
  — §3.2 pulls two ways on `sudo ls` in secure mode (global default, or
  exempt as a default-layer entry), `test-reviewer` raised it at the
  case gate, and a wrapper's own contribution to a line is `010`'s
  design (the walk it introduces). A case frozen here would pin wrapper
  behaviour against a build that does not walk one yet. Mirrored in
  `PLAN.md` `010`'s deliverables so the deferral has a step to land in.
- **Approved by:** operator, 2026-08-27 — defer to `010`.

Detail in git history.

### D-058 — `/review-step`, the file-by-file review loop

- **Date:** 2026-08-27
- **Step:** `009`
- **Decision:** a fourth ritual, `.claude/skills/review-step/` — one
  cycle per file the operator picks: feedback and discussion with
  nothing changing until they say they are finished, then everything
  agreed is implemented without committing, validated, and only then
  committed, with a ledger of every file's state written to the session
  scratchpad. Improvised at `009` (a 1,000-line case file, six decision
  entries, a spec-reading question) and it lost its own state the moment
  the conversation grew; validating a file is explicitly not approving
  the step, which stays `/approve-step`'s job.
- **Approved by:** operator, 2026-08-27 — requested during `009`'s case
  review, "to enable this mode easily on any step".

Detail in git history.

### D-059 — the default verdict is a fallback, not a floor (reversing `D-052`)

- **Date:** 2026-08-27
- **Step:** `009`
- **Decision:** the default is consulted **only** where no rule matched
  (matched meaning its conditions were satisfied — an ask/deny rule
  fired merely at ask strength by an unproven condition has not matched,
  so the default still applies) and no grant held; rules and defaults
  never collapse into one floor. The floor reading (`D-052`) made a
  declaration dead — an operator's own weaker carve-out rule on a
  deny-default tool would do nothing — and duplicated a construct the
  model already keeps separate: an unconditional `deny(reason=…)` rule
  *is* the floor, when one is wanted.
- **Approved by:** operator, 2026-08-27 — "default is for what is not
  matched by any rules/grants — else it's not a default, it's an
  enforcing minimal rule."

Detail in git history.

### D-060 — an undeclared token's arity is an ambiguity, not a guess to rest on

- **Date:** 2026-08-28
- **Step:** `009`
- **Decision:** §4.2 amended. Reading still presumes an undeclared
  dashed token bare, but that presumption is one reading, not the only
  one owed: where the token is followed by another, the operand
  alignment is ambiguous, and rules and grants are evaluated against
  every alignment the ambiguity admits (bounded by the number of
  undeclared tokens, never their combinations — §4.5's budget holds),
  the strictest verdict standing, fired at **full declared strength**.
  The engine was already firing full-strength denies on the bare-token
  guess, so refusing the alternative guess was not caution, only a
  preference between two guesses — and on a rules-only tool an
  ask-strength alternative would never actually deny, leaving the hole
  open exactly where it is worst: a gated tool's closed world at least
  degrades the miss to an ask (`aws --region … s3 rb s3://logs`), while
  a rules-only tool has nothing to catch it and `git -C /repo push -f`
  with `-C` undeclared answered **silence**.
  Accepted cost, stated rather than left to be found: a flag whose
  literal value is a gated subcommand word (`tool --output push`) now
  reaches that subcommand's verdict — the mirror of an error the bare
  reading already had.
- **Approved by:** operator, 2026-08-28 — "§4.2 is no sense, of course we
  have to amend that", after proposing the both-hypotheses evaluation
  and the strictest-verdict rule.

Detail in git history.

### D-061 — `--` is structure, not a flag the closed world weighs

- **Date:** 2026-08-28
- **Step:** `009`
- **Decision:** `--` is exempt from the unaccounted-flag/closed-world
  check — still matchable by rules (context A's `git checkout -- file.py`
  depends on it), no longer a breach. §4.2 requires `--` to stay
  matchable, but the closed world was comparing it against the tool's
  declared flags too, so every gated tool asked on it unless the
  operator explicitly declared `flag("--")` — found by `code-reviewer`.
- **Approved by:** operator, 2026-08-28 — raised in the review round and
  settled together with `D-062`.

Detail in git history.

### D-062 — an engine reason explains; it never advises removing a token

- **Date:** 2026-08-28
- **Step:** `009`
- **Decision:** a reason the **engine** writes states the objection and,
  only where the engine actually knows one, a safe path — never advice
  to remove an unaccounted token, since by definition the engine does
  not know what the token is for and it may be the very thing protecting
  the deploy. Advice addressed to the configuration author belongs in
  documentation, never in a runtime reason the model reads.
- **Approved by:** operator, 2026-08-28 — "saying to the agent it should
  remove the `--check-file` flag that protect the deploy look like a
  defect of the engine".

Detail in git history.

### D-063 — an unproven identity is cited where it explains, never where it decides

- **Date:** 2026-08-28
- **Step:** `009`
- **Decision:** the unresolved-path doubt decides nothing on its own —
  it defeats grants and caps the verdict at ask exactly as `D-054` says,
  but contributes no free-standing verdict. It is cited, marked
  `(unproven)`, only where the invocation objected for some other
  reason, never where nothing did. The implementation had drifted from
  `D-054`'s own "silence stays silence" clause, producing a false ask on
  a line where both possible readings are silent
  (`cd /srv && ./tools/deploy.py status`) — found by `test-reviewer` as
  an unreached branch.
- **Approved by:** operator, 2026-08-28 — "go for it, but if you have to
  change more tests than the test that was flagged as wrong it's a
  signal we have an issue". No existing case changed.

Detail in git history.
