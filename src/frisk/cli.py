"""The frisk command line (§9).

One CLI surface, reachable through several doors — the console script
of an installed engine, `python3 -m frisk`, and whatever the skill
uses — because a diagnosis must never depend on which door was
available. It runs without Claude Code: nothing here reads a hook-time
environment variable or the plugin cache path.

This build reads a line and reports it. `--version` answers, `registry`
prints the composed boundary, and `explain` shows the invocations it
found — with no verdict on any of them, and saying so in the direction
that is safe to misread: not a verdict, not an allow.

One cost is worth knowing before the hook door is designed: importing
this module costs about 5 ms over a bare interpreter on a current
machine, nearly all of it `argparse` pulling in `re` and `gettext`,
where importing `frisk` itself costs nothing measurable. A per-call
decision budget is single-digit milliseconds (§4.5), so the hook path
must reach the engine without coming through here.

That import is the whole of the cost: reading a line is nowhere near
it — a typical line takes tens of microseconds — so nothing about the
budget lives in this module's own work. Re-measure either half by
timing `frisk explain` against a bare `python3 -c pass`; the numbers
are a machine's, not a fact about the engine, which is why none is
recorded as one.

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
from .matchers import Value
from .reading import Doubt, Flag, Invocation, Reading, read, readable
from .registry import Cases, Registry, engine_defaults, printable

PROGRAM = "frisk"

#: Exit statuses. `explain` answers with the verdict it reached, so
#: three of these are verdicts and the rest are failures to reach one.
#: 2 is argparse's own usage failure and is left to it.
#:
#: **Silence is 0**, because silence is a real answer: frisk has no
#: opinion and the permission rules decide (§3.2). Every other status
#: is non-zero, so `frisk explain "$command" || refuse` refuses exactly
#: where frisk objected or could not answer. `allow` has no status yet:
#: no line returns one before `017`.
EXIT_SILENT = 0
EXIT_ASK = 1
EXIT_USAGE = 2
EXIT_DENY = 3
#: `registry` found no configuration: the plugin is enabled and gates
#: nothing, which §5.4 requires be said unmissably rather than answered
#: with an empty registry.
EXIT_NO_CONFIG = 4
#: The interim status of `explain` while judging is being built: it is
#: deliberately none of the verdict statuses above, so that a case
#: expecting a verdict cannot pass against a build that reaches none.
#: It retires with the last commit of `009`.
_UNJUDGED = 6
#: The configuration exists and could not be loaded (§7.1). Loud, and
#: never an empty registry standing in for a boundary that failed.
EXIT_CONFIG_ERROR = 5


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
    explain.add_argument(
        "--project",
        metavar="<dir>",
        default=None,
        help=(
            "the project whose configuration decides "
            "(default: found by walking up from here)"
        ),
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
            "show what each matcher answers for this value — "
            "satisfied, unsatisfied or unproven — and print only the "
            "declarations that can answer it"
        ),
    )
    registry.set_defaults(handler=registry_command)

    return parser


def explain_command(args: argparse.Namespace) -> int:
    """`frisk explain <command-line>` — the invocations the line holds.

    Three outcomes and two statuses. A configuration that will not load
    is the loud failure of §7.1 and nothing is read. A project with no
    configuration is read against the engine's default layers alone,
    with §5.4's "this gates nothing" on stderr — visible, but not a
    refusal to answer, because the report is still worth having.
    Everything else reports the reading.

    The status is `_UNJUDGED` in both reading cases, and it is the
    one true thing about this build: nothing here judges yet. `registry`
    answers `EXIT_NO_CONFIG` for the unconfigured project because it has
    nothing at all to print; this command does.
    """
    found = _configuration(args.project)
    if found is None:
        _unconfigured(
            args.project,
            "; what follows was read against the engine's default "
            "layers alone.",
        )
        registry = engine_defaults()
    else:
        loaded = _loaded(found)
        if loaded is None:
            return EXIT_CONFIG_ERROR
        registry = loaded
    print(_reported(args.command_line, read(args.command_line, registry)))
    return _UNJUDGED


def _unconfigured(project: str | None, consequence: str) -> None:
    """§5.4's "this project gates nothing", said unmissably.

    On stderr, which is the channel that is not the answer, so a caller
    reading stdout for a verdict never finds a sentence of prose in it.
    """
    where = project or "here or any directory above it"
    print(
        f"{PROGRAM}: no configuration in {printable(str(where))}. "
        f"An enabled frisk with no configuration gates nothing{consequence}",
        file=sys.stderr,
    )


def _loaded(found: Path) -> Registry | None:
    """The registry at this path, or None having already said why.

    §7.1's fail-loud lives here once. Both commands need it and both
    answer it the same way — a configuration that will not load is not
    an empty registry standing in for a boundary that failed — and two
    copies of that is one copy that can drift quiet.
    """
    try:
        registry = load(found)
    except ConfigurationError as failure:
        print(f"{PROGRAM}: {printable(str(failure))}", file=sys.stderr)
        return None
    nudge = deprecation(registry.generation())
    if nudge is not None:
        # §3.5's middle tier: the configuration loaded and every rule in
        # it holds, so this is not a failure and the status stays 0 —
        # but stderr, never stdout.
        print(f"{PROGRAM}: {printable(nudge)}", file=sys.stderr)
    return registry


#: The closing paragraph of every `explain`. It is what a caller who
#: reads stdout instead of the exit status must not be able to
#: misread, so it says the two things that are true of this build: the
#: line was read, and nothing judged it.
_NO_VERDICT = """\
Nothing was judged: this build reads the line and reports what it found.
This is not an allow: read a frisk of this version as absent from the
permission path.\
"""


def _reported(command_line: str, reading: Reading) -> str:
    """The whole report for one command line.

    Every field goes through `printable`, because the command line is
    attacker-controlled text printed above the sentence that says no
    verdict was reached: a newline or a terminal escape inside an
    operand must not be able to forge a line of frisk's own output or
    erase one.
    """
    lines = ["", f"  command: {render(command_line)}", ""]
    if reading.unparseable:
        lines.extend(_unparseable_lines(reading))
    elif not reading.invocations:
        lines.extend(["  no command runs on this line.", ""])
    for position, invocation in enumerate(reading.invocations, start=1):
        lines.extend(_invocation_lines(position, invocation))
        lines.append("")
    lines.append(_NO_VERDICT)
    return "\n".join(lines)


def _unparseable_lines(reading: Reading) -> list[str]:
    """§4.1's fallback, said so an operator can act on it."""
    named = ", ".join(printable(name) for name in reading.speaking)
    return [
        "  this line could not be parsed, so nothing was read from it.",
        "  it is unproven, not approved (§4.1).",
        "",
        "  tools with rules or grants named on the raw line: "
        + (named if named else "none"),
        "",
    ]


