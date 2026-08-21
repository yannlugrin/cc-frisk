"""Layering, shadowing and the inspection that keeps them honest (§3.4).

Three invariants are what §3.4 leaves no freedom about, and each has its
class here: sources compose in an explicit total order, the operator's
own declarations always win, and the effective registry is inspectable
so composition can never hide a rule.

The engine's default layers are declarations like any other, and this
file treats them that way: they are shadowed, amended and dropped by
exactly the mechanism a collection's entries are.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Callable

from frisk.declare import (
    Arity,
    accounted,
    amend,
    ask,
    bare,
    benign_assignments,
    deny,
    every_operand,
    flag,
    one_of,
    path_under,
    silent,
    takes_value,
    tool,
    use,
    wrapper,
)
from frisk.errors import ConfigurationError
from frisk.registry import ENGINE_LAYER, PROJECT_LAYER, Registry, collecting

STARTER = """
from frisk.declare import ask, deny, takes_value, tool

tool(
    "git",
    options=[takes_value("-C")],
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

INFRA = """
from frisk.declare import ask, tool

tool("git", rules=[ask("push", reason="Pushing is reviewed here.")])
"""

GATED = """
from frisk.declare import ask, grant, no_operands, tool

tool(
    "stubtool",
    default=ask(reason="stubtool changes infrastructure."),
    grants=[
        grant(
            "clean",
            when=no_operands(),
            reason="Cleaning nothing in particular.",
            label="empty clean",
        )
    ],
)
"""

ALIASED = """
from frisk.declare import ask, handoff, tool

tool(
    "docker",
    aliases=["podman"],
    handoffs=[handoff("run", keeps_operands=1)],
    rules=[ask("push", reason="A registry write.")],
)
"""

ASSIGNED = """
from frisk.declare import accounted, ask, tool

tool(
    "git",
    assignments=[accounted("GIT_PAGER")],
    rules=[ask("push", reason="A push publishes work.")],
)
"""


class CollectionFixture(unittest.TestCase):
    """A directory of collection files, as the config directory is."""

    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name)
        (self.base / "starter.py").write_text(STARTER)
        (self.base / "infra.py").write_text(INFRA)

    def write_collection(self, name: str, source: str) -> None:
        """One more collection file, for the cases that need one."""
        (self.base / f"{name}.py").write_text(source)

    def compose(
        self,
        declare: Callable[[], None],
        *,
        with_defaults: bool = False,
        base: Path | None = None,
    ) -> Registry:
        with collecting(
            base_dir=str(base or self.base), with_defaults=with_defaults
        ) as declared:
            declare()
        return declared.registry()


