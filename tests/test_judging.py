"""§3.2, §3.3, §6.1 and §6.2: what frisk answers, and why.

Every case here is transcribed from `SPECIFICATIONS.md` §3.2, §3.3,
§4.1, §6.1 and §6.2, or from a ruling in
`.claude/refs/behavior-corpus.md` — never from the engine, which does
not judge anything yet. Where a corpus ruling is the provenance, the
ruling is quoted beside the case.

**Two kinds of test live here, and they carry their policy
differently.** The unit half examines one clause of the decision model,
and each class declares the tools it needs in its own `setUpClass`, so
the declaration under test sits a few lines above the assertion and
cannot drift from it. The conformance half runs against
`tests/corpus/context_b.py` — a transcription of the adjudicated corpus,
which must stay unmodified to be worth anything — so those cases cite
the ruling and quote the deciding declaration in a comment instead.
A case is told apart at a glance by which registry it judges against.

Four boundaries are deliberate, and a case asserting the interim
behaviour on the far side of one would be a case a later step has to
undo. What lives behind another program — a wrapper's command, a
shell's `-c` payload, an interpreter's file operand — is `010`.
Substitutions, subshells and heredocs are `011`; handoffs and
redirection targets are `012`. And the **allow rows of §6.1's table**
are `017`, behind open fact (c) at `015`: a rule may declare `allow`
today, but no line answers one, so the cases here pin the withholding
rather than a release (`D-051`).

A fifth is narrower and named for the same reason: how secure mode
meets the **engine's default layers** — every wrapper, shell and
interpreter, all registered with no declared default — is deferred to
`010`, where a wrapper's own contribution to a line is designed
(`D-057`). Nothing here asserts it either way.

The corpus is therefore reproduced in part: the context B rulings this
step can reach, and no more. `014` is where all three contexts are
reproduced end to end; what stands here is the subset that judging
alone decides, so a regression in it is caught at the step that
introduced it rather than five steps later.
"""

from __future__ import annotations

import unittest
from collections.abc import Callable

from frisk.declare import (
    accounted,
    allow,
    any_flag,
    ask,
    bare,
    deny,
    every_operand,
    flag,
    grant,
    handoff,
    inside,
    no_operands,
    one_of,
    option,
    path_under,
    silent,
    takes_value,
    tool,
)
from frisk.judging import Judgment, combined, judge
from frisk.reading import read
from frisk.registry import Registry, collecting
from frisk.verdicts import Verdict
from tests.corpus import context_b


def corpus_policy() -> Registry:
    """Context B exactly, with the engine's default layers on.

    Nothing is added: the rulings below are adjudicated against this
    policy and no other, so a tool invented for a unit case would make
    every corpus verdict answer a different question.
    """
    with collecting() as declared:
        context_b.declare()
    return declared.registry()


def composed(declare: Callable[[], None]) -> Registry:
    """The registry one class's own declarations compose.

    The engine's default layers are on, as they are for the corpus, so
    the two registries differ only in the project policy above them.
    """
    with collecting() as declared:
        declare()
    return declared.registry()


#: Composed once: composition is `007`'s subject, not this file's.
CORPUS = corpus_policy()

#: Secure mode's two global default verdicts (§3.2: "a configurable
#: global default verdict (ask or deny)"). Both *are* secure mode; they
#: differ only in what replaces an implicit silence. The switch that
#: turns the mode on is `033`'s, so the cases reach the capability the
#: only way anything can today — as an argument.
SECURE_DENY = deny(
    reason=(
        "This project runs in secure mode: nothing frisk has not been "
        "taught is allowed to run unremarked."
    )
)
SECURE_ASK = ask(reason="Secure mode: say what this command is.")


class Judges(unittest.TestCase):
    """What every case below needs to reach a verdict.

    `registry` is the class's own policy, and defaults to the corpus so
    that a conformance class needs no `setUpClass` at all. A case that
    reaches for the *other* registry passes it explicitly, which keeps
    a class's own declarations the thing a reader assumes.
    """

    registry: Registry = CORPUS

    def judgment(
        self,
        command_line: str,
        secure: object = None,
        registry: Registry | None = None,
    ) -> Judgment:
        against = self.registry if registry is None else registry
        return judge(
            read(command_line, against),
            against,
            secure,  # type: ignore[arg-type]
        )

    def verdict(
        self,
        command_line: str,
        secure: object = None,
        registry: Registry | None = None,
    ) -> Verdict:
        return self.judgment(command_line, secure, registry).verdict

    def assertVerdict(  # noqa: N802 — unittest's own casing
        self,
        command_line: str,
        expected: Verdict,
        secure: object = None,
        registry: Registry | None = None,
    ) -> None:
        reached = self.judgment(command_line, secure, registry)
        self.assertEqual(
            reached.verdict,
            expected,
            f"{command_line!r} answered {reached.verdict.value}: {reached}",
        )

    def labels(self, judgment: Judgment) -> list[str | None]:
        return [citation.label for citation in judgment.citations]

    def phrases(self, judgment: Judgment) -> list[str]:
        return [
            phrase
            for citation in judgment.citations
            for phrase in citation.read
        ]


class CombinationTests(unittest.TestCase):
    """§6.1's table, dangerous branches first.

    No policy: `combined` takes the per-invocation verdicts a line
    produced and answers for the line, so there is no declaration to
    show.
    """

    def test_any_deny_anywhere_denies(self) -> None:
        # "any deny, anywhere (embedded commands included) → deny".
        self.assertIs(
            combined([Verdict.SILENT, Verdict.DENY, Verdict.ASK]),
            Verdict.DENY,
        )

    def test_no_deny_and_any_ask_asks(self) -> None:
        # "no deny, any ask → ask".
        self.assertIs(
            combined([Verdict.SILENT, Verdict.ASK, Verdict.SILENT]),
            Verdict.ASK,
        )

    def test_silence_only_is_silence(self) -> None:
        self.assertIs(
            combined([Verdict.SILENT, Verdict.SILENT]), Verdict.SILENT
        )

    def test_a_line_with_no_invocations_is_silence(self) -> None:
        self.assertIs(combined([]), Verdict.SILENT)

    def test_an_allow_is_withheld_until_the_allow_rows_ship(self) -> None:
        # §6.1's allow rows wait on open fact (c) at `015` and ship at
        # `017`. Until then every one of them answers its stricter
        # sibling — "the line falls back to genuine silence" (`D-051`).
        self.assertIs(combined([Verdict.ALLOW]), Verdict.SILENT)
        self.assertIs(
            combined([Verdict.ALLOW, Verdict.SILENT]), Verdict.SILENT
        )

    def test_an_ask_anywhere_withholds_an_allow_earned_elsewhere(
        self,
    ) -> None:
        # §3.2: "An `ask` or `deny` anywhere in a line must also
        # withhold any `allow` earned elsewhere in it: a grant speaks
        # for one invocation, never for the line."
        self.assertIs(combined([Verdict.ALLOW, Verdict.ASK]), Verdict.ASK)
        self.assertIs(combined([Verdict.ALLOW, Verdict.DENY]), Verdict.DENY)


