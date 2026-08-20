#!/usr/bin/env bash
# Is the implementation right?
#
# Fixtures and expectations proving the behaviour this repository itself
# ships — the cases that must fail included. A third-party tool is never
# retested here: that shellcheck reports SC2086 is its maintainers'
# problem, not this repository's.
#
# The governance fixtures below are literal Markdown, and Markdown is
# full of backticks. shellcheck reads a backtick inside single quotes as
# a command substitution the author forgot to enable (SC2016, info), so
# it fires on every fixture line and on every expected-message fragment.
# Here they are literal on purpose. Disabled file-wide rather than eight
# times over: nothing in this file wants expansion inside single quotes.
# shellcheck disable=SC2016

set -euo pipefail

cd "$(dirname "$0")/.."

# The development guard's own selftest: liveness, then every case, then
# coverage — a rule or grant no case reaches fails it, which is what
# keeps the registry's intent executable rather than remembered.
#
# Skipped where the guard is absent, keyed on the backup ref rather than
# on the guard file, for the reasons scripts/check-guard.sh sets out: the
# guard is machine-local and never tracked (CLAUDE.md rule 1), and a
# gate keyed on the file it guards goes inert exactly when the file
# disappears.
GUARD=.claude/hooks/bash_guard.py
MARKER=refs/backups/bash-guard

if git rev-parse --verify -q "$MARKER" >/dev/null 2>&1; then
    if [ ! -x "$GUARD" ]; then
        echo "test: $MARKER exists but $GUARD is missing or not executable." >&2
        echo "test: restore it — .claude/docs/guard-record.md carries the recipe." >&2
        exit 1
    fi
    echo "test: the development guard's selftest"
    "$GUARD" --selftest
else
    echo "test: no $MARKER here — the development guard is absent by design (skipped)."
fi

# The governance frontmatter check (PLAN.md 003). It is the first
# behaviour this repository ships beyond the guard, and the cases that
# must fail are the point: a check that cannot go red is a check that
# proves nothing, and this one guards a failure mode — a definition that
# silently never loads — which is invisible from inside a session.
#
# Fixtures are built in a temp tree rather than committed, because
# committing malformed governance files would make the repository's own
# `just check` permanently red.
echo "test: the governance frontmatter check"

CHECK="scripts/check_frontmatter.py"
PYTHON=.venv/bin/python

# Without this, every case below reports "wanted exit 0, got 127" and the
# real cause — no venv — is buried under nine failures. scripts/check.sh
# says the same thing in the same words.
if [ ! -x "$PYTHON" ]; then
    echo "test: toolchain missing — run 'just setup' first." >&2
    exit 1
fi
fixtures=$(mktemp -d)
trap 'rm -rf "$fixtures"' EXIT

cases_run=0
failures=0

# expect <want-exit> <case-name> <fixture-root> [<message fragment>]
#
# The fragment is not decoration. An expected exit 1 is satisfied by any
# failure at all — a typo in the fixture, an import error, a check that
# rejects everything — so a red case proves nothing until it names which
# complaint it wanted. Every must-fail case here carries one.
expect() {
    want=$1
    name=$2
    root=$3
    want_says=${4:-}
    cases_run=$((cases_run + 1))
    set +e
    out=$("$PYTHON" "$CHECK" "$root" 2>&1)
    got=$?
    set -e
    if [ "$got" != "$want" ]; then
        echo "test: FAIL $name — wanted exit $want, got $got" >&2
        printf '%s\n' "$out" >&2
        failures=$((failures + 1))
        return
    fi
    if [ -n "$want_says" ] && ! printf '%s' "$out" | grep -qF -- "$want_says"; then
        echo "test: FAIL $name — exited $got but never said '$want_says'" >&2
        printf '%s\n' "$out" >&2
        failures=$((failures + 1))
    fi
}

# A fixture root with one skill and one agent, written by the caller.
new_root() {
    root="$fixtures/$1"
    mkdir -p "$root/.claude/skills" "$root/.claude/agents"
    printf '%s' "$root"
}

