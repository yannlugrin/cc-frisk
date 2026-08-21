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
import unittest
from pathlib import Path

from frisk import __version__
from frisk.cli import EXIT_NO_VERDICT, EXIT_USAGE, main

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


class ExplainTest(unittest.TestCase):
    def test_explain_reports_on_stdout_and_leaves_stderr_empty(self) -> None:
        status, out, err = run("explain", "git push --force")
        self.assertEqual(status, EXIT_NO_VERDICT)
        self.assertIn("git push --force", out)
        self.assertEqual(err, "")

    def test_explain_reaches_no_verdict_and_implies_no_allow(self) -> None:
        status, out, _ = run("explain", "git push --force")
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
        status, out, _ = run("explain", "-h")
        self.assertNotEqual(status, 0)
        self.assertEqual(out, "", "help on the verdict channel, exit 0")
        status, out, _ = run("explain", "--", "-h")
        self.assertEqual(status, EXIT_NO_VERDICT)
        self.assertIn("-h", out)

    def test_the_echoed_command_line_cannot_forge_output(self) -> None:
        # It is attacker-controlled text printed above the sentence that
        # says no verdict was reached; a newline or a terminal escape
        # inside it must not be able to forge or erase a line.
        status, out, _ = run("explain", "ls\nverdict: allow\x1b[2J")
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
        _, out, err = run("explain", "café --touché")
        out.encode("ascii")
        err.encode("ascii")


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
        completed = run_out_of_process("explain", "ls")
        self.assertEqual(completed.returncode, EXIT_NO_VERDICT)
        # Through a real process boundary, where the streams are the
        # operating system's rather than two StringIO objects.
        self.assertIn("not an allow", completed.stdout)
        self.assertEqual(completed.stderr, "")


if __name__ == "__main__":
    unittest.main()
