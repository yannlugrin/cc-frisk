#!/usr/bin/env python3
"""Governance well-formedness: every skill and agent definition loads.

A malformed skill does not fail — it silently never loads, and a ritual
nobody can invoke looks exactly like a ritual nobody needed. Nothing in
the ecosystem asks that question, so this is CLAUDE.md rule 11's
sanctioned exception: a small check, and the whole of what rule 2's
governance family requires.

Two questions:

  1. **Must** — every definition parses. Delimited YAML frontmatter, a
     mapping, `name` and `description` present, and `name` agreeing with
     the path the loader finds it at. A `name` that disagrees means the
     definition that loads is not the one you edited.

  2. **Should** — one recognised citation shape resolves:

         `<path>` § "<Heading text>"

     the path against the tree, the heading against that file's actual
     headings. Instantiated skills and agents only: they are the class
     of pointer a session follows without re-reading the target, so a
     heading rename leaves four ritual files quietly citing nothing.

Prose is deliberately **not** scanned for backticked tokens. That check
has been built and regretted: a false-positive machine that grows worse
as the repository does, and unremovable once a rule mandates it.
"""

import re
import sys
from pathlib import Path

import yaml

# The tree to judge. Defaults to this repository; `just test` passes a
# fixture tree instead, which is the only way to exercise the cases that
# must fail without committing malformed governance files.
ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".claude/skills"
AGENTS = ROOT / ".claude/agents"

# `<path>.md` § "<Heading text>" — the one shape. Applied to whitespace
# normalized text, so a citation may wrap across lines.
CITATION = re.compile(r"`([^`]+\.md)`\s*§\s*\"([^\"]+)\"")
HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*#*$")

problems = []


def note(path, message):
    problems.append("%s: %s" % (path.relative_to(ROOT), message))


def frontmatter(path, text):
    """The parsed mapping, or None with the problem already recorded."""
    if not text.startswith("---\n"):
        note(path, "no frontmatter — the file must open with a `---` line")
        return None
    end = text.find("\n---", 3)
    if end == -1:
        note(path, "frontmatter is never closed by a `---` line")
        return None
    try:
        loaded = yaml.safe_load(text[4:end])
    except yaml.YAMLError as exc:
        note(path, "frontmatter does not parse as YAML: %s" % exc)
        return None
    if not isinstance(loaded, dict):
        note(path, "frontmatter is not a mapping")
        return None
    return loaded


def headings(path):
    found = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = HEADING.match(line)
        if match:
            found.add(" ".join(match.group(1).split()))
    return found


def check_citations(path, body):
    for target, title in CITATION.findall(" ".join(body.split())):
        resolved = ROOT / target
        if not resolved.is_file():
            note(path, "cites `%s`, which is not a file" % target)
            continue
        if " ".join(title.split()) not in headings(resolved):
            note(path, 'cites `%s` § "%s", which is not a heading there' % (target, title))


def check(path, expected_name):
    text = path.read_text(encoding="utf-8")
    meta = frontmatter(path, text)
    if meta is None:
        return
    name = meta.get("name")
    if not isinstance(name, str) or not name.strip():
        note(path, "frontmatter has no usable `name`")
    elif name != expected_name:
        note(path, "declares name `%s` but loads as `%s`" % (name, expected_name))
    description = meta.get("description")
    if not isinstance(description, str) or not description.strip():
        note(path, "frontmatter has no usable `description` — it is what routes invocations")
    check_citations(path, text[text.find("\n---", 3) + 4 :])


if SKILLS.is_dir():
    for entry in sorted(SKILLS.iterdir()):
        if entry.is_file():
            note(entry, "a skill lives at `<name>/SKILL.md`; a loose file here never loads")
        elif entry.is_dir():
            skill = entry / "SKILL.md"
            if skill.is_file():
                check(skill, entry.name)
            else:
                note(entry, "skill directory with no SKILL.md")

if AGENTS.is_dir():
    for entry in sorted(AGENTS.iterdir()):
        if entry.is_file() and entry.suffix == ".md":
            check(entry, entry.stem)
        elif entry.is_dir():
            note(entry, "an agent lives at `.claude/agents/<name>.md`; a directory here never loads")

if problems:
    for problem in problems:
        print("governance: %s" % problem, file=sys.stderr)
    sys.exit(1)
