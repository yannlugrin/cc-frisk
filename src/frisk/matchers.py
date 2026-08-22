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
    """Match a value that is exactly one of these strings.

        flag("--mode", one_of("dry-run", "check"))

    Comparison is exact, not a prefix: `one_of("check")` does not match
    `checkout`. A single value is spelled the same way, `one_of("cat")`.
    """
    raise NotImplementedError


def matching(regex: str) -> Matcher:
    """Match a value against a regular expression.

        at_least_one_operand(matching(r"^(create|delete)$"))

    The whole value is searched, not just its start, so **anchor the
    pattern yourself**: unanchored, `validates?\\.ya?ml` also accepts
    `validates.yaml.bak`. The raw string is compared — nothing is
    resolved or expanded first, which is what makes this the right
    matcher for values that are not paths.
    """
    raise NotImplementedError


def predicate(description: str, test: Callable[[str], bool]) -> Matcher:
    """Match a value with your own test, for what the others cannot say.

        predicate("a four-digit year", lambda v: v.isdigit() and len(v) == 4)

    The description comes first because it is what your registry and
    every refusal citing this matcher will show. Write it as the phrase
    you would want to read in a prompt.
    """
    raise NotImplementedError


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
    raise NotImplementedError


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
    raise NotImplementedError


def any_of(*matchers: Matcher) -> Matcher:
    """Match a value that satisfies at least one of these matchers.

    env("TARGET", any_of(path_under("/tmp"), one_of("staging")))
    """
    raise NotImplementedError


def all_of(*matchers: Matcher) -> Matcher:
    """Match a value that satisfies every one of these matchers.

    flag("--config", all_of(path_under("etc"), matching(r"\\.ya?ml$")))
    """
    raise NotImplementedError
