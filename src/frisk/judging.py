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

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, replace

from .declare import (
    AnyFlagUsed,
    Arity,
    Assignment,
    AtLeastOneOperand,
    Condition,
    EnvSet,
    EveryOperand,
    FlagUsed,
    Inside,
    NoOperands,
    OptionUsed,
    Rule,
    Scope,
    Source,
)
from .matchers import Matcher, Outcome, Value, combine_all, combine_any
from .reading import Assigned, Doubt, Flag, Invocation, Reading
from .registry import Entry, Registry
from .verdicts import Verdict, fires_at, grant_holds, strongest


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


# --------------------------------------------------------------------
# The whole line (§4.1, §6.1)


def judge(
    reading: Reading,
    registry: Registry,
    secure: Rule | None = None,
) -> Judgment:
    """The verdict for one command line, and why (§3.2, §6.1, §6.2)."""
    if reading.unparseable:
        return _unparseable(reading, secure)
    judged = tuple(
        _judged(invocation, registry, secure)
        for invocation in reading.invocations
    )
    verdict = combined([each.verdict for each in judged])
    return Judgment(
        verdict=verdict,
        citations=tuple(
            citation
            for each in judged
            for citation in each.citations
            if citation.verdict is verdict
        ),
        judged=judged,
    )


def combined(verdicts: Sequence[Verdict]) -> Verdict:
    """§6.1's table over a line's per-invocation verdicts.

    Three rows of the table, not seven: the allow rows wait on open
    fact (c) and ship at `017`, so every line that would reach one
    answers its stricter sibling — "the line falls back to genuine
    silence" (`D-051`). An allow earned by an invocation is therefore
    visible on `Judged` and never on the line.
    """
    if Verdict.DENY in verdicts:
        return Verdict.DENY
    if Verdict.ASK in verdicts:
        return Verdict.ASK
    return Verdict.SILENT


#: §4.1's fallback, written as steering text: the model reads it, so it
#: says what to do rather than only what went wrong (§6.2).
_UNPARSEABLE = (
    "This command line could not be parsed, so nothing in it was read "
    "and nothing about it is proven. It names {named}, which carry "
    "rules or grants here. Rewrite it as separate commands, or quote "
    "it so it parses, and frisk can judge what it actually runs."
)


def _unparseable(reading: Reading, secure: Rule | None) -> Judgment:
    """A line nothing could parse (§4.1).

    No invocations come back with it, so nothing is judged and the
    answer rests on the raw scan `reading` already ran. In secure mode
    the global default applies "regardless" — of the scan, which is
    what that word in §4.1 attaches to.
    """
    if secure is not None:
        return Judgment(
            verdict=secure.verdict,
            citations=(Citation(secure.verdict, secure.reason),),
        )
    if not reading.speaking:
        return Judgment(verdict=Verdict.SILENT)
    named = ", ".join(reading.speaking)
    return Judgment(
        verdict=Verdict.ASK,
        citations=(Citation(Verdict.ASK, _UNPARSEABLE.format(named=named)),),
    )


# --------------------------------------------------------------------
# One invocation (§3.2)


