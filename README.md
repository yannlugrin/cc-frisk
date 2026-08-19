# cc-frisk

This repository holds the specification and the in-progress
implementation of **frisk**: an open-source Claude Code plugin that
guards the Bash tool by parsing the command lines an agent proposes.

frisk resolves quoting, splits compound commands, walks through wrappers
(`sudo`, `env`, `timeout`, …), shells invoked with `-c`, `eval`, command
substitutions and container handoffs, then judges every command position
it finds. That lets it express verdicts Claude Code's native permission
rules cannot: "a force push however it is spelled", "this deploy tool is
safe only when a parse-only flag is present", or the force-push hidden
inside `git commit -m "$(git push -f)"`. It is three things in one
plugin — a generic **engine**, a per-project **configuration** owned by
the project, and a maintenance **skill** that turns every surprising
verdict into a precise rule plus a reproducing test case.

frisk parses and judges. It never executes commands, never touches the
network, and never edits its own rules — rules change only through the
operator.

**Status: pre-implementation.** Nothing here is installable yet.
`PLAN.md` is the authority on where the work stands.

## The files

| File | What it is |
|---|---|
| `SPECIFICATIONS.md` | The complete specification: goal, environment constraints, core model, engine behaviour, configuration, verdicts, failure handling, testing, CLI, skill, packaging, documentation deliverables, release path, future considerations and non-goals. |
| `DECISIONS.md` | The decision log — every choice made during implementation, with its context, alternatives and who approved it. |
| `PLAN.md` | The implementation plan: milestones and steps, each with its objective, the specification sections it implements, its deliverables and how they are tested. Also the §13 re-inventory, the open-fact ledger, the specification coverage map, the external prerequisites and the open questions. |
| `CLAUDE.md` | Standing instructions for the implementing AI. Directive, and addressed to it alone — not a description of the project. |
| `justfile`, `scripts/` | The documented entry points: `just setup`, `just check [all\|changed]`, `just test`, `just verify`. The scripts are thin glue; the checks themselves are configured, not written. |
| `.pre-commit-config.yaml`, `requirements.txt`, `.yamllint.yml`, `.pymarkdown.json` | The pinned toolchain and its configuration. The same checks run from the commit hook and from `just check`, so the two cannot disagree. |
| `.claude/refs/` | Material supplied by the project owner as input: the adjudicated behavior corpus (the parity yardstick of §8.1) and house harness conventions. Read-only; its authority lives at its source. |
| `.claude/spec-work/` | The specification phase's own working history. Not part of the product. |

Directories that appear as the implementation proceeds — `src/frisk/`,
`tests/`, `hooks/`, `skills/frisk/`, `.claude-plugin/`, `collections/`,
`docs/`, `.github/workflows/` — are described in `PLAN.md` at the step
that creates them.

To build and check the repository: `just setup`, then `just verify`.

## Authority order

When two documents disagree, the earlier one in this list wins:

1. **`SPECIFICATIONS.md`** — what must be built. It is read-only for the
   implementing AI and changes only by an explicit, logged amendment.
2. **`DECISIONS.md`** — what was decided along the way, including every
   amendment to the specification and every deviation from one of its
   recommended defaults.
3. **`PLAN.md`** — how and in what order it gets built.
4. **The code** — the current state of the work.

A discrepancy in that direction is a defect in the lower document. A
discrepancy the other way — code doing something no document describes —
is a defect in the code.

## For reviewers

If you are reviewing this repository, human or AI, this is the frame:

- **The specification's reading rules apply.** It states requirements as
  "must", recommended defaults as "should", and environment constraints
  as facts. Code contradicting a **must** is a defect.
- **A deviation from a *should* without a `DECISIONS.md` entry is a
  finding.** With an entry, it is a judgement to assess on its reasoning
  — not automatically wrong.
- **Check anything missing against `PLAN.md`'s current step before
  flagging it.** Most of the specification is deliberately not built
  yet; §13 stages the work and the plan places each item.
- **Each plan step lists the specification sections it implements. That
  list is the review checklist for that step.** The exception is the
  final milestone, whose entries are deliberately coarse until the work
  before them lands (`DECISIONS.md`, `D-008`).
- **A problem in the specification itself is a question for the project
  owner, never a change to propose.** The same holds for anything in
  `.claude/refs/`, which is supplied material, not this repository's
  product.

The specification's own §12 names the documentation the finished product
owes — a README, an operator configuration reference, an honesty
document, a platform verification record, `SECURITY.md` and
`CONTRIBUTING.md`. None of them exists yet; this file is the repository's
entry point until they do.

## License

MIT (§11). The license file lands with the first public release.
