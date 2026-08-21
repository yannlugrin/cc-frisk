"""§3.2's value layer: three-valued matching, and what a role does with it.

Every case here is transcribed from `SPECIFICATIONS.md` §3.2, §3.3 and
§4.2, or from a ruling in `.claude/refs/behavior-corpus.md` — never from
the engine, which does not exist yet. Where a corpus ruling pins a
matcher's answer, the ruling is quoted beside the case, because a case
whose provenance is a memory is a case that can drift.

The corpus's context B declares stubtool's grants over the boundaries
used below: paths under `/tmp` or `.scratch`, the glob
`/home/*/scratch`, the regex `^/mnt/\\w+/build$`, and the operand
pattern `^(?:.*/)?validates?\\.ya?ml$`. Its rulings are verdicts on whole
command lines; what they pin here is the one matcher answer each of them
turns on.
"""

from __future__ import annotations

import os
import unittest
from unittest import mock

from frisk.matchers import (
    NO_CONTEXT,
    MatchContext,
    Outcome,
    Value,
    all_of,
    any_of,
    matching,
    one_of,
    path_matching,
    path_under,
    predicate,
)
from frisk.verdicts import Verdict, fires_at, grant_holds, strongest

#: A line on which an earlier `cd` has poisoned relative paths (§3.2).
AFTER_CD = MatchContext(relative_paths_unproven=True)

#: The operand pattern of the corpus's context B, anchored and
#: dot-escaped exactly as the corpus states it.
VALIDATES = r"^(?:.*/)?validates?\.ya?ml$"


class StringMatcherTests(unittest.TestCase):
    """Matchers that read the raw string (§3.2)."""

    def test_one_of_accepts_a_declared_value(self) -> None:
        self.assertEqual(
            one_of("dry-run", "check").evaluate("dry-run"),
            Outcome.SATISFIED,
        )

    def test_one_of_rejects_anything_else(self) -> None:
        # Corpus: `stubtool apply --mode destroy` → ask.
        self.assertEqual(
            one_of("dry-run", "check").evaluate("destroy"),
            Outcome.UNSATISFIED,
        )

    def test_one_of_is_exact_not_a_prefix(self) -> None:
        self.assertEqual(
            one_of("check").evaluate("checkout"), Outcome.UNSATISFIED
        )

    def test_matching_is_anchored_by_its_author(self) -> None:
        # Corpus context B: the anchoring is called out because an
        # unanchored reading would wrongly pass `validates.yaml.bak`.
        pattern = matching(VALIDATES)
        self.assertEqual(pattern.evaluate("validates.yaml"), Outcome.SATISFIED)
        self.assertEqual(
            pattern.evaluate("run/validates.yaml"), Outcome.SATISFIED
        )
        self.assertEqual(pattern.evaluate("validate.yml"), Outcome.SATISFIED)
        self.assertEqual(
            pattern.evaluate("validates.yaml.bak"), Outcome.UNSATISFIED
        )

    def test_matching_reads_the_string_not_a_path(self) -> None:
        # No resolution happens here: `..` is text like any other.
        self.assertEqual(
            matching(r"^a/\.\./b$").evaluate("a/../b"), Outcome.SATISFIED
        )

    def test_predicate_answers_and_names_itself(self) -> None:
        digits = predicate("only digits", str.isdigit)
        self.assertEqual(digits.evaluate("42"), Outcome.SATISFIED)
        self.assertEqual(digits.evaluate("4x"), Outcome.UNSATISFIED)
        self.assertIn("only digits", digits.describe())

    def test_every_matcher_describes_itself(self) -> None:
        # `describe` is what a citation and `frisk registry` print
        # (§6.2, §9), so an empty one is a matcher nobody can review.
        for matcher in (
            one_of("cat"),
            matching(VALIDATES),
            predicate("only digits", str.isdigit),
            path_under("/tmp"),
            path_matching(r"^/mnt/\w+/build$"),
            any_of(one_of("a"), one_of("b")),
            all_of(one_of("a"), one_of("b")),
        ):
            with self.subTest(matcher=type(matcher).__name__):
                self.assertTrue(matcher.describe().strip())


