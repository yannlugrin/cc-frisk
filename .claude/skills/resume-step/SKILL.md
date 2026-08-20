---
name: resume-step
description: Post-interruption verification — run after work ended
  abnormally (a usage limit, a crash, a reboot, a killed console) or
  whenever the operator doubts what the last session claims to have done.
  Distrusts the transcript, verifies the claimed state against the
  repository and the world, then reports discrepancies and repair
  options. Verifies and reports only; it never repairs.
---

Work was interrupted or the last session's claims are in doubt. Your job
is to establish what is actually true, then stop.

**When to use.** Instead of `/orient` — it embeds the same orientation —
after an abnormal end, or whenever the operator doubts the last session's
account. Prefer invoking it from a fresh session, which cannot be tempted
to trust the old transcript.

**Frontmatter carries `name` and `description` only, deliberately.** What
a frontmatter tool list does and does not bind is recorded once, in
`.claude/docs/subagents.md` § "Skill and agent frontmatter"; re-read it
before adding a key here. What actually binds this ritual's verify-only
discipline is the prose below, `.claude/settings.json` and the guard
hook.

**Doctrine: the transcript is a claim, not evidence.** What the
conversation — or its summary, or your own memory of it — says was
completed is exactly what an interruption falsifies: the narrative was
written before the interrupt, the state after. Evidence is the repository
and the world; every claim is checked against them.

In order:

1. **Anchor on approved truth.** The last annotated step tag is the last
   operator-approved state:
   `git describe --tags --abbrev=0 --match 'step-*'`
   (before the first tag, the anchor is the repository root).
   `git log` and `git diff` from there to `HEAD`, plus `git status`, are
   the complete evidence of everything since — committed and
   uncommitted.
2. **Read what `/orient` reads, then cross-check it.** This ritual
   replaces `/orient`, so it performs the same session-start reading, not
   a narrower one: `CLAUDE.md` in full, `PLAN.md`, `DECISIONS.md` and the
   `SPECIFICATIONS.md` sections the current step names — the whole
   routine CLAUDE.md's session-start rule states, in its own words. Do
   not substitute a shorter list; CLAUDE.md routes a resumed session here
   *before touching anything*, so a ritual that reads less is how a
   session ends up working from no specification at all — and this is the
   ritual that runs when the state is least trustworthy.

   Then check each claim in those files against the git evidence. They
   were written by the same interrupted session, so a mismatch is a
   finding, never something to reconcile silently — a status of `awaiting
   test` over a half-delivered diff is precisely what you are looking
   for.
3. **Working-tree forensics.** Examine uncommitted changes for
   half-written work (a file edited where its counterpart was not, a
   reference to something that does not exist yet). Run `just check`:
   green is cheap evidence the tree is at least well-formed; red
   localizes the interruption.
4. **World state, inside the boundary.** The step may have touched things
   no file records — consult the current step's "How the operator tests
   it" and its cleanup note in `PLAN.md` for what it may have
   half-applied. Run the free checks:

   | Command | What it establishes |
   |---|---|
   | `just test` | the shipped behaviour still passes, guard `--selftest` included |
   | `git remote -v` | which remotes exist — `origin`, and whether a backup remote does |
   | `git show-ref refs/backups/bash-guard` | the guard's backup ref, the marker the two gates key on |
   | `ls -l .claude/hooks/bash_guard.py` | the guard is materialized and executable — **never read its contents** (CLAUDE.md rule 1) |
   | `.claude/hooks/bash_guard.py --liveness` | its registry builds; output is verdicts, not code |
   | `ls -l .venv/bin/pre-commit .git/hooks/pre-commit` | the toolchain and the commit hook are installed (`just setup` is idempotent if not) |
   | `git status --porcelain --untracked-files=all` | untracked leftovers a step may have scattered |

   **Gated — request from the operator, never run:** the second and third
   commands of the liveness triple in `.claude/docs/guard-record.md` §
   "The liveness triple — for the `003` rituals", and any push. Anything
   unverifiable from here you report as unverified — an honest gap beats
   a guessed answer.
5. **Report, then stop — two shapes:**
   - **Discrepancies found:** the resume point and its evidence; each
     discrepancy as the claim plus the contradicting evidence; what could
     not be verified; and the repair options — continue the step from the
     verified state, roll back to the last `step-*` tag, or redo the
     partial work — with your recommendation. The repair is the
     operator's ruling; you execute nothing until they choose.
   - **Everything consistent:** deliver `/orient`'s report — current step
     and status, what the in-progress diff contains, what remains — plus
     one line: verification found no discrepancies, and what was checked.
     Then wait for the operator's go.
