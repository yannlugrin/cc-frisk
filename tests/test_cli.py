"""The command line answers, answers safely, and on the right channel.

stdout is the verdict channel — it is what a caller reads and what §9's
machine-readable option will eventually carry — so every test here says
which stream it expects the text on. Merging the two, as an earlier
version of this file did, hides a report that moved to stderr behind an
assertion that still passes.
"""

from __future__ import annotations

import contextlib
import io
import os
import subprocess
import sys
import tempfile
import unittest
from collections.abc import Iterator
from pathlib import Path

from frisk import __version__
from frisk.cli import (
    EXIT_CONFIG_ERROR,
    EXIT_NO_VERDICT,
    EXIT_USAGE,
    main,
)

REPOSITORY = Path(__file__).resolve().parent.parent
SOURCE = REPOSITORY / "src"


def run(*argv: str) -> tuple[int, str, str]:
    """Call the CLI in process; return its status, stdout and stderr.

    argparse exits the process itself for `--version` and for a usage
    error, so a SystemExit is one more way of reporting a status here.
    """
    out = io.StringIO()
    err = io.StringIO()
    status = 0
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            status = main(list(argv))
        except SystemExit as stopped:
            code = stopped.code
            # argparse always exits with an int; a string code would be
            # a message, which is a failure however it is spelled.
            if isinstance(code, int):
                status = code
            else:
                status = 0 if code is None else 1
    return status, out.getvalue(), err.getvalue()


def run_out_of_process(*argv: str) -> subprocess.CompletedProcess[str]:
    """`python3 -m frisk`, reaching the package through PYTHONPATH.

    Not an isolated environment: this interpreter may well have frisk
    installed, and PYTHONPATH merely wins over it. What this proves is
    that the module door works, keeps the streams apart and carries the
    status out; that it works where nothing is installed at all is what
    CI's matrix shows.
    """
    return subprocess.run(
        [sys.executable, "-m", "frisk", *argv],
        cwd=str(REPOSITORY),
        env=dict(os.environ, PYTHONPATH=str(SOURCE)),
        capture_output=True,
        text=True,
        check=False,
    )


@contextlib.contextmanager
def configured(config: str = "") -> Iterator[str]:
    """A throwaway project root carrying a frisk configuration.

    Yields the root, not the file: `--project` names a project, and the
    engine is what decides where a project keeps its configuration.
    """
    with tempfile.TemporaryDirectory() as root:
        written = Path(root) / ".claude" / "frisk"
        written.mkdir(parents=True)
        (written / "config.py").write_text(config or PROJECT_CONFIG)
        yield root


class VersionTest(unittest.TestCase):
    def test_version_prints_the_engine_version_on_stdout(self) -> None:
        status, out, err = run("--version")
        self.assertEqual(status, 0)
        self.assertEqual(out.strip(), f"frisk {__version__}")
        self.assertEqual(err, "")

    def test_the_version_is_a_release_number(self) -> None:
        # Semver on the plugin (§11), so what an operator reads back
        # opens with three dotted numbers and "which engine answered"
        # is a comparable answer. A pre-release suffix is left free:
        # nothing has decided whether this project tags one.
        self.assertRegex(__version__, r"^\d+\.\d+\.\d+")


#: A project configuration for the cases that need `explain` to have a
#: boundary to read against. Small on purpose: what a registry composes
#: is `tests/test_composition.py`'s subject, and what a *line* holds is
#: `tests/test_reading.py`'s. This is the door between them.
PROJECT_CONFIG = """\
from frisk.declare import (
    any_flag,
    api_generation,
    ask,
    bare,
    deny,
    grant,
    takes_value,
    tool,
)

api_generation(1)

tool(
    "deploy",
    default=ask(reason="deploy changes infrastructure."),
    flags=[bare("--syntax-check")],
    grants=[
        grant(
            when=any_flag("--syntax-check"),
            reason="A local question: nothing is applied.",
        ),
    ],
)

tool(
    "git",
    options=[takes_value("-C")],
    flags=[takes_value("-m")],
    rules=[
        deny(
            "push",
            reason="A forced push rewrites remote history.",
            label="forced push",
        ),
        ask("commit", reason="A commit is work being recorded."),
    ],
)
"""