class DynamicValueTests(unittest.TestCase):
    """An unknown never satisfies a positive condition (§4.2)."""

    def test_no_matcher_family_matches_a_dynamic_value(self) -> None:
        dynamic = Value("$FOO", dynamic=True)
        for matcher in (
            one_of("$FOO"),
            matching(r"^\$FOO$"),
            predicate("anything at all", lambda _: True),
            path_under("/tmp"),
            path_matching(r"^.*$"),
        ):
            with self.subTest(matcher=type(matcher).__name__):
                self.assertEqual(matcher.evaluate(dynamic), Outcome.UNPROVEN)

    def test_dynamism_is_the_token_s_property_not_the_text_s(self) -> None:
        # After tokenization `'$FOO'` is a literal, and a matcher that
        # re-sniffed the text for a dollar sign would misjudge it. The
        # tokenizer decides; the matcher is told.
        self.assertEqual(
            one_of("$FOO").evaluate(Value("$FOO", dynamic=False)),
            Outcome.SATISFIED,
        )


class PathBoundaryTests(unittest.TestCase):
    """`path_under`: resolve, then compare by component (§3.2)."""

    def setUp(self) -> None:
        self.tmp = path_under("/tmp")
        self.scratch = path_under(".scratch")
        # stubtool's `clean` grant: every operand under /tmp or .scratch.
        self.clean = path_under("/tmp", ".scratch")

    def test_a_path_inside_the_boundary(self) -> None:
        # Corpus: `stubtool clean /tmp/x` → silent.
        self.assertEqual(self.tmp.evaluate("/tmp/x"), Outcome.SATISFIED)

    def test_the_boundary_is_inside_itself(self) -> None:
        # Corpus: `STUB_TARGET=/tmp stubtool apply` → silent.
        self.assertEqual(self.tmp.evaluate("/tmp"), Outcome.SATISFIED)

    def test_containment_is_by_component_not_by_prefix(self) -> None:
        # Corpus: `STUB_TARGET=/tmpevil stubtool apply` → ask.
        self.assertEqual(self.tmp.evaluate("/tmpevil"), Outcome.UNSATISFIED)

    def test_traversal_is_resolved_before_comparing(self) -> None:
        # Corpus: `/tmp/../etc` → ask, `/tmp/a/../b` → silent.
        self.assertEqual(self.tmp.evaluate("/tmp/../etc"), Outcome.UNSATISFIED)
        self.assertEqual(self.tmp.evaluate("/tmp/a/../b"), Outcome.SATISFIED)

    def test_traversal_past_the_root_is_still_resolved(self) -> None:
        # Corpus: `STUB_TARGET=/tmp/../../root stubtool apply` → ask.
        self.assertEqual(
            self.tmp.evaluate("/tmp/../../root"), Outcome.UNSATISFIED
        )

    def test_a_relative_boundary_takes_relative_paths(self) -> None:
        # Corpus: `.scratch/build` and `./.scratch/build` → silent,
        # `.scratch/../secrets` → ask, `.scratch/a/../b` → silent.
        self.assertEqual(
            self.scratch.evaluate(".scratch/build"), Outcome.SATISFIED
        )
        self.assertEqual(
            self.scratch.evaluate("./.scratch/build"), Outcome.SATISFIED
        )
        self.assertEqual(
            self.scratch.evaluate(".scratch/../secrets"),
            Outcome.UNSATISFIED,
        )
        self.assertEqual(
            self.scratch.evaluate(".scratch/a/../b"), Outcome.SATISFIED
        )

    def test_relative_value_against_absolute_boundary_is_unproven(
        self,
    ) -> None:
        # Corpus: `STUB_TARGET=tmp/x stubtool apply` → ask. No
        # resolution base is invented, so the mismatch is unproven
        # rather than a plain miss (§3.2).
        self.assertEqual(self.tmp.evaluate("tmp/x"), Outcome.UNPROVEN)

    def test_absolute_value_against_relative_boundary_is_unproven(
        self,
    ) -> None:
        self.assertEqual(
            self.scratch.evaluate("/etc/passwd"), Outcome.UNPROVEN
        )

    def test_a_miss_and_an_unproven_boundary_combine_to_unproven(
        self,
    ) -> None:
        # Corpus: `stubtool clean /etc/passwd` → ask. Absolute against
        # /tmp is a clean miss; absolute against .scratch is unproven;
        # the boundary set answers with the stricter of the two.
        self.assertEqual(self.clean.evaluate("/etc/passwd"), Outcome.UNPROVEN)

    def test_a_mixed_form_boundary_set_never_answers_no(self) -> None:
        # The consequence of the rule above, pinned deliberately rather
        # than left to be rediscovered (D-035): with one absolute and
        # one relative boundary, an absolute value is cross-form to the
        # second and a relative value to the first, so this matcher can
        # answer satisfied or unproven and nothing else. It costs a
        # prompt on a deny rule and nothing at all on a grant, which is
        # the only place the corpus uses such a set.
        for value in ("/etc/passwd", "elsewhere/x", "/tmp/../etc"):
            with self.subTest(value=value):
                self.assertNotEqual(
                    self.clean.evaluate(value), Outcome.UNSATISFIED
                )

    def test_a_single_form_boundary_can_answer_no(self) -> None:
        # And the same value against a boundary set it shares a form
        # with is a clean miss, so "unproven" above is the cross-form
        # rule at work rather than a matcher that cannot say no.
        self.assertEqual(self.tmp.evaluate("/etc/passwd"), Outcome.UNSATISFIED)

    def test_one_bad_operand_does_not_borrow_a_good_one_s_answer(
        self,
    ) -> None:
        # Corpus: `stubtool clean /tmp/x /etc/passwd` → ask. The
        # quantifier is what combines them (see the operand tests);
        # each value is judged alone here.
        self.assertEqual(self.clean.evaluate("/tmp/x"), Outcome.SATISFIED)
        self.assertEqual(self.clean.evaluate("/etc/passwd"), Outcome.UNPROVEN)


