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
        problems.append(f"{path}: cannot be read as UTF-8: {exc}")
        return
    block = FRONTMATTER.match(text)
    if block is None:
        problems.append(f"{path}: no frontmatter fenced by exact `---` lines")
        return
    try:
        meta = yaml.safe_load(block.group(1))
    except yaml.YAMLError as exc:
        problems.append(f"{path}: frontmatter does not parse: {exc}")
        return
    if not isinstance(meta, dict):
        problems.append(f"{path}: frontmatter is not a mapping")
        return
    if meta.get("name") != expected_name:
        problems.append(
            f"{path}: declares name {meta.get('name')!r} "
            f"but loads as {expected_name!r}"
        )
    description = meta.get("description")
    if not isinstance(description, str) or not description.strip():
        problems.append(
            f"{path}: no description — it is what routes invocations"
        )


for pattern, name_of in (
    ("skills/*/SKILL.md", lambda p: p.parent.name),
    ("agents/*.md", lambda p: p.stem),
):
    found = sorted((ROOT / ".claude").glob(pattern))
    if not found:
        # A moved or renamed directory would otherwise exit 0 having
        # checked nothing — the silent non-loading this file exists to
        # catch, one level up.
        problems.append(
            f".claude/{pattern}: matches nothing — has the tree moved?"
        )
    for entry in found:
        check(entry, name_of(entry))

for problem in problems:
    trimmed = problem.replace(str(ROOT) + "/", "")
    print(f"governance: {trimmed}", file=sys.stderr)
sys.exit(1 if problems else 0)
