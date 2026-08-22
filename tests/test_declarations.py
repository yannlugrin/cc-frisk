"""What a configuration can say, and what it is refused for saying.

The subject is the config-facing API of §5.2 and §5.3: the declarations
an operator writes, the errors a malformed one produces, and the shape
they compose into. Verdicts are not the subject — there is no engine to
produce one — so what is asserted here is *expressibility* and
*refusal*, which is what §5.2's "the API is designed against the whole
of it" can be held to before behaviour exists.

Everything here is **structural**: what composes, what is refused, and
what the composed entry holds. Nothing here asks what an answer *is* —
`evaluate` and `Outcome` belong to the value layer and to
`test_matchers.py`, operand quantifiers included, and a case that
reaches for them here is testing a matcher through a declaration.

Cases come from the specification and from
`.claude/refs/behavior-corpus.md`'s policy contexts, and each declares
what it needs inline — a claim about one alias is witnessed by a tool
with one alias, not by a fixture carrying five grants and four rules
that the reader has to open in another file and then discount. The
corpus's context B is used only where the fixture *is* the subject:
`ContextBExpressibilityTests`, which asks whether that policy can be
stated in full, because a policy that cannot be stated is a behaviour
that can never be reached.
"""

from __future__ import annotations

import unittest
from typing import Callable

from corpus import context_b

from frisk.declare import (
    Arity,
    Inside,
    Source,
    accounted,
    allow,
    any_flag,
    anywhere,
    ask,
    at_least_one_operand,
    bare,
    case,
    cases,
    deny,
    env,
    every_operand,
    flag,
    grant,
    handoff,
    host_only,
    inside,
    interpreter,
    matching,
    may_take_value,
    no_operands,
    one_of,
    option,
    option_handoff,
    path_under,
    redirections,
    shell,
    silent,
    takes_value,
    tool,
    wrapper,
)
from frisk.errors import ConfigurationError
from frisk.registry import PROJECT_LAYER, Kind, Registry, collecting
from frisk.verdicts import Verdict


def compose(declare: Callable[[], None]) -> Registry:
    """Run a declaration callable and return what it composed.

    `with_defaults` is off here: these cases are about one declaration
    at a time, and the engine's wrapper layer would put a dozen entries
    beside it in every assertion about the registry's contents.
    """
    with collecting(with_defaults=False) as declared:
        declare()
    return declared.registry()


class ReasonTests(unittest.TestCase):
    """A refusal that says nothing is worse than none (§5.3, §8.2)."""

    def test_a_rule_without_a_reason_is_refused(self) -> None:
        for constructor in (deny, ask, allow):
            with self.subTest(verdict=constructor.__name__):
                self.assertRaises(ConfigurationError, constructor, "push")

    def test_an_empty_reason_is_refused_like_a_missing_one(self) -> None:
        with self.assertRaises(ConfigurationError):
            deny("push", reason="   ")

    def test_a_grant_without_a_reason_is_refused(self) -> None:
        with self.assertRaises(ConfigurationError):
            grant("clean", when=no_operands())

    def test_a_default_verdict_needs_a_reason_too(self) -> None:
        with self.assertRaises(ConfigurationError):
            ask()

    def test_silence_needs_none(self) -> None:
        # Nothing is being refused, so there is nothing to explain —
        # and a declared silence is worth stating because it survives
        # secure mode where an implicit one does not (§3.2).
        self.assertEqual(silent("status").verdict, Verdict.SILENT)

    def test_the_refusal_names_what_it_refused(self) -> None:
        with self.assertRaises(ConfigurationError) as raised:
            deny("stash drop")
        self.assertIn("stash drop", str(raised.exception))


