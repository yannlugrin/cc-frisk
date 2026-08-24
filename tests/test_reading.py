"""§4.1 and §4.2: a command string, and the invocations it really holds.

Every case here is transcribed from `SPECIFICATIONS.md` §4.1, §4.2 and
§3.3, or from a ruling in `.claude/refs/behavior-corpus.md` — never from
the engine, which does not read a line yet. Where a corpus ruling turns
on a reading, the ruling is quoted beside the case: this step produces
no verdicts, so what a ruling pins here is the *shape* its verdict
depends on, and a case whose provenance is a memory is a case that can
drift.

Three boundaries are deliberate, and a case asserting the interim
behaviour on the far side of one would be a case a later step has to
undo. What lives behind another program — a wrapper's command, a
shell's `-c` payload, an interpreter's file operand — is `010`.
Substitutions, subshells and heredocs are `011`. Handoffs and
redirections are `012`. Reading stops at the segment boundary and hands
each segment's command word to the registry; nothing here looks through
one.

The fourth boundary is the verdict itself. Reading reports what it
found and what it could not establish (`Invocation.unproven`); what an
unproven invocation *costs* is §3.2's business at `009`, where a gated
tool's grants are what the flag releases or withholds.
"""

from __future__ import annotations

import textwrap
import unittest

from frisk.declare import (
    any_flag,
    ask,
    bare,
    deny,
    every_operand,
    grant,
    may_take_value,
    path_under,
    silent,
    takes_value,
    tool,
)
from frisk.matchers import Value
from frisk.reading import Assigned, Doubt, Flag, Invocation, Reading, read
from frisk.registry import Registry, collecting
from tests.corpus import context_b


def policy() -> Registry:
    """Context B, plus the shapes §4.2 needs that no ruling carries.

    The engine's default layers are on, because two of §4.1's rules are
    about them: a wrapper's name is no signal for the raw scan, and the
    walk through one is `010`'s, not this step's.

    `git` is the corpus's context A reduced to what reading needs — the
    declared global options `git -C dir push` turns on, and one rule so
    the name is *speaking* (§3.2). Its policy is context A's business at
    `009`; nothing here asserts a git verdict.
    """
    with collecting() as declared:
        context_b.declare()
        tool(
            "git",
            options=[takes_value("-C", "--git-dir", "--exec-path")],
            rules=[
                deny(
                    "push",
                    when=any_flag("-f", "--force"),
                    reason="A forced push rewrites remote history.",
                    label="forced push",
                ),
            ],
        )
        # §4.2's value-optional flag, in the spelling the section uses:
        # "some hand-rolled CLIs accept both `--argument custom --check`
        # and `--argument --check`". `--plain` is the same arity with no
        # declared default, which is the unprovable half of `D-039`.
        tool(
            "stubopt",
            default=ask(reason="stubopt changes state unless proven local."),
            flags=[
                bare("--check"),
                may_take_value("--argument", default="check"),
                may_take_value("--plain"),
            ],
            grants=[
                grant(
                    when=any_flag("--check"),
                    reason="A local question: nothing is applied.",
                ),
            ],
        )
        # §4.2's path declaration, and the basename declaration it is
        # more specific than.
        tool(
            "tools/deploy.py",
            default=ask(reason="This project's deploy script deploys."),
            grants=[
                grant(
                    when=every_operand(path_under("/tmp")),
                    reason="A scratch target is not production.",
                ),
            ],
        )
        tool(
            "deploy.py",
            default=ask(reason="A deploy script anywhere deploys."),
        )
        # Gated by a grant, carrying no rule and no default verdict:
        # the one shape that separates `D-047`'s grants limb from
        # `rule_bearing`. Every other gated tool in this fixture also
        # carries a rule or a non-silent default, so none of them can
        # tell a narrow scan from a speaking one.
        tool(
            "stubgrant",
            grants=[
                grant(
                    when=every_operand(path_under("/tmp")),
                    reason="A scratch target is not production.",
                ),
            ],
        )
        # Registered, silent by declaration, carrying nothing else: the
        # case that separates *registered* from *speaking* (§3.2).
        tool("stubmute", default=silent(reason="Nothing to say."))
    return declared.registry()


#: Composed once: every case reads against the same boundary, and
#: composition is `007`'s subject, not this file's.
POLICY = policy()


class Reads(unittest.TestCase):
    """What every case below needs to say what it found."""

    def read(self, command_line: str) -> Reading:
        return read(command_line, POLICY)

    def one(self, command_line: str) -> Invocation:
        """The single invocation this line holds."""
        reading = self.read(command_line)
        self.assertFalse(reading.unparseable, command_line)
        self.assertEqual(len(reading.invocations), 1, reading)
        return reading.invocations[0]

    def operands(self, invocation: Invocation) -> list[str]:
        return [value.text for value in invocation.operands]

    def flags(self, invocation: Invocation) -> dict[str, str | None]:
        return self.valued(invocation.flags)

    def options(self, invocation: Invocation) -> dict[str, str | None]:
        return self.valued(invocation.options)

    def assignments(self, invocation: Invocation) -> dict[str, str]:
        return {
            assigned.name: assigned.value.text
            for assigned in invocation.assignments
        }

    def valued(self, flags: tuple[Flag, ...]) -> dict[str, str | None]:
        return {
            flag.name: None if flag.value is None else flag.value.text
            for flag in flags
        }


