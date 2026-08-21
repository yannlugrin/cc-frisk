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
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Union

from .errors import ConfigurationError
from .matchers import (
    NO_CONTEXT,
    Matchable,
    MatchContext,
    Matcher,
    Outcome,
    all_of,
    any_of,
    matching,
    one_of,
    path_matching,
    path_under,
    predicate,
)
from .verdicts import Verdict

__all__ = [
    # Matchers, re-exported so a configuration has one import line.
    "Matcher",
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
    "OperandCondition",
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
    # Entities.
    "tool",
    "wrapper",
    "shell",
    "interpreter",
    "handoff",
    "accounted",
    "benign_assignments",
    "redirections",
    # Composition.
    "amend",
    "use",
    "anywhere",
    "host_only",
    "inside",
    # Cases.
    "case",
    "cases",
    "Source",
    "ConfigurationError",
]


# --------------------------------------------------------------------
# The generation declaration (§3.5)


def api_generation(generation: int) -> None:
    """Which generation of this API the configuration was written for.

    The scaffold writes it and every configuration carries it. Outside
    the range the engine speaks, loading fails closed with a message
    pointing at the skill's migration assistance — never a best guess,
    because misreading a configuration is silent where refusing is
    loud. A configuration that declares no generation at all fails the
    same way: the declaration is how a config says which contract it
    expects, and its absence is not a version.
    """
    raise NotImplementedError


# --------------------------------------------------------------------
# Flag arities (§4.2)


class Arity(enum.Enum):
    """How much of the line a flag takes with it (§4.2)."""

    BARE = "bare"
    VALUE = "value-required"
    OPTIONAL_VALUE = "value-optional"


@dataclass(frozen=True)
class FlagSet:
    """Flags sharing one arity, as one declaration."""

    arity: Arity
    names: Sequence[str]


def bare(*names: str) -> FlagSet:
    """Switches: these flags take nothing with them."""
    raise NotImplementedError


def takes_value(*names: str) -> FlagSet:
    """These flags take a value, as `--flag=v` or in the next token.

    On a gated tool this must be declared completely: a value-taking
    flag read as bare lets its value look like a flag of the
    invocation, and when that value is a safe marker
    (`deploy.yml -i --syntax-check`) a real deploy passes as a
    parse-only run — the one direction §4.2 calls the worst.
    """
    raise NotImplementedError


def may_take_value(*names: str) -> FlagSet:
    """These flags take a value unless the next token looks like a flag.

    Hand-rolled CLIs accept both `--argument custom` and
    `--argument --check`; reading such a flag as value-required
    swallows the very token that decides the verdict.
    """
    raise NotImplementedError


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


def flag(name: str, value: Matcher | None = None) -> Condition:
    """This flag is operative on the invocation, optionally with a value.

    *Operative* means the parser saw the token as a flag of this
    invocation (§5.2): a token swallowed as another flag's value is not
    one, which is what makes `deploy.yml -i --syntax-check` a real
    deploy. Value conditions are available here and not only on grants
    — prototyping could deny on a flag's presence but not on its value,
    and closing that asymmetry is one reason this API is fresh (§3.2).
    """
    raise NotImplementedError


def any_flag(*names: str) -> Condition:
    """At least one of these flags is operative on the invocation."""
    raise NotImplementedError


def env(name: str, value: Matcher | None = None) -> Condition:
    """This environment assignment binds the invocation (§4.2).

    Names are the shell's, so matching is case-sensitive and a
    lower-case name is an assignment too.
    """
    raise NotImplementedError


def option(name: str, value: Matcher | None = None) -> Condition:
    """This pre-subcommand option was used, optionally with a value.

    Which pre-subcommand options were used and with what values is
    remembered (§4.2), so "pushing is fine only for repositories under
    this directory" is a rule on `-C`'s value.
    """
    raise NotImplementedError


class OperandCondition(Condition):
    """A condition over the operand list, evaluable on its own.

    Operand quantification is pure value logic — a list of values and a
    matcher — so unlike the flag, option and assignment conditions it
    needs no parsed invocation to answer, and it answers here. The
    other kinds gain their evaluation with the invocation model they
    read.
    """

    def evaluate(
        self,
        operands: Sequence[Matchable],
        context: MatchContext = NO_CONTEXT,
    ) -> Outcome:
        raise NotImplementedError