def _judged(
    invocation: Invocation,
    registry: Registry,
    secure: Rule | None,
) -> Judged:
    """One invocation, judged alone and with no sight of its neighbours."""
    entry = invocation.entry
    if entry is None:
        return _unregistered(invocation, secure)

    # The closed worlds and the doubts first: none of them depends on
    # how the operands align, what they cost is the same under every
    # alignment, and what they defeat is every grant.
    fixed: list[Citation] = []
    unaccounted = _unaccounted_assignments(invocation, entry, registry)
    fixed.extend(unaccounted)
    breaches = tuple(_unaccounted_flags(invocation, entry))
    fixed.extend(_breach_citations(invocation, breaches))
    doubted, unresolved = _doubts(invocation, entry)
    fixed.extend(doubted)
    # §3.2 makes the closed world "the load-bearing property: a flag or
    # value nobody considered can only move a verdict *toward* the
    # stricter outcome". All three of them defeat a grant, the
    # assignment world included: a grant proving `--check` safe proves
    # nothing about a run carrying `GIT_SSH_COMMAND=…`, which runs an
    # arbitrary program.
    provable = not unaccounted and not breaches and not _defeating(invocation)

    # §4.2: an undeclared dashed token leaves the operand alignment
    # ambiguous, so every alignment the ambiguity admits is judged and
    # **the strictest verdict any of them reaches is the invocation's**
    # (`D-060`). Reading's presumed-bare alignment is the first, and on
    # the overwhelming majority of lines it is the only one.
    reached = [
        _aligned(invocation, entry, operands, secure, fixed, provable)
        for operands in _alignments(invocation, entry)
    ]
    if unresolved is not None:
        # §4.2: recognition degrades stricter, "like any path match" —
        # and an unproven path match fires a deny at ask strength
        # (§3.2). Producing the deny would refuse a file the line does
        # not identify, which is §4.3's wrong deny (`D-054`).
        #
        # Applied to the citations too, and before either is combined.
        # Dropping them instead would leave the operator and the model
        # with the unresolved-path ask alone — whose steering text says
        # to run the line where the path means what it says, which is
        # exactly the line that denies. §6.2 makes a reason steering
        # text; steering toward the refusal it hid is the opposite.
        reached = [
            (
                _downgraded(answer),
                tuple(_downgraded_citation(each) for each in cited),
            )
            for answer, cited in reached
        ]
    verdict = strongest([each[0] for each in reached])
    # §6.2: "when several declarations independently reach the returned
    # rank, the citation should name them all". Two alignments can
    # reach it through *different* declarations, so the first
    # alignment's list is not the answer.
    citations = _deduplicated(
        citation
        for answer, cited in reached
        if answer is verdict
        for citation in cited
    )
    if unresolved is not None and verdict is not Verdict.SILENT:
        # It explains, so it is named wherever something objected —
        # the operator meeting an ask on a line they believed granted
        # is owed the token that could not be resolved. It does not
        # decide, so where nothing objected it says nothing.
        citations = (replace(unresolved, verdict=verdict), *citations)
    return Judged(invocation=invocation, verdict=verdict, citations=citations)


def _downgraded(verdict: Verdict) -> Verdict:
    """A deny the engine declined to trust, at ask strength (`D-054`)."""
    return Verdict.ASK if verdict is Verdict.DENY else verdict


def _downgraded_citation(citation: Citation) -> Citation:
    """The same declaration, cited at the rank it actually reached."""
    if citation.verdict is not Verdict.DENY:
        return citation
    return replace(citation, verdict=Verdict.ASK)


def _deduplicated(citations: Iterable[Citation]) -> tuple[Citation, ...]:
    """These citations in order, with repeats dropped.

    Two alignments of one invocation cite the same declaration for the
    same reading of it, and naming it twice would tell the operator
    there are two things to look at.
    """
    kept: list[Citation] = []
    for citation in citations:
        if citation not in kept:
            kept.append(citation)
    return tuple(kept)


def _alignments(
    invocation: Invocation, entry: Entry
) -> list[tuple[Value, ...]]:
    """The operand alignments this invocation is judged under (§4.2).

    Reading's own alignment first, then the ones in which the
    undeclared tokens, **taken from the left**, consumed the word after
    them. That prefix-cumulative family is the bound `D-060` chose:
    a line with three undeclared tokens is judged four times, not
    eight, so the count is linear in their number rather than in their
    combinations. It is therefore not literally every alignment the
    ambiguity admits — the reading where only the *second* token took a
    value is not tried — and §4.2's wider phrase should be read against
    this bound.

    The count is linear; the *work* is not. Each alignment re-runs
    every rule and grant, and an operand quantifier walks the
    alignment's operands, so per-invocation cost grows with undeclared
    tokens times operands. Typical lines are microseconds, but an
    under-declared tool on a long line is where both factors grow at
    once — which is why the sweep is skipped outright below wherever it
    could not change an answer.
    """
    if not invocation.displaceable or not _operand_sensitive(entry):
        return [invocation.operands]
    alignments = [invocation.operands]
    dropped: set[int] = set()
    for index in sorted(invocation.displaceable):
        dropped.add(index)
        alignments.append(
            tuple(
                operand
                for position, operand in enumerate(invocation.operands)
                if position not in dropped
            )
        )
    return alignments