class TokenizationTests(Reads):
    """Quoting is resolved by tokenization, never by raw matching (§4.1)."""

    def test_a_flag_inside_a_quoted_value_is_not_a_flag(self) -> None:
        # §4.1's first example: `git commit -m 'fix the --amend bug'` is
        # not an amend. Raw matching is unsound in this direction.
        invocation = self.one("git commit -m 'fix the --amend bug'")
        self.assertEqual(self.operands(invocation), ["commit"])
        self.assertEqual(self.flags(invocation), {"-m": "fix the --amend bug"})

    def test_double_quotes_resolve_the_same_way(self) -> None:
        invocation = self.one('git commit -m "fix the --amend bug"')
        self.assertEqual(self.flags(invocation), {"-m": "fix the --amend bug"})

    def test_quotes_are_removed_from_the_value_they_carried(self) -> None:
        # Corpus: `stubtool --syntax-check 'my file.yml'` — the operand
        # the engine judges is the file name, not the quoted spelling.
        invocation = self.one("stubtool --syntax-check 'my file.yml'")
        self.assertEqual(self.operands(invocation), ["my file.yml"])

    def test_quotes_join_what_whitespace_would_have_split(self) -> None:
        invocation = self.one("stubtool clean '/tmp/a b'")
        self.assertEqual(self.operands(invocation), ["clean", "/tmp/a b"])

    def test_adjacent_quoted_runs_are_one_token(self) -> None:
        invocation = self.one("""stubtool clean '/tmp/a'"b"c""")
        self.assertEqual(self.operands(invocation), ["clean", "/tmp/abc"])

    def test_a_backslash_escapes_the_character_after_it(self) -> None:
        invocation = self.one(r"stubtool clean /tmp/a\ b")
        self.assertEqual(self.operands(invocation), ["clean", "/tmp/a b"])

    def test_a_backslash_inside_single_quotes_is_data(self) -> None:
        # Single quotes quote everything, the backslash included.
        invocation = self.one(r"stubtool clean '/tmp/a\ b'")
        self.assertEqual(self.operands(invocation), ["clean", r"/tmp/a\ b"])

    def test_an_empty_quoted_token_is_an_operand(self) -> None:
        # It is a token the shell passes; dropping it would renumber
        # every operand after it.
        invocation = self.one("stubtool clean ''")
        self.assertEqual(self.operands(invocation), ["clean", ""])


class SplittingTests(Reads):
    """Compound commands split at every separator (§4.1)."""

    def test_and_splits(self) -> None:
        # Corpus: `stubtool --syntax-check a.yml && stubtool deploy.yml`
        # → ask, which no reading of it as one invocation can reach.
        reading = self.read("stubtool --syntax-check a.yml && stubtool b.yml")
        self.assertEqual(len(reading.invocations), 2)
        self.assertEqual(self.operands(reading.invocations[0]), ["a.yml"])
        self.assertEqual(self.operands(reading.invocations[1]), ["b.yml"])

    def test_every_separator_splits(self) -> None:
        for separator in ("&&", "||", ";", "|", "|&", "&"):
            with self.subTest(separator=separator):
                reading = self.read(
                    f"stubtool a.yml {separator} stubtool b.yml"
                )
                self.assertEqual(len(reading.invocations), 2, separator)

    def test_a_newline_splits(self) -> None:
        # §4.1: "The newline is load-bearing, not an afterthought" —
        # `git status\ngit push --force` read as one invocation lets no
        # push rule fire.
        reading = self.read("git status\ngit push --force")
        self.assertEqual(len(reading.invocations), 2)
        self.assertEqual(self.operands(reading.invocations[0]), ["status"])
        self.assertEqual(self.operands(reading.invocations[1]), ["push"])
        self.assertEqual(self.flags(reading.invocations[1]), {"--force": None})

    def test_runs_of_newlines_and_blank_lines_split_once(self) -> None:
        # Corpus, a multiline command with a blank run between the two
        # lines → ask, so both invocations must be found and no empty
        # one between them.
        reading = self.read(
            textwrap.dedent(
                """\
                stubtool --syntax-check a.yml


                stubtool deploy.yml
                """
            )
        )
        self.assertEqual(len(reading.invocations), 2)
        self.assertEqual(
            [invocation.name for invocation in reading.invocations],
            ["stubtool", "stubtool"],
        )

    def test_a_separator_inside_quotes_is_data(self) -> None:
        # Corpus: `echo "one\nstubtool deploy.yml"` → silent. One
        # argument, and no stubtool invocation anywhere on the line.
        reading = self.read('echo "one\nstubtool deploy.yml"')
        self.assertEqual(len(reading.invocations), 1)
        self.assertEqual(reading.invocations[0].name, "echo")
        self.assertEqual(
            self.operands(reading.invocations[0]),
            ["one\nstubtool deploy.yml"],
        )

    def test_quoted_shell_separators_are_data_too(self) -> None:
        reading = self.read("echo 'a && b ; c | d'")
        self.assertEqual(len(reading.invocations), 1)
        self.assertEqual(
            self.operands(reading.invocations[0]), ["a && b ; c | d"]
        )

    def test_a_trailing_separator_leaves_no_empty_invocation(self) -> None:
        reading = self.read("git status;")
        self.assertEqual(len(reading.invocations), 1)

    def test_a_line_of_only_separators_holds_nothing(self) -> None:
        # Nothing to run is not a failure to parse: §4.1's fallback is
        # for a line the engine could not read, and answering silence
        # here through the *unparseable* door would put every empty
        # segment through the raw scan.
        reading = self.read("  ;  &&  \n\n ")
        self.assertEqual(reading.invocations, ())
        self.assertFalse(reading.unparseable)

    def test_the_empty_line_holds_nothing(self) -> None:
        reading = self.read("")
        self.assertEqual(reading.invocations, ())
        self.assertFalse(reading.unparseable)

    def test_several_separators_split_into_several_invocations(self) -> None:
        reading = self.read("a && b || c ; d | e & f")
        self.assertEqual(
            [invocation.name for invocation in reading.invocations],
            ["a", "b", "c", "d", "e", "f"],
        )


