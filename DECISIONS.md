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
  workflow choice the bootstrap instructions left open.
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
- **Context:** Implementation sessions do not persist. Without a
  memory that lives in the repository, each session would re-derive the
  state of the work from the code, and the specification's boundary
  between what is decided and what is open would erode silently — which
  is the failure mode this project exists to prevent, one layer up.
- **Decision:** Adopt the workflow the operator's bootstrap prompt
  prescribes, in full and permanently: `SPECIFICATIONS.md` is read-only
  for the implementer and changes only through the amendment channel of
  rule 1; work proceeds one operator-gated step at a time, nothing
  handed over unverified; all memory lives in `PLAN.md`,
  `DECISIONS.md`, `CLAUDE.md` and `.claude/docs/`; decisions are logged
  here; secrets never enter the repository; commits are small,
  step-prefixed and carry their own documentation updates; repository
  files are English; `README.md` is the neutral entry point; bug
  reports on the current step are the implementer's to drive within a
  stated boundary of free acts; persistence has a budget and asking is
  part of the workflow; and the smallest thing that satisfies a rule is
  the right thing. The rules are restated in `CLAUDE.md`, keeping the
  bootstrap prompt's numbering, because tooling and later entries cite
  them by number.
- **Alternatives considered:** *Working from the specification alone,*
  rejected because the specification deliberately says nothing about
  process and leaves open facts to be settled during implementation —
  there would be no record of who settled what. *A lighter workflow
  (plan plus commits, no decision log),* rejected because the
  specification's *should* tier is explicitly a latitude to deviate
  from **with reason**, and a reason nobody wrote down is a deviation
  nobody can review.
- **Approved by:** operator (the bootstrap prompt is the approval).

### D-002 — `CLAUDE.md`'s size budget, derived rather than inherited

- **Date:** 2026-08-19
- **Step:** — (bootstrap)
- **Context:** Rule 3 sets a baseline budget of 220 lines with a target
  of about 180 at first handover, and states that a repository whose
  rules carry long whole-carry text has a higher floor than those
  numbers assume — to be derived at the first task and logged, rather
  than met by breaching it later. This repository carries **two**
  whole-carry blocks: rule 9's boundary enumeration, which may never be
  compressed, summarised or moved to a lazily-read file, and rule 1's
  `bash_guard.py` quarantine, which lives until the parity retirement
  step. Neither may be trimmed to make room.
- **Decision:** This project's budget is **360 lines hard cap, ~330 at
  first handover**, replacing rule 3's 220/180 baseline. The arithmetic,
  measured on the file as written rather than estimated: the two
  whole-carry blocks are 66 lines (rule 9's enumeration 37, the
  quarantine 29); the remaining nine rules restated tightly enough that
  a fresh session behaves identically are ~165; the three carriers this
  file is required to be — the plan-entry shape in both its open and
  compacted forms, rule 6's tag-message shape, and the `Current state`
  section with its closed list — are ~50; the layout map, the session
  routine and the header are ~35; the temporary tooling-templates block
  is 12 and leaves at step `003`. That is 328 with no fat left after two
  compression passes, so the cap is set at 360 to leave the next session
  headroom to add a pointer without reflowing the document first. The
  eviction order is unchanged and is not the implementer's to reshuffle:
  first anything context-specific a read-trigger can reach
  (`.claude/docs/`), then the tooling-templates block once its directory
  is gone, then per-step detail the plan already carries. Rule 9's
  enumeration never leaves; rule 1's quarantine text leaves only when
  the retirement step deletes it; the current-step pointer stays. Two
  scheduled shrinks are already known: step `003` removes the templates
  block (−12), and the retirement step (`PLAN.md` `025`) removes the
  quarantine (−29). **The budget is re-derived downward at each**,
  rather than kept as slack.
- **Alternatives considered:** *Keeping the 220/180 baseline and
  deviating later,* rejected on the rule's own reasoning — a budget
  first met by breaching it teaches the next session that the budget is
  decorative. *Moving the boundary enumeration or the plan-entry shapes
  into `.claude/docs/` to fit,* rejected: rule 9 forbids the first
  explicitly, and the second is what the early closes read before any
  ritual exists to cite it. *Trimming the rules until they fit 220,*
  rejected as the floor being met by deleting something with nowhere
  else to go — the restatement is the rules' sole carrier after
  bootstrap.
- **Approved by:** implementer (within latitude: rule 3's derive-and-log
  clause, whose stated legitimate outcome is a budget of this project's
  own).

### D-003 — Split the prescribed foundation step `001` into two gates

- **Date:** 2026-08-19
- **Step:** `000`–`004` (the foundation milestone)
- **Context:** The bootstrap instructions prescribe four foundation
  steps and simultaneously invite the plan to split any of them that is
  too big for a single test, noting that step `001`'s probe campaign and
  its record are separately testable from the baseline proposal. As
  prescribed, `001` carries the guard instantiation, a tool inventory, a
  registry and its cases, the backup ref and its restore proof, the
  whole settings baseline, two harness gates, and a probe campaign whose
  method requires a mid-step session restart — with a single operator
  gate at the end.
- **Decision:** Split it. `001` delivers the guard, the settings
  baseline and both gates, tested by the operator's review of the
  proposal plus a green `--selftest`; `002` delivers the probe campaign
  and `.claude/docs/guard-record.md`, tested by reading the record and
  running the three liveness commands. The workflow tooling becomes
  `003` and CI `004`. All five remain **one milestone**, and CI stays
  last within it: the repository is not bootstrapped until its CI has
  run green.
- **Alternatives considered:** *Keeping the prescribed four,* which
  would put a settings proposal, a session restart and a probe campaign
  behind one gate — the operator's first correction would then arrive
  after the session had already been spent proving the thing being
  corrected. *Splitting further (guard, settings, probes as three),*
  rejected: the guard decides the shape of the settings, so proposing
  one without the other asks the operator to review half a boundary.
- **Approved by:** *pending* — put to the operator at the plan review.

### D-004 — The §13 re-inventory ruling

- **Date:** 2026-08-19
- **Step:** — (the plan's first artifact)
- **Context:** §13 requires the plan to open by re-inventorying the
  pre-1.0 parity bar: for each item accreted onto it, a written
  assessment of whether its *placement* still earns parity. The items
  stay owed whatever the ruling; only their stage is challengeable.
- **Decision:** Recorded in `PLAN.md` §1. The implementer's
  recommendation is that **the bar stands as §13 draws it** — every
  accreted item survives its own challenge, three of them (the
  control-structure routing minimum, §7.2's second class, §7.3's
  engine-version trigger) because they are cheap riders on machinery the
  bar already owes, and the one apparent deferral candidate (the starter
  registry's docker shape, a specification *should*) turns out to be
  pinned by the parity yardstick, since 109 of the behavior corpus's
  rulings run against a git-and-docker registry. Two placements are
  noted rather than challenged: docker as just described, and §5.4's
  once-per-session visibly-inert notice, which §13 already stages at 1.0
  with its residue stated.
- **Alternatives considered:** *Moving §7.3's engine-version trigger to
  1.0,* the largest single saving available and the one the "reviewable
  by one human" premise most invites — rejected because it is the one
  failure mode the plugin channel introduces and the prototype never
  had: an update that silently flips a verdict. *Moving docker out of
  the starter registry,* rejected as above; it is pinned by item 1.
- **Approved by:** *pending* — the operator rules at the plan review.