class FlagArityTests(unittest.TestCase):
    """Three arities, declared and kept apart (§4.2)."""

    def test_each_bucket_carries_its_arity(self) -> None:
        def declare() -> None:
            tool(
                "stubtool",
                flags=[
                    bare("--syntax-check"),
                    takes_value("-i", "--inventory"),
                    may_take_value("--argument"),
                ],
            )

        entry = compose(declare).lookup("stubtool")
        assert entry is not None
        self.assertEqual(entry.flags["--syntax-check"], Arity.BARE)
        self.assertEqual(entry.flags["-i"], Arity.VALUE)
        self.assertEqual(entry.flags["--inventory"], Arity.VALUE)
        self.assertEqual(entry.flags["--argument"], Arity.OPTIONAL_VALUE)

    def test_pre_subcommand_options_are_a_separate_set(self) -> None:
        # `git -C dir push` needs -C stripped so the subcommand lands
        # where rules expect it; a flag declaration would not do that.
        def declare() -> None:
            tool(
                "git",
                options=[takes_value("-C", "--git-dir")],
                flags=[takes_value("-m")],
            )

        entry = compose(declare).lookup("git")
        assert entry is not None
        self.assertNotIn("-C", entry.flags)
        self.assertNotIn("--git-dir", entry.flags)
        self.assertNotIn("-m", entry.options)

    def test_a_flag_declared_twice_with_two_arities_is_refused(
        self,
    ) -> None:
        def declare() -> None:
            tool(
                "stubtool",
                flags=[bare("--mode"), takes_value("--mode")],
            )

        with self.assertRaises(ConfigurationError):
            compose(declare)


class RecognitionTests(unittest.TestCase):
    """A tool is recognized by whole name, or by path (§4.2)."""

    def test_aliases_are_the_same_declaration(self) -> None:
        # Corpus: `stub2 wipe` → deny, exactly as `stubtool wipe` does.
        # The claim is one declaration, not one object: an entry equal
        # in everything but its name would satisfy the corpus and fail
        # an identity assertion.

        def declare() -> None:
            tool("stubtool", aliases=["stub2"])

        registry = compose(declare)
        entry = registry.lookup("stubtool")
        under_alias = registry.lookup("stub2")
        assert entry is not None and under_alias is not None
        self.assertEqual(entry, under_alias)
        self.assertEqual(entry.name, "stubtool")
        self.assertEqual(under_alias.name, "stubtool")
        self.assertIn("stub2", entry.aliases)
        self.assertIn("stub2", under_alias.aliases)

    def test_a_longer_name_is_a_different_tool(self) -> None:
        # Corpus: `stub2x wipe`, `stubtool-extra deploy.yml` and
        # `mystubtool deploy.yml` are all silent.
        def declare() -> None:
            tool("stubtool", aliases=["stub2"])

        registry = compose(declare)
        for name in ("stub2x", "stubtool-extra", "mystubtool"):
            with self.subTest(name=name):
                self.assertIsNone(registry.lookup(name))

    def test_a_tool_declared_by_path_is_found_by_its_spellings(
        self,
    ) -> None:
        def declare() -> None:
            tool(
                "tools/deploy.py",
                default=ask(reason="Deploys reach production."),
            )

        registry = compose(declare)
        for spelling in (
            "tools/deploy.py",
            "./tools/deploy.py",
            "tools/../tools/deploy.py",
        ):
            with self.subTest(spelling=spelling):
                self.assertIsNotNone(registry.lookup_path(spelling))

    def test_a_path_declaration_is_not_a_basename_declaration(
        self,
    ) -> None:
        # The point of the form: a grant written for the operator's
        # script must not release a same-named file anywhere (§4.2).
        def declare() -> None:
            tool(
                "tools/deploy.py",
                default=ask(reason="Deploys reach production."),
            )

        registry = compose(declare)
        self.assertIsNone(registry.lookup("deploy.py"))

    def test_a_basename_and_a_path_declaration_do_not_collide(
        self,
    ) -> None:
        # Declaring both must not read as one name declared twice, or a
        # project could never attach policy to a script whose basename
        # it also knows. Which of the two *wins* is §4.2's
        # most-specific-wins rule, and it is unobservable here —
        # `lookup` and `lookup_path` are separate doors — so it belongs
        # to `008`, with a command word to resolve.
        def declare() -> None:
            tool("deploy.py")
            tool(
                "tools/deploy.py",
                default=ask(reason="This deploy reaches production."),
            )

        registry = compose(declare)
        by_name = registry.lookup("deploy.py")
        by_path = registry.lookup_path("tools/deploy.py")
        assert by_name is not None and by_path is not None
        self.assertNotEqual(by_name, by_path)

    def test_the_separator_is_what_says_which_form_it_is(self) -> None:
        # The shell's own distinction: `deploy.py` is a name to look
        # up, `./deploy.py` is the file here. A script at the project
        # root needs the `./` for the same reason it needs it to run.
        def declare() -> None:
            tool("deploy.py")
            tool("./deploy.py", default=ask(reason="The root script."))

        registry = compose(declare)
        by_name = registry.lookup("deploy.py")
        by_path = registry.lookup_path("deploy.py")
        assert by_name is not None and by_path is not None
        self.assertFalse(by_name.path_declared)
        self.assertTrue(by_path.path_declared)

    def test_a_tool_needs_a_name(self) -> None:
        with self.assertRaises(ConfigurationError):
            compose(lambda: tool())

    def test_an_absolute_path_is_refused(self) -> None:
        # The configuration is committed and travels with the project:
        # `/usr/bin/git` on one machine is `/opt/homebrew/bin/git` on
        # the next, and project-relative is what survives a clone.
        # Accepting it would also gate almost nothing while reading
        # like it gates git, since a bare `git push` would not match.
        with self.assertRaises(ConfigurationError) as raised:
            compose(lambda: tool("/usr/bin/git"))
        self.assertIn("git", str(raised.exception))

    def test_a_name_declared_twice_in_one_source_is_refused(self) -> None:
        # Within a source there is no order (§3.2), so a second
        # declaration is a mistake rather than a shadow. Shadowing is
        # what layers are for.
        def declare() -> None:
            tool("git", default=silent())
            tool("git", default=ask(reason="Everything git does."))

        with self.assertRaises(ConfigurationError):
            compose(declare)

    def test_an_alias_colliding_in_one_source_is_refused(self) -> None:
        def declare() -> None:
            tool("podman", default=silent())
            tool("docker", aliases=["podman"], default=silent())

        with self.assertRaises(ConfigurationError):
            compose(declare)