class EngineDefaultTests(CollectionFixture):
    """Universal shell knowledge, shipped as ordinary declarations."""

    def setUp(self) -> None:
        super().setUp()
        self.registry = self.compose(lambda: None, with_defaults=True)

    def test_the_wrapper_layer_is_there(self) -> None:
        # The corpus's wrapper facts hold across all three of its
        # policy contexts, so these are engine knowledge, not policy.
        for name in ("sudo", "env", "timeout", "nice", "xargs", "nohup"):
            with self.subTest(name=name):
                entry = self.registry.lookup(name)
                assert entry is not None
                self.assertEqual(entry.kind, "wrapper")

    def test_a_wrapper_that_keeps_an_operand_says_so(self) -> None:
        # Corpus: `timeout 30 stubtool wipe` → deny, which needs the
        # duration stepped over rather than read as the command.
        entry = self.registry.lookup("timeout")
        assert entry is not None
        self.assertEqual(entry.keeps_operands, 1)
        self.assertEqual(entry.flags["-k"], Arity.VALUE)

    def test_only_the_value_taking_options_are_declared(self) -> None:
        # Corpus: `sudo --prompt-file /tmp/p stubtool wipe` → ask, and
        # the corpus states why — `--prompt-file` is deliberately *not*
        # declared, so the walk presumes it bare, lands on `/tmp/p`,
        # and loses the thread. Declaring it here would silently turn
        # that adjudicated ask into a deny.
        entry = self.registry.lookup("sudo")
        assert entry is not None
        self.assertEqual(entry.flags["-u"], Arity.VALUE)
        self.assertNotIn("--prompt-file", entry.flags)

    def test_every_wrapper_the_corpus_relies_on_is_declared(
        self,
    ) -> None:
        # Spot-checking a few names would let a missing
        # `keeps_operands` on `flock` surface for the first time at the
        # parity audit, against a ruling written years earlier.
        for name, (values, keeps) in CORPUS_WRAPPERS.items():
            with self.subTest(name=name):
                entry = self.registry.lookup(name)
                assert entry is not None
                self.assertEqual(entry.kind, "wrapper")
                self.assertEqual(entry.keeps_operands, keeps)
                self.assertEqual(
                    sorted(
                        flag
                        for flag, arity in entry.flags.items()
                        if arity is Arity.VALUE
                    ),
                    sorted(values),
                )

    def test_xargs_is_the_stdin_fed_runner(self) -> None:
        # Its command word is visible and its operands are not, which
        # is what makes operand conditions on the inner command
        # unprovable (§4.3).
        entry = self.registry.lookup("xargs")
        assert entry is not None
        self.assertTrue(entry.operands_from_stdin)

    def test_eval_joins_its_operands_instead_of_taking_a_payload(
        self,
    ) -> None:
        # Corpus: `eval stubtool wipe`, `eval "stubtool wipe"` and
        # `eval 'stubtool wipe'` all deny, while `eval` alone is
        # silent. Stepping over it would leave the quoted forms as one
        # unrecognizable token.
        entry = self.registry.lookup("eval")
        assert entry is not None
        self.assertEqual(entry.kind, "shell")
        self.assertTrue(entry.joins_operands)

    def test_the_benign_assignment_layer_is_declared(self) -> None:
        # §3.2's display/locale class. Without it every project would
        # have to teach the engine its own locale before
        # `LC_ALL=C git status` stopped asking.
        described = " ".join(
            str(assignment.name)
            for assignment in self.registry.benign_assignments()
        )
        for expected in ("LC_", "LANG", "TZ", "NO_COLOR"):
            with self.subTest(name=expected):
                self.assertIn(expected, described)

    def test_shells_and_interpreters_are_declared_apart(self) -> None:
        for name in ("sh", "bash"):
            with self.subTest(name=name):
                entry = self.registry.lookup(name)
                assert entry is not None
                self.assertEqual(entry.kind, "shell")
        python = self.registry.lookup("python3")
        assert python is not None
        self.assertEqual(python.kind, "interpreter")

    def test_the_default_layers_carry_no_rules_and_no_grants(
        self,
    ) -> None:
        # Which is what keeps them outside the coverage gate of §8.2:
        # there is nothing here for a project's cases to prove.
        for entry in self.registry.entries():
            with self.subTest(name=entry.name):
                self.assertEqual(entry.rules, ())
                self.assertEqual(entry.grants, ())

    def test_they_are_attributed_to_the_engine_layer(self) -> None:
        entry = self.registry.lookup("sudo")
        assert entry is not None
        self.assertEqual(entry.source.layer, ENGINE_LAYER)


#: The wrapper layer the corpus states as fact across all three of its
#: policy contexts: each name, the options it takes a value for, and the
#: positional operands it keeps before the wrapped command begins.
#: Undeclared options are presumed bare, so this table is the whole of
#: what the engine claims to know. Several corpus rulings depend on an
#: exact entry — most sharply `sudo`, whose `--prompt-file` is
#: deliberately absent.
CORPUS_WRAPPERS = {
    "sudo": (("-u", "--user", "-g", "--group", "-p", "--prompt"), 0),
    "doas": (("-u", "-C"), 0),
    "env": (("-u", "--unset", "-C", "--chdir", "-S", "--split-string"), 0),
    "command": ((), 0),
    "builtin": ((), 0),
    "exec": (("-a",), 0),
    "nohup": ((), 0),
    "setsid": ((), 0),
    "time": (("-f", "--format", "-o", "--output"), 0),
    "nice": (("-n", "--adjustment"), 0),
    "ionice": (("-c", "-n", "-p"), 0),
    "stdbuf": (
        ("-i", "-o", "-e", "--input", "--output", "--error"),
        0,
    ),
    "timeout": (("-s", "--signal", "-k", "--kill-after"), 1),
    "chrt": (("-p",), 1),
    "taskset": (("-c", "-p"), 1),
    "flock": (("-w", "--wait", "-E", "--conflict-exit-code"), 1),
    "xargs": (
        (
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
        ),
        0,
    ),
}