def _operand_sensitive(entry: Entry) -> bool:
    """Whether any declaration here reads the operand list at all.

    A tool whose rules key only on flags and assignments answers the
    same under every alignment, so re-judging it is pure cost. This is
    the cheap half of §4.5: the sweep runs where it can decide
    something and nowhere else.
    """
    for placed in entry.rules:
        if placed.rule.subcommand or _reads_operands(placed.rule.conditions):
            return True
    for granted in entry.grants:
        if granted.grant.subcommand or _reads_operands(
            granted.grant.conditions
        ):
            return True
    return False


def _reads_operands(conditions: Sequence[Condition]) -> bool:
    return any(
        isinstance(condition, (EveryOperand, AtLeastOneOperand, NoOperands))
        for condition in conditions
    )


def _aligned(
    invocation: Invocation,
    entry: Entry,
    operands: tuple[Value, ...],
    secure: Rule | None,
    fixed: Sequence[Citation],
    provable: bool,
) -> tuple[Verdict, tuple[Citation, ...]]:
    """This invocation judged with its operands aligned one way."""
    citations = list(fixed)
    matched, rule_citations = _rules(invocation, entry, operands)
    citations.extend(rule_citations)
    held = provable and _grant_holds(invocation, entry, operands)
    if not matched and not held:
        fallback = _default(invocation, entry, secure)
        if fallback is not None:
            citations.append(fallback)
    return (
        strongest([citation.verdict for citation in citations]),
        tuple(citations),
    )


def _unregistered(invocation: Invocation, secure: Rule | None) -> Judged:
    """A command position reaching no registered tool (§3.2, §4.2).

    Silence in the default posture, and the same answer whether the
    word was an ordinary unknown or a name the line cannot show
    (`$RUNNER deploy`): §4.2 separates the two only *inside* a wrapper
    or handoff, which is `010`'s ground. Assignments in front of it
    keep the tool's posture too — "an opinion the guard does not have
    about `make` should not appear because of a harmless `DEBUG=1`".
    """
    if secure is None:
        return Judged(invocation=invocation, verdict=Verdict.SILENT)
    return Judged(
        invocation=invocation,
        verdict=secure.verdict,
        citations=(
            Citation(
                verdict=secure.verdict,
                reason=secure.reason,
                tool=invocation.name,
            ),
        ),
    )


# --------------------------------------------------------------------
# The closed worlds (§3.2)
#
# Both of them answer the same shape of question — is this token one
# the declaration accounted for — and both fail the same way: not by
# refusing outright, but by making a grant unable to prove anything.
# What they add on top is the ask §3.3 asks for.


# The engine's own reasons, written under `D-062`: they say what is
# wrong and why, and never tell the reader to remove a token whose
# purpose the engine does not know — an unaccounted flag is by
# definition one it does not know, and `--check-file` is exactly the
# shape that makes "drop the flag" advice to disarm the safeguard.
# Where there is a safe path the engine can actually name, it names it.

_UNACCOUNTED_ASSIGNMENT = (
    "{name} is set in front of {tool}, and {tool}'s declaration does "
    "not account for it. An assignment can change what a command does "
    "without appearing among its flags, so frisk cannot tell what this "
    "run will do."
)

_UNACCOUNTED_FLAG = (
    "{name} is not among the flags {tool} declares, and {tool} is only "
    "safe in the shapes its declaration proves, so nothing here can "
    "establish what this run does. Run {tool} in one of those shapes, "
    "or say what this use is."
)


def _unaccounted_assignments(
    invocation: Invocation, entry: Entry, registry: Registry
) -> list[Citation]:
    """§3.2's assignment world, closed for **every** registered tool.

    Not only gated ones: dangerous assignments cannot be enumerated,
    while a tool's benign ones are finite and the surprise loop grows
    them. The benign layer is consulted first because it is the engine
    default every project would otherwise have to write.
    """
    unaccounted = []
    for assigned in invocation.assignments:
        if _accounts(registry.benign_assignments(), assigned, invocation):
            continue
        if _accounts(entry.assignments, assigned, invocation):
            continue
        unaccounted.append(
            Citation(
                verdict=Verdict.ASK,
                reason=_UNACCOUNTED_ASSIGNMENT.format(
                    name=assigned.name, tool=invocation.name
                ),
                tool=invocation.name,
                read=(f"environment {assigned.name}",),
            )
        )
    return unaccounted


