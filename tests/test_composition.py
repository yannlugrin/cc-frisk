"""Layering, shadowing and the inspection that keeps them honest (§3.4).

Three invariants are what §3.4 leaves no freedom about, and each has its
class here: sources compose in an explicit total order, the operator's
own declarations always win, and the effective registry is inspectable
so composition can never hide a rule.

The engine's default layers appear here as *material*: they are
declarations like any other, so they are shadowed, amended and dropped
by exactly the mechanism a collection's entries are, and they make the
cheapest fixture for showing it. What those layers actually contain —
which wrappers, which arities, which kept operands — is
`test_defaults.py`'s subject, and a case here that asserted it would be
testing frisk's shipped knowledge through the composition machinery.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Callable

from frisk.declare import (
    DENY,
    SILENT,
    Arity,
    Assignment,
    accounted,
    amend,
    ask,
    bare,
    benign_assignments,
    case,
    cases,
    deny,
    drop,
    every_operand,
    flag,
    may_take_value,
    one_of,
    path_under,
    redirections,
    silent,
    takes_value,
    tool,
    use,
    wrapper,
)
from frisk.errors import ConfigurationError
from frisk.registry import (
    ENGINE_LAYER,
    PROJECT_LAYER,
    Cases,
    Entry,
    Kind,
    Registry,
    collecting,
)
from frisk.verdicts import Verdict

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

PROVEN = """
from frisk.declare import DENY, case, deny, tool

tool(
    "git",
    rules=[
        deny(
            "push",
            reason="A forced push rewrites remote history.",
            label="forced push",
        )
    ],
    cases=[case("git push --force", DENY)],
)
"""

UNLABELLED = """
from frisk.declare import ask, grant, no_operands, tool

tool(
    "stubtool",
    default=ask(reason="stubtool changes infrastructure."),
    grants=[
        grant(
            "clean",
            when=no_operands(),
            reason="Cleaning nothing in particular.",
        )
    ],
)
"""

RUNNERS = """
from frisk.declare import ask, takes_value, wrapper