class ExplainTest(unittest.TestCase):
    def test_explain_reports_on_stdout_and_leaves_stderr_empty(self) -> None:
        # stderr carries what is *not* the answer — §5.4's "this project
        # is unconfigured" among it — so a configured project must leave
        # it empty.
        with configured() as project:
            status, out, err = run(
                "explain", "--project", project, "git push --force"
            )
        self.assertEqual(status, EXIT_NO_VERDICT)
        self.assertIn("git push --force", out)
        self.assertEqual(err, "")

    def test_explain_reaches_no_verdict_and_implies_no_allow(self) -> None:
        with configured() as project:
            status, out, _ = run(
                "explain", "--project", project, "git push --force"
            )
        self.assertEqual(status, EXIT_NO_VERDICT)
        self.assertNotEqual(status, 0, "a non-verdict must not read as ok")
        self.assertIn("not an allow", out)

    def test_explain_needs_a_command_line(self) -> None:
        status, out, err = run("explain")
        self.assertEqual(status, EXIT_USAGE)
        # A usage failure is not an answer: nothing on the verdict side.
        self.assertEqual(out, "")
        self.assertIn("required", err)

    def test_a_command_line_that_looks_like_an_option_is_not_help(
        self,
    ) -> None:
        # `frisk explain -h` must not be a help request answered with 0:
        # a caller writing `frisk explain "$command" || refuse` would
        # read that as approval of a command line nothing judged.
        status, out, err = run("explain", "-h")
        self.assertNotEqual(status, 0)
        self.assertEqual(out, "", "help on the verdict channel, exit 0")
        # And the failure says what to do instead, since argparse's own
        # message reports a *missing* argument for a supplied one.
        self.assertIn("--", err)
        with configured() as project:
            status, out, _ = run("explain", "--project", project, "--", "-h")
        self.assertEqual(status, EXIT_NO_VERDICT)
        self.assertIn("-h", out)

    def test_the_echoed_command_line_cannot_forge_output(self) -> None:
        # It is attacker-controlled text printed above the sentence that
        # says no verdict was reached; a newline or a terminal escape
        # inside it must not be able to forge or erase a line.
        with configured() as project:
            status, out, _ = run(
                "explain", "--project", project, "ls\nverdict: allow\x1b[2J"
            )
        self.assertEqual(status, EXIT_NO_VERDICT)
        echoed = [
            line for line in out.splitlines() if line.startswith("  command:")
        ]
        self.assertEqual(len(echoed), 1, out)
        self.assertIn("\\n", echoed[0])
        self.assertNotIn("\x1b", out)
        # The forged line stays inside the echoed one, on no line of
        # its own, so nothing reads as frisk's own output.
        self.assertEqual(out.count("verdict: allow"), 1)
        self.assertIn("not an allow", out)

    def test_everything_printed_is_ascii(self) -> None:
        # The floor's platforms can hand the process an ASCII stdout,
        # where a non-ASCII character raises instead of printing.
        with configured() as project:
            _, out, err = run("explain", "--project", project, "café --touché")
        out.encode("ascii")
        err.encode("ascii")


