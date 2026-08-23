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

* **Cross-form asks what the working directory could make true**
  (§3.2, `D-037`), not what form the two sides have. A relative value
  and a relative boundary hang off the same unknown base, so they
  compare textually like two absolute paths. A relative value against
  an absolute boundary is always unproven: some working directory
  would place it inside, and none can be read off the line. An
  absolute value against a relative boundary is never *satisfied* —
  the working directory can never be proven right — and splits on
  whether any could put it inside at all: unsatisfied when the
  boundary's components appear nowhere in the value (`.scratch` is
  absent from `/etc/passwd`, so no directory makes it true),
  unproven when they do (`./etc` against `/etc/passwd`, true when the
  working directory is `/`).
* **A `cd` earlier on the line poisons relative paths.** Every later
  relative *path* match is unproven — deliberately lexical, subshells
  included (§3.2). This is the rule above rather than a second one:
  two relative paths compare textually *because they share one unknown
  base*, and an in-line `cd` is exactly what stops them sharing it.
  Pattern and predicate matchers are untouched, which is why
  `cd /srv && tool run/validates.yaml` still satisfies a pattern
  matcher over its operand.
* **Nothing touches the filesystem** (§4.5): resolution is textual, and
  the paths being judged may not exist yet. `~` is expanded from the
  environment's `HOME`; `~other` is unproven, since naming another
  user's home would mean reading the password database. That is a
  claim about the matchers written here — `predicate()` runs a callable
  the configuration supplies, and what it does is the configuration's
  to answer for.

**Dynamic values are never matched.** A token the shell would expand
carries no value at decision time, and an unknown never satisfies a
positive condition (§4.2). Whether a token is dynamic is decided where
quoting is resolved — the tokenizer — not sniffed here: `'$FOO'` is a
literal after tokenization and a matcher re-reading it would misjudge
it. That is why the input type carries the flag.
"""

from __future__ import annotations

import enum
import fnmatch
import os
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Callable, Union

from .errors import ConfigurationError


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

#: A resolved path: whether it is absolute, and its components with
#: `.` and `..` already applied. `None` stands for a path that cannot
#: be resolved without touching the filesystem, which §4.5 forbids.
Resolved = Union[tuple[bool, tuple[str, ...]], None]


def combine_any(outcomes: Sequence[Outcome]) -> Outcome:
    """Kleene's or: a decision outranks an unknown (`D-035`)."""
    if Outcome.SATISFIED in outcomes:
        return Outcome.SATISFIED
    if Outcome.UNPROVEN in outcomes:
        return Outcome.UNPROVEN
    return Outcome.UNSATISFIED


def combine_all(outcomes: Sequence[Outcome]) -> Outcome:
    """Kleene's and: one clean miss decides, an unknown only delays."""
    if Outcome.UNSATISFIED in outcomes:
        return Outcome.UNSATISFIED
    if Outcome.UNPROVEN in outcomes:
        return Outcome.UNPROVEN
    return Outcome.SATISFIED


def compiled(pattern: str) -> re.Pattern[str]:
    """A declared pattern, compiled where it was declared.

    Once, at declaration, for two reasons. A pattern that will not
    compile is a structurally broken declaration, and §8.2 asks for
    those at load — left to the first value that reaches it, it is a
    traceback out of the middle of a printed registry or, on the hook
    path, a runtime deny whose message is an engine stack. And the
    pattern is a constant: recompiling it per judged value buys nothing
    but a lookup in a cache this process shares with every other regex
    user in it (§4.5).
    """
    try:
        return re.compile(pattern)
    except re.error as broken:
        raise ConfigurationError(
            f"'{pattern}' is not a usable regular expression: {broken}."
        ) from broken


def _asked(value: Matchable) -> Value:
    """A bare string is a plain, non-dynamic value."""
    return value if isinstance(value, Value) else Value(value)