wrapper(
    "sudo",
    flags=[takes_value("-u", "--user", "--prompt-file")],
    default=ask(reason="Everything sudo runs is elevated."),
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

    def beneath(self, name: str) -> Entry:
        """The entry a shadowing case starts from: engine layers only.

        Shadowing, amending and dropping are claims about a
        *transition*, and a case asserting only the result would pass
        on an engine that never declared the name in the first place.
        """
        entry = self.compose(lambda: None, with_defaults=True).lookup(name)
        assert entry is not None, f"{name} is not an engine default"
        return entry

    def compose(
        self,
        declare: Callable[[], None],
        *,
        with_defaults: bool = False,
        base: Path | None = None,
    ) -> Registry:
        with collecting(
            base_dir=base or self.base, with_defaults=with_defaults
        ) as declared:
            declare()
        return declared.registry()


class ShadowingTests(CollectionFixture):
    """Per-name shadowing, in both required forms (§3.4)."""

    def test_a_redeclaration_replaces_what_was_beneath(self) -> None:
        # Promoting a wrapper to a rule-bearing tool is the need
        # prototyping demonstrated; the old declaration must not
        # survive underneath it.
        beneath = self.beneath("sudo")
        self.assertEqual(beneath.kind, Kind.WRAPPER)
        self.assertEqual(beneath.flags["-u"], Arity.VALUE)

        def declare() -> None:
            tool(
                "sudo",
                default=ask(reason="Everything sudo runs is elevated."),
            )

        entry = self.compose(declare, with_defaults=True).lookup("sudo")
        assert entry is not None
        self.assertEqual(entry.kind, Kind.TOOL)
        self.assertEqual(entry.flags, {})
        self.assertEqual(entry.source.layer, PROJECT_LAYER)

    def test_an_amendment_keeps_what_it_does_not_touch(self) -> None:
        self.assertEqual(self.beneath("sudo").flags["-u"], Arity.VALUE)

        def declare() -> None:
            amend("sudo", flags=[takes_value("--prompt-file")])

        entry = self.compose(declare, with_defaults=True).lookup("sudo")
        assert entry is not None
        self.assertEqual(entry.kind, Kind.WRAPPER)
        self.assertEqual(entry.flags["-u"], Arity.VALUE)
        self.assertEqual(entry.flags["--prompt-file"], Arity.VALUE)

    def test_an_amendment_can_correct_an_arity(self) -> None:
        # §3.4 names this among what a config declaration must be able
        # to do to an engine default: "correcting its argument arity".
        # Re-declaring the flag replaces it — per-name shadowing, one
        # level down — which is why this needs no drop. `drop("-u")`
        # beside `takes_value("-u")` is the spelling that says two
        # things at once, and that pair is refused.
        self.assertEqual(self.beneath("sudo").flags["-u"], Arity.VALUE)

        def declare() -> None:
            amend("sudo", flags=[may_take_value("-u")])

        entry = self.compose(declare, with_defaults=True).lookup("sudo")
        assert entry is not None
        self.assertEqual(entry.flags["-u"], Arity.OPTIONAL_VALUE)

    def test_correcting_an_arity_keeps_the_rest_of_the_set(self) -> None:
        # A correction is not a replacement of the whole arity list:
        # sudo's other value-taking options are untouched, and
        # `--prompt-file` stays undeclared, so the corpus's adjudicated
        # `sudo --prompt-file /tmp/p stubtool wipe` → ask still holds.
        def declare() -> None:
            amend("sudo", flags=[may_take_value("-u")])

        entry = self.compose(declare, with_defaults=True).lookup("sudo")
        assert entry is not None
        self.assertEqual(entry.flags["--user"], Arity.VALUE)
        self.assertNotIn("--prompt-file", entry.flags)

    def test_an_amendment_can_remove_a_flag(self) -> None:
        # §3.4 is explicit that update must remove as well as add — and
        # "removed" is a claim about a transition, so the flag has to
        # be shown present before it is dropped.
        self.assertIn("-u", self.beneath("sudo").flags)

        def declare() -> None:
            amend("sudo", flags=[drop("-u")])

        entry = self.compose(declare, with_defaults=True).lookup("sudo")
        assert entry is not None
        self.assertNotIn("-u", entry.flags)

    def test_an_amendment_can_remove_a_rule_by_label(self) -> None:
        def declare() -> None:
            use("starter")
            amend("git", rules=[drop("forced push")])

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
            amend("stubtool", grants=[drop("empty clean")])

        entry = self.compose(declare).lookup("stubtool")
        assert entry is not None
        self.assertEqual(entry.grants, ())

    def test_an_unlabelled_grant_is_dropped_by_its_derived_label(
        self,
    ) -> None:
        # §3.4 requires narrowing an adopted collection's grants, and a
        # collection that shipped unlabelled ones would otherwise be
        # untrimmable — `tests/corpus/context_b.py` declares five. A
        # grant has no verdict, so `grant` fills that slot.
        self.write_collection("unlabelled", UNLABELLED)

        def declare() -> None:
            use("unlabelled")
            amend("stubtool", grants=[drop("stubtool:grant:clean")])

        entry = self.compose(declare).lookup("stubtool")
        assert entry is not None
        self.assertEqual(entry.grants, ())

    def test_a_declaration_with_no_subcommand_stops_at_the_verdict(
        self,
    ) -> None:
        # `sudo` carries a rule about the tool itself, so there is no
        # subcommand to end the label with.
        def declare() -> None:
            wrapper(
                "sudo",
                rules=[ask(reason="Running as another user.")],
            )

        entry = self.compose(declare).lookup("sudo")
        assert entry is not None
        self.assertEqual(
            [placed.label for placed in entry.rules], ["sudo:ask"]
        )

    def test_an_amendment_can_remove_an_alias_and_a_handoff(
        self,
    ) -> None:
        self.write_collection("aliased", ALIASED)

        def declare() -> None:
            use("aliased")
            amend(
                "docker",
                aliases=[drop("podman")],
                handoffs=[drop("run")],
            )

        registry = self.compose(declare)
        entry = registry.lookup("docker")
        assert entry is not None
        self.assertEqual(entry.handoffs, ())
        self.assertIsNone(registry.lookup("podman"))

    def test_an_amendment_can_narrow_an_accounted_assignment(
        self,
    ) -> None:
        # The same shadowing one level down, on a tool: a collection
        # accounts for GIT_PAGER outright, and a project accepts it
        # only as `cat` — §3.2's own example. Re-declaring the name
        # replaces it; nothing is dropped first.
        self.write_collection("assigned", ASSIGNED)
        pager = one_of("cat")

        def declare() -> None:
            use("assigned")
            amend("git", assignments=[accounted("GIT_PAGER", pager)])

        entry = self.compose(declare).lookup("git")
        assert entry is not None
        self.assertEqual(len(entry.assignments), 1)
        self.assertEqual(entry.assignments[0].name, "GIT_PAGER")
        self.assertIs(entry.assignments[0].value, pager)

    def test_an_amendment_can_remove_an_accounted_assignment(
        self,
    ) -> None:
        self.write_collection("assigned", ASSIGNED)

        def declare() -> None:
            use("assigned")
            amend("git", assignments=[drop("GIT_PAGER")])

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
        self.assertEqual(entry.kind, Kind.WRAPPER)

    def test_an_amendment_can_close_an_adopted_world(self) -> None:
        # Without this, gating a collection's rules-only tool means
        # replacing the whole declaration and re-listing every flag it
        # already declared.
        self.write_collection("starter", STARTER)

        def declare() -> None:
            use("starter")
            amend("git", closed_world=True)

        entry = self.compose(declare).lookup("git")
        assert entry is not None
        self.assertTrue(entry.gated)

    def test_an_amendment_leaves_the_world_as_it_found_it(self) -> None:
        # The reason the keyword is three-valued: a plain flag would
        # re-open a gated tool on every amendment that happened not to
        # mention it, and un-gating is not something an amendment about
        # a flag should do in passing.
        self.write_collection("gated", GATED)

        def declare() -> None:
            use("gated")
            amend("stubtool", flags=[bare("--quiet")])

        entry = self.compose(declare).lookup("stubtool")
        assert entry is not None
        self.assertTrue(entry.gated)

    def test_opening_a_world_that_still_has_grants_is_refused(
        self,
    ) -> None:
        # A grant that an undeclared flag could escape proves nothing,
        # so §3.2's "universally and closed-world" makes the pair a
        # contradiction rather than a preference.
        self.write_collection("gated", GATED)

        def declare() -> None:
            use("gated")
            amend("stubtool", closed_world=False)

        with self.assertRaises(ConfigurationError):
            self.compose(declare)

    def test_dropping_the_last_grant_reopens_a_derived_world(
        self,
    ) -> None:
        # Unset means *derived*, evaluated on the state the amendment
        # leaves behind: closed exactly when grants are declared. What
        # the tool keeps is its declared default, which is the point —
        # dropping the last grant says "no shape bypasses the default
        # here", not "this tool is unguarded". Removing the granted
        # behaviour itself is a `tool()` redeclaration, which replaces.
        self.write_collection("gated", GATED)

        def declare() -> None:
            use("gated")
            amend("stubtool", grants=[drop("empty clean")])

        entry = self.compose(declare).lookup("stubtool")
        assert entry is not None
        self.assertFalse(entry.gated)
        assert entry.default is not None
        self.assertEqual(entry.default.rule.verdict, Verdict.ASK)

    def test_an_explicitly_closed_world_survives_its_last_grant(
        self,
    ) -> None:
        # And this is what makes derived and declared observably
        # different: a world someone closed on purpose is not re-opened
        # by a trim they made for another reason.
        self.write_collection("gated", GATED)

        def declare() -> None:
            use("gated")
            amend(
                "stubtool",
                grants=[drop("empty clean")],
                closed_world=True,
            )

        entry = self.compose(declare).lookup("stubtool")
        assert entry is not None
        self.assertTrue(entry.gated)

    def test_dropping_and_adding_the_same_name_is_refused(self) -> None:
        # §3.2 makes order within a source meaningless, so the pair has
        # no defined reading: is `-u` gone, or value-taking again? The
        # operator meant one of the two and should say which.
        def declare() -> None:
            amend("sudo", flags=[drop("-u"), takes_value("-u")])

        with self.assertRaises(ConfigurationError):
            self.compose(declare, with_defaults=True)

    def test_one_source_speaks_for_a_name_once(self) -> None:
        # Added during implementation, not at the gate: the two forms
        # in one source have no order-free reading, and the losing
        # order discards the amendment in silence. `tool()` replaces
        # what sits beneath, so the amendment survives below it and is
        # wiped above it — an order deciding a boundary, which §3.2
        # forbids and `registry.py`'s own invariant denies.
        def declare() -> None:
            amend("sudo", flags=[drop("-u")])
            tool("sudo", default=silent())

        with self.assertRaises(ConfigurationError):
            self.compose(declare, with_defaults=True)

    def test_a_fresh_declaration_takes_no_drops(self) -> None:
        # Removing something from a declaration that does not exist yet
        # is a type error first — `tool()` accepts no `Drop` — and a
        # refusal at load for a configuration that runs unchecked.
        def declare() -> None:
            tool("sudo", flags=[drop("-u")])  # type: ignore[list-item]

        with self.assertRaises(ConfigurationError):
            self.compose(declare, with_defaults=True)

    def test_amending_a_name_nothing_declared_is_refused(self) -> None:
        # An amendment that silently does nothing is a boundary the
        # operator believes they have.
        with self.assertRaises(ConfigurationError):
            self.compose(lambda: amend("gti", flags=[drop("-u")]))

    def test_a_wrapper_can_be_removed_by_replacing_it(self) -> None:
        # §3.4's "effectively removing an entry whose name collides
        # with a project binary": the name stays registered, but as
        # the project's own silent tool rather than as a runner.
        self.assertEqual(self.beneath("time").kind, Kind.WRAPPER)

        def declare() -> None:
            tool("time", default=silent())

        entry = self.compose(declare, with_defaults=True).lookup("time")
        assert entry is not None
        self.assertEqual(entry.kind, Kind.TOOL)


class BenignAssignmentTests(CollectionFixture):
    """The third default layer, shadowable like the others (§3.2)."""

    def benign(self, registry: Registry) -> dict[str, Assignment]:
        """The effective benign layer, by variable name."""
        return {
            str(assignment.name): assignment
            for assignment in registry.benign_assignments()
        }

    def test_a_project_can_add_to_it(self) -> None:
        def declare() -> None:
            benign_assignments(accounted("PROJECT_LOCALE"))

        names = self.benign(self.compose(declare, with_defaults=True))
        self.assertIn("PROJECT_LOCALE", names)
        self.assertIn("TZ", names)

    def test_a_project_can_narrow_one_it_did_not_declare(self) -> None:
        # The third thing shadowing has to do, beside adding and
        # removing: re-declaring a name replaces what was there, so a
        # variable the engine calls benign outright can be made benign
        # only for the values a project accepts.
        beneath = self.benign(self.compose(lambda: None, with_defaults=True))
        self.assertIsNone(beneath["TZ"].value)
        utc = one_of("UTC")

        def declare() -> None:
            benign_assignments(accounted("TZ", utc))

        after = self.benign(self.compose(declare, with_defaults=True))
        self.assertIs(after["TZ"].value, utc)

    def test_narrowing_leaves_one_entry_for_the_name(self) -> None:
        # Replacing, not appending: two declarations for one variable
        # would leave the engine to pick, and the looser one would
        # always win.
        def declare() -> None:
            benign_assignments(accounted("TZ", one_of("UTC")))

        registry = self.compose(declare, with_defaults=True)
        named = [
            assignment
            for assignment in registry.benign_assignments()
            if str(assignment.name) == "TZ"
        ]
        self.assertEqual(len(named), 1)

    def test_a_project_can_drop_from_it(self) -> None:
        # Shadowable means removable: a variable the engine considers
        # unable to direct execution may still matter here.
        def declare() -> None:
            benign_assignments(drop("TZ"))

        names = self.benign(self.compose(declare, with_defaults=True))
        self.assertNotIn("TZ", names)

    def test_dropping_what_is_not_there_is_refused(self) -> None:
        with self.assertRaises(ConfigurationError):
            self.compose(
                lambda: benign_assignments(drop("NOT_A_VARIABLE")),
                with_defaults=True,
            )


class CollectionOrderTests(CollectionFixture):
    """An explicit total order, and the operator last (§3.4).

    Each case asserts what the winning source *decided*, not only which
    source is named: an implementation that recorded the right layer
    while keeping the loser's rules would satisfy provenance and gate
    the wrong thing. The two fixtures differ where it shows —
    `starter` denies a forced push and asks on commit, `infra` asks on
    any push — so which one won is visible in the verdicts.
    """

    def verdicts_on(self, entry: Entry, subcommand: str) -> list[Verdict]:
        """The verdicts of every effective rule on one subcommand."""
        return [
            placed.rule.verdict
            for placed in entry.rules
            if tuple(placed.rule.subcommand) == tuple(subcommand.split())
        ]

    def test_a_collection_composes_over_the_engine_defaults(
        self,
    ) -> None:
        registry = self.compose(lambda: use("starter"), with_defaults=True)
        git = registry.lookup("git")
        sudo = registry.lookup("sudo")
        assert git is not None and sudo is not None
        self.assertEqual(git.source.layer, "collection:starter")
        self.assertEqual(self.verdicts_on(git, "push"), [Verdict.DENY])
        # And the engine's own layer is untouched beneath it.
        self.assertEqual(sudo.source.layer, ENGINE_LAYER)
        self.assertEqual(sudo.flags["-u"], Arity.VALUE)

    def test_later_collections_override_earlier_ones(self) -> None:
        def declare() -> None:
            use("starter")
            use("infra")

        entry = self.compose(declare).lookup("git")
        assert entry is not None
        self.assertEqual(entry.source.layer, "collection:infra")
        # infra's ask replaces starter's deny rather than joining it:
        # a surviving deny would outrank the ask and the later
        # collection would have decided nothing.
        self.assertEqual(self.verdicts_on(entry, "push"), [Verdict.ASK])
        self.assertNotIn(
            "forced push", [placed.label for placed in entry.rules]
        )

    def test_the_order_is_the_declared_one_not_the_reverse(self) -> None:
        def declare() -> None:
            use("infra")
            use("starter")

        entry = self.compose(declare).lookup("git")
        assert entry is not None
        self.assertEqual(entry.source.layer, "collection:starter")
        self.assertEqual(self.verdicts_on(entry, "push"), [Verdict.DENY])
        self.assertIn("forced push", [placed.label for placed in entry.rules])

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
        # `tool()` replaces, so the collection's rules are gone and the
        # project's default is what decides.
        self.assertEqual(entry.rules, ())
        assert entry.default is not None
        self.assertEqual(entry.default.rule.verdict, Verdict.DENY)

    def test_a_collection_shadows_an_engine_wrapper(self) -> None:
        # §3.4: replace and update apply to a collection's entries
        # "exactly as to the engine's wrapper defaults — wrapper
        # declarations included, since collections carry tools of every
        # kind". The three-layer stack is where composition would hide
        # a rule, and every other ordering case has the engine's
        # wrappers sitting untouched beneath tools.
        self.write_collection("runners", RUNNERS)

        def declare() -> None:
            use("runners")

        entry = self.compose(declare, with_defaults=True).lookup("sudo")
        assert entry is not None
        self.assertEqual(entry.source.layer, "collection:runners")
        self.assertEqual(entry.kind, Kind.WRAPPER)
        self.assertIsNotNone(entry.default)
        # The collection replaced the engine's declaration rather than
        # landing beside it: `--prompt-file` is the corpus's deliberate
        # omission, and here a collection has taken it on.
        self.assertEqual(entry.flags["--prompt-file"], Arity.VALUE)
        self.assertNotIn("-g", entry.flags)

    def test_the_project_amends_what_a_collection_shadowed(
        self,
    ) -> None:
        # And the project sits above both, amending the collection's
        # declaration rather than the engine's.
        self.write_collection("runners", RUNNERS)

        def declare() -> None:
            use("runners")
            amend("sudo", flags=[drop("--prompt-file")])

        entry = self.compose(declare, with_defaults=True).lookup("sudo")
        assert entry is not None
        self.assertNotIn("--prompt-file", entry.flags)
        self.assertEqual(entry.flags["-u"], Arity.VALUE)

    def test_the_same_collection_twice_is_refused(self) -> None:
        def declare() -> None:
            use("starter")
            use("starter")

        with self.assertRaises(ConfigurationError):
            self.compose(declare)

    def test_a_collection_that_is_not_there_is_refused(self) -> None:
        with self.assertRaises(ConfigurationError):
            self.compose(lambda: use("absent"))

    def test_a_relative_base_directory_is_refused(self) -> None:
        # Which file `use()` executes must not depend on where the
        # process was started: §9 requires the CLI and the hook to
        # resolve the same configuration, and §5.1 lets the engine
        # execute the project's own config and what sits beside it —
        # both of which a relative base makes a per-invocation
        # question.
        with (
            self.assertRaises(ConfigurationError),
            collecting(base_dir=Path("collections"), with_defaults=False),
        ):
            use("starter")

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
            redirections(
                ask(
                    target=path_under(".claude"),
                    reason="A write into the guard's own settings.",
                    label="settings write",
                )
            )

        self.text = self.compose(declare, with_defaults=True).describe()
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
        # Echoing the declaration that produced it, so the registry
        # speaks the configuration's language rather than a report's.
        self.assertIn("tool(git)", self.lines)
        self.assertIn("tool(adeploy)", self.lines)

    def test_entry_blocks_are_separated_by_blank_lines(self) -> None:
        # The blank line that ends *this* block: asserting one exists
        # somewhere below is true of any output with two entries.
        start = self.lines.index("tool(git)")
        block = self.block_for("tool(git)")
        self.assertEqual(self.lines[start + 1 + len(block)], "")

    def test_entries_are_ordered_by_name(self) -> None:
        # Two runs of one configuration must compare line by line.
        self.assertLess(
            self.lines.index("tool(adeploy)"),
            self.lines.index("tool(git)"),
        )

    def test_an_entry_uses_three_indents_and_no_others(self) -> None:
        # Two for the entry's own fields, four for a group's members,
        # six for their fields. A stray depth is what makes two runs of
        # one configuration stop comparing line by line.
        depths = {
            len(line) - len(line.lstrip(" "))
            for line in self.block_for("tool(git)")
        }
        self.assertLessEqual(depths, {2, 4, 6})

    def test_the_source_field_names_layer_file_and_line(self) -> None:
        self.assertRegex(
            self.text, r"\n  source: collection:starter starter\.py:\d+"
        )

    def test_rules_sit_in_a_group_of_their_own(self) -> None:
        # So a tool carrying twenty rules and two grants does not make
        # a reader infer where one list ends.
        self.assertIn("  rules:", self.lines)
        self.assertLess(
            self.lines.index("  rules:"),
            self.lines.index("    deny(push) - forced push"),
        )

    def test_a_rule_reads_verdict_subcommand_and_label(self) -> None:
        self.assertIn("    deny(push) - forced push", self.lines)

    def test_gated_says_why_rather_than_only_whether(self) -> None:
        # The one property an operator cannot infer by looking: a
        # closed world is derived from grants unless it was declared
        # outright (D-034).
        self.assertIn("  gated: no", self.block_for("tool(git)"))

    def test_a_rule_s_own_fields_are_indented_six_spaces(self) -> None:
        start = self.lines.index("    deny(push) - forced push")
        self.assertEqual(
            self.lines[start + 1],
            "      reason: A forced push rewrites remote history.",
        )
        self.assertRegex(
            self.lines[start + 2],
            r"^      source: collection:starter starter\.py:\d+$",
        )

    def test_rules_keep_their_declaration_order(self) -> None:
        # The ranking decides a verdict, not the order (§3.2) — but an
        # operator comparing this block against the file they wrote
        # needs the two to run in step.
        self.assertLess(
            self.lines.index("    deny(push) - forced push"),
            self.lines.index("    ask(commit) - git:ask:commit"),
        )

    def test_a_field_a_declaration_did_not_use_is_absent(self) -> None:
        # An empty `aliases:` line is noise in a registry an operator
        # scans, and noise is what makes a rule easy to miss.
        self.assertNotIn("  aliases:", self.block_for("tool(adeploy)"))

    def test_the_two_sections_follow_the_entries(self) -> None:
        self.assertIn("benign assignments", self.lines)
        self.assertIn("redirections", self.lines)
        self.assertLess(
            self.lines.index("tool(git)"),
            self.lines.index("benign assignments"),
        )

    def test_a_section_with_nothing_in_it_is_absent(self) -> None:
        # The same rule as fields and groups: absent, not empty. A
        # registry that ends with a bare `redirections` header every
        # time teaches the reader to skip the place where a rule about
        # `.claude` would appear.
        bare_registry = self.compose(lambda: None, with_defaults=False)
        self.assertNotIn("redirections", bare_registry.describe())
        self.assertNotIn("benign assignments", bare_registry.describe())

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
        self.assertTrue(line.startswith("      when: "))
        self.assertTrue(line.endswith(" [satisfied]"))

    def test_the_whole_output_is_ascii(self) -> None:
        self.assertTrue(self.text.isascii())


class RegistryCaseVisibilityTests(CollectionFixture):
    """Cases are out of the way until they are the question (§9)."""

    def registry(self) -> Registry:
        self.write_collection("proven", PROVEN)

        def declare() -> None:
            use("proven")
            cases(case("sudo git push --force", DENY))

        return self.compose(declare)

    def test_cases_are_absent_by_default(self) -> None:
        # They are the longest section on a mature tool and the least
        # useful thing to read when the question is "what gates git?".
        described = self.registry().describe()
        self.assertNotIn("cases:", described)
        self.assertNotIn("git push --force", described)

    def test_asking_for_them_puts_them_under_their_declaration(
        self,
    ) -> None:
        described = self.registry().describe(cases=Cases.SHOWN)
        lines = described.splitlines()
        self.assertIn("  cases:", lines)
        self.assertIn("    git push --force -> deny", lines)
        # And the declarations they belong to are still there.
        self.assertIn("tool(git)", lines)

    def test_a_case_belonging_to_no_tool_gets_its_own_section(
        self,
    ) -> None:
        lines = self.registry().describe(cases=Cases.SHOWN).splitlines()
        self.assertIn("cases", lines)
        self.assertIn("  sudo git push --force -> deny", lines)

    def test_cases_only_prints_the_composed_list_alone(self) -> None:
        # Every layer's together — a collection ships the cases for its
        # own rules (§8.2) — and no declarations around them.
        lines = self.registry().describe(cases=Cases.ONLY).splitlines()
        self.assertNotIn("tool(git)", lines)
        self.assertIn("git push --force -> deny", lines)
        self.assertIn("sudo git push --force -> deny", lines)


class RegistryWrappingTests(CollectionFixture):
    """Wrapped for a reader, unwrapped for a parser (§9)."""

    LONG = (
        "A forced push rewrites remote history, and the work it "
        "overwrites may exist in no other clone, which is why this "
        "one is a deny rather than an ask."
    )

    def registry(self) -> Registry:
        long_reason = self.LONG

        def declare() -> None:
            tool(
                "git",
                rules=[deny("push", reason=long_reason, label="forced push")],
            )

        return self.compose(declare)

    def test_a_long_reason_wraps_under_its_key(self) -> None:
        lines = self.registry().describe().splitlines()
        opening = next(
            index
            for index, line in enumerate(lines)
            if line.startswith("      reason: ")
        )
        self.assertTrue(lines[opening + 1].startswith("        "))
        self.assertNotIn(self.LONG, lines[opening])

    def test_no_wrap_keeps_one_record_on_one_line(self) -> None:
        # A tool reading this output wants one record per line, and a
        # continuation is a record with no key on it.
        lines = self.registry().describe(wrap=False).splitlines()
        self.assertIn(f"      reason: {self.LONG}", lines)


class CaseCollectionTests(CollectionFixture):
    """Cases travel with the rules they prove (§8.2)."""

    def test_an_adopted_collection_brings_its_cases(self) -> None:
        # §8.2 lets coverage be supplied "by the source that
        # contributed the rule", so a collection ships the cases for
        # its own rules. Without that, adopting one would mint rules
        # nothing covers and turn a live import into a coverage deny.
        self.write_collection("proven", PROVEN)

        def declare() -> None:
            use("proven")

        registry = self.compose(declare)
        self.assertEqual(
            [each.command for each in registry.cases()],
            ["git push --force"],
        )

    def test_the_project_s_own_cases_join_the_collection_s(
        self,
    ) -> None:
        self.write_collection("proven", PROVEN)

        def declare() -> None:
            use("proven")
            cases(case("git status", SILENT))

        registry = self.compose(declare)
        self.assertEqual(
            sorted(each.command for each in registry.cases()),
            ["git push --force", "git status"],
        )


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
        self.lines = self.text.splitlines()

    def test_it_names_every_effective_entry(self) -> None:
        # As whole lines, not as substrings: "git" appears in a path,
        # in a reason and in a label, and an assertion satisfied by any
        # of those proves nothing about the entry.
        for header in (
            "tool(git)",
            "wrapper(sudo)",
            "wrapper(myrunner)",
        ):
            with self.subTest(header=header):
                self.assertIn(header, self.lines)

    def test_it_says_which_layer_each_came_from(self) -> None:
        self.assertRegex(
            self.text, r"\n  source: collection:starter starter\.py:\d+"
        )
        # Bare filenames for every layer, not an absolute path for
        # the engine's and a relative one for the config's: one column
        # that reads two ways is a column nobody can scan.
        self.assertRegex(
            self.text, rf"\n  source: {ENGINE_LAYER} [^/\s]+\.py:\d+"
        )
        self.assertRegex(
            self.text, rf"\n      source: {PROJECT_LAYER} \S+:\d+"
        )

    def test_it_prints_a_label_an_amendment_added(self) -> None:
        # The layout class pins the collection's label; this one pins
        # that a rule arriving by amendment is printed the same way,
        # which is the composition claim rather than the layout one.
        self.assertIn("    ask(push) - any push", self.lines)

    def test_a_value_annotates_every_matcher_with_its_outcome(
        self,
    ) -> None:
        # Every one, and each with its own answer: a tool carries
        # several matchers, and an implementation that annotated the
        # first — or annotated them all alike — would still print a
        # plausible registry.
        def declare() -> None:
            tool(
                "stubtool",
                rules=[
                    ask(
                        "apply",
                        when=flag("--mode", one_of("destroy")),
                        reason="A destroying mode.",
                    ),
                    ask(
                        "target",
                        when=flag("--to", one_of("prod")),
                        reason="Reaching production.",
                    ),
                ],
            )

        described = self.compose(declare).describe(value="destroy")
        annotations = [
            line.rsplit(" ", 1)[-1]
            for line in described.splitlines()
            if line.strip().startswith("when:")
        ]
        self.assertEqual(annotations, ["[satisfied]", "[unsatisfied]"])

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
