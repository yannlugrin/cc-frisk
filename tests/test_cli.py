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
    EXIT_ASK,
    EXIT_CONFIG_ERROR,
    EXIT_DENY,
    EXIT_ENGINE_ERROR,
    EXIT_NO_CONFIG,
    EXIT_SILENT,
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
    flags=[bare("--force", "--hard"), takes_value("-m")],
    rules=[
        deny(
            "push",
            when=any_flag("--force"),
            reason="A forced push rewrites remote history.",
            label="forced push",
        ),
        deny(
            "reset",
            when=any_flag("--hard"),
            reason="A hard reset destroys uncommitted work.",
            label="hard reset",
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
        self.assertEqual(status, EXIT_DENY)
        self.assertIn("git push --force", out)
        self.assertEqual(err, "")

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
        # `-h` is a command line nothing registers, so the answer is
        # silence — a verdict, reached, and printed.
        self.assertEqual(status, EXIT_SILENT)
        self.assertIn("-h", out)

    def test_the_echoed_command_line_cannot_forge_output(self) -> None:
        # It is attacker-controlled text printed above frisk's own
        # verdict line; a newline or a terminal escape inside it must
        # not be able to forge or erase one.
        with configured() as project:
            status, out, _ = run(
                "explain", "--project", project, "ls\nverdict: allow\x1b[2J"
            )
        self.assertEqual(status, EXIT_SILENT)
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
    """`explain` shows the invocations it found (§9, `008`).

    The verdict is `ExplainVerdictTest`'s subject; every case here
    checks the *analysis* printed beside it, which §9 requires because
    "why did this ask?" is answered by the reading, not the verdict.
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
        # Apart, and each under its own label. What this guards is the
        # printer, not the parse: reading separates the two and
        # `tests/test_reading.py` proves it, but a report that called
        # `--force` an operand and `push` a flag would tell the
        # operator the opposite of what was read, and the report is
        # what the maintenance loop runs on (§10).
        #
        # Anchored to whole lines rather than counted across the body.
        # Counting was scaffolding for picking *the* line, and it
        # breaks on anything else that names the same token — §6.2's
        # citation does, and so does a reason whose prose happens to
        # say "push", as this one's does.
        _, out, _ = self.explain("git push --force")
        body = self.body(out)
        self.assertRegex(body, r"(?m)^\s*flag:\s+'--force'$")
        self.assertRegex(body, r"(?m)^\s*operand:\s+'push'$")

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

    def test_the_analysis_is_shown_beside_the_verdict(self) -> None:
        # §9: `explain` "should also show its work — which invocations
        # were found through which walls of §4.3 — because 'why did
        # this ask?' is the maintenance loop's opening question and the
        # answer is the analysis, not just the verdict."
        status, out, _ = self.explain("git push --force")
        self.assertEqual(status, EXIT_DENY)
        self.assertIn("invocation", self.body(out))

    def test_an_unconfigured_project_is_said_out_loud(self) -> None:
        # §5.4: an enabled frisk with no configuration gates nothing,
        # and that must be visible rather than read as approval. The
        # line is still read — the engine's own default layers are a
        # boundary of sorts — so the report stands, the note goes to the
        # channel that is not the answer, and the status stays the one
        # true thing about this build: no verdict was reached. `registry`
        # answers 4 here because it has nothing at all to print; this
        # command does — and answers 4 with it, because a verdict
        # reached against no boundary is not one a script may trust
        # (`D-055`).
        with tempfile.TemporaryDirectory() as empty:
            status, out, err = run(
                "explain", "--project", empty, "git push --force"
            )
        self.assertEqual(status, EXIT_NO_CONFIG)
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
        # The operands are attacker-controlled text printed beside
        # frisk's own verdict.
        _, out, err = self.explain("git commit -m 'caf\xe9\n\x1b[2J'")
        out.encode("ascii")
        err.encode("ascii")
        self.assertNotIn("\x1b", out)


class ExplainVerdictTest(unittest.TestCase):
    """`explain` answers with the verdict, its reason and its citation.

    §9: "given a command line, the verdict the guard would return, with
    the reason and citation of §6.2, against the project's actual
    configuration; exit status usable from scripts."
    """

    def explain(self, command_line: str) -> tuple[int, str, str]:
        with configured() as project:
            return run("explain", "--project", project, command_line)

    def test_a_denied_line_says_deny_and_why(self) -> None:
        #   deny("push", when=any_flag("--force")) — label "forced push"
        status, out, err = self.explain("git push --force")
        self.assertEqual(status, EXIT_DENY)
        self.assertIn("deny", out)
        self.assertIn("A forced push rewrites remote history.", out)
        self.assertEqual(err, "")
        # And the sentence that exists to stop silence reading as
        # approval must not appear on a line frisk just refused —
        # "frisk has no opinion" under a deny is the one contradiction
        # this output cannot afford.
        self.assertNotIn("no opinion", out)

    def test_an_asked_line_says_ask_and_why(self) -> None:
        #   tool("deploy", default=ask(...)) — no grant holds here
        status, out, _ = self.explain("deploy site.yml")
        self.assertEqual(status, EXIT_ASK)
        self.assertIn("ask", out)
        self.assertIn("deploy changes infrastructure.", out)

    def test_a_silent_line_says_frisk_has_no_opinion(self) -> None:
        # §3.2: "silence means 'no opinion' and hands the call to the
        # permission rules and mode". A status of 0 is that answer, and
        # the text must not let it read as approval.
        #   grant(when=any_flag("--syntax-check"))
        status, out, _ = self.explain("deploy --syntax-check site.yml")
        self.assertEqual(status, EXIT_SILENT)
        self.assertIn("silent", out)
        self.assertIn("not an allow", out)

    def test_the_citation_names_the_declaration_that_fired(self) -> None:
        # §6.2: "Without the citation, a wrong verdict is a sentence
        # with nothing to grep for, and the maintenance loop starves."
        #   deny("push", when=any_flag("--force")) — label "forced push"
        _, out, _ = self.explain("git push --force")
        self.assertIn("forced push", out)
        self.assertIn("config.py:", out)
        # §6.2 asks for "the specific flag, assignment, value or
        # operand that matched", and this is the surface where that is
        # actually delivered — the engine-level assertions are of a
        # structure no user sees.
        self.assertRegex(out, r"(?m)^\s*read:\s+flag --force$")

    def test_every_declaration_at_the_deciding_rank_is_printed(self) -> None:
        # "the citation names every declaration at the deciding rank
        # *across the whole line*, embedded invocations included
        # (`git push -f && git reset --hard` cites both)" — §6.2's own
        # example, and two *different* declarations, which is what the
        # sentence is about.
        #   deny("push",  when=any_flag("--force")) — label "forced push"
        #   deny("reset", when=any_flag("--hard"))  — label "hard reset"
        _, out, _ = self.explain("git push --force && git reset --hard")
        self.assertIn("forced push", out)
        self.assertIn("hard reset", out)

    def test_a_silent_line_cites_nothing(self) -> None:
        # §5.3: "a declared silence refuses nothing and so has nothing
        # to explain". Paired with the deny above, which prints both,
        # so this is the absence of something the same build produces.
        #   nothing in PROJECT_CONFIG names `git status`
        _, denied, _ = self.explain("git push --force")
        self.assertIn("forced push", denied)
        self.assertIn("A forced push rewrites remote history.", denied)
        _, out, _ = self.explain("git status")
        self.assertNotIn("forced push", out)
        self.assertNotIn("A forced push rewrites remote history.", out)

    def test_the_statuses_are_the_contract_D_055_wrote(self) -> None:
        # Every other case here compares a symbol to itself, so this is
        # the one place the *numbers* are asserted — and they are a
        # contract the moment `PLAN.md` `028`'s README publishes them.
        # `D-055`: silence is 0 because silence is a real answer, and
        # everything else is non-zero, so `frisk explain "$cmd" ||
        # refuse` refuses exactly where frisk objected or could not
        # answer. Renumbering inverts that shell idiom silently.
        self.assertEqual(EXIT_SILENT, 0)
        self.assertEqual(EXIT_ASK, 1)
        self.assertEqual(EXIT_USAGE, 2)
        self.assertEqual(EXIT_DENY, 3)
        self.assertEqual(EXIT_NO_CONFIG, 4)
        self.assertEqual(EXIT_CONFIG_ERROR, 5)
        # And the engine's own failure is none of them: §3.3 makes the
        # guard's death loud, and 1 would have been *ask*.
        self.assertEqual(EXIT_ENGINE_ERROR, 6)


class EngineFailureTest(unittest.TestCase):
    """A dead engine must not answer with a verdict (§3.3, `D-055`)."""

    def test_an_engine_failure_is_none_of_the_verdict_statuses(
        self,
    ) -> None:
        # Not hypothetical input: `predicate()` runs a callable the
        # *configuration* supplies, so an operator's own lambda raising
        # on an unusual value lands in the decision path. CPython's
        # default for an unhandled exception is 1, which `D-055`
        # defines as **ask** — so a script written to that contract
        # would read a dead guard as a prompt and proceed.
        config = (
            "from frisk.declare import (\n"
            "    api_generation, deny, flag, predicate, takes_value, tool,\n"
            ")\n"
            "\n"
            "api_generation(1)\n"
            "\n"
            "tool(\n"
            '    "boom",\n'
            '    flags=[takes_value("--x")],\n'
            "    rules=[\n"
            "        deny(\n"
            '            when=flag("--x", predicate("raises", _raise)),\n'
            '            reason="Unreachable: the matcher raises first.",\n'
            "        )\n"
            "    ],\n"
            ")\n"
        )
        with configured(
            "def _raise(value):\n"
            "    raise RuntimeError('the configuration blew up')\n"
            "\n\n" + config
        ) as project:
            status, out, err = run(
                "explain", "--project", project, "boom --x y"
            )
        self.assertEqual(status, EXIT_ENGINE_ERROR)
        self.assertNotIn(status, (EXIT_SILENT, EXIT_ASK, EXIT_DENY))
        self.assertEqual(out, "")
        self.assertIn("RuntimeError", err)


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
                "explain", "--project", project, "git push --force"
            )
        # A status a caller can act on: `|| refuse` must refuse here.
        self.assertEqual(completed.returncode, EXIT_DENY)
        # Through a real process boundary, where the streams are the
        # operating system's rather than two StringIO objects.
        self.assertIn("deny", completed.stdout)
        self.assertEqual(completed.stderr, "")


if __name__ == "__main__":
    unittest.main()