class GlobBoundaryTests(unittest.TestCase):
    """A boundary may carry wildcards, and they never cross `/`."""

    def setUp(self) -> None:
        self.scratch = path_under("/home/*/scratch")

    def test_the_wildcard_matches_one_component(self) -> None:
        # Corpus: `STUB_TARGET=/home/yann/scratch stubtool apply`
        # → silent.
        self.assertEqual(
            self.scratch.evaluate("/home/yann/scratch"), Outcome.SATISFIED
        )

    def test_a_glob_boundary_still_contains_what_is_under_it(self) -> None:
        # Corpus: `/home/yann/scratch/build` → silent.
        self.assertEqual(
            self.scratch.evaluate("/home/yann/scratch/build"),
            Outcome.SATISFIED,
        )

    def test_the_wildcard_does_not_cross_a_separator(self) -> None:
        # Corpus: `/home/a/b/scratch` → ask.
        self.assertEqual(
            self.scratch.evaluate("/home/a/b/scratch"),
            Outcome.UNSATISFIED,
        )

    def test_a_sibling_directory_is_outside(self) -> None:
        # Corpus: `/home/yann/other` → ask.
        self.assertEqual(
            self.scratch.evaluate("/home/yann/other"), Outcome.UNSATISFIED
        )


class PathPatternTests(unittest.TestCase):
    """`path_matching` constrains the resolved path itself."""

    def setUp(self) -> None:
        self.build = path_matching(r"^/mnt/\w+/build$")

    def test_the_pattern_matches_the_whole_path(self) -> None:
        # Corpus: `/mnt/data/build` → silent.
        self.assertEqual(
            self.build.evaluate("/mnt/data/build"), Outcome.SATISFIED
        )

    def test_it_is_not_a_boundary(self) -> None:
        # Corpus: `/mnt/data/builds` → ask, `/mnt/data/build/sub` → ask.
        # This is the deliberate difference from `path_under`: what is
        # *under* a matched path is not itself matched.
        self.assertEqual(
            self.build.evaluate("/mnt/data/builds"), Outcome.UNSATISFIED
        )
        self.assertEqual(
            self.build.evaluate("/mnt/data/build/sub"),
            Outcome.UNSATISFIED,
        )

    def test_resolution_still_happens_first(self) -> None:
        # Corpus: `/mnt/data/build/../../../etc` → ask.
        self.assertEqual(
            self.build.evaluate("/mnt/data/build/../../../etc"),
            Outcome.UNSATISFIED,
        )


