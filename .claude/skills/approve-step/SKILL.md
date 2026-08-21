---
name: approve-step
description: Post-approval close of the current step — run only when the
  operator has declared the step approved in this exchange, after their
  manual testing. Sets status `done`, compacts the entry to its outcome,
  puts the annotated step tag on the close commit, and attempts the push
  so the permission gate puts the publish decision to the operator.
---

**When to use.** Only after the operator has declared the step approved
in this exchange, following their own manual test. The pre-test handover
is `/handover-step`, not this.

**Frontmatter carries `name` and `description` only, deliberately.** What
a frontmatter tool list does and does not bind is recorded once, in
`.claude/docs/subagents.md` § "Skill and agent frontmatter"; re-read it
before adding a key here.

Close the approved step. The precondition is the operator's explicit
approval in this exchange; if their message leaves any doubt, ask — never
treat this skill's invocation context as the approval itself.

In order:

1. **Confirm scope:** the step being closed is the one in `awaiting
   test`; its number has been frozen since it entered `in progress`.
2. **Compact the step entry — replace it, do not annotate it.** The entry
   described a plan; the step is now history, so everything that was a
   plan goes: objective, spec sections, deliverables, how the operator
   tests it. What remains is the heading marked `done` and a single
   outcome bullet. **The shape is stated in `CLAUDE.md` § "Plan
   conventions"** — read it there and follow it; do not transcribe it
   here, because a ritual carrying its own copy is the copy that goes
   stale. If that section ever stops carrying the shape, fix this
   citation rather than improvising one.

   What this ritual legitimately adds is only what matters while
   performing a close: write the bullet as the tag message's opening
   paragraph condensed (step 4 writes that message in the same
   commit-and-tag pass), so the two cannot disagree. Deleting the plan
   text is the point — an approved step's deliverable list keeps
   asserting intentions the step itself changed, in the file every
   session reads at start.
3. **Close commit:** in one commit — that compacted entry with its status
   `done`; `CLAUDE.md`'s "Current state" pointed at the next step **and
   the closed step's paragraph deleted, not demoted**: its outcome is in
   the entry and the tag this same commit writes, a durable fact belongs
   in `.claude/docs/`, an obligation in `PLAN.md`, an invariant in
   `DECISIONS.md`. A third copy in `CLAUDE.md` is how that section
   becomes a changelog — measured once at 131 lines, a paragraph at a
   time, each defensible on its own. Anything else the approval made
   stale goes in too. Run `just check` — the full form, never `just check
   changed`: this commit receives the step tag and is the state every
   later session treats as known-good.
   Subject: `step-NNN: close — approved, status done, entry compacted`.
4. **Annotated tag** `step-NNN` on that commit. **The tag-message shape
   is stated in `CLAUDE.md` § "Plan conventions"** — read it there. It is
   fixed in the ground rules precisely so the closes that happen before
   this ritual exists do not improvise it. Do not source it from
   `git tag -n99 -l 'step-*'`: the earliest tags were written before this
   ritual existed, so reading the shape off them makes whatever they
   improvised the standard. That command is the cross-check, never the
   carrier.
5. **Milestone boundary:** if this was the milestone's last step, do not
   start the next one — suggest the whole-state review (`state-reviewer`)
   and then the memory-compaction pass (`optimize-memory`), in that
   order, so the compaction runs after the review has read the
   uncompacted memory.

   **Spawn both on a model that did not write the milestone's work.**
   Normally that is any model other than yours — but a milestone spans
   many steps and may span models, so the one to exclude is whichever
   implemented, not merely your own. Pass the override explicitly at
   invocation: neither agent pins a model, and omitting the override does
   not mean "no opinion", it means they inherit yours, which is the one
   outcome to avoid. If no second model is available, say so when
   reporting the passes rather than presenting them as independent. This
   applies to these two passes only — `/handover-step`'s reviews buy a
   cold context, which any model gives, and may run on yours.
   When the passes edit the memory files, review their edits and land
   them as a `meta:` commit **before step 6** — or discard them, saying
   so in the report. The ritual must not end with an uncommitted tree it
   never mentions: step 6's push would otherwise publish the close while
   the compaction waits, unpublished, for the next close.
6. **Report, then attempt the push.** Show the step summary and what the
   close commit and tag contain — with `CLAUDE.md`'s line count and its
   change since the last close, so growth is visible at the moment it
   happens and in front of the operator. **Over the handover figure —
   not only over the hard cap** — present **both** remedies and let them
   rule: what could move out, and raising the figure. The cap is the
   breach; the handover figure is the one that says the next step
   arrives without room, and a prompt that waits for the cap fires only
   once there is nothing left to decide. Never resolve it by compressing
   something that cannot be compressed without loss — the number is a
   signal, and a gate here would make deletion the cheapest way to go
   green.

   Then, as **two separate tool calls, never chained**:

   ```sh
   git push --follow-tags
   ```

   ```sh
   git push origin refs/backups/bash-guard:refs/heads/backup/bash-guard
   ```

   `--follow-tags` carries the annotated tag with the commit, where a
   bare `git push` leaves the step tag behind, and a tag that exists only
   locally is invisible to everything reading the remote. The second call
   carries the quarantined guard's backup ref (`CLAUDE.md` rule 1) to
   `origin`'s `backup/bash-guard` branch — `D-028` reversed `D-017`'s
   private remote, and the operator accepted that this publishes the
   prototype's source. The local ref keeps its name and its place outside
   `refs/heads/`, which is what the gates key on.
   `.claude/docs/guard-record.md` § "Restore, and the backup ref" carries
   the reasoning.

   **Separate calls, because a chain defeats the gate.** `002` measured
   that settings-level prefix rules match only from the start of the
   command line, so a `git push` buried after `&&` is invisible to the
   platform gate and reaches the guard alone.

   **This is a named exception to rule 9's "never on your own
   initiative", and it does not generalise.** It holds here because the
   operator has just approved the step, the only open question is whether
   this closed state should be published now, and the permission gate
   answers exactly that question at exactly that moment — better than an
   offer they have to remember to answer. It does *not* license
   attempting any other gated act on the grounds that something
   downstream will catch it: everywhere else the guard is a backstop,
   never a substitute for asking. It rests on the push being gated
   here — `.claude/docs/guard-record.md` § "The liveness triple — for the
   `003` rituals" records that measurement. If a close ever pushes with
   no prompt, stop and report it: the exception has lost its footing and
   the ritual goes back to asking in prose.

   **A refusal is final.** If either push is declined or denied, say so,
   leave the commit and its tag local, and stop — no retry, no narrower
   spelling, no pushing the branch without the tag. Either way the next
   step starts only on the operator's go.