def _accounts(
    declared: Sequence[Assignment],
    assigned: Assigned,
    invocation: Invocation,
) -> bool:
    """Whether any of these declarations accounts for this assignment.

    A value condition must be *satisfied*: unproven is not an
    acceptance, or `GIT_PAGER=$WHATEVER` would pass the accounting that
    exists to catch exactly that.
    """
    for declaration in declared:
        if isinstance(declaration.name, str):
            if declaration.name != assigned.name:
                continue
        elif (
            declaration.name.evaluate(assigned.name, invocation.context)
            is not Outcome.SATISFIED
        ):
            continue
        if declaration.value is None:
            return True
        if (
            declaration.value.evaluate(assigned.value, invocation.context)
            is Outcome.SATISFIED
        ):
            return True
    return False


def _unaccounted_flags(invocation: Invocation, entry: Entry) -> list[str]:
    """The flags a gated tool's closed world does not admit (§3.2).

    A rules-only tool has no closed world: git meeting a flag nobody
    wrote down is not a problem, and the same `flags=` list there is
    arity and nothing more.
    """
    if not entry.gated:
        return []
    unaccounted: list[str] = []
    for flag in invocation.flags:
        # `--` is the end-of-options marker, which §4.2 calls
        # "matchable structure" — the reading layer synthesises it, the
        # operator did not write it as a flag. Counting it here would
        # make every gated tool ask on `deploy --check -- file.yml` and
        # leave no shape a grant could ever prove (`D-061`).
        if flag.name == "--" or flag.name in entry.flags:
            continue
        # One citation per name, however many times it was written:
        # `-x -x` is one thing to look at, not two.
        if flag.name not in unaccounted:
            unaccounted.append(flag.name)
    return unaccounted


def _breach_citations(
    invocation: Invocation, breaches: Sequence[str]
) -> list[Citation]:
    """What a closed-world breach costs, beyond defeating the grants.

    An ask of its own (`D-056`). Without it the breach could only reach
    the tool's default verdict, so on a tool with a closed world and no
    grants — nothing that could ever release it — the declared flag
    list would change no verdict at all, and `closed_world=True` would
    be a keyword that does nothing.
    """
    return [
        Citation(
            verdict=Verdict.ASK,
            reason=_UNACCOUNTED_FLAG.format(name=name, tool=invocation.name),
            tool=invocation.name,
            read=(f"flag {name}",),
        )
        for name in breaches
    ]


# --------------------------------------------------------------------
# What reading could not establish (§3.3)


_MALFORMED = (
    "{flag} takes a value and nothing follows it, so this command line "
    "could not be read as written and nothing about it is established."
)

_UNRESOLVED_PATH = (
    "{name} is a relative path, and an earlier `cd` on this line moved "
    "what it hangs off, so frisk cannot tell whether this is the file "
    "its declaration names. Run it on a line of its own, where the "
    "path means what it says."
)

_UNREADABLE = (
    "A value on this line is not a plain word — it carries whitespace, "
    "a glob or an expansion — so {tool}, which is only safe in the "
    "shapes its declaration proves, cannot be proven to run one of "
    "them."
)


def _doubts(
    invocation: Invocation, entry: Entry
) -> tuple[list[Citation], Citation | None]:
    """What each doubt costs, and whether the verdict is capped at ask.

    The three are priced apart because §4.2 scopes them apart. An
    unreadable token is stated *on gated invocations*, so it costs
    nothing on a rules-only tool — `git commit -m 'a plain message'` is
    silent — and on a gated one it asks in its own right, because §4.2
    says it leaves the invocation unproven "**whatever the grants would
    otherwise say**", and a tool gated by a closed world with no grants
    has nothing for a defeated grant to fall back onto. A malformed
    invocation is stated flat and is "unproven, not safe", so it asks
    whatever the tool (`D-053`). An unresolved path is unproven
    *identity*, and it is the one that **decides nothing of its own**
    (`D-063`). §4.2 says recognition there degrades "like any path
    match", and an unproven path match adds no verdict — it releases no
    grant and fires a declaration that was going to fire anyway at ask
    strength. So this one comes back separately: it caps the verdict,
    it defeats grants through `_defeating`, and it is cited only where
    something else already objected. On a rules-only tool where nothing
    is gated, both readings of the line — this file or another — are
    silent, and inventing an ask there would answer about neither.
    """
    citations = []
    unresolved = None
    for doubt in invocation.doubts:
        if doubt is Doubt.UNREADABLE and entry.gated:
            citations.append(
                Citation(
                    verdict=Verdict.ASK,
                    reason=_UNREADABLE.format(tool=invocation.name),
                    tool=invocation.name,
                )
            )
        elif doubt is Doubt.MALFORMED:
            citations.append(
                Citation(
                    verdict=Verdict.ASK,
                    reason=_MALFORMED.format(flag=_starved(invocation)),
                    tool=invocation.name,
                    read=(f"flag {_starved(invocation)}",),
                )
            )
        elif doubt is Doubt.UNRESOLVED_PATH:
            unresolved = Citation(
                verdict=Verdict.ASK,
                reason=_UNRESOLVED_PATH.format(name=invocation.name),
                tool=invocation.name,
                read=(f"command {invocation.name} (unproven)",),
            )
    return citations, unresolved


