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
- **Approved by:** operator (2026-08-19, at the plan review).

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
  noted rather than challenged: §5.4's
  once-per-session visibly-inert notice, which §13 already stages at 1.0
  with its residue stated; and the sentinel, which the plan's first draft
  built early and `D-007` returns to the 1.0 stage §13 gives it.
- **Alternatives considered:** *Moving §7.3's engine-version trigger to
  1.0,* the largest single saving available and the one the "reviewable
  by one human" premise most invites — rejected because it is the one
  failure mode the plugin channel introduces and the prototype never
  had: an update that silently flips a verdict. *Moving docker out of
  the starter registry,* initially rejected on a mistaken reading of the
  corpus and then **accepted** on the operator's correction — see
  `D-009`, which supersedes that half of this entry.
- **Approved by:** operator (2026-08-19, at the plan review). The ruling
  is the recommendation as recorded in `PLAN.md` §1: the bar stands as
  §13 draws it, with the starter registry's content settled separately by
  `D-009`.

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
- **Approved by:** operator (2026-08-19, at the plan review).

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
- **Approved by:** operator (2026-08-19, at the plan review).

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
- **Approved by:** operator (2026-08-19, at the plan review, by approving
  the plan that stages the sentinel at 1.0). Recorded explicitly because
  the alternative was put to the operator as a live choice rather than a
  formality: pulling the sentinel back before parity remains available as
  a re-staging decision if the residue proves uncomfortable in use.

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

### D-010 — `check` snapshots and restores rather than repairing

- **Date:** 2026-08-19
- **Step:** `000` (the harness)
- **Context:** `check` must assert without repairing: fixer hooks
  (`trailing-whitespace`, `end-of-file-fixer`, `mixed-line-ending`)
  rewrite files, the commit hook is where they may write, and a check
  that rewrites the working tree as a side effect is the
  `--intent-to-add` prohibition one step milder — with the rituals that
  read `git status --porcelain` for a clean tree sitting downstream of
  it. No standard mechanism does this. `pre-commit` has no check-only or
  `--no-fix` mode; its "files were modified by this hook" gives detection
  but not reversion; `git checkout --` would revert tracked files but is
  a git write to the working tree, which rule 9 protects, and cannot
  restore an untracked file at all.
- **Decision:** `scripts/check.sh` copies its file list to a temporary
  directory before running the hooks, compares afterwards, restores what
  was rewritten, names it, and fails. The revert runs from an `EXIT`
  trap so an interrupt restores too; a failed restore keeps the snapshot
  and prints its location. No git operation is involved — nothing touches
  the index, the working tree's git state, or history.
- **Alternatives considered:** *`git checkout --` / `git stash`,* rejected
  as git writes to the protected working tree, and blind to untracked
  files. *Detect-only (fail if the tree changed, leave the edits),*
  rejected: it repairs, which is the thing forbidden. *A `tar`-based
  snapshot,* which would also carry symlink-ness and modes — rejected as
  a portability cost (BSD and GNU `tar` differ on `--null`/`-T`) for a
  case that cannot arise: pre-commit's `identify` types symlinks as
  `symlink`, so no fixer hook writes through one. *Dropping the fixer
  hooks entirely so `check` needs no protection,* rejected: whitespace
  discipline is owed from `000`, and the commit hook is the right place
  for it to write.
