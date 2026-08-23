"""The config-facing API — what an operator writes (§5.2, §5.3, §3.5).

This module is the stability boundary of §3.5: these names, their
arguments and their meanings are what a project's configuration is
written against, versioned semver on the plugin. Engine internals move
freely beneath them; this surface breaks only on a major version, which
is why the configuration declares the generation it was written for and
why the engine refuses a generation it does not speak rather than
guessing at one.

**It is read by people who do not write Python** (§5.3). A configuration
is the document an operator reviews when they decide what their boundary
is, so the shapes here are declarations: nouns for what a tool is, verbs
for what a verdict does, one keyword per idea, and a mandatory reason on
everything that can refuse — an empty reason is a liveness failure
(§8.2), not a style lapse.

The whole surface a configuration needs is importable from here,
matchers included, so a config opens with one import rather than three.

**A declaration returns nothing.** Calling `tool(...)` records a tool in
the collection being loaded; the composed result is a `Registry`
(`registry.py`), and that — never a value handed back here — is what
composition, shadowing and inspection work on. The alternative, objects
the config wires together itself, would put the composition order in the
operator's hands one call at a time; §3.4 wants it in one declared
order.

Two capabilities of §5.2 are deliberately absent until the behaviour
they configure ships: secure mode with its global default verdict, and
§7.2's failure-policy dial. Both are top-level declarations like
`api_generation`, so both are additions rather than changes — nothing
here is shaped in a way that precludes them.
"""

from __future__ import annotations

import enum
import os
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Union

from .errors import ConfigurationError
from .matchers import (
    Matcher,
    all_of,
    any_of,
    matching,
    one_of,
    path_matching,
    path_under,
    predicate,
)
from .verdicts import Verdict

#: The configuration's whole vocabulary, and nothing else. §3.5 makes
#: this surface the stability boundary the plugin versions on, so a
#: name here is a name promised not to break — which is why the
#: module's types (`Matcher`, `Source`, `Rule`) are absent: they are
#: what the engine passes around, not what a configuration writes.
__all__ = [
    # Matchers, re-exported so a configuration has one import line.
    "all_of",
    "any_of",
    "matching",
    "one_of",
    "path_matching",
    "path_under",
    "predicate",
    # The generation declaration.
    "api_generation",
    # Flag arities.
    "bare",
    "takes_value",
    "may_take_value",
    # Conditions.
    "flag",
    "any_flag",
    "env",
    "option",
    "every_operand",
    "at_least_one_operand",
    "no_operands",
    # Scopes.
    "anywhere",
    "host_only",
    "inside",
    # Verdicts, as declarations and as case expectations.
    "deny",
    "ask",
    "allow",
    "silent",
    "grant",
    "DENY",
    "ASK",
    "ALLOW",
    "SILENT",
    # Assignments.
    "accounted",
    "benign_assignments",
    # Handoffs.
    "handoff",
    "option_handoff",
    # Cases.
    "case",
    "cases",
    # Entities.
    "tool",
    "wrapper",
    "shell",
    "interpreter",
    "redirections",
    # Composition.
    "amend",
    "drop",
    "use",
]


# --------------------------------------------------------------------
# The generation declaration (§3.5)


def api_generation(generation: int) -> None:
    """Which generation of this API the configuration was written for.

        api_generation(1)

    Put it at the top of your configuration; the scaffold writes it for
    you. It tells the engine which version of this vocabulary the file
    was written against, so an update that changes the vocabulary can
    keep reading your file — or refuse it and point you at the
    migration, rather than guess and quietly misread your boundary.

    A configuration without it does not load.
    """
    open_recording = recording("api_generation")
    if open_recording.generation is not None:
        raise ConfigurationError(
            "api_generation() is declared twice: a configuration says "
            "once which contract it was written against."
        )
    if isinstance(generation, bool) or not isinstance(generation, int):
        raise ConfigurationError(
            f"api_generation({generation!r}) takes a whole number."
        )
    open_recording.generation = generation


# --------------------------------------------------------------------
# Flag arities (§4.2)


class Arity(enum.Enum):
    """How much of the line a flag takes with it (§4.2)."""

    BARE = "bare"
    VALUE = "value-required"
    OPTIONAL_VALUE = "value-optional"


@dataclass(frozen=True)
class FlagSet:
    """Flags sharing one arity, as one declaration.

    `default` is what a value-optional flag means when used bare
    (`D-039`), and is None on every other arity: the fact belongs to
    the tool, so it is declared once beside the arity rather than
    restated at each rule that reads the value.
    """

    arity: Arity
    names: Sequence[str]
    default: str | None = None


def bare(*names: str) -> FlagSet:
    """Declare flags that take no value.

        flags=[bare("--force", "--dry-run")]

    Only needed on a gated tool, where every flag must be declared. A
    flag you never mention is assumed to take nothing anyway.
    """
    return _flag_set(Arity.BARE, names)


def takes_value(*names: str) -> FlagSet:
    """These flags take a value, as `--flag=v` or in the next token.

        flags=[takes_value("-i", "--inventory", "--tags")]

    Declare **every** one of these. A value-taking flag frisk does not
    know about lets its value look like a flag of the command, and
    `deploy.yml -i --syntax-check` then reads as a parse-only run when
    it is a real deploy — the one direction that fails toward letting
    something through.
    """
    return _flag_set(Arity.VALUE, names)


def may_take_value(*names: str, default: str | None = None) -> FlagSet:
    """These flags take a value unless the next token looks like a flag.

        flags=[may_take_value("--argument", default="check")]

    For a flag that takes a value only when the next token is not
    itself a flag — some hand-rolled tools accept both
    `--argument custom` and a bare `--argument`. Reading one as always
    taking a value swallows the very token that decides the verdict.

    `default` is what the tool itself uses when the flag is bare. Give
    it and the two spellings become one case: with
    `may_take_value("--argument", default="check")`, the condition
    `flag("--argument", one_of("check"))` matches `--argument` and
    `--argument check` alike, while `one_of("full", "deep")` picks out
    the others. frisk cannot know your tool's default; you can, and
    this is where you say it.

    Leave it out and a bare use has no value to test, so a condition on
    that value can be neither proven nor ruled out. It comes back
    unprovable, which sends the verdict to the stricter side rather
    than letting a rule go quiet about a flag it could not read.
    """
    return _flag_set(Arity.OPTIONAL_VALUE, names, default)


