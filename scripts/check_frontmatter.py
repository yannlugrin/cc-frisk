#!/usr/bin/env python3
"""Governance well-formedness: every skill and agent definition loads.

CLAUDE.md rule 2 puts this family on the list whatever the stack, because
a malformed skill does not fail — it silently never loads, and a ritual
nobody can invoke looks exactly like one nobody needed.

Claude Code's own `claude plugin validate --strict` covers most of it and
is the better tool where it applies, but it is the operator's unpinned
live CLI and it misses the one failure that matters most here: a `name`
disagreeing with its path, which leaves you editing one definition while
another loads (`D-021`). Hence a few lines, and no more than that.
"""

import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pinned in requirements.txt; `just setup` installs it
    sys.exit("governance: PyYAML is missing — run 'just setup' first")

ROOT = Path(__file__).resolve().parent.parent
problems = []


def check(path, expected_name):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n") or (end := text.find("\n---", 3)) == -1:
        problems.append("%s: frontmatter missing or never closed" % path)
        return
    try:
        meta = yaml.safe_load(text[4:end])
    except yaml.YAMLError as exc:
        problems.append("%s: frontmatter does not parse: %s" % (path, exc))
        return
    if not isinstance(meta, dict):
        problems.append("%s: frontmatter is not a mapping" % path)
        return
    if meta.get("name") != expected_name:
        problems.append("%s: declares name %r but loads as %r" % (path, meta.get("name"), expected_name))
    if not str(meta.get("description", "")).strip():
        problems.append("%s: no description — it is what routes invocations" % path)


for entry in sorted((ROOT / ".claude/skills").glob("*/SKILL.md")):
    check(entry, entry.parent.name)
for entry in sorted((ROOT / ".claude/agents").glob("*.md")):
    check(entry, entry.stem)

for problem in problems:
    print("governance: %s" % problem.replace(str(ROOT) + "/", ""), file=sys.stderr)
sys.exit(1 if problems else 0)