def _expanded(text: str) -> str | None:
    """`~` from the environment; `~other` and an absent `HOME` are None.

    Naming another user's home means reading the password database,
    and §4.5 forbids the engine every filesystem access there is.
    """
    if not text.startswith("~"):
        return text
    if text == "~" or text.startswith("~/"):
        home = os.environ.get("HOME")
        if not home:
            return None
        return home + text[1:]
    return None


def resolve(text: str) -> Resolved:
    """Apply `~`, `.` and `..` textually, without a filesystem.

    A `..` that would climb past an absolute root is dropped, as the
    root's parent is itself; on a relative path it is kept, since what
    it climbs past is the unknown base.
    """
    expanded = _expanded(text)
    if expanded is None:
        return None
    absolute = expanded.startswith("/")
    components: list[str] = []
    for component in expanded.split("/"):
        if component in ("", "."):
            continue
        if component == "..":
            if components and components[-1] != "..":
                components.pop()
            elif not absolute:
                components.append("..")
            continue
        components.append(component)
    return absolute, tuple(components)


def _inside(boundary: Sequence[str], value: Sequence[str]) -> bool:
    """Whole-component containment, wildcards never crossing `/`.

    The equality test first is not an optimization of `fnmatchcase` but
    a way around it: most boundary components carry no wildcard at all,
    and for those the glob machinery is a cache lookup and a regex
    match to answer a string comparison (§4.5).
    """
    if len(value) < len(boundary):
        return False
    return all(
        pattern == component or fnmatch.fnmatchcase(component, pattern)
        for pattern, component in zip(boundary, value)
    )


def _could_be_inside(boundary: Sequence[str], value: Sequence[str]) -> bool:
    """Whether *some* working directory would put `value` inside.

    An absolute value sits inside a relative boundary exactly when it
    reads as `<cwd>/<boundary>/<rest>`, so the boundary's components
    have to appear in it as a run — `.scratch` appears nowhere in
    `/etc/passwd`, and `etc` appears at the front of it (`D-037`).

    A leading `..` is not one of those components (`D-041`): it is the
    boundary re-basing itself onto a directory the line does not name,
    and it appears in no resolved absolute path, so looking for it
    would answer *unsatisfied* for every `../shared` — while a working
    directory anywhere in `/repo` puts `/repo/shared/x` inside that
    one. Resolution collects `..` at the front of a relative path, so
    the front is the only place it can be.
    """
    climbed = 0
    while climbed < len(boundary) and boundary[climbed] == "..":
        climbed += 1
    boundary = boundary[climbed:]
    width = len(boundary)
    if width == 0:
        return True
    return any(
        _inside(boundary, value[start : start + width])
        for start in range(len(value) - width + 1)
    )


class Matcher:
    """The common shape: evaluate a value, describe yourself.

    `describe` is not decoration — it is what `frisk registry` prints
    and what a citation names (§6.2), so every matcher owes a phrase an
    operator can recognize as their own declaration.
    """

    def evaluate(
        self, value: Matchable, context: MatchContext = NO_CONTEXT
    ) -> Outcome:
        asked = _asked(value)
        if asked.dynamic:
            # An unknown never satisfies a positive condition (§4.2),
            # and the family below never sees one: deciding it here
            # once is what keeps that guarantee out of every matcher.
            return Outcome.UNPROVEN
        return self.decide(asked.text, context)

    def decide(self, text: str, context: MatchContext) -> Outcome:
        """Answer for a value known to be literal."""
        raise NotImplementedError

    def describe(self) -> str:
        raise NotImplementedError


class PathMatcher(Matcher):
    """The family that resolves before comparing (§3.2)."""

    def decide(self, text: str, context: MatchContext) -> Outcome:
        resolved = resolve(text)
        if resolved is None:
            return Outcome.UNPROVEN
        absolute, components = resolved
        if not absolute and context.relative_paths_unproven:
            # The `cd` poisoning, and the reason it is this family's
            # alone: two relative paths compare textually because they
            # hang off one unknown base, and a `cd` is what stops them
            # sharing it (§3.2, `D-037`).
            return Outcome.UNPROVEN
        return self.decide_path(absolute, components)

    def decide_path(
        self, absolute: bool, components: Sequence[str]
    ) -> Outcome:
        raise NotImplementedError