# 1 — the green case: a well-formed skill and agent, and a citation that
# resolves across a line break, which is how they are actually written.
root=$(new_root green)
mkdir -p "$root/.claude/skills/ritual" "$root/.claude/docs"
printf -- '---\nname: ritual\ndescription: does a thing\n---\n\nSee `.claude/docs/note.md` §\n"A heading here" for why.\n' \
    > "$root/.claude/skills/ritual/SKILL.md"
printf -- '---\nname: helper\ndescription: >-\n  a folded scalar, because the agents use one\ntools: Read, Bash\n---\n\nbody\n' \
    > "$root/.claude/agents/helper.md"
printf -- '# Note\n\n## A heading here\n\ntext\n' > "$root/.claude/docs/note.md"
expect 0 "well-formed skill and agent, wrapped citation resolves" "$root"

# 2 — no frontmatter at all.
root=$(new_root no-frontmatter)
mkdir -p "$root/.claude/skills/ritual"
printf -- 'name: ritual\n\nbody\n' > "$root/.claude/skills/ritual/SKILL.md"
expect 1 "frontmatter missing" "$root" "no frontmatter"

# 3 — frontmatter that does not parse as YAML.
root=$(new_root bad-yaml)
mkdir -p "$root/.claude/skills/ritual"
printf -- '---\nname: ritual\ndescription: "unterminated\n---\n\nbody\n' > "$root/.claude/skills/ritual/SKILL.md"
expect 1 "frontmatter does not parse" "$root" "does not parse as YAML"

# 4 — the name disagrees with the path, so the definition that loads is
# not the one that was edited.
root=$(new_root name-mismatch)
mkdir -p "$root/.claude/skills/ritual"
printf -- '---\nname: rituel\ndescription: does a thing\n---\n\nbody\n' > "$root/.claude/skills/ritual/SKILL.md"
expect 1 "skill name disagrees with its directory" "$root" 'declares name `rituel` but loads as `ritual`'

# 5 — no description: the field that routes invocations.
root=$(new_root no-description)
mkdir -p "$root/.claude/agents"
printf -- '---\nname: helper\ntools: Read\n---\n\nbody\n' > "$root/.claude/agents/helper.md"
expect 1 "agent has no description" "$root" 'no usable `description`'

# 6 — a loose file where a skill directory belongs; it never loads.
root=$(new_root loose-skill)
printf -- '---\nname: ritual\ndescription: does a thing\n---\n\nbody\n' > "$root/.claude/skills/ritual.md"
expect 1 "skill written as a loose file" "$root" "a loose file here never loads"

# 7 — a citation whose target file does not exist.
root=$(new_root dangling-path)
mkdir -p "$root/.claude/skills/ritual"
printf -- '---\nname: ritual\ndescription: does a thing\n---\n\nSee `.claude/docs/gone.md` § "A heading here".\n' \
    > "$root/.claude/skills/ritual/SKILL.md"
expect 1 "citation to a file that does not exist" "$root" 'cites `.claude/docs/gone.md`, which is not a file'

# 8 — the file exists, the heading was renamed. This is the drift the
# shape exists to catch, and the only one a reader would not notice.
root=$(new_root dangling-heading)
mkdir -p "$root/.claude/skills/ritual" "$root/.claude/docs"
printf -- '---\nname: ritual\ndescription: does a thing\n---\n\nSee `.claude/docs/note.md` § "A heading here".\n' \
    > "$root/.claude/skills/ritual/SKILL.md"
printf -- '# Note\n\n## Renamed since\n\ntext\n' > "$root/.claude/docs/note.md"
expect 1 "citation to a heading that was renamed" "$root" "which is not a heading there"

# 9 — prose is not scanned. A backticked path in ordinary prose, with no
# citation shape around it, must not be resolved: that check has been
# built and regretted, and this case is what keeps it from creeping back.
root=$(new_root prose-untouched)
mkdir -p "$root/.claude/skills/ritual"
printf -- '---\nname: ritual\ndescription: does a thing\n---\n\nThe plan lives in `PLAN.md`, and `.claude/docs/gone.md` is not real.\n' \
    > "$root/.claude/skills/ritual/SKILL.md"
expect 0 "backticked prose is not resolved" "$root"