class ToolKindTests(unittest.TestCase):
    """Registered, gated, rule-bearing — three words, three meanings."""

    def test_a_rules_only_tool_is_not_gated(self) -> None:
        def declare() -> None:
            tool(
                "git",
                rules=[ask("push", reason="A push publishes work.")],
            )

        entry = compose(declare).lookup("git")
        assert entry is not None
        self.assertTrue(entry.rule_bearing)
        self.assertFalse(entry.gated)

    def test_declaring_a_grant_closes_the_world(self) -> None:
        # Grants are checked universally and closed-world (§3.2), so a
        # tool that declares one is gated by that alone.
        def declare() -> None:
            tool(
                "stubtool",
                default=ask(reason="stubtool changes infrastructure."),
                grants=[
                    grant(
                        when=no_operands(),
                        reason="A run with nothing to act on.",
                    )
                ],
            )

        entry = compose(declare).lookup("stubtool")
        assert entry is not None
        self.assertTrue(entry.gated)

    def test_a_closed_world_can_be_declared_without_a_grant(self) -> None:
        # §3.2 makes gated mean "grants and/or closed worlds", so the
        # second half must be sayable on its own.
        def declare() -> None:
            tool(
                "stubcli",
                closed_world=True,
                flags=[bare("--help")],
                default=deny(reason="Every use is the operator's."),
            )

        entry = compose(declare).lookup("stubcli")
        assert entry is not None
        self.assertTrue(entry.gated)
        self.assertFalse(entry.rule_bearing)

    def test_a_granted_world_cannot_be_declared_open(self) -> None:
        # `closed_world` is three-valued so that unset means "closed
        # exactly when grants are declared". An explicit False beside a
        # grant is the one combination that says nothing coherent: a
        # grant an undeclared flag could escape is not a proof of a
        # safe shape (§3.2).
        def declare() -> None:
            tool(
                "stubtool",
                default=ask(reason="stubtool changes infrastructure."),
                grants=[
                    grant(when=no_operands(), reason="Nothing to act on.")
                ],
                closed_world=False,
            )

        with self.assertRaises(ConfigurationError):
            compose(declare)

    def test_a_default_only_tool_is_registered_and_nothing_else(
        self,
    ) -> None:
        # Corpus: stubalways — no rules, no grants, default deny.
        def declare() -> None:
            tool(
                "stubalways",
                default=deny(reason="Every use is the operator's."),
            )

        entry = compose(declare).lookup("stubalways")
        assert entry is not None
        self.assertIsNotNone(entry.default)
        self.assertFalse(entry.gated)
        self.assertFalse(entry.rule_bearing)