@dataclass(frozen=True)
class OneOf(Matcher):
    values: tuple[str, ...]

    def decide(self, text: str, context: MatchContext) -> Outcome:
        if text in self.values:
            return Outcome.SATISFIED
        return Outcome.UNSATISFIED

    def describe(self) -> str:
        return "one of " + ", ".join(f"'{each}'" for each in self.values)


@dataclass(frozen=True)
class Matching(Matcher):
    pattern: str
    expression: re.Pattern[str] = field(init=False, compare=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "expression", compiled(self.pattern))

    def decide(self, text: str, context: MatchContext) -> Outcome:
        if self.expression.search(text):
            return Outcome.SATISFIED
        return Outcome.UNSATISFIED

    def describe(self) -> str:
        return f"matching '{self.pattern}'"


@dataclass(frozen=True)
class Predicate(Matcher):
    description: str
    test: Callable[[str], bool]

    def decide(self, text: str, context: MatchContext) -> Outcome:
        return Outcome.SATISFIED if self.test(text) else Outcome.UNSATISFIED

    def describe(self) -> str:
        return self.description


@dataclass(frozen=True)
class PathUnder(PathMatcher):
    boundaries: tuple[str, ...]
    #: The boundaries resolved once, at declaration. They are constants
    #: — resolving each of them again for every judged value is the
    #: same `~` lookup and the same `..` walk, per value per boundary,
    #: on the path §4.5 budgets in milliseconds.
    resolved: tuple[Resolved, ...] = field(
        init=False, compare=False, repr=False
    )

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "resolved",
            tuple(resolve(boundary) for boundary in self.boundaries),
        )

    def decide_path(
        self, absolute: bool, components: Sequence[str]
    ) -> Outcome:
        return combine_any(
            [
                self._against(boundary, absolute, components)
                for boundary in self.resolved
            ]
        )

    def _against(
        self,
        resolved: Resolved,
        absolute: bool,
        components: Sequence[str],
    ) -> Outcome:
        if resolved is None:
            return Outcome.UNPROVEN
        rooted, expected = resolved
        if rooted == absolute:
            # One unknown base, or none at all: compare textually.
            if _inside(expected, components):
                return Outcome.SATISFIED
            return Outcome.UNSATISFIED
        if rooted:
            # Relative value, absolute boundary: some working
            # directory would place it inside, and none is on the line.
            return Outcome.UNPROVEN
        if _could_be_inside(expected, components):
            return Outcome.UNPROVEN
        return Outcome.UNSATISFIED

    def describe(self) -> str:
        return "under " + " or ".join(self.boundaries)


@dataclass(frozen=True)
class PathMatching(PathMatcher):
    pattern: str
    expression: re.Pattern[str] = field(init=False, compare=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "expression", compiled(self.pattern))

    def decide_path(
        self, absolute: bool, components: Sequence[str]
    ) -> Outcome:
        rendered = ("/" if absolute else "") + "/".join(components)
        if absolute and not components:
            rendered = "/"
        if self.expression.search(rendered):
            return Outcome.SATISFIED
        return Outcome.UNSATISFIED

    def describe(self) -> str:
        return f"a path matching '{self.pattern}'"


@dataclass(frozen=True)
class AnyOf(Matcher):
    matchers: tuple[Matcher, ...]

    def decide(self, text: str, context: MatchContext) -> Outcome:
        return combine_any(
            [each.evaluate(text, context) for each in self.matchers]
        )

    def describe(self) -> str:
        return (
            "any of ("
            + "; ".join(each.describe() for each in self.matchers)
            + ")"
        )