class IndependenceTests(Judges):
    """§3.2: each invocation is judged alone. Against the corpus."""

    def test_a_safe_command_never_vouches_for_its_neighbour(self) -> None:
        # Corpus: `stubtool --syntax-check a.yml && stubtool deploy.yml`
        # → **ask**.
        #   grant(when=any_flag("--syntax-check", "--list-tasks"))
        #   default=ask(...)
        judgment = self.judgment(
            "stubtool --syntax-check a.yml && stubtool deploy.yml"
        )
        self.assertEqual(
            [judged.verdict for judged in judgment.judged],
            [Verdict.SILENT, Verdict.ASK],
        )
        self.assertIs(judgment.verdict, Verdict.ASK)

    def test_the_dangerous_half_decides_whichever_side_it_sits_on(
        self,
    ) -> None:
        # Corpus, both orders: the line answers the same either way.
        #   deny("wipe", ...) — label "wipe denies"
        self.assertVerdict(
            "stubtool --syntax-check a.yml && stubtool wipe", Verdict.DENY
        )
        self.assertVerdict(
            "stubtool wipe && stubtool --syntax-check a.yml", Verdict.DENY
        )


class OrderFreedomTests(unittest.TestCase):
    """§3.2: the ranking is order-free within one declaration source."""

    def registry_with(self, first: str) -> Registry:
        """The same two rules on one tool, in the order named."""
        asking = ask(
            "wipe",
            reason="Wiping destroys state that may not be rebuilt.",
            label="ask rule",
        )
        denying = deny(
            "wipe",
            reason="Wiping has no authorized use here.",
            label="deny rule",
        )
        ordered = [asking, denying] if first == "ask" else [denying, asking]

        def declare() -> None:
            tool("stubtool", rules=ordered)

        return composed(declare)

    def test_reordering_rules_inside_a_source_changes_nothing(self) -> None:
        # "reordering the rules inside a source never changes a
        # verdict" — the ranking decides, not the order found in.
        #
        # Narrower than it sounds: order-freedom holds *within one
        # source*. Across sources §3.4's declared precedence decides,
        # and there order is exactly what matters; that is
        # `tests/test_composition.py`'s subject.
        for first in ("ask", "deny"):
            with self.subTest(first=first):
                registry = self.registry_with(first)
                judgment = judge(read("stubtool wipe", registry), registry)
                self.assertIs(judgment.verdict, Verdict.DENY)
                # And the citation names only the deciding rank.
                self.assertEqual(
                    [citation.label for citation in judgment.citations],
                    ["deny rule"],
                )


class RuleTests(Judges):
    """§3.2's rules, checked existentially."""

    @classmethod
    def setUpClass(cls) -> None:
        def declare() -> None:
            # §3.2's rules-only tool, in the shape the section names:
            # "A tool that is safe by default with a listable set of
            # dangerous acts (git, docker) declares **rules**."
            tool(
                "git",
                options=[takes_value("-C")],
                rules=[
                    deny(
                        "push",
                        when=any_flag("-f", "--force"),
                        reason="A forced push rewrites remote history.",
                        label="forced push",
                    ),
                    ask(
                        "push",
                        reason=(
                            "A push reaches a remote. Push a branch instead."
                        ),
                        label="any push",
                    ),
                    ask(
                        "checkout",
                        when=option("-C", path_under("/srv")),
                        reason=("A checkout under /srv discards work there."),
                        label="checkout under /srv",
                    ),
                ],
            )
            # §3.2: "Value conditions must be available to deny and ask
            # rules, not only to grants" — prototyping could deny on a
            # flag's presence but not on its value.
            tool(
                "kubectl",
                flags=[takes_value("--context")],
                rules=[
                    deny(
                        "delete",
                        when=flag("--context", one_of("production")),
                        reason=(
                            "Deleting against the production cluster has "
                            "no authorized use. Switch context first."
                        ),
                        label="production context",
                    ),
                ],
            )

        cls.registry = composed(declare)

    def test_naming_an_act_gates_it(self) -> None:
        #   deny("push", when=any_flag("-f", "--force"))
        #   ask("push")
        self.assertVerdict("git push -f", Verdict.DENY)
        self.assertVerdict("git push", Verdict.ASK)

    def test_every_act_unnamed_falls_through_silently(self) -> None:
        # "every *subcommand and flag* unnamed falls through silently".
        # Nothing on this git names `status`, and the tool is not
        # gated, so an undeclared flag costs nothing either.
        self.assertVerdict("git status", Verdict.SILENT)
        self.assertVerdict("git status --unheard-of", Verdict.SILENT)

    def test_a_rule_may_condition_on_a_flag_value(self) -> None:
        #   deny("delete", when=flag("--context", one_of("production")))
        self.assertVerdict(
            "kubectl delete pod api --context production", Verdict.DENY
        )
        self.assertVerdict(
            "kubectl delete pod api --context staging", Verdict.SILENT
        )

    def test_a_rule_may_condition_on_a_pre_subcommand_option_value(
        self,
    ) -> None:
        # §4.2: "'pushing is fine only for repositories under this
        # directory' is a rule on `-C`'s value."
        #   ask("checkout", when=option("-C", path_under("/srv")))
        self.assertVerdict("git -C /srv/repo checkout main", Verdict.ASK)
        self.assertVerdict(
            "git -C /home/dev/repo checkout main", Verdict.SILENT
        )
        self.assertVerdict("git checkout main", Verdict.SILENT)


