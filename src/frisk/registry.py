"""Composition, shadowing, and the effective registry (§3.4, §9).

One primitive drives the layering: **per-name shadowing** — for any tool
name, the most specific declaration decides, either replacing what sits
beneath it (`tool` again) or amending it (`amend`, which must be able to
remove as well as add).

Layers compose in an explicit, total order, and the order is the
configuration's, never an accident of when a file was read:

1. the engine's default layers — shell wrappers, walked interpreters —
   declarations like any other, and shadowable like any other;
2. each collection, in the order the configuration adopted it, later
   overriding earlier;
3. the operator's own declarations, which always come last and always
   win, wherever in the file they sit. `use()` is an adoption, not a
   point in a stream, so a configuration that calls it after its own
   `tool()` does not thereby lose to the collection.

Within one layer there is no order at all: reordering rules inside a
source never changes a verdict (§3.2), and a name declared twice in one
layer is a mistake rather than a shadow, so it is refused.

**The result is inspectable, and that is a requirement** (§3.4): a
composition that could hide a rule would be a boundary nobody can
review. `Registry.describe()` is that surface — every effective
declaration, the layer and line it came from, and the label an operator
uses to drop it — and `frisk registry` is its door.
"""

from __future__ import annotations

import enum
import os
import textwrap
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

from . import defaults

# The two layer names are `declare`'s — a layer is what a recording is
# made of — and are re-exported here, beside the composition that reads
# them, because this is where a reader looks for composition's
# vocabulary. The redundant alias is what says "re-export" out loud.
from .declare import ENGINE_LAYER as ENGINE_LAYER
from .declare import PROJECT_LAYER as PROJECT_LAYER
from .declare import (
    Anywhere,
    Arity,
    Assignment,
    Case,
    Condition,
    Drop,
    Entity,
    FlagSet,
    Grant,
    Layer,
    OptionHandoff,
    Recording,
    Rule,
    Scope,
    Source,
    SubcommandHandoff,
    begin_recording,
    end_recording,
)
from .errors import ConfigurationError
from .matchers import Matcher, combine_all

# A collection's layer is `collection:<name>`; the other two are the
# constants imported above.

#: Where a rendered line stops. Only a reason ever wraps, and only when
#: `describe(wrap=True)` asks for it.
WIDTH = 79


class Cases(enum.Enum):
    """How much of the project's cases `describe` prints."""

    HIDDEN = "hidden"
    SHOWN = "shown"
    ONLY = "only"


class Kind(enum.Enum):
    """What a registered name is, and how the walk treats it (§3.4).

    A closed set, because each member is a different behaviour rather
    than a label: a **tool** is judged, a **wrapper** is stepped
    through to what it runs, a **shell**'s `-c` payload is re-analysed
    as a command line, and an **interpreter** is walked to the file it
    runs so that `python3 tools/deploy.py` is judged as
    `tools/deploy.py`'s registration.

    The value is also what `frisk registry` prints as the first token
    of an entry's header — `tool git`, `wrapper sudo` — so the printed
    form is derived from the kind rather than being it.
    """

    TOOL = "tool"
    WRAPPER = "wrapper"
    SHELL = "shell"
    INTERPRETER = "interpreter"


@dataclass(frozen=True)
class PlacedRule:
    """A rule as it stands in the effective registry."""

    rule: Rule
    label: str
    source: Source


@dataclass(frozen=True)
class PlacedGrant:
    """A grant as it stands in the effective registry."""

    grant: Grant
    label: str
    source: Source


