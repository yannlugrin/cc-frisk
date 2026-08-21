"""The command line answers, and answers in the safe direction."""

from __future__ import annotations

import contextlib
import io
import os
import subprocess
import sys
import unittest
from pathlib import Path

from frisk import __version__
from frisk.cli import EXIT_NO_VERDICT, EXIT_USAGE, main

REPOSITORY = Path(__file__).resolve().parent.parent
SOURCE = REPOSITORY / "src"


def run(*argv: str) -> tuple[int, str]:
    """Call the CLI in process; return its status and what it printed.

    argparse exits the process itself for `--version` and for a usage
    error, so a SystemExit is one more way of reporting a status here.
    """
    out = io.StringIO()
    status = 0
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
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
    return status, out.getvalue()


def run_out_of_process(*argv: str) -> subprocess.CompletedProcess[str]:
    """`python3 -m frisk`, reaching the package through PYTHONPATH.

    Not an isolated environment: this interpreter may well have frisk
    installed, and PYTHONPATH merely wins over it. What this proves is
    that the module door works and carries the status out; that it
    works where nothing is installed at all is the floor CI job's job.
    """
    return subprocess.run(
        [sys.executable, "-m", "frisk", *argv],
        cwd=str(REPOSITORY),
        env=dict(os.environ, PYTHONPATH=str(SOURCE)),
        capture_output=True,
        text=True,
        check=False,
    )


class VersionTest(unittest.TestCase):
    def test_version_prints_the_engine_version(self) -> None:
        status, printed = run("--version")
        self.assertEqual(status, 0)
        self.assertEqual(printed.strip(), f"frisk {__version__}")

    def test_the_version_is_a_release_number(self) -> None:
        # Semver on the plugin (§11), so what an operator reads back
        # opens with three dotted numbers and "which engine answered"
        # is a comparable answer. A pre-release suffix is left free:
        # nothing has decided whether this project tags one.
        self.assertRegex(__version__, r"^\d+\.\d+\.\d+")


class ExplainTest(unittest.TestCase):
    def test_explain_reaches_no_verdict_and_implies_no_allow(self) -> None:
        status, printed = run("explain", "git push --force")
        self.assertEqual(status, EXIT_NO_VERDICT)
        self.assertNotEqual(status, 0, "a non-verdict must not read as ok")
        self.assertIn("git push --force", printed)
        self.assertIn("not an allow", printed)

    def test_explain_needs_a_command_line(self) -> None:
        status, _ = run("explain")
        self.assertEqual(status, EXIT_USAGE)

    def test_a_command_line_that_looks_like_an_option_is_not_help(
        self,
    ) -> None:
        # `frisk explain -h` must not be a help request answered with 0:
        # a caller writing `frisk explain "$command" || refuse` would
        # read that as approval of a command line nothing judged.
        status, printed = run("explain", "-h")
        self.assertNotEqual(status, 0, printed)
        status, printed = run("explain", "--", "-h")
        self.assertEqual(status, EXIT_NO_VERDICT)
        self.assertIn("-h", printed)

    def test_the_echoed_command_line_cannot_forge_output(self) -> None:
        # It is attacker-controlled text printed above the sentence that
        # says no verdict was reached; a newline or a terminal escape
        # inside it must not be able to forge or erase a line.
        status, printed = run("explain", "ls\nverdict: allow\x1b[2J")
        self.assertEqual(status, EXIT_NO_VERDICT)
        echoed = [
            line
            for line in printed.splitlines()
            if line.startswith("  command:")
        ]
        self.assertEqual(len(echoed), 1, printed)
        self.assertIn("\\n", echoed[0])
        self.assertNotIn("\x1b", printed)
        # The forged line stays inside the echoed one, on no line of
        # its own, so nothing reads as frisk's own output.
        self.assertEqual(printed.count("verdict: allow"), 1)
        self.assertIn("not an allow", printed)

    def test_everything_printed_is_ascii(self) -> None:
        # The floor's platforms can hand the process an ASCII stdout,
        # where a non-ASCII character raises instead of printing.
        _, printed = run("explain", "caf\u00e9 --touch\u00e9")
        printed.encode("ascii")


class UsageTest(unittest.TestCase):
    def test_no_subcommand_prints_help_and_fails(self) -> None:
        status, printed = run()
        self.assertEqual(status, EXIT_USAGE)
        self.assertNotEqual(status, 0, "nothing judged must not read as ok")
        self.assertIn("explain", printed)

    def test_an_unknown_subcommand_fails(self) -> None:
        status, _ = run("judge", "ls")
        self.assertEqual(status, EXIT_USAGE)


class ModuleDoorTest(unittest.TestCase):
    """`python3 -m frisk` is the door that needs no installation.

    In process, `main` is called directly; here the package is reached
    the way a machine with no `pip install` reaches it, which is the
    only door the plugin can use (§2.2).
    """

    def test_python_m_frisk_runs_from_the_source_tree(self) -> None:
        completed = run_out_of_process("--version")
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stdout.strip(), f"frisk {__version__}")

    def test_python_m_frisk_carries_the_exit_status_out(self) -> None:
        completed = run_out_of_process("explain", "ls")
        self.assertEqual(completed.returncode, EXIT_NO_VERDICT)


if __name__ == "__main__":
    unittest.main()