# --------------------------------------------------------------------
# Conditions (§5.2)
#
# A condition constrains one invocation. Where a rule or a grant takes
# several, they are given as a sequence and all must hold: a rule
# needing "either of two different kinds" is two rules with the same
# verdict, which the order-free ranking of §3.2 makes equivalent. Or
# over values of one kind lives in the matchers (`any_of`) and in
# `any_flag`.


class Condition:
    """A constraint on an invocation, and the phrase that names it."""

    def describe(self) -> str:
        raise NotImplementedError

    def matchers(self) -> Sequence[Matcher]:
        """The value matchers inside this condition, if any.

        `frisk registry --value` walks these to show what each matcher
        answers for a value, which is how composition is inspected
        (§3.4) without a command line to judge yet.
        """
        raise NotImplementedError


#: What a rule or grant accepts for `when`.
When = Union[Condition, Sequence[Condition], None]


@dataclass(frozen=True)
class FlagUsed(Condition):
    """`flag(...)` — an operative flag, optionally carrying a value."""

    name: str
    value: Matcher | None = None

    def describe(self) -> str:
        if self.value is None:
            return f"flag {self.name}"
        return f"flag {self.name} is {self.value.describe()}"

    def matchers(self) -> Sequence[Matcher]:
        return () if self.value is None else (self.value,)


@dataclass(frozen=True)
class AnyFlagUsed(Condition):
    """`any_flag(...)` — an or over flag names, not over conditions."""

    names: Sequence[str]

    def describe(self) -> str:
        return "any flag in " + ", ".join(self.names)

    def matchers(self) -> Sequence[Matcher]:
        return ()


@dataclass(frozen=True)
class EnvSet(Condition):
    """`env(...)` — an assignment in front of the command."""

    name: str
    value: Matcher | None = None

    def describe(self) -> str:
        if self.value is None:
            return f"environment {self.name}"
        return f"environment {self.name} is {self.value.describe()}"

    def matchers(self) -> Sequence[Matcher]:
        return () if self.value is None else (self.value,)


@dataclass(frozen=True)
class OptionUsed(Condition):
    """`option(...)` — an option ahead of the subcommand."""

    name: str
    value: Matcher | None = None

    def describe(self) -> str:
        if self.value is None:
            return f"option {self.name}"
        return f"option {self.name} is {self.value.describe()}"

    def matchers(self) -> Sequence[Matcher]:
        return () if self.value is None else (self.value,)


@dataclass(frozen=True)
class EveryOperand(Condition):
    """`every_operand(...)` — and at least one, by §3.2."""

    value: Matcher

    def describe(self) -> str:
        return f"every operand is {self.value.describe()}"

    def matchers(self) -> Sequence[Matcher]:
        return (self.value,)


@dataclass(frozen=True)
class AtLeastOneOperand(Condition):
    """`at_least_one_operand(...)` — the other quantifier."""

    value: Matcher

    def describe(self) -> str:
        return f"at least one operand is {self.value.describe()}"

    def matchers(self) -> Sequence[Matcher]:
        return (self.value,)


@dataclass(frozen=True)
class NoOperands(Condition):
    """`no_operands()` — the empty case, spelled deliberately."""

    def describe(self) -> str:
        return "no operands"

    def matchers(self) -> Sequence[Matcher]:
        return ()


def flag(name: str, value: Matcher | None = None) -> Condition:
    """This flag is operative on the invocation, optionally with a value.

        deny("push", when=flag("--force"), reason=…)
        ask("apply", when=flag("--mode", one_of("prod")), reason=…)

    The flag must be *operative* — a real flag of this command, not a
    token that another flag swallowed as its value. This is what makes
    `deploy.yml -i --syntax-check` a real deploy: `--syntax-check` is
    `-i`'s inventory string there, so a rule about it does not fire.
    """
    return FlagUsed(name, value)


def any_flag(*names: str) -> Condition:
    """True when at least one of these flags is used.

    deny("push", when=any_flag("-f", "--force", "--mirror"), reason=…)
    """
    if not names:
        raise ConfigurationError(
            "any_flag() names the flags it is an or over."
        )
    return AnyFlagUsed(tuple(names))


def env(name: str, value: Matcher | None = None) -> Condition:
    """True when this variable is set in front of the command.

        deny(when=env("GIT_SSH_COMMAND"), reason=…)
        ask("apply", when=env("TARGET", one_of("prod")), reason=…)

    Matches `NAME=value cmd …`, the shape that can change what a
    command does without appearing in its flags. Names are the shell's,
    so matching is case-sensitive and a lower-case name is a variable
    too.
    """
    return EnvSet(name, value)


def option(name: str, value: Matcher | None = None) -> Condition:
    """True when an option *before* the subcommand was used.

        ask("push", when=option("-C", path_under("/srv")), reason=…)

    For the options a tool takes ahead of its subcommand — `git -C dir
    push` — which the tool must declare in `options=`. This is how
    "pushing is fine, but only for repositories under this directory"
    is said.
    """
    return OptionUsed(name, value)


def every_operand(value: Matcher) -> Condition:
    """Every operand satisfies this matcher — and there is at least one.

        grant("clean", when=every_operand(path_under("/tmp")), reason=…)

    Operands are what is left after the subcommand and the flags — the
    files and names a command acts on.

    **A command with no operands does not satisfy this.** `clean` with
    nothing after it has not shown what it would clean, so the grant
    does not release it. If you mean to allow that, say so with
    `no_operands()`.
    """
    return EveryOperand(value)


def at_least_one_operand(value: Matcher) -> Condition:
    """True when at least one operand matches.

    deny(when=at_least_one_operand(matching(r"^delete$")), reason=…)
    """
    return AtLeastOneOperand(value)


def no_operands() -> Condition:
    """True when the command has no operands at all.

        grant("status", when=no_operands(), reason=…)

    The deliberate spelling for the empty case, which `every_operand`
    refuses.
    """
    return NoOperands()


# --------------------------------------------------------------------
# Where a declaration was written


