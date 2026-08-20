#!/usr/bin/env python3
"""PreToolUse guard for Bash: gate commands that permission rules cannot express.

Template. Copy into a project as `.claude/hooks/bash_guard.py`, then edit only
the REGISTRY section near the bottom. Everything above it is meant to travel
between projects unchanged.

Permission patterns match a command prefix. That cannot express "a force push
however it is spelled" (`git push origin --force`), nor "safe only when a flag
is set" (`ansible-playbook site.yml --syntax-check`), because the deciding
token can sit anywhere and Claude tends to put it last.

Everything here is decided on *parsed* argv, one subcommand at a time. Matching
the raw line with regexes is unsound in both directions: `git commit -m 'fix
the --amend bug'` is not an amend, and in `ansible-playbook --syntax-check
a.yml && ansible-playbook deploy.yml` the safe half must not vouch for the
other. Only tokenizing resolves quoting; only splitting separates invocations.

A line can also hide a command inside another one. Assignments bind to what
runs next (`GIT_SSH_COMMAND=… git fetch`), wrappers run something else (`sudo
git push --force`), a shell's `-c` argument is a command line in its own right,
and a substitution or subshell is another command again — `echo $(git push
--force)`, and equally `git commit -m "$(git push --force)"`, where the quoting
hides it from the tokenizer entirely. Each is walked through to the command
underneath, and every command position found is judged — so gating a wrapper
never hides what it wraps.

Decisions: **deny** what has no authorized use, **ask** for anything that
writes outward or destroys work, stay silent otherwise. Silence is not approval
— it hands the call back to the permission rules and the current permission
mode, and what that mode then does with an unmatched command (prompt,
auto-approve, judge by classifier) is a property of the installed version,
probed at instantiation, never assumed from this docstring. There is also one
**allow**, which is the exception the next section is about.


WHERE THE GUARD GRANTS
----------------------

Almost nowhere, and the constraint is worth stating before the exception.

A hook's `"allow"` skips the interactive prompt — and measurement says it also
lifts two things the documentation does not mention: the bash safety
heuristics, and the **working-directory sandbox**. `touch ../escaped.txt`,
blocked outright when merely permitted by a rule, runs when a hook allows it.
So granting is not "approving a prompt on the operator's behalf"; it is
switching off the boundary that keeps a mistake inside the project. What it
cannot do is override a `deny` or `ask` rule from settings — those still hold,
which is why they, not this file, are the right place for anything that must
never happen.

That rules out the tempting general form, "if every command in the line is
silent, allow it". `touch "$(cat evil.txt)"` has nothing gated in it, and the
substitution's output becomes a path, which the guard never sees because it
does not exist until after the decision.

What remains is a grant keyed to a *shape whose output cannot direct a write*.
`git commit -m "$(…)"` qualifies: whatever comes back is a commit message.
That earns the one `Rule("allow", …)` in the registry, hedged three ways — it
ranks below deny and ask, it is withheld if anything else in the line has an
opinion, and `allow_globals` withholds it if any global option was used.

The reason it is worth having at all: Claude Code prompts on *any* line
containing a substitution, no permission rule can lift that, and the system
prompt pushes Claude toward writing them. Without the grant that prompt is
unavoidable and constant, which is how operators end up in a looser
permission mode — where
the sandbox is gone for everything, not just for one proven shape.

Before adding a second one, satisfy yourself that no expansion of the granted
command can become a path or a command. If it can, the answer is silence.


HOW A VERDICT IS REACHED
------------------------

Each command in a line is judged on its own, and the strongest verdict in the
line wins: deny, then ask, then allow, then silence. Within one invocation:

* a **Rule** that matches contributes its verdict — deny, ask or allow — and
  rules are consulted whether or not the tool declares grants;
* a **Grant** that matches contributes nothing: it is the absence of an
  objection, which is what silence means here;
* if nothing else applied, **`gated_verdict`** is contributed — the tool's
  answer for an invocation nothing matched;
* if that leaves nothing, the guard stays silent and the permission rules and
  the current mode decide.

`gated_verdict` set holds whether or not the tool declares grants, which is how
"everything here is the operator's" is said — a tool with no grants and
`gated_verdict="deny"` refuses every invocation, with its reason. Left unset it
derives: silent for a tool with no grants, `ask` for one that declares grants
and was not granted. So the common shapes need nothing: git and docker declare
rules and stay silent elsewhere; a deploy tool declares grants and asks
elsewhere; and a project that has decided unproven means refused says
`gated_verdict="deny"` once.

Two cases follow from that and are worth stating, because both look like holes
and neither is:

*Rules but no grants, and no rule matched* — silence. That is the safe-by-
default model working: the acts worth naming are named, everything else falls
through to the permission rules. git and docker are this shape.

*Neither rules nor grants* — silence, always. Such an entry exists for a
different job: it declares `nested`, so the guard can walk through it to the
command it runs, or it names aliases. Every shell wrapper is this shape.

`--liveness` checks the pair rather than the shape: a `gated_verdict` that is
not a real verdict, or one set with no `gated_reason` — a refusal that says
nothing is worse than none, since the reader cannot tell a rule from a bug.

A worked example, because the interaction is the part that misleads. With
`gated_verdict="deny"` and a grant on "any operand is a read verb", a deny
*rule* for write verbs looks redundant — a write-only command matches no grant
and is denied already, and `osmp server list && osmp server delete x` is
denied on its second invocation, since each is judged alone. It is not
redundant for one case: an operand that is a read verb without being a verb.

    openstack server delete list        # a server named "list"

The grant sees `list`, holds, and the command goes silent. Only a rule reading
"a write verb sits in this command" catches it. That is the whole of what such
a rule buys once judging is per-invocation, and it is worth its line where the
tool reaches real infrastructure.


CHOOSING A RULE KIND
--------------------

Put the enumeration on whichever side of the tool is finite, and let the
residue land on the safe default.

*Safe by default, with a listable set of dangerous acts* — git, docker, most
CLIs you read with. Declare `rules`. They are checked **existentially**: if any
subcommand in the line is a named act, the line is gated; everything unnamed
falls through silently, which is right because most of it is harmless.

*Dangerous by default, with a small safe set* — ansible-playbook, terraform,
kubectl, deploy scripts. Declare `grants`. They are checked **universally**:
every invocation must match a proven-safe shape, closed-world, and anything
else asks. A flag you never considered can then only move a verdict toward the
prompt, never away from it.

Getting this backwards is expensive both ways. Grants for git would mean
enumerating hundreds of safe subcommands, prompting on every one you forgot.
Rules for ansible would give you nowhere to put "unless --syntax-check", since
rules only fire — they never exempt.

A tool may declare both. Rules then hold regardless of the grants: a rule can
deny an act that a grant would otherwise have waved through.


WHAT MUST LAND IN settings.json
-------------------------------

This guard gates, and grants in exactly one place (see WHERE THE GUARD GRANTS).
It cannot loosen a `deny` or `ask` rule, so those remain yours alone. Pair it
accordingly:

1.  **Allow the tool broadly; let the guard claw back.** For every rule- or
    grant-bearing tool, add a broad allow — `Bash(git:*)`, and one line per
    such tool the project adds. Never for the SHELL_WRAPPERS layer: a broad
    allow on a command-runner is a broad allow on everything it runs when
    the guard is dead. Prefix rules respect word boundaries, so `Bash(git:*)` does
    not leak to `git-crypt`. This is the whole point: broad allow plus a narrow
    hook is what replaces a long, brittle allow list. A gated tool with no
    allow line is pointless — it would prompt on everything anyway, and its
    grants would never be reached.

2.  **Never write an `ask` rule for a tool the guard gates.** Rules are
    evaluated deny → ask → allow, and a matching `ask` prompts *even when a
    hook returns "allow"*. An `ask Bash(ansible-playbook:*)` therefore makes
    every carve-out impossible, including the guard's. That mistake is the
    reason this file exists — express the exception here, in a `Grant`.

3.  **Do not restate the guard's asks in settings.** A prefix rule is strictly
    weaker: `Bash(git push:*)` misses `git -C dir push`, which the guard
    catches. Two sources of truth, one of them wrong.

4.  **Do keep a short `deny` backstop for the unrecoverable acts.** A hook that
    crashes — a syntax error from an edit, a lost `+x`, a missing python3 —
    fails *open*: Claude Code logs the failure and proceeds to the permission
    rules. The guard's own try/except cannot catch that, because the module
    never loaded. Denies are prefix-weak (they miss `git push origin --force`),
    but they cost nothing and they cover the losses you cannot undo.

    This need is created by step 1. Under a narrow allow list a dead guard only
    costs extra prompts; under `Bash(git:*)` it costs an unprompted
    `git push --force`. The broad allow and the deny list are a package.

5.  **Mind the permission mode.** In a mode that prompts on unmatched
    commands, the guard's silence is backed by a prompt; in a mode that
    suppresses or delegates that prompt, the guard's asks may be the only
    gate left — which is exactly when the grants carry real weight. The
    mode list and each mode's actual unmatched-command behavior belong to
    the installed version: probe and record them, never take them from
    this docstring.

A minimal pairing for the default registry, which carries git and docker.
Add one allow line per tool the project puts in the registry:

    "permissions": {
      "allow": [
        "Bash(git:*)",
        "Bash(docker:*)"
      ],
      "deny": [
        "Bash(git push --force:*)",
        "Bash(git push -f:*)",
        "Bash(git filter-branch:*)",
        "Bash(git reflog expire:*)"
      ]
    },
    "hooks": {
      "PreToolUse": [
        { "matcher": "Bash",
          "hooks": [ { "type": "command",
                       "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/bash_guard.py" } ] }
      ]
    }


CHANGING THE RULES
------------------

The registry is not ordinary code. It is the boundary the operator relies on,
so it does not move on the assistant's own judgement.

*The GIT tool is ground rules.* It is the same in every project by design, and
it encodes losses that are permanent or expensive to undo. Do not add, weaken
or remove a git rule to get past a prompt in front of you. Changing it needs a
reason specific to the project and stated out loud — "this repo has no remote,
so pushing cannot happen" is one; "the prompt was in my way" is not. If a git
rule fires and you believe it should not have, that is a case to report, not a
rule to edit.

*Every rule change is the operator's call.* Adding, modifying or deleting any
Rule, Grant, known_flag or tool — propose it, say what it would newly allow or
newly gate, and wait for the operator to agree. The one exception is creating
this file from the template at the start of a project: the operator reviews the
whole registry in a single pass then, so the initial set does not need to be
approved rule by rule.

*A surprise becomes a test.* When the operator reports that the guard did the
wrong thing — prompted on something harmless, stayed silent on something it
should have caught — the fix is not complete until CASES contains the exact
command they reported, asserting the corrected verdict. A rule change with no
reproduction case is a regression waiting to happen, and the report is the only
evidence of what the rule was actually for.


WHAT THIS DOES NOT SEE
----------------------

The guard reads a command line; it does not run a shell. These are known and
accepted, listed so nobody mistakes silence for coverage.

*Nothing, for substitution.* It used to be listed here. An unquoted `$(…)`,
`<(…)` or `(…)` is split into its own tokens by the lexer and walked like any
other command; a quoted one — `-m "$(git push --force)"` — never reaches that
splitting, so it is read off the raw line instead, counting parentheses and
tracking single quotes. Double quotes and backticks run, so they are judged;
single quotes do not, so they are left alone. All of it is asserted in
ENGINE_CASES.

*A runner we do not recognise.* `myrunner git push --force` is silent, because
the first word is neither a registered tool, a known wrapper, nor a shell. The
fix is to add the runner to SHELL_WRAPPERS — deliberately, rather than by
guessing. An earlier version did guess, asking whenever a registered name
appeared anywhere in such a line, and it gated `ls ../docker`, `ls time` and
`cat docs/env`: a tool's name is also an ordinary word and an ordinary
directory. Narrowing it did not help, because the signal is absent rather than
weak. A known wrapper we cannot see past is a different case, with a real
signal behind it, and always asks.

*Program text in another language.* A shell's `-c` argument is re-examined;
`python3 -c` and `node -e` are not, since reading their argument as shell would
be guesswork.

*An argument made only of separator characters.* `git commit -m "&&"` splits
where the quoted `&&` sits, because posix tokenizing has already dropped the
quotes and the token is indistinguishable from the operator. It takes a
message that is *only* punctuation, so it has not seemed worth abandoning posix
mode over — but it is real.

*Handoff option arity is approximate.* `Nested.value_opts` covers the common
options; an unknown value-taking one makes the walk lose the command being run,
which asks. That direction is deliberate: a handoff we cannot follow is
unproven, not safe. The reverse — declaring a bare flag as value-taking — is
the one that loses something, since it skips a token too many and can step over
the command itself.


KEEPING IT HONEST
-----------------

This file is written at 88 columns and keeps them wherever it is vendored. A
project whose lint is narrower exempts the width rule for this path alone —
every other rule still applies — because reflowing it makes each refresh a
diff against your reformatting rather than against the template, and because
the formatter's answer here is worse: a nine-word set becomes eleven lines and
the comment explaining each dataclass field strands after a closing paren.
(With pre-commit, the exemption also needs `force-exclude`, since filenames
are passed explicitly.)

Because a broken guard fails open silently, it has to be gated twice, and the
two gates ask different questions.

`--liveness` asks *is this guard alive*: the file is executable, the registry
builds, every declared rule and grant is well-formed, and a payload on stdin
still comes back as a verdict. It runs no behaviour cases, so it stays a lint.
Wire it into whatever the project runs before a commit — that is where the
silent deaths happen: a syntax error from an edit, a lost `+x`, a rename.

`--selftest` asks *does this guard decide correctly*: liveness first, then
every case in CASES and ENGINE_CASES, then coverage — a rule or grant no case
reaches fails it. Wire that into the project's test entry point. Add a case
for every rule you add; that is the only place the intent is written down in
an executable form, and the coverage check is what makes it mandatory rather
than advisory.

Neither answers *is this guard reached*. A path in `settings.json` that names
a file which is not this one leaves valid JSON, a settings file that loads, a
green lint — and a guard that never runs. Nothing here can see that, so the
project checks the pointer itself (its governance well-formedness family is
the place) and probes it live: a command this guard refuses must come back
refused *by it*, naming the rule. If it merely prompts, the hook is not
reaching the tool call and only the deny backstop is left.

A project harness may also prove what CASES cannot. Cases are strings written
by hand; a harness can derive them — every playbook under an exempt directory
must be silent, every one outside it gated, so a file added tomorrow is judged
tomorrow without anyone remembering. Derive what only the project can derive,
and leave the rest here: a case about how a command line is read belongs in
ENGINE_CASES, one about a tool's verdicts in CASES, and duplicating either in
a harness means two places to update and one of them silently wrong.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import PurePosixPath

# =========================== engine ========================================
# Portable. Nothing below the REGISTRY banner should need to change here.

HEREDOC = re.compile(r"<<-?\s*['\"]?(\w+)['\"]?")
INTERPRETER = re.compile(r"\b(ba|z|k|da)?sh\b|\bpython3?\b|\bperl\b|\bruby\b|\bnode\b")
SCRIPT_RUNNERS = {"python", "python3", "py", "sh", "bash", "zsh", "ruby", "perl", "node"}

# Shells whose `-c` argument is another command line, and so is re-examined.
# Deliberately not python or node: their `-c` is program text in another
# language, and reading it as shell would be guesswork.
SHELL_RUNNERS = {"sh", "bash", "zsh", "dash", "ksh"}

# Builtins that join their arguments and run the result as a command line.
# They cannot be handled as wrappers: stepping over `eval` reaches the next
# *token*, which for `eval "git push --force"` is the whole command as one
# quoted string — a token that names no tool, so the line would go silent.
EVAL_RUNNERS = {"eval"}
DASH_C = re.compile(r"^-[a-zA-Z]*c$")  # -c, -lc, -ec …
MAX_DEPTH = 3  # `sh -c 'sh -c …'` must terminate


# Claude Code's documented separator set is `&&`, `||`, `;`, `|`, `|&`, `&` and
# newlines. Testing the characters rather than the whole token covers all of
# them and the runs shlex groups into one token besides — `\n\n\n` from blank
# lines, `;;`, `&&&`.
#
# The newline is the load-bearing member, not an afterthought: leaving it out
# meant `git status\ngit push --force` parsed as a single invocation whose
# subcommand was `status`, so no push rule could fire, and multiline command
# strings are routine.
SEPARATOR_CHARS = {"&", "|", ";", "\n"}

# Everything the lexer treats as punctuation, and so groups into its own token.
# Parentheses are in here because they open and close a command.
PUNCTUATION_CHARS = set("();<>|&\n")

# The shell joins a backslash-continuation into one line before splitting, so
# we must too — otherwise the escaped newline glues itself to the next token
# and `git push \<newline>--force` hides `--force` inside an operand.
CONTINUATION = re.compile(r"\\\n[ \t]*")

# `FOO=bar cmd …` sets FOO for that one command. Only assignments *before* the
# command name are environment; `git push FOO=bar` is an operand. They are
# matchable in their own right rather than merely skipped, because an
# assignment can be more dangerous than any flag — `GIT_SSH_COMMAND=…` runs an
# arbitrary program during a fetch, `GIT_DIR=…` retargets the whole operation.
#
# The name pattern is the shell's, which is why it accepts lower case: `foo=1`
# is as valid a prefix as `FOO=1`. `+=` is bash's append form and is a command
# prefix too, so it must be recognised — otherwise the token is not an
# assignment, becomes argv[0], resolves to no tool, and the whole command goes
# unexamined. Matching against known_env and Rule.env is by exact name, and so
# is case sensitive, as shell variables are.
ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*\+?=")

# A grant condition on a flag's value: a compiled regex, or a predicate for
# when the raw string is not what matters (a path that needs normalizing).
Matcher = re.Pattern[str] | Callable[[str], bool]

# What makes a location a glob rather than a plain directory, in `under`.
GLOB_CHARS = set("*?[")

# Whether Claude Code's own substitution heuristic will fire on this line —
# the only situation in which a grant is used rather than downgraded to
# silence. Textual on purpose: the thing being predicted is itself textual.
SUBSTITUTION = re.compile(r"\$\(|`")

# Operands and flag values of a *gated* tool must look like ordinary words.
# Anything stranger is unproven rather than safe.
VALUE_OK = re.compile(r"^[\w./=@:+-]+$")

# Set by --selftest to collect the rules and grants the cases actually reach.
# A rule no case can trigger is a rule nobody has checked, so the selftest
# fails on it — and a grant is checked the same way, for the opposite failure:
# an unreached grant means the proven-safe shape it declares has never been
# shown to resolve to silence. That direction is safe (the tool over-prompts)
# and therefore quiet, which is exactly why it needs the mechanical check.
AUDIT: set | None = None


@dataclass(frozen=True)
class Rule:
    """An act worth a verdict: this subcommand path, optionally with these flags.

    `path` is matched as a prefix of the invocation's operands, so ("push",)
    covers `git push origin main`, and ("reflog", "expire") reaches a
    second-level subcommand. `flags` is a trigger set — the rule fires when any
    one of them is present, wherever it sits — and `None` means the path alone
    is the act, no flag needed.

    `env` names environment assignments the same way, for the cases where the
    danger is in the environment rather than the command line. Conditions are
    ANDed: a rule with both fires only when a listed flag *and* a listed
    assignment are present. To gate on either alone, write two rules.

    Note the limit: `flags` and `env` test presence, never value. A rule can
    say "never --force"; it cannot say "never -i production". Value conditions
    live only in `Grant.flag_values` / `Grant.env_values`, and yield `ask`
    rather than `deny`.

    A verdict of `"allow"` is the one that grants, and it is the exception to
    everything else in this file — see WHERE THE GUARD GRANTS. It wins only
    when nothing else matched, it is withheld unless every command embedded in
    the line is silent too, and `allow_globals` bounds which of the tool's
    global options may be present. That list is closed-world like the rest: an
    unlisted global withholds the grant, because a forgotten entry must cost a
    prompt rather than give one away. `git --exec-path=/tmp/x commit` runs
    `/tmp/x/git-commit`, and `-c core.pager=…` is the same kind of hole, so the
    default of "no globals at all" is the honest starting point.
    """

    verdict: str  # "deny" | "ask" | "allow"
    path: tuple[str, ...]
    reason: str
    flags: frozenset[str] | None = None
    operands: Matcher | AnyOf | None = None  # None: the path alone is the act
    env: frozenset[str] | None = None  # None: no environment condition
    allow_globals: frozenset[str] = frozenset()  # allow rules only


@dataclass(frozen=True)
class Grant:
    """One proven-safe shape of an invocation of a gated tool.

    Every condition set here must hold for the grant to apply; a tool is silent
    when *any* of its grants applies. An empty `path` matches any subcommand,
    which is what a tool like ansible-playbook needs, having none.

    `require_any` names flags of which at least one must be *operative* — a
    token counts only if the parser saw it as a flag, so a `--syntax-check`
    swallowed as the value of `-i` does not satisfy it (see `Tool.value_flags`).
    `flag_values` additionally constrains what a flag was given, which is how
    "safe only when --target is under /tmp" would be expressed. `operands`
    constrains every operand past `path`, and requires at least one — that is
    where a tool like `rm` carries the paths it acts on, so it takes the same
    matchers as the rest.

    A matcher is a compiled regex or a predicate taking the value, in every one
    of those three positions. A regex is right when the raw string is what
    matters — a keyword, a name — and is anchored at the start, as `re.match`
    is: write `^(?:.*/)?name$` rather than relying on a search. For a path, use
    `under(...)`: a regex for `^/tmp/` says yes to `/tmp/../root`, which is a
    real traversal past the very boundary the grant exists to draw.
    """

    path: tuple[str, ...] = ()  # required leading subcommands
    require_any: frozenset[str] = frozenset()  # at least one must be operative
    flag_values: tuple[tuple[str, Matcher], ...] = ()  # flag must be given and match
    env_values: tuple[tuple[str, Matcher], ...] = ()  # assignment must be present, match
    operands: Matcher | None = None  # every operand past `path` must match
    allow_operands: bool = True  # False: no operands past `path`


@dataclass(frozen=True)
class Nested:
    """Where a tool stops describing itself and starts running something else.

    `sudo git push` and `docker run alpine git push` both hand off; they differ
    only in where. `path` is the subcommand that does it — empty for a plain
    wrapper, `("run",)` for docker, `("compose", "run")` for its compose form.
    `value_opts` are the tool's own options that consume the next token, and
    `operands` counts positionals it keeps for itself: `timeout 30 cmd` has
    one, `docker run … IMAGE cmd` has one.

    Getting `value_opts` or `operands` wrong costs a prompt, not silence: a
    handoff we cannot follow asks.
    """

    path: tuple[str, ...] = ()
    value_opts: frozenset[str] = frozenset()
    operands: int = 0


@dataclass(frozen=True)
class Tool:
    """How to recognize, parse and judge one command.

    `rules`
        Dangerous acts, checked existentially: any match gates the line.
        Consulted whether or not the tool is gated.

    `grants`
        Proven-safe shapes, checked universally: an invocation is silent only
        if it matches one. `None` means the tool is not gated and only `rules`
        apply; an empty tuple means gated with nothing declared safe, so every
        use asks.

    `gated_reason`
        The text shown in the permission prompt when no grant holds. It is the
        only thing read while deciding, so it should name the risk *and* the
        way to satisfy a grant ("rehearse it with --target under /tmp").
        Unused when `grants` is None.

    `known_flags`
        The closed world for a gated tool: every flag on the invocation must
        appear here, or the invocation is unproven and asks. This is not the
        tool's flag list — it is the set you have decided is safe to see, so
        leaving a flag out is how you gate it. The consequence worth keeping: a
        flag you never considered can only move a verdict toward the prompt,
        never away from it. Expect to extend this a few times early on; each
        addition should be a decision, not a reflex. Unused when not gated.

    `aliases`
        Other binary names that behave identically — `podman` for `docker`,
        `nerdctl` for both. The registry indexes the tool under each, so a
        drop-in replacement needs no second entry to keep in step.

    `nested`
        Where this tool runs another program, so the guard follows through to
        it. A wrapper is just a tool that is *only* this: `sudo` has no rules,
        it only hands off. Declaring it here rather than in a table beside the
        registry keeps a tool's option knowledge with the tool, and means
        judging the outer command never hides the inner one — both are judged,
        strongest verdict wins.

    `known_env`
        The same closed world for `FOO=bar` assignments written before the
        command. An unlisted assignment leaves a gated invocation unproven, so
        a project whose tool takes none can leave this empty and every
        assignment will prompt. Unused when the tool is not gated — a tool that
        is safe by default gates assignments through `Rule.env` instead.

    `value_flags`
        Flags that consume the following token — the tool's arity, which the
        parser cannot guess. Declaring `-i` is what makes `ansible-playbook
        deploy.yml -i --syntax-check` read as "inventory is the string
        --syntax-check", still a real deploy; undeclared, `--syntax-check`
        would look operative and the deploy would pass as a parse-only run. It
        also puts the value within reach of `Grant.flag_values`. Under-
        declaring is unsafe; over-declaring merely swallows an operand, so
        declare every value-taking flag you list in `known_flags`.

    `global_value_opts` / `global_bare_opts`
        Options accepted *before* the subcommand, stripped so that the
        subcommand path lands where `Rule.path` and `Grant.path` expect it.
        Undeclared, `git -C dir push` parses to operands ("dir", "push"), no
        rule for ("push",) matches, and the push goes ungated. `_value_` opts
        consume the next token (`-C dir`, or `--git-dir=x` in one token);
        `_bare_` opts stand alone (`--no-pager`). What separates these from
        `value_flags` is position: they are recognized only ahead of the
        subcommand, and never gate anything themselves.
    """

    name: str  # basename to match, e.g. "git" or "ansible-playbook"
    aliases: frozenset[str] = frozenset()  # other names for the same thing
    nested: tuple[Nested, ...] = ()  # where it hands off to another command
    rules: tuple[Rule, ...] = ()
    # Declaring grants makes the tool gated: dangerous unless a grant holds.
    grants: tuple[Grant, ...] | None = None
    gated_verdict: str | None = None  # verdict when nothing matched; see below
    gated_reason: str = ""  # shown in the prompt; say how to satisfy a grant
    known_flags: frozenset[str] = frozenset()  # closed world, gated tools only
    known_env: frozenset[str] = frozenset()  # closed world for assignments
    value_flags: frozenset[str] = frozenset()  # flags consuming the next token
    global_value_opts: frozenset[str] = frozenset()  # before the subcommand, take a value
    global_bare_opts: frozenset[str] = frozenset()  # before the subcommand, stand alone


@dataclass(frozen=True)
class Invocation:
    words: tuple[str, ...] = ()  # operands in order; subcommand path first
    flags: dict[str, str | None] = field(default_factory=dict)
    env: dict[str, str] = field(default_factory=dict)  # leading FOO=bar
    globals_seen: frozenset[str] = frozenset()  # stripped from before the subcommand
    malformed: bool = False  # a value flag with nothing after it


def registry(*tools: Tool) -> dict[str, Tool]:
    """Index tools by every name they answer to, over the shell wrappers.

    A project entry with the same name as a wrapper replaces it, so a tool that
    both gates and hands off must declare its own `nested` — the selftest
    checks for that rather than leaving it to be discovered.
    """
    indexed: dict[str, Tool] = {}
    for tool in (*SHELL_WRAPPERS, *tools):
        for name in (tool.name, *tool.aliases):
            indexed[name] = tool
    return indexed


MAX_NESTED_PATH = 3  # `docker compose run`


def strip_heredocs(command: str) -> str:
    """Drop heredoc bodies, which are data — a commit message quoting a gated
    command is not that command. A body fed to a *shell* stays: there the text
    really is what runs.

    A body fed to another language is dropped like any other data, on the same
    reasoning that leaves `python3 -c` alone (WHAT THIS DOES NOT SEE): reading
    Python as shell is guesswork, and it guesses wrong in the direction that
    costs a refusal — a backtick inside a Python string is not a command
    substitution, and a docstring naming a gated command is not that command.

    A kept body is only reachable because newlines separate commands: it lands
    as its own segment and is judged like any other. Without that it would
    merge into the surrounding argv and nothing could read it, so the two
    behaviours are coupled — do not weaken one without checking the other.
    """
    for match in HEREDOC.finditer(command):
        before = command[: match.start()]
        interpreter = None
        for found in INTERPRETER.finditer(before):
            interpreter = found.group(0)
        if interpreter and interpreter in SHELL_RUNNERS:
            return command
    kept: list[str] = []
    delimiter: str | None = None
    for line in command.splitlines():
        if delimiter is not None:
            if line.strip() == delimiter:
                delimiter = None
            continue
        kept.append(line)
        found = HEREDOC.search(line)
        if found:
            delimiter = found.group(1)
    return "\n".join(kept)


def split_commands(command: str) -> list[list[str]] | None:
    """Quote-aware split into per-subcommand argv lists. None means the line
    could not be parsed — callers must treat that as unproven, never as safe.

    Newline is made punctuation rather than whitespace so that an unquoted one
    ends a command while one inside quotes stays part of its token: a multiline
    commit message is a single argument, not two commands.
    """
    lexer = shlex.shlex(
        CONTINUATION.sub(" ", command), posix=True, punctuation_chars="();<>|&\n"
    )
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    try:
        tokens = list(lexer)
    except ValueError:  # unbalanced quotes
        return None
    commands: list[list[str]] = [[]]
    for token in tokens:
        if token and set(token) <= SEPARATOR_CHARS:
            commands.append([])
        else:
            commands[-1].append(token)
    return [c for c in commands if c]


def skip_own_args(argv: list[str], index: int, nested: Nested) -> int:
    """Step over a tool's own options and operands to reach what it runs."""
    while index < len(argv):  # its own options, which come first
        token = argv[index]
        if not token.startswith("-") or token == "-":
            break
        name = token.partition("=")[0]
        index += 2 if name in nested.value_opts and "=" not in token else 1

    for _ in range(nested.operands):  # then the operands it keeps for itself
        if index >= len(argv):
            break
        index += 1

    # Whatever is left is the command's, flags included: in `docker run img ls
    # -la` the `-la` is ls's, not docker's.
    return index