class ContinuationTests(Reads):
    """Backslash-line continuations are joined before splitting (§4.1)."""

    def test_a_continuation_keeps_the_flag_on_its_command(self) -> None:
        # Corpus, a multiline command: `stubtool deploy.yml \` then
        # `--syntax-check` → silent. Split rather than joined, the flag
        # would land on an invocation of its own.
        invocation = self.one("stubtool deploy.yml \\\n--syntax-check")
        self.assertEqual(self.operands(invocation), ["deploy.yml"])
        self.assertEqual(self.flags(invocation), {"--syntax-check": None})

    def test_indentation_after_a_continuation_is_whitespace(self) -> None:
        # Corpus: the same ruling with the continued line indented.
        invocation = self.one(
            "stubtool deploy.yml \\\n         --syntax-check"
        )
        self.assertEqual(self.flags(invocation), {"--syntax-check": None})

    def test_a_continuation_after_the_command_word(self) -> None:
        # Corpus: `stubtool \` then `--syntax-check site.yml` → silent.
        invocation = self.one("stubtool \\\n--syntax-check site.yml")
        self.assertEqual(invocation.name, "stubtool")
        self.assertEqual(self.operands(invocation), ["site.yml"])

    def test_a_continuation_hides_a_flag_from_a_raw_reading(self) -> None:
        # §4.1: otherwise `git push \` then `--force` hides the flag
        # inside a mangled operand.
        invocation = self.one("git push \\\n--force")
        self.assertEqual(self.operands(invocation), ["push"])
        self.assertEqual(self.flags(invocation), {"--force": None})

    def test_a_continuation_inside_single_quotes_is_data(self) -> None:
        # Single quotes quote the newline too, so this is one operand
        # holding a backslash and a newline, not a joined line.
        invocation = self.one("echo 'a \\\nb'")
        self.assertEqual(self.operands(invocation), ["a \\\nb"])

    def test_a_backslash_at_the_very_end_ends_the_line(self) -> None:
        invocation = self.one("git status \\\n")
        self.assertEqual(self.operands(invocation), ["status"])


class CommentTests(Reads):
    """Comments are not part of the command (§4.1)."""

    def test_a_comment_carries_no_flag(self) -> None:
        # Corpus: `stubtool deploy.yml  # --syntax-check next time` →
        # ask. The grant must not be satisfied by a comment.
        invocation = self.one(
            "stubtool deploy.yml  # --syntax-check next time"
        )
        self.assertEqual(self.operands(invocation), ["deploy.yml"])
        self.assertEqual(self.flags(invocation), {})

    def test_a_comment_runs_to_the_end_of_its_line_only(self) -> None:
        reading = self.read("git status # looking\ngit push --force")
        self.assertEqual(len(reading.invocations), 2)
        self.assertEqual(self.flags(reading.invocations[1]), {"--force": None})

    def test_a_whole_line_comment_holds_no_invocation(self) -> None:
        reading = self.read("# stubtool deploy.yml\ngit status")
        self.assertEqual(len(reading.invocations), 1)
        self.assertEqual(reading.invocations[0].name, "git")

    def test_a_hash_inside_a_word_is_not_a_comment(self) -> None:
        # `#` opens a comment only where a word begins; anywhere else it
        # is an ordinary character, and dropping the rest of the line
        # would lose real operands.
        invocation = self.one("stubtool clean /tmp/a#b")
        self.assertEqual(self.operands(invocation), ["clean", "/tmp/a#b"])

    def test_a_quoted_hash_is_not_a_comment(self) -> None:
        invocation = self.one("echo '# not a comment'")
        self.assertEqual(self.operands(invocation), ["# not a comment"])


class UnparseableLineTests(Reads):
    """A line that cannot be parsed is unproven, never silence (§4.1)."""

    def test_an_unbalanced_quote_makes_the_line_unparseable(self) -> None:
        # Corpus: `stubtool 'unbalanced` → ask.
        reading = self.read("stubtool 'unbalanced")
        self.assertTrue(reading.unparseable)

    def test_an_unparseable_line_yields_no_invocations(self) -> None:
        # Half a reading is worse than none: it would let a grant hold
        # on tokens the engine never finished reading.
        self.assertEqual(self.read("stubtool 'unbalanced").invocations, ())

    def test_the_scan_names_a_speaking_tool_on_the_raw_line(self) -> None:
        reading = self.read("stubtool 'unbalanced")
        self.assertEqual(reading.speaking, ("stubtool",))

    def test_the_scan_stays_silent_where_nothing_speaks(self) -> None:
        # Corpus: `echo 'unbalanced` → silent.
        reading = self.read("echo 'unbalanced")
        self.assertTrue(reading.unparseable)
        self.assertEqual(reading.speaking, ())

    def test_the_scan_compares_by_basename(self) -> None:
        # §4.1: "so a path spelling like `/usr/bin/git` does not evade
        # the scan".
        reading = self.read("/usr/bin/git status 'unbalanced")
        self.assertEqual(reading.speaking, ("git",))

    def test_a_grants_only_tool_speaks(self) -> None:
        # `D-047`'s grants limb, and the only case that can prove it:
        # stubgrant carries a grant and nothing else, so a scan asking
        # `rule_bearing` answers an unparseable line naming it with
        # silence — which is what §4.1's gloss exists to prevent, and
        # what an unparseable line naming `ansible-playbook` would get.
        reading = self.read("stubgrant 'unbalanced")
        self.assertEqual(reading.speaking, ("stubgrant",))

    def test_a_default_verdict_alone_speaks(self) -> None:
        # `D-047` again: stubalways has no rules and no grants at all.
        reading = self.read("stubalways 'unbalanced")
        self.assertEqual(reading.speaking, ("stubalways",))

    def test_a_registered_silent_tool_does_not_speak(self) -> None:
        reading = self.read("stubmute 'unbalanced")
        self.assertEqual(reading.speaking, ())

    def test_a_wrapper_name_is_no_signal(self) -> None:
        # §4.1: wrapper and baseline-read names "appear on too many
        # ordinary lines, and scanning for them would make the fallback
        # fire constantly".
        reading = self.read("sudo 'unbalanced")
        self.assertEqual(reading.speaking, ())

    def test_the_scan_matches_whole_words_only(self) -> None:
        # §4.2's recognition rule holds for the scan too: `git-crypt` is
        # not git, and a substring match would gate it.
        reading = self.read("git-crypt unlock 'unbalanced")
        self.assertEqual(reading.speaking, ())

    def test_the_scan_ignores_a_name_inside_a_larger_token(self) -> None:
        reading = self.read("mystubtool deploy 'unbalanced")
        self.assertEqual(reading.speaking, ())

    def test_the_scan_names_every_speaking_tool_it_finds(self) -> None:
        reading = self.read("git status && stubtool wipe 'unbalanced")
        self.assertEqual(reading.speaking, ("git", "stubtool"))

    def test_the_scan_reads_a_name_used_as_an_ordinary_word(self) -> None:
        # The accepted cost of a raw scan, and the reason it fires only
        # on a line nothing could parse: `ls ../stubtool` is silent
        # (corpus) on a parsed line, where §4.3 forbids scanning — here
        # there is no parse to trust, and §3.3 sends the doubt stricter.
        reading = self.read("ls ../stubtool 'unbalanced")
        self.assertEqual(reading.speaking, ("stubtool",))

    def test_a_parsed_line_carries_no_scan(self) -> None:
        # The scan is the *fallback*: it fires where there is no parse
        # to trust. On a parsed line §4.3 forbids scanning outright, so
        # a reading that ran it anyway would hand `009` a signal it must
        # remember never to read.
        reading = self.read("git status && stubtool wipe")
        self.assertFalse(reading.unparseable)
        self.assertEqual(reading.speaking, ())

    def test_the_scan_names_each_tool_once_in_a_stable_order(self) -> None:
        # It is printed, and `009` will cite it: a name repeated once
        # per mention, or ordered by where it happened to appear, is a
        # different report for the same line.
        reading = self.read("git status && git push 'unbalanced")
        self.assertEqual(reading.speaking, ("git",))

    def test_an_alias_is_the_same_name_to_the_scan(self) -> None:
        reading = self.read("stub2 wipe 'unbalanced")
        self.assertEqual(reading.speaking, ("stubtool",))


