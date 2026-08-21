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
            status = 0 if stopped.code is None else int(stopped.code)
    return status, out.getvalue()


def run_out_of_process(*argv: str) -> subprocess.CompletedProcess[str]:
    """`python3 -m frisk`, from the source tree, nothing installed."""
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
        # Not a regex over PEP 440's whole grammar: what matters is that
        # the string an operator reads back is three dotted numbers, so
        # that "which engine answered" is a comparable answer.
        parts = __version__.split(".")
        self.assertEqual(len(parts), 3, __version__)
        for part in parts:
            self.assertTrue(part.isdigit(), __version__)


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


class UsageTest(unittest.TestCase):
    def test_no_subcommand_prints_help_and_fails(self) -> None:
        status, printed = run()
        self.assertEqual(status, EXIT_USAGE)
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