class ExplainReadingTest(unittest.TestCase):
    """`explain` begins showing the invocations it found (§9, `008`).

    There is still no verdict — judging is `009` — so every case here
    checks the *reading* the command reports and the invariant that
    survives the whole build: no path out of `explain` returns 0.
    """

    def explain(self, command_line: str) -> tuple[int, str, str]:
        with configured() as project:
            return run("explain", "--project", project, command_line)

    def body(self, out: str) -> str:
        """`out` with the echoed command line taken out of it.

        `explain` echoes its input (`ExplainTest` pins that echo), so
        every word of the command is already in stdout before the
        reading is printed. An `assertIn` against the whole stream
        cannot tell the two apart, and would pass against a command
        that found the invocations perfectly and printed none of them.

        A function of the output and not of a command line, so that a
        case reading both the status and the report runs `explain`
        once, in a line the case itself carries.
        """
        return "\n".join(
            line
            for line in out.splitlines()
            if not line.lstrip().startswith("command:")
        )

    def test_the_invocation_is_reported_with_its_tool(self) -> None:
        _, out, _ = self.explain("git push --force")
        body = self.body(out)
        self.assertIn("invocation", body)
        self.assertIn("git", body)

    def test_a_flag_is_reported_apart_from_the_operands(self) -> None:
        # Apart, and each under its own label. Counting lines proves
        # only that they are on different lines — a report that called
        # `--force` an operand and `push` a flag would pass that, and
        # tell the operator the opposite of what was read. §6.2's
        # citation grows from this printer.
        _, out, _ = self.explain("git push --force")
        body = self.body(out)
        flags = [line for line in body.splitlines() if "--force" in line]
        operands = [line for line in body.splitlines() if "push" in line]
        self.assertEqual(len(flags), 1, body)
        self.assertEqual(len(operands), 1, body)
        self.assertRegex(flags[0], r"^\s*flag:")
        self.assertRegex(operands[0], r"^\s*operand:")

    def test_a_declared_option_is_reported_with_its_value(self) -> None:
        # The plan's own test line: `git -C dir push`. Read without the
        # declaration it is two operands and no push in sight, so the
        # name and the value it took belong together on one line.
        _, out, _ = self.explain("git -C /srv/repo push")
        body = self.body(out)
        paired = [
            line
            for line in body.splitlines()
            if "-C" in line and "/srv/repo" in line
        ]
        self.assertEqual(len(paired), 1, body)
        self.assertRegex(paired[0], r"^\s*option:")

    def test_every_invocation_on_the_line_is_reported(self) -> None:
        _, out, _ = self.explain("git status\ngit push --force")
        self.assertEqual(out.count("invocation"), 2, out)

    def test_an_unregistered_command_is_reported_as_unregistered(
        self,
    ) -> None:
        # Silence is a real answer (§3.2) and the operator has to be
        # able to see that frisk knows nothing about a name.
        _, out, _ = self.explain("make check")
        body = self.body(out)
        self.assertIn("make", body)
        self.assertIn("unregistered", body)

    def test_an_unprovable_invocation_says_which_value_did_it(self) -> None:
        # §6.2 owes the operator the reason their line could not be
        # proven, and a category name is not one: `unproven: unreadable`
        # names neither the token nor what it cost. The value is marked
        # where it is printed, and the summary points at it.
        _, out, _ = self.explain("deploy --syntax-check 'my file.yml'")
        body = self.body(out)
        marked = [line for line in body.splitlines() if "my file.yml" in line]
        self.assertEqual(len(marked), 1, body)
        self.assertIn("not a plain word", marked[0])
        self.assertIn("unproven:", body)

    def test_a_value_seen_and_harmless_is_marked_without_a_doubt(
        self,
    ) -> None:
        # git is registered and not gated, so a strange token costs
        # nothing — §4.2 scopes the rule to gated tools. Marking it
        # anyway, with no `unproven:` line beside it, is what tells the
        # reader it was seen and did not matter.
        _, out, _ = self.explain("git commit -m 'a plain message'")
        body = self.body(out)
        self.assertIn("not a plain word", body)
        self.assertNotIn("unproven:", body)

    def test_an_unparseable_line_says_so(self) -> None:
        # §4.1: unproven, "never silent approval of whatever it might
        # contain". The report must not look like an empty line.
        _, out, _ = self.explain("git status 'unbalanced")
        self.assertIn("could not be parsed", out)

    def test_an_unparseable_line_names_what_the_scan_found(self) -> None:
        # The scan is the whole reason the fallback is not silence, so
        # what it found is what the operator needs to see — and it is
        # not visible in the echoed command line, which holds the name
        # whether the scan ran or not.
        _, out, _ = self.explain("git status 'unbalanced")
        self.assertIn("git", self.body(out))

    def test_a_clean_scan_names_nothing(self) -> None:
        # `make` is registered nowhere and speaks for nothing, so an
        # unparseable line naming it is silence (§4.1) — a report
        # listing it would read as a finding.
        _, out, _ = self.explain("make check 'unbalanced")
        self.assertNotIn("make", self.body(out))

    def test_reading_a_line_is_still_not_a_verdict(self) -> None:
        status, out, _ = self.explain("git push --force")
        self.assertEqual(status, EXIT_NO_VERDICT)
        self.assertIn("not an allow", out)

    def test_an_unconfigured_project_is_said_out_loud(self) -> None:
        # §5.4: an enabled frisk with no configuration gates nothing,
        # and that must be visible rather than read as approval. The
        # line is still read — the engine's own default layers are a
        # boundary of sorts — so the report stands, the note goes to the
        # channel that is not the answer, and the status stays the one
        # true thing about this build: no verdict was reached. `registry`
        # answers 4 here because it has nothing at all to print; this
        # command does.
        with tempfile.TemporaryDirectory() as empty:
            status, out, err = run(
                "explain", "--project", empty, "git push --force"
            )
        self.assertEqual(status, EXIT_NO_VERDICT)
        self.assertIn("no configuration", err)
        self.assertIn("invocation", out)

    def test_a_configuration_that_will_not_load_is_loud(self) -> None:
        # §7.1: never a partially built registry standing in for a
        # boundary that failed, and never a reading that looks complete.
        with configured("api_generation(1)\nbroken(\n") as project:
            status, out, err = run(
                "explain", "--project", project, "git push --force"
            )
        self.assertEqual(status, EXIT_CONFIG_ERROR)
        self.assertEqual(out, "")
        self.assertNotEqual(err, "")

    def test_the_reported_reading_is_ascii_and_escaped(self) -> None:
        # The operands are attacker-controlled text printed above the
        # sentence that says no verdict was reached.
        _, out, err = self.explain("git commit -m 'caf\xe9\n\x1b[2J'")
        out.encode("ascii")
        err.encode("ascii")
        self.assertNotIn("\x1b", out)


