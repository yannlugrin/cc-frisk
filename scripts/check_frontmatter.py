#!/usr/bin/env python3
"""Governance well-formedness: every skill and agent definition loads.

CLAUDE.md rule 2 puts this family on the list whatever the stack, because
a malformed skill does not fail — it silently never loads, and a ritual
nobody can invoke looks exactly like one nobody needed.

Claude Code's own `claude plugin validate --strict` is the better tool
where it applies, but it is the operator's unpinned live CLI and several
failure classes pass it silently — a `name` disagreeing with its path
among them, which leaves you editing one definition while another loads
(`D-021`). What each tool catches is measured in `.claude/docs/harness.md`
§ "What `claude plugin validate` covers, and what it misses"; the count
lives there and nowhere else, having already drifted once. Hence a few
lines, and no more than that.
"""

import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pinned in requirements.txt; `just setup` installs it
    sys.exit("governance: PyYAML is missing — run 'just setup' first")

ROOT = Path(__file__).resolve().parent.parent
problems = []

# An exact `---` line closes the block. Matching the delimiter by prefix
# would accept `----`, which parses here and closes nothing for a loader
# that wants the exact line — a definition that silently never loads,
# which is what this file exists to catch. What the loader really accepts
# is unmeasured (`claude plugin validate` passes `----`, and it passes
# four other malformations too), so the guess is placed on the loud side.
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---(?:\n|\Z)", re.DOTALL)


def check(path, expected_name):
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        problems.append("%s: cannot be read as UTF-8: %s" % (path, exc))
        return
    block = FRONTMATTER.match(text)
    if block is None:
        problems.append(
            "%s: no frontmatter fenced by exact `---` lines" % path
        )
        return
    try:
        meta = yaml.safe_load(block.group(1))
    except yaml.YAMLError as exc:
        problems.append("%s: frontmatter does not parse: %s" % (path, exc))
        return
    if not isinstance(meta, dict):
        problems.append("%s: frontmatter is not a mapping" % path)
        return
    if meta.get("name") != expected_name:
        problems.append("%s: declares name %r but loads as %r" % (path, meta.get("name"), expected_name))
    description = meta.get("description")
    if not isinstance(description, str) or not description.strip():
        problems.append("%s: no description — it is what routes invocations" % path)


for pattern, name_of in (("skills/*/SKILL.md", lambda p: p.parent.name),
                         ("agents/*.md", lambda p: p.stem)):
    found = sorted((ROOT / ".claude").glob(pattern))
    if not found:
        # A moved or renamed directory would otherwise exit 0 having
        # checked nothing — the silent non-loading this file exists to
        # catch, one level up.
        problems.append(".claude/%s: matches nothing — has the tree moved?" % pattern)
    for entry in found:
        check(entry, name_of(entry))

for problem in problems:
    print("governance: %s" % problem.replace(str(ROOT) + "/", ""), file=sys.stderr)
sys.exit(1 if problems else 0)
