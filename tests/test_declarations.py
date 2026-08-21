"""What a configuration can say, and what it is refused for saying.

The subject is the config-facing API of §5.2 and §5.3: the declarations
an operator writes, the errors a malformed one produces, and the shape
they compose into. Verdicts are not the subject — there is no engine to
produce one — so what is asserted here is *expressibility* and
*refusal*, which is what §5.2's "the API is designed against the whole
of it" can be held to before behaviour exists.

Cases come from the specification and from
`.claude/refs/behavior-corpus.md`'s policy contexts. The corpus's
context B is reproduced as a fixture (`tests/corpus/context_b.py`) and
checked here for shape, because a policy that cannot be *stated* is a
behaviour that can never be reached.
"""

from __future__ import annotations

import unittest
from typing import Callable

from corpus import context_b

from frisk.declare import (
    Arity,
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
    path_under,
    redirections,
    shell,
    silent,
    takes_value,
    tool,
    wrapper,
)
from frisk.errors import ConfigurationError
from frisk.matchers import NO_CONTEXT, MatchContext, Outcome, Value
from frisk.registry import Registry, collecting
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
        self.assertEqual(entry.options["-C"], Arity.VALUE)
        self.assertNotIn("-C", entry.flags)
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
        registry = compose(context_b.declare)
        self.assertIs(registry.lookup("stub2"), registry.lookup("stubtool"))

    def test_a_longer_name_is_a_different_tool(self) -> None:
        # Corpus: `stub2x wipe`, `stubtool-extra deploy.yml` and
        # `mystubtool deploy.yml` are all silent.
        registry = compose(context_b.declare)
        for name in ("stub2x", "stubtool-extra", "mystubtool"):
            with self.subTest(name=name):
                self.assertIsNone(registry.lookup(name))

    def test_a_tool_declared_by_path_is_found_by_its_spellings(
        self,
    ) -> None:
        def declare() -> None:
            tool(
                path="tools/deploy.py",
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
                path="tools/deploy.py",
                default=ask(reason="Deploys reach production."),
            )

        registry = compose(declare)
        self.assertIsNone(registry.lookup("deploy.py"))

    def test_a_tool_needs_a_name_or_a_path(self) -> None:
        with self.assertRaises(ConfigurationError):
            compose(lambda: tool())

    def test_a_tool_may_not_have_both(self) -> None:
        with self.assertRaises(ConfigurationError):
            compose(lambda: tool("deploy.py", path="tools/deploy.py"))

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
        entry = compose(context_b.declare).lookup("stubtool")
        assert entry is not None
        self.assertTrue(entry.gated)
        self.assertTrue(entry.closed_world)

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

    def test_a_default_only_tool_is_registered_and_nothing_else(
        self,
    ) -> None:
        # Corpus: stubalways — no rules, no grants, default deny.
        entry = compose(context_b.declare).lookup("stubalways")
        assert entry is not None
        self.assertFalse(entry.gated)
        self.assertFalse(entry.rule_bearing)
        assert entry.default is not None
        self.assertEqual(entry.default.rule.verdict, Verdict.DENY)


class ConditionTests(unittest.TestCase):
    """Every condition of §5.2 is sayable, and names itself."""

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
        # presence but not on its value (§3.2).
        rule = deny(
            "apply",
            when=flag("--mode", one_of("destroy")),
            reason="A destroying mode.",
        )
        self.assertEqual(rule.verdict, Verdict.DENY)


class OperandQuantifierTests(unittest.TestCase):
    """Quantifiers over the operand list, three-valued (§3.2)."""

    def setUp(self) -> None:
        self.every = every_operand(path_under("/tmp", ".scratch"))
        self.at_least_one = at_least_one_operand(matching(r"^(list|show)$"))

    def test_every_operand_needs_all_of_them(self) -> None:
        # Corpus: `stubtool clean /tmp/x /tmp/y` → silent.
        self.assertEqual(
            self.every.evaluate(["/tmp/x", "/tmp/y"]), Outcome.SATISFIED
        )

    def test_one_failing_operand_fails_the_quantifier(self) -> None:
        # Corpus: `stubtool clean /tmp/x /etc/passwd` → ask.
        self.assertNotEqual(
            self.every.evaluate(["/tmp/x", "/etc/passwd"]),
            Outcome.SATISFIED,
        )

    def test_every_operand_requires_at_least_one(self) -> None:
        # Corpus, stated as a fact across all three contexts: `stubtool
        # clean` with no operands is *not* vacuously granted — a
        # command acting on nothing has not proven what it acts on.
        self.assertEqual(self.every.evaluate([]), Outcome.UNSATISFIED)

    def test_at_least_one_operand_needs_one(self) -> None:
        # Corpus: `stubcli server list` → silent, `stubcli` → deny.
        self.assertEqual(
            self.at_least_one.evaluate(["server", "list"]),
            Outcome.SATISFIED,
        )
        self.assertEqual(self.at_least_one.evaluate([]), Outcome.UNSATISFIED)

    def test_no_operands_is_its_own_grant_form(self) -> None:
        # §5.2 names it separately so that granting the empty case is a
        # decision rather than a side effect of a quantifier.
        empty = no_operands()
        self.assertEqual(empty.evaluate([]), Outcome.SATISFIED)
        self.assertEqual(empty.evaluate(["x"]), Outcome.UNSATISFIED)

    def test_an_unprovable_operand_leaves_the_quantifier_unproven(
        self,
    ) -> None:
        self.assertEqual(
            self.every.evaluate([Value("$FOO", dynamic=True)]),
            Outcome.UNPROVEN,
        )

    def test_a_clean_miss_outranks_an_unknown(self) -> None:
        self.assertEqual(
            self.every.evaluate(["/etc/passwd", Value("$FOO", dynamic=True)]),
            Outcome.UNPROVEN,
        )
        self.assertEqual(
            self.every.evaluate(["/tmp/../etc", Value("$FOO", dynamic=True)]),
            Outcome.UNSATISFIED,
        )

    def test_the_line_s_context_reaches_the_operands(self) -> None:
        poisoned = MatchContext(relative_paths_unproven=True)
        self.assertEqual(
            self.every.evaluate([".scratch/x"], NO_CONTEXT),
            Outcome.SATISFIED,
        )
        self.assertEqual(
            self.every.evaluate([".scratch/x"], poisoned),
            Outcome.UNPROVEN,
        )