@dataclass(frozen=True)
class Source:
    """The layer a declaration came from, and the line that wrote it.

    Both halves are needed by §3.4's inspection requirement: the layer
    is what decided a conflict, the file and line are what an operator
    opens to change it.

    `file` is a string rather than a `Path`, and the invariant its name
    promises is kept by its producer rather than by its type. Nothing
    here ever manipulates the path — the two consumers both render it,
    `frisk registry` printing `starter.py:12` and §6.2's citation
    naming where a rule was written — while a `Source` is built for
    every declaration on every config load, which is the hook's hot
    path (§4.5). Paying a `Path` parse per declaration to store
    something only ever printed is loss with nothing on the other side
    to earn it back.

    So the guarantee is structural: `Source` has exactly one producer,
    the composition machinery, which takes the value from the
    interpreter's own record of the file it is executing. It is never
    constructed by a configuration, and `__post_init__` holds the one
    property that makes it a path rather than a string: absolute, so
    that rendering it relative to the configuration's directory is
    well defined without consulting the filesystem, which §4.5 forbids.
    """

    layer: str
    file: str
    line: int

    def __post_init__(self) -> None:
        if not os.path.isabs(self.file):
            raise ValueError(
                f"a source file must be absolute, and '{self.file}' is "
                "not: rendering it relative to the configuration's "
                "directory would otherwise depend on the process's "
                "working directory."
            )


# --------------------------------------------------------------------
# Scopes (§4.3, §5.2)


@dataclass(frozen=True)
class Anywhere:
    """Wherever the invocation is found. The default."""

    def describe(self) -> str:
        return "anywhere"


@dataclass(frozen=True)
class HostOnly:
    """Outside every handoff."""

    def describe(self) -> str:
        return "on the host only"


@dataclass(frozen=True)
class Inside:
    """Inside one named handoff, and nowhere else."""

    handoff: str

    def describe(self) -> str:
        return f"inside {self.handoff}"


#: Where a rule or grant applies (§4.3, §5.2). A handed-off command
#: runs in a different world than the host's, and policy may
#: legitimately differ — `docker run image cmd --dangerous` and a bare
#: `cmd --dangerous` need not share a verdict.
#:
#: Three states and no fourth: §5.2 names the host and a named handoff,
#: and a handed-off command is by definition not on the host. Three
#: types rather than one carrying a name *and* a host flag, so "inside
#: and on the host" cannot be written down, and so the handoff's name
#: is reachable only where there is one.
Scope = Union[Anywhere, HostOnly, Inside]

#: The default: the rule applies wherever the invocation is found.
anywhere = Anywhere()

#: Only outside any handoff.
host_only = HostOnly()


def inside(handoff_name: str) -> Inside:
    """Confine a rule or grant to one handoff.

        ask("wipe", reason=…, scope=inside("docker run"))

    A command inside a container runs in a different world than the
    same command on the host, and may deserve a different answer. Use
    `host_only` for the other side.
    """
    if not handoff_name.strip():
        raise ConfigurationError(
            "inside() names the handoff it confines a rule to."
        )
    return Inside(handoff_name)


# --------------------------------------------------------------------
# Rules, grants and defaults (§3.2, §5.3)


@dataclass(frozen=True)
class Rule:
    """One declared verdict, with what it decided on and why."""

    verdict: Verdict
    subcommand: Sequence[str] = ()
    conditions: Sequence[Condition] = ()
    reason: str = ""
    label: str | None = None
    scope: Scope = anywhere
    target: Matcher | None = None
    #: Where the operator wrote it. Filled by the constructors below,
    #: never by a configuration: §3.4's inspection requirement is what
    #: needs it, and a rule can outlive the layer its entry came from.
    declared_at: Source | None = None


@dataclass(frozen=True)
class Grant:
    """One proven-safe shape. A grant that holds is silence (§3.2)."""

    subcommand: Sequence[str] = ()
    conditions: Sequence[Condition] = ()
    reason: str = ""
    label: str | None = None
    scope: Scope = anywhere
    declared_at: Source | None = None


def deny(
    subcommand: str = "",
    *,
    when: When = None,
    reason: str = "",
    label: str | None = None,
    scope: Scope = anywhere,
    target: Matcher | None = None,
) -> Rule:
    """Refuse: an act with no authorized use.

        deny("stash drop", reason="Dropping a stash cannot be undone.")

    The subcommand is written as it is typed, spaces and all —
    `deny("buildx imagetools create")`. Leave it out and the rule is
    about every use of the tool.

    `reason` is required and is shown to whoever meets the refusal, so
    write the objection *and* the way forward. `label` names the rule
    for `amend`; `scope` confines it to the host or to one handoff.
    """
    return _verdict(
        Verdict.DENY,
        subcommand,
        when,
        reason,
        label,
        scope,
        target,
        _source(),
    )


def ask(
    subcommand: str = "",
    *,
    when: When = None,
    reason: str = "",
    label: str | None = None,
    scope: Scope = anywhere,
    target: Matcher | None = None,
) -> Rule:
    """Ask: stop and let the user decide.

        ask("push", reason="A push publishes work to a shared remote.")

    For acts that are legitimate but should not happen unnoticed —
    anything that reaches outside the machine, or destroys work.
    Arguments are `deny`'s.
    """
    return _verdict(
        Verdict.ASK,
        subcommand,
        when,
        reason,
        label,
        scope,
        target,
        _source(),
    )


def allow(
    subcommand: str = "",
    *,
    when: When = None,
    reason: str = "",
    label: str | None = None,
    scope: Scope = anywhere,
    target: Matcher | None = None,
) -> Rule:
    """Allow: let it run without asking.

    Exceptional, and hedged: an allow anywhere in a command line is
    withheld if anything else in that line asks or denies. Use it for a
    shape you have proven safe and meet constantly; prefer a `grant` on
    a gated tool, which says the same thing without waiving anything.
    Arguments are `deny`'s.
    """
    return _verdict(
        Verdict.ALLOW,
        subcommand,
        when,
        reason,
        label,
        scope,
        target,
        _source(),
    )