class ShadowingTests(CollectionFixture):
    """Per-name shadowing, in both required forms (§3.4)."""

    def test_a_redeclaration_replaces_what_was_beneath(self) -> None:
        # Promoting a wrapper to a rule-bearing tool is the need
        # prototyping demonstrated; the old declaration must not
        # survive underneath it.
        def declare() -> None:
            tool(
                "sudo",
                default=ask(reason="Everything sudo runs is elevated."),
            )

        entry = self.compose(declare, with_defaults=True).lookup("sudo")
        assert entry is not None
        self.assertEqual(entry.kind, "tool")
        self.assertEqual(entry.flags, {})
        self.assertEqual(entry.source.layer, PROJECT_LAYER)

    def test_an_amendment_keeps_what_it_does_not_touch(self) -> None:
        def declare() -> None:
            amend("sudo", flags=[takes_value("--prompt-file")])

        entry = self.compose(declare, with_defaults=True).lookup("sudo")
        assert entry is not None
        self.assertEqual(entry.kind, "wrapper")
        self.assertEqual(entry.flags["-u"], Arity.VALUE)
        self.assertEqual(entry.flags["--prompt-file"], Arity.VALUE)

    def test_an_amendment_can_remove_a_flag(self) -> None:
        # §3.4 is explicit that update must remove as well as add.
        def declare() -> None:
            amend("sudo", drop_flags=["-u"])

        entry = self.compose(declare, with_defaults=True).lookup("sudo")
        assert entry is not None
        self.assertNotIn("-u", entry.flags)

    def test_an_amendment_can_remove_a_rule_by_label(self) -> None:
        def declare() -> None:
            use("starter")
            amend("git", drop=["forced push"])

        entry = self.compose(declare).lookup("git")
        assert entry is not None
        self.assertEqual(
            [placed.label for placed in entry.rules], ["git:ask:commit"]
        )

    def test_a_rule_without_a_label_gets_a_readable_one(self) -> None:
        # `amend`'s `drop` takes labels, so every rule needs one an
        # operator can read off `frisk registry` — the derived form is
        # what a collection's unlabelled rules are dropped by.
        def declare() -> None:
            use("starter")

        entry = self.compose(declare).lookup("git")
        assert entry is not None
        self.assertIn(
            "git:ask:commit", [placed.label for placed in entry.rules]
        )

    def test_an_amendment_reaches_a_collection_s_grant(self) -> None:
        self.write_collection("gated", GATED)

        def declare() -> None:
            use("gated")
            amend("stubtool", drop=["empty clean"])

        entry = self.compose(declare).lookup("stubtool")
        assert entry is not None
        self.assertEqual(entry.grants, ())

    def test_an_amendment_can_remove_an_alias_and_a_handoff(
        self,
    ) -> None:
        self.write_collection("aliased", ALIASED)

        def declare() -> None:
            use("aliased")
            amend("docker", drop_aliases=["podman"], drop_handoffs=["run"])

        registry = self.compose(declare)
        entry = registry.lookup("docker")
        assert entry is not None
        self.assertEqual(entry.handoffs, ())
        self.assertIsNone(registry.lookup("podman"))

    def test_an_amendment_can_remove_an_accounted_assignment(
        self,
    ) -> None:
        self.write_collection("assigned", ASSIGNED)

        def declare() -> None:
            use("assigned")
            amend("git", drop_assignments=["GIT_PAGER"])

        entry = self.compose(declare).lookup("git")
        assert entry is not None
        self.assertEqual(entry.assignments, ())

    def test_a_wrapper_can_be_given_a_default_verdict(self) -> None:
        # §4.3 names this as the operator's mechanism for gating
        # everything a runner runs: shadow the wrapper into something
        # with an ask default, rather than teach the engine a
        # heuristic.
        def declare() -> None:
            wrapper(
                "myrunner",
                flags=[takes_value("--as")],
                default=ask(reason="Whatever myrunner runs is unseen."),
            )

        entry = self.compose(declare).lookup("myrunner")
        assert entry is not None
        assert entry.default is not None
        self.assertEqual(entry.kind, "wrapper")

    def test_amending_a_name_nothing_declared_is_refused(self) -> None:
        # An amendment that silently does nothing is a boundary the
        # operator believes they have.
        with self.assertRaises(ConfigurationError):
            self.compose(lambda: amend("gti", drop_flags=["-u"]))

    def test_a_wrapper_can_be_removed_by_replacing_it(self) -> None:
        # §3.4's "effectively removing an entry whose name collides
        # with a project binary": the name stays registered, but as
        # the project's own silent tool rather than as a runner.
        def declare() -> None:
            tool("time", default=silent())

        entry = self.compose(declare, with_defaults=True).lookup("time")
        assert entry is not None
        self.assertEqual(entry.kind, "tool")


