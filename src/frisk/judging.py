"""Judging an invocation, and combining a line (§3.2, §6.1, §6.2).

Reading (§4.1, §4.2) says what a command line *contains*; this module
says what frisk *answers* about it. The two are separate modules because
they fail differently: a reading bug loses an invocation, a judging bug
gives the wrong verdict about one it found, and a report that cannot
tell those apart is a report the maintenance loop (§10) cannot act on.

Three properties of §3.2 are structural here rather than incidental.

* **Each invocation is judged alone.** `_judged` takes one invocation
  and never sees its neighbours: a safe command cannot vouch for the
  other half of its line, because there is no code path along which it
  could. What crosses invocations is `combined` below, and the only
  thing it moves is the verdict.
* **Evaluation is exhaustive.** Nothing short-circuits at the first
  deciding match — every rule of every invocation is evaluated, and
  every one that fired is kept — because §6.2's citation must name
  *every* declaration at the deciding rank across the whole line.
  Fixing one match and being surprised by the next is a wasted report
  cycle.
* **The verdict is order-free within one source.** Contributions are
  combined by `verdicts.strongest`, never by the order they were found
  in, so reordering the rules inside a configuration cannot change an
  answer. Across sources it is §3.4's composition that decided, long
  before anything here runs.

Secure mode arrives here as a parameter and nowhere else. The engine
capability ships now because it shapes the decision model and could not
be retrofitted (§3.2); the operator-facing switch that turns it on is a
later step, so no configuration can reach this argument yet.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .declare import Rule, Source
from .reading import Invocation, Reading
from .registry import Registry
from .verdicts import Verdict


@dataclass(frozen=True)
class Citation:
    """One declaration that fired, and what it read to fire (§6.2).

    A verdict an operator cannot grep for is a verdict they cannot
    report, so every non-silent contribution carries one of these: the
    reason (steering text — the objection *and* the acceptable path,
    because the model reads it), what was read, and which declaration
    decided.

    `label` and `source` are None for the verdicts no declaration
    reached: §4.1's unparseable line, and secure mode's global default
    standing in for an implicit silence. They are the engine's own
    answers, and saying so beats attributing them to a rule nobody
    wrote.
    """

    verdict: Verdict
    reason: str
    #: The command word as the operator wrote it, empty where the
    #: verdict belongs to the line rather than to an invocation.
    tool: str = ""
    subcommand: tuple[str, ...] = ()
    #: What matched, one phrase per condition — `flag --force`,
    #: `environment STUB_DANGER`, `operand /etc/passwd`.
    read: tuple[str, ...] = ()
    label: str | None = None
    source: Source | None = None


@dataclass(frozen=True)
class Judged:
    """One invocation and the verdict it earned alone (§3.2)."""

    invocation: Invocation
    verdict: Verdict
    #: Every contribution that fired on this invocation, at whatever
    #: rank — not only the deciding ones. The line decides which rank
    #: is cited, and it may be a rank this invocation did not reach.
    citations: tuple[Citation, ...] = ()


@dataclass(frozen=True)
class Judgment:
    """What frisk answers for a whole command line (§6.1)."""

    verdict: Verdict
    #: Every declaration at the deciding rank, across the whole line
    #: (§6.2). Empty for silence, which refuses nothing and so has
    #: nothing to explain.
    citations: tuple[Citation, ...] = ()
    judged: tuple[Judged, ...] = ()


def judge(
    reading: Reading,
    registry: Registry,
    secure: Rule | None = None,
) -> Judgment:
    """The verdict for one command line, and why (§3.2, §6.1, §6.2)."""
    raise NotImplementedError


def combined(verdicts: Sequence[Verdict]) -> Verdict:
    """§6.1's table over a line's per-invocation verdicts."""
    raise NotImplementedError