@dataclass(frozen=True)
class Entry:
    """Everything the engine knows about one registered name.

    The three words of §3.2 are properties here rather than prose:
    an entry exists at all, so the name is **registered**; `gated` is
    true when it declares grants or a closed world; `rule_bearing` is
    true when it carries any rule. They are distinct on purpose — the
    inside-handoff discriminator of §4.3 keys on rule-bearing, secure
    mode on registered, and the closed world on gated.
    """

    kind: Kind
    name: str
    source: Source
    aliases: Sequence[str] = ()
    default: PlacedRule | None = None
    flags: Mapping[str, Arity] = field(default_factory=dict)
    #: What a value-optional flag means when used bare, for the flags
    #: whose declaration said so (`D-039`). Kept beside `flags` rather
    #: than in it so that the common case — every flag's arity, nothing
    #: else — stays one mapping to read.
    flag_defaults: Mapping[str, str] = field(default_factory=dict)
    options: Mapping[str, Arity] = field(default_factory=dict)
    #: The same, for the pre-subcommand options. A separate mapping
    #: because the two are separate namespaces: a tool declaring `-u`
    #: in both would otherwise have one default, and dropping either
    #: would take the other's with it.
    option_defaults: Mapping[str, str] = field(default_factory=dict)
    assignments: Sequence[Assignment] = ()
    rules: Sequence[PlacedRule] = ()
    grants: Sequence[PlacedGrant] = ()
    handoffs: Sequence[SubcommandHandoff] = ()
    option_handoffs: Sequence[OptionHandoff] = ()
    cases: Sequence[Case] = ()
    keeps_operands: int = 0
    operands_from_stdin: bool = False
    joins_operands: bool = False
    #: The world as the configuration declared it, three-valued
    #: (`D-034`): None is "closed exactly when grants are declared",
    #: evaluated on the state a declaration leaves behind, and an
    #: explicit True survives a trim that removes the last grant. It is
    #: kept rather than resolved into `gated` because §9's output has
    #: to say *why* a tool is gated, and only the declaration knows.
    closed_world: bool | None = None

    @property
    def path_declared(self) -> bool:
        """Whether the name is a project-relative path (§4.2).

        Derived from the name as the operator wrote it rather than
        stored beside it, because the two could then disagree — and
        because the written form is what carries the distinction:
        `./deploy.py` is a path and `deploy.py` is a basename, and
        resolution would erase exactly that difference.
        """
        return "/" in self.name

    @property
    def gated(self) -> bool:
        """Declares grants or a closed world (§3.2).

        The one question the engine asks about a tool's flags: does an
        undeclared one leave the invocation unproven? On a rules-only
        tool the same `flags=` declaration is arity and nothing more,
        and git meeting a flag nobody wrote down is not a problem.

        The stored half is `closed_world` above, three-valued as the
        configuration wrote it; this property is the answer derived
        from it and the grants, and it is what the engine asks. The two
        are not one field because §9's output must say *why* a tool is
        gated, and "by its grants" and "by declaration" are the same
        answer to a different question.
        """
        if self.closed_world is None:
            return bool(self.grants)
        return self.closed_world

    @property
    def rule_bearing(self) -> bool:
        """Carries at least one rule (§3.2, §4.3)."""
        return bool(self.rules)