class GrantTests(Judges):
    """§3.2's grants, checked universally and closed-world."""

    @classmethod
    def setUpClass(cls) -> None:
        def declare() -> None:
            # §3.2's granted tool: "dangerous by default with a small
            # provable safe set". No `default=`, so §3.2's implicit
            # "ask for a granted tool" applies.
            tool(
                "helm",
                flags=[bare("--dry-run")],
                grants=[
                    grant(
                        when=any_flag("--dry-run"),
                        reason="A dry run renders the chart and applies it "
                        "to nothing.",
                    ),
                ],
            )
            # A closed world declared outright, with no grant behind it
            # (`D-056`): the flag list is an opt-in list the operator
            # steers by editing, and a flag outside it asks.
            tool(
                "aws",
                flags=[bare("--no-paginate"), takes_value("--profile")],
                closed_world=True,
                rules=[
                    deny(
                        "s3 rb",
                        reason="Removing a bucket destroys what it held.",
                        label="bucket removal",
                    ),
                ],
            )
            # §5.2's "no operands allowed" grant form, and an explicit
            # default to fall back to.
            tool(
                "terraform",
                default=ask(
                    reason="terraform reaches real infrastructure. "
                    "Rehearse with a targetless plan."
                ),
                grants=[
                    grant(
                        "plan",
                        when=no_operands(),
                        reason="A plan with no target reads the whole "
                        "state and changes nothing.",
                    ),
                ],
            )
            # §5.2's scopes, in the shape §4.3 gives them: the runner
            # declares where an inner command begins, and the tool that
            # *travels between the two worlds* carries one verdict per
            # world. The real pair:
            #
            #   playbook playbooks/nodes.yml
            #       -> deny; it reaches the real machines
            #   runner run --rm ansible-test playbook playbooks/nodes.yml
            #       -> silent; the container is deleted a second later
            #
            # `009` walks into no handoff — that is `012` — so only the
            # host line is reachable here, and it is the one that
            # matters: an engine ignoring `scope=` would let the grant
            # release a playbook hitting production.
            tool("runner", handoffs=[handoff("run", keeps_operands=1)])
            tool(
                "playbook",
                default=deny(
                    reason="A playbook reaches real machines. Rehearse "
                    "with --check."
                ),
                grants=[
                    grant(
                        scope=inside("runner run"),
                        reason="Inside a throwaway container the playbook "
                        "reaches nothing that outlives it.",
                    ),
                ],
            )

        cls.registry = composed(declare)

    def test_a_grant_that_holds_is_silence(self) -> None:
        #   grant(when=any_flag("--dry-run"))
        self.assertVerdict(
            "helm upgrade api ./chart --dry-run", Verdict.SILENT
        )

    def test_an_invocation_matching_no_grant_gets_the_default(self) -> None:
        # §3.2: "anything else gets the tool's default verdict."
        #   tool("terraform", default=ask(...))
        self.assertVerdict("terraform apply", Verdict.ASK)

    def test_a_flag_outside_the_closed_world_defeats_every_grant(
        self,
    ) -> None:
        # §3.3: "an unknown flag on a gated tool: stricter, never
        # quieter". The grant would hold on `--dry-run` alone.
        self.assertVerdict(
            "helm upgrade api ./chart --dry-run --unknown", Verdict.ASK
        )

    def test_a_flag_outside_the_closed_world_asks_in_its_own_right(
        self,
    ) -> None:
        # `D-056`(b). `aws` declares a closed world and no grant, so
        # nothing could ever release it: without a contribution of its
        # own the declared flag list would change no verdict at all and
        # `closed_world=True` would be a keyword that does nothing.
        # Taking a flag out of that list is how an operator makes it
        # ask, and that only works if the breach is a contribution.
        #   tool("aws", flags=[...], closed_world=True)
        self.assertVerdict("aws --profile dev s3 ls", Verdict.SILENT)
        self.assertVerdict("aws --region eu-west-1 s3 ls", Verdict.ASK)
        # And it is stricter, never stronger than what a rule decided.
        self.assertVerdict(
            "aws --region eu-west-1 s3 rb s3://logs", Verdict.DENY
        )

    def test_the_breach_names_the_flag_that_caused_it(self) -> None:
        # §6.2: no declaration reached this verdict, so the citation
        # has to name the token and carry the engine's own reason.
        judgment = self.judgment("aws --region eu-west-1 s3 ls")
        self.assertIs(judgment.verdict, Verdict.ASK)
        self.assertEqual(self.phrases(judgment), ["flag --region"])
        self.assertIsNone(judgment.citations[0].label)
        self.assertTrue(judgment.citations[0].reason.strip())

    def test_no_operands_is_the_empty_case_spelled_deliberately(
        self,
    ) -> None:
        #   grant("plan", when=no_operands())
        self.assertVerdict("terraform plan", Verdict.SILENT)
        self.assertVerdict("terraform plan modules/db", Verdict.ASK)

    def test_a_grant_confined_to_a_handoff_does_not_release_on_the_host(
        self,
    ) -> None:
        # §5.2: "the same tool may carry different rules on the host
        # and inside a named handoff". `host_only` and `inside(...)`
        # divide the *handoff* axis and nothing else — a wrapper such
        # as `sudo` is still the host — so this line is outside every
        # handoff and the grant must not release it.
        #   default=deny(...)
        #   grant(scope=inside("runner run"))
        judgment = self.judgment("playbook playbooks/nodes.yml")
        self.assertIs(judgment.verdict, Verdict.DENY)
        # The default denied it; the grant did not release and is not
        # what the operator should be sent to read.
        self.assertEqual(len(judgment.citations), 1)
        self.assertIn("reaches real machines", judgment.citations[0].reason)

    def test_rules_hold_even_where_a_grant_would_release(self) -> None:
        # Corpus: `stubtool touch --syntax-check` → **ask**, though
        # grant (1) holds on `--syntax-check`.
        #   grant(when=any_flag("--syntax-check", "--list-tasks"))
        #   ask("touch", ...) — label "touch asks"
        self.assertVerdict(
            "stubtool touch --syntax-check", Verdict.ASK, registry=CORPUS
        )

    def test_a_quantified_operand_matcher_needs_at_least_one_operand(
        self,
    ) -> None:
        # §3.2: "empty operands are never vacuously granted (a command
        # acting on nothing has not proven what it acts on)".
        # Corpus: `stubtool clean` → **ask**.
        #   grant("clean", when=every_operand(path_under("/tmp", ".scratch")))
        self.assertVerdict("stubtool clean", Verdict.ASK, registry=CORPUS)
        self.assertVerdict(
            "stubtool clean /tmp/x", Verdict.SILENT, registry=CORPUS
        )


class AssignmentWorldTests(Judges):
    """§3.2: assignments are closed-world for every registered tool."""

    @classmethod
    def setUpClass(cls) -> None:
        def declare() -> None:
            # Rules-only, not gated, and it still owes the accounting:
            # "**Environment assignments are closed-world for every
            # registered tool**, not only gated ones."
            tool(
                "psql",
                assignments=[accounted("PAGER", one_of("cat"))],
            )

        cls.registry = composed(declare)

    def test_an_unaccounted_assignment_asks_on_a_rules_only_tool(
        self,
    ) -> None:
        #   tool("psql", assignments=[accounted("PAGER", one_of("cat"))])
        self.assertVerdict("psql -l", Verdict.SILENT)
        self.assertVerdict("PSQL_HISTORY=/tmp/h psql -l", Verdict.ASK)

    def test_the_universal_benign_list_accounts_for_the_locale_class(
        self,
    ) -> None:
        # "the display/locale class — `LC_*`, `LANG`, `TZ`, `NO_COLOR`
        # and kin, variables that cannot direct execution" — an engine
        # default layer, so no project has to declare it.
        self.assertVerdict("LC_ALL=C psql -l", Verdict.SILENT)
        self.assertVerdict("LANG=C psql -l", Verdict.SILENT)

    def test_an_accounted_assignment_may_be_value_conditioned(self) -> None:
        # "(by name, optionally value-conditioned — `GIT_PAGER`
        # acceptable as `cat`, asking otherwise)".
        #   accounted("PAGER", one_of("cat"))
        self.assertVerdict("PAGER=cat psql -l", Verdict.SILENT)
        self.assertVerdict("PAGER=less psql -l", Verdict.ASK)

    def test_assignments_ahead_of_an_unregistered_tool_keep_its_posture(
        self,
    ) -> None:
        # "because an opinion the guard does not have about `make`
        # should not appear because of a harmless `DEBUG=1`."
        self.assertVerdict("DEBUG=1 make check", Verdict.SILENT)

    def test_the_unregistered_posture_is_the_global_default_in_secure_mode(
        self,
    ) -> None:
        # The other half of the same sentence: "silence in the default
        # posture, the global default in secure mode". The answer must
        # be the global default, not the assignment's own ask — the
        # wrong reason would carry the wrong citation.
        judgment = self.judgment("DEBUG=1 make check", SECURE_DENY)
        self.assertIs(judgment.verdict, Verdict.DENY)
        self.assertEqual(len(judgment.citations), 1)
        self.assertIn("secure mode", judgment.citations[0].reason)

    def test_an_assignment_shaped_token_after_the_command_is_an_operand(
        self,
    ) -> None:
        # §4.2: "An assignment-shaped token *after* the command name is
        # an operand, not environment." The pair is the whole lesson —
        # the same text is a deny in front of the command and an inert
        # argument behind it. An engine pattern-matching `NAME=value`
        # anywhere on the line would produce a wrong deny on the second.
        #   deny(when=env("STUB_DANGER")) — label "danger assignment"
        #
        # Corpus: `STUB_DANGER=1 stubtool --syntax-check site.yml` → deny
        #         `stubtool --syntax-check STUB_DANGER=1`          → silent
        #
        # The two rulings are not one line with the token moved — the
        # first carries an operand the second does not — but both are
        # adjudicated as written, and inventing a third line to make
        # the pair symmetric would assert something nobody ruled on.
        self.assertVerdict(
            "STUB_DANGER=1 stubtool --syntax-check site.yml",
            Verdict.DENY,
            registry=CORPUS,
        )
        self.assertVerdict(
            "stubtool --syntax-check STUB_DANGER=1",
            Verdict.SILENT,
            registry=CORPUS,
        )