class HomeExpansionTests(unittest.TestCase):
    """`~` is resolved before comparing, from the environment (§3.2)."""

    def test_home_is_expanded_in_the_value(self) -> None:
        with mock.patch.dict(os.environ, {"HOME": "/home/me"}):
            self.assertEqual(
                path_under("/home/me").evaluate("~/scratch"),
                Outcome.SATISFIED,
            )

    def test_home_is_expanded_in_the_boundary(self) -> None:
        with mock.patch.dict(os.environ, {"HOME": "/home/me"}):
            self.assertEqual(
                path_under("~/scratch").evaluate("/home/me/scratch/x"),
                Outcome.SATISFIED,
            )

    def test_an_expanded_home_is_still_judged_on_its_result(self) -> None:
        # Corpus: `STUB_TARGET=~/tmp stubtool apply` → ask.
        with mock.patch.dict(os.environ, {"HOME": "/home/me"}):
            self.assertEqual(
                path_under("/tmp").evaluate("~/tmp"), Outcome.UNSATISFIED
            )

    def test_another_user_s_home_is_unproven(self) -> None:
        # Resolving `~someone` means reading the password database,
        # which §4.5 forbids: the engine touches no filesystem.
        with mock.patch.dict(os.environ, {"HOME": "/home/me"}):
            self.assertEqual(
                path_under("/home").evaluate("~other/x"), Outcome.UNPROVEN
            )

    def test_an_unresolvable_home_is_unproven(self) -> None:
        environment = dict(os.environ)
        environment.pop("HOME", None)
        with mock.patch.dict(os.environ, environment, clear=True):
            self.assertEqual(
                path_under("/home/me").evaluate("~/x"), Outcome.UNPROVEN
            )


class DirectoryChangeTests(unittest.TestCase):
    """A `cd` earlier on the line poisons relative *paths* (§3.2)."""

    def test_relative_paths_become_unproven(self) -> None:
        self.assertEqual(
            path_under(".scratch").evaluate(".scratch/x", AFTER_CD),
            Outcome.UNPROVEN,
        )

    def test_absolute_paths_are_untouched(self) -> None:
        self.assertEqual(
            path_under("/tmp").evaluate("/tmp/x", AFTER_CD),
            Outcome.SATISFIED,
        )

    def test_pattern_matchers_are_untouched(self) -> None:
        # Corpus: `cd /srv && stubtool run/validates.yaml` → silent.
        # The grant it satisfies is a pattern over the raw operand, and
        # the poisoning is path-matcher-only; reading it wider would
        # turn this silent ruling into a prompt.
        self.assertEqual(
            matching(VALIDATES).evaluate("run/validates.yaml", AFTER_CD),
            Outcome.SATISFIED,
        )

    def test_predicate_matchers_are_untouched(self) -> None:
        ends_in_yaml = predicate(
            "ends in .yaml", lambda v: v.endswith(".yaml")
        )
        self.assertEqual(
            ends_in_yaml.evaluate("run/validates.yaml", AFTER_CD),
            Outcome.SATISFIED,
        )