class Registry:
    """The composed result: what the engine will judge against."""

    def __init__(
        self,
        entries: Mapping[tuple[str, str], Entry],
        aliases: Mapping[str, Entry],
        generation: int | None,
        benign: Sequence[Assignment],
        redirections: Sequence[PlacedRule],
        standalone_cases: Sequence[Case],
    ) -> None:
        self._entries = dict(entries)
        self._aliases = dict(aliases)
        self._generation = generation
        self._benign = tuple(benign)
        self._redirections = tuple(redirections)
        self._standalone_cases = tuple(standalone_cases)
        self._ordered = tuple(
            sorted(
                self._entries.values(), key=lambda e: (e.name, e.kind.value)
            )
        )

    def generation(self) -> int | None:
        """The API generation the configuration declared, if it did."""
        return self._generation

    def lookup(self, name: str) -> Entry | None:
        """The entry for a name or one of its aliases, if registered."""
        found = self._entries.get(("name", name))
        if found is not None:
            return found
        return self._aliases.get(name)

    def lookup_path(self, path: str) -> Entry | None:
        """The entry whose name is this project-relative path (§4.2).

        More specific than a basename declaration, which is what stops
        a grant written for the operator's script from releasing a
        same-named file anywhere.
        """
        return self._entries.get(("path", os.path.normpath(path)))

    def entries(self) -> Sequence[Entry]:
        """Every effective entry, in a stable order."""
        return self._ordered

    def cases(self) -> Sequence[Case]:
        """Every case from every layer, tool-sited or not (§8.2).

        Not the project's own alone: §8.2 lets a rule's coverage be
        supplied "by the source that contributed the rule (collections
        carry their own cases, exactly as the starter registry ships
        starter cases), so composition can never mint uncovered rules
        or turn a live import into a coverage deny". Adopting a
        collection therefore brings its cases with its rules, and
        dropping one of its rules leaves no orphan case behind.

        Where a case was *written* has no bearing on what it covers.
        The coverage gate walks the effective registry's rules and
        grants on one side and every case on the other, and asks which
        declarations actually fired — "reached" meaning the rule
        matched or the grant held, never merely that it was evaluated
        (§8.2). Siting keeps a rule and its proof in one edit; it is
        not an association the gate reads.

        The engine's default layers contribute nothing here: they carry
        no rules and no grants, so they stand outside the gate and have
        nothing to prove.
        """
        collected: list[Case] = []
        for entry in self._ordered:
            collected.extend(entry.cases)
        collected.extend(self._standalone_cases)
        return tuple(collected)

    def standalone_cases(self) -> Sequence[Case]:
        """The cases belonging to no single declaration (§5.2).

        Asked of the registry rather than found by subtracting the
        sited ones from `cases()`: a `Case` is a frozen dataclass, so
        two equal ones are indistinguishable, and a case written at the
        top level that happened to repeat a tool's would vanish from
        the section that exists to show it.
        """
        return self._standalone_cases

    def benign_assignments(self) -> Sequence[Assignment]:
        """The effective benign assignment layer (§3.2)."""
        return self._benign

    def redirections(self) -> Sequence[PlacedRule]:
        """The effective rules on redirection targets (§4.3)."""
        return self._redirections

    def describe(
        self,
        value: str | None = None,
        *,
        cases: Cases = Cases.HIDDEN,
        wrap: bool = True,
    ) -> str:
        """The effective registry as text an operator can read (§9).

        The layout is part of the contract, not a rendering detail: it
        is what the operator reads at every step's manual test, and a
        format that drifts makes two sessions describe the same
        boundary differently. One block per entry, blank-line
        separated, ordered by name so two runs of the same
        configuration compare line by line::

            tool(git)
              source: collection:starter starter.py:6
              gated: no
              default: silent
              options: -C=value --git-dir=value -c=value
              flags: -m=value --force
              assignments: GIT_PAGER=one of 'cat'
              rules:
                deny(push) - forced push
                  when: any flag in -f, --force, --mirror
                  reason: A forced push rewrites remote history.
                  source: collection:starter starter.py:9

        The rules that make it readable back:

        * An entry's header is `<kind>(<name>)`, echoing the
          declaration that produced it. Fields sit two spaces in, a
          group's members four, and their own fields six.
        * `source:` is `<layer> <file>:<line>` wherever it appears —
          first on the entry, because in a *composed* registry the
          question that brings someone to an entry is usually which
          layer won, and again on every rule and grant, which outlive
          the entry they were declared on and are what an amendment
          moves between layers.
        * `gated:` says **why**: `no`, `yes, by its grants`, or `yes, by
          declaration`. It is the one property an operator cannot infer
          by looking, since a closed world is derived from grants unless
          it was declared outright, and it always prints on a tool — its
          absence would read as "not applicable" rather than as "no".
        * Booleans otherwise print as `key: yes` and only when true.
        * `rules:`, `grants:` and `handoffs:` are groups with their
          members indented under them, so a tool carrying twenty rules
          and two grants does not make a reader infer where one list
          ends. A rule reads `<verdict>(<subcommand>) - <label>`, the
          label being what `drop` takes inside an `amend` list. Rules
          keep their declaration order: the ranking decides a verdict
          (§3.2), but an operator comparing the block against the file
          they wrote needs the two to run in step.
        * A field, group or section nothing filled is absent, not
          empty. A registry that ends with a bare `redirections` header
          every time teaches the reader to skip the place where a rule
          about `.claude` would appear.
        * Two sections follow the entries when they have content, under
          their own headers: `benign assignments` and `redirections`.
        * Everything is ASCII and escaped. A reason is text the
          configuration supplies, and this output is read by a human
          deciding what their boundary is: a newline inside a reason
          must not be able to forge a line of frisk's own output.

        `cases` keeps the project's cases out of the way by default.
        They are the longest section on a mature tool and the least
        useful thing to read when the question is "what gates git?" —
        `Cases.SHOWN` adds them under each declaration and as a final
        section for those belonging to no tool, and `Cases.ONLY` prints
        the composed list alone, every layer's cases together, with no
        declarations around them.

        `wrap` breaks a long reason onto continuation lines indented
        eight spaces — a depth reserved for continuations, so that a
        line's indent alone says whether it opens a record or continues
        one, and so a future field can be added at two, four or six
        without colliding with a wrapped reason. It is on for a reader
        and off for a parser: a
        tool reading this output plainly wants one record per line, and
        that stays true whether or not §9's machine-readable option
        ever ships.

        With `value`, every matcher line gains what that matcher
        answers, as a trailing `[satisfied]`, `[unsatisfied]` or
        `[unproven]`. Bracketed and suffixed because the three words
        contain one another: an eye scanning the column must not have
        to tell `satisfied` from `unsatisfied` by the letters in front
        of it, and neither must an assertion.
        """
        return _rendered(self, value, cases, wrap)


class Collection:
    """Declarations being recorded, and what they compose into."""

    def __init__(self, recording: Recording) -> None:
        self._recording = recording

    def registry(self) -> Registry:
        """Compose the layers and return the effective registry."""
        return _composed(self._recording)


@contextmanager
def collecting(
    layer: str = PROJECT_LAYER,
    *,
    base_dir: Path | None = None,
    with_defaults: bool = True,
) -> Iterator[Collection]:
    """Record every declaration made inside this block.

    `base_dir` is where `use()` looks for a collection file; without
    one, adopting a collection is an error rather than a search. It
    must be **absolute**, and unlike `Source.file` it is a `Path`
    because it is worked with rather than printed — joined with a
    collection's name, and compared against to refuse one that sits
    outside it. A relative base would resolve collections against
    whatever directory the process happens to be in, which is the
    ambiguity §9's same-configuration requirement exists to stop and
    would let §5.1's "the project's own config and what sits beside
    it" mean something different per invocation. The
    engine's default layers are included unless `with_defaults` is
    off, which exists for the suites that examine one declaration and
    would otherwise read the whole shell-wrapper layer.
    """
    recording = begin_recording(layer, base_dir)
    try:
        if with_defaults:
            engine = Layer(ENGINE_LAYER)
            recording.engine = engine
            recording.push(engine)
            try:
                defaults.declare()
            finally:
                recording.pop()
        yield Collection(recording)
    finally:
        end_recording()


