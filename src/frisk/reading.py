"""§4.1 and §4.2: what a command string actually holds.

This is the engine's first half. It takes the string the Bash tool was
handed and produces the invocations on it, each with everything that
binds to it — the assignments in front of it, the options and flags it
carries, its operands, and what the rest of the line says about it.
It reaches no verdict: judging is §3.2's, and it reads what this
module returns.

**Quoting is resolved, never pattern-matched.** §4.1 opens on that and
it is the whole reason this module exists rather than a regular
expression: `git commit -m 'fix the --amend bug'` is not an amend, and
a flag inside a quoted substitution is invisible to any pattern that
respects quotes. The tokenizer is therefore the load-bearing part, and
it keeps more than the shell would — which token was quoted, and how —
because §4.2's dynamic-value rule and §4.3's substitutions both turn on
exactly that.

**Three things are deliberately not done here.** What lives behind
another program — a wrapper's command, a shell's `-c` payload, an
interpreter's file operand — is `010`. Substitutions, subshells and
heredocs are `011`. Handoffs and redirections are `012`. Reading stops
at the segment boundary and hands each segment's command word to the
registry.

**And doubt is reported by source, never priced.** A token no matcher
can read, a declared value-taking flag with nothing after it, a name
whose identity an in-line `cd` has unsettled: each is a `Doubt` on the
invocation, and what one *costs* is §3.2's business at `009`. The
sources are kept apart because §4.2 does not scope them alike — one is
stated on gated invocations and two are stated flat — and because §6.2
owes an operator the token that did it, not the word "unproven".
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field

from .matchers import NO_CONTEXT, MatchContext, Value
from .registry import Entry, Registry


class Doubt(enum.Enum):
    """Why reading could not establish an invocation's shape (§3.3).

    Three members rather than one boolean, because §4.2 does not scope
    them alike and `009` has to be able to tell them apart. The
    unreadable-token rule is stated **on gated invocations** — "a token
    a gated invocation carries that the engine cannot read as a plain
    word" — while a malformed invocation and an unresolved name are
    stated flat: "a declared value-taking flag with nothing after it
    makes the invocation malformed, which is unproven, not safe". Priced
    through one boolean, a malformed `git -C` on a rules-only tool would
    read as silence, which is the direction §3.3 forbids.

    They are also what §6.2's citation will want: an operator told a
    line is unproven is owed which token did it.
    """

    #: A token no matcher can read as a plain word: whitespace, a glob
    #: character, or a shell variable reference (§4.2).
    #:
    #: Recorded on **gated invocations only**, because that is where
    #: §4.2 states it — "a token a gated invocation carries that the
    #: engine cannot read as a plain word" — and because what a strange
    #: token defeats is a grant. A rules-only tool has none, and
    #: `git commit -m 'a plain message'` is silent (corpus). The scope
    #: lives here rather than at `009` so that every doubt this layer
    #: reports is one, and nothing downstream has to remember which
    #: ones to ignore.
    UNREADABLE = "unreadable"
    #: A declared value-taking flag with nothing after it (§4.2).
    MALFORMED = "malformed"
    #: A relative spelling of a path-declared tool after an in-line
    #: `cd`: recognition degrades stricter, like any path match (§4.2).
    UNRESOLVED_PATH = "unresolved-path"


@dataclass(frozen=True)
class Assigned:
    """One environment assignment bound to an invocation (§4.2).

    The append form (`FOO+=bar`) and the plain one are the same claim on
    the same name, so nothing here records which was written: a
    condition asks whether `FOO` is set and what it says, and no
    declared vocabulary can ask the other question.
    """

    name: str
    value: Value


@dataclass(frozen=True)
class Flag:
    """A dashed token an invocation carries, and the value it took.

    One type for both of §4.2's namespaces — the flags of a command and
    the options that precede its subcommand — because the difference is
    where they sit, which is which sequence on the invocation holds
    them, not what they are.

    `value` is None for a bare use, and for a value-optional flag used
    bare whose declaration named no default (`D-039`): a condition on
    that value can then be neither proven nor ruled out, which is the
    unproven the matchers already answer.
    """

    name: str
    value: Value | None = None


@dataclass(frozen=True)
class Invocation:
    """One command found on the line, with everything that binds to it."""

    #: The command word exactly as the operator wrote it — `/usr/bin/git`,
    #: `.venv/bin/ansible-playbook`. §6.2's citation names what was
    #: written, not what it resolved to.
    name: str
    #: The registration this word reached, or None where the name is
    #: not registered at all. Recognition is §4.2's: the whole basename,
    #: never a prefix, aliases equivalent, and a project-relative path
    #: declaration more specific than a basename one.
    entry: Entry | None = None
    assignments: tuple[Assigned, ...] = ()
    #: The options that preceded the subcommand, per the tool's
    #: declaration, with the values they took — a rule may constrain
    #: `-C`'s value like any other (§4.2).
    options: tuple[Flag, ...] = ()
    flags: tuple[Flag, ...] = ()
    operands: tuple[Value, ...] = ()
    #: What the rest of the line says about this invocation's matches —
    #: today, whether an earlier `cd` has poisoned relative paths (§3.2).
    context: MatchContext = NO_CONTEXT
    #: True where the command word is a variable the line cannot name —
    #: `$RUNNER deploy` (§4.2). `entry` is None as for any unregistered
    #: word, and this is what separates the two: a wrapper that loses
    #: its walk on an unnameable command asks, where a literal unknown
    #: word is silence. Recorded here so `010` reads a parse fact rather
    #: than re-parsing the name.
    dynamic_name: bool = False
    #: Everything reading could not establish about this invocation
    #: (§3.3), by source. Empty is a clean reading.
    doubts: tuple[Doubt, ...] = ()

    @property
    def unproven(self) -> bool:
        """Reading left something unestablished — see `doubts` for what.

        The convenience over `doubts`, and never the whole answer: what
        an unproven invocation *costs* is §3.2's, and it differs by
        source, which is why the sources are kept.
        """
        return bool(self.doubts)


@dataclass(frozen=True)
class Reading:
    """Everything one command string yielded (§4.1)."""

    invocations: tuple[Invocation, ...] = ()
    #: The line could not be parsed, and is therefore unproven — not
    #: the deny of §7, which is reserved for the guard's own failures,
    #: and never silent approval of whatever it might contain (§4.1).
    #: No invocations come back with it: half a reading would let a
    #: grant hold over tokens nobody finished reading.
    unparseable: bool = False
    #: What §4.1's raw scan found on an unparseable line: the registered
    #: names that can produce a non-silent verdict — *speaking*, in
    #: §3.2's vocabulary (`D-047`) — appearing as whole
    #: whitespace-delimited words, compared by basename so `/usr/bin/git`
    #: does not evade the scan. Empty on a line that parsed.
    speaking: tuple[str, ...] = field(default_factory=tuple)


def read(command_line: str, registry: Registry) -> Reading:
    """The invocations this command string holds (§4.1, §4.2)."""
    raise NotImplementedError