def silent(
    subcommand: str = "",
    *,
    when: When = None,
    reason: str = "",
    label: str | None = None,
    scope: Scope = anywhere,
) -> Rule:
    """No opinion: hand the call to the permission rules and mode.

        tool("git", default=silent())

    frisk says nothing and your normal permission rules decide. This is
    what happens anyway where no rule matches, so declare it only when
    you mean it — a stated silence is deliberate where an absent rule
    is merely absent. The one verdict that needs no reason.
    """
    return _verdict(
        Verdict.SILENT,
        subcommand,
        when,
        reason,
        label,
        scope,
        None,
        _source(),
    )


def grant(
    subcommand: str = "",
    *,
    when: When = None,
    reason: str = "",
    label: str | None = None,
    scope: Scope = anywhere,
) -> Grant:
    """A shape proven safe, on a tool that is dangerous by default.

        grant(when=any_flag("--check", "--dry-run"), reason=…)
        grant("clean", when=every_operand(path_under("/tmp")), reason=…)

    For a tool that is dangerous by default: instead of listing what to
    refuse, you list the shapes you can prove are safe, and everything
    else gets the tool's default verdict.

    Declaring a grant **closes the tool's flag list**: from then on
    every flag it may carry has to appear in `flags=`, and a command
    carrying one you did not declare is unprovable rather than
    granted. That is the point — a flag nobody thought about can only
    make the answer stricter, never looser.

    A rule still wins over a grant. `deny` on a subcommand refuses it
    even where a grant would have released it.
    """
    path = tuple(subcommand.split())
    return Grant(
        subcommand=path,
        conditions=_conditions(when),
        reason=_reasoned(_subject("grant", path), reason),
        label=label,
        scope=scope,
        declared_at=_source(),
    )


#: Verdicts as values, for a case's expectation. Distinct from the
#: constructors above: `case("git push --force", DENY)` states an
#: outcome, `deny("push", …)` declares a rule.
DENY = Verdict.DENY
ASK = Verdict.ASK
ALLOW = Verdict.ALLOW
SILENT = Verdict.SILENT


# --------------------------------------------------------------------
# Assignments (§3.2)


@dataclass(frozen=True)
class Assignment:
    """An environment assignment a declaration accounts for."""

    name: str | Matcher
    value: Matcher | None = None


def accounted(name: str | Matcher, value: Matcher | None = None) -> Assignment:
    """This assignment is expected, optionally only with a value.

        tool("git", assignments=[accounted("GIT_PAGER", one_of("cat"))])

    Environment variables in front of a command can change what it
    does without showing up in its flags, so for every tool you
    register, one you have not accounted for **asks**. List the ones
    your project sets, with a matcher where only some values are fine.

    The name can be a matcher too, for a family:
    `accounted(matching(r"^LC_[A-Z_]+$"))`.
    """
    if isinstance(name, str):
        if not name.strip():
            raise ConfigurationError(
                "accounted() names the variable it expects."
            )
    elif not isinstance(name, Matcher):
        raise ConfigurationError(
            "accounted() takes a variable name, or a matcher for a "
            "family of them."
        )
    return Assignment(name=name, value=value)


def benign_assignments(*declared: Assignment | Drop) -> None:
    """The assignments no registered tool has to account for (§3.2).

        benign_assignments(accounted("PROJECT_LOCALE"), drop("TZ"))

    Variables no tool has to account for. frisk ships the display and
    locale ones — `LC_*`, `LANG`, `TZ`, `NO_COLOR` — so that
    `LC_ALL=C git status` does not ask in every project. Add your own,
    or drop one you would rather see.

    **Adding to this list is a decision to stop reading a variable at
    all**, everywhere. Keep it to variables that cannot change what
    runs: `GIT_SSH_COMMAND` and its many siblings are exactly what the
    accounting exists to catch.
    """
    open_recording = recording("benign_assignments")
    _typed(declared, (Assignment,), what="assignment", drops=True)
    open_recording.current.benign.extend(declared)


# --------------------------------------------------------------------
# Handoffs (§4.3)


@dataclass(frozen=True)
class SubcommandHandoff:
    """`docker run IMAGE cmd` — the tool's own subcommand hands over."""

    subcommand: Sequence[str] = ()
    keeps_operands: int = 0
    flags: Sequence[FlagSet] = field(default_factory=tuple)


@dataclass(frozen=True)
class OptionHandoff:
    """`find . -exec rm {} +` — an option opens it, a terminator ends it."""

    option: str = ""
    terminated_by: Sequence[str] = ()


#: What `tool(handoffs=…)` accepts. §4.3 asks for two shapes, and they
#: share nothing but the sentence that names them: a subcommand handoff
#: keeps operands of its own and declares the options it takes values
#: for, while an option-introduced one begins immediately and ends at a
#: terminator. Two constructors rather than one with a mode, so neither
#: carries an argument the other's shape makes meaningless — and no
#: common base, since the engine reaches them by different keys: one by
#: the subcommand path, the other by an option token anywhere on the
#: line.
Handoff = Union[SubcommandHandoff, OptionHandoff]


def handoff(
    subcommand: str,
    *,
    keeps_operands: int = 0,
    flags: Sequence[FlagSet] = (),
) -> SubcommandHandoff:
    """Declare a subcommand where the inner command begins.

        tool("docker", handoffs=[handoff("run", keeps_operands=1)])

    Some subcommands stop describing the tool and run something else:
    after `docker run alpine`, what follows is a command in its own
    right and is judged as one. Declare where that happens.

    `keeps_operands` is how many operands belong to the tool first —
    one for the image, service or container name. That name is never
    read as a program, however it is spelled.

    Declare the handoff's own value-taking options in `flags=`: finding
    where the inner command starts depends on knowing which tokens were
    swallowed as values.
    """
    path = tuple(subcommand.split())
    if not path:
        raise ConfigurationError(
            "handoff() names the subcommand that hands over."
        )
    if keeps_operands < 0:
        raise ConfigurationError(
            f"handoff('{subcommand}') keeps {keeps_operands} operands."
        )
    _typed(flags, (FlagSet,), what="flag", drops=False)
    return SubcommandHandoff(
        subcommand=path,
        keeps_operands=keeps_operands,
        flags=tuple(flags),
    )