def shell_payload(args: list[str]) -> str | None:
    """The string a shell was asked to run: the operand after a `-c`-ish flag."""
    for index, token in enumerate(args):
        if DASH_C.match(token):
            return args[index + 1] if index + 1 < len(args) else None
    return None


def names_a_tool(argv: list[str], tools: dict[str, Tool]) -> bool:
    return any(PurePosixPath(token).name in tools for token in argv)


def split_substitutions(argv: list[str]) -> list[list[str]]:
    """Break a segment where a parenthesis opens or closes a command.

    `$(…)`, `<(…)` and a bare `(…)` subshell all run a command, and the lexer
    has already given us the parentheses as their own tokens — which also
    proves they were unquoted. So this is parsing, not guesswork: the enclosed
    words are walked like any other command, and `$(git rev-parse HEAD)` stays
    silent on its own merits rather than by exception.
    """
    pieces: list[list[str]] = [[]]
    for token in argv:
        # The lexer groups a run of punctuation into one token, so the opener
        # arrives as `(` after a separate `$`, but as `<(` in one piece.
        punctuation = bool(token) and set(token) <= PUNCTUATION_CHARS
        if punctuation and ("(" in token or ")" in token):
            if pieces[-1] and pieces[-1][-1] == "$":
                pieces[-1].pop()  # the marker, not an operand of what precedes
            pieces.append([])
        else:
            pieces[-1].append(token)
    return [piece for piece in pieces if piece]


