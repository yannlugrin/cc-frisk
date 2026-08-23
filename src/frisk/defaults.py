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

The third layer is the **benign assignment list** of §3.2 — the
display/locale class, variables that cannot direct execution — declared
with `benign_assignments()` and shadowable the same way. It is here for
the same reason the wrappers are: without it `LC_ALL=C git status` is an
unaccounted assignment on a registered tool, and every project would
have to teach the engine its own locale.

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

from .declare import (
    accounted,
    benign_assignments,
    interpreter,
    matching,
    shell,
    takes_value,
    wrapper,
)


def declare() -> None:
    """Declare the engine's default layers into the open collection."""
    _wrappers()
    _shells()
    _interpreters()
    _benign()


def _wrappers() -> None:
    """Programs whose job is to run another program (§4.3)."""
    # `--prompt-file` is deliberately not declared: the corpus
    # adjudicates `sudo --prompt-file /tmp/p stubtool wipe` as an ask,
    # which is the walk presuming the option bare, landing on the
    # path and losing the thread.
    wrapper(
        "sudo",
        flags=[
            takes_value("-u", "--user", "-g", "--group"),
            takes_value("-p", "--prompt"),
        ],
    )
    wrapper("doas", flags=[takes_value("-u", "-C")])
    wrapper(
        "env",
        flags=[
            takes_value("-u", "--unset", "-C", "--chdir"),
            takes_value("-S", "--split-string"),
        ],
    )
    wrapper("command")
    wrapper("builtin")
    wrapper("exec", flags=[takes_value("-a")])
    wrapper("nohup")
    wrapper("setsid")
    wrapper("time", flags=[takes_value("-f", "--format", "-o", "--output")])
    wrapper("nice", flags=[takes_value("-n", "--adjustment")])
    wrapper("ionice", flags=[takes_value("-c", "-n", "-p")])
    wrapper(
        "stdbuf",
        flags=[
            takes_value("-i", "-o", "-e"),
            takes_value("--input", "--output", "--error"),
        ],
    )
    # The duration is an operand the wrapper keeps: without that,
    # `timeout 30 stubtool wipe` reads `30` as the command.
    wrapper(
        "timeout",
        flags=[takes_value("-s", "--signal", "-k", "--kill-after")],
        keeps_operands=1,
    )
    wrapper("chrt", flags=[takes_value("-p")], keeps_operands=1)
    wrapper("taskset", flags=[takes_value("-c", "-p")], keeps_operands=1)
    wrapper(
        "flock",
        flags=[
            takes_value("-w", "--wait", "-E", "--conflict-exit-code"),
        ],
        keeps_operands=1,
    )
    # What xargs runs is visible; what it runs it *on* arrives on
    # stdin, so no operand condition on the inner command is provable.
    wrapper(
        "xargs",
        flags=[
            takes_value("-n", "-P", "-I", "-d", "-E", "-L", "-s"),
            takes_value("--max-args", "--max-procs", "--replace"),
            takes_value("--delimiter", "--max-lines"),
        ],
        operands_from_stdin=True,
    )


def _shells() -> None:
    """Programs whose argument is itself a command line (§4.3).

    `-o` is declared for the same reason `-c` is: it swallows the token
    after it, and a walk reading `errexit` as the payload finds nothing.
    """
    shell("sh", flags=[takes_value("-c", "-o")])
    shell("bash", flags=[takes_value("-c", "-o")])
    # `eval` has no payload flag at all: it joins its operands and runs
    # the result, and stepping over it would leave the quoted forms as
    # one unrecognizable token.
    shell("eval", joins_operands=True)


def _interpreters() -> None:
    """Programs walked to the file they run (§4.2, `D-038`).

    Each declares the value-taking options that would shift that walk
    and nothing else. Options whose argument is attached (`perl
    -Mstrict`) or optional (`ruby -i`) are absent on purpose:
    declaring them value-taking would swallow the script.
    """
    interpreter(
        "python3",
        flags=[
            takes_value("-c", "-m", "-W", "-X"),
            takes_value("--check-hash-based-pycs"),
        ],
    )
    interpreter(
        "node",
        flags=[
            takes_value("-e", "--eval", "-p", "--print"),
            takes_value("-r", "--require"),
        ],
    )
    interpreter(
        "ruby", flags=[takes_value("-e", "-r", "-I", "-C", "-E", "-F")]
    )
    interpreter("perl", flags=[takes_value("-e", "-E", "-I")])


def _benign() -> None:
    """The display and locale class, and nothing that directs anything.

    `LANG` is declared by name rather than as a prefix: `LANGUAGE` is
    a locale variable too, and a prefix match here is the shape that
    would one day excuse `GIT_*`.
    """
    benign_assignments(
        accounted(matching(r"^LC_[A-Z_]+$")),
        accounted("LANG"),
        accounted("TZ"),
        accounted("NO_COLOR"),
    )