# --------------------------------------------------------------------
# Composition
#
# One pass over the layers in order, each declaration applied to what
# the layers beneath it left. Nothing is deferred: an amendment sees
# the composed state at its own layer, which is what makes dropping a
# collection's rule by the label `frisk registry` printed for it work.


def _key(name: str) -> tuple[str, str]:
    """The namespace a name is looked up in, and its settled spelling.

    Two namespaces, because §4.2 makes the two forms different claims:
    `deploy.py` is a command word, `./deploy.py` is a file in the
    project, and a project must be able to attach policy to both. The
    written form stays on the entry; only the key is normalized, so
    `./tools/deploy.py` and `tools/../tools/deploy.py` reach one entry.
    """
    if "/" in name:
        return ("path", os.path.normpath(name))
    return ("name", name)


@dataclass
class _Building:
    """One entry under construction, as the layers reach it."""

    kind: str
    name: str
    source: Source
    aliases: list[str] = field(default_factory=list)
    default: PlacedRule | None = None
    flags: dict[str, Arity] = field(default_factory=dict)
    flag_defaults: dict[str, str] = field(default_factory=dict)
    options: dict[str, Arity] = field(default_factory=dict)
    option_defaults: dict[str, str] = field(default_factory=dict)
    assignments: list[Assignment] = field(default_factory=list)
    rules: list[PlacedRule] = field(default_factory=list)
    grants: list[PlacedGrant] = field(default_factory=list)
    handoffs: list[SubcommandHandoff] = field(default_factory=list)
    option_handoffs: list[OptionHandoff] = field(default_factory=list)
    cases: list[Case] = field(default_factory=list)
    closed_world: bool | None = None
    keeps_operands: int = 0
    operands_from_stdin: bool = False
    joins_operands: bool = False


def _label(base: str, taken: Sequence[str]) -> str:
    """The derived label, with a numeric suffix where two collide.

    Counted from the top of the declaration, which is why `drop`'s
    docstring tells an operator to read the label off `frisk registry`
    rather than to count for themselves.
    """
    if base not in taken:
        return base
    ordinal = 2
    while f"{base}:{ordinal}" in taken:
        ordinal += 1
    return f"{base}:{ordinal}"


def _derived(name: str, verdict: str, subcommand: Sequence[str]) -> str:
    parts = [name, verdict]
    if subcommand:
        parts.append(" ".join(subcommand))
    return ":".join(parts)


def _written(owner: str, declared_at: Source | None) -> Source:
    """Where a rule or grant was written, which is never nowhere.

    Every verdict constructor fills it from the caller's frame, and
    `Rule` and `Grant` are absent from `declare.__all__`, so a
    configuration cannot produce one without it. A check rather than a
    fallback `Source`: §3.4 requires the layer and line to be
    printable, and inventing one would print a lie.
    """
    if declared_at is None:
        raise ConfigurationError(
            f"a declaration on '{owner}' records no source. Rules and "
            "grants come from deny(), ask(), allow(), silent() and "
            "grant(), which is what records where they were written."
        )
    return declared_at


def _placed_rule(owner: str, rule: Rule, taken: Sequence[str]) -> PlacedRule:
    base = _derived(owner, rule.verdict.value, rule.subcommand)
    label = rule.label if rule.label is not None else _label(base, taken)
    if rule.label is not None and rule.label in taken:
        raise ConfigurationError(
            f"'{owner}' carries two declarations labelled "
            f"'{rule.label}': a label is what drop() reaches, so two "
            "of them would remove whichever was found first."
        )
    return PlacedRule(
        rule=rule,
        label=label,
        source=_written(owner, rule.declared_at),
    )


def _placed_grant(
    owner: str, grant: Grant, taken: Sequence[str]
) -> PlacedGrant:
    base = _derived(owner, "grant", grant.subcommand)
    label = grant.label if grant.label is not None else _label(base, taken)
    if grant.label is not None and grant.label in taken:
        raise ConfigurationError(
            f"'{owner}' carries two declarations labelled '{grant.label}'."
        )
    return PlacedGrant(
        grant=grant,
        label=label,
        source=_written(owner, grant.declared_at),
    )


def _dropped(items: Sequence[object]) -> tuple[list[str], list[object]]:
    """A declaration list split into what it removes and what it adds."""
    removals: list[str] = []
    additions: list[object] = []
    for item in items:
        if isinstance(item, Drop):
            removals.extend(item.names)
        else:
            additions.append(item)
    return removals, additions