class AssignmentTests(Reads):
    """Leading assignments bind as conditions in their own right (§4.2)."""

    def test_a_leading_assignment_binds_to_the_command(self) -> None:
        # Corpus: `STUB_QUIET=1 stubtool --syntax-check site.yml` →
        # silent, so the command word is stubtool, not the assignment.
        invocation = self.one("STUB_QUIET=1 stubtool --syntax-check site.yml")
        self.assertEqual(invocation.name, "stubtool")
        self.assertEqual(self.assignments(invocation), {"STUB_QUIET": "1"})

    def test_several_assignments_all_bind(self) -> None:
        # Corpus: `STUB_QUIET=1 STUB_TARGET=/tmp/x stubtool apply` →
        # silent, which needs both to be seen.
        invocation = self.one("STUB_QUIET=1 STUB_TARGET=/tmp/x stubtool apply")
        self.assertEqual(
            self.assignments(invocation),
            {"STUB_QUIET": "1", "STUB_TARGET": "/tmp/x"},
        )
        self.assertEqual(self.operands(invocation), ["apply"])

    def test_the_append_form_is_an_assignment(self) -> None:
        # Corpus: `STUB_DANGER+=1 stubtool --syntax-check site.yml` →
        # deny, and `STUB_QUIET+=1 …` → silent: both are read under the
        # bare name.
        invocation = self.one("STUB_DANGER+=1 stubtool --syntax-check a.yml")
        self.assertEqual(self.assignments(invocation), {"STUB_DANGER": "1"})

    def test_a_quoted_value_is_resolved(self) -> None:
        invocation = self.one('STUB_TARGET="/tmp/a b" stubtool apply')
        self.assertEqual(
            self.assignments(invocation), {"STUB_TARGET": "/tmp/a b"}
        )

    def test_a_lower_case_name_is_an_assignment_too(self) -> None:
        # §4.2: "names are the shell's, so lower-case names are
        # assignments too". Corpus: `stub_danger=1 stubtool
        # --syntax-check site.yml` → ask — an assignment nothing
        # accounts for, which it could not be if it were read as a
        # command word.
        invocation = self.one("stub_danger=1 stubtool --syntax-check a.yml")
        self.assertEqual(invocation.name, "stubtool")
        self.assertEqual(self.assignments(invocation), {"stub_danger": "1"})

    def test_matching_is_case_sensitive(self) -> None:
        # The same ruling from the other side: the accounted name is
        # `STUB_DANGER`, and `stub_danger` is a different variable.
        invocation = self.one("stub_danger=1 stubtool a.yml")
        self.assertNotIn("STUB_DANGER", self.assignments(invocation))

    def test_an_assignment_after_the_command_word_is_an_operand(self) -> None:
        # Corpus: `stubtool --syntax-check STUB_DANGER=1` → silent. Read
        # as environment it would fire the deny rule.
        invocation = self.one("stubtool --syntax-check STUB_DANGER=1")
        self.assertEqual(self.assignments(invocation), {})
        self.assertEqual(self.operands(invocation), ["STUB_DANGER=1"])

    def test_an_assignment_with_no_command_runs_nothing(self) -> None:
        self.assertEqual(self.read("STUB_QUIET=1").invocations, ())

    def test_a_token_that_is_not_a_name_is_the_command_word(self) -> None:
        # `=x` and `1FOO=x` are not shell names, so they are not
        # assignments; reading them as one would lose the command.
        for line in ("=x stubtool a.yml", "1FOO=x stubtool a.yml"):
            with self.subTest(line=line):
                invocation = self.one(line)
                self.assertNotEqual(invocation.name, "stubtool")
                self.assertEqual(self.assignments(invocation), {})

    def test_an_exotic_assignment_form_lands_stricter(self) -> None:
        # §4.2: "Exotic assignment forms (array syntax and other
        # shell-specific shapes) may gain full modeling later; until
        # then they must land in the stricter direction, never be
        # misread as something harmless."
        #
        # The naive reading is the harmless one and it is badly wrong:
        # `FOO=(a` binds as an ordinary assignment, `b)` becomes the
        # command word, and the tool that is actually being run drops to
        # an operand of a command nobody wrote. Unparseable is the
        # honest answer — the *segment structure* was not read — and
        # §4.1's scan then does its job.
        reading = self.read("FOO=(a b) stubtool apply")
        self.assertTrue(reading.unparseable)
        self.assertEqual(reading.speaking, ("stubtool",))

    def test_an_assignment_carrying_a_variable_is_dynamic(self) -> None:
        # §4.2: a value carrying `$FOO` cannot prove a grant condition.
        invocation = self.one("STUB_TARGET=$HOME/x stubtool apply")
        self.assertEqual(
            invocation.assignments,
            (Assigned("STUB_TARGET", Value("$HOME/x", dynamic=True)),),
        )