class BenignAssignmentTests(CollectionFixture):
    """The third default layer, shadowable like the others (§3.2)."""

    def test_a_project_can_add_to_it(self) -> None:
        def declare() -> None:
            benign_assignments(accounted("PROJECT_LOCALE"))

        registry = self.compose(declare, with_defaults=True)
        names = [
            str(assignment.name)
            for assignment in registry.benign_assignments()
        ]
        self.assertIn("PROJECT_LOCALE", names)
        self.assertIn("TZ", names)

    def test_a_project_can_drop_from_it(self) -> None:
        # Shadowable means removable: a variable the engine considers
        # unable to direct execution may still matter here.
        def declare() -> None:
            benign_assignments(drop=["TZ"])

        registry = self.compose(declare, with_defaults=True)
        names = [
            str(assignment.name)
            for assignment in registry.benign_assignments()
        ]
        self.assertNotIn("TZ", names)

    def test_dropping_what_is_not_there_is_refused(self) -> None:
        with self.assertRaises(ConfigurationError):
            self.compose(
                lambda: benign_assignments(drop=["NOT_A_VARIABLE"]),
                with_defaults=True,
            )


class CollectionOrderTests(CollectionFixture):
    """An explicit total order, and the operator last (§3.4)."""

    def test_a_collection_composes_over_the_engine_defaults(
        self,
    ) -> None:
        registry = self.compose(lambda: use("starter"), with_defaults=True)
        git = registry.lookup("git")
        sudo = registry.lookup("sudo")
        assert git is not None and sudo is not None
        self.assertEqual(git.source.layer, "collection:starter")
        self.assertEqual(sudo.source.layer, ENGINE_LAYER)

    def test_later_collections_override_earlier_ones(self) -> None:
        def declare() -> None:
            use("starter")
            use("infra")

        entry = self.compose(declare).lookup("git")
        assert entry is not None
        self.assertEqual(entry.source.layer, "collection:infra")
        self.assertEqual(len(entry.rules), 1)

    def test_the_order_is_the_declared_one_not_the_reverse(self) -> None:
        def declare() -> None:
            use("infra")
            use("starter")

        entry = self.compose(declare).lookup("git")
        assert entry is not None
        self.assertEqual(entry.source.layer, "collection:starter")

    def test_the_operator_wins_wherever_the_adoption_sits(self) -> None:
        # `use()` is an adoption, not a point in a stream: a config
        # that declares its own git before adopting a collection does
        # not thereby lose to it.
        def declare() -> None:
            tool("git", default=deny(reason="This project's own git."))
            use("starter")

        entry = self.compose(declare).lookup("git")
        assert entry is not None
        self.assertEqual(entry.source.layer, PROJECT_LAYER)

    def test_the_same_collection_twice_is_refused(self) -> None:
        def declare() -> None:
            use("starter")
            use("starter")

        with self.assertRaises(ConfigurationError):
            self.compose(declare)

    def test_a_collection_that_is_not_there_is_refused(self) -> None:
        with self.assertRaises(ConfigurationError):
            self.compose(lambda: use("absent"))

    def test_adopting_a_collection_with_nowhere_to_look_is_refused(
        self,
    ) -> None:
        # Without a configuration directory there is no "beside the
        # config" to resolve against, and searching for one would be
        # the engine choosing what to execute.
        with (
            self.assertRaises(ConfigurationError),
            collecting(with_defaults=False),
        ):
            use("starter")

    def test_a_collection_outside_the_config_directory_is_refused(
        self,
    ) -> None:
        # The engine executes the project's own configuration and what
        # sits beside it, and nothing else (§5.1).
        with self.assertRaises(ConfigurationError):
            self.compose(lambda: use("../starter"))


