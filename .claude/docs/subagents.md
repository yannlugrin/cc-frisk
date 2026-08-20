# Subagents and skills — the measured record

**Read before writing or changing anything under `.claude/agents/` or
`.claude/skills/`, and before relying on a subagent to know a rule.**

Measured on **Claude Code 2.1.237**, 2026-08-20, step `003`. Every claim
here is a live measurement with its recipe. Documentation is not a
measurement: the published docs agreed with two of these and were silent
on the rest, and the probes are what this repository stands on.

## What a subagent's context carries

**`CLAUDE.md` reaches a subagent — both the built-in kinds and a
project-defined one.** Measured twice: a built-in `general-purpose`
agent, and the project-defined `probe-tools-restricted`. Each was
forbidden every tool and asked for three things that exist only in
`CLAUDE.md`; each returned rule 9's opening line verbatim and rule 11 as
"Proportion".

**But the copy it carries is the parent session's, not the file on
disk.** Both agents reported the current-step pointer as `none` — the
value when this session started. The project-defined one was spawned two
commits after that pointer had become `003`, and still said `none`.

*Consequences.* An agent may cite a rule by number and rely on it being
readable. It may **not** be trusted on anything volatile — the
current-step pointer above all — which must be passed in its prompt or
read from disk with `Read`. And it has no `PLAN.md`, `DECISIONS.md` or
`SPECIFICATIONS.md`: an agent that needs those reads them, so its
`tools:` list must include `Read`.

*Re-measure.* Repeat with both agent kinds; change the third question to
whatever the current-step pointer now says, and edit `CLAUDE.md` between
the edit and the spawn to re-test staleness.

## Skill and agent frontmatter

| Key | Where | What it does |
|---|---|---|
| `name`, `description` | both | required. `name` must match the directory (`skills/<name>/SKILL.md`) or the filename (`agents/<name>.md`), or the definition that loads is not the one you edited. |
| `tools:` on an agent | agents | **restricts — measured.** A controlled pair, identical but for this line: `tools: Read` had no Bash tool at all ("no such tool in my tool list"), `tools: Read, Bash` ran the command. The pair is the measurement; one failing arm cannot tell a restriction from a refusal. Omitting the key inherits the parent's full set. |
| `allowed-tools:` on a skill | skills | **restricts nothing — measured.** Under `allowed-tools: Read`, both a `Bash` call and a `Write` ran. This reproduces on 2.1.237 what the handoff phase found on 2.1.231. |
| `disallowed-tools:` on a skill | skills | not used, not probed. Reported to bind the whole invoking turn and never prompt — too blunt for a ritual, and a mechanism that strips a tool from the operator's own turn is worse than prose. |

So: **an agent's `tools:` is a real boundary and may be relied on; a
skill's frontmatter is not.** A ritual's read-only discipline stays
prose plus `.claude/settings.json` plus the guard hook. Keep instantiated
skill frontmatter to `name` and `description`: a key that binds nothing
reads as a guarantee.

*Re-measure.* Spawn `probe-tools-restricted` against `probe-tools-open`
with the same prompt and compare; invoke `/probe-frontmatter`. All three
fixtures are deleted at `PLAN.md` `004`.

## When a definition loads

**Not immediately, but within the session — no restart needed.** A file
written to `.claude/agents/` was still absent minutes later (spawning it
returned `Agent type not found`, the error enumerating only what existed
at session start), then became available later in that same session
without any restart. The rescan interval was not measured.

*Consequence.* A step that writes a skill or an agent cannot verify it
on demand, but need not hand over with a restart in its test
instructions either: the honest instruction is that a new definition
appears after a delay, and a restart forces it. Do not build a ritual
that depends on picking one up promptly.

*Re-measure.* Write a throwaway agent file, spawn it at once, then again
after other work; the two results are the answer.

## What cannot be measured from inside a session

A permission prompt that the session's mode auto-answers is
indistinguishable from no prompt at all — `002` established this and it
binds here too. During the skill probe a `Write` under `.claude/`
completed with no visible prompt, which is **not** evidence that
`CLAUDE.md`'s "every write under `.claude/` prompts" has stopped
holding. Anything about prompting is measured the way
`.claude/docs/guard-record.md` § "Method" prescribes, or not at all.

## The citation shape

`scripts/check_frontmatter.py` resolves one shape in skills and agents:

    `<path>` § "<Heading text>"

path against the tree, heading against the target's headings. Use it for
every pointer a ritual carries; anything else is prose and is not
checked. The script's docstring carries the rest.