def _no_double_talk(
    removals: Sequence[str], added: Sequence[str], what: str
) -> None:
    """`drop("-u")` beside `takes_value("-u")` says two things at once."""
    both = sorted(set(removals) & set(added))
    if both:
        raise ConfigurationError(
            f"the {what} list both drops and declares "
            f"{', '.join(both)}: within a source there is no order "
            "(§3.2), so the pair has no reading. To change something, "
            "declare it again — the new one replaces the old."
        )


def _apply_flags(
    target: dict[str, Arity],
    known_defaults: dict[str, str],
    items: Sequence[object],
    what: str,
    owner: str,
) -> None:
    removals, additions = _dropped(items)
    declared: dict[str, Arity] = {}
    defaults_declared: dict[str, str | None] = {}
    for item in additions:
        assert isinstance(item, FlagSet)
        for name in item.names:
            if name in declared and declared[name] is not item.arity:
                raise ConfigurationError(
                    f"'{owner}' declares {name} with two arities, "
                    f"{declared[name].value} and {item.arity.value}."
                )
            declared[name] = item.arity
            defaults_declared[name] = item.default
    _no_double_talk(removals, list(declared), what)
    for name in removals:
        if name not in target:
            raise ConfigurationError(
                f"'{owner}' declares no {what} {name}, so there is "
                "nothing to drop."
            )
        del target[name]
        known_defaults.pop(name, None)
    for name, arity in declared.items():
        target[name] = arity
        value = defaults_declared[name]
        if value is None:
            known_defaults.pop(name, None)
        else:
            known_defaults[name] = value


def _assignment_key(assignment: Assignment) -> str:
    """A variable is named by its name, a family by its matcher."""
    name = assignment.name
    return name if isinstance(name, str) else name.describe()


def _apply_assignments(
    target: list[Assignment], items: Sequence[object], owner: str
) -> None:
    removals, additions = _dropped(items)
    _no_double_talk(
        removals,
        [_assignment_key(a) for a in additions if isinstance(a, Assignment)],
        "assignment",
    )
    for name in removals:
        matches = [a for a in target if _assignment_key(a) == name]
        if not matches:
            raise ConfigurationError(
                f"{owner} accounts for no {name}, so there is nothing to drop."
            )
        for each in matches:
            target.remove(each)
    for item in additions:
        assert isinstance(item, Assignment)
        key = _assignment_key(item)
        replaced = False
        for index, standing in enumerate(target):
            if _assignment_key(standing) == key:
                # Re-declaring a name replaces it: two declarations for
                # one variable would leave the looser one to win.
                target[index] = item
                replaced = True
                break
        if not replaced:
            target.append(item)


def _handoff_position(handoff: object) -> str:
    if isinstance(handoff, SubcommandHandoff):
        return " ".join(handoff.subcommand)
    assert isinstance(handoff, OptionHandoff)
    return handoff.option


def _apply_handoffs(building: _Building, items: Sequence[object]) -> None:
    removals, additions = _dropped(items)
    _no_double_talk(
        removals, [_handoff_position(each) for each in additions], "handoff"
    )
    for name in removals:
        by_subcommand = [
            each
            for each in building.handoffs
            if _handoff_position(each) == name
        ]
        by_option = [
            each
            for each in building.option_handoffs
            if _handoff_position(each) == name
        ]
        if not by_subcommand and not by_option:
            raise ConfigurationError(
                f"'{building.name}' declares no handoff at {name}, so "
                "there is nothing to drop."
            )
        for each in by_subcommand:
            building.handoffs.remove(each)
        for option_handoff in by_option:
            building.option_handoffs.remove(option_handoff)
    for item in additions:
        if isinstance(item, SubcommandHandoff):
            building.handoffs.append(item)
        else:
            assert isinstance(item, OptionHandoff)
            building.option_handoffs.append(item)


def _apply_aliases(building: _Building, items: Sequence[object]) -> None:
    removals, additions = _dropped(items)
    _no_double_talk(removals, [str(each) for each in additions], "alias")
    for name in removals:
        if name not in building.aliases:
            raise ConfigurationError(
                f"'{building.name}' has no alias {name}, so there is "
                "nothing to drop."
            )
        building.aliases.remove(name)
    for item in additions:
        assert isinstance(item, str)
        if item not in building.aliases:
            building.aliases.append(item)


def _apply_rules(building: _Building, items: Sequence[object]) -> None:
    removals, additions = _dropped(items)
    for label in removals:
        matches = [each for each in building.rules if each.label == label]
        if not matches:
            raise ConfigurationError(
                f"'{building.name}' carries no rule labelled "
                f"'{label}'. `frisk registry` prints the label of "
                "every rule, derived ones included."
            )
        for each in matches:
            building.rules.remove(each)
    for item in additions:
        assert isinstance(item, Rule)
        building.rules.append(
            _placed_rule(
                building.name,
                item,
                [each.label for each in building.rules],
            )
        )