class DefaultVerdictTests(Judges):
    """§3.2's per-tool default verdicts."""

    @classmethod
    def setUpClass(cls) -> None:
        def declare() -> None:
            # No `default=`, carrying rules: §3.2's "silent for a
            # rules-only tool".
            tool(
                "npm",
                rules=[
                    ask(
                        "publish",
                        reason="Publishing puts a package on a public "
                        "registry, and a version cannot be unpublished.",
                        label="publish",
                    ),
                ],
            )
            # No `default=`, carrying a grant: §3.2's "ask for a
            # granted tool".
            tool(
                "helm",
                flags=[bare("--dry-run")],
                grants=[
                    grant(
                        when=any_flag("--dry-run"),
                        reason="A dry run renders the chart and applies it "
                        "to nothing.",
                    ),
                ],
            )
            # No `default=`, carrying a closed world and no grant:
            # `D-056`(a) reads §3.2's enumeration verbatim — ask where
            # the tool declares *grants*, silent otherwise.
            tool(
                "aws",
                flags=[bare("--no-paginate"), takes_value("--profile")],
                closed_world=True,
            )
            # §3.2's "an explicit verdict": every use of this one is
            # the operator's — and a weaker rule on it, which is the
            # shape that separates a default read as a fallback from
            # one read as a floor (`D-059`).
            tool(
                "kubectl",
                default=deny(
                    reason="Every command against this cluster is the "
                    "operator's to approve."
                ),
                rules=[
                    ask(
                        "get",
                        reason="Reading the cluster is cheap, but it is "
                        "still the cluster.",
                        label="read",
                    ),
                ],
            )
            # A declared silence: §5.3's "a declared silence refuses
            # nothing and so has nothing to explain".
            tool(
                "pytest",
                default=silent(reason="Running the suite is the job."),
            )

        cls.registry = composed(declare)

    def test_a_rules_only_tool_with_no_declared_default_is_silent(
        self,
    ) -> None:
        #   tool("npm", rules=[ask("publish", ...)])  — no default=
        self.assertVerdict("npm install", Verdict.SILENT)
        self.assertVerdict("npm publish", Verdict.ASK)

    def test_a_granted_tool_with_no_declared_default_asks(self) -> None:
        # "ask for a granted tool".
        #   tool("helm", grants=[grant(...)])  — no default=
        self.assertVerdict("helm upgrade api ./chart", Verdict.ASK)

    def test_a_closed_world_without_grants_is_silent_by_default(
        self,
    ) -> None:
        # `D-056`(a): §3.2's enumeration verbatim — ask where the tool
        # declares *grants*, silent otherwise. `aws` declares a closed
        # world and no grant, so an accounted invocation is the
        # rules-only silence, not an ask.
        #   tool("aws", flags=[...], closed_world=True)  — no default=
        self.assertVerdict("aws --no-paginate s3 ls", Verdict.SILENT)
        self.assertVerdict("aws --profile dev s3 ls", Verdict.SILENT)

    def test_an_explicit_verdict_stands_on_its_own(self) -> None:
        # "'every use of this one is the operator's' is a tool with a
        # deny default and nothing else." Corpus: `stubalways anything
        # at all` → **deny**.
        #   tool("kubectl", default=deny(...))
        self.assertVerdict("kubectl", Verdict.DENY)
        self.assertVerdict("kubectl version --client", Verdict.DENY)

    def test_a_weaker_rule_carves_out_of_a_stronger_default(self) -> None:
        # §3.2: the default is the outcome for "no rule matched, no
        # grant held" — a **fallback**, not a floor (`D-059`,
        # reversing `D-052`). An operator writing `ask("get")` on a
        # deny-default tool has written a carve-out, and reading the
        # default as a floor would make that declaration do nothing at
        # all. The floor is a construct the model already has and
        # keeps separate: an unconditional `deny()` rule, which fires
        # on every invocation.
        #   default=deny(...) ; ask("get", ...) — label "read"
        self.assertVerdict("kubectl get pods", Verdict.ASK)
        # And it is the carve-out the operator is sent to read.
        self.assertEqual(
            self.labels(self.judgment("kubectl get pods")), ["read"]
        )

    def test_an_unproven_rule_is_not_a_rule_that_matched(self) -> None:
        # The refinement that keeps `D-059` safe: "no rule matched"
        # means the conditions were *satisfied*, never merely that the
        # rule contributed. Context B's stubcli denies by default and
        # carries a write-verb deny rule; a dynamic operand fires that
        # rule at **ask** strength (§4.2), and if that suppressed the
        # default then uncertainty would have softened a deny-default
        # tool — the one direction §3.3 forbids.
        #   default=deny(...)
        #   deny(when=at_least_one_operand(matching(WRITE_VERBS)))
        #   grant(when=at_least_one_operand(matching(READ_VERBS)))
        self.assertVerdict(
            "stubcli server $VERB x", Verdict.DENY, registry=CORPUS
        )

    def test_a_declared_silence_refuses_nothing(self) -> None:
        #   tool("pytest", default=silent(...))
        judgment = self.judgment("pytest tests/")
        self.assertIs(judgment.verdict, Verdict.SILENT)
        self.assertEqual(judgment.citations, ())

    def test_an_unregistered_tool_is_silence_in_the_default_posture(
        self,
    ) -> None:
        # Nothing declares `make`, and §4.1 forbids scanning the rest
        # of a parsed line for registered names.
        self.assertVerdict("make check", Verdict.SILENT)