class OptionTests(Reads):
    """Options preceding a subcommand are recognized and stripped (§4.2)."""

    def test_a_declared_option_leaves_the_subcommand_first(self) -> None:
        # Corpus: `git -C /srv/repo push` → ask. §4.2: undeclared, it
        # "parses as operands `dir push` and no push rule matches".
        invocation = self.one("git -C /srv/repo push")
        self.assertEqual(self.operands(invocation), ["push"])

    def test_the_option_value_is_remembered(self) -> None:
        # §4.2: rule and grant conditions "must be able to constrain
        # the latter like any flag value" — "pushing is fine only for
        # repositories under this directory" is a rule on `-C`'s value.
        invocation = self.one("git -C /srv/repo push")
        self.assertEqual(self.options(invocation), {"-C": "/srv/repo"})

    def test_an_attached_option_value_is_read(self) -> None:
        # Corpus: `git --git-dir=.git commit --amend` → ask.
        invocation = self.one("git --git-dir=.git commit --amend")
        self.assertEqual(self.options(invocation), {"--git-dir": ".git"})
        self.assertEqual(self.operands(invocation), ["commit"])
        self.assertEqual(self.flags(invocation), {"--amend": None})

    def test_options_and_flags_are_separate_namespaces(self) -> None:
        # The entry keeps two mappings; a reading that merged them would
        # let a rule on `-C`'s value be satisfied by a flag of the same
        # name (§4.2, `Entry.options`).
        invocation = self.one("git -C /srv push --force")
        self.assertEqual(self.options(invocation), {"-C": "/srv"})
        self.assertEqual(self.flags(invocation), {"--force": None})

    def test_an_undeclared_leading_option_is_presumed_bare(self) -> None:
        # Stricter, and it keeps the subcommand where rules expect it:
        # swallowing the next token would move `push` out of reach.
        invocation = self.one("git --unknown push --force")
        self.assertEqual(self.operands(invocation), ["push"])
        self.assertEqual(
            self.flags(invocation), {"--unknown": None, "--force": None}
        )

    def test_an_option_after_the_subcommand_is_not_an_option(self) -> None:
        # §4.2 scopes the declaration to what *precedes* a subcommand;
        # past it, `-C` is a flag of the subcommand like any other.
        invocation = self.one("git push -C /srv")
        self.assertEqual(self.options(invocation), {})
        self.assertEqual(self.flags(invocation), {"-C": None})
        self.assertEqual(self.operands(invocation), ["push", "/srv"])

    def test_a_tool_with_no_declared_options_reads_none(self) -> None:
        invocation = self.one("stubtool -i prod --syntax-check site.yml")
        self.assertEqual(invocation.options, ())