def every_operand(value: Matcher) -> OperandCondition:
    """Every operand satisfies this matcher — and there is at least one.

    Empty operands are never vacuously granted (§3.2): a command acting
    on nothing has not proven what it acts on. The empty case has its
    own spelling, `no_operands()`, so that granting it is a decision
    rather than a side effect.

    An empty operand list is **unsatisfied**, not unproven. Nothing is
    uncertain about it — the list is known and it is empty — and §3.3's
    stricter direction is for what cannot be decided. On a grant the
    two readings agree (neither releases); on a deny rule stated over
    every operand they do not, and firing an ask about a command whose
    operands are known to be absent would be a prompt bought with a
    fiction.
    """
    raise NotImplementedError


def at_least_one_operand(value: Matcher) -> OperandCondition:
    """At least one operand satisfies this matcher."""
    raise NotImplementedError


def no_operands() -> OperandCondition:
    """The invocation carries no operands at all."""
    raise NotImplementedError


# --------------------------------------------------------------------
# Where a declaration was written


@dataclass(frozen=True)
class Source:
    """The layer a declaration came from, and the line that wrote it.

    Both halves are needed by §3.4's inspection requirement: the layer
    is what decided a conflict, the file and line are what an operator
    opens to change it.
    """

    layer: str
    file: str
    line: int


# --------------------------------------------------------------------
# Scopes (§4.3, §5.2)


@dataclass(frozen=True)
class Scope:
    """Where a rule or grant applies: the host, or inside a handoff.

    A handed-off command runs in a different world than the host's, and
    policy may legitimately differ — `docker run image cmd --dangerous`
    and a bare `cmd --dangerous` need not share a verdict.
    """

    description: str
    handoff: str | None = None
    host: bool = False


#: The default: the rule applies wherever the invocation is found.
anywhere = Scope("anywhere")

#: Only outside any handoff.
host_only = Scope("on the host", host=True)


def inside(handoff_name: str) -> Scope:
    """Only inside the named handoff — `inside("docker run")`."""
    raise NotImplementedError


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


@dataclass(frozen=True)
class Grant:
    """One proven-safe shape. A grant that holds is silence (§3.2)."""

    subcommand: Sequence[str] = ()
    conditions: Sequence[Condition] = ()
    reason: str = ""
    label: str | None = None
    scope: Scope = anywhere


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

    The subcommand is a path, written as it is typed —
    `deny("stash drop")`, `deny("buildx imagetools create")`. Omitted,
    the rule is about the tool itself. `reason` is required, and
    `target` belongs only to a rule inside `redirections()`.
    """
    raise NotImplementedError


def ask(
    subcommand: str = "",
    *,
    when: When = None,
    reason: str = "",
    label: str | None = None,
    scope: Scope = anywhere,
    target: Matcher | None = None,
) -> Rule:
    """Put it to the operator: an outward write, or destroyed work."""
    raise NotImplementedError


def allow(
    subcommand: str = "",
    *,
    when: When = None,
    reason: str = "",
    label: str | None = None,
    scope: Scope = anywhere,
    target: Matcher | None = None,
) -> Rule:
    """Grant the call outright — exceptional, and hedged (§6.3)."""
    raise NotImplementedError


def silent(
    subcommand: str = "",
    *,
    when: When = None,
    reason: str = "",
    label: str | None = None,
    scope: Scope = anywhere,
) -> Rule:
    """No opinion: hand the call to the permission rules and mode.

    The only verdict whose reason is optional — nothing is being
    refused — and the only one worth declaring explicitly, since a
    declared silence survives secure mode where an implicit one does
    not (§3.2).
    """
    raise NotImplementedError


def grant(
    subcommand: str = "",
    *,
    when: When = None,
    reason: str = "",
    label: str | None = None,
    scope: Scope = anywhere,
) -> Grant:
    """A shape proven safe, on a tool that is dangerous by default.

    Declaring any grant closes the tool's world: from then on every
    flag it may carry must be declared, and an invocation matching no
    grant gets the tool's default verdict. That is the load-bearing
    property of §3.2 — a flag or a value nobody considered can only
    move a verdict toward the stricter outcome.
    """
    raise NotImplementedError


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

    Assignments are closed-world for every registered tool, not only
    gated ones (§3.2): one that is neither on the engine's benign list
    nor accounted for here is an explicit ask citing the assignment.
    `accounted("GIT_PAGER", one_of("cat"))` accepts the pager and asks
    about every other value.

    The name may itself be a matcher, which is what a family of
    variables needs — `accounted(matching(r"^LC_[A-Z_]+$"))` — and it
    is why the benign layer below needs no vocabulary of its own.
    """
    raise NotImplementedError