class ThreeValuedTests(Judges):
    """§3.2: unproven always moves stricter, by role."""

    @classmethod
    def setUpClass(cls) -> None:
        def declare() -> None:
            tool(
                "kubectl",
                flags=[takes_value("--context")],
                rules=[
                    deny(
                        "delete",
                        when=flag("--context", one_of("production")),
                        reason="Deleting against the production cluster "
                        "has no authorized use. Switch context first.",
                        label="production context",
                    ),
                ],
            )

        cls.registry = composed(declare)

    def test_unproven_fires_a_deny_rule_at_ask_strength(self) -> None:
        # §4.2: "a dynamic value fires the rule at **ask** strength:
        # the gated value cannot be proven present (so no deny), but it
        # cannot be ruled out either (so never silence)".
        #   deny("delete", when=flag("--context", one_of("production")))
        self.assertVerdict(
            "kubectl delete pod api --context $CTX", Verdict.ASK
        )

    def test_unproven_releases_no_grant(self) -> None:
        # "it fails a grant condition (no release)". The contrast is
        # what makes it bite: the same grant holds on a literal path.
        #   grant("clean", when=every_operand(path_under("/tmp", ".scratch")))
        self.assertVerdict(
            "stubtool clean /tmp/x", Verdict.SILENT, registry=CORPUS
        )
        self.assertVerdict(
            "stubtool clean $TARGET", Verdict.ASK, registry=CORPUS
        )

    def test_a_cd_makes_a_later_relative_path_match_unproven(self) -> None:
        # §3.2: "a directory change earlier in the judged line
        # (`cd /elsewhere && tool ./x`) makes every later relative
        # *path* match unproven". Context B's `clean` grant is the one
        # with a **relative** boundary (`.scratch`), so it is the one a
        # `cd` can move. Corpus: `stubtool clean .scratch/build` →
        # **silent**.
        #   grant("clean", when=every_operand(path_under("/tmp", ".scratch")))
        for line, expected in (
            ("stubtool clean .scratch/build", Verdict.SILENT),
            ("cd /srv && stubtool clean .scratch/build", Verdict.ASK),
            # An absolute operand hangs off no base a `cd` can move.
            ("cd /srv && stubtool clean /tmp/x", Verdict.SILENT),
        ):
            with self.subTest(line=line):
                self.assertVerdict(line, expected, registry=CORPUS)

    def test_the_poisoning_is_path_matchers_only(self) -> None:
        # §3.2: "path matchers only; pattern and predicate matchers are
        # untouched". Corpus: `cd /srv && stubtool run/validates.yaml`
        # → **silent** — that grant is a pattern match.
        #   grant(when=every_operand(matching(VALIDATES)))
        self.assertVerdict(
            "cd /srv && stubtool run/validates.yaml",
            Verdict.SILENT,
            registry=CORPUS,
        )


class DoubtTests(Judges):
    """§3.3: a doubt reading recorded is priced here."""

    @classmethod
    def setUpClass(cls) -> None:
        def declare() -> None:
            # Rules-only and not gated: what a strange token costs
            # here is the question, and §4.2 scopes the
            # unreadable-token rule to *gated* tools.
            tool(
                "git",
                options=[takes_value("-C")],
                flags=[takes_value("-m")],
                rules=[
                    deny(
                        "push",
                        when=any_flag("-f", "--force"),
                        reason="A forced push rewrites remote history.",
                        label="forced push",
                    ),
                ],
            )
            # §4.2's path declaration, for the doubt an in-line `cd`
            # casts on a relative spelling of one.
            tool(
                "tools/deploy.py",
                default=ask(
                    reason="This project's deploy script deploys. Point "
                    "it at /tmp to rehearse."
                ),
                rules=[
                    deny(
                        "wipe",
                        reason="Wiping the deploy target is refused.",
                        label="deploy wipe",
                    ),
                ],
                grants=[
                    grant(
                        when=every_operand(path_under("/tmp")),
                        reason="A scratch target is not production.",
                    ),
                ],
            )

        cls.registry = composed(declare)

    def test_a_token_no_matcher_can_read_defeats_a_grant(self) -> None:
        # Corpus: `stubtool --syntax-check 'my file.yml'` → **ask**.
        # §4.2: "one operand carrying a space is not the plain word a
        # grant accepts."
        #   grant(when=any_flag("--syntax-check", "--list-tasks"))
        #   default=ask(...)
        self.assertVerdict(
            "stubtool --syntax-check 'my file.yml'",
            Verdict.ASK,
            registry=CORPUS,
        )

    def test_a_strange_token_costs_nothing_on_a_rules_only_tool(
        self,
    ) -> None:
        # §4.2 states the unreadable-token rule *on gated tools*: what
        # a strange token defeats is a grant, and a rules-only tool has
        # none. Corpus: `git commit -m 'a plain message'` → **silent**.
        #   tool("git", ...) — rules only, no grant, no closed world
        self.assertVerdict("git commit -m 'a plain message'", Verdict.SILENT)

    def test_a_malformed_invocation_is_unproven_not_safe(self) -> None:
        # §4.2: "a declared value-taking flag with nothing after it
        # makes the invocation malformed, which is unproven, not safe",
        # stated flat rather than on gated tools — so it costs an ask
        # even where the tool is silent by default (`D-053`).
        #   options=[takes_value("-C")]
        self.assertVerdict("git -C", Verdict.ASK)

    def test_a_relative_spelling_after_a_cd_degrades_recognition(
        self,
    ) -> None:
        # §4.2: "After an in-line `cd`, a relative spelling of a
        # path-declared tool is unproven and recognition degrades
        # stricter, like any path match." No grant releases, and the
        # tool's own deny fires at ask strength — the same treatment
        # any unproven path match gets (§3.2, `D-054`).
        #   tool("tools/deploy.py", default=ask(...), rules=[deny("wipe")],
        #        grants=[grant(when=every_operand(path_under("/tmp")))])
        self.assertVerdict("tools/deploy.py /tmp/x", Verdict.SILENT)
        self.assertVerdict("tools/deploy.py wipe", Verdict.DENY)
        self.assertVerdict("cd /srv && ./tools/deploy.py /tmp/x", Verdict.ASK)
        self.assertVerdict("cd /srv && ./tools/deploy.py wipe", Verdict.ASK)


class UnparseableTests(Judges):
    """§4.1: a line that cannot be parsed is unproven, not safe.

    Against the corpus, and no declaration decided any of it: the scan
    reads the raw line for a *speaking* name and nothing else.
    """

    def test_an_unparseable_line_is_priced_by_the_raw_scan(self) -> None:
        # Neither line parses, so neither produces an invocation and no
        # declaration decides either. What separates them is what
        # §4.1's raw scan found: `stubtool` carries rules and grants,
        # so it is *speaking* (§3.2); `echo` is registered nowhere. The
        # scan is `008`'s and is pinned in tests/test_reading.py; what
        # this step owes is its price — a non-empty scan asks, an empty
        # one is silence.
        #
        # Corpus: `stubtool 'unbalanced` → **ask**
        #         `echo 'unbalanced`     → **silent**
        asked = self.judgment("stubtool 'unbalanced")
        silent = self.judgment("echo 'unbalanced")
        self.assertIs(asked.verdict, Verdict.ASK)
        self.assertIs(silent.verdict, Verdict.SILENT)
        # Half a reading would let a grant hold over tokens nobody
        # finished reading, so neither line was judged at all (§4.1).
        self.assertEqual(asked.judged, ())
        self.assertEqual(silent.judged, ())

    def test_the_fallback_verdict_is_the_engines_own(self) -> None:
        # §6.2: a non-silent verdict carries a reason and a citation,
        # and no declaration reached this one.
        judgment = self.judgment("stubtool 'unbalanced")
        self.assertEqual(len(judgment.citations), 1)
        self.assertTrue(judgment.citations[0].reason.strip())
        self.assertIsNone(judgment.citations[0].label)


