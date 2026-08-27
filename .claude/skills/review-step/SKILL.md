---
name: review-step
description: File-by-file operator review of the current step — run when
  the operator wants to walk the step's work one file at a time, giving
  feedback, discussing it, and validating each change before the next
  file. Works on a code step and on a step whose product is a document.
  It holds the ledger of which files are validated; it never approves
  the step.
---

**When to use.** When the operator says they want to review the step
file by file — after `/handover-step` has put it in `awaiting test`, at
a test gate, or as the final read of a step whose product is a
document. It is neither of the surrounding rituals: `/handover-step`
hands the step over, `/approve-step` closes it. This is what happens in
between, at the operator's pace.

**Frontmatter carries `name` and `description` only, deliberately.**
What a frontmatter tool list does and does not bind is recorded once, in
`.claude/docs/subagents.md` § "Skill and agent frontmatter"; re-read it
before adding a key here — in particular before assuming a tool list
would enforce step 2's do-nothing rule. It would not. What binds that
rule is the prose below.

## The shape

**One cycle per file**, or per small batch of files, and the operator
picks which. Do not propose an order unless asked; do not run ahead.

1. **The operator gives feedback** on that file.
2. **Discuss and plan — change nothing.** Answer, disagree where you
   disagree, say how you would apply each point and what it would
   reach. No edits, no writes, no commits: reads and conversation only.
   This is the rule the whole ritual rests on, and "it was obviously
   right" is not an exception to it. A point you would apply
   differently is raised now, not resolved unilaterally later.
3. **The operator says they have finished** with that file. That is the
   only signal that opens step 4 — not a lull, not an apparent
   agreement, not the last point being answered.
4. **Implement everything agreed, in full**, wherever it reaches. **Do
   not commit.**
5. **Verify, then stop and wait** for the operator to validate the
   changes. Rule 2's hand-nothing-over-unverified applies: run the
   checks that apply to what you changed before asking. Which regime is
   in force matters — see below.
6. **On validation, commit.** Small, coherent, `step-NNN:` subjects, as
   rule 6 requires; the staleness sweep applies to these commits like
   any other. Never push. Then mark the file validated and restate the
   ledger.
7. **Next file** — back to 1, until the operator says the review is
   finished.

## The ledger

Track every file the step touched and where it stands. Four states:
`not reviewed`, `under review`, `awaiting validation`, `validated`.

The list is `git diff --name-only <last step tag>..HEAD` plus anything
uncommitted — the same range `/handover-step`'s reviews read. Present it
at the start, restate it at every step 6, and state it whenever asked.

**Write it to the session scratchpad** as well, one line per file, and
update it at each state change. A ledger held only in the conversation
is lost to a context compaction mid-review, and the operator would have
to remember what they had validated. If the ledger is gone anyway — a
new session, a resumed one — **ask the operator what they had
validated**; never infer it from the commit history, which cannot show
a file validated with no change.

Two consequences worth stating out loud when they arise:

- A change agreed while reviewing file X may have to touch file Y. Make
  it, and say so — but Y is **not** thereby reviewed. It keeps its turn.
- If later feedback contradicts something already committed for an
  earlier file, say so plainly and let the operator decide. Never
  silently reopen a validated file.

## Two regimes

The step is in one of them, and step 5 verifies differently in each.
Say which one is in force when the review opens.

- **At a test gate** (the cases are written, the implementation is
  not): `just check` green, `just test` **red** on the new cases and
  nothing else. A change that makes the suite green here has
  implemented something, which is not what this gate is for.
- **After the implementation**: `just verify` green — both halves.

Either way, `/handover-step`'s review agents have already run over the
step's diff. This ritual does not re-run them per file; if the
operator's feedback reopens something large enough to want a cold pass,
say so and let them decide.

## What this ritual is not

**Validating a file is not approving the step.** Approval is a separate
act: the operator confirms they are done with the whole review, and
only then does `/approve-step` run. A step is never closed from inside
this loop, and a file marked `validated` carries no status of its own
into `PLAN.md`.

**The frozen-case rule still holds** (`CLAUDE.md` rule 2). Where the
operator's feedback would change an approved case, a decision entry or
the specification, it is a change made explicitly — with its
`DECISIONS.md` entry, and for the specification the amendment commit
rule 1 prescribes — never an edit that quietly makes something pass.

**Rule 9's boundary is unchanged.** Nothing here licenses a push, a
release, or any other gated act; step 6 commits locally and stops.
