"""Context B — the corpus's engine-behavior policy, as declarations.

Three deliberately artificial tools, whose shapes exist to exercise the
engine rather than to describe any real program:

* **stubtool** (alias `stub2`) — gated, default ask, with the whole
  vocabulary on it: a closed world of accounted flags, accounted
  assignments, five grants across three matcher families, rules that
  outrank grants, and two handoffs.
* **stubcli** — gated with a **deny** default, granted by a read-verb
  operand and denied by a write-verb one.
* **stubalways** — no rules, no grants, default deny: every use is the
  operator's.

Transcribed from `.claude/refs/behavior-corpus.md`'s "Context B"
section, flag for flag. The exact sets matter: several rulings turn on
`-i` being value-taking, on `--mode` being accounted, and on the
`validates?` pattern being anchored and dot-escaped.
"""

from __future__ import annotations

from frisk.declare import (
    accounted,
    any_flag,
    any_of,
    ask,
    at_least_one_operand,
    bare,
    deny,
    env,
    every_operand,
    flag,
    grant,
    handoff,
    matching,
    one_of,
    path_matching,
    path_under,
    takes_value,
    tool,
)

#: Anchored and dot-escaped: an unanchored reading would wrongly pass
#: `validates.yaml.bak`.
VALIDATES = r"^(?:.*/)?validates?\.ya?ml$"

READ_VERBS = r"^(list|show|catalog)$"
WRITE_VERBS = r"^(create|delete|set)$"


def declare() -> None:
    """Declare context B into the collection the caller has open."""
    tool(
        "stubtool",
        aliases=["stub2"],
        default=ask(
            reason=(
                "stubtool changes infrastructure unless the run is "
                "proven to be a local question."
            )
        ),
        flags=[
            bare("--syntax-check", "--list-tasks"),
            takes_value("-i", "--inventory", "--tags", "--limit", "--mode"),
        ],
        assignments=[accounted("STUB_QUIET"), accounted("STUB_TARGET")],
        grants=[
            grant(
                when=any_flag("--syntax-check", "--list-tasks"),
                reason="A local question: nothing is applied.",
            ),
            grant(
                when=every_operand(matching(VALIDATES)),
                reason="Validation playbooks only.",
            ),
            grant(
                "clean",
                when=every_operand(path_under("/tmp", ".scratch")),
                reason="Cleaning scratch space.",
            ),
            grant(
                "apply",
                when=flag("--mode", one_of("dry-run", "check")),
                reason="A dry run applies nothing.",
            ),
            grant(
                "apply",
                when=env(
                    "STUB_TARGET",
                    any_of(
                        path_under("/tmp"),
                        path_under("/home/*/scratch"),
                        path_matching(r"^/mnt/\w+/build$"),
                    ),
                ),
                reason="A scratch target is not production.",
            ),
        ],
        rules=[
            ask(
                "wipe",
                reason="Wiping destroys state that may not be rebuilt.",
                label="wipe asks",
            ),
            deny(
                "wipe",
                reason="Wiping has no authorized use here.",
                label="wipe denies",
            ),
            ask(
                "touch",
                reason="Touching reaches production whatever else holds.",
                label="touch asks",
            ),
            deny(
                when=env("STUB_DANGER"),
                reason="STUB_DANGER changes what the tool does.",
                label="danger assignment",
            ),
        ],
        handoffs=[
            handoff(
                "exec",
                keeps_operands=1,
                flags=[takes_value("-u")],
            ),
            handoff("run", keeps_operands=1),
        ],
    )

    tool(
        "stubcli",
        default=deny(
            reason="stubcli writes to shared infrastructure by default."
        ),
        grants=[
            grant(
                when=at_least_one_operand(matching(READ_VERBS)),
                reason="A read-only verb.",
            ),
        ],
        rules=[
            deny(
                when=at_least_one_operand(matching(WRITE_VERBS)),
                reason="A write verb reaches shared infrastructure.",
                label="write verbs",
            ),
        ],
    )

    tool(
        "stubalways",
        default=deny(reason="Every use of stubalways is the operator's."),
    )
