"""What the engine ships as its default layers (§3.4).

Universal shell knowledge, not project policy: the programs whose job is
to run other programs, the shells whose `-c` payload is a command line,
and the interpreters a registered tool can be run through. It lives
engine-side because every project needs it and no project should have to
write it.

**This file is about content, not about the API.** That a `wrapper(…)`
declaration composes into an entry carrying its arities is
`test_declarations.py`'s subject, proven against a fixture invented for
the case. Here the subject is what frisk itself declares, and the
corpus's rulings rest on it directly: a missing `keeps_operands` on
`flock`, or a `--prompt-file` declared for `sudo`, changes what a real
command line resolves to while every API case still passes. Nothing
else in the suite would notice before the parity audit.

The values come from `.claude/refs/behavior-corpus.md`, whose wrapper
layer is stated as fact across all three of its policy contexts —
"declared value-taking options, and positional operands a wrapper keeps
for itself before the wrapped command begins". Undeclared options are
presumed bare (§4.3), so what each case asserts is the *whole* of what
the engine claims to know about that program: the exact value-taking
set, and nothing beyond it.

One wrapper per method, deliberately. Each reads as that program's
contract rather than as a row of a shared table, `unittest -k sudo`
runs just that one, and a correction to one wrapper is a change to its
own case instead of an edit to a table sixteen programs share.
"""

from __future__ import annotations

import unittest
from collections.abc import Sequence

from frisk.declare import Arity
from frisk.registry import ENGINE_LAYER, Entry, Kind, Registry, collecting


def engine_defaults() -> Registry:
    """The engine's own layers, with nothing composed on top."""
    with collecting(with_defaults=True) as declared:
        pass
    return declared.registry()


class DefaultLayerTests(unittest.TestCase):
    """Properties of the layers as a whole."""

    def setUp(self) -> None:
        self.registry = engine_defaults()

    def test_they_carry_no_rules_and_no_grants(self) -> None:
        # This is why §8.2 lets them stand outside the coverage gate:
        # they are analysis knowledge, and there is nothing here for a
        # project's cases to prove. The moment a config shadows one
        # into a rule-bearing tool, the config owes the cases.
        for entry in self.registry.entries():
            with self.subTest(name=entry.name):
                self.assertEqual(entry.rules, ())
                self.assertEqual(entry.grants, ())

    def test_every_declared_flag_is_value_taking(self) -> None:
        # Not a coincidence worth rediscovering: §4.3 presumes an
        # undeclared option bare, so a `bare` declaration here adds
        # nothing, and `may_take_value` claims a program accepts both
        # `--flag value` and `--flag`, which is true of some
        # hand-rolled CLIs and of none of these. A default that needs
        # another arity is a deliberate exception and should fail this
        # until it is argued for.
        for entry in self.registry.entries():
            for flag, arity in entry.flags.items():
                with self.subTest(name=entry.name, flag=flag):
                    self.assertEqual(arity, Arity.VALUE)

    def test_they_are_attributed_to_the_engine_layer(self) -> None:
        # So `frisk registry` shows where an entry came from, and a
        # configuration that shadows one can be seen to have done it.
        for entry in self.registry.entries():
            with self.subTest(name=entry.name):
                self.assertEqual(entry.source.layer, ENGINE_LAYER)