class ArityTests(Reads):
    """The three declared arities, parsed (§4.2)."""

    def test_a_bare_flag_takes_nothing(self) -> None:
        # Corpus: `stubtool --syntax-check site.yml` → silent.
        invocation = self.one("stubtool --syntax-check site.yml")
        self.assertEqual(self.flags(invocation), {"--syntax-check": None})
        self.assertEqual(self.operands(invocation), ["site.yml"])

    def test_a_flag_is_found_wherever_it_sits(self) -> None:
        # §4.2: "the deciding token is often last, because that is where
        # the agent tends to put it". Corpus: `stubtool site.yml
        # --syntax-check` → silent.
        invocation = self.one("stubtool site.yml --syntax-check")
        self.assertEqual(self.flags(invocation), {"--syntax-check": None})
        self.assertEqual(self.operands(invocation), ["site.yml"])

    def test_a_value_required_flag_takes_the_next_token(self) -> None:
        # Corpus: `stubtool -i prod --syntax-check site.yml` → silent.
        invocation = self.one("stubtool -i prod --syntax-check site.yml")
        self.assertEqual(
            self.flags(invocation), {"-i": "prod", "--syntax-check": None}
        )
        self.assertEqual(self.operands(invocation), ["site.yml"])

    def test_a_value_required_flag_takes_an_attached_value(self) -> None:
        # Corpus: `stubtool --tags foo --syntax-check deploy.yml` →
        # silent; `--flag=value` is the same declaration's other
        # spelling (§4.2).
        invocation = self.one("stubtool --tags=foo --syntax-check deploy.yml")
        self.assertEqual(
            self.flags(invocation), {"--tags": "foo", "--syntax-check": None}
        )

    def test_an_attached_empty_value_is_a_value(self) -> None:
        invocation = self.one("stubtool --tags= --syntax-check a.yml")
        self.assertEqual(self.flags(invocation)["--tags"], "")

    def test_a_value_required_flag_swallows_a_flag_shaped_token(self) -> None:
        # §4.2's worst direction, made concrete: corpus `stubtool
        # deploy.yml -i --syntax-check` → ask, because `--syntax-check`
        # is really `-i`'s inventory string and satisfies no grant.
        invocation = self.one("stubtool deploy.yml -i --syntax-check")
        self.assertEqual(self.flags(invocation), {"-i": "--syntax-check"})
        self.assertNotIn("--syntax-check", self.flags(invocation))

    def test_the_same_swallow_through_another_declared_flag(self) -> None:
        # Corpus: `stubtool deploy.yml --tags --syntax-check` → ask.
        invocation = self.one("stubtool deploy.yml --tags --syntax-check")
        self.assertEqual(self.flags(invocation), {"--tags": "--syntax-check"})

    def test_a_value_required_flag_with_nothing_after_it_is_malformed(
        self,
    ) -> None:
        # §4.2: "a declared value-taking flag with nothing after it
        # makes the invocation malformed, which is unproven, not safe".
        # Corpus: `stubtool deploy.yml --limit` → ask.
        invocation = self.one("stubtool deploy.yml --limit")
        self.assertEqual(invocation.doubts, (Doubt.MALFORMED,))
        self.assertEqual(self.flags(invocation), {"--limit": None})

    def test_a_malformed_option_on_a_rules_only_tool_is_malformed_too(
        self,
    ) -> None:
        # §4.2 scopes the *unreadable-token* rule to gated invocations
        # and states this one flat. A reading that priced both through
        # one flag would leave `git -C` — the global option whose value
        # decides which repository is touched — unpriced on a tool that
        # is registered and not gated, which is the direction §3.3
        # forbids.
        invocation = self.one("git -C")
        self.assertEqual(invocation.doubts, (Doubt.MALFORMED,))

    def test_a_malformed_flag_at_the_end_of_a_segment(self) -> None:
        # The segment ends at the separator, so the next command's word
        # is never eaten as a value.
        reading = self.read("stubtool apply --mode && git status")
        self.assertEqual(len(reading.invocations), 2)
        self.assertEqual(reading.invocations[0].doubts, (Doubt.MALFORMED,))
        self.assertEqual(reading.invocations[1].name, "git")

    def test_a_value_optional_flag_takes_an_ordinary_next_token(self) -> None:
        # §4.2: "some hand-rolled CLIs accept both `--argument custom
        # --check` and `--argument --check`".
        invocation = self.one("stubopt --argument custom --check")
        self.assertEqual(
            self.flags(invocation), {"--argument": "custom", "--check": None}
        )
        self.assertEqual(self.operands(invocation), [])

    def test_a_value_optional_flag_leaves_a_flag_shaped_token_alone(
        self,
    ) -> None:
        # §4.2: "reading a value-optional flag as value-required can
        # swallow the very token that decides the verdict".
        invocation = self.one("stubopt --argument --check")
        self.assertIn("--check", self.flags(invocation))

    def test_a_bare_value_optional_flag_takes_its_declared_default(
        self,
    ) -> None:
        # `D-039`: the tool's own default, declared once beside the
        # arity, so `--argument` and `--argument check` are one case.
        invocation = self.one("stubopt --argument --check")
        self.assertEqual(self.flags(invocation)["--argument"], "check")

    def test_a_bare_value_optional_flag_without_a_default_has_no_value(
        self,
    ) -> None:
        # `D-039`'s other half: no declared default, so a condition on
        # the value can be neither proven nor ruled out.
        invocation = self.one("stubopt --plain --check")
        self.assertIsNone(self.flags(invocation)["--plain"])

    def test_a_value_optional_flag_at_the_end_is_not_malformed(self) -> None:
        # Nothing is missing: the arity says the value may be absent.
        invocation = self.one("stubopt --check --argument")
        self.assertFalse(invocation.unproven)
        self.assertEqual(self.flags(invocation)["--argument"], "check")

    def test_an_undeclared_flag_is_read_as_bare(self) -> None:
        # Corpus: `stubtool --syntax-check deploy.yml --unknown` → ask,
        # from the closed world at `009`; here it must at least not
        # swallow the token after it.
        invocation = self.one("stubtool --syntax-check deploy.yml --unknown x")
        self.assertEqual(
            self.flags(invocation),
            {"--syntax-check": None, "--unknown": None},
        )
        self.assertEqual(self.operands(invocation), ["deploy.yml", "x"])

    def test_a_repeated_flag_is_kept_once_per_use(self) -> None:
        # A mapping would drop one; `-e nodes_remove=test1` beside a
        # harmless `-e` is exactly the case a deny rule reads (context
        # C's ruling on ansible-playbook).
        invocation = self.one("stubtool --tags a --tags b deploy.yml")
        self.assertEqual(
            invocation.flags,
            (Flag("--tags", Value("a")), Flag("--tags", Value("b"))),
        )


class EndOfOptionsTests(Reads):
    """`--` is structure, and is itself matchable (§4.2)."""

    def test_the_marker_is_recorded(self) -> None:
        # Corpus: `git checkout -- file.py` → ask. §4.2: "it is the
        # explicit 'operand is a path' signal some rules key on".
        invocation = self.one("git checkout -- file.py")
        self.assertIn("--", self.flags(invocation))

    def test_operands_survive_the_marker(self) -> None:
        invocation = self.one("git checkout -- file.py")
        self.assertEqual(self.operands(invocation), ["checkout", "file.py"])

    def test_a_dashed_token_after_the_marker_is_an_operand(self) -> None:
        # Otherwise a grant could be satisfied by a token the tool
        # itself will read as a file name.
        invocation = self.one("stubtool -- --syntax-check")
        self.assertEqual(self.operands(invocation), ["--syntax-check"])
        self.assertEqual(self.flags(invocation), {"--": None})

    def test_flags_before_the_marker_are_still_flags(self) -> None:
        # Corpus: `git checkout -f -- .` → ask.
        invocation = self.one("git checkout -f -- .")
        self.assertEqual(self.flags(invocation), {"-f": None, "--": None})
        self.assertEqual(self.operands(invocation), ["checkout", "."])