class ConditionTests(unittest.TestCase):
    """Every condition of §5.2 is sayable, and names itself."""

    def test_a_description_names_what_it_constrains(self) -> None:
        # The floor below says a description exists; this says it is
        # the operator's own declaration read back. `describe()`
        # returning "x" satisfies the first and no citation at all.
        self.assertIn("--force", flag("--force").describe())
        self.assertIn("STUB_DANGER", env("STUB_DANGER").describe())
        self.assertIn("-C", option("-C").describe())

    def test_the_whole_vocabulary_describes_itself(self) -> None:
        for condition in (
            flag("--force"),
            flag("--mode", one_of("dry-run")),
            any_flag("-f", "--force"),
            env("STUB_DANGER"),
            env("GIT_PAGER", one_of("cat")),
            option("-C", path_under("/srv")),
            every_operand(matching(r"^a$")),
            at_least_one_operand(matching(r"^a$")),
            no_operands(),
        ):
            with self.subTest(condition=type(condition).__name__):
                self.assertTrue(condition.describe().strip())

    def test_the_end_of_options_marker_is_matchable(self) -> None:
        # §4.2 makes `--` matchable, and context A needs it: `checkout`
        # with a pathspec asks where plain checkout does not. All this
        # layer can show is that the constructor takes it like any
        # other flag name; recognizing it on a line is `008`'s.
        marker = flag("--")
        self.assertTrue(marker.describe().strip())

    def test_a_condition_exposes_the_matchers_inside_it(self) -> None:
        # `frisk registry --value` walks these (§3.4's inspection).
        self.assertEqual(len(flag("--mode", one_of("a")).matchers()), 1)
        self.assertEqual(len(flag("--force").matchers()), 0)

    def test_several_conditions_on_one_rule_all_hold(self) -> None:
        rule = deny(
            "push",
            when=[flag("--force"), option("-C", path_under("/srv"))],
            reason="A forced push into the deployment tree.",
        )
        self.assertEqual(len(rule.conditions), 2)

    def test_a_value_condition_is_available_to_deny_and_ask(self) -> None:
        # Closing the prototype's asymmetry: it could deny on a flag's
        # presence but not on its value (§3.2). What the matcher then
        # answers belongs to the matchers' own suite; what belongs here
        # is that a value-carrying condition reaches both constructors
        # and arrives intact, rather than being dropped on the floor —
        # which is the asymmetry being closed.
        for constructor in (deny, ask):
            with self.subTest(verdict=constructor.__name__):
                condition = flag("--mode", one_of("destroy"))
                rule = constructor(
                    "apply",
                    when=condition,
                    reason="A destroying mode.",
                )
                self.assertEqual(list(rule.conditions), [condition])


