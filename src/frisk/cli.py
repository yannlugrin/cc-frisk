"""The frisk command line (§9).

One CLI surface, reachable through several doors — the console script
of an installed engine, `python3 -m frisk`, and whatever the skill
uses — because a diagnosis must never depend on which door was
available. It runs without Claude Code: nothing here reads a hook-time
environment variable or the plugin cache path.

This build carries the skeleton. `--version` answers; `explain` reports
that there is no engine to answer with, and says so in the direction
that is safe to misread: not a verdict, not an allow.
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence

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

Nothing was parsed and no verdict was reached. This is not an allow —
read a frisk of this version as absent from the permission path.\
"""


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

    subcommands = parser.add_subparsers(dest="command", metavar="<command>")
    explain = subcommands.add_parser(
        "explain",
        help="show the verdict frisk would return for a command line",
        description=(
            "Show the verdict frisk would return for a command line, "
            "with the reason it was reached."
        ),
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
            command=args.command_line,
        )
    )
    return EXIT_NO_VERDICT


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point for both doors. Returns the process exit status."""
    parser = build_parser()
    args = parser.parse_args(argv)

    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return EXIT_USAGE

    exit_status: int = handler(args)
    return exit_status
