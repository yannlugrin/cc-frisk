---
name: orient
description: Session-start orientation — run before touching anything, at
  the start of a normal session, after /clear, or when the operator asks
  where we are. Establishes the current step, the last approved state and
  the work in progress, then reports and stops.
---

**When to use.** At the start of a normal session, after `/clear`, or
when the operator asks where we are. After an interruption (a usage
limit, a crash, a killed console), or when the last session's claims are
in doubt, `/resume-step` is the right ritual, not this.

**Read-only.** This ritual reads and reports; it edits nothing, commits
nothing, and runs no command that changes the repository or the world.

**Frontmatter carries `name` and `description` only, deliberately.** What
a frontmatter tool list does and does not bind is recorded once, in
`.claude/docs/subagents.md` § "Skill and agent frontmatter"; re-read it
before adding a key here. What actually binds this ritual's read-only
discipline is the prose above, `.claude/settings.json` and the guard
hook.

Execute the session-start routine from CLAUDE.md, in order:

1. Read `CLAUDE.md` in full, `PLAN.md`'s current step (the pointer is in
   CLAUDE.md's "Current state"), and the tail of `DECISIONS.md`.
2. Read the `SPECIFICATIONS.md` sections the current step lists under
   **Spec sections**. Where it lists none, say so rather than skipping
   silently.
3. Locate the last approved state — match the step namespace only, never
   the latest tag of any kind:
   `git describe --tags --abbrev=0 --match 'step-*'`
   Before the first step tag exists, the range is the whole history.
4. Review the work in progress: `git log` and `git diff` from that tag
   (or root) to `HEAD`, plus `git status` for uncommitted work.
5. Anomaly check: if what you gathered does not add up — a dirty tree the
   step's status does not explain, a `PLAN.md` status the diff
   contradicts, a stale `CLAUDE.md` pointer — do not deliver the normal
   report: report the anomaly and recommend `/resume-step`, then stop.
   This skill detects; it does not diagnose.
6. Report to the operator: current step and status, what the in-progress
   diff contains, and what remains — then stop and wait for
   instructions. Touch nothing before reporting.
