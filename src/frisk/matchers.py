"""Matchers and their three-valued evaluation (§3.2).

Wherever the configuration constrains a value — a flag's value, an
environment assignment's value, an operand, a redirection target — the
same matcher forms apply, and every one of them answers with one of
three outcomes rather than a boolean.

**Why three.** A boundary that cannot be decided is not a boundary that
was crossed, and it is not one that held either. `tmp/x` against the
absolute boundary `/tmp` is the case: no resolution base exists on the
line, so inventing one would be a guess in the releasing direction.
`unproven` is that third answer, and §3.3 fixes what it costs — the
verdict moves stricter, never quieter. What "stricter" means depends on
the role the matcher was evaluated in, and that split lives in
`verdicts.py`, not here: a matcher never knows whether it was asked by a
grant or by a deny rule.

**Two families, two comparison rules.** Pattern, membership and
predicate matchers read the raw string: what the operator wrote is what
is compared. Path matchers resolve `..` and `~` *before* comparing, so a
boundary cannot be escaped textually, and they carry three further
rules that the string family does not:

* **Cross-form is unproven.** A relative value matches only a relative
  boundary and an absolute value only an absolute one; the mismatch
  invents no base and is unproven.
* **A `cd` earlier on the line poisons relative paths.** Every later
  relative *path* match is unproven — deliberately lexical, subshells
  included (§3.2). Pattern and predicate matchers are untouched, which
  is why `cd /srv && tool run/validates.yaml` still satisfies a pattern
  matcher over its operand.
* **Nothing touches the filesystem** (§4.5): resolution is textual, and
  the paths being judged may not exist yet. `~` is expanded from the
  environment's `HOME`; `~other` is unproven, since naming another
  user's home would mean reading the password database.

**Dynamic values are never matched.** A token the shell would expand
carries no value at decision time, and an unknown never satisfies a
positive condition (§4.2). Whether a token is dynamic is decided where
quoting is resolved — the tokenizer — not sniffed here: `'$FOO'` is a
literal after tokenization and a matcher re-reading it would misjudge
it. That is why the input type carries the flag.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Callable, Union


class Outcome(enum.Enum):
    """What a matcher answers. See the module docstring for why three."""

    SATISFIED = "satisfied"
    UNSATISFIED = "unsatisfied"
    UNPROVEN = "unproven"


@dataclass(frozen=True)
class Value:
    """One value as it stands after structural analysis (§4.2).

    `dynamic` marks a token the shell would expand — `$FOO`, `${FOO}`,
    an unquoted substitution — as decided by the tokenizer.
    """

    text: str
    dynamic: bool = False


#: What a matcher accepts. A bare `str` is a plain, non-dynamic value,
#: which is what a test or a `frisk registry --value` probe passes.
Matchable = Union[str, Value]


@dataclass(frozen=True)
class MatchContext:
    """What the rest of the judged line says about this match.

    One field today: whether an earlier `cd` on the line has made
    relative paths unproven (§3.2). It is a context rather than a
    parameter because the poisoning is a property of the line, not of
    the matcher or the value.
    """

    relative_paths_unproven: bool = False


#: The context of a value with no line around it.
NO_CONTEXT = MatchContext()


class Matcher:
    """The common shape: evaluate a value, describe yourself.

    `describe` is not decoration — it is what `frisk registry` prints
    and what a citation names (§6.2), so every matcher owes a phrase an
    operator can recognize as their own declaration.
    """

    def evaluate(
        self, value: Matchable, context: MatchContext = NO_CONTEXT
    ) -> Outcome:
        raise NotImplementedError

    def describe(self) -> str:
        raise NotImplementedError


def one_of(*values: str) -> Matcher:
    """The value is exactly one of these strings.

    The single-value case is spelled the same way — `one_of("cat")` —
    deliberately: a second constructor for it would be two names for
    one concept in a surface §5.3 asks to keep small.
    """
    raise NotImplementedError


def matching(regex: str) -> Matcher:
    """The raw string matches this regular expression.

    Anchoring is the author's: an unanchored `validates?\\.ya?ml` also
    accepts `validates.yaml.bak`.
    """
    raise NotImplementedError


def predicate(description: str, test: Callable[[str], bool]) -> Matcher:
    """Everything else — a Python test, with the phrase that names it.

    The description comes first because it is what the operator reads
    in the registry and in a citation; the callable is the escape
    hatch, and an escape hatch that cannot be cited is not reviewable.
    """
    raise NotImplementedError


def path_under(*boundaries: str) -> Matcher:
    """The resolved path is one of these boundaries, or inside one.

    A boundary may carry glob wildcards, which never cross `/`:
    `/home/*/scratch` accepts `/home/me/scratch/build` and rejects
    `/home/a/b/scratch`. Containment is by path component, so `/tmpevil`
    is not under `/tmp`, and the boundary itself is inside itself.
    """
    raise NotImplementedError


def path_matching(regex: str) -> Matcher:
    """The resolved path matches this regular expression, exactly.

    The difference from `path_under` is deliberate and load-bearing:
    this form constrains the path itself, so `^/mnt/\\w+/build$` accepts
    `/mnt/data/build` and neither `/mnt/data/builds` nor
    `/mnt/data/build/sub`. Resolution still happens first, so
    `/mnt/data/build/../../../etc` is judged as `/etc`.
    """
    raise NotImplementedError


def any_of(*matchers: Matcher) -> Matcher:
    """Satisfied if any is; unproven if none is and any is unproven."""
    raise NotImplementedError


def all_of(*matchers: Matcher) -> Matcher:
    """Unsatisfied if any is; unproven if none is and any is unproven."""
    raise NotImplementedError