class OperandQuantifierTests(unittest.TestCase):
    """The three operand constraints of §5.2, as declarations.

    What each one *answers* for a list of operands is a verdict on a
    command line, and it is proven where conditions meet invocations —
    as the corpus states it, `stubtool clean` with no operands asks.
    Here they are declarations like any other condition: they carry the
    matcher they were given, they name themselves, and the empty case
    has its own spelling rather than falling out of a quantifier.
    """

    def test_a_quantifier_carries_the_matcher_it_was_given(self) -> None:
        scratch = path_under("/tmp", ".scratch")
        for condition in (
            every_operand(scratch),
            at_least_one_operand(scratch),
        ):
            with self.subTest(condition=condition.describe()):
                self.assertEqual(list(condition.matchers()), [scratch])

    def test_the_two_quantifiers_are_different_conditions(self) -> None:
        # Both constrain the operands with one matcher, and §5.2 asks
        # for both spellings because they mean opposite things: a grant
        # over every operand and a deny over any one of them.
        scratch = path_under("/tmp")
        self.assertNotEqual(
            every_operand(scratch), at_least_one_operand(scratch)
        )

    def test_each_quantifier_says_which_one_it_is(self) -> None:
        scratch = path_under("/tmp")
        self.assertIn("every", every_operand(scratch).describe())
        self.assertIn("at least one", at_least_one_operand(scratch).describe())

    def test_no_operands_constrains_the_count_not_a_value(self) -> None:
        # §5.2 names it separately so that granting the empty case is a
        # decision rather than a side effect of a quantifier — and it
        # has no matcher at all, so nothing probes it for a value.
        empty = no_operands()
        self.assertEqual(list(empty.matchers()), [])
        self.assertTrue(empty.describe().strip())


class AssignmentTests(unittest.TestCase):
    """Accounted assignments, with and without a value (§3.2)."""

    def test_a_tool_declares_what_it_expects(self) -> None:
        # Corpus: STUB_QUIET and STUB_TARGET are accounted, so
        # `STUB_QUIET=1 stubtool --syntax-check site.yml` is silent
        # while `STUB_UNKNOWN=1 …` asks.
        def declare() -> None:
            tool(
                "stubtool",
                assignments=[
                    accounted("STUB_QUIET"),
                    accounted("STUB_TARGET"),
                ],
            )

        entry = compose(declare).lookup("stubtool")
        assert entry is not None
        names = [assignment.name for assignment in entry.assignments]
        self.assertEqual(sorted(names), ["STUB_QUIET", "STUB_TARGET"])

    def test_an_assignment_may_be_accounted_only_for_a_value(
        self,
    ) -> None:
        # §3.2's own example: GIT_PAGER acceptable as `cat`, asking
        # otherwise.
        pager = one_of("cat")

        def declare() -> None:
            tool("git", assignments=[accounted("GIT_PAGER", pager)])

        entry = compose(declare).lookup("git")
        assert entry is not None
        self.assertEqual(entry.assignments[0].name, "GIT_PAGER")
        self.assertIs(entry.assignments[0].value, pager)