def embedded_commands(command: str) -> list[str]:
    """Command lines hidden inside a single token: `-m "$(git push --force)"`.

    A quoted substitution survives tokenizing as one word, so `split_commands`
    never sees the parentheses and the command inside is never judged. That is
    a shape Claude reaches for constantly — a commit message built from
    `$(cat …)` — so it cannot be left unexamined.

    Read off the raw line rather than the tokens, tracking single quotes as it
    goes. Tokens are the wrong instrument twice over: posix tokenizing has
    already discarded which quote was used — and the difference decides
    everything, since the shell runs `"$(…)"` and does not run `'$(…)'` — while
    a backticked command containing a space is split across two tokens, so no
    token ever holds a complete pair.

    Parentheses are counted, so `$(a $(b))` yields the outer text and the
    recursion finds the inner one.
    """
    found: list[str] = []
    index, end, in_single = 0, len(command), False
    while index < end:
        char = command[index]
        if in_single:
            in_single = char != "'"
            index += 1
        elif char == "'":
            in_single = True
            index += 1
        elif char == "`":
            close = command.find("`", index + 1)
            if close == -1:
                break
            found.append(command[index + 1 : close])
            index = close + 1
        elif command.startswith("$(", index):
            depth, scan = 1, index + 2
            while scan < end and depth:
                depth += (command[scan] == "(") - (command[scan] == ")")
                scan += 1
            if depth:
                break  # unbalanced; the line will not parse anyway
            found.append(command[index + 2 : scan - 1])
            index = scan
        else:
            index += 1
    return [inner for inner in found if inner.strip()]


def nested_at(tool: Tool, argv: list[str], index: int) -> tuple[Nested | None, int]:
    """The tool's longest handoff whose subcommand path starts at `index`.

    `index` is just past the tool's own name, so these are its subcommands:
    `docker` hands off at `run`, and at `compose run`, but not at `build`.
    """
    words = argv[index : index + MAX_NESTED_PATH]
    for nested in sorted(tool.nested, key=lambda n: len(n.path), reverse=True):
        if tuple(words[: len(nested.path)]) == nested.path:
            return nested, len(nested.path)
    return None, 0


