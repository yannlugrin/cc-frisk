# Subagents and skills — the measured record

**Read before writing or changing anything under `.claude/agents/` or
`.claude/skills/`, and before relying on a subagent to know a rule.**

Measured on **Claude Code 2.1.237** unless a line says otherwise. Every
claim here is either a live measurement with its recipe, or is labelled
*unmeasured* and treated at its stricter branch. Documentation is not a
measurement: where the published docs and a probe disagree, the probe
wins and the disagreement is recorded.

## Does CLAUDE.md reach a subagent?

**Yes — measured, 2026-08-20, step `003`.** A subagent's context carries
this repository's `CLAUDE.md` before its first turn.

*Method.* Spawn a `general-purpose` subagent on a different model, with
a prompt forbidding every tool and asking for three things that exist
only in `CLAUDE.md`: the opening line of rule 9 verbatim, the number of
the rule beginning "Proportion", and the three-digit current-step
pointer. It answered all three correctly and reported using no tools.
Three answers, not one, because a single plausible guess proves nothing;
the current-step pointer in particular changes every step, so a correct
answer cannot come from training data.

*Consequence.* `PLAN.md` `003`'s pre-committed unfavourable branch —
inlining the gated set into every agent body — **does not apply**. An
agent may cite a rule by number and rely on it being readable. It may
not rely on `PLAN.md`, `DECISIONS.md` or `SPECIFICATIONS.md`, which are
not auto-loaded: an agent that needs those reads them, and its `tools:`
list must then include `Read`.

*Re-measure.* Repeat the method above; change the third question to
whatever the current-step pointer now says.

## Skill and agent frontmatter

Keep instantiated skill frontmatter to `name` and `description`. Agent
frontmatter adds `tools`. Nothing else is used here, and a key this
version does not define buys nothing while its handling is unspecified.

| Key | Where | Status |
|---|---|---|
| `name`, `description` | skills and agents | required; `name` must match the directory (`skills/<name>/SKILL.md`) or the filename (`agents/<name>.md`), or the definition is not the one that loads |
| `tools:` on an agent | agents | **unmeasured here.** Documented as a strict allowlist — only listed tools are available, and omitting the key inherits the parent's full set. The probe is built and restart-gated (below). |
| `allowed-tools:` on a skill | skills | **unmeasured here.** The handoff phase probed it on 2.1.231 and found it restricted nothing. The probe is built and restart-gated (below). |
| `disallowed-tools:` on a skill | skills | not used, not probed. Reported to bind the whole invoking turn and never prompt — too blunt for a ritual, and a mechanism that removes a tool from the operator's own turn is worse than prose. |

*Stricter branch, in force until those two probes report.* **No
frontmatter tool list is treated as an enforcement boundary.** A
read-only ritual's discipline is prose plus `.claude/settings.json` plus
the guard hook; a reviewer agent that must not write is one whose body
says so. If the probes come back restrictive, a tool list becomes a
second, cheap layer — never the first one.

*Re-measure — both probes, after a restart.* See the fixtures below.
For the agent arm: spawn `probe-tools-restricted` (frontmatter `tools:
Read`) and `probe-tools-open` (frontmatter `tools: Read, Bash`) with the
same prompt, and compare. The pair is the measurement — a single failing
arm cannot distinguish a restriction from a refusal. For the skill arm:
invoke `/probe-frontmatter` and read what it reports.

## When a definition loads

**Session start only — measured, 2026-08-20, step `003`.** A subagent
definition written to `.claude/agents/` mid-session is not picked up:
spawning it returns `Agent type '<name>' not found`, and the error
enumerates only the agents that existed when the session began.

*Consequence.* Any step that creates or renames a skill or an agent
hands over with a restart in its test instructions, and cannot itself
verify the thing it just wrote. Assume the same for `.claude/skills/`.

*Re-measure.* Write a throwaway agent file and spawn it in the same
session; the error message is the result.

## The probe fixtures

Three files exist only to be measured against, and **step `004` deletes
all three** once their answers are recorded above:

- `.claude/agents/probe-tools-restricted.md` — `tools: Read`
- `.claude/agents/probe-tools-open.md` — `tools: Read, Bash` (the
  control arm)
- `.claude/skills/probe-frontmatter/SKILL.md` — `allowed-tools: Read`

They are tracked, so they publish with the repository, and they appear
in every session's agent and skill lists until they go. That is the cost
of measuring rather than assuming; it is paid for one step.

## The governance check

`scripts/check_frontmatter.py` asserts what this file assumes: every
definition parses, carries `name` and `description`, and agrees with its
own path. It also resolves one recognised citation shape —

    `<path>` § "<Heading text>"

— against the target file's headings, in instantiated skills and agents
only. A pointer nobody follows is how four ritual files come to cite a
section that no longer exists. **Prose is never scanned for backticked
tokens**: that check has been built and regretted elsewhere, and once a
rule mandates it, it cannot be deleted without amending the rule.