class HandoffTests(unittest.TestCase):
    """Both shapes of §4.3's inner commands are declarable."""

    def test_a_subcommand_handoff_keeps_its_own_operand(self) -> None:
        # The kept operand is the image, service or container name, and
        # locating it depends on the handoff's own value-taking
        # options: `-u root` must be stepped over, not counted.
        def declare() -> None:
            tool(
                "stubtool",
                handoffs=[
                    handoff(
                        "exec", keeps_operands=1, flags=[takes_value("-u")]
                    ),
                    handoff("run", keeps_operands=1),
                ],
            )

        entry = compose(declare).lookup("stubtool")
        assert entry is not None
        by_subcommand = {
            tuple(each.subcommand): each for each in entry.handoffs
        }
        self.assertEqual(by_subcommand[("run",)].keeps_operands, 1)
        self.assertEqual(by_subcommand[("exec",)].keeps_operands, 1)
        self.assertEqual(len(by_subcommand[("exec",)].flags), 1)
        exec_flags = by_subcommand[("exec",)].flags[0]
        self.assertEqual(tuple(exec_flags.names), ("-u",))
        self.assertEqual(exec_flags.arity, Arity.VALUE)

    def test_a_multi_word_handoff_position(self) -> None:
        # docker's compose forms: `compose run SERVICE cmd`.
        declared = handoff("compose run", keeps_operands=1)
        self.assertEqual(tuple(declared.subcommand), ("compose", "run"))

    def test_an_option_introduced_handoff_names_its_terminators(
        self,
    ) -> None:
        # `find . -name '*.log' -exec rm -rf {} +` — the command sits
        # mid-line, opened by an option and closed by a terminator. Its
        # own constructor, because it shares no argument with the
        # subcommand form: no operand is kept and no option of its own
        # is declared, the inner command beginning immediately.
        declared = option_handoff("-exec", terminated_by=[";", "+"])
        self.assertEqual(declared.option, "-exec")
        self.assertEqual(tuple(declared.terminated_by), (";", "+"))

    def test_the_two_shapes_land_in_separate_lists(self) -> None:
        # One `handoffs=` to write, two collections to read: the engine
        # reaches a subcommand handoff by the subcommand path and an
        # option-introduced one by an option token anywhere on the
        # line, so they are never searched together.
        def declare() -> None:
            tool(
                "stubtool",
                handoffs=[
                    handoff("run", keeps_operands=1),
                    option_handoff("-exec", terminated_by=[";", "+"]),
                ],
            )

        entry = compose(declare).lookup("stubtool")
        assert entry is not None
        self.assertEqual(len(entry.handoffs), 1)
        self.assertEqual(len(entry.option_handoffs), 1)
        self.assertEqual(entry.option_handoffs[0].option, "-exec")


class SourceTests(unittest.TestCase):
    """Where a declaration was written (§3.4)."""

    def test_a_source_file_must_be_an_absolute_path(self) -> None:
        # The field is a `str` whose name promises a path, so the
        # promise is kept where the value is produced rather than by
        # the type. Absolute is the half that is checkable without
        # touching the filesystem — §4.5 forbids that — and it is what
        # makes rendering the path relative to the configuration's
        # directory well defined.
        with self.assertRaises(ValueError):
            Source(layer=PROJECT_LAYER, file="starter.py", line=12)


class ScopeTests(unittest.TestCase):
    """The three scope values themselves (§4.3, §5.2).

    Three states and no fourth: anywhere, the host, or one named
    handoff. "Inside and on the host" is not a state the API can
    express, because a handed-off command is by definition not on the
    host. Whether a *rule* or a *grant* carries one is the two classes
    below; what a scope is, and how it names itself, is here.
    """

    def test_every_scope_names_itself(self) -> None:
        # Scopes reach the operator through `frisk registry` and
        # through a citation, like everything else declared.
        for scope in (anywhere, host_only, inside("docker run")):
            with self.subTest(scope=type(scope).__name__):
                self.assertTrue(scope.describe().strip())


class RuleScopeTests(unittest.TestCase):
    """A rule carries the scope it was declared with (§4.3, §5.2)."""

    def test_a_rule_defaults_to_applying_anywhere(self) -> None:
        rule = ask("push", reason="A push publishes work.")
        self.assertEqual(rule.scope, anywhere)

    def test_a_rule_can_be_confined_to_the_host(self) -> None:
        rule = ask("wipe", reason="Wiping the host.", scope=host_only)
        self.assertEqual(rule.scope, host_only)

    def test_a_rule_can_be_confined_to_one_handoff(self) -> None:
        # `docker run image cmd --dangerous` and a bare
        # `cmd --dangerous` need not share a verdict.
        rule = ask(
            "wipe",
            reason="Wiping inside the container.",
            scope=inside("docker run"),
        )
        self.assertEqual(rule.scope, Inside("docker run"))