class SecureModeTests(Judges):
    """§3.2's global default verdict, replacing every implicit silence."""

    @classmethod
    def setUpClass(cls) -> None:
        def declare() -> None:
            # No `default=`: an implicit silence, which is what secure
            # mode replaces.
            tool(
                "npm",
                rules=[
                    ask(
                        "publish",
                        reason="Publishing puts a package on a public "
                        "registry, and a version cannot be unpublished.",
                        label="publish",
                    ),
                    deny(
                        "unpublish",
                        reason="Unpublishing breaks every install that "
                        "pinned this version.",
                        label="unpublish",
                    ),
                ],
            )
            # An explicitly declared silence, which secure mode keeps.
            tool(
                "pytest",
                default=silent(reason="Running the suite is the job."),
            )
            tool(
                "helm",
                flags=[bare("--dry-run")],
                grants=[
                    grant(
                        when=any_flag("--dry-run"),
                        reason="A dry run renders the chart and applies it "
                        "to nothing.",
                    ),
                ],
            )
            tool(
                "kubectl",
                default=deny(
                    reason="Every command against this cluster is the "
                    "operator's to approve."
                ),
            )

        cls.registry = composed(declare)

    def test_a_command_position_reaching_no_registered_tool_gets_it(
        self,
    ) -> None:
        # "It applies to command positions resolving to no registered
        # tool".
        self.assertVerdict("make check", Verdict.SILENT)
        self.assertVerdict("make check", Verdict.DENY, SECURE_DENY)
        self.assertVerdict("make check", Verdict.ASK, SECURE_ASK)

    def test_a_registered_tool_with_an_unset_default_gets_it(self) -> None:
        # "and equally to registered tools whose default verdict was
        # left unset".
        #   tool("npm", rules=[...])  — no default=
        self.assertVerdict("npm install", Verdict.SILENT)
        self.assertVerdict("npm install", Verdict.DENY, SECURE_DENY)

    def test_an_explicitly_declared_silence_survives_it(self) -> None:
        # "in secure mode there is no silent outcome anywhere unless
        # the configuration made it explicit: an explicitly declared
        # silent default".
        #   tool("pytest", default=silent(...))
        self.assertVerdict("pytest tests/", Verdict.SILENT, SECURE_DENY)

    def test_a_grant_that_holds_survives_it(self) -> None:
        # "or a grant that holds (a holding grant is always silence —
        # the proven-safe shape is the point of declaring it)".
        #   grant(when=any_flag("--dry-run"))
        self.assertVerdict(
            "helm upgrade api ./chart --dry-run", Verdict.SILENT, SECURE_DENY
        )

    def test_an_explicit_default_verdict_is_untouched(self) -> None:
        #   tool("kubectl", default=deny(...))
        self.assertVerdict("kubectl get pods", Verdict.DENY, SECURE_DENY)

    def test_a_matched_rule_leaves_the_global_default_unconsulted(
        self,
    ) -> None:
        # `D-059`: where a rule matched the default is not consulted,
        # and secure mode's global default is a default, not an
        # override. Both directions are needed and they catch opposite
        # faults — an ask rule must survive a deny default, or the
        # default was consulted; a deny rule must survive an ask
        # default, or the global default overrode it and a deny was
        # lost.
        #   ask("publish", ...) ; deny("unpublish", ...)
        self.assertVerdict("npm publish", Verdict.ASK, SECURE_DENY)
        self.assertVerdict(
            "npm unpublish left-pad@1.0.0", Verdict.DENY, SECURE_ASK
        )

    def test_a_command_the_line_cannot_name_gets_it(self) -> None:
        # §4.2: "A variable in *command position* (`$RUNNER deploy`)
        # … in secure mode it gets the global default, and in the
        # default posture outside those contexts it is silence".
        self.assertVerdict("$RUNNER deploy", Verdict.SILENT)
        self.assertVerdict("$RUNNER deploy", Verdict.DENY, SECURE_DENY)

    def test_an_unparseable_line_gets_it_regardless(self) -> None:
        # §4.1: "in secure mode (§3.2), the global default verdict
        # applies regardless" — regardless of the speaking scan.
        self.assertVerdict("echo 'unbalanced", Verdict.SILENT)
        self.assertVerdict("echo 'unbalanced", Verdict.DENY, SECURE_DENY)

    def test_the_global_default_carries_its_own_reason(self) -> None:
        # §6.2: every non-silent verdict carries a reason and a
        # citation. No declaration reached this one.
        judgment = self.judgment("make check", SECURE_DENY)
        self.assertEqual(len(judgment.citations), 1)
        self.assertIn("secure mode", judgment.citations[0].reason)
        self.assertIsNone(judgment.citations[0].label)