class WrapperDefaultTests(unittest.TestCase):
    """Each wrapper's own contract (§3.4, §4.3).

    A wrapper's declaration is a best effort by construction: undeclared
    options are presumed bare and stepped over, and the walk is lost
    only when the position it lands on resolves to nothing. That makes
    the exact value-taking set load-bearing in both directions —
    declaring too few loses the thread, declaring too many swallows the
    command.
    """

    def setUp(self) -> None:
        self.registry = engine_defaults()

    def wrapper(
        self, name: str, values: Sequence[str], keeps: int = 0
    ) -> Entry:
        """Assert one wrapper's whole contract, and return its entry.

        The flag set is compared exactly, arities included, because
        this layer has only one arity to declare: §4.3 presumes an
        undeclared wrapper option bare, so a value-taking one is the
        only kind worth writing down. An extra `bare` declaration would
        be noise, and a `may_take_value` would consume a token
        conditionally and move where the walk lands — which is the
        failure this table exists to prevent, and which a check on the
        value-taking names alone would not see.
        """
        entry = self.registry.lookup(name)
        assert entry is not None, f"{name} is not declared"
        self.assertEqual(entry.kind, Kind.WRAPPER)
        self.assertEqual(entry.keeps_operands, keeps)
        self.assertEqual(
            dict(entry.flags),
            dict.fromkeys(values, Arity.VALUE),
        )
        return entry

    def test_sudo(self) -> None:
        # `--prompt-file` is deliberately absent, and the corpus
        # depends on the absence: `sudo --prompt-file /tmp/p stubtool
        # wipe` → **ask**, because the walk presumes the option bare,
        # lands on `/tmp/p`, and loses the thread. Declaring it here
        # would silently turn that adjudicated ask into a deny.
        self.wrapper(
            "sudo", ["-u", "--user", "-g", "--group", "-p", "--prompt"]
        )

    def test_doas(self) -> None:
        self.wrapper("doas", ["-u", "-C"])

    def test_env(self) -> None:
        # Corpus: `env STUB_QUIET=1 stubtool --syntax-check a.yml` →
        # silent, so the assignment has to survive the walk.
        self.wrapper(
            "env", ["-u", "--unset", "-C", "--chdir", "-S", "--split-string"]
        )

    def test_command(self) -> None:
        self.wrapper("command", [])

    def test_builtin(self) -> None:
        self.wrapper("builtin", [])

    def test_exec(self) -> None:
        self.wrapper("exec", ["-a"])

    def test_nohup(self) -> None:
        # Corpus: `nohup stubtool wipe` → deny.
        self.wrapper("nohup", [])

    def test_setsid(self) -> None:
        self.wrapper("setsid", [])

    def test_time(self) -> None:
        # Corpus: `time stubtool wipe` → deny, `time make check` →
        # silent.
        self.wrapper("time", ["-f", "--format", "-o", "--output"])

    def test_nice(self) -> None:
        # Corpus: `nice -n 5 stubtool wipe` → deny, which needs `-n` to
        # swallow the 5.
        self.wrapper("nice", ["-n", "--adjustment"])

    def test_ionice(self) -> None:
        self.wrapper("ionice", ["-c", "-n", "-p"])

    def test_stdbuf(self) -> None:
        self.wrapper(
            "stdbuf", ["-i", "-o", "-e", "--input", "--output", "--error"]
        )

    def test_timeout(self) -> None:
        # Corpus: `timeout 30 stubtool wipe` and `timeout -k 5 30
        # stubtool wipe` both deny — the duration is a kept operand,
        # not the command.
        self.wrapper(
            "timeout", ["-s", "--signal", "-k", "--kill-after"], keeps=1
        )

    def test_chrt(self) -> None:
        self.wrapper("chrt", ["-p"], keeps=1)

    def test_taskset(self) -> None:
        self.wrapper("taskset", ["-c", "-p"], keeps=1)

    def test_flock(self) -> None:
        self.wrapper(
            "flock", ["-w", "--wait", "-E", "--conflict-exit-code"], keeps=1
        )

    def test_xargs(self) -> None:
        # Corpus: `xargs -n 1 stubtool wipe` → deny. Its own operands
        # arrive on stdin and are invisible by construction, which is
        # what makes operand conditions on the inner command
        # unprovable (§4.3).
        entry = self.wrapper(
            "xargs",
            [
                "-n",
                "-P",
                "-I",
                "-d",
                "-E",
                "-L",
                "-s",
                "--max-args",
                "--max-procs",
                "--replace",
                "--delimiter",
                "--max-lines",
            ],
        )
        self.assertTrue(entry.operands_from_stdin)


class ShellDefaultTests(unittest.TestCase):
    """Programs whose argument is itself a command line (§4.3).

    A shell's `-c` payload is re-analyzed in full, so the flag has to
    be declared value-taking or the payload is read as an operand and
    the command inside it is never seen. The combined spellings
    (`-lc`, `-ec`) are a payload rule rather than an arity one and are
    handled where the line is read.
    """

    def setUp(self) -> None:
        self.registry = engine_defaults()

    def shell(
        self, name: str, values: Sequence[str], joins: bool = False
    ) -> Entry:
        """Assert one shell's whole contract, and return its entry."""
        entry = self.registry.lookup(name)
        assert entry is not None, f"{name} is not declared"
        self.assertEqual(entry.kind, Kind.SHELL)
        self.assertEqual(entry.joins_operands, joins)
        self.assertEqual(dict(entry.flags), dict.fromkeys(values, Arity.VALUE))
        return entry

    def test_sh(self) -> None:
        # Corpus: `sh -c 'stubtool wipe'` → deny. `-o` is declared for
        # the same reason `-c` is: it swallows the token after it, and
        # a walk that reads `errexit` as the payload finds nothing.
        self.shell("sh", ["-c", "-o"])

    def test_bash(self) -> None:
        # Corpus: `bash -lc 'stubtool wipe'` → deny, `bash -c
        # 'stubtool deploy.yml'` → ask.
        self.shell("bash", ["-c", "-o"])

    def test_eval(self) -> None:
        # Corpus: `eval stubtool wipe`, `eval "stubtool wipe"` and
        # `eval 'stubtool wipe'` all deny, while `eval` alone is
        # silent. It has no payload flag at all — the joined operands
        # are the command line — and stepping over it would leave the
        # quoted forms as one unrecognizable token.
        self.shell("eval", [], joins=True)