class CombinatorTests(unittest.TestCase):
    """`any_of` and `all_of` over three values, not two."""

    def setUp(self) -> None:
        self.yes = one_of("a")
        self.no = one_of("b")
        # Relative against an absolute boundary: unproven by §3.2.
        self.unproven = path_under("/tmp")

    def test_any_of_is_satisfied_by_one(self) -> None:
        self.assertEqual(
            any_of(self.no, self.yes).evaluate("a"), Outcome.SATISFIED
        )

    def test_any_of_prefers_satisfied_over_unproven(self) -> None:
        self.assertEqual(
            any_of(self.unproven, one_of("tmp/x")).evaluate("tmp/x"),
            Outcome.SATISFIED,
        )

    def test_any_of_reports_unproven_when_nothing_was_satisfied(
        self,
    ) -> None:
        self.assertEqual(
            any_of(self.unproven, self.no).evaluate("tmp/x"),
            Outcome.UNPROVEN,
        )

    def test_any_of_is_unsatisfied_only_when_every_answer_was(
        self,
    ) -> None:
        self.assertEqual(
            any_of(one_of("a"), one_of("b")).evaluate("c"),
            Outcome.UNSATISFIED,
        )

    def test_all_of_needs_every_answer(self) -> None:
        self.assertEqual(
            all_of(one_of("a"), matching("^a$")).evaluate("a"),
            Outcome.SATISFIED,
        )

    def test_all_of_is_unsatisfied_as_soon_as_one_is(self) -> None:
        # A clean miss is a decision; it outranks an unknown, so this
        # is unsatisfied rather than unproven.
        self.assertEqual(
            all_of(self.unproven, one_of("nothing")).evaluate("tmp/x"),
            Outcome.UNSATISFIED,
        )

    def test_all_of_is_unproven_when_only_unknowns_remain(self) -> None:
        self.assertEqual(
            all_of(self.unproven, one_of("tmp/x")).evaluate("tmp/x"),
            Outcome.UNPROVEN,
        )


class VerdictRankingTests(unittest.TestCase):
    """Deny over ask over allow over silence (§3.2)."""

    def test_the_strongest_of_several(self) -> None:
        self.assertEqual(
            strongest([Verdict.SILENT, Verdict.ASK, Verdict.ALLOW]),
            Verdict.ASK,
        )
        self.assertEqual(strongest([Verdict.ASK, Verdict.DENY]), Verdict.DENY)
        self.assertEqual(
            strongest([Verdict.SILENT, Verdict.ALLOW]), Verdict.ALLOW
        )

    def test_the_ranking_does_not_depend_on_order(self) -> None:
        self.assertEqual(
            strongest([Verdict.DENY, Verdict.ASK]),
            strongest([Verdict.ASK, Verdict.DENY]),
        )

    def test_nothing_at_all_is_silence(self) -> None:
        self.assertEqual(strongest([]), Verdict.SILENT)


class ThreeValuedRoleTests(unittest.TestCase):
    """Unproven moves stricter *by role* (§3.2, §4.2)."""

    def test_a_satisfied_condition_fires_the_rule_as_declared(
        self,
    ) -> None:
        for verdict in (Verdict.DENY, Verdict.ASK, Verdict.ALLOW):
            with self.subTest(verdict=verdict):
                self.assertEqual(fires_at(verdict, Outcome.SATISFIED), verdict)

    def test_an_unsatisfied_condition_fires_nothing(self) -> None:
        for verdict in (Verdict.DENY, Verdict.ASK, Verdict.ALLOW):
            with self.subTest(verdict=verdict):
                self.assertIsNone(fires_at(verdict, Outcome.UNSATISFIED))

    def test_an_unproven_deny_fires_at_ask_strength(self) -> None:
        # The gated value cannot be proven present, so no deny; it
        # cannot be ruled out either, so never silence.
        self.assertEqual(fires_at(Verdict.DENY, Outcome.UNPROVEN), Verdict.ASK)

    def test_an_unproven_ask_still_asks(self) -> None:
        self.assertEqual(fires_at(Verdict.ASK, Outcome.UNPROVEN), Verdict.ASK)

    def test_an_unproven_allow_fires_nothing(self) -> None:
        # An unknown never weakens a boundary (§4.2).
        self.assertIsNone(fires_at(Verdict.ALLOW, Outcome.UNPROVEN))

    def test_only_a_satisfied_condition_releases_a_grant(self) -> None:
        self.assertTrue(grant_holds(Outcome.SATISFIED))
        self.assertFalse(grant_holds(Outcome.UNSATISFIED))
        self.assertFalse(grant_holds(Outcome.UNPROVEN))


class ContextDefaultTests(unittest.TestCase):
    """The no-line-around-it context is the unpoisoned one."""

    def test_the_default_context_poisons_nothing(self) -> None:
        self.assertFalse(NO_CONTEXT.relative_paths_unproven)