class AssignmentTests(unittest.TestCase):
    """Accounted assignments, with and without a value (§3.2)."""

    def test_a_tool_declares_what_it_expects(self) -> None:
        # Corpus: STUB_QUIET and STUB_TARGET are accounted, so
        # `STUB_QUIET=1 stubtool --syntax-check site.yml` is silent
        # while `STUB_UNKNOWN=1 …` asks.
        entry = compose(context_b.declare).lookup("stubtool")
        assert entry is not None
        names = [assignment.name for assignment in entry.assignments]
        self.assertEqual(sorted(names), ["STUB_QUIET", "STUB_TARGET"])

    def test_an_assignment_may_be_accounted_only_for_a_value(
        self,
    ) -> None:
        # §3.2's own example: GIT_PAGER acceptable as `cat`, asking
        # otherwise.
        def declare() -> None:
            tool(
                "git",
                assignments=[accounted("GIT_PAGER", one_of("cat"))],
            )

        entry = compose(declare).lookup("git")
        assert entry is not None
        matcher = entry.assignments[0].value
        assert matcher is not None
        self.assertEqual(matcher.evaluate("cat"), Outcome.SATISFIED)
        self.assertEqual(matcher.evaluate("less"), Outcome.UNSATISFIED)


class HandoffTests(unittest.TestCase):
    """Both shapes of §4.3's inner commands are declarable."""

    def test_a_subcommand_handoff_keeps_its_own_operand(self) -> None:
        entry = compose(context_b.declare).lookup("stubtool")
        assert entry is not None
        by_subcommand = {
            tuple(each.subcommand): each for each in entry.handoffs
        }
        self.assertEqual(by_subcommand[("run",)].keeps_operands, 1)
        self.assertEqual(by_subcommand[("exec",)].keeps_operands, 1)
        self.assertEqual(
            tuple(by_subcommand[("exec",)].flags[0].names), ("-u",)
        )

    def test_a_multi_word_handoff_position(self) -> None:
        # docker's compose forms: `compose run SERVICE cmd`.
        declared = handoff("compose run", keeps_operands=1)
        self.assertEqual(tuple(declared.subcommand), ("compose", "run"))

    def test_a_flag_introduced_handoff_with_a_terminator(self) -> None:
        # `find . -name '*.log' -exec rm -rf {} +` — the command sits
        # mid-line, opened by an option and closed by a terminator.
        declared = handoff(option="-exec", terminated_by=[";", "+"])
        self.assertEqual(declared.option, "-exec")
        self.assertEqual(tuple(declared.terminated_by), (";", "+"))

    def test_a_handoff_is_a_subcommand_or_an_option_not_both(
        self,
    ) -> None:
        with self.assertRaises(ConfigurationError):
            handoff("run", option="-exec")


class ScopeTests(unittest.TestCase):
    """Judgment is scopable by execution context (§4.3, §5.2)."""

    def test_a_rule_defaults_to_applying_anywhere(self) -> None:
        rule = ask("push", reason="A push publishes work.")
        self.assertIs(rule.scope, anywhere)

    def test_a_rule_can_be_confined_to_the_host(self) -> None:
        rule = ask("wipe", reason="Wiping the host.", scope=host_only)
        self.assertTrue(rule.scope.host)

    def test_a_rule_can_be_confined_to_one_handoff(self) -> None:
        # `docker run image cmd --dangerous` and a bare
        # `cmd --dangerous` need not share a verdict.
        rule = ask(
            "wipe",
            reason="Wiping inside the container.",
            scope=inside("docker run"),
        )
        self.assertEqual(rule.scope.handoff, "docker run")


class RedirectionTests(unittest.TestCase):
    """A redirection target is matchable (§4.3, §5.2)."""

    def test_a_target_rule_composes(self) -> None:
        def declare() -> None:
            redirections(
                ask(
                    target=path_under(".claude"),
                    reason="A write into the guard's own settings.",
                )
            )

        placed = compose(declare).redirections()
        self.assertEqual(len(placed), 1)
        self.assertEqual(placed[0].rule.verdict, Verdict.ASK)

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
        self.assertEqual(entry.kind, "wrapper")
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
        self.assertEqual(bash.kind, "shell")
        self.assertEqual(python.kind, "interpreter")


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