# 10 — frontmatter opened and never closed.
root=$(new_root unclosed)
mkdir -p "$root/.claude/skills/ritual"
printf -- '---\nname: ritual\ndescription: does a thing\n\nbody\n' > "$root/.claude/skills/ritual/SKILL.md"
expect 1 "frontmatter never closed" "$root" "never closed"

# 11 — frontmatter that parses but is not a mapping.
root=$(new_root not-a-mapping)
mkdir -p "$root/.claude/skills/ritual"
printf -- '---\n- a\n- b\n---\n\nbody\n' > "$root/.claude/skills/ritual/SKILL.md"
expect 1 "frontmatter is a sequence, not a mapping" "$root" "not a mapping"

# 12 — a skill directory with no SKILL.md. Named in
# .pre-commit-config.yaml as the concrete absence that justifies
# always_run: true, so it owes a case more than most.
root=$(new_root empty-skill-dir)
mkdir -p "$root/.claude/skills/ritual"
expect 1 "skill directory with no SKILL.md" "$root" "no SKILL.md"

# 13 — a directory where an agent file belongs.
root=$(new_root agent-as-dir)
mkdir -p "$root/.claude/agents/helper"
expect 1 "agent written as a directory" "$root" "never loads"

# 14 — an agent file with the wrong extension: it never loads and, until
# this case, was never reported either.
root=$(new_root agent-wrong-suffix)
printf -- '---\nname: helper\ndescription: does a thing\n---\n\nbody\n' > "$root/.claude/agents/helper.markdown"
expect 1 "agent with a non-.md suffix" "$root" 'must be a `.md` file'

# 15 — a citation may not steer the check outside the tree. `ROOT / p`
# discards ROOT for an absolute p, and `..` climbs; this repository
# builds a permission guard, so that idiom does not get to live here.
root=$(new_root citation-escape)
mkdir -p "$root/.claude/skills/ritual"
# The target must *exist*, or is_file() rejects it for the wrong reason
# and the case passes with the containment check deleted. It sits one
# level above the fixture root, reachable only by climbing out.
printf -- '# Outside\n\n## Reachable only by climbing out\n' > "$fixtures/outside.md"
printf -- '---\nname: ritual\ndescription: does a thing\n---\n\nSee `../outside.md` § "Reachable only by climbing out".\n' \
    > "$root/.claude/skills/ritual/SKILL.md"
expect 1 "citation climbing out of the tree" "$root" "not a file in this tree"

# 16 — a heading that only exists inside a fenced code block is not a
# heading. This repository's own harness.md has four such lines, so
# without the fence pass a citation to a phantom resolves green.
root=$(new_root fenced-heading)
mkdir -p "$root/.claude/skills/ritual" "$root/.claude/docs"
printf -- '---\nname: ritual\ndescription: does a thing\n---\n\nSee `.claude/docs/note.md` § "1 — not a heading".\n' \
    > "$root/.claude/skills/ritual/SKILL.md"
printf -- '# Note\n\n```sh\n# 1 — not a heading\n```\n' > "$root/.claude/docs/note.md"
expect 1 "heading inside a fence is not a heading" "$root" "not a heading there"

# 17 — and the converse: a citation shape *inside* a fence is an example,
# not a citation. The 004 agents will document this convention.
root=$(new_root fenced-citation)
mkdir -p "$root/.claude/skills/ritual"
printf -- '---\nname: ritual\ndescription: does a thing\n---\n\nThe shape is:\n\n```\n`docs/example.md` § "Some Heading"\n```\n' \
    > "$root/.claude/skills/ritual/SKILL.md"
expect 0 "citation shape inside a fence is an example" "$root"

# 18 — a root that does not exist must not pass. Without this the two
# green cases above would be satisfied by a fixture tree that failed to
# materialise, which is the same silent-inertness the check exists for.
expect 1 "nonexistent root" "$fixtures/never-created" "is not a directory"

if [ "$failures" != 0 ]; then
    echo "test: $failures of $cases_run governance cases failed" >&2
    exit 1
fi
echo "test: $cases_run/$cases_run governance frontmatter cases passed"

# Beyond the guard and that check, this repository ships no behaviour of
# its own yet: the engine and its suites join at the steps that create
# them (PLAN.md 006 onward).
