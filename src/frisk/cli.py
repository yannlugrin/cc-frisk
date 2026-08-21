"""The frisk command line (§9).

One CLI surface, reachable through several doors — the console script
of an installed engine, `python3 -m frisk`, and whatever the skill
uses — because a diagnosis must never depend on which door was
available. It runs without Claude Code: nothing here reads a hook-time
environment variable or the plugin cache path.

This build carries the skeleton. `--version` answers; `explain` reports
that there is no engine to answer with, and says so in the direction
that is safe to misread: not a verdict, not an allow.

One cost is worth knowing before the hook door is designed: importing
this module costs about 5 ms over a bare interpreter on a current
machine, nearly all of it `argparse` pulling in `re` and `gettext`,
where importing `frisk` itself costs nothing measurable. A per-call
decision budget is single-digit milliseconds (§4.5), so the hook path
must reach the engine without coming through here.

Two invariants hold for every path through this module, and both are
asserted in the suite rather than left to argparse's defaults:

* **No path returns 0 without a verdict.** A caller writing
  `frisk explain "$command" || refuse` must never be told "fine" about
  a command line nothing judged.
* **Everything printed is ASCII, and the command line is escaped.** The
  text is read by a human deciding whether to allow something, and the
  command line in it is attacker-controlled: a newline or a terminal
  escape inside it must not be able to forge a line of frisk's own
  output or erase one. `ascii()` does both jobs, and it keeps the
  output printable on the C locale of a floor-version platform, where
  an em dash would raise instead of print.
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from typing import NoReturn

from . import __version__

PROGRAM = "frisk"

#: Exit statuses. `explain` will eventually answer with the verdict it
#: reached, and those statuses are chosen when there are verdicts to
#: report; 2 is argparse's own usage failure and is left to it.
EXIT_USAGE = 2
EXIT_NO_VERDICT = 3

_NO_ENGINE = """\
{program} {version} carries no decision engine yet: this build ships the
command line only.

  command: {command}

Nothing was parsed and no verdict was reached. This is not an allow:
read a frisk of this version as absent from the permission path.\
"""


def render(command_line: str) -> str:
    """The one place a command line is turned into displayable text."""
    return ascii(command_line)


class CommandLineParser(argparse.ArgumentParser):
    """A subcommand parser whose argument is a command line.

    Such an argument routinely starts with a dash, and argparse reports
    `frisk explain -h` as a *missing* argument — naming neither the
    token it consumed nor the way to pass one. The failure is already
    safe; this makes it legible.
    """

    def error(self, message: str) -> NoReturn:
        super().error(
            f"{message}\n"
            "note: a command line beginning with '-' is data, not an "
            "option.\n      Pass it after '--', as in: "
            "frisk explain -- -h"
        )


def build_parser() -> argparse.ArgumentParser:
    """The whole command surface, in one place."""
    parser = argparse.ArgumentParser(
        prog=PROGRAM,
        description="Judge the command lines an agent proposes to run.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{PROGRAM} {__version__}",
        help="print the engine version answering here and exit",
    )

    subcommands = parser.add_subparsers(
        metavar="<command>", parser_class=CommandLineParser
    )
    explain = subcommands.add_parser(
        "explain",
        help="show the verdict frisk would return for a command line",
        description=(
            "Show the verdict frisk would return for a command line, "
            "with the reason it was reached. A command line that starts "
            "with a dash is data like any other: pass it after `--`."
        ),
        # No `-h` here, deliberately. With one, `frisk explain -h` is a
        # help request that exits 0 — a status 0 for a command line
        # nothing judged, which is the one thing this build must never
        # produce. `frisk --help` documents the subcommand instead.
        add_help=False,
    )
    explain.add_argument(
        "command_line",
        metavar="<command-line>",
        help="the command line to judge, as one argument",
    )
    explain.set_defaults(handler=explain_command)

    return parser


def explain_command(args: argparse.Namespace) -> int:
    """`frisk explain <command-line>` — parses nothing yet, and says so."""
    print(
        _NO_ENGINE.format(
            program=PROGRAM,
            version=__version__,
            command=render(args.command_line),
        )
    )
    return EXIT_NO_VERDICT


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for both doors. Returns the process exit status."""
    parser = build_parser()
    args = parser.parse_args(argv)

    handler = getattr(args, "handler", None)
    if handler is None:
        # Help, but on the channel that matches the status: this is a
        # usage failure, not an answer, and stdout is the verdict side.
        parser.print_help(sys.stderr)
        return EXIT_USAGE

    exit_status: int = handler(args)
    return exit_status