def _starved(invocation: Invocation) -> str:
    """The value-taking flag left with nothing after it (§6.2).

    Recovered from the invocation rather than carried on the doubt: a
    `Doubt` names the *kind* of gap, and §6.2 owes the operator the
    token. The reading that set the doubt is the reading being read
    here, so the two cannot disagree.
    """
    entry = invocation.entry
    if entry is not None:
        for flag in invocation.flags:
            if (
                flag.value is None
                and entry.flags.get(flag.name) is Arity.VALUE
            ):
                return flag.name
        for option in invocation.options:
            if (
                option.value is None
                and entry.options.get(option.name) is Arity.VALUE
            ):
                return option.name
    return "a flag"


def _defeating(invocation: Invocation) -> bool:
    """Whether any doubt stops a grant proving anything (§3.3).

    All three do. A grant is a proof of a safe shape, and every doubt
    is the absence of part of what it would have to prove.
    """
    return bool(invocation.doubts)


# --------------------------------------------------------------------
# Rules, grants and the default (§3.2)


def _rules(
    invocation: Invocation, entry: Entry, operands: Sequence[Value]
) -> tuple[bool, list[Citation]]:
    """Every rule on this tool, evaluated — and whether one matched.

    Exhaustive by requirement: §6.2's citation must name every
    declaration at the deciding rank, so nothing may stop at the first
    one that decides.

    `matched` is *satisfied*, never merely "contributed" (`D-059`). A
    deny rule fired at ask strength by an unproven condition has not
    matched, so the tool's default still applies and the two combine by
    rank — otherwise uncertainty would soften a deny-default tool,
    which is the one direction §3.3 forbids.
    """
    matched = False
    citations = []
    for placed in entry.rules:
        if not _here(placed.rule.scope):
            continue
        outcome, phrases, subcommand = _evaluated(
            placed.rule.subcommand,
            placed.rule.conditions,
            invocation,
            operands,
            strict=False,
        )
        if outcome is None:
            continue
        if outcome is Outcome.SATISFIED:
            matched = True
        fired = fires_at(placed.rule.verdict, outcome)
        if fired is None:
            continue
        citations.append(
            Citation(
                verdict=fired,
                reason=placed.rule.reason,
                tool=invocation.name,
                subcommand=subcommand,
                read=phrases,
                label=placed.label,
                source=placed.source,
            )
        )
    return matched, citations


def _grant_holds(
    invocation: Invocation, entry: Entry, operands: Sequence[Value]
) -> bool:
    """Whether any grant proves this invocation safe (§3.2).

    Existential among the grants and universal within each: one proven
    shape is enough, and a grant is proven only when every condition is
    *satisfied* — unproven is the absence of the proof, not a weaker
    version of it.
    """
    for placed in entry.grants:
        if not _here(placed.grant.scope):
            continue
        outcome, _, _ = _evaluated(
            placed.grant.subcommand,
            placed.grant.conditions,
            invocation,
            operands,
            strict=True,
        )
        # `None` is "this grant does not apply here" — a different
        # thing from applying and not being satisfied, and neither
        # releases.
        if outcome is not None and grant_holds(outcome):
            return True
    return False