class GrantScopeTests(unittest.TestCase):
    """A grant is scopable by execution context too (§5.2).

    §5.2 asks for *judgment* scopable by execution context, not for
    rules scopable by it: a shape that is safe inside a container need
    not be safe on the host, and the release has to be sayable in the
    narrower place.
    """

    def test_a_grant_defaults_to_applying_anywhere(self) -> None:
        released = grant(
            "clean", when=no_operands(), reason="Cleaning nothing."
        )
        self.assertEqual(released.scope, anywhere)

    def test_a_grant_can_be_confined_to_the_host(self) -> None:
        released = grant(
            "clean",
            when=no_operands(),
            reason="Cleaning the host's own scratch space.",
            scope=host_only,
        )
        self.assertEqual(released.scope, host_only)

    def test_a_grant_can_be_confined_to_a_handoff(self) -> None:
        released = grant(
            "clean",
            when=no_operands(),
            reason="Cleaning inside the container.",
            scope=inside("docker run"),
        )
        self.assertEqual(released.scope, Inside("docker run"))


class RedirectionTests(unittest.TestCase):
    """A redirection target is matchable (§4.3, §5.2)."""

    def test_a_target_rule_composes(self) -> None:
        target = path_under(".claude")

        def declare() -> None:
            redirections(
                ask(
                    target=target,
                    reason="A write into the guard's own settings.",
                )
            )

        placed = compose(declare).redirections()
        self.assertEqual(len(placed), 1)
        self.assertIs(placed[0].rule.target, target)

    def test_a_target_rule_needs_a_target(self) -> None:
        with self.assertRaises(ConfigurationError):
            compose(lambda: redirections(ask(reason="Anything.")))

    def test_a_target_belongs_only_to_a_redirection_rule(self) -> None:
        def declare() -> None:
            tool(
                "git",
                rules=[
                    ask(
                        "push",
                        target=path_under(".claude"),
                        reason="Not a redirection rule.",
                    )
                ],
            )

        with self.assertRaises(ConfigurationError):
            compose(declare)


class CaseTests(unittest.TestCase):
    """Cases sit beside the rules they prove (§5.2, §8.2)."""

    def test_a_tool_carries_its_own_cases(self) -> None:
        def declare() -> None:
            tool(
                "git",
                rules=[
                    deny(
                        "push",
                        when=any_flag("-f", "--force"),
                        reason="A forced push rewrites remote history.",
                    )
                ],
                cases=[
                    case("git push --force", Verdict.DENY),
                    case("git status", Verdict.SILENT),
                ],
            )

        registry = compose(declare)
        entry = registry.lookup("git")
        assert entry is not None
        self.assertEqual(len(entry.cases), 2)
        self.assertEqual(len(registry.cases()), 2)

    def test_a_case_about_no_single_tool_stands_alone(self) -> None:
        def declare() -> None:
            cases(case("sudo git push --force", Verdict.DENY))

        self.assertEqual(len(compose(declare).cases()), 1)

    def test_a_case_expects_a_verdict_not_a_rule(self) -> None:
        with self.assertRaises(ConfigurationError):
            case("git push", deny("push", reason="A push."))  # type: ignore[arg-type]


class EntityKindTests(unittest.TestCase):
    """Wrappers, shells and interpreters are declarations too (§3.4)."""

    def test_a_wrapper_declares_its_values_and_its_operands(self) -> None:
        def declare() -> None:
            wrapper(
                "timeout",
                flags=[takes_value("-s", "--signal", "-k")],
                keeps_operands=1,
            )

        entry = compose(declare).lookup("timeout")
        assert entry is not None
        self.assertEqual(entry.kind, Kind.WRAPPER)
        self.assertEqual(entry.keeps_operands, 1)
        self.assertEqual(entry.flags["-k"], Arity.VALUE)

    def test_a_wrapper_may_carry_rules_of_its_own(self) -> None:
        # `sudo git push --force` is a sudo *and* a denied push.
        def declare() -> None:
            wrapper(
                "sudo",
                flags=[takes_value("-u", "--user")],
                rules=[ask(reason="Running as another user.")],
            )

        entry = compose(declare).lookup("sudo")
        assert entry is not None
        self.assertTrue(entry.rule_bearing)

    def test_a_stdin_fed_runner_says_so(self) -> None:
        # `… | xargs -0 rm`: the command word is visible, its operands
        # are not, so operand conditions on it are unprovable (§4.3).
        def declare() -> None:
            wrapper(
                "xargs",
                flags=[takes_value("-n", "-P", "-I")],
                operands_from_stdin=True,
            )

        entry = compose(declare).lookup("xargs")
        assert entry is not None
        self.assertTrue(entry.operands_from_stdin)

    def test_a_shell_and_an_interpreter_are_different_kinds(self) -> None:
        def declare() -> None:
            shell("bash")
            interpreter("python3", flags=[takes_value("-c", "-m")])

        registry = compose(declare)
        bash = registry.lookup("bash")
        python = registry.lookup("python3")
        assert bash is not None and python is not None
        self.assertEqual(bash.kind, Kind.SHELL)
        self.assertEqual(python.kind, Kind.INTERPRETER)