def option_handoff(
    option: str, *, terminated_by: Sequence[str]
) -> OptionHandoff:
    """Declare a flag-introduced inner command, closed by a terminator.

        tool("find", handoffs=[
            option_handoff("-exec", terminated_by=[";", "+"]),
        ])

    For the shape `find . -name '*.log' -exec rm -rf {} +`, where the
    inner command sits in the middle of the line, opened by an option
    and closed by a terminator. The terminator is required: without it
    nothing says where the inner command ends and the tool's own
    operands resume.
    """
    if not option.strip():
        raise ConfigurationError(
            "option_handoff() names the option that opens the inner command."
        )
    if not terminated_by:
        raise ConfigurationError(
            f"option_handoff('{option}') needs a terminator: without "
            "one, nothing says where the inner command ends and the "
            "tool's own operands resume."
        )
    return OptionHandoff(option=option, terminated_by=tuple(terminated_by))


# --------------------------------------------------------------------
# Cases (§5.2, §8.2)


@dataclass(frozen=True)
class Case:
    """A command line, and the verdict frisk must return for it."""

    command: str
    expect: Verdict


def case(command: str, expect: Verdict) -> Case:
    """A project's own test case, sited beside the rule it proves.

        tool("git", rules=[…], cases=[case("git push --force", DENY)])

    Your own tests: a command line, and what frisk must answer for it.
    `frisk selftest` runs them, and requires every rule and grant you
    declared to be reached by at least one — a rule no case reaches is
    either dead or untested, and from outside those look the same.

    Write them beside the rule they prove. Use `cases(…)` at the top
    level for one that belongs to no single tool.
    """
    if not isinstance(command, str) or not command.strip():
        raise ConfigurationError("case() takes the command line to judge.")
    if not isinstance(expect, Verdict):
        raise ConfigurationError(
            f"case({command!r}, ...) states the verdict frisk must "
            "return — DENY, ASK, ALLOW or SILENT — and a rule is not "
            "one of them."
        )
    return Case(command=command, expect=expect)


def cases(*declared: Case) -> None:
    """Declare cases that belong to no single tool.

        cases(case("sudo git push --force", DENY))

    For a case about a whole line — a wrapper walk, a substitution,
    two commands combining — where no single tool is the subject.
    """
    open_recording = recording("cases")
    _typed(declared, (Case,), what="case", drops=False)
    open_recording.current.cases.extend(declared)


# --------------------------------------------------------------------
# Entities (§3.4, §4.2, §4.3)


def tool(
    name: str = "",
    *,
    aliases: Sequence[str] = (),
    default: Rule | None = None,
    flags: Sequence[FlagSet] = (),
    options: Sequence[FlagSet] = (),
    assignments: Sequence[Assignment] = (),
    rules: Sequence[Rule] = (),
    grants: Sequence[Grant] = (),
    handoffs: Sequence[Handoff] = (),
    closed_world: bool | None = None,
    cases: Sequence[Case] = (),
) -> None:
    """Register a tool: what it is called, what it takes, what it may do.

        tool("git", rules=[deny("push", …)])
        tool("tools/deploy.py", default=ask(reason=…))

    **The name says which kind it is, the way a shell does.** No
    separator means a command name, matched whole: `git` also matches
    `/usr/bin/git`, and never matches `git-crypt`. A separator means a
    file in your project: `tools/deploy.py`, matched however it is
    spelled, and `./deploy.py` for a script at the project root — the
    same `./` you would need to run it.

    An absolute path is refused: your configuration is committed and
    travels with the project, and `/usr/bin/git` here is
    `/opt/homebrew/bin/git` on someone else's machine. Declare the
    command name instead.

    `aliases` are other names for the same tool — drop-in replacements
    such as `podman` for `docker`.

    `flags` tells the parser which flags take a value, so that a value
    is never mistaken for a flag. On a gated tool it does more: it
    becomes the complete list of flags the tool may carry, and anything
    outside it makes the command unprovable.

    `options` are the options a tool takes *before* its subcommand.
    Without them `git -C dir push` reads as a `git` with two operands
    and no push rule fires.

    `closed_world` closes the tool's flag list without granting
    anything. You rarely need it: declaring any grant closes the world
    already. Leave it unset unless you mean to say so explicitly — and
    note that it cannot be set to `False` while a grant stands, since a
    grant an unknown flag could escape proves nothing.
    """
    _entity(
        "tool",
        name,
        _source(),
        aliases=aliases,
        default=default,
        flags=flags,
        options=options,
        assignments=assignments,
        rules=rules,
        grants=grants,
        handoffs=handoffs,
        closed_world=closed_world,
        cases=cases,
    )


def wrapper(
    name: str = "",
    *,
    aliases: Sequence[str] = (),
    flags: Sequence[FlagSet] = (),
    keeps_operands: int = 0,
    assignments: Sequence[Assignment] = (),
    operands_from_stdin: bool = False,
    default: Rule | None = None,
    rules: Sequence[Rule] = (),
) -> None:
    """A program whose job is to run another program (§3.4, §4.3).

        wrapper("timeout", flags=[takes_value("-s")], keeps_operands=1)

    A program whose job is to run another one. frisk steps over it and
    judges what it runs, so `sudo git push --force` is a denied push.

    Declare the options that take a value, and `keeps_operands` for
    operands the wrapper takes for itself — `timeout 30 cmd` keeps the
    duration. Options you do not declare are assumed to take nothing;
    get that wrong and frisk may lose track of the inner command, which
    makes it ask rather than stay quiet.

    `operands_from_stdin` is the `… | xargs -0 rm` shape: the command
    is visible but what it acts on arrives on stdin, so no rule about
    its operands can be proven.

    A wrapper can carry rules and a default of its own. That is how you
    gate everything an unknown runner runs: declare it with an `ask`
    default.
    """
    _entity(
        "wrapper",
        name,
        _source(),
        aliases=aliases,
        default=default,
        flags=flags,
        assignments=assignments,
        rules=rules,
        keeps_operands=keeps_operands,
        operands_from_stdin=operands_from_stdin,
    )