class CitationTests(Judges):
    """§6.2: every non-silent verdict says what was read and what fired."""

    @classmethod
    def setUpClass(cls) -> None:
        def declare() -> None:
            tool(
                "git",
                options=[takes_value("-C")],
                rules=[
                    deny(
                        "push",
                        when=any_flag("-f", "--force"),
                        reason="A forced push rewrites remote history.",
                        label="forced push",
                    ),
                    ask(
                        "push",
                        reason="A push reaches a remote.",
                        label="any push",
                    ),
                    ask(
                        "checkout",
                        when=option("-C", path_under("/srv")),
                        reason="A checkout under /srv discards work there.",
                        label="checkout under /srv",
                    ),
                ],
            )
            tool(
                "kubectl",
                flags=[takes_value("--context")],
                rules=[
                    deny(
                        "delete",
                        when=flag("--context", one_of("production")),
                        reason="Deleting against the production cluster "
                        "has no authorized use.",
                        label="production context",
                    ),
                ],
            )

        cls.registry = composed(declare)

    def test_only_the_deciding_rank_is_cited(self) -> None:
        # "not every weaker match beneath it." Context B's `wipe`
        # carries both an ask and a deny.
        #   ask("wipe", ...)  — label "wipe asks"
        #   deny("wipe", ...) — label "wipe denies"
        judgment = self.judgment(
            "stubtool wipe --syntax-check", registry=CORPUS
        )
        self.assertIs(judgment.verdict, Verdict.DENY)
        self.assertEqual(self.labels(judgment), ["wipe denies"])

    def test_every_declaration_at_the_deciding_rank_across_the_line(
        self,
    ) -> None:
        # "line evaluation is exhaustive — no short-circuit at the
        # first deciding match — and the citation names every
        # declaration at the deciding rank *across the whole line*
        # (`git push -f && git reset --hard` cites both)".
        judgment = self.judgment(
            "stubtool wipe && stub2 wipe", registry=CORPUS
        )
        self.assertIs(judgment.verdict, Verdict.DENY)
        self.assertEqual(self.labels(judgment), ["wipe denies", "wipe denies"])
        self.assertEqual(
            [citation.tool for citation in judgment.citations],
            ["stubtool", "stub2"],
        )

    def test_a_citation_names_the_tool_the_subcommand_and_what_matched(
        self,
    ) -> None:
        # "the tool, the subcommand path, the specific flag,
        # assignment, value or operand that matched, and which
        # declaration fired."
        #   deny("push", when=any_flag("-f", "--force")) — "forced push"
        judgment = self.judgment("git push -f")
        self.assertIs(judgment.verdict, Verdict.DENY)
        citation = judgment.citations[0]
        self.assertEqual(citation.tool, "git")
        self.assertEqual(citation.subcommand, ("push",))
        self.assertEqual(citation.read, ("flag -f",))
        self.assertEqual(citation.label, "forced push")
        # And where it was written, so the operator can open it.
        self.assertIsNotNone(citation.source)

    def test_an_assignment_that_fired_a_rule_is_named(self) -> None:
        #   deny(when=env("STUB_DANGER")) — label "danger assignment"
        judgment = self.judgment(
            "STUB_DANGER=1 stubtool --syntax-check a.yml", registry=CORPUS
        )
        self.assertIs(judgment.verdict, Verdict.DENY)
        self.assertEqual(self.phrases(judgment), ["environment STUB_DANGER"])

    def test_an_unaccounted_assignment_names_itself(self) -> None:
        # No declaration reached this verdict: the closed world did.
        #   assignments=[accounted("STUB_QUIET"), accounted("STUB_TARGET")]
        judgment = self.judgment(
            "STUB_UNKNOWN=1 stubtool --syntax-check a.yml", registry=CORPUS
        )
        self.assertIs(judgment.verdict, Verdict.ASK)
        self.assertEqual(self.phrases(judgment), ["environment STUB_UNKNOWN"])
        self.assertIsNone(judgment.citations[0].label)

    def test_a_flag_outside_the_closed_world_names_itself(self) -> None:
        # Corpus: `stubtool --syntax-check deploy.yml --unknown` →
        # **ask**. The verdict is the tool's default; what the operator
        # needs to know is which token cost them the grant.
        #   flags=[bare("--syntax-check", "--list-tasks"),
        #          takes_value("-i", "--inventory", "--tags", "--limit",
        #                      "--mode")]
        judgment = self.judgment(
            "stubtool --syntax-check deploy.yml --unknown", registry=CORPUS
        )
        self.assertIs(judgment.verdict, Verdict.ASK)
        self.assertEqual(self.phrases(judgment), ["flag --unknown"])

    def test_a_gated_default_cites_the_declaration_that_set_it(
        self,
    ) -> None:
        # §6.2: "for gated defaults also *how to satisfy a grant*" —
        # the reason is the declaration's, so the citation carries it.
        #   default=ask(reason="stubtool changes infrastructure unless
        #                       the run is proven to be a local question.")
        judgment = self.judgment("stubtool deploy.yml", registry=CORPUS)
        self.assertIs(judgment.verdict, Verdict.ASK)
        self.assertEqual(len(judgment.citations), 1)
        # A phrase unique to the *default* declaration: grant (1)'s
        # reason also says "local question", so that substring would
        # pass against an engine citing the grant that failed.
        self.assertIn("changes infrastructure", judgment.citations[0].reason)
        self.assertEqual(judgment.citations[0].tool, "stubtool")

    def test_an_operand_that_matched_is_named(self) -> None:
        #   deny(when=at_least_one_operand(matching(WRITE_VERBS)))
        judgment = self.judgment("stubcli server delete x", registry=CORPUS)
        self.assertIs(judgment.verdict, Verdict.DENY)
        self.assertEqual(self.phrases(judgment), ["operand 'delete'"])

    def test_an_option_that_matched_is_named_with_its_value(self) -> None:
        #   ask("checkout", when=option("-C", path_under("/srv")))
        judgment = self.judgment("git -C /srv/repo checkout main")
        self.assertIs(judgment.verdict, Verdict.ASK)
        self.assertEqual(self.phrases(judgment), ["option -C '/srv/repo'"])

    def test_an_unproven_condition_says_so(self) -> None:
        # The ask an operator will ask about: nothing on the line was
        # proven, and the citation has to say which token could not be.
        #   deny("delete", when=flag("--context", one_of("production")))
        judgment = self.judgment("kubectl delete pod api --context $CTX")
        self.assertIs(judgment.verdict, Verdict.ASK)
        self.assertEqual(
            self.phrases(judgment), ["flag --context '$CTX' (unproven)"]
        )

    def test_silence_carries_nothing_to_explain(self) -> None:
        judgment = self.judgment(
            "stubtool --syntax-check site.yml", registry=CORPUS
        )
        self.assertIs(judgment.verdict, Verdict.SILENT)
        self.assertEqual(judgment.citations, ())


class AllowStagingTests(Judges):
    """§6.1's allow rows wait on open fact (c) — `D-051`."""

    @classmethod
    def setUpClass(cls) -> None:
        def declare() -> None:
            # Context A's hedged allow, in the shape §6.3 gives it: a
            # commit carrying its message on the line.
            tool(
                "git",
                flags=[takes_value("-m", "--message")],
                rules=[
                    allow(
                        "commit",
                        when=flag("-m"),
                        reason="A commit with its message on the line "
                        "writes only to this repository.",
                        label="commit message",
                    ),
                ],
            )

        cls.registry = composed(declare)

    def test_an_invocation_can_earn_an_allow(self) -> None:
        # The verdict exists and a rule can declare it; what has not
        # shipped is the line-level release.
        #   allow("commit", when=flag("-m"))
        judgment = self.judgment("git commit -m wip")
        self.assertEqual(
            [judged.verdict for judged in judgment.judged], [Verdict.ALLOW]
        )

    def test_the_line_answers_silence_until_the_hedges_ship(self) -> None:
        judgment = self.judgment("git commit -m wip")
        self.assertIs(judgment.verdict, Verdict.SILENT)
        self.assertEqual(judgment.citations, ())