class RegistryLayoutTests(CollectionFixture):
    """The printed layout is contract, not rendering (§3.4, §9).

    It is what the operator reads at every later step's manual test, so
    a format that drifts makes two sessions describe the same boundary
    differently. These cases fix the shape; `InspectionTests` fixes
    what has to appear in it.
    """

    def setUp(self) -> None:
        super().setUp()
        self.write_collection("gated", GATED)

        def declare() -> None:
            use("starter")
            tool(
                "adeploy",
                default=ask(reason="Deploys reach production."),
            )

        self.text = self.compose(declare).describe()
        self.lines = self.text.splitlines()

    def block_for(self, header: str) -> list[str]:
        """The lines of one entry block, header excluded."""
        start = self.lines.index(header)
        collected = []
        for line in self.lines[start + 1 :]:
            if not line.strip():
                break
            collected.append(line)
        return collected

    def test_an_entry_opens_with_its_kind_and_name(self) -> None:
        self.assertIn("tool git", self.lines)
        self.assertIn("tool adeploy", self.lines)

    def test_entry_blocks_are_separated_by_blank_lines(self) -> None:
        self.assertIn("", self.lines[self.lines.index("tool git") + 1 :])

    def test_entries_are_ordered_by_name(self) -> None:
        # Two runs of one configuration must compare line by line.
        self.assertLess(
            self.lines.index("tool adeploy"),
            self.lines.index("tool git"),
        )

    def test_an_entry_s_fields_are_indented_two_spaces(self) -> None:
        for line in self.block_for("tool git"):
            with self.subTest(line=line):
                self.assertTrue(line.startswith("  "))
                self.assertFalse(line.startswith("     "))

    def test_the_source_field_names_layer_file_and_line(self) -> None:
        self.assertRegex(
            self.text, r"\n  source: collection:starter starter\.py:\d+"
        )

    def test_a_rule_reads_verdict_label_subcommand(self) -> None:
        self.assertIn("  deny [forced push] push", self.lines)

    def test_a_rule_s_own_lines_are_indented_four_spaces(self) -> None:
        start = self.lines.index("  deny [forced push] push")
        self.assertEqual(
            self.lines[start + 1],
            "    reason: A forced push rewrites remote history.",
        )
        self.assertRegex(
            self.lines[start + 2],
            r"^    source: collection:starter starter\.py:\d+$",
        )

    def test_rules_keep_their_declaration_order(self) -> None:
        # The ranking decides a verdict, not the order (§3.2) — but an
        # operator comparing this block against the file they wrote
        # needs the two to run in step.
        self.assertLess(
            self.lines.index("  deny [forced push] push"),
            self.lines.index("  ask [git:ask:commit] commit"),
        )

    def test_a_field_a_declaration_did_not_use_is_absent(self) -> None:
        # An empty `aliases:` line is noise in a registry an operator
        # scans, and noise is what makes a rule easy to miss.
        self.assertNotIn("  aliases:", self.block_for("tool adeploy"))

    def test_the_two_sections_follow_the_entries(self) -> None:
        self.assertIn("benign assignments", self.lines)
        self.assertIn("redirections", self.lines)
        self.assertLess(
            self.lines.index("tool git"),
            self.lines.index("benign assignments"),
        )

    def test_a_matcher_carries_its_outcome_as_a_suffix(self) -> None:
        def declare() -> None:
            tool(
                "stubtool",
                rules=[
                    ask(
                        "apply",
                        when=flag("--mode", one_of("destroy")),
                        reason="A destroying mode.",
                        label="destroying mode",
                    )
                ],
            )

        described = self.compose(declare).describe(value="destroy")
        line = next(
            each
            for each in described.splitlines()
            if each.strip().startswith("when:")
        )
        self.assertTrue(line.startswith("    when: "))
        self.assertTrue(line.endswith(" [satisfied]"))

    def test_the_whole_output_is_ascii(self) -> None:
        self.assertTrue(self.text.isascii())