class UsageTest(unittest.TestCase):
    def test_no_subcommand_prints_help_on_stderr_and_fails(self) -> None:
        status, out, err = run()
        self.assertEqual(status, EXIT_USAGE)
        self.assertNotEqual(status, 0, "nothing judged must not read as ok")
        self.assertIn("explain", err)
        self.assertEqual(out, "")

    def test_an_unknown_subcommand_fails(self) -> None:
        status, out, err = run("judge", "ls")
        self.assertEqual(status, EXIT_USAGE)
        self.assertEqual(out, "")
        self.assertIn("judge", err)


class ModuleDoorTest(unittest.TestCase):
    """`python3 -m frisk` is the door that needs no installation."""

    def test_python_m_frisk_runs_from_the_source_tree(self) -> None:
        completed = run_out_of_process("--version")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), f"frisk {__version__}")
        self.assertEqual(completed.stderr, "")

    def test_python_m_frisk_carries_the_exit_status_out(self) -> None:
        # Configured, because stderr carries what is *not* the answer
        # and §5.4's "this project gates nothing" is one of those: run
        # against the repository, which has no configuration of its own,
        # the note would be the only thing on the stream this case is
        # here to prove stays empty.
        with configured() as project:
            completed = run_out_of_process(
                "explain", "--project", project, "ls"
            )
        self.assertEqual(completed.returncode, EXIT_NO_VERDICT)
        # Through a real process boundary, where the streams are the
        # operating system's rather than two StringIO objects.
        self.assertIn("not an allow", completed.stdout)
        self.assertEqual(completed.stderr, "")


if __name__ == "__main__":
    unittest.main()
