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

from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field

from .declare import (
    Arity,
    Assignment,
    Case,
    Grant,
    Handoff,
    Rule,
    Source,
)

#: The layer names that appear in a `Source` and in the inspection
#: output. A collection's layer is `collection:<name>`.
ENGINE_LAYER = "engine"
PROJECT_LAYER = "project"


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

    kind: str
    name: str
    source: Source
    aliases: Sequence[str] = ()
    path: str = ""
    default: PlacedRule | None = None
    flags: Mapping[str, Arity] = field(default_factory=dict)
    options: Mapping[str, Arity] = field(default_factory=dict)
    assignments: Sequence[Assignment] = ()
    rules: Sequence[PlacedRule] = ()
    grants: Sequence[PlacedGrant] = ()
    handoffs: Sequence[Handoff] = ()
    cases: Sequence[Case] = ()
    closed_world: bool = False
    keeps_operands: int = 0
    operands_from_stdin: bool = False

    @property
    def gated(self) -> bool:
        """Declares grants or a closed world (§3.2)."""
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
        """The entry declared for a project-relative path (§4.2).

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

    def redirections(self) -> Sequence[PlacedRule]:
        """The effective rules on redirection targets (§4.3)."""
        raise NotImplementedError

    def describe(self, value: str | None = None) -> str:
        """The effective registry as text an operator can read (§9).

        Every entry with its kind, its layer and the line it was
        written on, and every rule and grant with the label `amend`'s
        `drop` takes. With `value`, each matcher additionally carries
        what it answers for that value — satisfied, unsatisfied or
        unproven — which is how the three-valued model is inspected
        before any command line exists to judge.
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
    base_dir: str | None = None,
    with_defaults: bool = True,
) -> Iterator[Collection]:
    """Record every declaration made inside this block.

    `base_dir` is where `use()` looks for a collection file; without
    one, adopting a collection is an error rather than a search. The
    engine's default layers are included unless `with_defaults` is
    off, which exists for the suites that examine one declaration and
    would otherwise read the whole shell-wrapper layer.
    """
    raise NotImplementedError