def _apply_grants(building: _Building, items: Sequence[object]) -> None:
    removals, additions = _dropped(items)
    for label in removals:
        matches = [each for each in building.grants if each.label == label]
        if not matches:
            raise ConfigurationError(
                f"'{building.name}' carries no grant labelled '{label}'."
            )
        for each in matches:
            building.grants.remove(each)
    for item in additions:
        assert isinstance(item, Grant)
        building.grants.append(
            _placed_grant(
                building.name,
                item,
                [each.label for each in building.grants],
            )
        )


def _applied(building: _Building, entity: Entity) -> None:
    """Everything one declaration adds to or removes from an entry."""
    _apply_aliases(building, entity.aliases)
    _apply_flags(
        building.flags,
        building.flag_defaults,
        entity.flags,
        "flag",
        building.name,
    )
    _apply_flags(
        building.options,
        building.option_defaults,
        entity.options,
        "option",
        building.name,
    )
    _apply_assignments(building.assignments, entity.assignments, building.name)
    _apply_handoffs(building, entity.handoffs)
    _apply_rules(building, entity.rules)
    _apply_grants(building, entity.grants)
    building.cases.extend(entity.cases)
    if entity.default is not None:
        building.default = PlacedRule(
            rule=entity.default,
            label=entity.default.label
            or _derived(building.name, "default", ()),
            source=_written(building.name, entity.default.declared_at),
        )
    if entity.closed_world is not None:
        building.closed_world = entity.closed_world
    if building.closed_world is False and building.grants:
        raise ConfigurationError(
            f"'{building.name}' declares grants and an open world: a "
            "grant an undeclared flag could escape proves nothing "
            "(§3.2), so the pair contradicts itself rather than "
            "expressing a preference."
        )


def _applied_to(
    built: dict[tuple[str, str], _Building], entity: Entity
) -> None:
    key = _key(entity.name)
    if entity.amendment:
        standing = built.get(key)
        if standing is None:
            raise ConfigurationError(
                f"amend('{entity.name}') has nothing to amend: no "
                "layer beneath declares that name, and an amendment "
                "that silently does nothing is a boundary the operator "
                "believes they have."
            )
        _applied(standing, entity)
        return
    building = _Building(
        kind=entity.kind,
        name=entity.name,
        source=entity.source,
        keeps_operands=entity.keeps_operands,
        operands_from_stdin=entity.operands_from_stdin,
        joins_operands=entity.joins_operands,
    )
    _applied(building, entity)
    built[key] = building


def _no_repeats(layer: Layer) -> None:
    """One source speaks for a name once, however it spells it.

    Within a layer there is no order (§3.2), so a second declaration
    has no order-free reading and is a mistake rather than a shadow —
    shadowing is what layers are for. That holds across the two forms
    as well as within each: `tool()` replaces what sits beneath, so an
    `amend()` of the same name in the same source keeps its effect
    when written below and loses it when written above, which is an
    order deciding a boundary.
    """
    claimed: dict[tuple[str, str], str] = {}
    for entity in layer.entities:
        keys = [_key(entity.name)]
        if not entity.amendment:
            keys += [
                _key(str(alias))
                for alias in entity.aliases
                if not isinstance(alias, Drop)
            ]
        for key in keys:
            if key in claimed:
                raise ConfigurationError(
                    f"'{key[1]}' is spoken for twice in {layer.name}, "
                    f"by '{claimed[key]}' and by '{entity.name}'. "
                    "Within a source there is no order (§3.2), so the "
                    "second is a mistake rather than a shadow; "
                    "shadowing is what layers are for."
                )
            claimed[key] = entity.name


def _finished(building: _Building) -> Entry:
    return Entry(
        kind=Kind(building.kind),
        name=building.name,
        source=building.source,
        aliases=tuple(building.aliases),
        default=building.default,
        flags=dict(building.flags),
        flag_defaults=dict(building.flag_defaults),
        option_defaults=dict(building.option_defaults),
        options=dict(building.options),
        assignments=tuple(building.assignments),
        rules=tuple(building.rules),
        grants=tuple(building.grants),
        handoffs=tuple(building.handoffs),
        option_handoffs=tuple(building.option_handoffs),
        cases=tuple(building.cases),
        keeps_operands=building.keeps_operands,
        operands_from_stdin=building.operands_from_stdin,
        joins_operands=building.joins_operands,
        closed_world=building.closed_world,
    )