#: Context B's rulings, restricted to what judging alone decides.
#:
#: Complete for that restriction and deliberately overlapping the
#: focused cases above: those name the clause a ruling turns on, this
#: is the yardstick and has to stand on its own. `014` reproduces all
#: three contexts; what is knowingly absent here is everything behind
#: another program (`010`), every substitution, subshell and heredoc
#: (`011`), and both handoffs (`012`).
CORPUS_RULINGS = (
    # Grants, the closed world, and the tool's own default.
    ("stubtool --syntax-check site.yml", Verdict.SILENT),
    ("stubtool site.yml --syntax-check", Verdict.SILENT),
    ("stubtool -i prod --syntax-check site.yml", Verdict.SILENT),
    ("stubtool --tags foo --syntax-check deploy.yml", Verdict.SILENT),
    ("stubtool --list-tasks deploy.yml", Verdict.SILENT),
    ("stubtool run/validates.yaml", Verdict.SILENT),
    ("stubtool deploy.yml", Verdict.ASK),
    ("stubtool -i prod deploy.yml", Verdict.ASK),
    ("stubtool validates.yaml -e target=prod", Verdict.ASK),
    ("stubtool deploy.yml -i --syntax-check", Verdict.ASK),
    ("stubtool deploy.yml --tags --syntax-check", Verdict.ASK),
    ("stubtool deploy.yml --limit", Verdict.ASK),
    ("stubtool deploy.yml -e msg='--syntax-check'", Verdict.ASK),
    ("stubtool --syntax-check deploy.yml --unknown", Verdict.ASK),
    ("stubtool wipe --syntax-check", Verdict.DENY),
    ("stubtool touch --syntax-check", Verdict.ASK),
    ("stubtool other --syntax-check", Verdict.SILENT),
    # The assignment world.
    ("STUB_QUIET=1 stubtool --syntax-check site.yml", Verdict.SILENT),
    ("STUB_UNKNOWN=1 stubtool --syntax-check site.yml", Verdict.ASK),
    ("STUB_DANGER=1 stubtool --syntax-check site.yml", Verdict.DENY),
    ("STUB_QUIET=1 stubtool deploy.yml", Verdict.ASK),
    ("STUB_TARGET=/tmp/x stubtool apply", Verdict.SILENT),
    ("STUB_TARGET=/prod stubtool apply", Verdict.ASK),
    ("stubtool apply", Verdict.ASK),
    ("STUB_TARGET=/tmp/../etc stubtool apply", Verdict.ASK),
    ("STUB_TARGET=/tmp/../../root stubtool apply", Verdict.ASK),
    ("STUB_TARGET=/tmp/a/../b stubtool apply", Verdict.SILENT),
    ("STUB_TARGET=/tmp stubtool apply", Verdict.SILENT),
    ("STUB_TARGET=/tmpevil stubtool apply", Verdict.ASK),
    ("STUB_TARGET=tmp/x stubtool apply", Verdict.ASK),
    ("STUB_TARGET=~/tmp stubtool apply", Verdict.ASK),
    ("STUB_TARGET=/home/yann/scratch stubtool apply", Verdict.SILENT),
    ("STUB_TARGET=/home/yann/scratch/build stubtool apply", Verdict.SILENT),
    ("STUB_TARGET=/home/a/b/scratch stubtool apply", Verdict.ASK),
    ("STUB_TARGET=/home/yann/other stubtool apply", Verdict.ASK),
    ("STUB_TARGET=/mnt/data/build stubtool apply", Verdict.SILENT),
    ("STUB_TARGET=/mnt/data/builds stubtool apply", Verdict.ASK),
    ("STUB_TARGET=/mnt/data/build/sub stubtool apply", Verdict.ASK),
    ("STUB_TARGET=/home/yann/scratch/../../etc stubtool apply", Verdict.ASK),
    ("STUB_TARGET=/mnt/data/build/../../../etc stubtool apply", Verdict.ASK),
    ("stubtool apply --mode dry-run", Verdict.SILENT),
    ("stubtool apply --mode check", Verdict.SILENT),
    ("stubtool apply --mode destroy", Verdict.ASK),
    ("stubtool apply --mode", Verdict.ASK),
    ("stubtool --syntax-check STUB_DANGER=1", Verdict.SILENT),
    ("STUB_QUIET=1 STUB_TARGET=/tmp/x stubtool apply", Verdict.SILENT),
    ("STUB_DANGER+=1 stubtool --syntax-check site.yml", Verdict.DENY),
    ("STUB_QUIET+=1 stubtool --syntax-check site.yml", Verdict.SILENT),
    ("stub_danger=1 stubtool --syntax-check site.yml", Verdict.ASK),
    # A deny default, a read verb, a write verb.
    ("stubcli server list", Verdict.SILENT),
    ("stubcli security group rule list", Verdict.SILENT),
    ("stubcli catalog list", Verdict.SILENT),
    ("stubcli server delete x", Verdict.DENY),
    ("stubcli server frobnicate x", Verdict.DENY),
    ("stubcli", Verdict.DENY),
    ("stubcli server list && stubcli server delete x", Verdict.DENY),
    ("stubcli server delete list", Verdict.DENY),
    ("stubalways anything at all", Verdict.DENY),
    ("stubalways", Verdict.DENY),
    # A registered name used as an ordinary word, and near-misses.
    ("grep stubtool README.md", Verdict.SILENT),
    ("ls ../stubtool", Verdict.SILENT),
    ("cat docs/env", Verdict.SILENT),
    ("echo 'stubtool deploy.yml'", Verdict.SILENT),
    ("stubtool-extra deploy.yml", Verdict.SILENT),
    ("mystubtool deploy.yml", Verdict.SILENT),
    ("stub2x wipe", Verdict.SILENT),
    # Aliases are fully equivalent names.
    ("stub2 wipe", Verdict.DENY),
    ("stub2 --syntax-check site.yml", Verdict.SILENT),
    ("stub2 deploy.yml", Verdict.ASK),
    # A subcommand and a path boundary.
    ("stubtool clean /tmp/x", Verdict.SILENT),
    ("stubtool clean /tmp/x /tmp/y", Verdict.SILENT),
    ("stubtool clean .scratch/build", Verdict.SILENT),
    ("stubtool clean ./.scratch/build", Verdict.SILENT),
    ("stubtool clean /tmp/x /etc/passwd", Verdict.ASK),
    ("stubtool clean /etc/passwd", Verdict.ASK),
    ("stubtool clean /tmp/../etc", Verdict.ASK),
    ("stubtool clean .scratch/../secrets", Verdict.ASK),
    ("stubtool clean .scratch/a/../b", Verdict.SILENT),
    ("stubtool clean", Verdict.ASK),
    ("stubtool build .", Verdict.ASK),
    ("stubtool --syntax-check 'my file.yml'", Verdict.ASK),
    ("cd /srv && stubtool run/validates.yaml", Verdict.SILENT),
    # Separators: every invocation judged, none vouching for another.
    ("stubtool deploy.yml && stubtool --syntax-check a.yml", Verdict.ASK),
    ("stubtool --syntax-check a.yml && stubtool deploy.yml", Verdict.ASK),
    (
        "stubtool --syntax-check a.yml && stubtool b.yml --syntax-check",
        Verdict.SILENT,
    ),
    ("stubtool --syntax-check a.yml; stubtool deploy.yml", Verdict.ASK),
    ("stubtool --syntax-check a.yml | stubtool deploy.yml", Verdict.ASK),
    ("stubtool --syntax-check a.yml && stubtool wipe", Verdict.DENY),
    ("stubtool wipe && stubtool --syntax-check a.yml", Verdict.DENY),
    ("stubtool --syntax-check a.yml\nstubtool deploy.yml", Verdict.ASK),
    ("stubtool deploy.yml\nstubtool --syntax-check a.yml", Verdict.ASK),
    ("echo hi\nstubtool deploy.yml", Verdict.ASK),
    ("stubtool --syntax-check a.yml\n\n\nstubtool deploy.yml", Verdict.ASK),
    (
        "stubtool --syntax-check a.yml\nstubtool --list-tasks b.yml",
        Verdict.SILENT,
    ),
    ('echo "one\nstubtool deploy.yml"', Verdict.SILENT),
    ("stubtool deploy.yml \\\n--syntax-check", Verdict.SILENT),
    ("stubtool deploy.yml \\\n         --syntax-check", Verdict.SILENT),
    ("stubtool \\\n--syntax-check site.yml", Verdict.SILENT),
    ("stubtool deploy.yml  # --syntax-check next time", Verdict.ASK),
    # §4.1's unparseable fallback.
    ("stubtool 'unbalanced", Verdict.ASK),
    ("echo 'unbalanced", Verdict.SILENT),
    # Ordinary lines nothing gates.
    ("make check", Verdict.SILENT),
    ("ls -la && rg TODO src/", Verdict.SILENT),
    ("python3 scripts/build.py --force", Verdict.SILENT),
    ('echo "no substitution here"', Verdict.SILENT),
)


class CorpusTests(Judges):
    """The adjudicated corpus, for the part `009` can reach."""

    def test_every_ruling_in_scope(self) -> None:
        for line, expected in CORPUS_RULINGS:
            with self.subTest(line=line):
                self.assertVerdict(line, expected)

    def test_every_non_silent_verdict_carries_a_reason_and_a_citation(
        self,
    ) -> None:
        # §6.2, over every ruling at once: "Every non-silent verdict
        # must carry a reason **and a citation**", because "a wrong
        # verdict that cannot be traced to a line of configuration
        # cannot be reported".
        for line, expected in CORPUS_RULINGS:
            if expected is Verdict.SILENT:
                continue
            with self.subTest(line=line):
                judgment = self.judgment(line)
                self.assertTrue(judgment.citations, line)
                for citation in judgment.citations:
                    self.assertIs(citation.verdict, expected)
                    self.assertTrue(citation.reason.strip(), citation)