class InspectionTests(CollectionFixture):
    """The effective registry is inspectable, by requirement (§3.4, §9)."""

    def setUp(self) -> None:
        super().setUp()

        def declare() -> None:
            use("starter")
            wrapper("myrunner", flags=[takes_value("--as")])
            amend(
                "git",
                rules=[
                    ask(
                        "push",
                        reason="Pushing publishes work.",
                        label="any push",
                    )
                ],
            )

        self.registry = self.compose(declare, with_defaults=True)
        self.text = self.registry.describe()

    def test_it_names_every_effective_entry(self) -> None:
        for name in ("git", "sudo", "myrunner"):
            with self.subTest(name=name):
                self.assertIn(name, self.text)

    def test_it_says_which_layer_each_came_from(self) -> None:
        self.assertIn("collection:starter", self.text)
        self.assertIn(PROJECT_LAYER, self.text)
        self.assertIn(ENGINE_LAYER, self.text)

    def test_it_prints_the_line_a_declaration_was_written_on(
        self,
    ) -> None:
        # The layer decides a conflict; the file and line are what an
        # operator opens to change it.
        self.assertIn("starter.py:", self.text)

    def test_it_prints_the_label_an_amendment_would_drop(self) -> None:
        self.assertIn("forced push", self.text)
        self.assertIn("any push", self.text)

    def test_it_carries_the_reason_of_every_rule(self) -> None:
        self.assertIn("A forced push rewrites remote history.", self.text)

    def test_a_value_annotates_every_matcher_with_its_outcome(
        self,
    ) -> None:
        def declare() -> None:
            tool(
                "stubtool",
                flags=[bare("--syntax-check")],
                rules=[
                    ask(
                        "apply",
                        when=flag("--mode", one_of("destroy")),
                        reason="A destroying mode.",
                    )
                ],
            )

        registry = self.compose(declare)
        # Bracketed, because "unsatisfied" contains "satisfied": an
        # assertion on the bare word passes whichever answer came back,
        # which is the shape of defect D-032 exists to stop.
        self.assertIn("[satisfied]", registry.describe(value="destroy"))
        self.assertIn("[unsatisfied]", registry.describe(value="check"))
        self.assertNotIn("[satisfied]", registry.describe(value="check"))

    def test_a_value_it_cannot_decide_reads_as_unproven(self) -> None:
        def declare() -> None:
            tool(
                "stubtool",
                rules=[
                    ask(
                        "clean",
                        when=every_operand(path_under("/tmp")),
                        reason="Cleaning outside scratch space.",
                    )
                ],
            )

        registry = self.compose(declare)
        # A relative value against an absolute boundary: the third
        # answer has to reach the inspection surface too, or the
        # surface cannot show the model it exists to show.
        self.assertIn("[unproven]", registry.describe(value="tmp/x"))
