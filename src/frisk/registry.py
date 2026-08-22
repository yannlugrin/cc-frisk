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
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

from .declare import (
    Arity,
    Assignment,
    Case,
    Grant,
    OptionHandoff,
    Rule,
    Source,
    SubcommandHandoff,
)

#: The layer names that appear in a `Source` and in the inspection
#: output. A collection's layer is `collection:<name>`.
ENGINE_LAYER = "engine"
PROJECT_LAYER = "project"


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
    options: Mapping[str, Arity] = field(default_factory=dict)
    assignments: Sequence[Assignment] = ()
    rules: Sequence[PlacedRule] = ()
    grants: Sequence[PlacedGrant] = ()
    handoffs: Sequence[SubcommandHandoff] = ()
    option_handoffs: Sequence[OptionHandoff] = ()
    cases: Sequence[Case] = ()
    keeps_operands: int = 0
    operands_from_stdin: bool = False
    joins_operands: bool = False

    @property
    def path_declared(self) -> bool:
        """Whether the name is a project-relative path (§4.2).

        Derived from the name as the operator wrote it rather than
        stored beside it, because the two could then disagree — and
        because the written form is what carries the distinction:
        `./deploy.py` is a path and `deploy.py` is a basename, and
        resolution would erase exactly that difference.
        """
        raise NotImplementedError

    @property
    def gated(self) -> bool:
        """Declares grants or a closed world (§3.2).

        The one question the engine asks about a tool's flags: does an
        undeclared one leave the invocation unproven? On a rules-only
        tool the same `flags=` declaration is arity and nothing more,
        and git meeting a flag nobody wrote down is not a problem.

        There is no separate `closed_world` here, though the
        configuration has that word: grants are checked "universally
        and closed-world" (§3.2), so declaring one closes the world,
        and a field for it would always equal this property. The
        keyword stays config-side, where it is how an operator closes a
        world without writing a grant.
        """
        raise NotImplementedError

    @property
    def rule_bearing(self) -> bool:
        """Carries at least one rule (§3.2, §4.3)."""
        raise NotImplementedError


class Registry:
    """The composed result: what the engine will judge against."""

    def generation(self) -> int | None:
        """The API generation the configuration declared, if it did."""
        raise NotImplementedError

    def lookup(self, name: str) -> Entry | None:
        """The entry for a name or one of its aliases, if registered."""
        raise NotImplementedError

    def lookup_path(self, path: str) -> Entry | None:
        """The entry whose name is this project-relative path (§4.2).

        More specific than a basename declaration, which is what stops
        a grant written for the operator's script from releasing a
        same-named file anywhere.
        """
        raise NotImplementedError

    def entries(self) -> Sequence[Entry]:
        """Every effective entry, in a stable order."""
        raise NotImplementedError

    def cases(self) -> Sequence[Case]:
        """Every case the configuration declared, tool-sited or not."""
        raise NotImplementedError

    def benign_assignments(self) -> Sequence[Assignment]:
        """The effective benign assignment layer (§3.2)."""
        raise NotImplementedError

    def redirections(self) -> Sequence[PlacedRule]:
        """The effective rules on redirection targets (§4.3)."""
        raise NotImplementedError

    def describe(self, value: str | None = None) -> str:
        """The effective registry as text an operator can read (§9).

        The layout is part of the contract, not a rendering detail: it
        is what the operator reads at every step's manual test, and a
        format that drifts makes two sessions describe the same
        boundary differently. It is a suite of blocks, one per entry,
        separated by blank lines, ordered by name so two runs of the
        same configuration compare line by line::

            tool git
              source: collection:starter starter.py:4
              aliases: git2
              options: -C=value
              flags: -m=value
              assignments: GIT_PAGER=one of 'cat'
              default: silent
              deny [forced push] push
                reason: A forced push rewrites remote history.
                source: collection:starter starter.py:7
              ask [git:ask:commit] commit
                when: flag --tags
                reason: A commit is work being recorded.
                source: collection:starter starter.py:12

        The rules that make it readable back:

        * An entry's header is `<kind> <name>`, its fields are indented
          two spaces, and a rule's own lines four. Fields absent from a
          declaration are absent from the block — an empty `aliases:`
          line is noise in a registry an operator scans.
        * A rule reads `<verdict> [<label>] <subcommand>`, the label in
          brackets because it is what `amend`'s `drop` takes. Rules keep
          their declaration order: the ranking, not the order, decides
          a verdict (§3.2), but an operator comparing the block against
          the file they wrote needs the two to run in step.
        * `source:` is `<layer> <file>:<line>` everywhere it appears —
          on the entry, and again on any rule that came from elsewhere.
        * Two sections follow the entries, under their own headers:
          `benign assignments` and `redirections`.
        * Everything is ASCII and escaped. A reason is text the
          configuration supplies, and this output is read by a human
          deciding what their boundary is: a newline inside a reason
          must not be able to forge a line of frisk's own output.

        With `value`, every matcher line gains what that matcher
        answers, as a trailing `[satisfied]`, `[unsatisfied]` or
        `[unproven]`. Bracketed and suffixed because the three words
        contain one another: an eye scanning the column must not have
        to tell `satisfied` from `unsatisfied` by the letters in front
        of it, and neither must an assertion.
        """
        raise NotImplementedError


class Collection:
    """Declarations being recorded, and what they compose into."""

    def registry(self) -> Registry:
        """Compose the layers and return the effective registry."""
        raise NotImplementedError


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
    raise NotImplementedError
