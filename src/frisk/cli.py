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
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import NoReturn

from . import __version__
from .config import config_path, deprecation, load, locate
from .errors import ConfigurationError
from .registry import Cases, printable

PROGRAM = "frisk"

#: Exit statuses. `explain` will eventually answer with the verdict it
#: reached, and those statuses are chosen when there are verdicts to
#: report; 2 is argparse's own usage failure and is left to it.
EXIT_USAGE = 2
EXIT_NO_VERDICT = 3
#: `registry` found no configuration: the plugin is enabled and gates
#: nothing, which §5.4 requires be said unmissably rather than answered
#: with an empty registry.
EXIT_NO_CONFIG = 4
#: The configuration exists and could not be loaded (§7.1). Loud, and
#: never an empty registry standing in for a boundary that failed.
EXIT_CONFIG_ERROR = 5

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

    registry = subcommands.add_parser(
        "registry",
        help="print the effective registry the configuration composes",
        description=(
            "Print the effective registry: every declaration that "
            "survived composition, the layer and line it came from, "
            "and the label that amends it. Composition must never be "
            "able to hide a rule (§3.4), and this is where that is "
            "checked."
        ),
    )
    registry.add_argument(
        "--project",
        metavar="<dir>",
        default=None,
        help=(
            "the project to read the configuration of "
            "(default: found by walking up from here)"
        ),
    )
    shown = registry.add_mutually_exclusive_group()
    shown.add_argument(
        "--cases",
        action="store_true",
        help=(
            "also print the project's cases, under the declarations they prove"
        ),
    )
    shown.add_argument(
        "--cases-only",
        action="store_true",
        help=(
            "print the composed list of cases and nothing else, every "
            "layer's together"
        ),
    )
    registry.add_argument(
        "--no-wrap",
        action="store_true",
        help=(
            "keep every record on one line: wrapped reasons read "
            "better and parse worse"
        ),
    )
    registry.add_argument(
        "--value",
        metavar="<value>",
        default=None,
        help=(
            "also show what each matcher answers for this value: "
            "satisfied, unsatisfied or unproven"
        ),
    )
    registry.set_defaults(handler=registry_command)

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


#: The three lines that open a printed registry, before the entry
#: blocks of `Registry.describe`. §9 requires every answer to state
#: which engine gave it and which configuration it came from — a
#: registry with no provenance is an answer about an unknown project —
#: and the generation is what says which contract that file was written
#: against.
REGISTRY_HEADER = """\
{program} {version}
config: {config}
generation: {generation}\
"""


def registry_command(args: argparse.Namespace) -> int:
    """`frisk registry` — print the composed registry and its sources.

    Three outcomes, three statuses: a registry printed, no
    configuration at all, or a configuration that would not load. The
    second is not an empty registry and the third is not a silent one —
    both are the visible failure §5.4 and §7.1 ask for.
    """
    found = _configuration(args.project)
    if found is None:
        where = args.project or "here or any directory above it"
        print(
            f"{PROGRAM}: no configuration in {printable(str(where))}. "
            "An enabled frisk with no configuration gates nothing.",
            file=sys.stderr,
        )
        return EXIT_NO_CONFIG
    try:
        registry = load(found)
    except ConfigurationError as failure:
        print(f"{PROGRAM}: {printable(str(failure))}", file=sys.stderr)
        return EXIT_CONFIG_ERROR
    nudge = deprecation(registry.generation())
    if nudge is not None:
        # §3.5's middle tier: the configuration loaded and every rule
        # in it holds, so this is not a failure and the status stays 0
        # — but stderr, never stdout, so a script reading the registry
        # never finds a sentence of prose in it.
        print(f"{PROGRAM}: {printable(nudge)}", file=sys.stderr)
    print(
        REGISTRY_HEADER.format(
            program=PROGRAM,
            version=__version__,
            config=printable(str(found)),
            generation=registry.generation(),
        )
    )
    print()
    print(
        registry.describe(
            args.value,
            cases=_shown(args),
            wrap=not args.no_wrap,
        )
    )
    return 0


def _configuration(project: str | None) -> Path | None:
    """The configuration to print, or None where there is none.

    `--project` names a project, so its configuration is the one at
    that root: walking up from a named directory would answer about a
    parent the operator did not name.
    """
    if project is not None:
        # Absolute, because `.` is the natural spelling and the engine
        # refuses a relative configuration directory — which is an
        # invariant about the engine, not a fault in the input.
        # `abspath` rather than `resolve`: normalizing `.` and `..` is
        # the whole need, and following symlinks would report a path
        # the operator did not name.
        named = config_path(Path(os.path.abspath(project)))
        return named if named.is_file() else None
    return locate(Path.cwd())


def _shown(args: argparse.Namespace) -> Cases:
    if args.cases_only:
        return Cases.ONLY
    return Cases.SHOWN if args.cases else Cases.HIDDEN


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