def benign_assignments(
    *declared: Assignment, drop: Sequence[str] = ()
) -> None:
    """The assignments no registered tool has to account for (§3.2).

    The display/locale class — `LC_*`, `LANG`, `TZ`, `NO_COLOR` and kin
    — variables that cannot direct execution. It is an engine default
    layer like the wrappers: enumerated, reviewable, and shadowable, so
    a configuration adds to it and drops from it by name. Without this
    layer `LC_ALL=C git status` would be an unaccounted assignment on a
    registered tool, and therefore an ask.

    What belongs here is exactly what cannot change what runs.
    `GIT_SSH_COMMAND` and its dozens of siblings are the reason the
    closed world exists (§3.2); an addition here is a decision to stop
    reading a variable at all.
    """
    raise NotImplementedError


# --------------------------------------------------------------------
# Handoffs (§4.3)


@dataclass(frozen=True)
class Handoff:
    """A position where a tool stops describing itself and runs a program."""

    subcommand: Sequence[str] = ()
    option: str | None = None
    terminated_by: Sequence[str] = ()
    keeps_operands: int = 0
    flags: Sequence[FlagSet] = field(default_factory=tuple)


def handoff(
    subcommand: str = "",
    *,
    option: str | None = None,
    terminated_by: Sequence[str] = (),
    keeps_operands: int = 0,
    flags: Sequence[FlagSet] = (),
) -> Handoff:
    """Declare where the inner command begins.

    Two shapes, both required by §4.3. The ordinary one is a
    subcommand: `handoff("run", keeps_operands=1, flags=[…])` — the
    kept operand is the image, service or container name and is never
    read as a program, and the handoff's own value-taking options must
    be declared because locating the kept operand depends on them. The
    other is a flag-introduced inner command closed by a terminator:
    `handoff(option="-exec", terminated_by=[";", "+"])`, which is where
    `find . -exec rm -rf {} +` hides its command.
    """
    raise NotImplementedError


# --------------------------------------------------------------------
# Cases (§5.2, §8.2)


@dataclass(frozen=True)
class Case:
    """A command line and the verdict the guard must return for it."""

    command: str
    expect: Verdict


def case(command: str, expect: Verdict) -> Case:
    """A project's own test case, sited beside the rule it proves.

    Cases live in the tool they are about — `tool("git", rules=[…],
    cases=[…])` — because a rule and its proof drifting into separate
    files is how the coverage gate of §8.2 becomes paperwork. They can
    also stand alone at the top level for a case about no single tool.
    """
    raise NotImplementedError


def cases(*declared: Case) -> None:
    """Declare cases that belong to no single tool.

    A case about a whole line — a wrapper walk, a substitution, the
    combination of two invocations — has no tool to sit beside, and
    forcing it into one would file it where nobody looks for it.
    """
    raise NotImplementedError


# --------------------------------------------------------------------
# Entities (§3.4, §4.2, §4.3)