class RecognitionTests(Reads):
    """A tool is recognized by the whole basename of its word (§4.2)."""

    def test_a_bare_name_is_recognized(self) -> None:
        self.assertIs(
            self.one("stubtool a.yml").entry, POLICY.lookup("stubtool")
        )

    def test_a_path_spelling_is_the_same_tool(self) -> None:
        # §4.2: "`git` and `/usr/bin/git` are the same tool".
        self.assertIs(
            self.one("/usr/bin/git status").entry, POLICY.lookup("git")
        )

    def test_a_relative_interpreter_path_is_the_same_tool(self) -> None:
        # Corpus: `.venv/bin/ansible-playbook playbooks/check/…` →
        # silent, which needs the basename to reach the registration.
        invocation = self.one(".venv/bin/stubtool --syntax-check a.yml")
        self.assertIs(invocation.entry, POLICY.lookup("stubtool"))

    def test_the_written_word_is_kept(self) -> None:
        # §6.2's citation and §9's output name what the operator wrote,
        # not what it resolved to.
        self.assertEqual(self.one("/usr/bin/git status").name, "/usr/bin/git")

    def test_a_longer_name_is_a_different_tool(self) -> None:
        # Corpus: `stub2x wipe` → silent, `stubtool-extra deploy.yml` →
        # silent, `mystubtool deploy.yml` → silent. §4.2: "never a
        # prefix or substring".
        for word in ("stub2x", "stubtool-extra", "mystubtool"):
            with self.subTest(word=word):
                self.assertIsNone(self.one(f"{word} deploy.yml").entry)

    def test_a_hyphenated_neighbour_is_not_the_tool(self) -> None:
        # §4.2: "`git-crypt` is not git".
        self.assertIsNone(self.one("git-crypt unlock").entry)

    def test_an_alias_reaches_the_same_entry(self) -> None:
        # Corpus: `stub2 wipe` → deny, `stub2 --syntax-check site.yml`
        # → silent: the alias is a fully equivalent name (§4.2).
        self.assertIs(self.one("stub2 wipe").entry, POLICY.lookup("stubtool"))

    def test_a_name_used_as_an_operand_is_not_an_invocation(self) -> None:
        # Corpus: `grep stubtool README.md` → silent, `ls ../stubtool` →
        # silent. Only the command word is read as a tool.
        invocation = self.one("grep stubtool README.md")
        self.assertIsNone(invocation.entry)
        self.assertEqual(invocation.name, "grep")

    def test_an_unregistered_command_word_has_no_entry(self) -> None:
        # Corpus: `make check` → silent.
        self.assertIsNone(self.one("make check").entry)

    def test_a_variable_in_command_position_is_a_name_that_cannot_be_read(
        self,
    ) -> None:
        # §4.2: "A variable in *command position* (`$RUNNER deploy`) is
        # a command that cannot be named". Its three verdicts are `009`
        # and `010`'s; what reading owes is the fact itself, kept apart
        # from an ordinary unregistered word — `010`'s lost walk asks
        # for the first and stays silent for the second, and it must not
        # have to re-parse the name to tell them apart.
        invocation = self.one("$RUNNER deploy")
        self.assertEqual(invocation.name, "$RUNNER")
        self.assertIsNone(invocation.entry)
        self.assertTrue(invocation.dynamic_name)

    def test_an_ordinary_unknown_command_word_is_not_dynamic(self) -> None:
        self.assertFalse(self.one("myrunner deploy").dynamic_name)


class PathDeclarationTests(Reads):
    """A tool may be declared by project-relative path (§4.2)."""

    def test_a_path_declaration_is_reached_by_its_own_spelling(self) -> None:
        invocation = self.one("tools/deploy.py --now")
        self.assertIs(invocation.entry, POLICY.lookup_path("tools/deploy.py"))

    def test_traversals_are_resolved_before_comparing(self) -> None:
        # §4.2: "so `./tools/deploy.py` and `tools/../tools/deploy.py`
        # both hit".
        for spelling in ("./tools/deploy.py", "tools/../tools/deploy.py"):
            with self.subTest(spelling=spelling):
                self.assertIs(
                    self.one(f"{spelling} --now").entry,
                    POLICY.lookup_path("tools/deploy.py"),
                )

    def test_a_path_declaration_beats_the_basename_one(self) -> None:
        # §3.4's most-specific-wins rule: "a path declaration attaches
        # policy to the file the operator meant".
        self.assertIsNot(
            self.one("tools/deploy.py --now").entry,
            POLICY.lookup("deploy.py"),
        )

    def test_another_directory_falls_back_to_the_basename(self) -> None:
        # §4.2's warning made concrete from the other side: a basename
        # registration "would let a grant written for the operator's
        # script release a same-named file anywhere", so the two
        # declarations must not be the same entry.
        self.assertIs(
            self.one("vendor/deploy.py --now").entry,
            POLICY.lookup("deploy.py"),
        )

    def test_an_absolute_spelling_is_not_the_project_path(self) -> None:
        self.assertIs(
            self.one("/srv/tools/deploy.py --now").entry,
            POLICY.lookup("deploy.py"),
        )