def segment_verdicts(
    argv: list[str], tools: dict[str, Tool], depth: int = 0
) -> list[tuple[str, str]]:
    """Every verdict earned by one segment.

    A segment can hold more than one command position, because a wrapper runs
    something else: `sudo git push --force` is both a sudo and a git push. The
    walk records the wrapper's own verdict if it is registered, then keeps going
    to the command it wraps, so gating the wrapper never hides the wrapped
    command. Assignments seen along the way bind to whatever runs next.
    """
    verdicts: list[tuple[str, str]] = []
    env: dict[str, str] = {}
    index = 0
    wrapped = False  # we stepped over a wrapper, so something is being run

    while index < len(argv):
        while index < len(argv) and ASSIGNMENT.match(argv[index]):
            key, _, value = argv[index].partition("=")
            env[key.rstrip("+")] = value
            index += 1
        if index >= len(argv):
            break

        name = PurePosixPath(argv[index]).name
        tool = tools.get(name)
        if tool is not None:
            # Where this tool's own arguments end. Everything past a handoff
            # belongs to what it runs, and must not be read as the tool's own:
            # the `--syntax-check` in `docker run img ansible-playbook
            # --syntax-check x` is ansible's, and must not satisfy a grant on
            # docker.
            nested, words = nested_at(tool, argv, index + 1)
            handoff = (
                skip_own_args(argv, index + 1 + words, nested)
                if nested is not None
                else len(argv)
            )
            verdict = judge(tool, parse(tool, argv[index + 1 : handoff], env))
            if verdict:
                verdicts.append(verdict)

            if nested is None:
                return verdicts
            index = handoff
            wrapped = True
            continue

        if depth < MAX_DEPTH:
            payload = None
            if name in SHELL_RUNNERS:
                payload = shell_payload(argv[index + 1 :])
            elif name in EVAL_RUNNERS and index + 1 < len(argv):
                payload = " ".join(argv[index + 1 :])
            if payload is not None:
                verdict = decide_bash(payload, tools, depth + 1)
                if verdict:
                    verdicts.append(verdict)
                return verdicts
        if name in SCRIPT_RUNNERS and index + 1 < len(argv):
            script = tools.get(PurePosixPath(argv[index + 1]).name)
            if script is not None:
                verdict = judge(script, parse(script, argv[index + 2 :], env))
                if verdict:
                    verdicts.append(verdict)
            return verdicts

        # Nothing recognised in command position. Inside a wrapper that is
        # enough to ask: we stepped over something whose job is to run a
        # command, so one *is* being run and we lost it — most likely to an
        # option we do not know takes a value. The prompt is also how an
        # unlisted wrapper announces itself for adding to SHELL_WRAPPERS.
        #
        # Outside a wrapper this must not fire, and the temptation is real: an
        # unrecognised leader in a mode where silence means execution looks
        # like a hole worth covering. It is not coverable this way. The test
        # below asks whether a registered name appears *anywhere* in the rest,
        # and a tool's name is also an ordinary word and an ordinary directory:
        # `ls ../docker`, `ls time`, `cat docs/env` would all prompt. Narrowing
        # it does not help — `ls docker` survives every variant — because the
        # signal is absent, not weak. Unknown runners are covered by listing
        # them in SHELL_WRAPPERS, which is why that list is generous.
        if wrapped and names_a_tool(argv[index:], tools):
            verdicts.append(
                ("ask", "a command this guard cannot identify is running a gated tool")
            )
        return verdicts
    return verdicts


def parse(tool: Tool, args: list[str], env: dict[str, str]) -> Invocation:
    """Split args into a subcommand path plus operands, and flags with values."""
    index = 0
    seen: set[str] = set()  # remembered: an allow rule cares which were used
    while index < len(args):  # global options sit before the subcommand
        name = args[index].partition("=")[0]
        if name in tool.global_value_opts:
            seen.add(name)
            index += 1 if "=" in args[index] else 2
        elif name in tool.global_bare_opts:
            seen.add(name)
            index += 1
        else:
            break

    words: list[str] = []
    flags: dict[str, str | None] = {}
    awaiting: str | None = None
    literal = False
    for token in args[index:]:
        if awaiting is not None:
            flags[awaiting] = token
            awaiting = None
        elif literal or not token.startswith("-") or token == "-":
            words.append(token)
        elif token == "--":
            flags["--"] = None
            literal = True
        else:
            name, separator, value = token.partition("=")
            if separator:
                flags[name] = value
            elif name in tool.value_flags:
                awaiting = name
            else:
                flags[name] = None
    return Invocation(
        tuple(words), flags, env, frozenset(seen), awaiting is not None
    )


class AnyOf:
    """Wraps an operand matcher to mean *at least one*, not *every*.

    The quantifier cannot live in the matcher — a matcher sees one value at a
    time — so it is carried here and unwrapped where operands are compared.
    Use it where the deciding token can sit anywhere among the operands, as a
    verb does in `openstack server list`: the position varies with the noun,
    and `security group rule list` puts it fourth.
    """

    __slots__ = ("matcher",)

    def __init__(self, matcher: Matcher) -> None:
        self.matcher = matcher


def any_of(matcher: Matcher) -> AnyOf:
    """`operands=any_of(READ_VERBS)`: one operand matching is enough."""
    return AnyOf(matcher)


def matches(matcher: Matcher, value: str) -> bool:
    if isinstance(matcher, re.Pattern):
        return matcher.match(value) is not None
    return bool(matcher(value))


def operands_match(matcher, operands: list[str]) -> bool:
    """Compare operands against a matcher, honouring `any_of`.

    Empty operands never match: a matcher on operands is a statement about
    what the command acts on, and a command acting on nothing has not proven
    it.
    """
    quantify = any if isinstance(matcher, AnyOf) else all
    matcher = matcher.matcher if isinstance(matcher, AnyOf) else matcher
    return bool(operands) and quantify(matches(matcher, o) for o in operands)


def under(*locations: str | re.Pattern[str]) -> Callable[[str], bool]:
    """Match a value that is a path at, or inside, any of `locations`.

    Each location may be:

    * a directory — `"/tmp"` matches it and everything below it;
    * a glob — `"/home/*/scratch"`, where `*` does not cross a `/`, so
      `/home/yann/scratch` matches and `/home/a/b/scratch` does not;
    * a compiled regex, matched against the whole resolved path.

    Use this for any value that is a path, rather than matching the raw string.
    `^/tmp/` as a plain `Matcher` regex says yes to `/tmp/../etc/passwd`: the
    string starts with the prefix while the path does not live under it. That
    makes a grant hold where it should not, which is the one direction a grant
    must never fail in.

    The value is resolved *before* matching, whichever form is used — so a
    regex passed here is safe where the same regex used directly as a `Matcher`
    would not be. `..` is resolved textually and `~` is expanded. Symlinks are
    not followed: that would mean touching the filesystem from inside a hook,
    on a path that may not exist yet. A relative path resolves against nothing
    and so matches no absolute location — it asks, the safe direction.
    """

    def matcher(value: str) -> bool:
        resolved = os.path.normpath(os.path.expanduser(value))
        path = PurePosixPath(resolved)
        for location in locations:
            if isinstance(location, re.Pattern):
                if location.match(resolved):
                    return True
            elif GLOB_CHARS & set(location):
                stem = location.rstrip("/")
                if path.full_match(stem) or path.full_match(f"{stem}/**"):
                    return True
            else:
                root = os.path.normpath(location)
                if resolved == root or resolved.startswith(root.rstrip("/") + "/"):
                    return True
        return False

    return matcher


def grant_holds(grant: Grant, invocation: Invocation) -> bool:
    if invocation.words[: len(grant.path)] != grant.path:
        return False
    if grant.require_any and not (grant.require_any & invocation.flags.keys()):
        return False
    for flag, matcher in grant.flag_values:
        value = invocation.flags.get(flag)
        if value is None or not matches(matcher, value):
            return False
    for name, matcher in grant.env_values:
        value = invocation.env.get(name)
        if value is None or not matches(matcher, value):
            return False
    operands = invocation.words[len(grant.path) :]
    if not grant.allow_operands and operands:
        return False
    if grant.operands is not None:
        return operands_match(grant.operands, operands)
    return True


def is_granted(tool: Tool, invocation: Invocation) -> bool:
    if invocation.malformed:
        return False
    if not invocation.flags.keys() <= tool.known_flags:
        return False  # an unaccounted flag: unproven
    if not invocation.env.keys() <= tool.known_env:
        return False  # an unaccounted assignment: likewise
    values = [v for v in invocation.flags.values() if v is not None]
    values += list(invocation.env.values())
    if not all(VALUE_OK.match(v) for v in [*values, *invocation.words]):
        return False
    held = False
    for grant in tool.grants or ():
        if grant_holds(grant, invocation):
            if AUDIT is not None:  # the selftest is checking which grants hold
                AUDIT.add(grant)
            held = True
    return held


def matching_rules(tool: Tool, invocation: Invocation) -> list[Rule]:
    """Every rule this invocation satisfies. Conditions are ANDed."""
    matched = []
    for rule in tool.rules:
        if invocation.words[: len(rule.path)] != rule.path:
            continue
        if rule.flags is not None and not (rule.flags & invocation.flags.keys()):
            continue
        if rule.env is not None and not (rule.env & invocation.env.keys()):
            continue
        if rule.operands is not None and not operands_match(
            rule.operands, list(invocation.words[len(rule.path):])
        ):
            continue
        matched.append(rule)
    return matched


def cited(tool: Tool, rule: Rule | None, invocation: Invocation) -> str:
    """Name what decided, so a wrong verdict can be traced to a line of registry.

    A reason says why the guard objects; this says *what it read* to get there
    — the tool, the subcommand path, and the flag, assignment or operand that
    matched. Without it a false positive is a sentence with nothing to grep
    for, and the only way to find the rule is to read them all.
    """
    subject = " ".join((tool.name, *invocation.words[:3])).strip()
    if rule is None:
        return f"[{subject}: no proven-safe shape]"
    hits: list[str] = []
    if rule.flags:
        hits += sorted(rule.flags & invocation.flags.keys())
    if rule.env:
        hits += sorted(rule.env & invocation.env.keys())
    if rule.operands is not None:
        operands = list(invocation.words[len(rule.path):])
        matcher = rule.operands.matcher if isinstance(rule.operands, AnyOf) else rule.operands
        hits += [o for o in operands if matches(matcher, o)]
    where = " ".join(("rule", tool.name, *rule.path)).strip()
    return f"[{where}{': ' + ', '.join(hits) if hits else ''}]"


def judge(tool: Tool, invocation: Invocation) -> tuple[str, str] | None:
    """Strongest verdict for one invocation: deny, then ask, then allow.

    Order-free within each rank, so a table cannot be broken by reordering it.
    An allow ranks last on purpose — anything with an opinion outranks a grant.
    """
    verdicts: list[tuple[str, str]] = []
    for rule in matching_rules(tool, invocation):
        if AUDIT is not None:  # the selftest is checking which rules can fire
            AUDIT.add(rule)
        if rule.verdict == "allow" and not (
            invocation.globals_seen <= rule.allow_globals
        ):
            continue  # a global we have not accounted for: no grant
        verdicts.append((rule.verdict, f"{rule.reason} {cited(tool, rule, invocation)}"))
    # The verdict for an invocation nothing matched. Set explicitly, it holds
    # whether or not the tool declares grants — which is how "everything here
    # is the operator's" is said without inventing an empty grant list.
    # Unset, it derives: silent for a tool with no grants, ask for one that
    # has them and was not granted.
    gated = tool.gated_verdict or ("ask" if tool.grants is not None else None)
    if gated is not None and (tool.grants is None or not is_granted(tool, invocation)):
        verdicts.append((gated, f"{tool.gated_reason} {cited(tool, None, invocation)}"))
    for rank in ("deny", "ask", "allow"):
        for verdict in verdicts:
            if verdict[0] == rank:
                return verdict
    return None


def decide_bash(
    command: str, tools: dict[str, Tool], depth: int = 0
) -> tuple[str, str] | None:
    line = strip_heredocs(command)
    commands = split_commands(line)
    if commands is None:
        mentioned = any(re.search(rf"(?<![\w.-]){re.escape(n)}\b", line) for n in tools)
        if mentioned:
            return "ask", "this line could not be parsed, so nothing about it is proven"
        return None

    asked: tuple[str, str] | None = None
    allowed: tuple[str, str] | None = None
    for argv in commands:
        for piece in split_substitutions(argv):
            for verdict in segment_verdicts(piece, tools, depth):
                if verdict[0] == "deny":
                    return verdict
                if verdict[0] == "allow":
                    allowed = allowed or verdict
                else:
                    asked = asked or verdict

    # A substitution that was quoted never reached the splitting above: it is
    # still sitting inside one token. Judge those command lines too.
    if depth < MAX_DEPTH:
        for inner in embedded_commands(line):
            verdict = decide_bash(inner, tools, depth + 1)
            if verdict is None:
                continue
            if verdict[0] == "deny":
                return verdict
            if verdict[0] != "allow":
                asked = asked or verdict

    # An ask anywhere in the line withholds a grant made elsewhere in it: the
    # grant speaks for one command, never for its neighbours.
    if asked or allowed is None:
        return asked

    # A grant is only *used* where it is needed. Without a substitution the
    # line would reach the permission rules unaided, and granting it would
    # waive the working-directory sandbox for nothing. This is the textual test
    # again, and correctly so: the question is whether Claude Code's own
    # textual heuristic will fire, not what the command does.
    return allowed if SUBSTITUTION.search(line) else None