class InterpreterDefaultTests(unittest.TestCase):
    """Programs walked to the file they run (§4.2).

    `python3 tools/deploy.py` is judged as `tools/deploy.py`'s
    registration if one exists, so the walk's job is to find the file
    operand — and every option that swallows a token moves where it
    lands. `python3 -X dev tools/deploy.py` with `-X` undeclared reads
    `dev` as the file and never reaches the registration.

    Each set is the value-taking options that would shift that walk,
    not an exhaustive reading of the program's manual. Under-declaring
    fails toward asking (§4.3: an unknown value-taking option loses the
    walk, and a lost walk asks), while over-declaring swallows an
    operand — so the conservative set is the safe one, and the surprise
    loop grows it. Program text in another language is never read as
    shell, so these payloads stay opaque: corpus, `python3 -c
    'print(1)'` → silent.
    """

    def setUp(self) -> None:
        self.registry = engine_defaults()

    def interpreter(self, name: str, values: Sequence[str]) -> Entry:
        """Assert one interpreter's whole contract."""
        entry = self.registry.lookup(name)
        assert entry is not None, f"{name} is not declared"
        self.assertEqual(entry.kind, Kind.INTERPRETER)
        self.assertEqual(dict(entry.flags), dict.fromkeys(values, Arity.VALUE))
        return entry

    def test_python3(self) -> None:
        # The bare ones — `-u`, `-B`, `-O` — need no declaration.
        self.interpreter(
            "python3",
            ["-c", "-m", "-W", "-X", "--check-hash-based-pycs"],
        )

    def test_node(self) -> None:
        self.interpreter(
            "node", ["-e", "--eval", "-p", "--print", "-r", "--require"]
        )

    def test_ruby(self) -> None:
        # `-i` is deliberately absent: its argument is optional and
        # attached, so declaring it value-taking would swallow the
        # script, and the layer declares only value-taking options.
        self.interpreter("ruby", ["-e", "-r", "-I", "-C", "-E", "-F"])

    def test_perl(self) -> None:
        # `-M` and `-m` are absent for the same reason: their module
        # name is attached (`-Mstrict`), so nothing follows to swallow.
        self.interpreter("perl", ["-e", "-E", "-I"])


class BenignAssignmentDefaultTests(unittest.TestCase):
    """The assignments no registered tool has to account for (§3.2)."""

    def setUp(self) -> None:
        self.registry = engine_defaults()

    def test_the_display_and_locale_class_is_declared(self) -> None:
        # Variables that cannot direct execution. Without this layer
        # `LC_ALL=C git status` is an unaccounted assignment on a
        # registered tool, and therefore an ask, in every project.
        declared = " ".join(
            str(assignment.name)
            for assignment in self.registry.benign_assignments()
        )
        for expected in ("LC_", "LANG", "TZ", "NO_COLOR"):
            with self.subTest(name=expected):
                self.assertIn(expected, declared)

    def test_execution_directing_variables_are_not_on_it(self) -> None:
        # The closed world of §3.2 exists for exactly these:
        # `GIT_SSH_COMMAND=… git fetch` runs an arbitrary program, and
        # git alone has dozens of siblings. An addition to the benign
        # layer is a decision to stop reading a variable at all.
        declared = {
            str(assignment.name)
            for assignment in self.registry.benign_assignments()
        }
        for name in ("GIT_SSH_COMMAND", "GIT_PAGER", "LD_PRELOAD", "PATH"):
            with self.subTest(name=name):
                self.assertNotIn(name, declared)
