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
- **Decision:** This project's budget is **390 lines hard cap, ~365 at
  first handover**, replacing rule 3's 220/180 baseline. The arithmetic,
  measured on the file rather than estimated: the two whole-carry blocks
  are 66 lines (rule 9's enumeration 37, the quarantine 29); the
  remaining nine rules restated tightly enough that a fresh session
  behaves identically are ~200; the three carriers this file is required
  to be — the plan-entry shape in both forms, rule 6's tag-message shape,
  and the `Current state` section with its closed list — are ~45; the
  layout map, the session routine and the header are ~30; the temporary
  tooling-templates block is 10 and leaves at step `004`. The number was
  derived twice: 360 before the file was written, then 390 after the
  bootstrap fidelity review recovered roughly forty lines of load-bearing
  clauses the first restatement had dropped (rule 2's check/test
  definitions and its three limits, rule 3's path-scoped-rules mechanism,
  the governance well-formedness family, the pre-approval gate on writing
  a runner). A trim pass gave about half of that back. The revision is
  recorded rather than hidden because a budget that moves silently is a
  budget nobody believes.
  The eviction order is unchanged and is not the implementer's to
  reshuffle: first anything context-specific a read-trigger can reach
  (`.claude/docs/`), then the tooling-templates block once its directory
  is gone, then per-step detail the plan already carries. Rule 9's
  enumeration never leaves; rule 1's quarantine text leaves only when the
  retirement step deletes it; the current-step pointer stays. Two
  scheduled shrinks are already known: step `004` removes the templates
  block (−10) and the retirement step (`PLAN.md` `027`) removes the
  quarantine (−29). **The budget is re-derived downward at each**, rather
  than kept as slack.
- **Alternatives considered:** *Keeping the 220/180 baseline and
  deviating later,* rejected on the rule's own reasoning — a budget first
  met by breaching it teaches the next session that the budget is
  decorative. *Moving the boundary enumeration or the plan-entry shapes
  into `.claude/docs/` to fit,* rejected: rule 9 forbids the first
  explicitly, and the second is what the early closes read before any
  ritual exists to cite it. *Trimming the rules until they fit 220,*
  rejected as the floor being met by deleting something with nowhere else
  to go — this restatement is the rules' sole carrier after bootstrap,
  and the fidelity review demonstrated that trimming was already the
  active failure mode, not a hypothetical one.
- **Approved by:** implementer (within latitude: rule 3's derive-and-log
  clause, whose stated legitimate outcome is a budget of this project's
  own).

### D-003 — Split two of the prescribed foundation steps

- **Date:** 2026-08-19
- **Step:** `000`–`005` (the foundation milestone)
- **Context:** The bootstrap instructions prescribe four foundation steps
  and simultaneously invite the plan to split any that is too big for a
  single test — noting explicitly that step `001`'s probe campaign and
  its record are separately testable from the baseline proposal, and
  that "this step is too big to judge in one gate" is among the most
  valuable findings the bootstrap review can return. Two of the four were
  overloaded. As prescribed, `001` carried the guard instantiation, a
  tool inventory, a registry and its cases, the backup ref and its
  restore proof, the whole settings baseline, two harness gates, and a
  probe campaign whose method requires a mid-step session restart, behind
  one gate. The tooling step carried nine template instantiations plus a
  probe — the `CLAUDE.md`-reaches-a-subagent probe — whose pre-committed
  unfavourable branch would rewrite the body of all five agents.
- **Decision:** Split both. `001` delivers the guard, the settings
  baseline and both gates, tested by the operator's review of the
  proposal plus a green `--selftest` and a proven restore; `002` delivers
  the probe campaign and `.claude/docs/guard-record.md`. `003` runs the
  subagent probes and instantiates the four **skills** — testable by real
  ritual invocations; `004` instantiates the five **agents** under the
  now-known context rule and deletes the templates directory. CI becomes
  `005`. All six remain **one milestone**, and CI stays last within it:
  the repository is not bootstrapped until its CI has run green.
- **Alternatives considered:** *Keeping the prescribed four,* which would
  put a settings proposal, a session restart and a probe campaign behind
  one gate, and would write five agents against an unmeasured assumption
  about what they can read — the operator's first correction would arrive
  after the session had already been spent. *Splitting `001` three ways
  (guard, settings, probes),* rejected: the guard decides the shape of
  the settings, so proposing one without the other asks the operator to
  review half a boundary.
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
  noted rather than challenged: docker as just described; §5.4's
  once-per-session visibly-inert notice, which §13 already stages at 1.0
  with its residue stated; and the sentinel, which the plan's first draft
  built early and `D-007` returns to the 1.0 stage §13 gives it.
- **Alternatives considered:** *Moving §7.3's engine-version trigger to
  1.0,* the largest single saving available and the one the "reviewable
  by one human" premise most invites — rejected because it is the one
  failure mode the plugin channel introduces and the prototype never
  had: an update that silently flips a verdict. *Moving docker out of
  the starter registry,* rejected as above; it is pinned by item 1.
- **Approved by:** *pending* — the operator rules at the plan review.

### D-005 — Declarations before reading the line

- **Date:** 2026-08-19
- **Step:** `007` (declarations, matchers, layering) and `008` (reading
  the line)
- **Context:** The plan's first draft built §4.1's line reading before
  §3.4's declaration model. The bootstrap cold review found the
  dependency inverted, and it is: declared flag arities, alias and
  project-relative-path recognition, the gated/registered/rule-bearing
  distinction and the rule-bearing-name fallback scan are all defined in
  terms of declarations. A step whose gate cannot be reached without the
  next step's output is not a gate.
- **Decision:** The declaration model, the matchers and the layering come
  first (`007`), then reading the line (`008`). `007` additionally ships
  the effective-registry inspection surface §3.4 requires anyway ("the
  effective registry must be inspectable (§9) so composition never hides
  a rule"), which is what makes it testable by the operator before any
  verdict exists.
- **Alternatives considered:** *Moving only the declaration-dependent
  half of the reading step forward,* the smaller textual edit, rejected
  because it inflates one step and leaves the conceptual order still
  inverted. *Leaving the order and testing `008` by unit suite alone,*
  rejected: rule 2 requires each step testable by the operator, and a
  suite the operator does not read is not that test.
- **Approved by:** *pending* — put to the operator at the plan review
  (step reordering is a joint decision, rule 4).

### D-006 — The verification pass split into two gates

- **Date:** 2026-08-19
- **Step:** `015` and `016`
- **Context:** The plan's first draft settled nine open facts in one
  step — four of them escalating to the operator mid-step, two of them
  matrices across every permission mode. The cold review called it a
  campaign rather than a step, and proposed three gates: the
  mode-independent facts, open fact (c) alone, and the mode matrix.
- **Decision:** Two gates, split by apparatus rather than by fact.
  `015` settles the go/no-go (c) together with the mode-independent items
  5, 10, 11 and 13 — cheap, no permissive modes. `016` settles the
  permissive-mode matrix: (a), (b), (d) and item 9. §2.1's sequencing
  mandate binds only (c) before the allow machinery, which both orders
  satisfy.
- **Alternatives considered:** *The reviewer's three-way split,* rejected
  as over-splitting: (c) is a single measurement, and its *ruling* is a
  separate operator decision inside `015` either way, so a gate of its
  own buys a heading rather than a decision point. *Leaving one step,*
  rejected on the reviewer's reasoning — it was the plan's most expensive
  step and the hardest to resume from mid-flight.
- **Approved by:** *pending* — put to the operator at the plan review.

### D-007 — The sentinel restaged to 1.0

- **Date:** 2026-08-19
- **Step:** `035` (was inside the pre-parity milestones)
- **Context:** The plan's first draft built §7.4's sentinel and its kill
  switches before the parity declaration. §13's pre-1.0 bar is a closed
  list and does not name them; §13's **1.0** bullet names "the sentinel
  offer" explicitly. §13 also states the governing principle: the
  reviewable surface is a cost even when an AI implements.
- **Decision:** The sentinel and both kill switches move to `035`, in
  Milestone 9, which is where §13 stages them. This is a correction
  restoring the specification's own staging, not a challenge to it. The
  consequence is stated rather than hidden: before 1.0, two rows of
  §7.5's coverage map — "plugin absent on this machine" and "config
  absent where one existed" — have no catcher, and the parity statement
  at `026` names that residue.
- **Alternatives considered:** *Keeping it pre-parity as a deliberate
  quick win,* which §13's "everything else may ship here as a quick win"
  permits — a real option, and the reason this is put to the operator
  rather than settled: the sentinel is the only layer that catches a
  fresh clone with no plugin, and testers are exactly the population that
  clones.
- **Approved by:** *pending* — put to the operator at the plan review.

### D-008 — Milestone 9's entries are deliberately coarse

- **Date:** 2026-08-19
- **Step:** `030`–`041`
- **Context:** `CLAUDE.md`'s plan conventions require an open step entry
  to carry objective, spec sections, deliverables with their locations,
  and a test statement. Milestone 9's twelve entries carry objective and
  deliverables only. The bootstrap cold review flagged the deviation, and
  `CLAUDE.md` rule 4 says a workflow choice left open gets logged rather
  than assumed.
- **Decision:** Milestone 9's entries stay coarse until Milestone 8
  closes, then are expanded to full entries before any of them starts.
  Sizing a step's test instructions against a system whose earlier half
  does not exist produces text that will be rewritten, and the plan is
  read every session in the meantime.
- **Alternatives considered:** *Writing them in full now,* rejected as
  planning against a system that does not exist — several of these steps
  replace work from earlier milestones (`031` replaces `013`'s routing
  minimum) and their shape depends on how that work landed. *Omitting
  them,* rejected outright: the plan must account for the whole
  specification, and an unlisted requirement is a lost one.
- **Approved by:** implementer (within latitude: a workflow choice the
  bootstrap instructions left open), with the deviation surfaced in
  `PLAN.md` §14 for the operator to overrule.