def shell(
    name: str = "",
    *,
    aliases: Sequence[str] = (),
    flags: Sequence[FlagSet] = (),
    joins_operands: bool = False,
) -> None:
    """A shell: its `-c` payload is a command line and is re-analyzed.

        shell("bash")
        shell("eval", joins_operands=True)

    A shell's `-c` argument is a command line, so it is read as one and
    everything inside it is judged — combined spellings such as `-lc`
    included. `bash -c 'git push --force'` denies exactly as the bare
    command would.

    A shell reached with no payload and no script file — `curl url |
    sh` — is running something the line cannot show, and asks.

    `joins_operands` is for `eval`, which has no payload flag: it joins
    its arguments and runs the result. With nothing to join it is
    running nothing at all, so a bare `eval` says nothing rather than
    asking.
    """
    _entity(
        "shell",
        name,
        _source(),
        aliases=aliases,
        flags=flags,
        joins_operands=joins_operands,
    )


def interpreter(
    name: str = "",
    *,
    aliases: Sequence[str] = (),
    flags: Sequence[FlagSet] = (),
) -> None:
    """An interpreter walked to the file it runs (§4.2).

        interpreter("python3", flags=[takes_value("-c", "-m")])

    A tool run through an interpreter is still that tool: if you have
    registered `tools/deploy.py`, then `python3 tools/deploy.py` is
    judged by that registration.

    Program text in another language is never read as shell — guessing
    at another grammar produces false refusals — so a `-c` or `-e`
    payload is left alone. Declare whatever takes a value, or the walk
    will mistake that value for the script.
    """
    _entity(
        "interpreter",
        name,
        _source(),
        aliases=aliases,
        flags=flags,
    )


def redirections(*rules: Rule) -> None:
    """Rules on where a command's output lands (§4.3).

        redirections(
            ask(target=path_under(".claude"), reason="…"),
        )

    `> file` can destroy a file by truncating it, or write somewhere
    nothing else on the line writes — `echo x > .claude/settings.json`
    carries all its danger in the redirection. These rules match the
    target rather than the command.

    Redirections say nothing by default: `2>/dev/null` is everywhere,
    and only your rules give any of them meaning.
    """
    open_recording = recording("redirections")
    for rule in rules:
        if not isinstance(rule, Rule):
            raise ConfigurationError(f"{rule!r} is not a verdict declaration.")
        if rule.target is None:
            raise ConfigurationError(
                "a redirection rule needs target=: these rules match "
                "where the output lands rather than the command."
            )
    open_recording.current.redirections.extend(rules)


# --------------------------------------------------------------------
# Composition (§3.4)


@dataclass(frozen=True)
class Drop:
    """Names to remove from the list this sits in."""

    names: Sequence[str]


def drop(*names: str) -> Drop:
    """Remove these from the list this appears in (§3.4).

        amend("sudo", flags=[drop("-u"), takes_value("--prompt-file")])
        amend("git", rules=[drop("forced push")])

    Put it in the list you are taking something out of: a flag name in
    `flags`, a label in `rules` and `grants`, an alias in `aliases`, a
    handoff's position in `handoffs`, a variable in `assignments`.

    Rules and grants are named by **label**. Give one when you declare
    them, or use the one frisk derives — `git:ask:commit`,
    `stubtool:grant:clean`, `sudo:ask` for a rule about the tool
    itself, with a numeric suffix where two would collide. `frisk
    registry` prints whichever it is, so what you drop is what you read
    there — and if you are about to drop something from a collection
    you did not write, read it there first: a derived label counts from
    the top of its declaration, so editing the file above it moves it.
    Give your own label to anything you mean to keep referring to.

    Dropping and adding the same name in one `amend` is refused: it
    says two things at once. To change a flag's arity or a matcher,
    just declare it again — the new one replaces the old.
    """
    if not names:
        raise ConfigurationError("drop() names what it takes out of the list.")
    return Drop(tuple(names))


def amend(
    name: str = "",
    *,
    aliases: Sequence[str | Drop] = (),
    default: Rule | None = None,
    flags: Sequence[FlagSet | Drop] = (),
    options: Sequence[FlagSet | Drop] = (),
    assignments: Sequence[Assignment | Drop] = (),
    rules: Sequence[Rule | Drop] = (),
    grants: Sequence[Grant | Drop] = (),
    handoffs: Sequence[Handoff | Drop] = (),
    closed_world: bool | None = None,
    cases: Sequence[Case] = (),
) -> None:
    """Amend the declaration beneath instead of replacing it (§3.4).

    Redeclaring a name with `tool()` replaces what sits under it
    entirely; `amend()` is the other required form, and it must be able
    to **remove** as well as add — drop a flag from an arity list, drop
    a rule, narrow a grant — because adopting a collection and then
    trimming it is what makes collections adoptable at all.

        amend("git", rules=[ask("push", reason=…)])
        amend("sudo", flags=[drop("-u"), takes_value("--prompt-file")])

    Use this to adjust something already declared — an engine default,
    or a tool a collection you adopted brought with it — without
    rewriting it. `tool()` with the same name is the other choice: it
    **replaces** the declaration entirely.

    Anything you list is added. To take something away, put `drop(…)`
    in the list it belongs to. To change a flag's arity or a
    matcher, just declare it again: the new one replaces the old.

    `closed_world` left unset means "closed exactly when grants are
    declared", so dropping a tool's last grant re-opens its flag list.
    That is not the tool losing its guard: its default verdict stays,
    and what you have said is that no shape bypasses that default any
    more. A world you closed on purpose with `True` survives a trim you
    made for another reason.

    You cannot drop a `default=`. Declare another one instead.
    """
    _entity(
        "amend",
        name,
        _source(),
        amendment=True,
        aliases=aliases,
        default=default,
        flags=flags,
        options=options,
        assignments=assignments,
        rules=rules,
        grants=grants,
        handoffs=handoffs,
        closed_world=closed_world,
        cases=cases,
    )