def tool(
    name: str = "",
    *,
    path: str = "",
    aliases: Sequence[str] = (),
    default: Rule | None = None,
    flags: Sequence[FlagSet] = (),
    options: Sequence[FlagSet] = (),
    assignments: Sequence[Assignment] = (),
    rules: Sequence[Rule] = (),
    grants: Sequence[Grant] = (),
    handoffs: Sequence[Handoff] = (),
    closed_world: bool = False,
    cases: Sequence[Case] = (),
) -> None:
    """Register a tool: what it is called, what it takes, what it may do.

    A tool is recognized by the basename of its command word, on the
    whole name only — `git` and `/usr/bin/git` are the same tool,
    `git-crypt` is not git. `aliases` are fully equivalent names for
    this same declaration (drop-in replacements). `path` registers the
    tool by project-relative path instead — `tool(path="tools/deploy.py")`
    — matched with the path machinery of §3.2 and more specific than a
    basename declaration, which is what keeps a grant written for the
    operator's script from releasing a same-named file anywhere.

    `flags` declares arities. On a gated tool the same declaration is
    also the closed world; on a rules-only tool it is arity and nothing
    more, which is why `closed_world` exists as its own word: declaring
    grants closes the world implicitly, and a tool that needs a closed
    world without a grant says so.

    `options` are the options that precede a subcommand and are
    stripped so the subcommand lands where rules expect it —
    undeclared, `git -C dir push` parses as operands and no push rule
    matches.
    """
    raise NotImplementedError


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

    The walk steps over the wrapper's declared value-taking options and
    its kept positional operands — `timeout 30 cmd` keeps one — and
    judges what it reaches. Undeclared options are presumed bare, so a
    wrapper declaration is a best effort by construction and its
    failure direction is the strict one: when the position the walk
    lands on resolves to nothing, the thread is lost and §4.3 decides.

    `operands_from_stdin` is the `… | xargs -0 rm` shape: the inner
    command word is visible but its operands arrive on stdin and are
    invisible, so operand-requiring conditions on it are unprovable.

    A wrapper may carry rules and a default of its own — `sudo git
    push --force` is a sudo *and* a denied push — which is also how an
    operator gates everything a runner runs, by shadowing it into a
    tool with an ask default rather than by heuristic.
    """
    raise NotImplementedError


def shell(
    name: str = "",
    *,
    aliases: Sequence[str] = (),
    flags: Sequence[FlagSet] = (),
    joins_operands: bool = False,
) -> None:
    """A shell: its `-c` payload is a command line and is re-analyzed.

    Combined spellings (`-lc`, `-ec`) are the same payload. A shell
    reached with no `-c` payload and no file operand — `curl url | sh`
    — is running a program the line cannot show, and asks (§4.3).

    `joins_operands` is `eval`, which has no payload flag at all: it
    joins its arguments and runs the result, so the joined string is
    what gets re-analyzed. Stepping over it instead would leave a
    quoted payload as one unrecognizable token, and `eval "git push
    --force"` would say nothing.
    """
    raise NotImplementedError


def interpreter(
    name: str = "",
    *,
    aliases: Sequence[str] = (),
    flags: Sequence[FlagSet] = (),
) -> None:
    """An interpreter walked to the file it runs (§4.2).

    `python3 tools/deploy.py` is judged as `deploy.py`'s registration
    if one exists. Program text in another language is never read as
    shell — guessing another grammar produces false refusals — so an
    interpreter's `-c`/`-e` payload is opaque, and an interpreter with
    no payload and no file operand asks like the bare piped shell.
    """
    raise NotImplementedError


def redirections(*rules: Rule) -> None:
    """Rules on where a command's output lands (§4.3).

    A redirection target can destroy by truncation or write where
    nothing else in the line writes, so targets are matchable:
    `redirections(ask(target=path_under(".claude"), reason=…))`. Their
    default is silence — redirections are ubiquitous and only rules
    give them meaning.
    """
    raise NotImplementedError


# --------------------------------------------------------------------
# Composition (§3.4)


def amend(
    name: str = "",
    *,
    path: str = "",
    aliases: Sequence[str] = (),
    default: Rule | None = None,
    flags: Sequence[FlagSet] = (),
    options: Sequence[FlagSet] = (),
    assignments: Sequence[Assignment] = (),
    rules: Sequence[Rule] = (),
    grants: Sequence[Grant] = (),
    handoffs: Sequence[Handoff] = (),
    cases: Sequence[Case] = (),
    drop: Sequence[str] = (),
    drop_flags: Sequence[str] = (),
    drop_assignments: Sequence[str] = (),
    drop_handoffs: Sequence[str] = (),
    drop_aliases: Sequence[str] = (),
) -> None:
    """Amend the declaration beneath instead of replacing it (§3.4).

    Redeclaring a name with `tool()` replaces what sits under it
    entirely; `amend()` is the other required form, and it must be able
    to **remove** as well as add — drop a flag from an arity list, drop
    a rule, narrow a grant — because adopting a collection and then
    trimming it is what makes collections adoptable at all.

    `drop` names rules and grants by their label. Every rule and grant
    has one: the label given at declaration, or one derived as
    `<name>:<verdict>:<subcommand>` — `git:ask:commit`, with a numeric
    suffix where that collides. `frisk registry` prints whichever it
    is, so what an operator drops is what they read.
    """
    raise NotImplementedError


def use(collection: str) -> None:
    """Adopt a collection of declarations, in the order declared.

    Sources compose in an explicit, total order — the order the
    configuration declares them, later overriding earlier — so a
    conflict between two collections is decided by the operator's
    ordering and never by accident. The operator's own declarations
    come last and always win, wherever in the file they sit: `use()` is
    an adoption, not a point in a stream.

    A collection is a declaration file beside the configuration, named
    without its extension: `use("starter")` runs
    `.claude/frisk/starter.py`. It is executed, not imported — a
    composition must be able to happen twice in one process, and an
    imported module declares once and then sits in `sys.modules`
    saying nothing.
    """
    raise NotImplementedError