# =========================== REGISTRY ======================================
# The project-specific part. This is the only section to edit — and no rule
# here changes without the operator's agreement. See CHANGING THE RULES.
#
# Pair every rule- or grant-bearing tool here with a broad allow in
# settings.json — never the SHELL_WRAPPERS below, whose names get no allow
# lines — and never with an `ask` rule — see WHAT MUST LAND IN settings.json
# in the module docstring.
#
# Tools a project adds go after GIT. For the shape of a gated entry — grants,
# known_flags, value_flags, and how a rule ranks against a grant — read the
# `stubtool` fixture near the selftest. It is a test fixture rather than a
# config to copy verbatim, but every field is exercised there, and CHOOSING A
# RULE KIND in the module docstring says which kind a tool wants.

# --- shell wrappers: programs whose only job is to run another program ------
# Tools with no rules and no grants — nothing to say about themselves,
# everything to say about what comes next. They come first because everything
# below is judged through them: `sudo git push --force` is a git push.
#
# Unlike the tools that follow, this list is not project policy — how a shell
# hides a command is the same everywhere — so it is the one part of the
# registry that usually travels between projects unchanged. Add to it when a
# project uses a runner that is not here; a missing entry is a silent hole,
# while an entry for a program you never run costs nothing.
SHELL_WRAPPERS: tuple[Tool, ...] = (
    Tool("sudo", nested=(Nested(value_opts=frozenset(
        {"-u", "--user", "-g", "--group", "-p", "--prompt"})),)),
    Tool("doas", nested=(Nested(value_opts=frozenset({"-u", "-C"})),)),
    Tool("env", nested=(Nested(value_opts=frozenset(
        {"-u", "--unset", "-C", "--chdir", "-S", "--split-string"})),)),
    Tool("command", nested=(Nested(),)),
    Tool("builtin", nested=(Nested(),)),
    Tool("exec", nested=(Nested(value_opts=frozenset({"-a"})),)),
    Tool("nohup", nested=(Nested(),)),
    Tool("setsid", nested=(Nested(),)),
    Tool("time", nested=(Nested(value_opts=frozenset(
        {"-f", "--format", "-o", "--output"})),)),
    Tool("nice", nested=(Nested(value_opts=frozenset({"-n", "--adjustment"})),)),
    Tool("ionice", nested=(Nested(value_opts=frozenset({"-c", "-n", "-p"})),)),
    Tool("stdbuf", nested=(Nested(value_opts=frozenset(
        {"-i", "-o", "-e", "--input", "--output", "--error"})),)),
    Tool("timeout", nested=(Nested(
        value_opts=frozenset({"-s", "--signal", "-k", "--kill-after"}), operands=1),)),
    Tool("chrt", nested=(Nested(value_opts=frozenset({"-p"}), operands=1),)),
    Tool("taskset", nested=(Nested(value_opts=frozenset({"-c", "-p"}), operands=1),)),
    Tool("flock", nested=(Nested(
        value_opts=frozenset({"-w", "--wait", "-E", "--conflict-exit-code"}),
        operands=1),)),
    Tool("xargs", nested=(Nested(value_opts=frozenset(
        {"-n", "-P", "-I", "-d", "-E", "-L", "-s", "--max-args", "--max-procs",
         "--replace", "--delimiter", "--max-lines"})),)),
)


# --- git: safe by default, dangerous acts enumerated -----------------------
# GROUND RULES. This tool is deliberately identical across every project, and
# the acts it names are the ones whose cost is permanent or expensive: rewritten
# published history, destroyed uncommitted work, discarded recovery data.
#
# Do not edit it to clear a prompt that is in your way. A change needs a reason
# specific to this project, said out loud and agreed by the operator; a firing
# rule you disagree with is a case to report, not a rule to rewrite. The two
# worktree asks are the only ones a project can reasonably drop, and only if it
# does not use worktrees.

GIT = Tool(
    name="git",
    global_value_opts=frozenset(
        {"-C", "--git-dir", "--work-tree", "-c", "--exec-path", "--namespace"}
    ),
    global_bare_opts=frozenset(
        {"--no-pager", "--paginate", "--bare", "--no-replace-objects"}
    ),
    rules=(
        Rule(
            "deny", ("push",),
            "history is linear here and published state is never rewritten",
            flags=frozenset({"--force", "-f", "--force-with-lease", "--mirror", "--delete"}),
        ),
        Rule("deny", ("filter-branch",), "rewriting history has no authorized use here"),
        Rule("deny", ("filter-repo",), "rewriting history has no authorized use here"),
        Rule(
            "deny", ("reflog", "expire"),
            "destroying git's recovery data has no authorized use",
        ),
        Rule(
            "deny", ("reflog", "delete"),
            "destroying git's recovery data has no authorized use",
        ),
        Rule(
            "deny", ("update-ref",), "destroying git's recovery data has no authorized use",
            flags=frozenset({"-d"}),
        ),
        Rule(
            "deny", ("gc",), "destroying git's recovery data has no authorized use",
            flags=frozenset({"--prune"}),
        ),
        # The one grant. `git commit -m "$(…)"` is the shape Claude writes
        # constantly, and Claude Code prompts on any line containing a
        # substitution — a decision no permission rule can lift, so without
        # this the prompt is unavoidable and constant.
        #
        # It is safe *for this shape only*: whatever the substitution turns out
        # to expand to, it becomes a commit message, and a message cannot
        # direct a write anywhere. Compare `touch "$(cat x)"`, where the same
        # output becomes a path — which is why the grant names a subcommand and
        # a flag rather than being a general rule about silent commands.
        #
        # `allow_globals` is empty, so `git -C /elsewhere commit -m …` is not
        # granted: -C moves the repository, and granting also waives the
        # working-directory sandbox.
        Rule("allow", ("commit",), "a commit message cannot direct a write",
             flags=frozenset({"-m", "--message"})),
        Rule("ask", ("push",), "pushing is an outward write"),
        Rule(
            "ask", ("commit",), "this rewrites the last commit",
            flags=frozenset({"--amend"}),
        ),
        Rule("ask", ("rebase",), "this rewrites history"),
        Rule(
            "ask", ("reset",), "this destroys committed state",
            flags=frozenset({"--hard", "--merge", "--keep"}),
        ),
        Rule("ask", ("clean",), "this destroys untracked work"),
        Rule("ask", ("restore",), "this destroys uncommitted work"),
        # `-f` is git's own alias for --discard-changes on switch, and on
        # checkout it throws away local modifications the same way a pathspec
        # does. Gating the long form and the pathspec form but not the short
        # alias would leave the commonest spelling of the act ungated.
        #
        # A bare `git checkout <name>` stays silent: whether the operand is a
        # branch or a path decides whether anything is destroyed, and that is
        # not knowable from the command line. `--` is the explicit marker that
        # it is a path, which is why the rule keys on it.
        Rule(
            "ask", ("checkout",), "this destroys uncommitted work",
            flags=frozenset({"--", "-f", "--force"}),
        ),
        Rule(
            "ask", ("switch",), "this destroys uncommitted work",
            flags=frozenset({"--discard-changes", "-f", "--force"}),
        ),
        Rule("ask", ("stash", "drop"), "this destroys stashed work"),
        Rule("ask", ("stash", "clear"), "this destroys stashed work"),
        Rule(
            "ask", ("branch",), "this deletes a branch",
            flags=frozenset({"-d", "-D", "--delete"}),
        ),
        Rule(
            "ask", ("tag",), "this moves or deletes a tag",
            flags=frozenset({"-d", "--delete", "-f", "--force"}),
        ),
        # Drop these two if the project does not use worktrees.
        Rule("ask", ("worktree", "remove"), "this can discard work in another worktree"),
        Rule("ask", ("worktree", "prune"), "this can discard work in another worktree"),
    ),
)

# --- docker: it runs other programs, so the guard follows through ----------
# Safe by default with a listable set of dangerous acts, so `rules`. The three
# families below are dangerous in any project that runs docker at all, and cost
# nothing in one that does not — the rules simply never fire. A project adds its
# own beside them; it does not need to invent these.
#
# All four forms have the same shape — options, then one operand the form keeps
# for itself, then the command — and differ only in which options take a value:
#
#   run IMAGE [cmd]            spawns a container
#   compose run SERVICE [cmd]  spawns one from a compose service
#   exec CONTAINER cmd         uses a container already running
#   compose exec SERVICE cmd   same, by service
#
# What is gated is the command run *in* the container. The image or service is
# deliberately not read as a program, even when it is named after one: an image
# called `org/git` may or may not entrypoint into git, and guessing from the
# name would gate `docker run org/rm -rf` as an `rm` on the host.
#
# Only genuinely value-taking options are listed — over-declaring one would
# skip a token too many and could step over the command itself.
#
# A command inside a container is not always the host's: `docker run --rm
# alpine git push` cannot reach this repo, while `-v $(pwd):/r` can. The guard
# cannot tell those apart, and gates both.

DOCKER_RUN_OPTS = frozenset({
    "-v", "--volume", "-e", "--env", "-p", "--publish", "-w", "--workdir",
    "-u", "--user", "-l", "--label", "-h", "--hostname", "-m", "--memory",
    "-a", "--attach", "--name", "--entrypoint", "--network", "--mount",
    "--env-file", "--label-file", "--add-host", "--device", "--dns", "--expose",
    "--platform", "--pull", "--restart", "--runtime", "--security-opt",
    "--shm-size", "--stop-signal", "--sysctl", "--tmpfs", "--ulimit", "--userns",
    "--volumes-from", "--volume-driver", "--cap-add", "--cap-drop", "--gpus",
    "--cgroupns", "--cidfile", "--group-add", "--ip", "--isolation", "--link",
    "--log-driver", "--log-opt", "--mac-address", "--memory-swap", "--pid",
    "--pids-limit", "--storage-opt", "--uts", "--cpus", "--health-cmd",
})
DOCKER_EXEC_OPTS = frozenset({
    "-e", "--env", "-u", "--user", "-w", "--workdir", "--env-file", "--detach-keys",
})

PUBLISHES = "this publishes to a registry, a write to shared state"
SWEEPS = "this sweep is host-global and reaches other projects on this machine"

DOCKER = Tool(
    name="docker",
    aliases=frozenset({"podman", "nerdctl"}),
    rules=(
        # Publishing, in every spelling that reaches a registry.
        Rule("ask", ("push",), PUBLISHES),
        Rule("ask", ("image", "push"), PUBLISHES),
        Rule("ask", ("manifest", "push"), PUBLISHES),
        Rule("ask", ("compose", "push"), PUBLISHES),
        Rule("ask", ("buildx", "imagetools", "create"), PUBLISHES),
        # A publish hidden inside a build. Gated on the flag being present, not
        # on its value, because a rule can only test presence: `--output
        # type=registry` publishes where `type=local` does not. The cost is a
        # prompt on a local export, which is the safe direction.
        Rule("ask", ("build",), PUBLISHES,
             flags=frozenset({"--push", "--output", "-o"})),
        Rule("ask", ("buildx", "build"), PUBLISHES,
             flags=frozenset({"--push", "--output", "-o"})),
        Rule("ask", ("buildx", "bake"), PUBLISHES, flags=frozenset({"--push"})),
        # Host-global sweeps. Deleting this project's own images, volumes and
        # containers by name stays silent — rebuildable working material — but
        # a prune takes whatever else this host holds.
        Rule("ask", ("system", "prune"), SWEEPS),
        Rule("ask", ("image", "prune"), SWEEPS),
        Rule("ask", ("volume", "prune"), SWEEPS),
        Rule("ask", ("network", "prune"), SWEEPS),
        Rule("ask", ("container", "prune"), SWEEPS),
        Rule("ask", ("builder", "prune"), SWEEPS),
        Rule("ask", ("buildx", "prune"), SWEEPS),
        # Registry credentials.
        Rule("ask", ("login",), "this hands registry credentials to the daemon"),
        Rule("ask", ("logout",), "this changes which registry credentials are held"),
    ),
    nested=(
        Nested(("run",), DOCKER_RUN_OPTS, operands=1),
        Nested(("exec",), DOCKER_EXEC_OPTS, operands=1),
        Nested(("compose", "run"), DOCKER_RUN_OPTS, operands=1),
        Nested(("compose", "exec"), DOCKER_EXEC_OPTS, operands=1),
    ),
)