def _invocation_lines(position: int, invocation: Invocation) -> list[str]:
    """One invocation, with everything that bound to it (§4.2)."""
    lines = [
        f"  invocation {position}: {render(invocation.name)} "
        f"({_registration(invocation)})"
    ]
    for assigned in invocation.assignments:
        lines.append(
            f"    assignment: {render(assigned.name)}"
            f" = {_value_shown(assigned.value)}"
        )
    for option in invocation.options:
        lines.append(f"    option:     {_flag_shown(option)}")
    for flag in invocation.flags:
        lines.append(f"    flag:       {_flag_shown(flag)}")
    for operand in invocation.operands:
        lines.append(f"    operand:    {_value_shown(operand)}")
    for doubt in invocation.doubts:
        lines.append(f"    unproven:   {_DOUBTS[doubt]}")
    return lines


#: What each source of doubt means, said rather than named. The bare
#: enum value is a category, and §6.2 owes an operator the reason their
#: line could not be proven — the token itself is marked on the field
#: above, by `_value_shown`.
_DOUBTS = {
    Doubt.UNREADABLE: (
        "a value above is not a plain word, so no grant can prove it"
    ),
    Doubt.MALFORMED: "a declared value-taking flag has nothing after it",
    Doubt.UNRESOLVED_PATH: (
        "a relative name, after an in-line `cd` moved what it hangs off"
    ),
}


def _registration(invocation: Invocation) -> str:
    """What the engine knows this command word to be."""
    if invocation.entry is None:
        return "unregistered" + (
            ", a name the line cannot show" if invocation.dynamic_name else ""
        )
    entry = invocation.entry
    return f"{entry.kind.value} {printable(entry.name)}"


def _flag_shown(flag: Flag) -> str:
    """A flag as written, and the value it took.

    `render` rather than `printable`, like every other field taken from
    the command line: a flag *name* is attacker-controlled text too, and
    one escaping rule for line-derived text is one rule to get right.
    `printable` stays for text the configuration supplied.
    """
    if flag.value is None:
        return render(flag.name)
    return f"{render(flag.name)} = {_value_shown(flag.value)}"


def _value_shown(value: Value) -> str:
    """A value as the engine holds it, with the unknown marked.

    A value no matcher can read is marked wherever it appears, not only
    where it cost something: on a gated tool it is what the `unproven:`
    line below points at, and on a rules-only tool its absence from
    that line is the reader learning it was seen and did not matter.
    """
    if value.dynamic:
        return f"{render(value.text)} (expanded by the shell)"
    if not readable(value):
        return f"{render(value.text)} (not a plain word)"
    return render(value.text)


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
        _unconfigured(args.project, ".")
        return EXIT_NO_CONFIG
    registry = _loaded(found)
    if registry is None:
        return EXIT_CONFIG_ERROR
    print(
        REGISTRY_HEADER.format(
            program=PROGRAM,
            version=__version__,
            config=printable(str(found)),
            generation=registry.generation(),
        )
    )
    print()
    described = registry.describe(
        args.value,
        cases=_shown(args),
        wrap=not args.no_wrap,
    )
    print(described)
    if args.value is not None and not described.strip():
        # A value narrows the output to what can answer it, so nothing
        # at all is a real answer — and one an empty page states badly.
        print(
            f"{PROGRAM}: no declaration in this registry reads a value, "
            "so there is nothing for this one to answer.",
            file=sys.stderr,
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