class ContextBExpressibilityTests(unittest.TestCase):
    """The corpus's engine-behavior policy is sayable in full (§5.2)."""

    def setUp(self) -> None:
        self.registry = compose(context_b.declare)

    def test_the_closed_world_is_exactly_what_the_corpus_declares(
        self,
    ) -> None:
        entry = self.registry.lookup("stubtool")
        assert entry is not None
        self.assertEqual(
            sorted(entry.flags),
            [
                "--inventory",
                "--limit",
                "--list-tasks",
                "--mode",
                "--syntax-check",
                "--tags",
                "-i",
            ],
        )

    def test_the_value_taking_flags_are_exactly_those(self) -> None:
        # Several rulings turn on -i taking a value: it is what makes
        # `deploy.yml -i --syntax-check` a real deploy rather than a
        # parse-only run (§4.2).
        entry = self.registry.lookup("stubtool")
        assert entry is not None
        self.assertEqual(
            sorted(
                name
                for name, arity in entry.flags.items()
                if arity is Arity.VALUE
            ),
            ["--inventory", "--limit", "--mode", "--tags", "-i"],
        )

    def test_the_exec_handoff_takes_a_value_for_its_option(
        self,
    ) -> None:
        # The corpus writes exec's option as "value-opt `-u`", which
        # could be read as value-taking or value-optional; context A's
        # analogous docker `exec` list puts `-u --user` under
        # value-taking and the fixture reads it that way. Asserted here
        # so the reading is recorded against the transcription rather
        # than left in the fixture's prose alone.
        entry = self.registry.lookup("stubtool")
        assert entry is not None
        by_subcommand = {
            tuple(each.subcommand): each for each in entry.handoffs
        }
        self.assertEqual(len(by_subcommand[("exec",)].flags), 1)
        exec_flags = by_subcommand[("exec",)].flags[0]
        self.assertEqual(tuple(exec_flags.names), ("-u",))
        self.assertEqual(exec_flags.arity, Arity.VALUE)

    def test_all_five_grants_survive_composition(self) -> None:
        entry = self.registry.lookup("stubtool")
        assert entry is not None
        self.assertEqual(len(entry.grants), 5)

    def test_a_subcommand_carries_two_rules_of_different_strength(
        self,
    ) -> None:
        # `wipe` carries both an ask and a deny, and §3.2 requires the
        # ranking to decide rather than the order.
        entry = self.registry.lookup("stubtool")
        assert entry is not None
        verdicts = {
            placed.rule.verdict
            for placed in entry.rules
            if tuple(placed.rule.subcommand) == ("wipe",)
        }
        self.assertEqual(verdicts, {Verdict.ASK, Verdict.DENY})

    def test_the_three_default_verdicts_differ(self) -> None:
        defaults = {}
        for name in ("stubtool", "stubcli", "stubalways"):
            entry = self.registry.lookup(name)
            assert entry is not None and entry.default is not None
            defaults[name] = entry.default.rule.verdict
        self.assertEqual(
            defaults,
            {
                "stubtool": Verdict.ASK,
                "stubcli": Verdict.DENY,
                "stubalways": Verdict.DENY,
            },
        )