class LineContextTests(Reads):
    """An in-line `cd` poisons every later relative path (§3.2)."""

    def test_a_line_without_a_cd_carries_a_clean_context(self) -> None:
        invocation = self.one("stubtool clean .scratch/build")
        self.assertFalse(invocation.context.relative_paths_unproven)

    def test_a_cd_poisons_what_follows_it(self) -> None:
        # §3.2: "a directory change earlier in the judged line
        # (`cd /elsewhere && tool ./x`) makes every later relative
        # *path* match unproven".
        reading = self.read("cd /elsewhere && stubtool clean .scratch/build")
        self.assertTrue(
            reading.invocations[-1].context.relative_paths_unproven
        )

    def test_a_cd_does_not_reach_backwards(self) -> None:
        reading = self.read("stubtool clean .scratch/build && cd /elsewhere")
        self.assertFalse(
            reading.invocations[0].context.relative_paths_unproven
        )

    def test_a_cd_reaches_past_an_intervening_command(self) -> None:
        # §3.2: it "applies to everything after the `cd` on the line" —
        # the invocation between them does not clear it.
        #
        # What this case does *not* prove is §3.2's lexical-not-scope-
        # aware ruling, whose discriminating example is the subshell:
        # "`(cd build && make) && tool ./x` is poisoned for `./x`
        # although the outer base never moved". Bare `(...)` is `011`'s,
        # and the case belongs there, where the parse can tell a
        # subshell from a command word.
        reading = self.read("cd build && make && stubtool clean .scratch/x")
        self.assertTrue(
            reading.invocations[-1].context.relative_paths_unproven
        )

    def test_a_cd_as_an_operand_poisons_nothing(self) -> None:
        # Only a command word changes a directory.
        reading = self.read("echo cd && stubtool clean .scratch/x")
        self.assertFalse(
            reading.invocations[-1].context.relative_paths_unproven
        )

    def test_a_relative_path_declaration_after_a_cd_is_unproven(self) -> None:
        # §4.2: "After an in-line `cd`, a relative spelling of a
        # path-declared tool is unproven and recognition degrades
        # stricter, like any path match."
        reading = self.read("cd /srv && ./tools/deploy.py --now")
        invocation = reading.invocations[-1]
        self.assertIs(invocation.entry, POLICY.lookup_path("tools/deploy.py"))
        self.assertEqual(invocation.doubts, (Doubt.UNRESOLVED_PATH,))


class UnreadableTokenTests(Reads):
    """What the engine cannot read as a plain word (§4.2, §3.3)."""

    def test_an_operand_carrying_a_space_is_unreadable(self) -> None:
        # §4.2: "`deploy --syntax-check 'my file.yml'` asks, because one
        # operand carrying a space is not the plain word a grant
        # accepts". Corpus: `stubtool --syntax-check 'my file.yml'` →
        # ask, although the grant's flag is right there.
        invocation = self.one("stubtool --syntax-check 'my file.yml'")
        self.assertEqual(invocation.doubts, (Doubt.UNREADABLE,))

    def test_a_glob_character_is_unreadable(self) -> None:
        # §4.2: "an operand or value containing whitespace, glob
        # characters, or the like". Grants prove ordinary shapes.
        for operand in ("*.yml", "site?.yml", "[ab].yml"):
            with self.subTest(operand=operand):
                self.assertTrue(
                    self.one(f"stubtool --syntax-check {operand}").unproven
                )

    def test_a_variable_reference_is_dynamic(self) -> None:
        # §4.2: "A shell variable reference is an unknown at decision
        # time"; the matchers already answer unproven for one, so the
        # reading has to mark it.
        invocation = self.one("stubtool --syntax-check $FOO")
        self.assertEqual(invocation.operands, (Value("$FOO", dynamic=True),))

    def test_the_braced_spelling_is_dynamic_too(self) -> None:
        invocation = self.one("stubtool --syntax-check ${FOO}")
        self.assertEqual(invocation.operands, (Value("${FOO}", dynamic=True),))

    def test_a_variable_inside_a_larger_token_is_dynamic(self) -> None:
        invocation = self.one("stubtool clean /tmp/$FOO")
        self.assertTrue(invocation.operands[-1].dynamic)

    def test_a_dynamic_token_leaves_the_invocation_unproven(self) -> None:
        # §4.2: "on a gated tool it leaves the invocation unproven".
        self.assertTrue(self.one("stubtool --syntax-check $FOO").unproven)

    def test_a_single_quoted_variable_is_literal(self) -> None:
        # Single quotes stop expansion, so there is nothing unknown.
        invocation = self.one("stubtool clean '$FOO'")
        self.assertEqual(invocation.operands[-1], Value("$FOO"))

    def test_a_dynamic_flag_value_is_marked(self) -> None:
        invocation = self.one("stubtool --tags $FOO --syntax-check a.yml")
        self.assertEqual(
            invocation.flags[0], Flag("--tags", Value("$FOO", dynamic=True))
        )

    def test_a_dynamic_token_on_an_unregistered_tool_is_still_marked(
        self,
    ) -> None:
        # §4.2 names this shape: "On positions nothing constrains, it is
        # an opaque token like any other word (`echo $FOO` stays silent
        # in the default posture)." The token is still dynamic — a
        # matcher would answer unproven for it — and the invocation
        # carries no doubt, because there is no gate for one to fail.
        invocation = self.one("echo $FOO")
        self.assertEqual(invocation.operands, (Value("$FOO", dynamic=True),))
        self.assertEqual(invocation.doubts, ())

    def test_a_plain_line_is_proven(self) -> None:
        # Corpus: `stubtool --syntax-check site.yml` → silent, which no
        # unproven reading of it could reach.
        self.assertFalse(self.one("stubtool --syntax-check site.yml").unproven)

    def test_ordinary_path_and_value_shapes_stay_readable(self) -> None:
        # Corpus: `stubtool clean /tmp/x /tmp/y` → silent;
        # `stubtool apply --mode dry-run` → silent.
        self.assertFalse(self.one("stubtool clean /tmp/x /tmp/y").unproven)
        self.assertFalse(self.one("stubtool apply --mode dry-run").unproven)

    def test_a_dollar_that_names_nothing_is_not_dynamic(self) -> None:
        # A bare `$` is a literal character to the shell.
        invocation = self.one("stubtool clean /tmp/a$")
        self.assertFalse(invocation.operands[-1].dynamic)

    def test_a_strange_token_on_a_rules_only_tool_is_no_doubt(self) -> None:
        # §4.2 scopes this rule to gated invocations — "a token a gated
        # invocation carries that the engine cannot read as a plain
        # word" — because what a strange token defeats is a grant, and a
        # rules-only tool has none. Corpus: `git commit -m 'a plain
        # message'` → silent, on a tool that is registered and not
        # gated. Recorded flat, it would be a doubt on nearly every
        # ordinary line.
        invocation = self.one("git commit -m 'a plain message'")
        self.assertEqual(invocation.doubts, ())
        entry = invocation.entry
        assert entry is not None
        self.assertFalse(entry.gated)