- **Approved by:** implementer (within latitude: a workflow choice the
  bootstrap instructions left open — the harness's shape and names).
  **Recorded with a process note:** rule 2 says a mechanism written
  because nothing standard fits is put to the operator *before* it is
  built, and this one was not. It is ~30 lines of glue rather than a
  runner, and step `000`'s cold review searched for a standard
  replacement and found none — but the rule asks for the question, not
  for the answer to be right, and the question was skipped. Reversible on
  request.

### D-011 — The permission baseline: broad allows, a guard, a short deny backstop

- **Superseded in part by `D-013` (2026-08-20):** the `just` treatment
  below — a grant in the registry, six exact-match allows in the
  settings — is overturned. Everything else in this entry stands.
- **Date:** 2026-08-20
- **Step:** `001` (the permission and hook baseline)
- **Context:** rule 9 draws a boundary around this repository's own
  development — local and read-only is free, outward or usage-spending
  is gated — and rule 4 says that boundary is never the implementer's to
  set. Claude Code's native permission rules match on command prefixes,
  which cannot express "a force push however it is spelled":
  `Bash(git push:*)` misses `git -C dir push`, and no prefix reaches a
  push hidden in a substitution. A parsing `PreToolUse` guard can, which
  is why one is instantiated here — and why the settings must be shaped
  around it rather than duplicating it.
- **Decision:** `.claude/settings.json` carries, as one piece:
  `defaultMode: acceptEdits`; `disableBypassPermissionsMode: "disable"`
  and **no** `disableAutoMode`, leaving `auto` reachable so `002` can
  A/B a classifier against the guard; one **broad allow per
  registry-bearing tool** (`git`, `gh`, `pip`, the delete family, the
  boundary-file writers) so the guard is what judges them, plus a short
  list of plainly read-only utilities that the guard leaves silent and
  which would otherwise prompt on every `ls`; **exact-match allows for
  the six documented `just` recipe spellings** rather than
  `Bash(just:*)`, because a broad allow on a command-runner is a broad
  allow on everything it runs the moment the guard is dead; **no broad
  allow for any runner** — `python3`, `sudo`, `env`, `xargs` and their
  kin included, which is a real cost, since rule 9's free list names
  `python3` and it will now prompt, as will the documented direct
  equivalents `bash scripts/check.sh` and `.venv/bin/pre-commit run`,
  a friction accepted rather than papered over with `Bash(bash:*)`;
  **no `ask` rule for anything the guard gates**, since a matching `ask`
  prompts even where the guard says allow and would cancel every
  carve-out; **no prefix rule restating a guard decision**, `git push`
  included; an `ask` tier on the **native file tools** for
  `.claude/settings.json` and `.claude/hooks/**`, ask rather than deny
  so the guard's own maintenance keeps an unlock path; and an
  **eleven-line `deny` backstop** confined to acts that cannot be undone
  — force, mirror, delete and prune pushes, `filter-branch`,
  `filter-repo`, `reflog expire`, `update-ref -d` and
  `update-ref --stdin` — which binds when the hook is dead. Auto memory
  stays off. A third allow category is named honestly beside the other
  two: `mkdir`, `touch`, `mktemp` are neither registry-bearing nor
  read-only, but they are trivially local writes the loop needs. `chmod`
  was in that group and was **removed**: `chmod -x` on the guard is the
  disarm, so it is gated in the guard and prompts here. Said plainly,
  and recorded in `.claude/docs/guard-record.md`: a broad allow plus a
  dead hook is a **wider** surface than a narrow allow list ever was;
  the backstop covers **canonical spellings only** (prefix rules match
  from the start of the line, so `git push origin main --force` matches
  nothing though the guard denies it — that gap is this project's
  thesis); and it deliberately does not cover destructive deletes, whose
  spellings are an open set a prefix rule cannot enumerate.
- **Alternatives considered:** *A blanket `Bash` allow with the guard as
  the only gate* — maximal convenience, and the maximal version of the
  dead-guard hole; rejected for the same reason wrappers get no broad
  allow. *Keeping the narrow allow list and no guard* — rejected: it is
  what cannot express the spellings that matter, and this repository's
  whole subject is that gap. *`default` (manual) mode* — rejected by the
  operator as a prompt per governance-document edit, on a workflow that
  edits several per step. *`auto` mode as the baseline* — rejected: it
  puts a second, non-deterministic decider beside the guard, and for a
  project whose product *is* a deterministic guard the two disagreeing
  is worse than either alone. *Locking `auto` out as well* — rejected by
  the operator, who wants it available for the `002` comparison.
  *Restating the push gate as a prefix `ask`* — rejected: strictly
  weaker than the guard's rule and a second source of truth. *A `deny`
  on the ordinary push* — rejected outright: rule 6 attempts a push at
  every step close, and a denied pattern cannot be approved in the very
  exchange rule 9 relies on.
- **Approved by:** operator, 2026-08-20, reviewing the baseline and its
  gates as one piece at step `001`'s handover. Three components were
  their own rulings earlier the same day: the permission mode, the
  bypass lock without the auto lock, and the absence of a backup remote.
  A third spelling was wrong and is already corrected: the baseline
  listed a `Write(…)` rule beside each `Edit(…)` one, and **`Write(…)`
  matches nothing** — the file tools are matched by `Edit(…)` rules,
  `Write` included (operator, 2026-08-20). The three dead entries were
  removed; the coverage they were meant to add is what the `Edit(…)`
  rules already gave, so the tier above is unchanged.
- **Verified at `002` (2026-08-20), no change needed.** The two
  spellings this entry left unverified both bind on Claude Code
  `2.1.237`: `Bash(git push --force:*)` matches, so the backstop is not
  decoration, and an explicit `ask` rule beats `acceptEdits` for the
  file tools — measured outside `.claude/`, where a platform behaviour
  would otherwise have masked it. The `Edit(…)`-matches-`Write` mapping
  is confirmed too. So is this entry's accepted cost: `python3` does
  prompt. Neither pre-committed fallback — re-spelling the backstop,
  moving the `ask` tier to `deny` — was needed. Two facts the entry did
  not anticipate are recorded in `.claude/docs/guard-record.md`: the
  `deny` list matches only from the **start** of the command line, so
  `git push origin main --force` matches nothing and only the guard
  catches it; and Claude Code gates **every write under `.claude/`**
  regardless of the rules, which no `allow` entry suppresses.

### D-012 — The boundary is inert exactly where the guard is absent

- **Date:** 2026-08-20
- **Step:** `001` (the permission and hook baseline)
- **Context:** the guard is machine-local and never tracked — this
  repository is the plugin's public install channel, and no later strip
  removes what an initial commit carries. But the settings file that
  registers it *is* committed, and the gates that keep it honest run in
  the same `just check` that CI runs. Nothing committed may reference the
  guard in a way that fails where it is absent: CI and fresh clones never
  have it, this machine always should. The two failures pull in opposite
  directions — a gate that is loud everywhere breaks every clone, and a
  gate that is quiet everywhere misses the silent death it exists to
  catch.
- **Decision:** two mechanisms, both keyed on the same fact. **(1) The
  hook registration is self-guarding**:
  `g="${CLAUDE_PROJECT_DIR:-.}/.claude/hooks/bash_guard.py"; [ -x "$g" ]
  && exec "$g" || exit 0`. `exec` hands the process over, so a present
  guard's stdout and exit code arrive untouched; an absent one exits 0
  in silence, and a clone of the public repository carries a hook that
  costs nothing. Verified in all four combinations (present/absent ×
  variable set/unset). **(2) Both gates key on
  `refs/backups/bash-guard`** — the backup ref the instantiation creates
  — as the marker for "the guard is expected here". It exists on
  machines that instantiated the guard, lives outside `refs/heads/`, and
  is carried by no clone or default refspec. `scripts/check-guard.sh`
  always asserts governance well-formedness — both settings files parse,
  neither disables all hooks nor re-enables auto memory, the effective
  mode is not a permissive one, the bypass lock and a non-empty `deny`
  backstop survive, and a `PreToolUse` hook matching Bash still names the
  guard — and, where the marker is, **executes the registered command
  line** with a force-push payload and requires a `deny` back, which a
  substring test cannot do. `just test` runs `--selftest` under the same
  condition. **Linked worktrees are named explicitly**: the marker lives
  in the shared git directory while the gitignored guard does not, so a
  worktree would otherwise run the tracked allow list with no guard
  behind it — both gates fail there and print the symlink that fixes it.
  Twelve states plus the worktree case were probed rather than assumed
  (`.claude/docs/harness.md`, probe 6).
- **Alternatives considered:** *Keying the gates on the guard file
  itself* — rejected as self-defeating: a deleted guard would make its
  own gate inert, which is precisely the silent death being hunted.
  *A separate machine-local sentinel file* — rejected under rule 11: the
  backup ref already exists exactly where the guard is expected, and a
  second marker is a second thing to keep true. *Putting the hook
  registration in the gitignored `.claude/settings.local.json`* —
  genuinely tempting, since a machine-local fact belongs in a
  machine-local file, and rejected on review: the registration would then
  be unversioned and unreviewable, the operator would review two files
  instead of one diff, and the governance check would have no pointer to
  assert. *Registering the plain path and accepting hook errors in
  clones* — rejected: this repository is a public install channel, and
  shipping a settings file whose hook fails on every Bash call is a
  defect delivered to strangers.
- **Approved by:** implementer (within latitude: a workflow choice the
  bootstrap instructions left open — the harness's shape and names).
  The custom check itself needs no separate sanction: `CLAUDE.md`'s
  harness note already provides for a few-line governance check, no
  ecosystem tool answering either question.

### D-013 — `just` is safe-by-default: our own task runner is not a dangerous tool

- **Date:** 2026-08-20
- **Step:** none (`meta` — amends `D-011`, which is `001`'s)
- **Context:** `D-011` treated `just` as dangerous-by-default on both
  sides of the boundary: in the guard's registry as a **grant** (a
  closed world of six proven spellings, anything else asks), and in
  `.claude/settings.json` as six exact-match allows rather than
  `Bash(just:*)`. The stated reason was that a broad allow on a
  command-runner is a broad allow on everything it runs the moment the
  guard is dead. In use that produced prompts on ordinary work: a
  redirection is enough to leave the proven world, so
  `just check changed 2>&1 | tail -20` asked, as did every spelling the
  list did not literally contain. **An enforcement mechanism that asks
  about routine work is worse than one that does not exist** — it trains
  the operator to approve without reading, which is the failure this
  whole project exists to prevent.
- **Decision:** `just` becomes **safe-by-default on both sides**. In the
  registry it is a rule, not a grant: any recipe, any arguments, any
  redirection is silent, **including a recipe that does not exist yet**,
  and a short set of named flags asks because each one breaks the
  premise that this is *our* justfile run in *our* project — `-f` /
  `--justfile` and `-d` / `--working-directory` (another justfile,
  another directory), `--shell` / `--shell-arg` /
  `--clear-shell-args` (another interpreter), `--chooser` / `--choose`
  (an arbitrary command as chooser), and `--init` / `--fmt` (which
  write a justfile). In the settings the six exact allows become one
  `Bash(just:*)`, because a guard that goes silent while the allow list
  still enumerates spellings simply moves the prompt from the hook to
  the permission rules. `pip` stays a grant: its closed world is about
  packages fetched from a network, which is a real risk and not ours to
  vouch for.
- **What this rests on, named honestly:** `CLAUDE.md` rule 2's invariant
  that **no `just` recipe ever performs an act rule 9 gates**. The guard
  judges the `just` line and can never see inside a recipe, so a recipe
  that pushed or deleted would pass unseen. That invariant is now
  load-bearing rather than merely stated. It is a fair thing to rest on:
  the justfile is tracked, reviewed in the same diffs as everything
  else, and written by us — which is exactly the argument the closed
  world was ignoring.
- **Alternatives considered:** *Teaching the guard's parser to strip
  redirections*, which was the first fix proposed — rejected by the
  operator under rule 11: the guard is scaffolding retired at `PLAN.md`
  `027`, parser work on it is effort spent on the thing frisk replaces,
  and §4.3 already legislates the correct behaviour for the product
  (recorded in `.claude/docs/guard-record.md`). It would also have
  fixed one spelling and left every unlisted recipe asking. *Enumerating
  the four recipes as a rule instead of a grant* — rejected: a seventh
  recipe would prompt on its first use, which is the same defect with a
  longer fuse. *Leaving the settings at six exact allows and changing
  only the guard* — rejected as half a fix, per the decision above.
- **Approved by:** operator, 2026-08-20, who identified the grant as the
  root cause and rejected the premise that a runner whose every task we
  write ourselves is a dangerous tool. `D-011` stands otherwise; only
  its `just` treatment is overturned.

### D-014 — `CLAUDE.md`'s budget re-derived at 400 for a rule that grew

- **Date:** 2026-08-20
- **Step:** — (workflow maintenance, no step)
- **Context:** The workflow doctrine gained U-063, which adds text to
  two of the nine rules `CLAUDE.md` restates: rule 3 must now say what
  a `.claude/docs/` file *is* and name its two disqualifiers, and rule 2
  must say that the operator tests behaviour and never a document.
  `D-002` derived 390 hard / ~365 at handover from an arithmetic whose
  largest term was "the remaining nine rules restated tightly enough
  that a fresh session behaves identically are ~200". Two of those nine
  are now larger, so the floor that arithmetic measured has moved.
  Written tightly, the two additions cost 12 lines against 2 of
  headroom.
- **Decision:** the budget is **400 lines hard, ~375 at handover**,
  replacing `D-002`'s 390/~365. `D-002` stands otherwise: its eviction
  order, its never-leaves list and its two scheduled shrinks are
  unchanged, and both shrinks still apply to the new number — step `004`
  removes the tooling-templates block (−10) and `PLAN.md` `027` removes
  the quarantine text (−29), each re-derived downward on arrival rather
  than kept as slack. The file lands at exactly 400 after a trim pass
  that gave back 3 of the 12 by wording alone. **It therefore has no
  headroom**, and step `003` — which must add a `.claude/docs/` pointer
  for its probe results and update the current-step block — arrives
  needing a compaction pass or a further re-derivation. That is stated
  here rather than discovered there.
- **Alternatives considered:** *Absorbing the 12 lines by compressing
  the `Current state` section* (44 lines, grown across three closes) —
  rejected, though it is the subtractive answer rule 11 prefers: it pays
  for a permanent rule change with live world state, and `003` needs
  that room immediately afterwards, so the compaction would be spent
  twice over. *Leaving the budget at 390 and breaching it* — rejected on
  `D-002`'s own reasoning, that a budget first met by breaching it
  teaches the next session the budget is decorative. *Trimming the two
  new clauses until they fit 390* — rejected: they are the doctrine's
  text, and `D-002` already recorded trimming as the active failure mode
  a fidelity review had to reverse.
- **Approved by:** operator, 2026-08-20, ruling on the workflow-update
  triage.
- **Resolved (2026-08-20, `D-016`):** the deferred compaction was taken
  in the U-065 update pass instead of at `003`. The number is unchanged
  and `D-014` stands; the file now sits at 394, so the "no headroom"
  state recorded above no longer holds and `003` arrives with room.

### D-015 — Doctrine adopted through U-064

- **Date:** 2026-08-20
- **Step:** — (workflow maintenance, no step)
- **Context:** The workflow this repository runs is a restatement of the
  `specify` skill's doctrine, not a copy of it, so nothing propagates
  when that doctrine moves. `D-001` adopted the workflow without naming
  the changelog id it adopted, which left the first update pass no
  choice but to walk every *running* entry from U-022. Of the nineteen
  audited (multi-track entries excluded — this repository is
  single-track), seventeen came back already satisfied, most of them
  because this project *is* the source of the doctrine's 2026-08-19
  revision: U-057 to U-062 were banked from its own handoff review
  rounds. No entry was found to conflict with a logged decision; `D-011`
  and `D-013` both land with the doctrine rather than against it.
- **Decision:** this repository is **adopted through U-064**, and a
  future update pass reads only entries above that id. Two entries were
  behind and are applied in this pass:
  - **U-063** — rule 3 now states what a `.claude/docs/` file is and
    disqualifies justification and duplication; rule 2 now states that
    the operator tests behaviour and never a document; step `003`'s
    operator test becomes a re-run of its two probes instead of a read
    of what they found; and the frozen `optimize-memory` and
    `step-reviewer` templates gain the sweep's fourth question and the
    excess lens's memory-as-a-report clause, so `004` instantiates the
    current doctrine.
  - **U-022** — the `Current state` world-state bullet named two
    permission modes as a standing fact with no version stamp beside
    it. Reworded to the behavioural classification; the names, with the
    version they were measured on, stay in
    `.claude/docs/guard-record.md`. No baseline change follows: `002`
    verified on Claude Code `2.1.237` that the committed
    `permissions.defaultMode` is a name the running version accepts.
  U-064 applies to bootstrap only and a project past `001` is reached
  by U-063's remedy instead, so adopting U-063 covers it; the higher id
  is named so the next pass does not re-open the question.
- **Alternatives considered:** *Recording adoption at U-063,* the
  highest *running* entry — rejected as leaving U-064 permanently
  unresolved in the index for every later pass to re-read. *Carrying
  U-063's template fixes as new bullets in `PLAN.md` `004` instead of
  editing the frozen templates* — rejected: the template is what `004`
  actually copies, a plan bullet is an instruction that can be missed,
  and editing the copies restores byte-identity with the doctrine's
  assets, which `diff -r` verifies in a second. *Applying U-062's
  `description` note as well* — accepted despite the entry being marked
  bootstrap-only, because rule 2 makes both reviews standing gates while
  the templates ship a `description` saying "on request only", and the
  `description` is what decides whether the agent is reached at all.
  *Fixing `README.md`'s growth list, which omits `.claude/skills/` and
  `.claude/agents/`* — deferred, not rejected: rule 6's same-commit
  sweep makes it `003`'s, and `003` is next.
- **Approved by:** operator, 2026-08-20, ruling point by point on the
  audit triage.

### D-016 — Doctrine adopted through U-065, and the budget given headroom

- **Date:** 2026-08-20
- **Step:** — (workflow maintenance, no step)
- **Context:** One *running* entry sat above `D-015`'s adoption point.
  **U-065** attaches rule 3's headroom requirement to the budget itself
  — the baseline, a number derived at the first task, or one re-derived
  later — because that requirement had only ever lived in the
  changelog's *remedy* field, which no project reads. Its detection test
  has two limbs and this repository tripped both: `CLAUDE.md` stood at
  exactly 400 lines against the 400 it states, and `D-014` re-derived to
  a number equal to the file's length. The entry is in fact drawn from
  this repository, quoting both derivations (389 against 390, then 400
  against 400). `D-014` had already recorded the consequence — that
  step `003` arrives owing a compaction pass it did not budget for.
- **Decision:** this repository is **adopted through U-065**. The cap
  stays at **400 lines hard, ~375 at handover**; `D-014`'s number is
  unchanged and the headroom comes from taking the compaction it
  deferred. `CLAUDE.md` goes 400 → 394, and rule 3 now states that every
  budget lands above what the file owes, a re-derivation included, so
  the two shrinks `D-002` schedules (step `004`, −10; `PLAN.md` `027`,
  −29) re-derive downward under the rule rather than to the file's
  length. Seven lines came back under the eviction order's own
  precedence: per-step detail the plan already carries — `002`'s
  measured findings in the world-state bullet, which its plan entry, the
  `step-002` tag message and `.claude/docs/guard-record.md` (probes P1,
  P4, P7) each hold — and the §14 question numbers in the obligations
  bullet, which `PLAN.md` already routes to their steps. Three more came
  from the layout section's `.claude/` inventory, which restated rules 1
  and 3 clause for clause and is now a pointer to them: rule 3's
  duplication disqualifier, applied to this file itself.
- **Alternatives considered:** *Invoking U-065's own escape clause* —
  "a file already at its cap is not re-cut for this alone" — rejected on
  two grounds: the next change that touches the budget is step `003`,
  which begins next, so the deferral buys one commit; and the headroom
  clause cannot reach rule 3 without room, which is the failure U-065
  names. *Raising the cap above 400* — rejected by the operator: it pays
  for headroom with budget rather than with compaction, and `D-002`'s
  reasoning that a budget met by moving it teaches the next session the
  budget is decorative applies to raising it as much as to breaching it.
  *Compacting further to reach ~385, the figure first estimated* —
  rejected: the remaining candidates were the plan-entry shape and the
  `.claude/refs/` inventory, and neither is reachable by a read-trigger
  (U-055 has the close ritual cite the first, and the second *is* its
  own trigger), so the cut would have been a rule trimmed to make room,
  which `D-002` and `D-014` both refused. Six lines is headroom for
  `003`'s pointer, and `004` returns ten.
- **Approved by:** operator, 2026-08-20, ruling to keep the cap at 400
  and take the compaction.

### D-017 — The backup remote is named `backup`

- **Date:** 2026-08-20
- **Step:** `003`
- **Context:** rule 6's step-close push carries rule 1's
  `refs/backups/bash-guard` to the operator's private backup remote, and
  `PLAN.md` `003` requires `/approve-step` to resolve that remote **by
  name** and report its absence rather than fail on a machine that lacks
  it. No such remote exists, so the bootstrap left the name open: a
  ritual cannot resolve by name without one, and inventing it at the
  first close that needs it is how two machines end up with two names.
- **Decision:** the name is **`backup`**. `/approve-step` resolves it
  with `git remote get-url backup` and, on success only, runs
  `git push backup refs/backups/bash-guard`; absence prints a line and
  attempts nothing. The name is recorded in
  `.claude/docs/guard-record.md`, which `CLAUDE.md` rule 1 already names
  as the home for this detail.
- **Alternatives considered:** *`private`* — accurate about the remote's
  character but says nothing about what it is for, and this repository
  will never have a second private remote to distinguish it from.
  *`guard-backup`* — precise, but the ref already says `bash-guard` and
  the push command names both, so the remote would say it a third time.
  *Leaving it open and asking at the first close* — rejected: that is
  the improvisation the plan's "resolve by name" clause exists to
  prevent, and it would land in the one ritual that runs while the
  operator is waiting on a push decision.
- **Approved by:** implementer (within latitude: a workflow choice the
  bootstrap instructions left open, rule 4)

### D-018 — The governance check imports PyYAML from the project venv

- **Date:** 2026-08-20
- **Step:** `003`
- **Context:** `PLAN.md` `003` sanctions a small custom check for
  governance frontmatter. (The clause that stood here — "nothing in the
  ecosystem asks whether a skill or agent definition loads" — was false
  and is struck; `D-021` records what `claude plugin validate` does and
  does not cover.) What actually parses those files is Claude
  Code's YAML parser, so approximating it needs a real YAML parser;
  hand-rolling one over a subset that already includes folded scalars is
  precisely what rule 11 forbids. Every other linter here is a
  pre-commit hook pinned by `rev` in its own isolated environment, and
  `requirements.txt` said so in as many words.
- **Decision:** `scripts/check_frontmatter.py` imports PyYAML, pinned as
  `PyYAML==6.0.3` in `requirements.txt`, and runs on the project
  interpreter (`language: system`, entry `.venv/bin/python …`). `.venv`
  is guaranteed wherever the checks run, since pre-commit itself lives
  there and `scripts/check.sh` invokes `.venv/bin/pre-commit`.
  `requirements.txt`'s "only pre-commit lives here"
  claim is rewritten in the same commit: third-party linters stay
  isolated and pinned by `rev`; what shares this interpreter is the hook
  runner and what our own checks import.
- **Alternatives considered:** *A `language: python` local hook with
  `additional_dependencies`* — the most idiomatic pre-commit answer, and
  a live alternative: it was rejected when `just test` still drove the
  script against fixture roots, and `D-022` removed that suite, so the
  reason is spent. Left as-is rather than churned; revisit if the pin
  ever needs isolating. *System `python3` plus
  system PyYAML*, matching `scripts/check-guard.sh`'s stdlib-only
  heredoc — rejected: it is an unpinned workstation prerequisite that
  happens to hold on this machine and does not hold on a bare CI runner,
  which `005` will discover the hard way. *Embedding the check in
  `check-guard.sh`'s existing heredoc* — same dependency problem, plus
  it welds two unrelated subjects together. *Hand-parsing the
  frontmatter* — rejected by rule 11 outright.
- **Approved by:** implementer (within latitude: a workflow choice the
  bootstrap instructions left open, rule 4)

### D-019 — Python well-formedness joins with the first `.py` file, style waits for `006`

- **Date:** 2026-08-20
- **Step:** `003`
- **Context:** rule 2 requires a check family to arrive **with the first
  artifact of its class, never ahead of it**.
  `scripts/check_frontmatter.py` is this repository's first `.py` file,
  which brings the Python family forward from `PLAN.md` `006`, where
  `.pre-commit-config.yaml` had scheduled it. Pinning a style tool now
  would mean fetching a version that is nowhere in the repository —
  outside rule 9's local boundary — and pre-empting the configuration
  `006` will want for the engine.
- **Decision:** the Python family arrives now as
  **well-formedness only** — `check-ast` and `debug-statements`, both
  from `pre-commit/pre-commit-hooks`, already pinned at `v6.0.0` in this
  file, so no new pin and no fetch. They ask exactly what the rest of
  `just check` asks: does the artifact load, and does it carry anything
  that should never have been committed. **Style and TOML still join at
  `006`** with the engine, where there is a body of code for a style to
  be about; `.pre-commit-config.yaml`'s family comment is updated to say
  so rather than left claiming Python arrives at `006` wholesale.
- **Alternatives considered:** *Adding a full style linter now* —
  requires an unpinned network fetch to learn a valid `rev`, so it is an
  operator question, and it would settle the engine's style
  configuration in a step that ships eighty lines of check script.
  *Shipping the `.py` file with no Python family at all* — a plain rule
  2 breach, and the kind that is never noticed later. *Avoiding the
  `.py` file by embedding the Python in a shell heredoc*, as
  `check-guard.sh` does — considered seriously, since it would have kept
  the family question shut; rejected with `D-018`, which needs a pinned
  import that a heredoc on system `python3` cannot have.
- **Approved by:** implementer (within latitude: a workflow choice the
  bootstrap instructions left open, rule 4)

### D-020 — The agent-name arm of the citation check is deferred to `004`

- **Date:** 2026-08-20
- **Step:** `003`
- **Context:** `PLAN.md` `003` rides two *shoulds* beside the governance
  check's required parse: "an agent name checked against
  `.claude/agents/` and a path checked against the tree", and a section
  pointer checked against the target's headings. The path and heading
  arms shipped. The agent-name arm cannot be green at `003`: rule 2's
  gates live in `/handover-step` and `/approve-step`, which name
  `step-reviewer`, `code-reviewer`, `test-reviewer`, `state-reviewer`
  and `optimize-memory` — five agents `PLAN.md` `004` creates. The plan
  anticipates the forward reference ("resolved there") but the check
  would still go red for a step in between.
- **Decision:** the arm is deferred to `004`, recorded as a deliverable
  in that step's entry rather than as a suppression list here. Both
  rituals carry an explicit until-`004` fallback naming what to do while
  the agents do not exist, so the forward reference cannot read as a
  gate that silently skips — which is the failure the *should* exists to
  catch, addressed in prose in the interim.
- **Alternatives considered:** *An exemption list in
  `scripts/check_frontmatter.py`* naming the five not-yet-adopted
  agents — rejected: a suppression built for one step outlives it, and
  the list would have to be deleted at `004` by the same session that
  would rather leave it. *Adopting the five agents at `003`* — that is
  `004`, and merging them would batch two steps because they look
  related, which rule 2 forbids. *Dropping the arm permanently* —
  rejected: a dangling agent name is exactly the silent-skip the plan
  names, and `004` is where the check can pass on its first run.
- **Approved by:** withdrawn, operator, 2026-08-20 — `D-022` removed the
  citation check entirely, so there is no arm left to defer. Kept
  because ids freeze.

### D-021 — `check_frontmatter.py` beside `claude plugin validate`, not instead of it

- **Date:** 2026-08-20
- **Step:** `003`
- **Context:** rule 11 says to ask whether the ecosystem already ships
  the tool before writing one. That question was not asked before
  `scripts/check_frontmatter.py` was written, and the cold code review
  asked it afterwards. It does ship one: `claude plugin validate
  --strict <dir>` — and the check's own comments had claimed the
  opposite in as many words. It covers about half the parse question,
  and **the half it leaves is the half that fails silently**: a `name`
  disagreeing with its path, a malformation that swallows the closing
  `---`, and a skill directory with no `SKILL.md` all exit 0 — the last
  of these uncovered by our script either. The measurement, its version
  stamp and its re-measure recipe live in `.claude/docs/harness.md`
  (rule 2), not here. Two claims this entry carried at `003` were wrong
  and are corrected there: unparseable YAML exits 1 only while the
  `---` delimiters survive the malformation, and "a skill directory with
  no `SKILL.md` exits 1" was an artifact of an otherwise-empty fixture
  tree, which finds no components at all and falls back to *manifest*
  validation.
- **Decision:** both exist, and neither is folded into the other. The
  script stays as the harness's gate; the validator is **not** wired
  into `.pre-commit-config.yaml` or CI. It is `claude` — the operator's
  live, unpinned CLI — and every other tool in that file is pinned by
  `rev` with an isolated environment, which rule 2 requires of a
  third-party check; wiring it in would make `just check` depend on
  which Claude Code the workstation happens to have, and would put a
  Claude Code install in `005`'s CI to lint five markdown files. The
  false "nothing in the ecosystem asks that question" claim is struck
  from the script's docstring and from `.pre-commit-config.yaml` in the
  same commit; both now name the validator and say what it misses. The
  script's residue that is genuinely its own — name↔path agreement, the
  `name`↔path agreement — is the part rule 11 actually sanctions
  (`D-022` cut the rest).
- **Revisit at `PLAN.md` `021`**, where the plugin tree lands and the
  validator becomes necessary for the *product's* manifest rather than
  optional for dev tooling. If it is pinned and wired then, the
  duplicated parse diagnostics here should go with it. Retiring the
  script wholesale is not on that table: it would surrender three
  silent-failure classes, not one. Re-measure before deciding.
- **Alternatives considered:** *Replacing the script with the
  validator* — loses name↔path agreement, the layout checks and the
  citations, which is most of the value, and buys an unpinned
  dependency. *Keeping both and wiring the validator in as a second
  hook* — the honest maximal answer, rejected on pinning and on CI
  weight, and revisitable at `021`. *Narrowing the script to only what
  the validator misses* — tempting, but it would make `just check` green
  on a skill with no frontmatter at all unless the validator ran too, so
  it only works bundled with the previous option. *Deleting the check
  entirely* — `PLAN.md` `003` requires the family, and the validator is
  not in the harness.
- **Approved by:** operator, 2026-08-21, ruling during the U-066 update
  pass; carried `*pending*` from `003`'s handover. Rule 11 questions
  about whether a thing should exist are theirs, and this one was
  answered by building first.

### D-022 — The governance check is a parse check and nothing more

- **Date:** 2026-08-20
- **Step:** `003`
- **Context:** the check shipped at ~170 lines with a citation resolver,
  fence-aware heading extraction, unicode normalisation, a fixture-root
  argument and an 18-case suite in `just test`. `PLAN.md` `003` had said
  plainly that "a few-line custom check is **sanctioned** by rule 11
  here, **and it is the whole of what the rule requires**", offering the
  citation resolver only as an optional *should*. The operator called
  the result over-built and, decisively, pointed out that `just verify`
  runs `check` **before** `test`: the checker is executed against the
  real tree on every single invocation, so a fixture suite re-proving it
  is a regression harness for process scaffolding nobody will touch
  again.
- **Decision:** the check is cut to the parse question alone —
  frontmatter is present, closed, parses, is a mapping, `name` agrees
  with the path the loader finds it at, `description` is non-empty.
  ~53 lines. `scripts/test.sh` is restored to its pre-`003` shape: the
  guard's selftest, then the note that no product behaviour exists yet.
  Deleted with the suite: the citation resolver and its recognised
  shape, the fenced-code pass, unicode normalisation, the root argument
  and its guards. `D-020` is withdrawn — the arm it deferred no longer
  exists. The rituals keep writing pointers in the `` `path` § "Heading"
  `` form because it reads well, but **nothing checks them**, and no rule
  requires that they do.
- **The reason, so this is not re-litigated:** a check that runs ahead of
  the tests on every invocation does not also need tests. What earns its
  place is the one diagnostic no other tool provides — `name` against
  path, which `claude plugin validate --strict` passes silently
  (`D-021`).
- **Alternatives considered:** *Deleting the checker entirely* — put to
  the operator and declined: `CLAUDE.md` rule 2 mandates the governance
  family "whatever the stack", so removal would need a rule amendment,
  which is a bigger change than the problem. *Keeping the script and
  dropping only the suite* — rejected: the citation resolver was the
  bulk of the complexity and was never asked for, so cutting the tests
  while keeping what made them feel necessary is the wrong half.
- **The process failure, recorded because it is the point:** rule 11
  says to ask whether the ecosystem ships the tool **before** writing
  one, and rule 2 requires a runner we build to be put to the operator
  **before it is built**. Neither happened. `D-021` records the first
  miss; this entry records that the size was never put up for a ruling
  either, and that the instruction capping it was in the plan text being
  read at the time.
- **Approved by:** operator, 2026-08-20, choosing "parse check only, no
  suite" from the three options put to them.

### D-023 — Doctrine adopted through U-066, less one contradicted fact

- **Date:** 2026-08-21
- **Step:** — (workflow maintenance, no step)
- **Context:** one *running* entry sat above `D-016`'s adoption point.
  **U-066** is drawn from this repository's own step `003` — it quotes
  the ~170→~53-line cut and the −442 net as its measurement — so its
  three repairs were mostly already in force here. Its *Detect* limbs
  were walked: no governance check now carries a suite, fixture tree or
  root argument (`D-022`); `scripts/check_frontmatter.py` is 53 lines
  and `D-021` is the entry recording the build-vs-buy question, now
  ruled; and the "nothing in the ecosystem" claim survived in `D-018`'s
  Context after `D-021` struck it from the script and the hook config.
  The remedy's ordered re-measure then contradicted the entry itself.
- **Decision:** this repository is **adopted through U-066**, with three
  repairs applied and one clause declined.
  *Applied:* rule 2 now states that `just verify` runs `check` before
  `test` and draws the consequence — the check half executes against the
  real tree every invocation, so it needs no suite of its own. This was
  the argument that settled `D-022` and no rule stated it (+1 line;
  `CLAUDE.md` 397 → 398, cap unchanged at 400). `D-018`'s false
  ecosystem clause is struck. The validator measurement moves out of
  `D-021` into `.claude/docs/harness.md` with its version, method and
  re-measure recipe, as rule 2 requires of a measured value — being
  logged only in a decision entry is why it went stale unseen.
  *Declined:* U-066's parenthetical that the validator "passes silently
  … on frontmatter that does not parse, which it skips without a word".
  Measured on 2.1.238: unparseable YAML with the `---` delimiters intact
  exits **1** with an explicit error. The claim holds only for the
  narrower case where the malformation swallows the closing delimiter.
  Adopted in the corrected form recorded in `harness.md`.
- **Alternatives considered:** *Taking U-066's parenthetical as written*
  — rejected on measurement; the update pass applies under this
  project's rules, and rule 2's "probe every enforcement mechanism"
  outranks an unmeasured restatement, which is the class `D-021` already
  exists to correct. *Deferring rule 2's line to `004`'s compaction* —
  the budget had room for one line and the clause is the load-bearing
  half of U-066; deferring a rule to buy a line the file already had is
  the decorative-budget failure `D-002` names. *A new entry superseding
  `D-021` rather than amending it* — rejected: the decision there is
  unchanged and comes out better founded, and this log reserves new
  entries for reversals. Its wrong *facts* were corrected in place.
- **Upstream:** U-066 needs a dated correction-in-place note, and
  `D-021`'s own missing-`SKILL.md` claim was an artifact of an
  otherwise-empty fixture tree falling back to manifest validation —
  reported to the operator, whose call it is to touch the skill.
- **Approved by:** operator, 2026-08-21, approving the U-066 triage and
  the `D-021` amendment.
