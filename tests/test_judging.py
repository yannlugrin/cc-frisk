"""§3.2, §3.3, §6.1 and §6.2: what frisk answers, and why.

Every case here is transcribed from `SPECIFICATIONS.md` §3.2, §3.3,
§4.1, §6.1 and §6.2, or from a ruling in
`.claude/refs/behavior-corpus.md` — never from the engine, which does
not judge anything yet. Where a corpus ruling is the provenance, the
ruling is quoted beside the case.

Four boundaries are deliberate, and a case asserting the interim
behaviour on the far side of one would be a case a later step has to
undo. What lives behind another program — a wrapper's command, a
shell's `-c` payload, an interpreter's file operand — is `010`.
Substitutions, subshells and heredocs are `011`; handoffs and
redirection targets are `012`. And the **allow rows of §6.1's table**
are `017`, behind open fact (c) at `015`: a rule may declare `allow`
today, but no line answers one, so the cases here pin the withholding
rather than a release (`D-051`).

The corpus is therefore reproduced in part: the context B rulings this
step can reach, and no more. `014` is where all three contexts are
reproduced end to end; what stands here is the subset that judging
alone decides, so a regression in it is caught at the step that
introduced it rather than five steps later.
"""

from __future__ import annotations

import unittest

from frisk.declare import (
    accounted,
    allow,
    any_flag,
    ask,
    at_least_one_operand,
    bare,
    deny,
    every_operand,
    flag,
    grant,
    host_only,
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
    policy and no other, so a tool invented for a spec case would make
    every corpus verdict answer a different question.
    """
    with collecting() as declared:
        context_b.declare()
    return declared.registry()


def shapes() -> Registry:
    """The shapes §3.2 and §6.2 name that no context B ruling carries.

    A second registry rather than more tools in the first, for the
    reason above. Each entry exists for one clause, named where it is
    declared.
    """
    with collecting() as declared:
        # §3.2's rules-only tool: safe by default, a listable set of
        # dangerous acts, and a value condition on a *rule* — "Value
        # conditions must be available to deny and ask rules, not only
        # to grants".
        tool(
            "rulesonly",
            options=[takes_value("-C")],
            flags=[takes_value("--target", "--message")],
            rules=[
                deny(
                    "push",
                    when=any_flag("-f", "--force"),
                    reason="A forced push rewrites remote history.",
                    label="forced push",
                ),
                ask(
                    "push",
                    reason="A push reaches a remote. Push a branch instead.",
                    label="any push",
                ),
                deny(
                    "write",
                    when=flag("--target", path_under("/prod")),
                    reason="Writing to /prod has no authorized use.",
                    label="production target",
                ),
                ask(
                    "checkout",
                    when=option("-C", path_under("/srv")),
                    reason="A checkout under /srv discards work there.",
                    label="checkout under /srv",
                ),
            ],
        )
        # §3.2's "an explicit verdict": every use of this one is the
        # operator's.
        tool("always", default=deny(reason="Every use of always is yours."))
        # A declared silence — §3.2's "an explicitly declared silent
        # default", which secure mode must keep.
        tool("mute", default=silent(reason="Nothing to say."))
        # No default at all, no grants: §3.2's implicit "silent for a
        # rules-only tool".
        tool(
            "unset",
            rules=[
                ask("burn", reason="Burning destroys state.", label="burn"),
            ],
        )
        # No default at all, *granted*: §3.2's implicit "ask for a
        # granted tool".
        tool(
            "unsetgated",
            flags=[bare("--dry-run")],
            grants=[
                grant(
                    when=any_flag("--dry-run"),
                    reason="A dry run applies nothing.",
                ),
            ],
        )
        # §3.2's other two quantifier forms, and the closed world
        # declared without a grant.
        tool(
            "shaped",
            default=ask(reason="shaped changes state unless proven local."),
            flags=[bare("--all"), takes_value("--path")],
            grants=[
                grant(
                    "status",
                    when=no_operands(),
                    reason="Status with no target reads one thing.",
                ),
                grant(
                    "read",
                    when=at_least_one_operand(path_under("/tmp")),
                    reason="A scratch path is not production.",
                ),
            ],
        )
        # §4.3/§5.2's scopes. `inside` names a handoff no line here
        # enters, so it must never fire; `host_only` must.
        tool(
            "scoped",
            rules=[
                deny(
                    "run",
                    reason="Running this inside a container is refused.",
                    label="inside only",
                    scope=inside("scoped exec"),
                ),
                ask(
                    "run",
                    reason="Running this on the host asks.",
                    label="host only",
                    scope=host_only,
                ),
            ],
        )
        # §6.3's verdict, declared so §6.1's allow rows can be pinned
        # as *withheld* until `017`.
        tool(
            "hedged",
            flags=[takes_value("-m")],
            rules=[
                allow(
                    "commit",
                    when=flag("-m"),
                    reason="A commit message is the one hedged grant.",
                    label="commit message",
                ),
            ],
        )
        # §3.2's assignment world on a tool that is *not* gated, and
        # the value-conditioned accounting it names: "`GIT_PAGER`
        # acceptable as `cat`, asking otherwise".
        tool(
            "paged",
            assignments=[accounted("PAGER", one_of("cat"))],
            rules=[
                ask("push", reason="A push reaches a remote.", label="push"),
            ],
        )
        # §4.2's path declaration, for the doubt an in-line `cd` casts
        # on a relative spelling of one.
        tool(
            "tools/deploy.py",
            default=ask(reason="This project's deploy script deploys."),
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
    return declared.registry()


#: Composed once each: composition is `007`'s subject, not this file's.
CORPUS = corpus_policy()
SHAPES = shapes()


class Judges(unittest.TestCase):
    """What every case below needs to reach a verdict."""

    registry = CORPUS

    def judgment(self, command_line: str, secure: object = None) -> Judgment:
        return judge(
            read(command_line, self.registry),
            self.registry,
            secure,  # type: ignore[arg-type]
        )

    def verdict(self, command_line: str, secure: object = None) -> Verdict:
        return self.judgment(command_line, secure).verdict

    def assertVerdict(  # noqa: N802 — unittest's own casing
        self,
        command_line: str,
        expected: Verdict,
        secure: object = None,
    ) -> None:
        reached = self.judgment(command_line, secure)
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


class Shaped(Judges):
    """The cases judged against the hand-written shapes."""

    registry = SHAPES


class CombinationTests(unittest.TestCase):
    """§6.1's table, dangerous branches first."""

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
    """§3.2: each invocation is judged alone."""

    def test_a_safe_command_never_vouches_for_its_neighbour(self) -> None:
        # Corpus: `stubtool --syntax-check a.yml && stubtool deploy.yml`
        # → **ask**.
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
        rules = {
            "ask": ask("wipe", reason="Wiping destroys state.", label="a"),
            "deny": deny("wipe", reason="Wiping is refused.", label="d"),
        }
        ordered = (
            [rules["ask"], rules["deny"]]
            if first == "ask"
            else [rules["deny"], rules["ask"]]
        )
        with collecting() as declared:
            tool("both", rules=ordered)
        return declared.registry()

    def test_reordering_rules_inside_a_source_changes_nothing(self) -> None:
        # "reordering the rules inside a source never changes a
        # verdict" — the ranking decides, not the order found in.
        for first in ("ask", "deny"):
            with self.subTest(first=first):
                registry = self.registry_with(first)
                judgment = judge(read("both wipe", registry), registry)
                self.assertIs(judgment.verdict, Verdict.DENY)
                # And the citation names only the deciding rank.
                self.assertEqual(
                    [citation.label for citation in judgment.citations], ["d"]
                )


class RuleTests(Shaped):
    """§3.2's rules, checked existentially."""

    def test_naming_an_act_gates_it(self) -> None:
        self.assertVerdict("rulesonly push -f", Verdict.DENY)
        self.assertVerdict("rulesonly push", Verdict.ASK)

    def test_every_act_unnamed_falls_through_silently(self) -> None:
        # "every *subcommand and flag* unnamed falls through silently".
        self.assertVerdict("rulesonly status", Verdict.SILENT)
        self.assertVerdict("rulesonly status --unheard-of", Verdict.SILENT)

    def test_a_rule_may_condition_on_a_flag_value(self) -> None:
        # §3.2: "Value conditions must be available to deny and ask
        # rules, not only to grants".
        self.assertVerdict("rulesonly write --target /prod/x", Verdict.DENY)
        self.assertVerdict("rulesonly write --target /tmp/x", Verdict.SILENT)

    def test_a_rule_may_condition_on_a_pre_subcommand_option_value(
        self,
    ) -> None:
        # §4.2: "'pushing is fine only for repositories under this
        # directory' is a rule on `-C`'s value."
        self.assertVerdict("rulesonly -C /srv/repo checkout m", Verdict.ASK)
        self.assertVerdict("rulesonly -C /home/x checkout m", Verdict.SILENT)
        self.assertVerdict("rulesonly checkout m", Verdict.SILENT)

    def test_a_rule_scoped_inside_a_handoff_never_fires_on_the_host(
        self,
    ) -> None:
        # §5.2: "the same tool may carry different rules on the host
        # and inside a named handoff". Nothing here is inside one, so
        # the host rule decides and the inside rule stays silent — an
        # ask, never the deny the inside rule declares.
        self.assertVerdict("scoped run", Verdict.ASK)


class GrantTests(Shaped):
    """§3.2's grants, checked universally and closed-world."""

    def test_a_grant_that_holds_is_silence(self) -> None:
        self.assertVerdict("unsetgated --dry-run", Verdict.SILENT)

    def test_an_invocation_matching_no_grant_gets_the_default(self) -> None:
        self.assertVerdict("unsetgated", Verdict.ASK)

    def test_a_flag_outside_the_closed_world_defeats_every_grant(
        self,
    ) -> None:
        # §3.3: "an unknown flag on a gated tool: stricter, never
        # quieter". The grant would hold on `--dry-run` alone.
        self.assertVerdict("unsetgated --dry-run --unknown", Verdict.ASK)

    def test_no_operands_is_the_empty_case_spelled_deliberately(
        self,
    ) -> None:
        self.assertVerdict("shaped status", Verdict.SILENT)
        self.assertVerdict("shaped status x", Verdict.ASK)

    def test_at_least_one_operand_needs_one_that_satisfies(self) -> None:
        self.assertVerdict("shaped read /tmp/x /etc/passwd", Verdict.SILENT)
        self.assertVerdict("shaped read /etc/passwd", Verdict.ASK)

    def test_a_quantified_operand_matcher_needs_at_least_one_operand(
        self,
    ) -> None:
        # §3.2: "empty operands are never vacuously granted (a command
        # acting on nothing has not proven what it acts on)".
        self.assertVerdict("shaped read", Verdict.ASK)

    def test_rules_hold_even_where_a_grant_would_release(self) -> None:
        # Corpus: `stubtool touch --syntax-check` → **ask**, though
        # grant (1) holds on `--syntax-check`.
        judgment = judge(read("stubtool touch --syntax-check", CORPUS), CORPUS)
        self.assertIs(judgment.verdict, Verdict.ASK)


class AssignmentWorldTests(Shaped):
    """§3.2: assignments are closed-world for every registered tool."""

    def test_an_unaccounted_assignment_asks_on_a_rules_only_tool(
        self,
    ) -> None:
        # "**Environment assignments are closed-world for every
        # registered tool**, not only gated ones". `paged` declares one
        # rule and no grant, and still owes this accounting.
        self.assertVerdict("FOO=1 paged status", Verdict.ASK)

    def test_the_universal_benign_list_accounts_for_the_locale_class(
        self,
    ) -> None:
        # "the display/locale class — `LC_*`, `LANG`, `TZ`, `NO_COLOR`
        # and kin, variables that cannot direct execution".
        self.assertVerdict("LC_ALL=C paged status", Verdict.SILENT)
        self.assertVerdict("LANG=C paged status", Verdict.SILENT)

    def test_an_accounted_assignment_may_be_value_conditioned(self) -> None:
        # "(by name, optionally value-conditioned — `GIT_PAGER`
        # acceptable as `cat`, asking otherwise)".
        self.assertVerdict("PAGER=cat paged status", Verdict.SILENT)
        self.assertVerdict("PAGER=less paged status", Verdict.ASK)

    def test_assignments_ahead_of_an_unregistered_tool_keep_its_posture(
        self,
    ) -> None:
        # "because an opinion the guard does not have about `make`
        # should not appear because of a harmless `DEBUG=1`."
        self.assertVerdict("DEBUG=1 make check", Verdict.SILENT)

    def test_an_assignment_after_the_command_name_is_an_operand(
        self,
    ) -> None:
        # Corpus: `stubtool --syntax-check STUB_DANGER=1` → **silent**.
        judgment = judge(
            read("stubtool --syntax-check STUB_DANGER=1", CORPUS), CORPUS
        )
        self.assertIs(judgment.verdict, Verdict.SILENT)


class DefaultVerdictTests(Shaped):
    """§3.2's per-tool default verdicts."""

    def test_a_rules_only_tool_with_no_declared_default_is_silent(
        self,
    ) -> None:
        # "silent for a rules-only tool".
        self.assertVerdict("unset anything", Verdict.SILENT)
        self.assertVerdict("unset burn", Verdict.ASK)

    def test_a_granted_tool_with_no_declared_default_asks(self) -> None:
        # "ask for a granted tool".
        self.assertVerdict("unsetgated", Verdict.ASK)

    def test_an_explicit_verdict_stands_on_its_own(self) -> None:
        # "'every use of this one is the operator's' is a tool with a
        # deny default and nothing else." Corpus: `stubalways anything
        # at all` → **deny**.
        self.assertVerdict("always", Verdict.DENY)
        self.assertVerdict("always --anything at all", Verdict.DENY)

    def test_a_declared_silence_refuses_nothing(self) -> None:
        # §5.3: "a declared silence refuses nothing and so has nothing
        # to explain".
        judgment = self.judgment("mute anything")
        self.assertIs(judgment.verdict, Verdict.SILENT)
        self.assertEqual(judgment.citations, ())

    def test_an_unregistered_tool_is_silence_in_the_default_posture(
        self,
    ) -> None:
        self.assertVerdict("make check", Verdict.SILENT)


class ThreeValuedTests(Shaped):
    """§3.2: unproven always moves stricter, by role."""

    def test_unproven_fires_a_deny_rule_at_ask_strength(self) -> None:
        # §4.2: "a dynamic value fires the rule at **ask** strength:
        # the gated value cannot be proven present (so no deny), but it
        # cannot be ruled out either (so never silence)".
        self.assertVerdict("rulesonly write --target $TARGET", Verdict.ASK)

    def test_unproven_releases_no_grant(self) -> None:
        # "it fails a grant condition (no release)".
        self.assertVerdict("shaped read $TARGET", Verdict.ASK)

    def test_a_cd_makes_a_later_relative_path_match_unproven(self) -> None:
        # §3.2: "a directory change earlier in the judged line
        # (`cd /elsewhere && tool ./x`) makes every later relative
        # *path* match unproven". Context B's `clean` grant is the one
        # with a **relative** boundary (`.scratch`), so it is the one a
        # `cd` can move. Corpus: `stubtool clean .scratch/build` →
        # **silent**.
        judge_against = CORPUS
        for line, expected in (
            ("stubtool clean .scratch/build", Verdict.SILENT),
            ("cd /srv && stubtool clean .scratch/build", Verdict.ASK),
            # An absolute operand hangs off no base a `cd` can move.
            ("cd /srv && stubtool clean /tmp/x", Verdict.SILENT),
        ):
            with self.subTest(line=line):
                reached = judge(read(line, judge_against), judge_against)
                self.assertIs(reached.verdict, expected)

    def test_the_poisoning_is_path_matchers_only(self) -> None:
        # §3.2: "path matchers only; pattern and predicate matchers are
        # untouched". Corpus: `cd /srv && stubtool run/validates.yaml`
        # → **silent** — that grant is a pattern match.
        reached = judge(
            read("cd /srv && stubtool run/validates.yaml", CORPUS), CORPUS
        )
        self.assertIs(reached.verdict, Verdict.SILENT)


class DoubtTests(Shaped):
    """§3.3: a doubt reading recorded is priced here."""

    def test_a_token_no_matcher_can_read_defeats_a_grant(self) -> None:
        # Corpus: `stubtool --syntax-check 'my file.yml'` → **ask**.
        # §4.2: "one operand carrying a space is not the plain word a
        # grant accepts."
        judgment = judge(
            read("stubtool --syntax-check 'my file.yml'", CORPUS), CORPUS
        )
        self.assertIs(judgment.verdict, Verdict.ASK)

    def test_a_strange_token_costs_nothing_on_a_rules_only_tool(
        self,
    ) -> None:
        # §4.2 states the unreadable-token rule *on gated tools*: what
        # a strange token defeats is a grant, and a rules-only tool has
        # none.
        self.assertVerdict("rulesonly status 'my file'", Verdict.SILENT)

    def test_a_malformed_invocation_is_unproven_not_safe(self) -> None:
        # §4.2: "a declared value-taking flag with nothing after it
        # makes the invocation malformed, which is unproven, not safe",
        # stated flat rather than on gated tools — so it costs an ask
        # even where the tool is silent by default (`D-053`).
        self.assertVerdict("rulesonly --target", Verdict.ASK)

    def test_a_relative_spelling_after_a_cd_degrades_recognition(
        self,
    ) -> None:
        # §4.2: "After an in-line `cd`, a relative spelling of a
        # path-declared tool is unproven and recognition degrades
        # stricter, like any path match." No grant releases, and the
        # tool's own deny fires at ask strength — the same treatment
        # any unproven path match gets (§3.2).
        self.assertVerdict("tools/deploy.py /tmp/x", Verdict.SILENT)
        self.assertVerdict("tools/deploy.py wipe", Verdict.DENY)
        self.assertVerdict("cd /srv && ./tools/deploy.py /tmp/x", Verdict.ASK)
        self.assertVerdict("cd /srv && ./tools/deploy.py wipe", Verdict.ASK)


class UnparseableTests(Judges):
    """§4.1: a line that cannot be parsed is unproven, not safe."""

    def test_a_speaking_name_on_an_unparseable_line_asks(self) -> None:
        # Corpus: `stubtool 'unbalanced` → **ask**.
        judgment = self.judgment("stubtool 'unbalanced")
        self.assertIs(judgment.verdict, Verdict.ASK)
        self.assertEqual(judgment.judged, ())
        # §6.2: a non-silent verdict carries a reason, and this one is
        # the engine's own — no declaration reached it.
        self.assertEqual(len(judgment.citations), 1)
        self.assertTrue(judgment.citations[0].reason.strip())
        self.assertIsNone(judgment.citations[0].label)

    def test_an_unparseable_line_naming_nothing_that_speaks_is_silent(
        self,
    ) -> None:
        # Corpus: `echo 'unbalanced` → **silent**.
        self.assertVerdict("echo 'unbalanced", Verdict.SILENT)


class SecureModeTests(Shaped):
    """§3.2's global default verdict, replacing every implicit silence."""

    #: The switch is `033`'s; the capability is this step's, so the
    #: cases reach it the only way anything can today — as an argument.
    SECURE = deny(
        reason=(
            "This project runs in secure mode: nothing frisk has not "
            "been taught is allowed to run unremarked."
        )
    )
    ASKING = ask(reason="Secure mode: say what this command is.")

    def test_a_command_position_reaching_no_registered_tool_gets_it(
        self,
    ) -> None:
        # "It applies to command positions resolving to no registered
        # tool".
        self.assertVerdict("make check", Verdict.SILENT)
        self.assertVerdict("make check", Verdict.DENY, self.SECURE)
        self.assertVerdict("make check", Verdict.ASK, self.ASKING)

    def test_a_registered_tool_with_an_unset_default_gets_it(self) -> None:
        # "and equally to registered tools whose default verdict was
        # left unset".
        self.assertVerdict("unset anything", Verdict.SILENT)
        self.assertVerdict("unset anything", Verdict.DENY, self.SECURE)

    def test_an_explicitly_declared_silence_survives_it(self) -> None:
        # "in secure mode there is no silent outcome anywhere unless
        # the configuration made it explicit: an explicitly declared
        # silent default".
        self.assertVerdict("mute anything", Verdict.SILENT, self.SECURE)

    def test_a_grant_that_holds_survives_it(self) -> None:
        # "or a grant that holds (a holding grant is always silence —
        # the proven-safe shape is the point of declaring it)".
        self.assertVerdict("unsetgated --dry-run", Verdict.SILENT, self.SECURE)

    def test_an_explicit_default_verdict_is_untouched(self) -> None:
        self.assertVerdict("always", Verdict.DENY, self.SECURE)

    def test_a_declared_rule_still_decides(self) -> None:
        self.assertVerdict("unset burn", Verdict.ASK, self.SECURE)

    def test_a_command_the_line_cannot_name_gets_it(self) -> None:
        # §4.2: "A variable in *command position* (`$RUNNER deploy`)
        # … in secure mode it gets the global default, and in the
        # default posture outside those contexts it is silence".
        self.assertVerdict("$RUNNER deploy", Verdict.SILENT)
        self.assertVerdict("$RUNNER deploy", Verdict.DENY, self.SECURE)

    def test_an_unparseable_line_gets_it_regardless(self) -> None:
        # §4.1: "in secure mode (§3.2), the global default verdict
        # applies regardless" — regardless of the speaking scan.
        self.assertVerdict("echo 'unbalanced", Verdict.SILENT)
        self.assertVerdict("echo 'unbalanced", Verdict.DENY, self.SECURE)

    def test_the_global_default_carries_its_own_reason(self) -> None:
        # §6.2: every non-silent verdict carries a reason and a
        # citation. No declaration reached this one.
        judgment = self.judgment("make check", self.SECURE)
        self.assertEqual(len(judgment.citations), 1)
        self.assertIn("secure mode", judgment.citations[0].reason)
        self.assertIsNone(judgment.citations[0].label)


class CitationTests(Judges):
    """§6.2: every non-silent verdict says what was read and what fired."""

    def test_only_the_deciding_rank_is_cited(self) -> None:
        # "not every weaker match beneath it." Context B's `wipe`
        # carries both an ask and a deny.
        judgment = self.judgment("stubtool wipe --syntax-check")
        self.assertIs(judgment.verdict, Verdict.DENY)
        self.assertEqual(self.labels(judgment), ["wipe denies"])

    def test_every_declaration_at_the_deciding_rank_across_the_line(
        self,
    ) -> None:
        # "line evaluation is exhaustive — no short-circuit at the
        # first deciding match — and the citation names every
        # declaration at the deciding rank *across the whole line*
        # (`git push -f && git reset --hard` cites both)".
        judgment = self.judgment("stubtool wipe && stub2 wipe")
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
        judgment = judge(read("rulesonly push -f", SHAPES), SHAPES)
        self.assertIs(judgment.verdict, Verdict.DENY)
        citation = judgment.citations[0]
        self.assertEqual(citation.tool, "rulesonly")
        self.assertEqual(citation.subcommand, ("push",))
        self.assertEqual(citation.read, ("flag -f",))
        self.assertEqual(citation.label, "forced push")
        # And where it was written, so the operator can open it.
        self.assertIsNotNone(citation.source)

    def test_an_assignment_that_fired_a_rule_is_named(self) -> None:
        judgment = self.judgment("STUB_DANGER=1 stubtool --syntax-check a.yml")
        self.assertIs(judgment.verdict, Verdict.DENY)
        self.assertEqual(self.phrases(judgment), ["environment STUB_DANGER"])

    def test_an_unaccounted_assignment_names_itself(self) -> None:
        # No declaration reached this verdict: the closed world did.
        judgment = self.judgment(
            "STUB_UNKNOWN=1 stubtool --syntax-check a.yml"
        )
        self.assertIs(judgment.verdict, Verdict.ASK)
        self.assertEqual(self.phrases(judgment), ["environment STUB_UNKNOWN"])
        self.assertIsNone(judgment.citations[0].label)

    def test_a_flag_outside_the_closed_world_names_itself(self) -> None:
        # Corpus: `stubtool --syntax-check deploy.yml --unknown` →
        # **ask**. The verdict is the tool's default; what the operator
        # needs to know is which token cost them the grant.
        judgment = self.judgment(
            "stubtool --syntax-check deploy.yml --unknown"
        )
        self.assertIs(judgment.verdict, Verdict.ASK)
        self.assertEqual(self.phrases(judgment), ["flag --unknown"])

    def test_a_gated_default_cites_the_declaration_that_set_it(
        self,
    ) -> None:
        # §6.2: "for gated defaults also *how to satisfy a grant*" —
        # the reason is the declaration's, so the citation carries it.
        judgment = self.judgment("stubtool deploy.yml")
        self.assertIs(judgment.verdict, Verdict.ASK)
        self.assertEqual(len(judgment.citations), 1)
        self.assertIn("local question", judgment.citations[0].reason)
        self.assertEqual(judgment.citations[0].tool, "stubtool")

    def test_an_operand_that_matched_is_named(self) -> None:
        judgment = self.judgment("stubcli server delete x")
        self.assertIs(judgment.verdict, Verdict.DENY)
        self.assertEqual(self.phrases(judgment), ["operand 'delete'"])

    def test_an_option_that_matched_is_named_with_its_value(self) -> None:
        judgment = judge(
            read("rulesonly -C /srv/r checkout m", SHAPES), SHAPES
        )
        self.assertIs(judgment.verdict, Verdict.ASK)
        self.assertEqual(self.phrases(judgment), ["option -C '/srv/r'"])

    def test_an_unproven_condition_says_so(self) -> None:
        # The ask an operator will ask about: nothing on the line was
        # proven, and the citation has to say which token could not be.
        judgment = judge(
            read("rulesonly write --target $TARGET", SHAPES), SHAPES
        )
        self.assertIs(judgment.verdict, Verdict.ASK)
        self.assertEqual(
            self.phrases(judgment), ["flag --target '$TARGET' (unproven)"]
        )

    def test_silence_carries_nothing_to_explain(self) -> None:
        judgment = self.judgment("stubtool --syntax-check site.yml")
        self.assertIs(judgment.verdict, Verdict.SILENT)
        self.assertEqual(judgment.citations, ())


class AllowStagingTests(Shaped):
    """§6.1's allow rows wait on open fact (c) — `D-051`."""

    def test_an_invocation_can_earn_an_allow(self) -> None:
        # The verdict exists and a rule can declare it; what has not
        # shipped is the line-level release.
        judgment = self.judgment("hedged commit -m x")
        self.assertEqual(
            [judged.verdict for judged in judgment.judged], [Verdict.ALLOW]
        )

    def test_the_line_answers_silence_until_the_hedges_ship(self) -> None:
        judgment = self.judgment("hedged commit -m x")
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