def use(collection: str) -> None:
    """Adopt a collection of declarations, in the order declared.

    Sources compose in an explicit, total order — the order the
    configuration declares them, later overriding earlier — so a
    conflict between two collections is decided by the operator's
    ordering and never by accident. The operator's own declarations
    come last and always win, wherever in the file they sit: `use()` is
    an adoption, not a point in a stream.

        use("starter")

    A collection is a declaration file beside your configuration, named
    without its extension: `use("starter")` runs
    `.claude/frisk/starter.py`. It brings its cases with its rules.

    Adopt as many as you like. Where two collections declare the same
    tool, the one adopted **later** wins — the order is yours and
    nothing else decides it. Your own declarations always win over all
    of them, wherever in the file they sit, so adopting a collection
    below your own `tool()` does not undo it.
    """
    open_recording = recording("use")
    base = open_recording.base_dir
    if base is None:
        raise ConfigurationError(
            f"use('{collection}') has nowhere to look: a collection is "
            "a file beside the configuration, and no configuration "
            "directory is open."
        )
    if collection in open_recording.adopted:
        raise ConfigurationError(
            f"use('{collection}') adopts the same collection twice, "
            "and the order of two adoptions of one file says nothing."
        )
    adopted = Path(os.path.normpath(str(base / f"{collection}.py")))
    if adopted.parent != base:
        raise ConfigurationError(
            f"use('{collection}') reaches outside the configuration "
            "directory: the engine executes the project's own "
            "configuration and what sits beside it, and nothing else."
        )
    if not adopted.is_file():
        raise ConfigurationError(
            f"use('{collection}') found no '{adopted.name}' beside the "
            "configuration."
        )
    open_recording.adopt(collection)
    namespace: dict[str, Any] = {
        "__name__": f"frisk_collection_{collection}",
        "__file__": str(adopted),
    }
    try:
        # The bytes, for the reason `config.load` gives: a collection
        # is Python source, and source is UTF-8 whatever the locale is.
        exec(compile(adopted.read_bytes(), str(adopted), "exec"), namespace)
    finally:
        open_recording.pop()


# --------------------------------------------------------------------
# What a declaration records
#
# A declaration returns nothing (see the module docstring): it appends
# to the layer the caller has open. What is recorded is the operator's
# words, unresolved — composition is `registry.py`'s, and keeping the
# two apart is what lets `use()` execute a collection at the point of
# the call while the operator's own layer still wins.

#: The layer names a `Source` carries. They live here because a layer
#: is what a recording is made of, and `registry.py` re-exports them
#: beside the composition that reads them.
ENGINE_LAYER = "engine"
PROJECT_LAYER = "project"


@dataclass
class Entity:
    """One `tool`, `wrapper`, `shell`, `interpreter` or `amend` call.

    `kind` is the string `registry.Kind` is built from rather than the
    enum itself: this module is the bottom of the import graph, and a
    declaration must not have to know what composition makes of it.
    """

    kind: str
    name: str
    source: Source
    amendment: bool = False
    aliases: Sequence[object] = ()
    default: Rule | None = None
    flags: Sequence[object] = ()
    options: Sequence[object] = ()
    assignments: Sequence[object] = ()
    rules: Sequence[object] = ()
    grants: Sequence[object] = ()
    handoffs: Sequence[object] = ()
    closed_world: bool | None = None
    cases: Sequence[Case] = ()
    keeps_operands: int = 0
    operands_from_stdin: bool = False
    joins_operands: bool = False


@dataclass
class Layer:
    """One source's declarations, in the order they were written."""

    name: str
    entities: list[Entity] = field(default_factory=list)
    benign: list[object] = field(default_factory=list)
    redirections: list[Rule] = field(default_factory=list)
    cases: list[Case] = field(default_factory=list)


class Recording:
    """The layers being recorded, and which one is open.

    The stack is what makes `use()` an adoption rather than a point in
    a stream: adopting a collection pushes a layer of its own, so the
    declarations it makes are attributed to it and land ahead of the
    operator's, wherever in the file the `use()` call sits.
    """

    def __init__(self, layer: str, base_dir: Path | None) -> None:
        self.base_dir = base_dir
        self.generation: int | None = None
        self.engine: Layer | None = None
        self.collections: list[Layer] = []
        self.project = Layer(layer)
        self.adopted: list[str] = []
        self._stack: list[Layer] = [self.project]

    @property
    def current(self) -> Layer:
        return self._stack[-1]

    def push(self, layer: Layer) -> None:
        """Open a layer: declarations now land in it."""
        self._stack.append(layer)

    def adopt(self, name: str) -> None:
        """Open a collection's layer, beneath whatever adopted it.

        A collection the configuration adopts composes over the engine
        and under the operator. One adopted *by a collection* composes
        under its adopter, for the same reason the operator wins over
        everything: whoever adopts decides. Inserting before the
        adopter also keeps adoption order among siblings, since each
        insertion lands after the ones already there.
        """
        layer = Layer(f"collection:{name}")
        adopter = self._stack[-1]
        if adopter is self.project:
            self.collections.append(layer)
        else:
            self.collections.insert(self.collections.index(adopter), layer)
        self.adopted.append(name)
        self.push(layer)

    def pop(self) -> None:
        self._stack.pop()

    def ordered(self) -> list[Layer]:
        """Every layer, in composition order: engine, collections, us."""
        layers = [] if self.engine is None else [self.engine]
        return [*layers, *self.collections, self.project]


_open: Recording | None = None


def begin_recording(layer: str, base_dir: Path | None) -> Recording:
    """Open a recording. `registry.collecting` is the only caller."""
    global _open
    if base_dir is not None:
        if not base_dir.is_absolute():
            raise ConfigurationError(
                f"the configuration directory '{base_dir}' is relative: "
                "which file a collection resolves to would then depend "
                "on where the process was started."
            )
        base_dir = Path(os.path.normpath(str(base_dir)))
    _open = Recording(layer, base_dir)
    return _open


def end_recording() -> None:
    """Close the recording, whatever happened inside it."""
    global _open
    _open = None


def recording(declaration: str) -> Recording:
    """The open recording, or the error that says there is none."""
    if _open is None:
        raise ConfigurationError(
            f"{declaration}() was called outside a configuration: "
            "declarations are recorded into the collection being "
            "loaded, and there is none open."
        )
    return _open


def _source(depth: int = 2) -> Source:
    """Where the caller's caller wrote this declaration.

    The frame rather than the call stack: `Source` is built for every
    declaration on every config load, which is the hook's hot path
    (§4.5), and `inspect.stack()` reads the file behind every frame it
    reports.
    """
    frame = sys._getframe(depth)
    file = frame.f_code.co_filename
    if not os.path.isabs(file):
        file = os.path.abspath(file)
    layer = PROJECT_LAYER if _open is None else _open.current.name
    return Source(layer=layer, file=file, line=frame.f_lineno)