# Add this project's own tools here, then extend CASES to cover them.

TOOLS: dict[str, Tool] = registry(GIT, DOCKER)


# =========================== hook entry point ==============================


def decide(tool_name: str, tool_input: dict) -> tuple[str, str] | None:
    if tool_name == "Bash":
        return decide_bash(str(tool_input.get("command", "")), TOOLS)
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
        verdict = decide(
            str(payload.get("tool_name", "")), payload.get("tool_input") or {}
        )
    # A broken guard must not fail open: any internal error becomes an ask.
    # This cannot catch a module that fails to load — see KEEPING IT HONEST.
    except Exception as exc:  # noqa: BLE001
        verdict = ("ask", f"guard hook error, decide manually: {exc}")

    if verdict is None:
        return 0
    decision, reason = verdict
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": decision,
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    return 0


# =========================== selftest ======================================
# Add a case for every rule you add, and — when the operator reports the guard
# getting something wrong — the exact command they reported. Wire `--selftest`
# into pre-commit or CI: a guard that stops working should fail the lint, not
# fail open.

# Cases for the registry's own tools: what each rule does and does not gate.
# Keep these about the tool. Anything that is really about how the engine reads
# a command line belongs in ENGINE_CASES, where it is tested once for all tools.
CASES: tuple[tuple[str, str], ...] = (
    # git — silent
    ("git status", "silent"),
    ("git log --oneline -20", "silent"),
    ("git diff HEAD~1", "silent"),
    ("git worktree list", "silent"),  # not `worktree remove`
    ("git stash list", "silent"),  # not `stash drop`
    ("git branch --list", "silent"),  # not `branch -d`
    ("git checkout main", "silent"),  # no `--`
    ("git tag -a v1 -m release", "silent"),  # not `tag -d` or `tag -f`
    ("git restore --staged file.py", "ask"),  # known: only unstages, still asks
    # git — ask
    ("git push", "ask"),
    ("git push origin main", "ask"),
    ("git -C /srv/repo push", "ask"),  # git's global options are declared
    ("git --git-dir=.git commit --amend", "ask"),
    ("git commit --amend --no-edit", "ask"),
    ("git commit -m x --amend", "ask"),  # the flag is found wherever it sits
    # the one grant — see WHERE THE GUARD GRANTS
    ('git commit -m "$(cat msg.txt)"', "allow"),
    ('git commit -m "fix $(git rev-parse --short HEAD)"', "allow"),
    ('git commit --message "$(cat m)"', "allow"),
    # …and only where it is needed: without a substitution the line reaches the
    # permission rules unaided, so the grant is downgraded to silence rather
    # than waiving the sandbox for nothing
    ("git commit -m wip", "silent"),
    ("git commit -m 'a plain message'", "silent"),
    # withheld, each for its own reason
    ('git commit -m "$(git push --force)"', "deny"),  # gated command inside
    ('git commit --amend -m "$(cat m)"', "ask"),  # an ask outranks a grant
    ('git commit -m "$(cat m)" && git push', "ask"),  # ask elsewhere in the line
    ('git commit -m "$(cat m)" && git push --force', "deny"),
    ('git -C /elsewhere commit -m "$(cat m)"', "silent"),  # a global moves the repo
    ('git --exec-path=/tmp/x commit -m "$(cat m)"', "silent"),  # …and this runs code
    ("git commit -F msg.txt", "silent"),  # not the granted shape
    ("git rebase -i main", "ask"),
    ("git reset --hard HEAD~1", "ask"),
    ("git clean -fd", "ask"),
    ("git restore .", "ask"),
    ("git checkout -- file.py", "ask"),
    ("git switch --discard-changes main", "ask"),
    # reported: `-f` is git's own alias for --discard-changes, and on checkout
    # it discards local modifications just as a pathspec does
    ("git checkout -f main", "ask"),
    ("git checkout --force main", "ask"),
    ("git checkout -f -- .", "ask"),
    ("git switch -f main", "ask"),
    ("git switch --force main", "ask"),
    # a bare operand is a branch or a path, and which cannot be told from here
    ("git checkout main", "silent"),
    ("git switch main", "silent"),
    ("git stash drop", "ask"),
    ("git stash clear", "ask"),
    ("git branch -D topic", "ask"),
    ("git worktree remove wt", "ask"),
    ("git worktree prune", "ask"),
    ("git tag -d v1", "ask"),
    ("git tag -a -f v1", "ask"),
    # git — deny
    ("git push --force", "deny"),
    ("git push origin --force main", "deny"),
    ("git push -f origin main", "deny"),
    ("git -C . push --force-with-lease", "deny"),
    ("git filter-branch --tree-filter true HEAD", "deny"),
    ("git filter-repo --path src", "deny"),
    # docker hands off, in both positions a command can hide in
    ("docker run --rm alpine git push --force", "deny"),  # command after the image
    # What is gated is the command run *in* the container. The image is not
    # read as a program even when it is named after one — here the command is
    # `push`, whatever the image's entrypoint turns out to be.
    ("docker run --rm git push --force", "silent"),
    ("docker run --rm alpine/git push --force", "silent"),
    ("docker run --rm alpine/git:2.45 push --force", "silent"),
    ("docker run --rm -v /r:/r alpine git push --force", "deny"),
    ("docker exec -u root api git push --force", "deny"),
    # likewise for a service or container name: the command is the word after
    # it, so here `push` runs inside something that happens to be called git
    ("docker compose run git push --force", "silent"),
    ("docker exec git push", "silent"),
    ("docker compose exec git push", "silent"),
    ("docker compose run --rm web git push --force", "deny"),
    ("docker compose exec web git push --force", "deny"),
    ("podman run --rm alpine git push --force", "deny"),  # alias
    ("nerdctl run --rm alpine git push --force", "deny"),  # alias
    ("docker run --rm alpine git status", "silent"),
    ("docker run --rm alpine echo hello", "silent"),
    # trailing words that are arguments to the image's entrypoint rather than a
    # command, with nothing gated among them
    ("docker run --rm alpine/curl -sL https://example.com", "silent"),
    ("docker run --rm alpine/curl https://example.com", "silent"),
    ("docker run --rm myimage --verbose --output /tmp/x", "silent"),
    ("docker run --rm postgres:16 postgres --version", "silent"),
    ("docker run --rm alpine", "silent"),  # no trailing words at all
    ("docker run --rm -d --name web nginx", "silent"),
    # Known wart: an entrypoint argument that merely spells a registered tool's
    # name is read as "something we could not identify is running one". The
    # command position here holds `-o`, not a tool, but the fail-closed scan
    # sees `git` further along and asks. Costs a prompt, never a wrong deny.
    ("docker run --rm alpine/curl -o git https://example.com", "ask"),
    ("docker build .", "silent"),  # docker does not hand off here
    ("docker compose up -d", "silent"),
    ("git reflog expire --expire=now --all", "deny"),
    ("git reflog delete HEAD@{2}", "deny"),
    ("git update-ref -d refs/heads/topic", "deny"),
    ("git gc --prune=now", "deny"),
    # --- docker: publishing, sweeps, credentials ----------------------------
    ("docker push registry.example/app:1", "ask"),
    ("docker image push registry.example/app:latest", "ask"),
    ("docker manifest push registry.example/app:latest", "ask"),
    ("docker compose push", "ask"),
    ("docker buildx imagetools create -t registry.example/a:1 registry.example/a:2",
     "ask"),
    ("docker build --push -t app:dev .", "ask"),
    ("docker build -t app:dev . --push", "ask"),  # the flag arrives last
    ("docker build -o type=registry,name=registry.example/a:dev .", "ask"),
    ("docker buildx build --push .", "ask"),
    ("docker buildx bake --push", "ask"),
    ("docker system prune -a", "ask"),
    ("docker image prune -a", "ask"),
    ("docker volume prune", "ask"),
    ("docker network prune", "ask"),
    ("docker container prune", "ask"),
    ("docker builder prune", "ask"),
    ("docker buildx prune", "ask"),
    ("docker login registry.example", "ask"),
    ("docker logout registry.example", "ask"),
    # the ordinary local loop stays silent, including deletes by name
    ("docker build -t app:dev .", "silent"),
    ("docker run --rm -it app:dev", "silent"),
    ("docker rm -f app-test", "silent"),
    ("docker rmi app:dev", "silent"),
    ("docker volume rm app-data", "silent"),
    ("docker image ls", "silent"),  # not `image prune`
    ("docker system df", "silent"),  # not `system prune`
    ("docker pull debian:trixie-slim", "silent"),
    ("docker manifest inspect registry.example/app:latest", "silent"),  # a read
)


# --- test fixture: a tool that does not exist ------------------------------
# `stubtool` is not in TOOLS and is not a real program. It exists so the engine
# can be tested on its own terms: how a command line is cut up, how flags are
# parsed, how verdicts rank. Doing that through a registry tool would tie the
# engine's tests to rules that legitimately change per project — trimming a git
# rule should never break a test about newline handling.
#
# It declares everything the engine can express, so nothing is tested by
# accident: rules and grants together, a deny and an ask on the same path, a
# value-taking flag, a closed-world flag set. Its shape is modelled on a deploy
# tool that is dangerous by default and safe only when it parses instead of
# applying — the pattern a real terraform, kubectl or ansible-playbook entry
# would follow — but it is a fixture, not a config to copy verbatim.

STUB_SAFE_FILE = re.compile(r"^(?:.*/)?validates?\.ya?ml$")

STUB_READ_VERBS = re.compile(r"^(list|show|catalog)$")
STUB_WRITE_VERBS = re.compile(r"^(create|delete|set)$")

# A second fixture, for the shapes the first cannot express: a verb that can
# sit anywhere among the operands, and a tool whose unproven case is a denial
# rather than a prompt.
STUBCLI = Tool(
    name="stubcli",
    gated_verdict="deny",
    gated_reason="stub: only a demonstrable read is free here",
    grants=(Grant(operands=any_of(STUB_READ_VERBS)),),
    rules=(
        Rule("deny", (), "stub: a write verb sits in this command",
             operands=any_of(STUB_WRITE_VERBS)),
    ),
)

# Nothing here is ever silent: no grants, no rules, one verdict. The shape a
# tool takes when every use of it is the operator's.
STUBALWAYS = Tool(
    name="stubalways",
    gated_verdict="deny",
    gated_reason="stub: every use of this one is the operator's",
)