def _composed(recording: Recording) -> Registry:
    """Compose the recorded layers into the effective registry."""
    built: dict[tuple[str, str], _Building] = {}
    benign: list[Assignment] = []
    redirections: list[PlacedRule] = []
    standalone: list[Case] = []
    for layer in recording.ordered():
        _no_repeats(layer)
        for entity in layer.entities:
            _applied_to(built, entity)
        _apply_assignments(benign, layer.benign, "the benign layer")
        for rule in layer.redirections:
            redirections.append(
                _placed_rule(
                    "redirection",
                    rule,
                    [each.label for each in redirections],
                )
            )
        standalone.extend(layer.cases)
    entries = {key: _finished(each) for key, each in built.items()}
    aliases: dict[str, Entry] = {}
    for entry in entries.values():
        for alias in entry.aliases:
            aliases[alias] = entry
    return Registry(
        entries=entries,
        aliases=aliases,
        generation=recording.generation,
        benign=tuple(benign),
        redirections=tuple(redirections),
        standalone_cases=tuple(standalone),
    )


# --------------------------------------------------------------------
# The printed registry (§9)
#
# The layout is contract, not rendering: it is what the operator reads
# at every manual test, and a format that drifts makes two sessions
# describe one boundary differently. `Registry.describe` states the
# rules; this is where they are kept.


def printable(text: str) -> str:
    """Text a configuration supplied, as one printable ASCII line.

    A reason is written by the configuration and read by a human
    deciding what their boundary is: a newline inside one must not be
    able to forge a line of frisk's own output, and a terminal escape
    must not be able to erase one. Backslashes are left alone, since a
    literal one cannot forge anything and doubling it would make every
    regex in the output unreadable.

    It is idempotent, and applied twice on purpose: a reason is escaped
    before it is wrapped, so the wrap measures the width the reader
    sees rather than the width of a control character, and every line
    is escaped again at the join, so no field added later can smuggle a
    line break past the one place that stops it.
    """
    rendered = []
    for character in text:
        if character == "\n":
            rendered.append("\\n")
        elif character == "\r":
            rendered.append("\\r")
        elif character == "\t":
            rendered.append("\\t")
        elif " " <= character <= "~":
            rendered.append(character)
        else:
            rendered.append(ascii(character)[1:-1])
    return "".join(rendered)


def _source_text(source: Source) -> str:
    """`<layer> <file>:<line>`, the file by its name alone.

    One column that reads two ways is a column nobody can scan, so the
    engine's own layer is named the same way a configuration's is.
    """
    return f"{source.layer} {os.path.basename(source.file)}:{source.line}"


def _gating(entry: Entry) -> str:
    """Why a tool is gated, not only whether (`D-034`)."""
    if entry.closed_world:
        return "yes, by declaration"
    if entry.grants:
        return "yes, by its grants"
    return "no"


def _annotated(text: str, matchers: Sequence[Matcher], value: str) -> str:
    """What these matchers answer for the probed value.

    Bracketed and suffixed because the three words contain one another:
    an eye scanning the column must not have to tell `satisfied` from
    `unsatisfied` by the letters in front of it.
    """
    if not matchers:
        return text
    outcome = combine_all([each.evaluate(value) for each in matchers])
    return f"{text} [{outcome.value}]"


def _field(indent: int, key: str, text: str, wrap: bool) -> list[str]:
    """One `key: value` line, its continuations reserved to depth 8."""
    opening = f"{' ' * indent}{key}: "
    body = printable(text)
    if not wrap:
        return [opening + body]
    return textwrap.wrap(
        body,
        width=WIDTH,
        initial_indent=opening,
        subsequent_indent=" " * 8,
        break_long_words=False,
        break_on_hyphens=False,
    ) or [opening.rstrip()]


def _flag_text(
    flags: Mapping[str, Arity], defaults_by_flag: Mapping[str, str]
) -> str:
    rendered = []
    for name, arity in flags.items():
        if arity is Arity.BARE:
            rendered.append(name)
        elif arity is Arity.VALUE:
            rendered.append(f"{name}=value")
        else:
            bare_meaning = defaults_by_flag.get(name)
            suffix = "" if bare_meaning is None else f"({bare_meaning})"
            rendered.append(f"{name}=value?{suffix}")
    return " ".join(rendered)


def _assignment_text(assignment: Assignment, value: str | None = None) -> str:
    name = _assignment_key(assignment)
    if assignment.value is None:
        return name
    described = f"{name}={assignment.value.describe()}"
    if value is None:
        return described
    return _annotated(described, [assignment.value], value)


def _condition_lines(
    indent: int, conditions: Sequence[Condition], value: str | None
) -> list[str]:
    lines = []
    for condition in conditions:
        described = condition.describe()
        if value is not None:
            described = _annotated(described, condition.matchers(), value)
        lines.append(f"{' ' * indent}when: {described}")
    return lines


def _verdict_lines(
    indent: int,
    header: str,
    conditions: Sequence[Condition],
    scope: Scope,
    reason: str,
    source: Source,
    target: Matcher | None,
    value: str | None,
    wrap: bool,
) -> list[str]:
    """One rule or grant: its header, then its own fields one deeper."""
    inner = indent + 2
    lines = [f"{' ' * indent}{header}"]
    if target is not None:
        described = target.describe()
        if value is not None:
            described = _annotated(described, [target], value)
        lines.append(f"{' ' * inner}target: {described}")
    lines.extend(_condition_lines(inner, conditions, value))
    if not isinstance(scope, Anywhere):
        lines.append(f"{' ' * inner}scope: {scope.describe()}")
    if reason:
        lines.extend(_field(inner, "reason", reason, wrap))
    lines.append(f"{' ' * inner}source: {_source_text(source)}")
    return lines