# --------------------------------------------------------------------
# What a declaration is refused for


def _conditions(when: When) -> tuple[Condition, ...]:
    """`when=` holds one condition or a sequence of them (`D-034`)."""
    if when is None:
        return ()
    if isinstance(when, Condition):
        return (when,)
    given = tuple(when)
    for each in given:
        if not isinstance(each, Condition):
            raise ConfigurationError(
                f"when= takes conditions, and {each!r} is not one."
            )
    return given


def _reasoned(subject: str, reason: str) -> str:
    if not reason.strip():
        raise ConfigurationError(
            f"{subject} needs a reason: whoever meets this refusal is "
            "shown the reason and nothing else, so a missing one "
            "leaves them with no way forward."
        )
    return reason


def _subject(verdict: str, subcommand: Sequence[str]) -> str:
    return f"{verdict}({' '.join(subcommand)})"


def _typed(
    items: Sequence[object],
    allowed: tuple[type, ...],
    *,
    what: str,
    drops: bool,
) -> None:
    """Every item is of a kind this list accepts, `Drop` included."""
    for item in items:
        if isinstance(item, Drop):
            if not drops:
                raise ConfigurationError(
                    f"drop() in a {what} list of a fresh declaration: "
                    "there is nothing beneath it to remove from. Use "
                    "amend() to take something out of what is already "
                    "declared."
                )
            continue
        if not isinstance(item, allowed):
            raise ConfigurationError(f"{item!r} is not a {what} declaration.")


def _entity(
    kind: str,
    name: str,
    source: Source,
    *,
    amendment: bool = False,
    aliases: Sequence[object] = (),
    default: Rule | None = None,
    flags: Sequence[object] = (),
    options: Sequence[object] = (),
    assignments: Sequence[object] = (),
    rules: Sequence[object] = (),
    grants: Sequence[object] = (),
    handoffs: Sequence[object] = (),
    closed_world: bool | None = None,
    cases: Sequence[Case] = (),
    keeps_operands: int = 0,
    operands_from_stdin: bool = False,
    joins_operands: bool = False,
) -> None:
    """Validate one entity declaration and record it."""
    open_recording = recording("amend" if amendment else kind)
    if not name.strip():
        raise ConfigurationError(
            f"a {kind} must be named: the name is what a command line "
            "is recognized by (§4.2)."
        )
    if name.startswith("/") or name.startswith("~"):
        raise ConfigurationError(
            f"'{name}' is an absolute path. A configuration is "
            "committed and travels with the project, where that path "
            "is a different machine's; declare the command name, or a "
            "project-relative path to a file in the project."
        )
    _typed(rules, (Rule,), what="rule", drops=amendment)
    for each in rules:
        if isinstance(each, Rule) and each.target is not None:
            raise ConfigurationError(
                f"'{name}' declares a rule with target=: a target "
                "matches where output lands, so the rule belongs in "
                "redirections()."
            )
    _typed(aliases, (str,), what="alias", drops=amendment)
    _typed(flags, (FlagSet,), what="flag", drops=amendment)
    _typed(options, (FlagSet,), what="option", drops=amendment)
    _typed(assignments, (Assignment,), what="assignment", drops=amendment)
    _typed(grants, (Grant,), what="grant", drops=amendment)
    _typed(
        handoffs,
        (SubcommandHandoff, OptionHandoff),
        what="handoff",
        drops=amendment,
    )
    _typed(cases, (Case,), what="case", drops=False)
    if default is not None:
        if not isinstance(default, Rule):
            raise ConfigurationError(
                "default= takes a verdict, such as ask(reason=...)."
            )
        # A default is what the tool answers when nothing else matched,
        # so neither of these has a reading — and both were silently
        # dropped, which left the operator's file and the printed
        # registry disagreeing about the boundary.
        if default.subcommand:
            raise ConfigurationError(
                f"'{name}' declares a default on the subcommand "
                f"'{' '.join(default.subcommand)}'. A default is the "
                "verdict when no rule matched; put the subcommand in "
                "rules= instead."
            )
        if default.target is not None:
            raise ConfigurationError(
                f"'{name}' declares a default with target=: a target "
                "matches where output lands, so the rule belongs in "
                "redirections()."
            )
    open_recording.current.entities.append(
        Entity(
            kind=kind,
            name=name,
            source=source,
            amendment=amendment,
            aliases=tuple(aliases),
            default=default,
            flags=tuple(flags),
            options=tuple(options),
            assignments=tuple(assignments),
            rules=tuple(rules),
            grants=tuple(grants),
            handoffs=tuple(handoffs),
            closed_world=closed_world,
            cases=tuple(cases),
            keeps_operands=keeps_operands,
            operands_from_stdin=operands_from_stdin,
            joins_operands=joins_operands,
        )
    )


def _flag_set(
    arity: Arity, names: Sequence[str], default: str | None = None
) -> FlagSet:
    """One arity bucket, with the names it was given."""
    if not names:
        raise ConfigurationError(
            f"a {arity.value} declaration names no flags."
        )
    for name in names:
        if not isinstance(name, str) or not name.strip():
            raise ConfigurationError(f"{name!r} is not a flag name.")
    if default is not None and arity is not Arity.OPTIONAL_VALUE:
        raise ConfigurationError(
            "default= says what a *bare* use of a value-optional flag "
            "means, so it belongs to may_take_value() alone."
        )
    return FlagSet(arity=arity, names=tuple(names), default=default)


def _verdict(
    verdict: Verdict,
    subcommand: str,
    when: When,
    reason: str,
    label: str | None,
    scope: Scope,
    target: Matcher | None,
    source: Source,
) -> Rule:
    """One declared verdict, refused if it could refuse and says why."""
    path = tuple(subcommand.split())
    if verdict is not Verdict.SILENT:
        reason = _reasoned(_subject(verdict.value, path), reason)
    return Rule(
        verdict=verdict,
        subcommand=path,
        conditions=_conditions(when),
        reason=reason,
        label=label,
        scope=scope,
        target=target,
        declared_at=source,
    )
