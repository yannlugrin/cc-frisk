#!/usr/bin/env python3
"""Governance well-formedness: every skill and agent definition loads.

A malformed skill does not fail — it silently never loads, and a ritual
nobody can invoke looks exactly like a ritual nobody needed.

**The ecosystem does ask most of this question.** Claude Code ships
`claude plugin validate --strict <dir>`, which on 2.1.237 catches a
missing frontmatter block, frontmatter that does not parse, a missing
description and a skill directory with no SKILL.md, and reports
unrecognized fields besides. What it does **not** catch, measured
against the same fixtures, is a `name` that disagrees with the path the
loader finds the file at — which is the failure that leaves you editing
one definition while another loads. That, the layout checks, and the
citation resolution below are what this script adds; it is not a
substitute for the validator and does not try to be. `D-021` records
why both exist and which one is authoritative.

Two checks, both hard failures — there is no warning tier here:

  1. Every definition parses. Delimited YAML frontmatter, a mapping,
     `name` and `description` present, and `name` agreeing with its
     path.

  2. One recognised citation shape resolves:

         `<path>` § "<Heading text>"

     the path against the tree, the heading against that file's actual
     headings. Instantiated skills and agents only: they are the class
     of pointer a session follows without re-reading the target, so a
     heading rename leaves ritual files quietly citing nothing.

Prose is deliberately **not** scanned for backticked tokens. That check
has been built and regretted: a false-positive machine that grows worse
as the repository does, and unremovable once a rule mandates it.
"""

import re
import sys
import unicodedata
from pathlib import Path

try:
    import yaml
except ImportError:  # pinned in requirements.txt; `just setup` installs it
    sys.exit("governance: PyYAML is missing — run 'just setup' first")

# The tree to judge. Defaults to this repository; `just test` passes a
# fixture tree instead, which is the only way to exercise the cases that
# must fail without committing malformed governance files.
ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".claude/skills"
AGENTS = ROOT / ".claude/agents"

# `<path>.md` § "<Heading text>" — the one shape. Applied to whitespace
# normalized text, so a citation may wrap across lines.
CITATION = re.compile(r"`([^`]+\.md)`\s*§\s*\"([^\"]+)\"")
# ATX headings, up to three leading spaces (CommonMark). The closing run
# is only a closing run when whitespace precedes it, so `## C#` keeps its
# `#`. Setext headings are not recognised; pymarkdown's md003 keeps this
# repository on ATX, and a citation to a setext heading would read as a
# missing heading rather than pass wrongly.
HEADING = re.compile(r"^ {0,3}#{1,6}\s+(.+?)(?:\s+#+)?\s*$")
FENCE = re.compile(r"^ {0,3}(```+|~~~+)")

problems = []
_headings_cache = {}


def note(path, message):
    problems.append("%s: %s" % (path.relative_to(ROOT), message))


def norm(text):
    """The one normaliser. Both sides of every comparison go through it."""
    return unicodedata.normalize("NFC", " ".join(text.split()))


def read(path, blamed):
    """Text, or None with the problem recorded against `blamed`."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, ValueError) as exc:
        note(blamed, "cannot read %s: %s" % (path.relative_to(ROOT), exc))
        return None


def unfenced(text):
    """The lines outside fenced code blocks.

    Both halves of the citation check need this. Without it `headings()`
    registers every `# comment` in a shell block as a heading — this
    repository's own harness.md has four — so a citation to a phantom
    heading resolves green, which is the exact failure the shape exists
    to catch. And the citation scan flattens fences into prose, so a
    ritual that documents the shape inside a code block has its own
    example resolved against the tree.
    """
    kept, fence = [], None
    for line in text.splitlines():
        opener = FENCE.match(line)
        if fence is None:
            if opener:
                fence = opener.group(1)[0]
                continue
            kept.append(line)
        elif opener and opener.group(1)[0] == fence:
            fence = None
    return kept


def headings(path, blamed):
    key = str(path)
    if key not in _headings_cache:
        text = read(path, blamed)
        found = set()
        if text is not None:
            for line in unfenced(text):
                match = HEADING.match(line)
                if match:
                    found.add(norm(match.group(1)))
        _headings_cache[key] = found
    return _headings_cache[key]


def check_citations(path, body):
    for target, title in CITATION.findall(norm("\n".join(unfenced(body)))):
        # `ROOT / target` silently discards ROOT when target is absolute,
        # and never rejects `..`. Both would let a governance file steer
        # the check at files outside the tree, so `just check` would stop
        # being a function of this repository.
        resolved = (ROOT / target).resolve()
        if not resolved.is_relative_to(ROOT) or not resolved.is_file():
            note(path, "cites `%s`, which is not a file in this tree" % target)
            continue
        if norm(title) not in headings(resolved, path):
            note(path, 'cites `%s` § "%s", which is not a heading there' % (target, title))


def check(path, expected_name):
    text = read(path, path)
    if text is None:
        return
    if not text.startswith("---\n"):
        note(path, "no frontmatter — the file must open with a `---` line")
        return
    end = text.find("\n---", 3)
    if end == -1:
        note(path, "frontmatter is never closed by a `---` line")
        return
    try:
        meta = yaml.safe_load(text[4:end])
    except yaml.YAMLError as exc:
        note(path, "frontmatter does not parse as YAML: %s" % exc)
        return
    if not isinstance(meta, dict):
        note(path, "frontmatter is not a mapping")
        return

    name = meta.get("name")
    if not isinstance(name, str) or not name.strip():
        note(path, "frontmatter has no usable `name`")
    elif name != expected_name:
        note(path, "declares name `%s` but loads as `%s`" % (name, expected_name))
    description = meta.get("description")
    if not isinstance(description, str) or not description.strip():
        note(path, "frontmatter has no usable `description` — it is what routes invocations")
    check_citations(path, text[end + 4 :])


def main():
    if not ROOT.is_dir():
        sys.exit("governance: %s is not a directory" % ROOT)
    if len(sys.argv) == 1 and not (SKILLS.is_dir() or AGENTS.is_dir()):
        # A green run over a tree with neither directory says nothing at
        # all. Against a fixture root that is the caller's business; here
        # it means the layout moved and this check went quietly inert,
        # which is the failure class it exists to catch, one level up.
        sys.exit("governance: neither %s nor %s exists" % (SKILLS, AGENTS))

    if SKILLS.is_dir():
        for entry in sorted(SKILLS.iterdir()):
            if entry.name.startswith("."):
                continue
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
            if entry.name.startswith("."):
                continue
            if entry.is_dir():
                note(entry, "an agent lives at `.claude/agents/<name>.md`; a directory here never loads")
            elif entry.suffix == ".md":
                check(entry, entry.stem)
            elif entry.is_file():
                note(entry, "an agent must be a `.md` file; this one never loads")

    if problems:
        for problem in problems:
            print("governance: %s" % problem, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