def _rule_lines(
    indent: int, placed: PlacedRule, value: str | None, wrap: bool
) -> list[str]:
    subcommand = " ".join(placed.rule.subcommand)
    return _verdict_lines(
        indent,
        f"{placed.rule.verdict.value}({subcommand}) - {placed.label}",
        placed.rule.conditions,
        placed.rule.scope,
        placed.rule.reason,
        placed.source,
        placed.rule.target,
        value,
        wrap,
    )


def _grant_lines(
    indent: int, placed: PlacedGrant, value: str | None, wrap: bool
) -> list[str]:
    subcommand = " ".join(placed.grant.subcommand)
    return _verdict_lines(
        indent,
        f"grant({subcommand}) - {placed.label}",
        placed.grant.conditions,
        placed.grant.scope,
        placed.grant.reason,
        placed.source,
        None,
        value,
        wrap,
    )


def _case_text(case: Case) -> str:
    return f"{case.command} -> {case.expect.value}"


def _entry_lines(
    entry: Entry, value: str | None, cases: Cases, wrap: bool
) -> list[str]:
    """One entry's block: header, its fields, then its groups."""
    lines = [f"{entry.kind.value}({entry.name})"]
    lines.append(f"  source: {_source_text(entry.source)}")
    if entry.kind is Kind.TOOL:
        lines.append(f"  gated: {_gating(entry)}")
    if entry.aliases:
        lines.append("  aliases: " + " ".join(entry.aliases))
    if entry.default is not None:
        lines.append(f"  default: {entry.default.rule.verdict.value}")
        if entry.default.rule.reason:
            lines.extend(_field(4, "reason", entry.default.rule.reason, wrap))
    if entry.options:
        lines.append(
            "  options: " + _flag_text(entry.options, entry.option_defaults)
        )
    if entry.flags:
        lines.append(
            "  flags: " + _flag_text(entry.flags, entry.flag_defaults)
        )
    if entry.assignments:
        lines.append(
            "  assignments: "
            + " ".join(
                _assignment_text(each, value) for each in entry.assignments
            )
        )
    if entry.keeps_operands:
        lines.append(f"  keeps operands: {entry.keeps_operands}")
    if entry.operands_from_stdin:
        lines.append("  operands from stdin: yes")
    if entry.joins_operands:
        lines.append("  joins operands: yes")
    if entry.handoffs or entry.option_handoffs:
        lines.append("  handoffs:")
        for handoff in entry.handoffs:
            position = " ".join(handoff.subcommand)
            lines.append(f"    {position} keeps {handoff.keeps_operands}")
            if handoff.flags:
                lines.append(
                    "      flags: "
                    + _flag_text(
                        {
                            name: declared.arity
                            for declared in handoff.flags
                            for name in declared.names
                        },
                        {},
                    )
                )
        for opened in entry.option_handoffs:
            ends = " or ".join(opened.terminated_by)
            lines.append(f"    {opened.option} until {ends}")
    if entry.rules:
        lines.append("  rules:")
        for rule in entry.rules:
            lines.extend(_rule_lines(4, rule, value, wrap))
    if entry.grants:
        lines.append("  grants:")
        for grant in entry.grants:
            lines.extend(_grant_lines(4, grant, value, wrap))
    if cases is Cases.SHOWN and entry.cases:
        lines.append("  cases:")
        for case in entry.cases:
            lines.append(f"    {_case_text(case)}")
    return lines


def _rendered(
    registry: Registry, value: str | None, cases: Cases, wrap: bool
) -> str:
    """The whole registry, as the text `describe` promises."""
    if cases is Cases.ONLY:
        return "\n".join(
            printable(_case_text(case)) for case in registry.cases()
        )
    lines: list[str] = []
    for entry in registry.entries():
        if lines:
            lines.append("")
        lines.extend(_entry_lines(entry, value, cases, wrap))
    benign = registry.benign_assignments()
    if benign:
        lines.extend(["", "benign assignments"])
        for assignment in benign:
            lines.append("  " + _assignment_text(assignment, value))
    redirections = registry.redirections()
    if redirections:
        lines.extend(["", "redirections"])
        for placed in redirections:
            lines.extend(_rule_lines(2, placed, value, wrap))
    standalone = registry.standalone_cases()
    if cases is Cases.SHOWN and standalone:
        lines.extend(["", "cases"])
        for case in standalone:
            lines.append("  " + _case_text(case))
    return "\n".join(printable(line) for line in lines)