def _here(scope: Scope) -> bool:
    """Whether a rule or grant scoped this way applies to this position.

    `009` walks into no handoff — that is `012` — so every invocation
    it sees is outside every one of them. `anywhere` and `host_only`
    both apply; `inside(...)` cannot, and firing it would refuse a
    command that never entered the world the operator confined it to.
    """
    return not isinstance(scope, Inside)


_IMPLICIT_ASK = (
    "No grant proved this run safe, and {tool} is declared safe only in "
    "the shapes its grants name. Run it in one of those shapes, or say "
    "what this use is."
)


def _default(
    invocation: Invocation, entry: Entry, secure: Rule | None
) -> Citation | None:
    """The tool's outcome for "no rule matched, no grant held" (§3.2).

    A **fallback**, not a floor (`D-059`): this is reached only where
    nothing matched and nothing was released, so a rule the operator
    wrote is never undercut by it.

    Three sources in order. A declared default is the operator's own
    and stands, silence included — §5.3 gives a declared silence
    nothing to explain, so it returns no citation. Otherwise secure
    mode's global default replaces the silence nobody declared (§3.2).
    Otherwise §3.2's enumeration: ask where the tool declares grants,
    silent otherwise (`D-056`).
    """
    if entry.default is not None:
        rule = entry.default.rule
        if rule.verdict is Verdict.SILENT:
            return None
        return Citation(
            verdict=rule.verdict,
            reason=rule.reason,
            tool=invocation.name,
            label=entry.default.label,
            source=entry.default.source,
        )
    if secure is not None:
        return Citation(
            verdict=secure.verdict,
            reason=secure.reason,
            tool=invocation.name,
        )
    if entry.grants:
        return Citation(
            verdict=Verdict.ASK,
            reason=_IMPLICIT_ASK.format(tool=invocation.name),
            tool=invocation.name,
        )
    return None


# --------------------------------------------------------------------
# Conditions (§3.2, §5.2)
#
# One evaluator, two callers, and the only difference between them is
# how repeated tokens combine: a rule asks whether the gated thing is
# there at all, a grant asks whether every occurrence is proven safe.
# `--mode dry-run --mode destroy` must not release a grant, and
# `-f` twice must still fire a deny.


def _evaluated(
    subcommand: Sequence[str],
    conditions: Sequence[Condition],
    invocation: Invocation,
    carried: Sequence[Value],
    *,
    strict: bool,
) -> tuple[Outcome | None, tuple[str, ...], tuple[str, ...]]:
    """This declaration against this invocation.

    `None` for the outcome means the declaration does not apply at all
    — its subcommand path is not what this invocation ran — which is
    different from applying and not being satisfied.
    """
    path = tuple(subcommand)
    reached = _subcommand(path, carried)
    if reached is None:
        return None, (), path
    outcome, operands = reached
    outcomes = [outcome]
    phrases: list[str] = []
    for condition in conditions:
        answer, said = _answers(condition, invocation, operands, strict)
        outcomes.append(answer)
        phrases.extend(said)
    return combine_all(outcomes), tuple(phrases), path


def _subcommand(
    path: Sequence[str], operands: Sequence[Value]
) -> tuple[Outcome, tuple[Value, ...]] | None:
    """Whether these operands open with this subcommand path.

    The path is matched three-valued like anything else: a dynamic
    token in subcommand position cannot be read, and an unknown never
    satisfies a positive condition nor weakens a boundary (§4.2), so
    `tool $SUB --force` leaves a deny on `$SUB` unproven rather than
    ruled out.
    """
    if not path:
        return Outcome.SATISFIED, tuple(operands)
    if len(operands) < len(path):
        return None
    outcomes = []
    for want, got in zip(path, operands):
        if got.dynamic:
            outcomes.append(Outcome.UNPROVEN)
        elif got.text == want:
            outcomes.append(Outcome.SATISFIED)
        else:
            return None
    return combine_all(outcomes), tuple(operands[len(path) :])


