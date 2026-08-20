---
name: handover-step
description: Pre-test handover sequence — run when the current step's
  implementation is complete and ready for operator testing, or when the
  operator asks for the handover. Checks, staleness sweep, review, then
  hand the step to the operator.
---

**When to use.** When the step is implemented and ready for the
operator's manual test, or when they ask for the handover. The
post-approval close is `/approve-step`, not this.

**Frontmatter carries `name` and `description` only, deliberately.** What
a frontmatter tool list does and does not bind is recorded once, in
`.claude/docs/subagents.md` § "Skill and agent frontmatter"; re-read it
before adding a key here — in particular before assuming a tool list
would be safe, since step 3 spawns subagents and a missing entry would
make those reviews silently not happen.

Hand the current step over for operator testing. In order:

1. **Checks green:** run `just verify` (CLAUDE.md rule 2: the check and
   the test halves both pass); fix until it does. If the step added
   artifacts the harness should cover, confirm it actually covers them —
   a check that never ran is not green.
2. **Staleness sweep (rule 6's same-commit rule):** update, in the same
   commit(s) as the work, everything the step made stale — `PLAN.md` step
   status (to `awaiting test`) and any renumber references, `CLAUDE.md`'s
   current-step pointer, `.claude/docs/` pointers and file references,
   `README.md`'s file map, `docs/` deliverables, `DECISIONS.md` entries,
   and any `.claude/docs/` lesson worth keeping for future sessions.
3. **Review — the standing gates.** All of these read the step's diff
   (last `step-*` tag → `HEAD`), which shows committed work only, so the
   step's work and the sweep must be in commits before any of them runs.
   Address or explicitly rebut every finding before handover; anything
   touching a decision or the specification goes to the operator rather
   than being resolved here.

   | Pass | Runs when | Agent |
   |---|---|---|
   | Plan-and-spec conformance | every step | `step-reviewer` |
   | Cold code review — security, performance, code quality | the step changed code | `code-reviewer` |
   | Test review | the step changed the suite | `test-reviewer` |

   The three standing foci of the code review are fixed by rule 2:
   **security** (permission-path code; the §5.1/§15 trust model must not
   weaken), **performance** (§4.5's per-call latency budget), and **code
   quality**. While the `bash_guard.py` quarantine lives, that file is
   out of scope for every pass — its vendored code is exempt and its
   `REGISTRY`/`CASES` edits are reviewed inside the isolated-subagent
   channel, outcomes only, in a report that says so.

   *Until step `004` adopts these three agents*, run each applicable pass
   as a freshly briefed subagent from a clean context and say in the
   handover that it ran that way. Delete this paragraph at `004`.
4. **Tree clean:** everything above — the step's work, the sweep, the
   review fixes — is already in small, coherent commits with `step-NNN:`
   subjects (committed as the work happened, not batched here);
   `git status` shows nothing pending. No catch-all closing commit. Never
   push.
5. **Handover message:** (a) short summary of what the step did;
   (b) precise manual test instructions — exact commands and what the
   operator should observe, including cost and cleanup if the test
   crosses rule 9's boundary; (c) state that you are waiting for the
   operator's verdict. The operator tests behaviour, never a document: a
   file belongs in these instructions only when it *is* the deliverable.
   Do not begin the next step.