STUB = Tool(
    name="stubtool",
    # A second name for the same tool, so alias indexing is exercised.
    aliases=frozenset({"stub2"}),
    # Two handoffs: one whose own options take a value, one that keeps an
    # operand for itself before the command begins.
    nested=(
        Nested(("exec",), value_opts=frozenset({"-u"}), operands=1),
        Nested(("run",), operands=1),
    ),
    gated_reason="stub: this invocation is not one of the proven-safe shapes",
    known_flags=frozenset(
        {"--syntax-check", "--list-tasks", "-i", "--inventory", "--tags", "--limit",
         "--mode"}
    ),
    value_flags=frozenset({"-i", "--inventory", "--tags", "--limit", "--mode"}),
    known_env=frozenset({"STUB_QUIET", "STUB_TARGET"}),
    grants=(
        # Two ways to be safe: it only parses, or the file it is given is one
        # that is read-only by construction.
        Grant(require_any=frozenset({"--syntax-check", "--list-tasks"})),
        Grant(operands=STUB_SAFE_FILE),
        # Operands that are paths, so `under` applies there too — the shape a
        # tool like `rm` needs, where the paths are the operands.
        Grant(path=("clean",), operands=under("/tmp", ".scratch")),
        # A flag whose value must match. A regex is right here: the value is a
        # keyword, so the raw string is exactly what matters.
        Grant(path=("apply",), flag_values=(("--mode", re.compile(r"^(dry-run|check)$")),)),
        # An assignment whose value is a path, so `under` resolves it before
        # comparing. A `^/tmp/` regex would accept `/tmp/../etc`. All three
        # location forms are used, so each is covered by the cases.
        Grant(
            path=("apply",),
            env_values=(
                (
                    "STUB_TARGET",
                    under("/tmp", "/home/*/scratch", re.compile(r"^/mnt/\w+/build$")),
                ),
            ),
        ),
    ),
    rules=(
        # Deliberately ask-first: deny must win on ranking, not on table order.
        Rule("ask", ("wipe",), "stub: an ask that deny outranks"),
        Rule("deny", ("wipe",), "stub: an act with no authorized use"),
        # A rule holds even where a grant would otherwise make the line silent.
        Rule("ask", ("touch",), "stub: a rule fires though a grant holds"),
        # The danger is in the environment, not on the command line.
        Rule("deny", (), "stub: an assignment with no authorized use",
             env=frozenset({"STUB_DANGER"})),
    ),
)

# How the engine reads a command line: splitting, quoting, parsing, ranking.
# Driven entirely by the `stubtool` fixture so that these stay true no matter
# what a project does to its own registry. Nothing here should name a real tool.
ENGINE_CASES: tuple[tuple[str, str], ...] = (
    # --- grants: proven safe, or not ---------------------------------------
    ("stubtool --syntax-check site.yml", "silent"),
    ("stubtool site.yml --syntax-check", "silent"),  # the flag is found last
    ("stubtool -i prod --syntax-check site.yml", "silent"),
    ("stubtool --tags foo --syntax-check deploy.yml", "silent"),
    ("stubtool --list-tasks deploy.yml", "silent"),
    ("stubtool run/validates.yaml", "silent"),  # operand pattern grant
    ("stubtool deploy.yml", "ask"),
    ("stubtool -i prod deploy.yml", "ask"),
    ("stubtool validates.yaml -e target=prod", "ask"),  # unaccounted flag
    # a value-taking flag swallows the next token, so it is not operative
    ("stubtool deploy.yml -i --syntax-check", "ask"),
    ("stubtool deploy.yml --tags --syntax-check", "ask"),
    ("stubtool deploy.yml --limit", "ask"),  # value flag with nothing after it
    # closed world: a flag that is not accounted for leaves it unproven
    ("stubtool deploy.yml -e msg='--syntax-check'", "ask"),
    ("stubtool --syntax-check deploy.yml --unknown", "ask"),
    # --- rules, and how they rank against grants ---------------------------
    ("stubtool wipe --syntax-check", "deny"),  # deny outranks ask and the grant
    ("stubtool touch --syntax-check", "ask"),  # a rule fires though a grant holds
    ("stubtool other --syntax-check", "silent"),  # no rule: the grant decides
    # --- environment assignments -------------------------------------------
    # An assignment before the command is environment, and is matched in its
    # own right rather than skipped.
    ("STUB_QUIET=1 stubtool --syntax-check site.yml", "silent"),  # accounted for
    ("STUB_UNKNOWN=1 stubtool --syntax-check site.yml", "ask"),  # closed world
    ("STUB_DANGER=1 stubtool --syntax-check site.yml", "deny"),  # rule beats grant
    ("STUB_QUIET=1 stubtool deploy.yml", "ask"),  # still not a proven shape
    ("STUB_TARGET=/tmp/x stubtool apply", "silent"),  # grant turns on the value
    ("STUB_TARGET=/prod stubtool apply", "ask"),
    ("stubtool apply", "ask"),  # the assignment is what made it safe
    # `under` resolves the path before comparing, so a grant on a location
    # cannot be satisfied by a string that merely starts with it
    ("STUB_TARGET=/tmp/../etc stubtool apply", "ask"),
    ("STUB_TARGET=/tmp/../../root stubtool apply", "ask"),
    ("STUB_TARGET=/tmp/a/../b stubtool apply", "silent"),  # still under /tmp
    ("STUB_TARGET=/tmp stubtool apply", "silent"),  # the directory itself
    ("STUB_TARGET=/tmpevil stubtool apply", "ask"),  # a prefix is not a parent
    ("STUB_TARGET=tmp/x stubtool apply", "ask"),  # relative: matches nothing
    ("STUB_TARGET=~/tmp stubtool apply", "ask"),  # ~ expands, and is not /tmp
    # a glob location: `*` does not cross a separator
    ("STUB_TARGET=/home/yann/scratch stubtool apply", "silent"),
    ("STUB_TARGET=/home/yann/scratch/build stubtool apply", "silent"),
    ("STUB_TARGET=/home/a/b/scratch stubtool apply", "ask"),
    ("STUB_TARGET=/home/yann/other stubtool apply", "ask"),
    # a regex location, matched against the whole resolved path
    ("STUB_TARGET=/mnt/data/build stubtool apply", "silent"),
    ("STUB_TARGET=/mnt/data/builds stubtool apply", "ask"),
    ("STUB_TARGET=/mnt/data/build/sub stubtool apply", "ask"),  # anchored, exact
    # resolution happens before matching for *every* form, not just the plain one
    ("STUB_TARGET=/home/yann/scratch/../../etc stubtool apply", "ask"),
    ("STUB_TARGET=/mnt/data/build/../../../etc stubtool apply", "ask"),
    # a flag whose value must match, where the raw string is what matters
    ("stubtool apply --mode dry-run", "silent"),
    ("stubtool apply --mode check", "silent"),
    ("stubtool apply --mode destroy", "ask"),
    ("stubtool apply --mode", "ask"),  # value flag with nothing after it
    # an assignment *after* the command name is an operand, not environment
    ("stubtool --syntax-check STUB_DANGER=1", "silent"),
    ("STUB_QUIET=1 STUB_TARGET=/tmp/x stubtool apply", "silent"),  # several
    # bash's append form is a command prefix too, and names the same variable
    ("STUB_DANGER+=1 stubtool --syntax-check site.yml", "deny"),
    ("STUB_QUIET+=1 stubtool --syntax-check site.yml", "silent"),
    # lower case is a valid shell name, so it is detected — but it is a
    # different variable, and for a gated tool the closed world catches it
    ("stub_danger=1 stubtool --syntax-check site.yml", "ask"),
    # --- wrappers: a program whose job is to run another program ------------
    # The wrapped command is reached and judged on its own terms.
    ("sudo stubtool deploy.yml", "ask"),
    ("sudo stubtool wipe", "deny"),
    ("env stubtool wipe", "deny"),
    ("time stubtool wipe", "deny"),
    ("nohup stubtool wipe", "deny"),
    ("xargs stubtool wipe", "deny"),
    # eval joins its arguments and runs the result, so the payload is
    # re-examined rather than stepped over — a quoted one is a single token
    # that names no tool, and stepping over it would go silent
    ("eval stubtool wipe", "deny"),
    ('eval "stubtool wipe"', "deny"),
    ("eval 'stubtool wipe'", "deny"),
    ('eval "stubtool --syntax-check a.yml"', "silent"),
    ('eval "make check"', "silent"),
    ('eval "sh -c \'stubtool wipe\'"', "deny"),  # nesting still terminates
    ("eval", "silent"),  # nothing to run
    ("sudo stubtool --syntax-check site.yml", "silent"),
    # the wrapper's own options are stepped over to find the command
    ("sudo -u deployer stubtool wipe", "deny"),
    ("sudo --user=deployer stubtool wipe", "deny"),
    ("nice -n 5 stubtool wipe", "deny"),
    ("timeout 30 stubtool wipe", "deny"),  # a positional the wrapper takes
    ("timeout -k 5 30 stubtool wipe", "deny"),
    ("xargs -n 1 stubtool wipe", "deny"),
    ("sudo --unknown-flag stubtool wipe", "deny"),  # unknown flags are skipped
    # wrappers stack, and assignments along the way still bind
    ("sudo env STUB_DANGER=1 stubtool --syntax-check a.yml", "deny"),
    ("sudo nice -n 5 stubtool wipe", "deny"),
    ("env STUB_QUIET=1 stubtool --syntax-check a.yml", "silent"),
    # a value-taking option really does consume its value: here `stubtool` is
    # the user to run `wipe` as, not a command, and there is nothing to gate
    ("sudo -u stubtool wipe", "silent"),
    # but an option we do not know is value-taking loses the thread, and a
    # wrapper we cannot see past asks rather than going quiet
    ("sudo --prompt-file /tmp/p stubtool wipe", "ask"),
    ("sudo sh -lc 'stubtool wipe'", "deny"),
    # a wrapper running something ungated says nothing
    ("sudo apt install ripgrep", "silent"),
    ("time make check", "silent"),
    # --- a shell asked to run a command line re-examines it -----------------
    ("sh -c 'stubtool wipe'", "deny"),
    ("bash -c 'stubtool deploy.yml'", "ask"),
    ("sh -c 'stubtool --syntax-check a.yml'", "silent"),
    ("bash -lc 'stubtool wipe'", "deny"),
    ("sh -c 'sh -c \"stubtool wipe\"'", "deny"),  # nesting terminates
    ("sh -c 'make check'", "silent"),
    # python's -c is another language, and is deliberately not read as shell
    ("python3 -c 'print(1)'", "silent"),
    # --- an unrecognised leader is silent by default ------------------------
    # A runner that is not in SHELL_WRAPPERS is not seen through — the fix is
    # to list it there, not to guess from a name appearing in the line, which
    # would gate the second case too.
    ("myrunner stubtool wipe", "silent"),
    # --- any_of, and a gated tool whose unproven case is a denial ----------
    ("stubcli server list", "silent"),  # the verb sits second
    ("stubcli security group rule list", "silent"),  # …and here, fourth
    ("stubcli catalog list", "silent"),
    ("stubcli server delete x", "deny"),  # no read verb: not a proven shape
    ("stubcli server frobnicate x", "deny"),  # unknown is gated, not silent
    ("stubcli", "deny"),  # a matcher on operands needs operands
    ("stubcli server list && stubcli server delete x", "deny"),  # judged apart
    # the one case the deny rule buys once judging is per-invocation: a read
    # verb that is a name rather than a verb
    ("stubcli server delete list", "deny"),
    # gated_verdict without grants: the tool that is always the operator's
    ("stubalways anything at all", "deny"),
    ("stubalways", "deny"),
    ("sudo stubalways --help", "deny"),  # a wrapper does not launder it
    ("grep stubtool README.md", "silent"),
    ("ls ../stubtool", "silent"),
    ("cat docs/env", "silent"),  # `env` is a wrapper name, and also a filename
    # --- a tool that hands off to another command ---------------------------
    # The outer invocation and the inner one are both judged; strongest wins.
    ("stubtool exec box stubtool wipe", "deny"),
    ("stubtool exec -u root box stubtool wipe", "deny"),  # its own option skipped
    ("stubtool exec box stubtool --syntax-check a.yml", "ask"),  # outer unproven
    ("stubtool exec box echo hi", "ask"),  # nothing gated inside
    ("stubtool build .", "ask"),  # no handoff declared at `build`
    # `run` keeps one operand for itself, then the command begins
    ("stubtool run image stubtool wipe", "deny"),  # command after the operand
    ("stubtool run stubtool wipe", "ask"),  # the operand is not read as a program
    ("stubtool run image --syntax-check a.yml", "ask"),  # no command, just args
    # --- operands that are paths, matched with `under` ----------------------
    # Every operand must match, and each is resolved before it is compared.
    ("stubtool clean /tmp/x", "silent"),
    ("stubtool clean /tmp/x /tmp/y", "silent"),
    ("stubtool clean .scratch/build", "silent"),  # a relative location
    ("stubtool clean ./.scratch/build", "silent"),
    ("stubtool clean /tmp/x /etc/passwd", "ask"),  # one operand outside
    ("stubtool clean /etc/passwd", "ask"),
    ("stubtool clean /tmp/../etc", "ask"),  # the traversal, on an operand
    ("stubtool clean .scratch/../secrets", "ask"),
    ("stubtool clean .scratch/a/../b", "silent"),  # resolves back inside
    ("stubtool clean", "ask"),  # an operand grant needs at least one
    # --- aliases: another name for the same tool ----------------------------
    ("stub2 wipe", "deny"),
    ("stub2 --syntax-check site.yml", "silent"),
    ("stub2 deploy.yml", "ask"),
    ("stub2 exec box stubtool wipe", "deny"),  # handoffs come with the alias
    ("stub2 run image stubtool wipe", "deny"),  # and the handoff comes with it
    ("sudo stub2 wipe", "deny"),  # and compose with a wrapper
    ("stub2x wipe", "silent"),  # whole-word, as with the primary name
    # --- quoting ------------------------------------------------------------
    ("echo 'stubtool deploy.yml'", "silent"),  # a whole command quoted is data
    # quotes are resolved before matching: this stays one operand, and one
    # operand carrying a space is not the plain word a grant will accept
    ("stubtool --syntax-check 'my file.yml'", "ask"),
    # a tool is matched on whole words, not on a prefix of its name
    ("stubtool-extra deploy.yml", "silent"),
    ("mystubtool deploy.yml", "silent"),
    # --- separators ---------------------------------------------------------
    ("cd /srv && stubtool run/validates.yaml", "silent"),
    ("stubtool deploy.yml && stubtool --syntax-check a.yml", "ask"),
    ("stubtool --syntax-check a.yml && stubtool deploy.yml", "ask"),
    ("stubtool --syntax-check a.yml && stubtool b.yml --syntax-check", "silent"),
    ("stubtool --syntax-check a.yml; stubtool deploy.yml", "ask"),
    ("stubtool --syntax-check a.yml | stubtool deploy.yml", "ask"),
    ("stubtool --syntax-check a.yml && stubtool wipe", "deny"),
    ("stubtool wipe && stubtool --syntax-check a.yml", "deny"),
    # --- newlines separate commands too -------------------------------------
    ("stubtool --syntax-check a.yml\nstubtool deploy.yml", "ask"),
    ("stubtool deploy.yml\nstubtool --syntax-check a.yml", "ask"),
    ("echo hi\nstubtool deploy.yml", "ask"),
    ("stubtool --syntax-check a.yml\n\n\nstubtool deploy.yml", "ask"),
    ("stubtool --syntax-check a.yml\nstubtool --list-tasks b.yml", "silent"),
    # a newline inside quotes is data: it must not start a new command
    ('echo "one\nstubtool deploy.yml"', "silent"),
    # --- backslash continuations are joined, as the shell joins them --------
    ("stubtool deploy.yml \\\n--syntax-check", "silent"),
    ("stubtool deploy.yml \\\n         --syntax-check", "silent"),
    ("stubtool \\\n--syntax-check site.yml", "silent"),
    # --- a comment is not part of the command -------------------------------
    ("stubtool deploy.yml  # --syntax-check next time", "ask"),
    # --- heredocs -----------------------------------------------------------
    # a body written to a file or a message is data, and dropped
    ("cat > play.yml <<'EOF'\nstubtool deploy.yml\nEOF", "silent"),
    # a body fed to an interpreter is what runs, so it is kept and judged
    ("bash <<'EOF'\nstubtool deploy.yml\nEOF", "ask"),
    ("sh <<SH\nstubtool deploy.yml\nSH", "ask"),
    # --- a line that cannot be parsed is unproven, not safe -----------------
    ("stubtool 'unbalanced", "ask"),
    ("echo 'unbalanced", "silent"),  # no registered tool named: no opinion
    # --- commands the registry says nothing about stay untouched ------------
    ("make check", "silent"),
    ("ls -la && rg TODO src/", "silent"),
    ("python3 scripts/build.py --force", "silent"),
    # --- a command inside a substitution or subshell is still a command -----
    ("echo $(stubtool wipe)", "deny"),
    ("echo $(stubtool --syntax-check a.yml)", "silent"),
    ("VAR=$(stubtool wipe)", "deny"),
    ("cat <(stubtool wipe)", "deny"),
    ("(stubtool wipe)", "deny"),
    ("(cd /srv && stubtool wipe)", "deny"),
    ("echo $(date)", "silent"),  # substitution of something ungated
    ("stubtool --syntax-check $(git rev-parse HEAD).yml", "silent"),
    # A quoted substitution never reaches the splitting above — it is still one
    # token — so it is read off the raw line instead, tracking quotes. Double
    # quotes and backticks run; single quotes do not.
    ('echo "$(stubtool wipe)"', "deny"),
    ("echo `stubtool wipe`", "deny"),
    ('stubtool --syntax-check "$(stubtool wipe)"', "deny"),
    ("echo '$(stubtool wipe)'", "silent"),  # literal: the shell runs nothing
    ("echo '`stubtool wipe`'", "silent"),
    # A heredoc fed to a *shell* is what runs, so it is judged; one fed to
    # another language is program text, and reading it as shell guesses wrong
    # in the direction that costs a refusal.
    ("bash <<'SH'\nstubtool wipe\nSH", "deny"),
    ("python3 - <<'PY'\nnote = \"see `stubtool wipe` for why\"\nPY", "silent"),
    ("python3 - <<'PY'\ns = s.replace(\"stubtool wipe\", \"x\")\nPY", "silent"),
    ('echo "$(stubtool --syntax-check a.yml)"', "silent"),  # nothing gated inside
    ('echo "$(echo $(stubtool wipe))"', "deny"),  # parentheses are counted
    ('echo "no substitution here"', "silent"),
)