def _answers(
    condition: Condition,
    invocation: Invocation,
    operands: Sequence[Value],
    strict: bool,
) -> tuple[Outcome, tuple[str, ...]]:
    """What one condition says, and the phrase §6.2 owes for it.

    The phrase names what was **read** — the flag and the value the
    line actually carried — rather than what was declared, because an
    operator meeting a verdict needs the token, and `frisk registry`
    already prints the declaration.
    """
    if isinstance(condition, FlagUsed):
        return _carried(
            condition.name,
            condition.value,
            invocation.flags,
            "flag",
            invocation,
            strict,
        )
    if isinstance(condition, OptionUsed):
        return _carried(
            condition.name,
            condition.value,
            invocation.options,
            "option",
            invocation,
            strict,
        )
    if isinstance(condition, EnvSet):
        return _assigned(condition, invocation, strict)
    if isinstance(condition, AnyFlagUsed):
        for flag in invocation.flags:
            if flag.name in condition.names:
                return Outcome.SATISFIED, (f"flag {flag.name}",)
        return Outcome.UNSATISFIED, ()
    if isinstance(condition, NoOperands):
        if operands:
            return Outcome.UNSATISFIED, ()
        return Outcome.SATISFIED, ("no operands",)
    if isinstance(condition, EveryOperand):
        return _quantified(condition.value, operands, invocation, every=True)
    if isinstance(condition, AtLeastOneOperand):
        return _quantified(condition.value, operands, invocation, every=False)
    raise AssertionError(f"no evaluation for {type(condition).__name__}")


def _carried(
    name: str,
    matcher: Matcher | None,
    carried: Sequence[Flag],
    kind: str,
    invocation: Invocation,
    strict: bool,
) -> tuple[Outcome, tuple[str, ...]]:
    """A flag or option the invocation carries, and what its value says."""
    found = [each for each in carried if each.name == name]
    if not found:
        return Outcome.UNSATISFIED, ()
    if matcher is None:
        return Outcome.SATISFIED, (f"{kind} {name}",)
    answers = []
    for each in found:
        if each.value is None:
            # A value-optional flag used bare whose declaration named no
            # default (`D-039`): the condition can be neither proven nor
            # ruled out.
            answers.append((Outcome.UNPROVEN, f"{kind} {name}"))
            continue
        outcome = matcher.evaluate(each.value, invocation.context)
        answers.append((outcome, f"{kind} {name} '{each.value.text}'"))
    return _decided(answers, strict)


def _assigned(
    condition: EnvSet, invocation: Invocation, strict: bool
) -> tuple[Outcome, tuple[str, ...]]:
    """An environment assignment bound to this invocation."""
    found = [
        each for each in invocation.assignments if each.name == condition.name
    ]
    if not found:
        return Outcome.UNSATISFIED, ()
    if condition.value is None:
        return Outcome.SATISFIED, (f"environment {condition.name}",)
    answers = [
        (
            condition.value.evaluate(each.value, invocation.context),
            f"environment {condition.name} '{each.value.text}'",
        )
        for each in found
    ]
    return _decided(answers, strict)


def _quantified(
    matcher: Matcher,
    operands: Sequence[Value],
    invocation: Invocation,
    *,
    every: bool,
) -> tuple[Outcome, tuple[str, ...]]:
    """§3.2's two operand quantifiers.

    Both require **at least one** operand: "empty operands are never
    vacuously granted — a command acting on nothing has not proven what
    it acts on", and §5.2's `no_operands()` is the deliberate spelling
    for the empty case.
    """
    if not operands:
        return Outcome.UNSATISFIED, ()
    answers = [
        (matcher.evaluate(each, invocation.context), f"operand '{each.text}'")
        for each in operands
    ]
    return _decided(answers, strict=every)


def _decided(
    answers: Sequence[tuple[Outcome, str]], strict: bool
) -> tuple[Outcome, tuple[str, ...]]:
    """Combine several readings of one condition, and say which decided.

    `strict` is the caller's role, and it is the whole difference
    between the two: a grant needs every occurrence proven, so one
    miss decides it; a rule asks whether the gated thing is present at
    all, so one hit does. Threading the role rather than fixing one
    combiner is what keeps `--mode dry-run --mode destroy` from
    releasing a grant while `-f` twice still fires a deny.
    """
    outcomes = [outcome for outcome, _ in answers]
    combined_outcome = (
        combine_all(outcomes) if strict else combine_any(outcomes)
    )
    return combined_outcome, tuple(
        phrase + (" (unproven)" if outcome is Outcome.UNPROVEN else "")
        for outcome, phrase in answers
        if outcome is combined_outcome
    )
