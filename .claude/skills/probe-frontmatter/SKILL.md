---
name: probe-frontmatter
description: Measurement fixture for step 003 — does a skill's
  `allowed-tools` frontmatter restrict anything in the version we run?
  Not a working ritual; delete it at step 004 once the answer is
  recorded.
allowed-tools: Read
---

You are performing a measurement, not a task. Accuracy beats
helpfulness, and "the tool is not available to me" is the useful answer.

This file's frontmatter declares `allowed-tools: Read`. If that key
restricts anything, the two attempts below must fail. Do not skip an
attempt because you expect it to fail — the absence of the attempt is
not a measurement.

1. Attempt `ls .claude/skills` through the **Bash** tool. Report
   `BASH RAN: <output>`, `BASH UNAVAILABLE: not in my tool list`, or
   `BASH BLOCKED: <the literal error or prompt text>`.
2. Attempt to create the file `.claude/probe-frontmatter-touched` through
   the **Write** tool, with the single line `probe`. Report `WRITE RAN`,
   `WRITE UNAVAILABLE: not in my tool list`, or `WRITE BLOCKED: <the
   literal error or prompt text>`.
3. If step 2 created the file, delete it and say so.
4. State the version: `claude --version` if Bash was available,
   otherwise say the version is unknown from inside the probe.

Record the outcome in `.claude/docs/subagents.md` § "Skill and agent
frontmatter", replacing whatever that section currently says is
unmeasured, and note the Claude Code version it was measured on.