@dataclass(frozen=True)
class AllOf(Matcher):
    matchers: tuple[Matcher, ...]

    def decide(self, text: str, context: MatchContext) -> Outcome:
        return combine_all(
            [each.evaluate(text, context) for each in self.matchers]
        )

    def describe(self) -> str:
        return (
            "all of ("
            + "; ".join(each.describe() for each in self.matchers)
            + ")"
        )


def one_of(*values: str) -> Matcher:
    """Match a value that is exactly one of these strings.

        flag("--mode", one_of("dry-run", "check"))

    Comparison is exact, not a prefix: `one_of("check")` does not match
    `checkout`. A single value is spelled the same way, `one_of("cat")`.
    """
    return OneOf(tuple(values))


def matching(regex: str) -> Matcher:
    """Match a value against a regular expression.

        at_least_one_operand(matching(r"^(create|delete)$"))

    The whole value is searched, not just its start, so **anchor the
    pattern yourself**: unanchored, `validates?\\.ya?ml` also accepts
    `validates.yaml.bak`. The raw string is compared — nothing is
    resolved or expanded first, which is what makes this the right
    matcher for values that are not paths.
    """
    return Matching(regex)


def predicate(description: str, test: Callable[[str], bool]) -> Matcher:
    """Match a value with your own test, for what the others cannot say.

        predicate("a four-digit year", lambda v: v.isdigit() and len(v) == 4)

    The description comes first because it is what your registry and
    every refusal citing this matcher will show. Write it as the phrase
    you would want to read in a prompt.

    Your callable runs on the decision path, once per value it is asked
    about, inside a per-call budget measured in milliseconds. Keep it
    pure and cheap: no filesystem, no network, no state of its own. An
    exception from it is not caught — a matcher that raises is a
    configuration defect, and frisk would rather that be loud than
    become a verdict nobody can explain.
    """
    return Predicate(description, test)


def path_under(*boundaries: str) -> Matcher:
    """Match a path inside one of these directories.

        every_operand(path_under("/tmp", ".scratch"))

    `..` and `~` are resolved before comparing, so a boundary cannot be
    escaped by spelling: `/tmp/../etc` is *not* under `/tmp`. Containment
    is by whole path component, so `/tmpevil` is not under `/tmp`, and a
    boundary contains itself.

    A boundary may carry glob wildcards, which never cross `/`:
    `/home/*/scratch` accepts `/home/me/scratch/build` and rejects
    `/home/a/b/scratch`.

    Several boundaries mean *any of them*, and mixing absolute and
    relative ones is fine. A relative boundary never *matches* an
    absolute value — nothing on a command line says which directory it
    would be relative to — but it can still rule one out: `.scratch`
    refuses `/etc/passwd`, because no working directory could put that
    path inside a `.scratch`. Where one could, the answer is "cannot
    tell" instead, and the verdict moves to the stricter side: `./etc`
    against `/etc/passwd` is undecided, since the working directory
    might be `/`.
    """
    return PathUnder(tuple(boundaries))


def path_matching(regex: str) -> Matcher:
    """Match a path against a regular expression, as a whole path.

        env("BUILD_ROOT", path_matching(r"^/mnt/\\w+/build$"))

    Unlike `path_under`, this does **not** accept what is inside a
    match: `^/mnt/\\w+/build$` takes `/mnt/data/build` and refuses both
    `/mnt/data/builds` and `/mnt/data/build/sub`. Use `path_under` for a
    directory boundary and this for a path with a shape.

    `..` and `~` are still resolved first, so
    `/mnt/data/build/../../../etc` is judged as `/etc`.
    """
    return PathMatching(regex)


def any_of(*matchers: Matcher) -> Matcher:
    """Match a value that satisfies at least one of these matchers.

    env("TARGET", any_of(path_under("/tmp"), one_of("staging")))
    """
    return AnyOf(tuple(matchers))


def all_of(*matchers: Matcher) -> Matcher:
    """Match a value that satisfies every one of these matchers.

    flag("--config", all_of(path_under("etc"), matching(r"\\.ya?ml$")))
    """
    return AllOf(tuple(matchers))
