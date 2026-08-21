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
    amend,
    ask,
    bare,
    deny,
    flag,
    one_of,
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


class CollectionFixture(unittest.TestCase):
    """A directory of collection files, as the config directory is."""

    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name)
        (self.base / "starter.py").write_text(STARTER)
        (self.base / "infra.py").write_text(INFRA)

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

    def test_a_collection_outside_the_config_directory_is_refused(
        self,
    ) -> None:
        # The engine executes the project's own configuration and what
        # sits beside it, and nothing else (§5.1).
        with self.assertRaises(ConfigurationError):
            self.compose(lambda: use("../starter"))


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
        self.assertIn("satisfied", registry.describe(value="destroy"))
        self.assertIn("unsatisfied", registry.describe(value="check"))
