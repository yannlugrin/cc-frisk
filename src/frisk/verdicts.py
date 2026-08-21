"""Verdicts, their ranking, and what an outcome does to a rule (§3.2).

The ranking — deny over ask over allow over silence — is what makes a
line's judgment order-free: verdicts from different invocations, rules
and sources combine by strength, never by the order they were found in.

The two role functions are the other half of §3.2's three-valued model,
and they are here rather than in `matchers.py` because they are exactly
what a matcher must not know: the same `unproven` releases nothing from
a grant and fires a deny rule at ask strength, and only the role tells
the two apart.
"""

from __future__ import annotations

import enum
from collections.abc import Iterable

from .matchers import Outcome


class Verdict(enum.Enum):
    """The four answers, strongest first (§3.2)."""

    DENY = "deny"
    ASK = "ask"
    ALLOW = "allow"
    SILENT = "silent"


def strongest(verdicts: Iterable[Verdict]) -> Verdict:
    """The strongest of these, `SILENT` when there are none.

    Deny and ask always win; that `ALLOW` outranks `SILENT` here is
    only the ranking — how an allow earned on one invocation is
    withheld because another asked is §6.1's combination, not this.
    """
    raise NotImplementedError


def fires_at(declared: Verdict, outcome: Outcome) -> Verdict | None:
    """What a rule declaring `declared` contributes, given `outcome`.

    Satisfied fires the rule as declared. Unsatisfied fires nothing.
    Unproven is the case the boolean model got wrong: a deny or ask
    rule fires at **ask** strength — the gated value cannot be proven
    present, so no deny, and it cannot be ruled out, so never silence —
    while an allow rule fires nothing at all, because an unknown never
    weakens a boundary (§4.2).
    """
    raise NotImplementedError


def grant_holds(outcome: Outcome) -> bool:
    """Whether a grant condition with this outcome releases.

    Only `SATISFIED` does. A grant is a proof of a safe shape, and
    unproven is the absence of the proof, not a weaker version of it.
    """
    raise NotImplementedError