def run(cases: tuple[tuple[str, str], ...], tools: dict[str, Tool], label: str) -> int:
    failures = 0
    for command, expected in cases:
        verdict = decide_bash(command, tools)
        got = verdict[0] if verdict else "silent"
        if got != expected:
            failures += 1
            print(f"FAIL  got {got:<7} want {expected:<7} {command!r}")
    print(f"{len(cases) - failures}/{len(cases)} {label} cases passed")
    return failures


def uncovered_rules() -> int:
    """Report rules and grants no case can reach. Intent nobody checks is
    intent nobody has.

    This is the mechanical half of "add a case for every rule you add": a rule
    that fires for nothing is either dead — a path or flag spelled wrong — or
    simply untested, and both look identical from the outside. Grants are held
    to the same bar for the failure that is easier to miss: an unreached grant
    over-prompts rather than under-prompts, so nothing goes wrong loudly and
    the safe shape you declared may never have worked at all.
    """
    global AUDIT
    AUDIT = set()
    try:
        for cases, tools in ((CASES, TOOLS), (ENGINE_CASES, registry(STUB, STUBCLI, STUBALWAYS))):
            for command, _ in cases:
                decide_bash(command, tools)
        tools = (*TOOLS.values(), STUB, STUBCLI, STUBALWAYS)
        declared = {rule for tool in tools for rule in tool.rules}
        declared |= {grant for tool in tools for grant in tool.grants or ()}
        missing = declared - AUDIT
    finally:
        AUDIT = None
    for item in sorted(missing, key=lambda i: (i.path, getattr(i, "verdict", ""))):
        kind = "rule" if isinstance(item, Rule) else "grant"
        flags = "".join(f" {flag}" for flag in sorted(getattr(item, "flags", None) or ()))
        path = " ".join(item.path) or "(any)"
        print(f"UNCOVERED  no case reaches {kind} {path}{flags}")
    print(f"{len(declared) - len(missing)}/{len(declared)} rules and grants covered")
    return len(missing)


VERDICTS = frozenset({"deny", "ask", "allow"})


def liveness() -> int:
    """Is the guard alive? Structure and contract only — no behaviour cases.

    Everything here fails silently in production: Claude Code logs a hook it
    could not run and proceeds to the permission rules, which are broad by
    design. So this is the half that belongs in a lint, and it deliberately
    asserts nothing about *verdicts* — those change with every project's
    registry, while these properties do not.
    """
    problems: list[str] = []

    if not os.access(__file__, os.X_OK):
        problems.append("not executable: Claude Code cannot run it as a hook")

    if not TOOLS:
        problems.append("the registry is empty: no tool would ever be judged")

    # Distinct tools, not registry keys: an alias would otherwise report
    # the same broken rule once per name it answers to.
    for tool in sorted({id(t): t for t in TOOLS.values()}.values(),
                       key=lambda t: t.name):
        name = tool.name
        for rule in tool.rules:
            where = f"{name} rule {' '.join(rule.path) or '(any)'}"
            if rule.verdict not in VERDICTS:
                problems.append(f"{where}: verdict {rule.verdict!r} is not one of "
                                f"{sorted(VERDICTS)}")
            if not rule.reason.strip():
                problems.append(f"{where}: no reason, so a prompt would say nothing")
            if rule.verdict == "allow" and tool.grants is None and not rule.flags:
                problems.append(f"{where}: an unconditional allow on a tool with no "
                                "grants waives the sandbox for the whole tool")
        if tool.gated_verdict is not None:
            if tool.gated_verdict not in VERDICTS:
                problems.append(f"{name}: gated_verdict {tool.gated_verdict!r} is "
                                f"not one of {sorted(VERDICTS)}")
            if not tool.gated_reason.strip():
                problems.append(f"{name}: gated_verdict with no gated_reason, so "
                                "the prompt or refusal would say nothing")
        for grant in tool.grants or ():
            if not (grant.path or grant.operands or grant.require_any
                    or grant.flag_values):
                problems.append(f"{name} grant: matches everything, so the tool is "
                                "not gated at all")

    # The contract, end to end: a payload in, a well-formed answer out.
    for payload, label in (
        ({"tool_name": "Bash", "tool_input": {"command": "true"}}, "a bash call"),
        ({"tool_name": "Read", "tool_input": {"file_path": "x"}}, "a non-bash call"),
        ({}, "an empty payload"),
    ):
        try:
            verdict = decide(str(payload.get("tool_name", "")),
                             payload.get("tool_input") or {})
        except Exception as exc:  # noqa: BLE001 — any failure here is the finding
            problems.append(f"{label} raised {exc!r} instead of returning a verdict")
            continue
        if verdict is not None and (
            not isinstance(verdict, tuple) or len(verdict) != 2
            or verdict[0] not in VERDICTS
        ):
            problems.append(f"{label} returned {verdict!r}, not None or (verdict, reason)")

    for problem in problems:
        print(f"DEAD  {problem}")
    tools = set(TOOLS.values())
    gated = [t for t in tools if t.rules or t.grants or t.gated_verdict]
    declared = sum(len(t.rules) + len(t.grants or ()) for t in gated)
    print(f"liveness: {len(gated)} gated tools, {declared} rules and grants, "
          f"{len(tools) - len(gated)} wrappers, "
          f"{'ok' if not problems else 'BROKEN'}")
    return len(problems)


def selftest() -> int:
    failures = liveness()
    failures += run(CASES, TOOLS, "registry")
    failures += run(ENGINE_CASES, registry(STUB, STUBCLI, STUBALWAYS), "engine")
    failures += uncovered_rules()
    return 1 if failures else 0


if __name__ == "__main__":
    if "--selftest" in sys.argv[1:]:
        sys.exit(selftest())
    if "--liveness" in sys.argv[1:]:
        sys.exit(1 if liveness() else 0)
    sys.exit(main())
