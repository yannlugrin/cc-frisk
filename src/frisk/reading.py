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
import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field

from .declare import Arity
from .matchers import NO_CONTEXT, MatchContext, Value
from .registry import Entry, Registry

#: Every token that ends one invocation and begins another (§4.1).
#:
#: Longest first, and the order is load-bearing rather than tidy: `&&`
#: has to be tried before `&` and `|&` and `||` before `|`, or
#: `a && b` reads as two separators around an empty segment. The
#: newline is in the same list because §4.1 puts it there — "including
#: runs of them and blank lines" — and an engine that treated it as
#: whitespace would read `git status\ngit push --force` as one
#: `git status` with extra operands. It appears in all three of §4.1's
#: spellings (`D-048`), `\r\n` before `\n` for the same
#: longest-first reason, so no token is left carrying a carriage
#: return.
#:
#: Named rather than inlined so the suite can iterate what the engine
#: actually uses: one case checks that every separator §4.1 lists is
#: handled, and another that every separator declared here splits
#: cleanly, so a member added later cannot arrive unexercised.
SEPARATORS: tuple[str, ...] = (
    "&&",
    "||",
    "|&",
    ";",
    "|",
    "&",
    "\r\n",
    "\n",
    "\r",
)


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
    try:
        segments = _segments(command_line)
        invocations = _invocations(segments, registry)
    except _Unparseable:
        # Half a reading is worse than none: a grant proved over tokens
        # nobody finished reading is exactly the silent approval §4.1
        # refuses. What comes back instead is the raw scan.
        return Reading(
            unparseable=True, speaking=_speaking(command_line, registry)
        )
    return Reading(invocations=invocations)


class _Unparseable(Exception):
    """This string is not a command line the engine can read (§4.1)."""


# --------------------------------------------------------------------
# Tokenizing and splitting (§4.1)
#
# One pass over the string, resolving quoting as it goes, emitting the
# words of each segment. A word remembers two things beyond its text:
# whether the shell would expand it, because §4.2 makes an unknown a
# decision rather than a string; and the source it was written as,
# because an assignment's *form* is what decides whether it is one.


@dataclass(frozen=True)
class _Word:
    """One token, quoting resolved."""

    text: str
    raw: str
    dynamic: bool = False

    def value(self) -> Value:
        return Value(self.text, dynamic=self.dynamic)


#: What stops a token being a plain word (§4.2). The three POSIX glob
#: characters and nothing invented beside them.
_GLOB = "*?["

#: The three spellings of a line ending (`D-048`). They are separators,
#: and they are also what a backslash continues over.
_LINE_ENDINGS = ("\r\n", "\n", "\r")

#: Inside double quotes a backslash is literal unless what follows is
#: one of these — so `"a\b"` really is `a\b`, where outside the quotes
#: it would be `ab`.
_DOUBLE_QUOTE_ESCAPES = ("$", "`", '"', "\\")

_NAME = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ_"
_NAME_REST = _NAME + "0123456789"

#: A leading environment assignment (§4.2). Matched against the word as
#: *written*: `FOO=bar` is one and `FOO'='bar` is not, and only the raw
#: form can tell them apart once quoting has been resolved away.
_ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\+?=")

