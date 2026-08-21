"""The engine's default layers (§3.4).

Universal shell knowledge, not project policy: the programs whose job is
to run other programs, and the interpreters a registered tool can be run
through. It lives engine-side because every project needs it and no
project should have to write it — but it is declared with the same
constructors as anything else, so it is enumerable (§12), reviewable,
and **shadowable**: a configuration declaring the same name wins, which
is how an operator promotes a wrapper to a rule-bearing tool, corrects
an arity, adds an exotic runner, or removes an entry whose name collides
with a project binary.

These entries carry no rules and no grants, which is what keeps them
outside the coverage gate of §8.2: there is nothing here for a project's
cases to prove.

The **baseline read tools** are the other default layer §3.4 names, and
they are deliberately not here — they exist to serve the allow doctrine
of §6.3 and arrive with it.

Two arity facts are worth stating because getting them wrong loses the
walk rather than a value: a wrapper's *undeclared* options are presumed
bare (§4.3), so this layer declares only the value-taking ones; and a
wrapper that keeps positional operands of its own — `timeout 30 cmd` —
must say how many, because that is what tells the walk where the inner
command begins.
"""

from __future__ import annotations


def declare() -> None:
    """Declare the engine's default layers into the open collection."""
    raise NotImplementedError