#: An array-shaped assignment, which §4.2 requires land stricter rather
#: than be misread as something harmless (`D-048` names the direction,
#: §4.2 the rule). Read naively `FOO=(a b) tool run` binds `FOO` to
#: `(a`, makes `b)` the command word, and drops the tool being run to an
#: operand of a command nobody wrote.
_ARRAY_ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\+?=\(")


def _segments(command_line: str) -> list[list[_Word]]:
    """The words of each invocation on the line, separators applied.

    Empty segments are dropped rather than represented: a trailing `;`,
    a run of blank lines and the gap in `\\n\\r` are all the same
    nothing, and nothing runs no command.
    """
    segments: list[list[_Word]] = []
    words: list[_Word] = []
    text: list[str] = []
    raw: list[str] = []
    state = {"dynamic": False, "started": False}
    index = 0
    length = len(command_line)

    def end_word() -> None:
        if state["started"]:
            words.append(_Word("".join(text), "".join(raw), state["dynamic"]))
        del text[:]
        del raw[:]
        state["dynamic"] = False
        state["started"] = False

    def end_segment() -> None:
        end_word()
        if words:
            segments.append(list(words))
        del words[:]

    while index < length:
        separator = _separator_at(command_line, index)
        if separator is not None:
            end_segment()
            index += len(separator)
            continue
        character = command_line[index]
        if character in " \t":
            end_word()
            index += 1
            continue
        if character == "#" and not state["started"]:
            # A comment opens only where a word begins. Inside one, `#`
            # is an ordinary character and dropping the rest of the line
            # would lose real operands (§4.1).
            while (
                index < length and _separator_at(command_line, index) is None
            ):
                index += 1
            continue
        if character == "\\":
            continued = _continuation_at(command_line, index)
            if continued is not None:
                # Removed outright: a continuation joins what it
                # separates and starts no word of its own (§4.1).
                raw.append(continued)
                index += len(continued)
                continue
            if index + 1 >= length:
                # A backslash with nothing to escape; the shell would
                # wait for input that is not coming.
                raise _Unparseable
            state["started"] = True
            text.append(command_line[index + 1])
            raw.append(command_line[index : index + 2])
            index += 2
            continue
        if character == "'":
            closing = command_line.find("'", index + 1)
            if closing < 0:
                raise _Unparseable
            state["started"] = True
            text.append(command_line[index + 1 : closing])
            raw.append(command_line[index : closing + 1])
            index = closing + 1
            continue
        if character == '"':
            state["started"] = True
            index, referenced = _double_quoted(command_line, index, text, raw)
            state["dynamic"] = state["dynamic"] or referenced
            continue
        if character == "$":
            reference = _reference_at(command_line, index)
            if reference is not None:
                state["started"] = True
                state["dynamic"] = True
                text.append(reference)
                raw.append(reference)
                index += len(reference)
                continue
        state["started"] = True
        text.append(character)
        raw.append(character)
        index += 1

    end_segment()
    return segments


def _separator_at(command_line: str, index: int) -> str | None:
    """The separator starting here, longest first, or None."""
    for separator in SEPARATORS:
        if command_line.startswith(separator, index):
            return separator
    return None


def _continuation_at(command_line: str, index: int) -> str | None:
    """A backslash-line continuation starting here, or None (§4.1)."""
    for ending in _LINE_ENDINGS:
        if command_line.startswith("\\" + ending, index):
            return "\\" + ending
    return None


def _reference_at(command_line: str, index: int) -> str | None:
    """The variable reference starting at this `$`, or None (§4.2).

    `$(` is not one: an unquoted substitution is a *command*, split out
    and judged as what it is at `011`, and calling it a dynamic value
    here would leave `deploy --syntax-check $(git rev-parse HEAD).yml`
    unproven where the corpus rules it silent.
    """
    following = index + 1
    if following >= len(command_line):
        return None
    if command_line[following] == "{":
        closing = command_line.find("}", following)
        if closing < 0:
            return None
        return command_line[index : closing + 1]
    if command_line[following] not in _NAME:
        return None
    end = following
    while end < len(command_line) and command_line[end] in _NAME_REST:
        end += 1
    return command_line[index:end]


def _double_quoted(
    command_line: str, index: int, text: list[str], raw: list[str]
) -> tuple[int, bool]:
    """Consume a double-quoted run; say whether it expanded anything."""
    referenced = False
    raw.append('"')
    index += 1
    length = len(command_line)
    while index < length:
        character = command_line[index]
        if character == '"':
            raw.append('"')
            return index + 1, referenced
        if character == "\\":
            continued = _continuation_at(command_line, index)
            if continued is not None:
                raw.append(continued)
                index += len(continued)
                continue
            following = index + 1
            if (
                following < length
                and command_line[following] in _DOUBLE_QUOTE_ESCAPES
            ):
                text.append(command_line[following])
                raw.append(command_line[index : following + 1])
                index += 2
                continue
        if character == "$":
            reference = _reference_at(command_line, index)
            if reference is not None:
                referenced = True
                text.append(reference)
                raw.append(reference)
                index += len(reference)
                continue
        text.append(character)
        raw.append(character)
        index += 1
    raise _Unparseable


# --------------------------------------------------------------------
# What binds to an invocation (§4.2)


def _invocations(
    segments: list[list[_Word]], registry: Registry
) -> tuple[Invocation, ...]:
    """One invocation per segment that runs something, in order."""
    invocations: list[Invocation] = []
    context = NO_CONTEXT
    for segment in segments:
        invocation = _invocation(segment, registry, context)
        if invocation is None:
            continue
        invocations.append(invocation)
        if not context.relative_paths_unproven and _changes_directory(
            invocation
        ):
            # Lexical, not scope-aware (§3.2): everything after the `cd`
            # on the line, whatever the shell's own scoping would say.
            context = MatchContext(relative_paths_unproven=True)
    return tuple(invocations)


def _invocation(
    words: list[_Word], registry: Registry, context: MatchContext
) -> Invocation | None:
    """One segment as an invocation, or None where nothing runs."""
    assignments: list[Assigned] = []
    index = 0
    while index < len(words) and _ASSIGNMENT.match(words[index].raw):
        word = words[index]
        if _ARRAY_ASSIGNMENT.match(word.raw):
            raise _Unparseable
        name, _, text = word.text.partition("=")
        assignments.append(
            Assigned(name.rstrip("+"), Value(text, dynamic=word.dynamic))
        )
        index += 1
    if index >= len(words):
        # Assignments and nothing else: a shell variable is set and no
        # command runs. The `export` spelling, which outlives the
        # segment, is §4.2's deferral and `030`'s.
        return None

    command = words[index]
    entry, by_path = _recognized(command.text, registry)
    options, flags, operands, malformed = _bound(words[index + 1 :], entry)
    return Invocation(
        name=command.text,
        entry=entry,
        assignments=tuple(assignments),
        options=options,
        flags=flags,
        operands=operands,
        context=context,
        dynamic_name=command.dynamic,
        doubts=_doubts(
            entry=entry,
            values=_matched(assignments, options, flags, operands),
            malformed=malformed,
            unresolved=by_path
            and not command.text.startswith("/")
            and context.relative_paths_unproven,
        ),
    )


def _recognized(name: str, registry: Registry) -> tuple[Entry | None, bool]:
    """The entry this command word reaches, and whether by path (§4.2).

    A path declaration is tried first and is more specific than a
    basename one, so a grant written for `tools/deploy.py` cannot be
    claimed by a file of that name anywhere else. Everything else is the
    whole basename — `git` and `/usr/bin/git` are one tool, `git-crypt`
    is not git — which `Registry.lookup` already holds, aliases and all.
    """
    if "/" in name:
        found = registry.lookup_path(name)
        if found is not None:
            return found, True
    return registry.lookup(os.path.basename(name)), False


def _bound(
    words: list[_Word], entry: Entry | None
) -> tuple[tuple[Flag, ...], tuple[Flag, ...], tuple[Value, ...], bool]:
    """The options, flags and operands of one command (§4.2)."""
    options: list[Flag] = []
    flags: list[Flag] = []
    operands: list[Value] = []
    malformed = False
    subcommand_reached = False
    past_marker = False
    index = 0
    while index < len(words):
        word = words[index]
        index += 1
        if past_marker:
            operands.append(word.value())
            continue
        if word.text == "--":
            # Structure, and matchable structure: some rules key on it
            # as the explicit "the operand is a path" signal (§4.2).
            flags.append(Flag("--"))
            past_marker = True
            continue
        if not _flag_shaped(word.text):
            operands.append(word.value())
            subcommand_reached = True
            continue
        name, attached = _named(word)
        table, defaults, target = _namespace(entry, name, subcommand_reached)
        target_list = options if target else flags
        if attached is not None:
            target_list.append(Flag(name, attached))
            continue
        arity = table.get(name, Arity.BARE)
        if arity is Arity.VALUE:
            if index < len(words):
                target_list.append(Flag(name, words[index].value()))
                index += 1
            else:
                # Nothing to take: the invocation is malformed, which is
                # unproven and not safe (§4.2). The segment ends here, so
                # the next command's word is never eaten as a value.
                target_list.append(Flag(name))
                malformed = True
        elif arity is Arity.OPTIONAL_VALUE:
            if index < len(words) and not _flag_shaped(words[index].text):
                target_list.append(Flag(name, words[index].value()))
                index += 1
            else:
                default = defaults.get(name)
                target_list.append(
                    Flag(name, None if default is None else Value(default))
                )
        else:
            target_list.append(Flag(name))
    return tuple(options), tuple(flags), tuple(operands), malformed


def _flag_shaped(text: str) -> bool:
    """Whether this token reads as an option rather than an operand."""
    return text.startswith("-") and text != "-"


def _named(word: _Word) -> tuple[str, Value | None]:
    """A flag's name, and the value attached with `=` if there was one.

    Attached, the value is present whatever follows, so no arity has a
    judgement to make about it — including the empty `--flag=`, which is
    the empty string said explicitly and never a value-optional flag's
    declared default (`D-039`).
    """
    name, sign, attached = word.text.partition("=")
    if not sign:
        return word.text, None
    return name, Value(attached, dynamic=word.dynamic)


def _namespace(
    entry: Entry | None, name: str, subcommand_reached: bool
) -> tuple[Mapping[str, Arity], Mapping[str, str], bool]:
    """Which of §4.2's two namespaces this dashed token belongs to.

    Options are the ones declared *and* written before the subcommand;
    everything else is a flag, an undeclared token included, which is
    then presumed bare. Presuming otherwise would move the subcommand
    out of reach of every rule written for it.
    """
    if entry is None:
        return {}, {}, False
    if not subcommand_reached and name in entry.options:
        return entry.options, entry.option_defaults, True
    return entry.flags, entry.flag_defaults, False


def _matched(
    assignments: list[Assigned],
    options: tuple[Flag, ...],
    flags: tuple[Flag, ...],
    operands: tuple[Value, ...],
) -> list[Value]:
    """Every value a matcher could be asked about on this invocation."""
    values = [assigned.value for assigned in assignments]
    values.extend(
        flag.value for flag in (*options, *flags) if flag.value is not None
    )
    values.extend(operands)
    return values


def _readable(value: Value) -> bool:
    """Whether a matcher can read this as the plain word grants prove."""
    if value.dynamic:
        return False
    return not any(
        character.isspace() or character in _GLOB for character in value.text
    )


def _doubts(
    *,
    entry: Entry | None,
    values: list[Value],
    malformed: bool,
    unresolved: bool,
) -> tuple[Doubt, ...]:
    """What reading could not establish, in a fixed order (§3.3)."""
    doubts: list[Doubt] = []
    gated = entry is not None and entry.gated
    if gated and not all(_readable(value) for value in values):
        doubts.append(Doubt.UNREADABLE)
    if malformed:
        doubts.append(Doubt.MALFORMED)
    if unresolved:
        doubts.append(Doubt.UNRESOLVED_PATH)
    return tuple(doubts)


def _changes_directory(invocation: Invocation) -> bool:
    """Whether this invocation is the `cd` that poisons what follows.

    Textual, and by basename like any other recognition: `cd` is a shell
    builtin, so no registration can ever stand for it.
    """
    return os.path.basename(invocation.name) == "cd"


# --------------------------------------------------------------------
# The fallback (§4.1)


def _speaking(command_line: str, registry: Registry) -> tuple[str, ...]:
    """The speaking tools named on a line nothing could parse (§4.1).

    A raw scan over whitespace-delimited words, compared by basename so
    a path spelling does not evade it, and it deliberately over-reads:
    with no parse there is nothing to say which word was a command, so
    `ls ../stubtool` counts. That is why it fires only here — on a
    *parsed* line §4.3 forbids the scan outright, because a tool's name
    is also an ordinary word.

    Names are reported once and in a stable order: it is printed, and
    `009` will cite it.
    """
    found = {
        entry.name
        for entry in (
            registry.lookup(os.path.basename(word))
            for word in command_line.split()
        )
        if entry is not None and entry.speaking
    }
    return tuple(sorted(found))
