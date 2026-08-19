# frisk — specifications

An open-source Claude Code plugin: a parsing-based guard for the Bash tool.
Repository `cc-frisk`; plugin, CLI and skill namespace `frisk`.

## How to read this document

This specification states intent and constraints for an implementer (an AI,
typically Claude Code). It never prescribes implementation: no code, no file
layouts, no module names. Statements sit in one of three tiers:

- **Requirements** — written as "must". Decisions already taken, not open for
  reconsideration during implementation. Where a requirement exists because
  of a trade-off, the reasoning is given so it can be evaluated rather than
  merely obeyed.
- **Recommended defaults** — written as "should". Starting points the
  implementation may deviate from with reason.
- **Constraints of the environment** — facts about Claude Code, shells,
  interpreters and the distribution channel. Not decisions: stated, with the
  reason they matter, because discovering them mid-implementation is
  expensive. Facts marked *measured* were observed on a working prototype
  rather than taken from documentation. Facts that cannot be settled before
  implementation appear as lettered **open facts** with a pre-committed
  response per outcome.

Where this document says something must **not** happen, it is usually
because the failure is silent: a guard that is believed to be protecting a
boundary while protecting nothing produces no error — only, eventually, an
unprompted force-push. Silent failure is this project's central enemy, and
most of its architecture exists to convert silent failures into loud ones.

## 1. Goal

frisk is a guard for the Bash tool in Claude Code. It parses each command
line the agent proposes — resolving quoting, splitting compound commands,
walking through wrappers (`sudo`, `env`, `timeout`, …), shells invoked with
`-c`, `eval`, command substitutions and container handoffs — and judges
every command position it finds, returning a verdict Claude Code's native
permission rules cannot express. A native rule matches a command prefix; it
can say "allow git" or "deny `git push --force`" as *strings*, but it cannot
say "a force push however it is spelled", nor "this deploy tool is safe only
when a parse-only flag is present", nor see the force-push inside
`sudo git push -f` or `git commit -m "$(git push -f)"`. frisk decides on
parsed argv, one invocation at a time, so it can.

It is three things in one plugin:

- an **engine** — generic parsing and decision code, distributed and updated
  as plugin code, proven by its own shipped test suite;
- a **per-project configuration** — the rules, in a file owned by the
  project and never touched by the plugin once created, carrying its own
  test cases;
- a **skill** — maintenance assistance that turns every surprising verdict
  into a precise rule plus a reproducing test case, with every rule change
  remaining the operator's call.

Its audience is the operator who runs Claude Code on work they care about:
they want the agent to move fast through the harmless majority of commands
and to be stopped, or slowed to a question, at exactly the acts that destroy
work, rewrite published state, or reach infrastructure. In its optional
**secure mode**, frisk inverts its default posture and becomes a closed
world: anything its configuration has not spoken for is asked about or
denied — closing the **Bash surface** of permissive permission modes.
Only that surface: frisk sees no other tool, so file edits and the rest
keep their native handling (§6.1), and every claim frisk's
documentation makes must stay scoped to it.

frisk parses and judges; it never executes commands, never touches the
network, and never edits its own rules — rules change only through the
operator. It guards one boundary well rather than many broadly: depth of
structural analysis over breadth of per-tool integrations, a single
project's discipline over a global policy engine.

## 2. Environment and Context

Everything in this section is a constraint of the environment, researched
2026-08-16 against the Claude Code documentation, the history of a
prototype (see §3.1 — its code is deliberately not an input to the
implementation), and the public repositories named below. Reasons why each
fact matters are attached in place.

### 2.1 The hook contract

PreToolUse hooks run **first**, before permission evaluation, on every Bash
tool call. A hook receives a JSON payload on stdin — among its fields the
tool name, the command string, the working directory, a `session_id`, and a
`transcript_path` — and answers with one of three decisions, `allow`, `deny`
or `ask`, each carrying a reason, or with silence (no decision), which
hands the call to the normal permission flow (deny rules, then ask, then
allow, then the mode's default). Hook decisions do not bypass permission
rules: deny and ask rules are evaluated *regardless* of what the hook
returned — a matching deny blocks and a matching ask prompts even over a
hook `allow` — while a hook's own `deny` or `ask` similarly cannot be
lifted by a settings allow rule. These precedence claims are cited from
the platform documentation as of this section's research date; because
they are load-bearing and such behavior has shifted across platform
versions, they are open fact (b) below. This contract is what makes the
whole product possible: the guard is consulted on every Bash call, may
veto and release, and composes with the rule system rather than
replacing it.

Consequences the design rests on:

- **Hooks fail open.** A hook script that is missing, not executable, or
  crashes produces a non-blocking error: Claude Code logs it and proceeds as
  if the hook did not exist. Nothing inside the hook can catch its own
  failure to load. Every self-protection mechanism in §7 exists because of
  this fact.
- **Hooks are time-limited**, and an overrun is just another hook
  failure — fail open. The default limit's value is a verification-pass
  item (sources disagree on it, which is exactly why it is measured
  rather than asserted — and if it proves unmeasurable, the budget is
  sized against the *smallest* limit any consulted source claims); the
  engine must impose its own internal time budget sized far below
  whatever the measurement finds, covering *all*
  hook work — per-command decisions and the validation runs of
  §7.2/§7.3 alike — converting an overrun into a deny while it still
  can. An overrun is a §7.1 runtime failure (the machine-level dial
  reaches it; the config dial does not), it recurs on each call that
  overruns, and its deny names the overrun so the operator is not
  chasing a phantom rule. A validation run that overruns must not
  become a standing deny storm: validation state — at least
  session-scoped — records the outcome so subsequent calls report it
  without re-running the whole suite each time. A hard hang the budget
  cannot catch remains a named residue (§7.5).
- **A settings `ask` rule outranks a hook's `allow`** (the deny-first
  precedence above), so pairing guidance (§6) must forbid `ask` rules on
  tools the guard gates — otherwise every carve-out the configuration
  expresses is unreachable.
- **A hook's `deny` and `ask` cannot be overridden by settings `allow`
  rules**, which is why the guard can be paired with broad allows: the broad
  rule admits the tool, the guard claws back the dangerous acts.
- **Verdict reasons are shown to the model.** A deny or ask reason flows
  into Claude's context so it can adapt its next attempt. A reason is
  therefore steering text, not just an explanation for the operator —
  §6.2 makes requirements of this.
- **Session transcripts are JSONL files on disk** and the hook is told where
  the current one lives. This is what makes the deferred transcript-mining
  feature (§14) known-feasible, so deferring it is safe.

One more consequence, verified: **hooks can speak without blocking.** A
hook may emit a non-blocking, user-visible message (shown in the
transcript, not to the model) alongside or instead of a decision. This
is the surface the once-per-session notices of §5.4, §7.2 and §7.4
stand on.

Four properties carry more weight than their verification, and the
design treats them as open facts. The verification pass that settles
them is run by the implementing agent, inside the live Claude Code
environment it necessarily runs in, with three operator-provided
prerequisites named at handoff: consent to drive sessions in the
permissive modes, a scratch area outside the working directory for
fact (a)'s write attempt, and the platform version recorded with every
measurement. One outcome is pre-committed for the pass as a whole: **a
fact that cannot be measured is treated at the stricter branch of its
pre-committed response** and recorded as unmeasured — for (c) that
means the allow is withheld everywhere (the retirement path), which
stalls nothing: the parity bar is satisfied by the retirement clause
(§13).

- **(a)** *Measured during prototyping:* a hook `allow` does not merely skip
  the permission prompt — it also lifts Claude Code's bash safety heuristics
  and the working-directory sandbox, so an allowed command may write outside
  the project where a merely-permitted one is blocked. **What rests on it:**
  how §6 treats `allow` verdicts — as sandbox-waiving grants to be hedged
  and minimized, or as ordinary prompt-skips. **Pre-committed response:**
  the specification assumes the stronger consequence in either outcome —
  `allow` is always treated as sandbox-waiving (§6), so if the behavior has
  changed since measurement nothing breaks, and if it persists the design is
  already safe. The implementation must verify the current behavior when it
  builds §6's pairing guidance, and record what it found. (All
  verification-pass findings — this one, (b), (c), and the folded-in
  items — are recorded in a committed repository document, not left in
  a conversation.)
- **(b)** *Documented, version-sensitive:* settings `deny` and `ask` rules
  are evaluated regardless of a hook's decision — a matching `ask` prompts
  even over a hook `allow`. **What rests on it:** pairing rule 2 (§6.1),
  which forbids `ask` rules on guarded tools because they would make every
  carve-out unreachable. **Pre-committed response:** the same verification
  pass as (a) re-checks this on the current version. If confirmed, the
  specification stands as written. If instead a hook `allow` turns out to
  bypass settings ask/deny rules, pairing rule 2 demotes from requirement
  to hygiene guidance and nothing else moves: the deny backstop (§6.1
  rule 4) exists for the dead-guard case where no hook decision is
  returned at all, and §6.3's allow works in either world — the outcome
  changes only how cautious the pairing must be, never the guard's own
  behavior.
- **(c)** *Measured during prototyping:* Claude Code forces a permission
  prompt on command lines containing a command substitution (`$(…)` or
  backticks), and no permission rule can lift that prompt. The exact
  trigger condition is undocumented and version-sensitive. **What rests
  on it:** the entire reason `allow` exists (§6.3), and the substitution
  condition in §6.1's combination table. **Pre-committed response:** the
  engine models the trigger conservatively from the command text; where
  it cannot tell whether the platform would prompt, the allow is
  withheld — costing a prompt, never a fence. The verification pass
  measures the current trigger and records it, and it is sequenced
  *before* the allow machinery of §6.3 is built — this measurement is
  the go/no-go for the whole apparatus, and nothing should be built
  that its outcome would retire; if the platform stops
  prompting on substitutions altogether, the allow verdict loses its
  purpose and is retired to silence — starter allow declaration and
  hedge machinery idling with it — which changes convenience, not
  safety.
- **(d)** *Documented in outline, version-sensitive in detail:* a hook's
  `deny` blocks and its `ask` prompts **in every permission mode**,
  including the permissive ones. **What rests on it:** §1's claim that
  secure mode closes the Bash surface of permissive modes, and §6.1's
  "only gate left" reasoning — mode precedence over hook decisions is a
  different question from open fact (b)'s settings-rule precedence.
  **Pre-committed response:** hook `deny` is assumed mode-proof — a
  platform mode that overrode even a hook deny is a mode nothing can
  gate, and the documentation would name it unsupported rather than
  pretend. If a mode is found to swallow hook `ask` (approving instead
  of prompting), then in that mode ask degrades to silence, and the
  secure-mode guidance for operators of that mode recommends the deny
  default instead — the closed world survives, the question form does
  not. The verification pass measures both directions per mode,
  absorbing the mode-taxonomy check of §6.1.

The verification pass's full inventory, consolidated so no scattered
item is missed — each row's pre-committed response lives at the cited
place:

1. Open fact (a): hook allow's sandbox waiver (§2.1).
2. Open fact (b): settings deny/ask precedence over hook decisions
   (§2.1).
3. Open fact (c): the substitution-prompt trigger — the go/no-go,
   sequenced before any allow machinery (§2.1).
4. Open fact (d): hook deny/ask survival per permission mode, absorbing
   the mode-taxonomy check (§2.1, §6.1).
5. The platform hook-timeout default, sizing the internal budget
   (§2.1).
6. The per-plugin persistent data directory (§2.2).
7. Plugin-configuration delivery to hooks as environment variables
   (§2.2).
8. Project-recommended-plugin prompting behavior (§2.2).
9. Settings deny/ask enforcement under each permissive mode (§6.1).
10. Prefix-rule word-boundary behavior (§6.1 rule 1).
11. The platform's built-in read-only command handling (§6.1 rule 1).
12. The Python-floor table of OS-shipped interpreters (§3.1).
13. Whether the Bash tool persists shell state across tool calls
    (§4.4 — decides the reach of the export blind spot).

### 2.2 The plugin system

- A plugin is a git-distributed directory with a manifest, and may bundle
  hooks, skills, agents and commands. Hooks declared by a plugin behave
  identically to hooks declared in settings — same payload, same decisions,
  same fail-open — and run whenever the plugin is enabled.
- Plugins are installed from **marketplaces**; a repository can be its own
  marketplace, so `cc-frisk` needs no third-party channel. Installed
  plugins are copied into a **per-version cache** directory: plugin code
  must treat its own location as read-only and version-unstable. A
  persistent per-plugin data directory exists and survives updates
  (part of the verification pass, pre-committed: if the current
  platform offers no such home, durable state degrades to
  session-scoped state — validation re-runs once per session rather
  than once per change, once-per-session notices still work within
  their session, and `status`'s last-validation answer reaches back
  only as far as the session — a performance-and-reach cost, never a
  correctness or safety one). The
  cache lives at a discoverable on-disk location and the installed
  version is recorded in user-level state, so code running *outside* a
  plugin hook — the CLI (§9), the sentinel (§7.4) — can feasibly locate
  the installed engine; the mechanism is free, but locating-or-failing-
  loudly is a requirement on both. Zip-archive install sources are
  versioned by SHA-256 digest (or an explicit pin in the marketplace
  entry) — the documented fact §11's attestable-release recommendation
  stands on.
- Hook commands can locate the plugin through `${CLAUDE_PLUGIN_ROOT}` and
  the project through `${CLAUDE_PROJECT_DIR}` — both exist only when Claude
  Code invokes the hook, which is why anything runnable from a terminal or
  CI (§8, §9) must not depend on them.
- Plugin **user configuration** is stored user-globally only; Claude Code
  deliberately ignores project-scope plugin-config entries, so a cloned
  repository cannot inject values into hook commands. Values reach hooks as
  environment variables. Consequence: any frisk option carried this way
  (§7's failure-policy relaxation) is machine-wide, never per-project — and
  per-project options must live in frisk's own config file instead.
  The three sources that *are* read, in descending precedence: **managed
  settings** (organization-controlled policy), the `--settings`
  flag/inline settings, and the user's own settings file. Consequence:
  every frisk option carried as plugin configuration is automatically
  org-governable — an organization can deliver values fleet-wide and
  those values *outrank* the user's, so a policy like the failure-mode
  relaxation of §7.1 can be organizationally pinned. This delivery
  mechanism is itself part of the verification pass, with a
  pre-committed response: if values do not reach hooks as documented on
  the current version, the machine-level dial of §7.1 simply has no
  carrier — the engine default (deny) stands unrelaxed, stricter and
  safe, until the platform offers a carrier again. Managed settings
  also carry permission rules (deny backstops included) and plugin
  enablement.
- A committed project settings file **can enable but cannot install** a
  plugin: for a cloner who lacks it, the entry cannot be relied on to
  prompt or install — the documented behavior is silent skipping, and no
  refusal mechanism exists (whether some versions prompt for
  project-recommended plugins is folded into the implementation's
  verification pass, alongside open fact (a) — and the response is
  pre-committed either way: the sentinel remains; a prompt, if one
  exists, softens its rationale without replacing it). The guard cannot make
  itself present on a machine; §7's sentinel exists because of this
  fact.
- Plugin installation cannot run build steps (lifecycle scripts are
  blocked). Nothing in the plugin may require compilation or dependency
  installation to function.

### 2.3 Runtime

- `python3` ships with stock Linux distributions and WSL; on macOS it
  arrives with the Xcode Command Line Tools — the base system carries
  only a stub that fails (or triggers an install dialog) until they are
  installed, so a fresh Mac is a machine where the guard's interpreter
  is *absent* and only the sentinel (§7.4), if adopted, says so. Its
  version lags current Python by years on common systems, and on native
  Windows its presence is not dependable. A POSIX shell, by contrast,
  necessarily exists wherever the Bash tool runs. This asymmetry drives two
  decisions: the engine is Python with a conservative version floor (§3.1),
  and the sentinel that checks for the engine is shell (§7.4).
- Hook latency is bounded by usability, not by a hard limit: the guard runs
  on every Bash call, inside tool calls that take seconds. Tens of
  milliseconds of interpreter startup are noise; anything requiring a
  daemon or a compilation step to be fast enough is out of proportion.

### 2.4 Prior art

Five tools occupy the same space; none combines structural depth with plugin
packaging, which is frisk's position. Stated here so the implementer knows
what exists and what frisk deliberately is not:

- **cc-bash-guard** — closest prior art: external YAML policy, rule-local
  tests, a verify/explain CLI, and ~10 built-in per-tool semantic parsers.
  Breadth of ready-made parsers; frisk's differentiation is generic
  structural depth (wrapper/substitution/nested-shell walking, closed-world
  flag enumeration applicable to any tool) and the operator-owned Python
  config.
- **claude-code-auto-approve** — per-segment matching of compound commands
  against existing permission rules; no semantic parsing, no config.
- **claude-permissions-plugin** — plugin-packaged, but promotes
  frequently-seen commands into the allow list; the opposite instinct.
- **claude-code-permissions** — regex deny-patterns over split subcommands;
  single global hook, no tests.
- **claude-code-execpolicy** — argv-position matching against an
  execpolicy-style ruleset; allow-only, composes with other guards.

## 3. Core Model

The architecture, with the reasoning that produced it; each subsection
carries its why, because the why is what a reviewer or implementer can
evaluate when a requirement meets reality.

### 3.1 Three parts, one trust split

frisk must be split into an **engine**, a **per-project configuration**, and
a **skill**, because the three change for different reasons under different
authority:

- The **engine** — parsing, walking, judging, self-testing — is generic
  code, identical for every user, distributed and updated through the
  plugin channel, and proven by the test suite that ships and runs with it
  (§8.1). Users receive it proven; they never re-prove it.
- The **configuration** is policy: which tools are registered, which acts
  are gated, which shapes are proven safe, plus the project's own test
  cases. It is created once in the project's config directory (on the
  operator's request, §5.4) and **must never be touched by an unattended
  write afterwards** (§5.1 names the two operator-gated exceptions) — it
  is the operator's boundary, under the operator's version control, and an
  update channel that could rewrite it would be an update channel that
  could rewrite the boundary.
- The **skill** is the assistant between them: it scaffolds, explains,
  migrates, and turns surprises into rules and cases (§10) — always by
  proposing to the operator, never by deciding.

The engine must be **Python, standard library only, zero dependencies**.
The reasoning is a safety argument before a convenience one: hooks fail
open (§2.1), so the interpreter's *presence* on the machine is a safety
property, and `python3` is the most dependable interpreter on the
supported platforms (§2.3). Zero dependencies keeps the audit surface equal to the
repository — this code sits in the permission path, and what users can
read is what they are trusting — and keeps installation build-free as the
channel requires (§2.2). The engine must run on a conservative interpreter
floor: features from recent Python versions are reimplemented rather than
required — and the reimplementation is the *only* implementation, on every
interpreter: no conditional dispatch to native equivalents where they
exist, because verdicts must be identical across the supported range and
a dual path would make gate two vouch for whichever branch the testing
machine happens to run, for a performance gain that is nanoseconds
against a millisecond budget. The operator's `python3` is whatever their
OS shipped —
and a floor guessed too high fails in the worst direction, since an engine
the shipped interpreter cannot parse fails open (§2.1) and only the
optional sentinel would notice. The floor should be **3.9** (what current
macOS command-line tools, RHEL 9 and every current LTS distribution
ship, as researched at this document's date); the implementation
re-verifies that table before committing to it and may move the floor
with reason.
The parsing technique itself is implementation-internal: nothing outside
the engine may depend on how a command line is analyzed, so a stronger
parser can replace the initial one without touching config or contract.

The engine, the API and the plugin are designed **fresh**. A prototype of
this guard existed and was used in real projects; its lessons — the
decision model below, the fail directions, the behavioral corpus of §8.1 —
are fully serialized into this document, which — together with one
companion artifact, the adjudicated behavior corpus of §8.1, delivered
as reference data at handoff — is the sole carrier; without the corpus
the parity bar of §13 has no yardstick and cannot be declared met. The
prototype's code and API shapes are *deliberately* not provided and not
inputs to the implementation — this is not a missing reference: they grew
inside one file under per-project constraints, and carrying them forward
would freeze accidental design into a public product. Nothing beyond this
document and the corpus is needed or intended.

### 3.2 The decision model

The engine's job on each Bash call: analyze the command line into every
**invocation** it contains — through separators, quoting, wrappers,
substitutions and handoffs (§4) — judge each invocation independently, and
combine the results. Deny then ask are strongest and always win;
how `allow` and silence aggregate over a line is governed by the
combination table of §6.1, which is authoritative wherever this
section's summary and that table could be read apart.

- **Verdicts** form a strict ranking: **deny** over **ask** over **allow**
  over **silence**. Deny is for acts with no authorized use; ask is for
  outward writes and destroyed work; allow is an exceptional, hedged grant
  (§6.3); silence means "no opinion" and hands the call to the permission
  rules and mode. The ranking must be order-free *within one declaration
  source*: reordering the rules inside a source never changes a verdict.
  Across sources — engine defaults, imported collections, the
  operator's own declarations — §3.4's explicit precedence decides, and
  nothing else.
- **Each invocation is judged alone.** A safe command must never vouch for
  its neighbour in the same line; the safe half of
  `tool --check a && tool deploy b` says nothing about the other half. An
  `ask` or `deny` anywhere in a line must also withhold any `allow` earned
  elsewhere in it: a grant speaks for one invocation, never for the line.
- **Two rule kinds, by which side of a tool is finite.** A tool that is
  safe by default with a listable set of dangerous acts (git, docker)
  declares **rules**, checked *existentially*: naming an act gates it,
  every *subcommand and flag* unnamed falls through silently. A tool that
  is dangerous by default with a small provable safe set (deploy and
  infrastructure tools) declares **grants**, checked *universally and
  closed-world*: every invocation must match a proven-safe shape — flags
  enumerated, values constrained — and anything else gets the tool's
  default verdict. A tool is **gated** exactly when it declares grants
  and/or closed worlds — distinct from *registered* (known to the engine
  at all) and *rule-bearing* (carrying any rule); the three terms are
  used with these meanings throughout. The closed world is the
  load-bearing property: a flag or value nobody considered can only move
  a verdict *toward* the stricter outcome, never away from it.
  **Environment assignments are closed-world for every registered
  tool**, not only gated ones: a leading assignment that is neither on
  the engine's universal benign list (the display/locale class — `LC_*`,
  `LANG`, `TZ`, `NO_COLOR` and kin, variables that cannot direct
  execution; an engine default layer like the others, enumerated and
  shadowable, §3.4) nor accounted for by the tool's declaration
  (by name, optionally value-conditioned — `GIT_PAGER` acceptable as
  `cat`, asking otherwise) is an explicit **ask**, citing the
  assignment. The reasoning is the closed-world reasoning: dangerous
  assignments cannot be enumerated (`GIT_SSH_COMMAND=… git fetch` runs
  an arbitrary program, and git alone has dozens of siblings), while a
  tool's benign ones are finite and the surprise loop grows them.
  Assignments ahead of an *unregistered* tool stay with the tool's own
  posture — silence in the default posture, the global default in
  secure mode — because an opinion the guard does not have about `make`
  should not appear because of a harmless `DEBUG=1`. A tool may declare
  both rules and grants; rules hold even where a grant
  would otherwise release.
- **Matchers are uniform.** Wherever the configuration constrains a value —
  a flag's value, an environment assignment's value, an operand — the same
  matcher forms apply: patterns for values where the raw string is what
  matters, path matchers that resolve traversals (`..`, `~`) *before*
  comparing so that a boundary cannot be escaped textually — with fixed
  cross-form semantics: a relative value matches a relative boundary
  (textually, after resolution) and an absolute value an absolute one,
  while a relative value never satisfies an absolute boundary nor the
  reverse (no resolution base is invented; the mismatch is unproven,
  the stricter outcome), and a directory change earlier in the judged
  line (`cd /elsewhere && tool ./x`) makes every later relative *path*
  match unproven — path matchers only; pattern and predicate matchers
  are untouched, and the poisoning is deliberately **lexical, not
  scope-aware**: it applies to everything after the `cd` on the line,
  subshell nesting included, even though real shell semantics isolate a
  subshell's directory change — `(cd build && make) && tool ./x` is
  poisoned for `./x` although the outer base never moved. The cost is a
  prompt on that rare shape; the alternative — tracking directory scope
  — would change observable verdicts and is therefore a possible future
  specification change, never implementation freedom. Matcher evaluation is
  therefore **three-valued** — satisfied, unsatisfied, or *unproven* —
  and unproven always moves stricter by role: it fails a grant
  condition (no release), and it fires a deny/ask rule's condition at
  ask strength (the gated value cannot be ruled out); it never reads as
  a plain "false" that lets a rule go silent. And a quantified operand
  matcher stated over "every operand" requires **at least one** operand
  to satisfy it — empty operands are never vacuously granted (a command
  acting on nothing has not proven what it acts on; the distinct
  "no operands allowed" grant form of §5.2 covers the empty case
  deliberately). Predicates for
  everything else, and quantifiers over operand lists ("every operand" /
  "at least one operand"). Value conditions must be available to deny and
  ask rules, not only to grants — prototyping could deny on a flag's
  presence but not on its value, and closing that asymmetry is one reason
  the API is designed fresh (§3.1).
- **Per-tool default verdicts.** Each registered tool has a defined outcome
  for "no rule matched, no grant held": silent for a rules-only tool, ask
  for a granted tool, or an explicit verdict ("every use of this one is the
  operator's" is a tool with a deny default and nothing else). Every
  non-silent verdict must carry a reason **and a citation** — what was
  read, which rule decided — because a wrong verdict that cannot be traced
  to a line of configuration cannot be reported, and reports are what the
  maintenance loop (§10) runs on.
- **Secure mode** extends the same idea to the whole command line: a
  configurable global default verdict (ask or deny) that replaces every
  *implicit* silence. It applies to command positions resolving to no
  registered tool, and equally to registered tools whose default verdict
  was left unset — in secure mode there is no silent outcome anywhere
  unless the configuration made it explicit: an explicitly declared silent
  default, or a grant that holds (a holding grant is always silence — the
  proven-safe shape is the point of declaring it). The engine's default
  layers (§3.4) are declarations like any others — reviewable,
  enumerated (§12) and shadowable — so in secure mode they keep their
  declared default verdicts: `cat foo` stays silent, and an operator who
  wants it gated shadows the default away. It must be off by
  default: it is only livable with a substantial base of proven-safe
  common commands, which is rule-collection territory (§14), and until then it
  is a deliberate tool for operators who want a closed world and accept
  teaching it their environment. It is an engine-level capability from the
  start because it shapes the decision model and could not be retrofitted.

### 3.3 Fail directions

A single principle, applied everywhere, stated once here and assumed by
every later section: **every uncertainty moves the verdict toward the
stricter outcome, and every death of the guard itself is made loud.**
A line that cannot be parsed is unproven, not safe. A wrapper that cannot
be seen through asks. A malformed invocation, an unknown flag on a gated
tool, an environment assignment accounted for by nothing (§3.2):
stricter, never quieter. And
when the guard itself fails — config unloadable, cases failing, engine
erroring — the answer is a deny that says what broke (§7), because a
boundary that fails by proceeding plausibly is the silent failure this
document exists to prevent. The one residue that cannot be caught from
inside — the guard never executing at all — is covered from outside, by
the layered mechanisms of §7.4, and the coverage map of who catches what
is kept explicit (§7.5).

### 3.4 Composition and layering

Configuration is layered, and one primitive drives all of it: **per-name
shadowing** — for any tool name, the most specific declaration decides,
either by replacing what sits beneath it or by amending it.

- The engine ships default layers of universal shell knowledge: the
  **shell wrappers** — programs whose job is to run other programs,
  through which every judged command is walked — and the minimal
  **baseline read tools** whose motivation lives with the allow doctrine
  (§6.3). This knowledge is universal shell behavior, not
  project policy, which is why it lives engine-side; but a config
  declaration for the same name must win: promoting a wrapper to a
  rule-bearing tool (a need demonstrated during prototyping),
  correcting its argument arity, adding an exotic runner, or effectively
  removing an entry whose name collides with a project binary. Overriding
  takes two forms and both are required: **replace** (the new declaration
  stands entirely in place of the old) and **update** (the declaration is
  amended — and an update must be able to *remove* as well as add: drop a
  flag from an arity list, drop a rule, not only append). Promotion,
  addition and removal all reduce to these two.
- Rule sets must be **composable, importable units** from the start: a
  configuration is built from selectable parts (the scaffold's starter
  registry is simply the first such part), so that shipped, community,
  organization or personal collections (§14) can later be adopted and
  overridden without engine changes — wrapper declarations included, since
  collections carry tools of every kind. The replace/update semantics
  above apply to a collection's entries exactly as to the engine's wrapper
  defaults: adopting a collection and then trimming it — removing one of
  its rules, narrowing one of its grants — must be expressible. How a
  collection and the operator's own declarations merge — copy at
  initialization, live import, precedence details — is deliberately left
  to implementation, bounded by three invariants: sources compose in an
  explicit, total order — the order the configuration declares them,
  later overriding earlier, so collection-versus-collection conflicts
  are decided by the operator's declared ordering and never by accident;
  the operator's own declarations always come last and always win; and
  whatever the mechanism, the effective registry must be inspectable
  (§9) so composition never hides a rule. Why composability exists from
  the start rather than arriving with external collections: the
  scaffold's own starter registry is the first collection — a unit the
  config adopts and may trim — so the mechanism has a consumer from day
  one, and a single-source implementation suffices before 1.0.

### 3.5 The compatibility contract

Plugin updates arrive through the marketplace, potentially silently, against
a config file the plugin does not own and cannot see until it runs.
Three layers keep that safe:

1. The **config-facing API** — the constructors, matcher helpers and
   composition mechanism the config uses — is the stability boundary,
   versioned semver on the plugin: breaking changes to it only on a major
   version. Engine internals stay free to change beneath it.
2. The configuration **declares which API generation it was written
   against** (the scaffold writes this). The engine speaks a
   **contiguous range** of generations, not necessarily one: it should
   keep accepting recent older generations — an addition of new
   capabilities must not strand configs that don't use them — and may
   carry internal fallbacks or migrations where a change permits, with a
   generation moving through supported → deprecated (accepted, with a
   visible nudge toward migration) → dropped. Outside the accepted
   range, the engine must fail closed with a message pointing at the
   skill's migration assistance — never guess: misinterpreting a config
   is worse than denying everything, because it is silent and plausible
   where deny-all is loud.
3. The project's own cases are its upgrade test, **enforced**: when the
   engine version changes, the project suite re-runs before anything is
   judged (§7.3), so an update that flips any recorded verdict becomes a
   loud deny naming the failing case, not a silently moved boundary.

The API must also satisfy a legibility requirement, stated here because it
constrains the API design as strongly as any mechanism: the configuration
surface must read clearly to an operator who does not know Python —
declarative in feel, minimal in ceremony — because the config is the
document the operator reviews when they decide what their boundary is, and
a boundary that cannot be read is not the operator's.

## 4. The Decision Engine

The engine receives the command string of a Bash tool call and returns one
verdict or silence. To do that it must find **every invocation** the string
contains and judge each alone (§3.2). The requirements in this section are
behavioral: each names something the analysis must get right, with the
failure that motivates it. The analysis technique is free (§3.1) — but a
technique that cannot satisfy one of these behaviors is the wrong
technique, and each behavior below is asserted by the engine's shipped test
suite (§8.1). Precision here is deliberate: this is the section where a
silent gap becomes an unprompted destructive command.

### 4.1 Reading the line

- **Quoting is resolved by real tokenization, never by pattern-matching the
  raw string.** Raw matching is unsound in both directions:
  `git commit -m 'fix the --amend bug'` is not an amend, and a flag hidden
  in a quoted substitution is invisible to any regex that respects quotes.
- **Compound commands are split at every separator** — `&&`, `||`, `;`,
  `|`, `|&`, `&` and **newlines**, including runs of them and blank lines.
  The newline is load-bearing, not an afterthought: multiline command
  strings are routine, and an engine that misses it reads
  `git status\ngit push --force` as a single `git status` invocation with
  extra operands — no push rule can fire. A separator inside quotes is
  data, not a separator: a multiline commit message is one argument.
- **Backslash-line continuations are joined before splitting**, as the
  shell joins them — otherwise `git push \`⏎`--force` hides the flag
  inside a mangled operand.
- **Comments are not part of the command.** `tool a.yml # --check next
  time` contains no `--check`.
- **A line that cannot be parsed is unproven — not the deny of §7,
  which is reserved for the guard's own failures — and never silent
  approval of whatever it might contain.** Outcome: in the default posture, ask if a
  *rule-bearing* tool's name — one with rules, grants or a non-silent
  default verdict — appears as a whole whitespace-delimited word on the
  raw line, words compared by basename so a path spelling like
  `/usr/bin/git` does not evade the scan, silence otherwise (wrapper
  and baseline-read names are no signal: they appear on too many
  ordinary lines, and scanning for them would make the fallback fire
  constantly); in
  secure mode (§3.2), the global default verdict applies regardless.

### 4.2 What binds to an invocation

- **Leading environment assignments** (`FOO=bar cmd`, including the
  append form `FOO+=bar` and quoted values `FOO="bar baz"`; names are the
  shell's, so lower-case names are assignments too, and matching against
  declared names is case-sensitive) bind to the command that follows and
  must be matchable *as conditions in their own right*, not merely
  skipped: an assignment can outrank any flag in danger —
  `GIT_SSH_COMMAND=…` runs an arbitrary program during a fetch. An
  assignment-shaped token *after* the command name is an operand, not
  environment. The `export` spelling is the same danger one segment
  removed: `export GIT_SSH_COMMAND=…; git fetch` poisons the later
  command without any prefix for the closed world to see. Required, on
  the 1.0 staging of §13: a segment of the form `export NAME=value
  [NAME2=value2 …]` establishes those assignments for **every
  subsequent invocation in the same tool call**, entering exactly the
  accounting of §3.2 — benign list, per-tool accounted sets, otherwise
  ask at the consuming registered command; unregistered consumers keep
  their posture. Until it ships, the honesty documentation names the
  gap. The export *family's* edges — `declare -x`, `unset`, a valueless
  `export NAME` re-exporting something set earlier — are declared blind
  spots (§4.4) rather than half-modeled. Exotic assignment forms (array
  syntax and other shell-specific shapes) may gain full modeling later;
  until then they must land in the stricter direction, never be misread
  as something harmless.
- **Options that precede a subcommand are recognized per the tool's
  declaration and stripped**, so the subcommand lands where rules expect
  it — undeclared, `git -C dir push` parses as operands `dir push` and no
  push rule matches. Which were used, *and with what values*, is
  remembered: the allow hedges (§6.3) need the former, and rule and grant
  conditions must be able to constrain the latter like any flag value —
  "pushing is fine only for repositories under this directory" is a rule
  on `-C`'s value.
- **Flags are found wherever they sit** — the deciding token is often
  last, because that is where the agent tends to put it. Three arities
  are declarable and parsed: bare (a switch), value-required
  (`--flag=value`, or value-in-next-token), and **value-optional** — some
  hand-rolled CLIs accept both `--argument custom --check` and
  `--argument --check`, taking a default when the next token looks like a
  flag; the declaration model must be able to say so, since reading a
  value-optional flag as value-required can swallow the very token that
  decides the verdict. `--` is recognized as the end-of-options marker
  and is itself matchable (it is the explicit "operand is a path" signal
  some rules key on); a declared value-taking flag with nothing after it
  makes the invocation malformed, which is unproven, not safe. Arity
  fail directions split by context, and getting the split wrong recreates
  a real hole: **within a gated tool's accounted flags, arity must be
  declared complete** — an accounted value-taking flag whose arity is
  under-declared lets its value look operative, and when that value is a
  safe-marker flag (`ansible-playbook deploy.yml -i --syntax-check`,
  where `--syntax-check` is really `-i`'s inventory string) it falsely
  satisfies a grant and a real deploy passes as a parse-only run — the
  worst direction. Over-declaring a tool's flag merely swallows an
  operand. Wholly *unaccounted* flags are the closed world's problem and
  fail stricter on their own; and for wrappers and handoffs the
  directions invert (an unknown value-taking option loses the walk,
  which asks — §4.3, §4.4). The tests must cover the declared set.
- **A tool is recognized by the basename of its command word**, on the
  whole name only, never a prefix or substring — `git` and `/usr/bin/git`
  are the same tool, `.venv/bin/ansible-playbook` is `ansible-playbook`;
  but `git-crypt` is not git, and a tool's name used as an ordinary word
  or directory is not the tool. Aliases are fully equivalent names for
  the same declaration. A tool may also be declared **by
  project-relative path** (`tools/deploy.py`), matched with the path
  machinery of §3.2 — traversals resolved before comparing, so
  `./tools/deploy.py` and `tools/../tools/deploy.py` both hit, the
  interpreter-run form included — and a path declaration is more
  specific than a basename one under §3.4's most-specific-wins rule.
  This matters most in secure mode, where a basename registration would
  let a grant written for the operator's script release a same-named
  file anywhere; a path declaration attaches policy to the file the
  operator meant. After an in-line `cd`, a relative spelling of a
  path-declared tool is unproven and recognition degrades stricter,
  like any path match. Identity remains textual: copying the file
  elsewhere evades any declaration, path or basename — the existing
  non-adversarial scope (§15), stated so nothing implies content
  pinning.
- **A shell variable reference is an unknown at decision time**, and is
  treated by one rule: *an unknown never satisfies a positive condition,
  and never weakens a boundary.* A value carrying `$FOO` or `${FOO}` (in
  a flag value, an assignment, an operand) cannot prove a grant
  condition — on a gated tool it leaves the invocation unproven. Meeting
  a value-conditioned deny/ask *rule*, a dynamic value fires the rule at
  **ask** strength: the gated value cannot be proven present (so no
  deny), but it cannot be ruled out either (so never silence) — the
  stricter-but-honest middle, matching the path matcher's treatment of
  unresolvable forms (§3.2). On positions nothing constrains, it is an
  opaque token like any other word (`echo $FOO` stays silent in the
  default posture). A
  variable in *command position* (`$RUNNER deploy`, `$(${FOO})`) is a
  command that cannot be named: inside a wrapper or handoff it asks, in
  secure mode it gets the global default, and in the default posture
  outside those contexts it is silence — the same no-name-scanning
  reasoning as §4.3. This policy must be stated in the operator
  documentation (§12): "why did my `$VAR` command ask?" needs a
  documented answer. The unknown-token rule has a wider sibling on
  gated tools: **a token a gated invocation carries that the engine
  cannot read as a plain word** — an operand or value containing
  whitespace, glob characters, or the like — **leaves the invocation
  unproven** (§3.3), whatever the grants would otherwise say:
  `deploy --syntax-check 'my file.yml'` asks, because one operand
  carrying a space is not the plain word a grant accepts. Grants prove
  ordinary shapes; a strange token is not ordinary. The rule judges
  tokens **as they stand after structural analysis**: an *unquoted*
  substitution never reaches a matcher position at all — §4.3 splits it
  out and judges it as the command it is, so
  `deploy --syntax-check $(git rev-parse HEAD).yml` stays silent when
  its pieces do — while a quoted one survives inside a token and is the
  dynamic-token case above.
- **A registered tool run through an interpreter is still that tool**:
  `python3 tools/deploy.py` is judged as `deploy.py`'s registration if one
  exists. Which interpreters are walked this way is an engine default
  layer like the wrappers (§3.4): shadowable, and enumerated in the
  operator documentation (§12) with the rest. A walked interpreter with
  **no `-c`/`-e` payload and no file operand** — `curl url | python3`,
  the installer idiom in another language — is executing a program the
  line cannot show, and **asks**, exactly as the bare piped shell does
  (§4.3): the reasoning transfers unchanged.

### 4.3 Seeing through

A line can hide a command inside another one; every hiding place below
must be walked through, and every command position found is judged.
Recursion through these mechanisms must be depth-bounded, terminating on
pathologically nested input; a line cut short by the bound is treated as
§4.1's unparseable line — unproven, never silently truncated.

- **Wrappers.** A registered wrapper (§3.4) contributes its own verdict if
  it has one, and the walk continues to what it runs: `sudo git push
  --force` is a sudo *and* a denied push. The wrapper's own value-taking
  options and kept positional operands are stepped over per its
  declaration (`timeout 30 cmd`, `sudo -u deployer cmd`); wrappers stack;
  assignments encountered along the walk keep binding — and they are
  accounted against the declaration of the command that ultimately
  consumes them — and when the check fails, the citation is attributed
  to that consuming command's closed world, naming the assignment (the
  wrapper's own accounting is an additional acceptance path, never an
  attribution target), which is what the surprise loop drafts its rule
  from. The consuming command is the innermost judged command the walk
  reaches, whose
  registration decides whether the closed world of §3.2 applies at all
  (`GIT_PAGER=cat sudo git log` is judged by git's accounted list;
  `DEBUG=1 sudo make` reaches unregistered `make` and keeps its
  posture). A wrapper's own declaration may additionally account
  variables addressed to the wrapper itself. The engine suite must
  cover the wrapped-assignment cases. Two asymmetric
  failure modes, both required: *inside* a wrapper, an undeclared
  option is presumed bare and stepped over, and the walk continues —
  when the next token resolves to a registered tool, judgment proceeds
  normally (`sudo --unknown-flag git push -f` still denies). The walk
  is *lost* only when the command position it lands on resolves to
  nothing — the presumed-bare guess may have skipped one token too few
  — and there the inside-handoff discriminator of this section applies:
  ask if a rule-bearing name appears among the remaining tokens
  (something is being run and a gated tool may be it), silence
  otherwise. That is what "losing the thread" means, precisely. *Outside* any wrapper,
  an unrecognized leading word is silence: on a *parsed* line, scanning
  the rest of the line for registered names must not be attempted,
  because a tool's name is also an ordinary word — a prototype tried it
  and gated `ls ../docker` and `cat docs/env`. The signal there is
  absent, not weak; unknown runners are handled by registering them. A
  command *cleanly reached* behind a wrapper and found unregistered —
  `sudo make install` — is the same no-signal case and is silence in the
  default posture (secure mode: the global default): if no rule was
  written, the decision is the platform's. The operator changes that by
  declaration, not by heuristic — shadowing the wrapper into a tool
  with an ask default gates everything it runs; a rule on the inner
  command gates just that act. One narrower discriminator inside
  handoffs is deliberate and required: when a handoff's *command
  position* holds something that is not command-shaped at all (a
  flag-shaped token — arguments to an image's entrypoint rather than a
  program), the position is silence *unless a rule-bearing tool's name
  appears among the remaining tokens*, which asks. This is the one
  sanctioned exception to the no-scanning rule, and it is deliberately
  asymmetric: `docker run alpine/curl -sL https://example.com` is
  silent, while `docker run alpine/curl -o git https://example.com`
  asks — a known wart that costs a prompt, never a wrong deny, kept
  because inside a handoff something *is* being run and a gated name
  downstream is a real signal there.
  (§4.1's unparseable-line fallback does scan the raw line, and is the
  deliberate exception: with no parse there is nothing better to read,
  and the cost of its false positive is a prompt, the tolerable
  direction.)
- **Control structures and function definitions.** Shell keywords are
  routine agent output — `for f in *.log; do rm "$f"; done`,
  `if git push; then …; fi`, brace groups, `f() { …; }` — and a naive
  splitter reads `do git push -f` as an unknown command named `do`,
  which under §6.1's broad allows is a silent force-push. Required
  treatment, owed by 1.0 (§13): control-flow keywords in command
  position are recognized and stepped past so the commands inside
  bodies are judged; loop and case headers are not commands and
  contribute nothing; a function body is judged at *definition* (so a
  later bare call of its name cannot launder what it contains); any
  construct the walk cannot follow routes to §4.1's unparseable
  fallback. Until the full treatment ships, the pre-1.0 minimum is that
  routing itself — a segment led by a control-flow keyword is treated
  as unparsed, never silently misread — and the honesty documentation
  names the interim. The engine suite gains a control-structure case
  family; the behavior corpus is silent here (the prototype shared the
  gap), which is exactly why the requirement is stated rather than
  inherited.
- **Two command-running shapes the wrapper model does not fit**, both
  everyday: a **flag-introduced inner command** — `find . -name '*.log'
  -exec rm -rf {} +`, where the command sits mid-line, opened by an
  option and closed by a terminator — and a **stdin-fed runner** —
  `… | xargs -0 rm`, where the command word is visible but its operands
  arrive on stdin and are invisible by construction. Both must become
  expressible in the declaration model (the first as an
  option-introduced, terminator-bounded handoff; the second as a runner
  whose inner command is judged on its visible parts, with
  operand-requiring conditions unprovable — stricter, per §3.3), on the
  §13 staging: expressible in the API, shipped by 1.0. The staging
  covers the *declaration model* only — plain wrapper walking of such
  runners (`xargs stubtool wipe` stepping to the inner command) is
  ordinary §4.3 behavior, owed at parity like any wrapper, and named in the
  honesty documentation for as long as they are not — `find -exec
  rm -rf` silent under a broad allow is not a gap to leave unstated.
- **Shells and eval.** A shell's `-c` argument (in its combined-flag
  spellings too, `-lc`, `-ec`) is a command line and is re-analyzed in
  full. A registered shell with **no `-c` payload and no file operand**
  — `curl url | sh`, `echo … | bash` — is executing a program the line
  cannot show at all: it **asks** (§3.3), the lost-thread case in shell
  form, and the vendor-installer pipe is precisely the well-meaning
  mistake §15 says this guard targets. (`bash deploy.sh` remains the
  §4.4 file blind spot — there the program is at least named.) `eval` joins its arguments and runs the result, so the joined
  string is re-analyzed — stepping over it instead would leave a quoted
  payload as one unrecognizable token. Interpreters of *other languages*
  (`python3 -c`, `node -e`) are never read as shell: guessing another
  grammar produces false refusals (a backtick in a Python string is not a
  substitution).
- **Substitutions and subshells.** Unquoted `$(…)`, `<(…)`, `>(…)` and
  bare `(…)` run commands and are judged as such — `>(…)` included, and
  never misread as a redirection. Double-quoted substitutions
  and backticks also run and must also be judged, even though tokenization
  has hidden them inside a single token — `git commit -m "$(git push
  --force)"` is the shape the agent writes constantly. Single-quoted
  substitution text does not run and must not be judged. Nesting is
  resolved; each found command line is analyzed like any other.
- **Redirections.** A redirection target is where a command's output
  lands, and it can destroy by truncation (`> file`) or write where
  nothing else in the line writes — `echo x > .claude/settings.json`
  carries its danger entirely in the redirection. Redirections must be
  recognized as structure: never read as operands or flags of the
  command, and their targets must be matchable by rules (§5.2) so that
  writes into named locations can be gated. Their default is silence —
  redirections are ubiquitous (`2>/dev/null`) and only rules give them
  meaning; an unparseable redirection form follows §3.3 toward the
  stricter outcome. The deferral boundary here is explicit: what may
  ship after parity (§13) is *rule-based target matching* only —
  **recognizing** write-capable redirections is owed the moment any
  allow exists, because hedge six (§6.3) cannot function without it,
  and `git commit -m "$(date)" > ~/.bashrc` riding the waiver is the
  exact silent failure that hedge exists to stop. Until target
  matching ships, the settings-protection pairing (§6.1 rule 5) rides
  on the native file-tool path rules alone and must say so.
- **Heredocs.** A heredoc body is data — a file being written, a message —
  and is excluded from analysis, *except* when its consumer is a shell, in
  which case the body is exactly what runs and is judged. A body fed to
  another language's interpreter is data again, for the same reason
  `python3 -c` is not read. Two orthogonal axes govern heredocs, and
  conflating them misreads both. *Axis one — who consumes the body*:
  fed to a shell, the body is the program and is judged as shell
  whatever the delimiter's quoting (`bash <<'SH'` with a gated command
  inside denies); fed to anything else, the body is data. *Axis two —
  delimiter quoting controls expansion*: with an **unquoted delimiter**
  (`<<EOF`) the shell expands the body, so a command substitution
  inside it executes at expansion time whatever the consumer is —
  `cat > notes.md <<EOF` with `$(git push --force)` in the body runs
  the push — so substitutions and backticks inside unquoted-delimiter
  bodies are found and judged even in bodies otherwise dropped as
  data; a quoted delimiter (`<<'EOF'`) makes the body literal *as
  data*: no expansion runs, and literal text dropped as data is never
  judged — but a literal body fed to a shell is still that shell's
  program (axis one). Two consequences for the bare-runner asks: a
  heredoc attached to a shell or interpreter means the program *is*
  shown, so the no-payload ask (here and §4.2) does not fire — the
  shell's body is judged, the foreign interpreter's is data
  (`python3 - <<'PY'` is silent; `-` with an attached heredoc counts
  as fed-by-heredoc, not as a missing file operand).
- **Declared handoffs.** A tool can declare subcommand positions where it
  stops describing itself and runs something else (`docker run IMAGE cmd`,
  `docker exec CONTAINER cmd`, compose forms). The outer invocation is
  judged as itself, the inner command is judged in full, and tokens past
  the handoff belong to the inner command only — an inner `--check` must
  never satisfy an outer grant. The operand the handoff keeps for itself
  (image, service, container name) is never read as a program, however it
  is named: judging `docker run org/rm -rf` as an `rm` on the host would
  be guesswork in the wrong direction. A handed-off command also runs in
  a different world than the host's, and policy may legitimately differ —
  `docker run image cmd --dangerous` and a bare `cmd --dangerous` need
  not share a verdict — so the configuration must be able to scope
  judgment by execution context (§5.2).

### 4.4 Declared blind spots

The engine reads a command line; it does not run a shell. The following
are known, accepted, and must appear in the honesty documentation (§12) so
nobody mistakes silence for coverage — and anything of this kind
discovered later joins that document rather than persisting silently:
unregistered runner programs (the fix is registering them, never
name-guessing); program text in other languages; shell script *files* —
`bash deploy.sh` runs a file the engine never reads (§4.3 re-analyzes
only `-c` payloads), and `source x.sh` or `. x.sh` runs one in the
current shell, both judged only by what is visible on the line; operands consisting only
of separator characters inside quotes (indistinguishable after
tokenization); handoff arity approximations (which fail toward asking);
the export family's edges (`declare -x`, `unset`, valueless
`export NAME`), and — until §4.2's export modeling ships — plain
`export NAME=value` itself; whether the platform's Bash tool persists
shell state *across* tool calls is version-sensitive (a verification
item): where it does, an export from an earlier call is invisible to
any line-scoped parsing, permanently; and symlinks — path matchers resolve `..` and `~` textually without
consulting the filesystem (§4.5), so a path that traverses a symlink can
satisfy a location boundary it does not really stay inside, a limit
consistent with the non-adversarial scope (§15) but stated here so
nobody reads "resolved before comparing" as filesystem truth.

### 4.5 Proportion

The guard runs on every Bash call. The decision itself should stay in
single-digit milliseconds on typical lines (interpreter startup dominates,
§2.3); nothing in the design may require a daemon, network access, or
filesystem access beyond its own config and cache — in particular,
matchers resolve paths textually and never consult the filesystem, both
for speed and because the paths being judged may not exist yet.

## 5. Configuration

### 5.1 Location, lifecycle, trust

The configuration lives in a dedicated directory inside the project's
`.claude/` directory — one directory because config, cases and future
additions (a declarative source, §14) each want a home, and because one
directory is one thing the operator versions and one thing the plugin
promises about. The directory's exact name and internal layout are the
implementation's choice; the name should carry the plugin's name.

Lifecycle invariants, all requirements:

- It is created only by the scaffold (§5.4), only on the operator's
  request.
- After creation, no **unattended** write may ever touch it: not the
  update channel, not the hook, not the engine, and not the skill acting
  on its own initiative. The update channel updates the engine; a
  channel that could rewrite the config could rewrite the boundary.
  Exactly two write paths exist, both operator-gated: the scaffold at
  creation, and the skill applying a change the operator has just
  approved (§10) — the surprise loop writes rules and cases directly on
  agreement, not as diffs for the operator to paste.
- It is meant to be committed: the config is part of the project, and its
  history is the history of the project's boundary.

The configuration is **trusted code**, executed by the hook and the CLI. It
sits at exactly the trust level of a hand-written hook in the same
directory — which is what it replaces — and of any committed settings hook:
opening a hostile repository and letting its hooks run is an existing
Claude Code surface, gated by Claude Code's workspace trust, and frisk
must not enlarge it (the engine executes only the project's own config,
never anything received over the network). The trust model is stated
plainly in SECURITY.md (§12).

### 5.2 What the configuration must be able to express

The full decision model of §3.2, concretely: registering a tool under one
or more names (aliases — drop-in replacements share one declaration) or
by project-relative path (§4.2);
deny/ask/allow rules on subcommand paths conditioned on flag presence,
flag values, environment-assignment presence and values, pre-subcommand
option values, and operand constraints with both quantifiers ("every
operand", "at least one"); grants combining required-operative-flags (**operative**: the parser
saw the token as a flag of this invocation — a flag swallowed as
another flag's value is not operative, which is what makes
`deploy.yml -i --syntax-check` a real deploy, §4.2),
flag- and env-value constraints and operand constraints, including "no
operands allowed"; per-tool default verdicts with mandatory reasons; the
closed worlds of a gated tool (accounted flags); the accounted
assignments every registered tool may declare, with value conditions
(§3.2); a tool's flag arities (bare, value-required,
value-optional) and pre-subcommand options; handoff declarations, with judgment scopable by
execution context — the same tool may carry different rules on the host
and inside a named handoff (§4.3); rules on redirection targets (§4.3); wrapper additions and per-name
shadowing of engine defaults with replace and update-with-removal
semantics (§3.4); the secure-mode switch with its chosen default verdict
and reason; the failure-policy dial of §7.2; collection imports (§3.4);
and the project's test cases (command → expected verdict) beside the
rules they prove.

Not all of this surface need ship at once — §13 stages it — but the API
is designed against the whole of it, so nothing here is precluded by an
earlier release.

### 5.3 Legibility

Requirements, not niceties: the configuration must read
as *declarations* — an operator who does not know Python must be able to
review their boundary, since a boundary that cannot be read is not the
operator's. Every rule, grant and default verdict carries a
human-readable reason (empty reasons are a liveness failure, §8.2: a
refusal that says nothing is worse than none). Construct names say what
they do; ceremony is minimal; a registry entry should be reviewable in a
single reading pass. This constrains the API design as strongly as any
mechanism in §3.

### 5.4 The scaffold

Until a configuration exists, an enabled plugin gates nothing — and
must be **visibly inert**: the hook itself says so, once per session,
through the non-blocking user-visible channel of §2.1, with the CLI's
status carrying the same answer when asked. The notice makes no
distinction between a project never scaffolded and a config that
*stopped existing* — deleted, renamed, lost on an older branch — and
that is deliberate: the second case is the sharper danger, a project
whose settings still carry §6.1's broad allows while the guard silently
gates nothing, and the notice is its floor of visibility. For projects
that adopted the sentinel, the floor is higher: its probe requires the
project's config to load (§7.4), so a vanished config is a deny, not a
notice. An installed guard silently implying coverage is the
false-safety failure §7 exists to prevent, arrived at by another road.

On the operator's request — typically through the skill — the scaffold
creates the configuration, pre-filled with the starter registry, and the
moment that makes it legitimate is the **one-pass review**: the operator
reads the whole starter set once and accepts it, which is why no
rule-by-rule approval is needed at creation and why every later change is
individually the operator's (§10). The scaffold also writes the
API-generation declaration (§3.5), creates the starter cases covering
every starter rule (the coverage gate of §8.2 must pass from day one),
walks the operator through the settings pairing of §6.1 including the
deny backstop, and offers the sentinel (§7.4).

The starter registry is **interim by design** — it exists so a freshly
scaffolded project has a meaningful boundary on day one, and it shrinks
to a selection step once default collections exist (§14). Its content:

- **git ground rules** — required. Deny: forced, mirror and delete
  pushes however spelled; history rewriting (filter-branch and
  equivalents); destruction of git's recovery data (reflog
  expiry/deletion, ref deletion, pruning gc). Ask: any push; commit
  amendment; rebase; hard/merge resets; clean; restore; the
  work-discarding forms of checkout and switch; stash dropping and
  clearing; branch and tag deletion or forced movement; worktree removal
  and pruning; and the presence of a config-override option (`-c`,
  `--config-env`) — the sibling spelling of the assignment danger
  §3.2's closed world exists for, since `git -c core.sshCommand=…
  fetch` runs an arbitrary program exactly as `GIT_SSH_COMMAND=…`
  does, and a boundary that gates one spelling and not the other
  gates neither (value-conditioned carve-outs for benign overrides may
  refine this through the surprise loop). Allow: exactly the
  commit-message substitution shape of
  §6.3, with its hedges. These are **ground rules**: identical across
  projects by design, encoding losses that are permanent or expensive;
  the skill must treat a proposal to weaken them as reportable, not
  routine (§10). (Exact spellings and flag inventories are
  implementation, proven by the starter cases.)
- **A small set of additional common tools**, chosen at implementation
  and reviewed by the operator like everything else in the one-pass
  review. docker (with its drop-in equivalents as aliases) is the
  recommended candidate, shaped as: ask on every spelling of publishing
  to a registry including publish-capable build flags, host-global
  prunes, and registry credential operations; handoffs on the run/exec
  forms and their compose equivalents; the ordinary local loop — build,
  run, named deletes — silent.
- The engine's default layers — wrappers and baseline read tools
  (§3.4, §6.3) — in effect.

Two deliberate acceptances, stated so they read as choices rather than
oversights. **The starter docker shape leaves `docker run` host mounts
(`-v /anywhere:/x`) silent**: a host mount hands the container
arbitrary host paths, but the `-v $(pwd):/app` development loop is too
common to gate without over-prompting; the one-pass review carries this
knowingly, and real-world use may condition mounts later through the
surprise loop. And **`rm` is not in the starter registry.** Unregistered, it
still meets the default mode's native prompt (nobody broad-allows it),
while registering it usefully would demand path rules that either
over-prompt (builds delete temporary files constantly) or
under-protect; its real home is secure mode and future collections
(§14), and real-world use may rule differently later — through the
surprise loop, like everything else.

## 6. Verdicts and the Permission System

### 6.1 Pairing

The guard is one half of a pairing; settings are the other, and the
pairing rules below are requirements on the guidance the scaffold and
skill produce, because each wrong pairing defeats the guard in a
different silent way:

1. **Allow each guarded tool broadly, let the guard claw back.** Scope:
   the tools whose configuration can actually return silence or allow —
   never a tool registered deny-everything ("every use is the
   operator's"), for which a broad allow buys nothing while the guard
   lives (the hook's deny is final) and is pure liability when it dies:
   the tool the operator locked hardest would become unprompted
   execution. And never the engine's default layers, which
   are analysis knowledge, not gated tools, and call for no settings
   entries at all (generated guidance must never suggest
   `Bash(sudo:*)` or an allow for `cat`) — for the wrappers because a
   broad allow on a command-runner is a broad allow on everything it
   runs when the guard is dead, and for the baseline reads because the
   platform's own built-in read-only command handling already covers
   them (a platform behavior the verification pass re-checks; the
   failure direction is extra prompts, never a lost fence) and every
   settings line is boundary surface that must earn its place. For each
   tool in the scope just drawn — not literally every registered
   tool — write a broad settings allow. This is the product's
   point — a broad allow plus a deep hook replaces a long, brittle
   allow list. (Prefix rules respect word boundaries — `Bash(git:*)`
   does not leak to `git-crypt` — a platform fact the verification
   pass re-checks.) A guarded tool with no allow line prompts on everything
   anyway, and its grants are never reached.
2. **Never an `ask` rule on a guarded tool.** A matching settings `ask`
   prompts even when the hook allows (§2.1), so it makes every
   carve-out — including the guard's — unreachable. Exceptions are
   expressed in the config, not in settings.
3. **Never restate the guard's asks as prefix rules.** `Bash(git push:*)`
   misses `git -C dir push`; the guard does not. Two sources of truth,
   one of them wrong.
4. **Keep a short deny backstop for unrecoverable acts.** Prefix-weak,
   but alive when the guard is not (§2.1 fail-open): under the broad
   allows of rule 1, a dead guard means an unprompted force-push unless
   the backstop holds. The broad allows and the backstop are a package.
   This is not rule 3's mistake in reverse: rule 3 objects to a second
   source of *truth*, and the backstop is not one — it is a dead-man's
   brake, deliberately redundant, kept only for acts whose loss is
   unrecoverable, where redundancy is the feature.
5. **Protect the boundary's own files.** The pairing must gate edits
   to the settings files and to frisk's configuration directory — with
   the native permission rules for the file-editing tools, and the guard
   for shell-based edits once redirection-target matching ships (§4.3;
   until then the native path rules carry this alone, and the pairing
   guidance says so) — so the boundary cannot be rewritten as casually
   as any other file; and the skill asks for explicit approval before
   every settings edit it performs, scaffold time included (§10).

Permission modes shade the picture, and the pairing guidance must be
mode-aware — and honest about what rule 1 trades. For a **broadly
allowed tool**, the guard's silence is *not* backed by a prompt: it is
unprompted execution, by design — that is the deal rule 1 makes, and it
is exactly why the named-acts coverage of §3.2, the deny backstop of
rule 4, and secure mode exist. The default mode's prompt backs silence
only for tools with no broad allow — the unregistered ones. The
permissive modes differ, and the guidance must name them precisely
(the taxonomy is version-sensitive platform behavior, re-checked by
the verification pass): **acceptEdits** auto-accepts file edits and a
small set of filesystem commands — unmatched Bash still prompts there,
so the guard's posture barely changes; **auto** replaces the prompt
with a background classifier, and **bypassPermissions** approves
everything — under those two, rule 1 loses its sting while rules 2–5
are believed to keep their force — whether settings deny/ask rules are
enforced under each permissive mode is itself version-sensitive, joins
the verification pass with its response pre-committed (a mode found to
skip deny rules empties §7.5's backstop row for that mode, and the
documentation says so rather than implying a backstop that is not
there) — and the guard's asks and denies become the only
gate left *on the Bash surface* (file edits and other tools keep or
lose their own native handling regardless of frisk, §1). That is what
secure mode (§3.2) exists to make honest: silence-on-the-unknown
becomes a question or refusal precisely where silence would otherwise
mean execution. The generated pairing guidance and the README's
pairing section (§12) must carry this model — scoped claims included —
not the comfortable misreading.

**Line-level combination.** Per-invocation verdicts combine over a line
by this table, dangerous branches first:

| The line contains | Result |
|---|---|
| any deny, anywhere (embedded commands included) | deny |
| no deny, any ask | ask |
| allow(s) earned by invocations in direct, unwrapped command position; every command position examined (see below); every dynamic token inside a granted position; no unproven write-capable redirection; and a substitution the platform's heuristic determinably fires on (open fact (c)) | allow |
| allow(s), but any command position unexamined — an unregistered tool anywhere on the line | silence |
| allow(s), but a substitution or variable reference sits outside every allow-granted position | silence |
| allow(s), all examined and placed, but no substitution the platform's heuristic fires on (none present, or determinably not firing) | silence |
| silence only | silence |

**Examined** means what it says: the position resolved to a registered
tool — wrappers walked, embedded commands included — and came back
silent or allow from actual rule evaluation. Unregistered-tool silence
is *not* examination, it is the absence of one, and it withholds the
allow: the line falls back to genuine silence and the platform's own
substitution prompt fires exactly as it would without frisk. **Placed**
is the companion condition on data rather than commands: every dynamic
token on the line — a command substitution or a variable reference —
must sit inside a position the granting allow rule itself proves (the
commit message's value slot); one landing anywhere else withholds the
allow, §6.3 says why. A **write-capable redirection** (`>`, `>>`,
`>|`, `<>`, `>&file`) anywhere on the line likewise withholds the allow
unless a rule proves its target (§4.3) — a redirected write is a
landing site no examination covers — while input redirections
(heredocs included) and pure fd-duplications (`2>&1`) do not, because
they direct nothing outward. When it is unclear whether the platform's
own substitution heuristic would fire on the line, the allow is
likewise withheld — the stricter direction, costing a prompt (§3.3).
§6.3 carries the reasoning for all of it. In secure mode, command positions resolving to
no registered tool contribute the configured global default *before*
this combination. The substitution condition is textual on purpose: the
question it answers is whether Claude Code's own textual heuristic will
fire (§6.3), not what the command does.

### 6.2 Reasons and citations

Every non-silent verdict must carry two things: a **reason** — why the
act is objectionable, and for gated defaults also *how to satisfy a
grant* ("rehearse with --check", "keep targets under /tmp") — and a
**citation** — what the guard read to decide: the tool, the subcommand
path, the specific flag, assignment, value or operand that matched, and
which declaration fired. Without the citation, a wrong verdict is a
sentence with nothing to grep for, and the maintenance loop (§10)
starves: reports are its only input.

Two refinements, both consequences of who reads this text. **The model
reads it** (§2.1): a deny or ask reason flows into Claude's context and
steers the next attempt, so reasons must be written as steering text —
name the objection *and* the acceptable path, so the model's recovery is
toward the safe alternative rather than toward creative respelling.
**The operator greps it**: when several declarations independently reach
the returned rank, the citation should name them all — fixing one match
and being surprised by the next is a wasted report cycle — bounded by
legibility: line evaluation is exhaustive — no short-circuit at the
first deciding match — and the citation names every declaration at the
deciding rank *across the whole line*, embedded invocations included
(`git push -f && git reset --hard` cites both), not every weaker
match beneath it.

### 6.3 The allow doctrine

`allow` is the exceptional verdict, and open fact (a) of §2.1 is why: a
hook allow is assumed to lift the working-directory sandbox, so granting
is not "answering the prompt for the operator" — it is switching off the
fence. It exists nonetheless because of open fact (c): the platform
prompts on substitution-bearing lines, no permission rule can lift
that, and the
agent is pushed toward those shapes constantly; without a release valve,
operators worn down by prompts switch to permissive modes and lose the
fence for everything, not just one shape.

The semantic precondition for declaring an allow is: **the granted shape
must guarantee that whatever a substitution expands to cannot direct a
write** — cannot become a path, a command, or a target. The
commit-message shape qualifies: the expansion lands in a message string.
`touch "$(cat x)"` shows why nothing weaker qualifies: nothing in it is
gated, yet the expansion becomes a path, and the guard can never see
expansion output — it does not exist at decision time. **This
precondition is operator doctrine, not an engine check**: the engine
analyzes command strings and knows nothing of tool semantics, so the
rule is carried by the documentation and pressed by the skill — which
must, whenever a new allow is proposed, present the doctrine and demand
the argument — never verified by code.

One platform fact shapes all of it: **a hook allow is indivisible.** It
covers the whole tool call — there is no channel that waives the
substitution prompt for one command while leaving its neighbours to
normal permission handling — so whatever shares the line with a granted
invocation is released with it, fence down. That is why the release is
bounded by examination, not by shape alone.

What the engine *does* enforce, mechanically, are the seven hedges:
an allow ranks below everything (§3.2); it is spent only on a **fully
examined line** — every other command position, top-level, embedded or
behind a wrapper, resolves to a registered tool and itself came back
silent or allow, because unregistered silence means "never looked at",
and `rm -rf build && git commit -m "$(date)"` must fall back to the
platform's own prompt rather than ride the commit's grant out of the
sandbox (the combination table above); it is withheld if the invocation
used any global option not explicitly accounted for by the declaring
rule — `git -C /elsewhere commit -m "$(…)"` retargets the repository at
the same moment the sandbox is waived; and it is downgraded to silence
when the line contains no substitution, because such a line reaches the
permission rules unaided and granting would waive the sandbox for
nothing. And a fifth hedge guards data where the other four guard
commands: the allow is withheld if any **dynamic token** — a
substitution or a variable reference — sits outside the positions the
granting rule proves. Those positions are exactly the **value slots of
the flags the allow rule names**, exhaustively — the rule's flag list
does double duty, trigger and granted-position definition — so no
other flag's value, no operand, and no position of any other
invocation is ever granted (`git commit --author="$(x)" -m hi`
withholds: `--author` was never proven). Operand-position grants are
deliberately not offered: operands are usually paths, exactly the
slots the semantic precondition cannot bless. Examination vouches for what each command *is*;
it says nothing about where a dynamic value *lands*. In
`touch $(cat x) && git commit -m "$(cat m)"` every command is examined
— touch declared, cat baseline, commit granted — yet the first
substitution's output becomes a **path** handed to touch, exactly the
`touch "$(cat x)"` danger this section opened with, smuggled in through
a compound line. No grant proves that position, so the allow is
withheld and the platform's own prompt fires, as it would without
frisk. A sixth hedge closes the same door from the shell's side:
**write-capable redirections withhold the allow** unless a rule proves
the target. `echo x > ~/.bashrc && git commit -m "$(date)"` passes
every other hedge — commands examined, token placed — yet the
redirection writes outside the project the instant the waiver lifts
the sandbox, and a redirection is neither a command position nor a
dynamic token: none of the other hedges can see it. Input redirections
and fd-duplications are exempt, deliberately — a heredoc feeds data
*in*, which is why the granted commit shape's `<<'EOF'` does not
withhold and the daily flow survives; `>/dev/null` is not exempt,
because /dev/null is a path like any other to a textual engine, and
the cost is a rare prompt. And a seventh hedge guards the granted
position itself: the allow is spent only when the granted invocation
sits in **direct, unwrapped command position** — `sudo git commit -m
"$(date)"` withholds, because the grant proved the shape of a *git
commit*, not of a privilege-escalated one, and a wrapper changes what
the command is at the exact moment the sandbox drops. A leading
environment assignment is *not* a wrapper for this hedge:
`FOO=bar git commit -m "$(…)"` is governed by the assignment closed
world (§3.2) instead — accounted or benign, the allow stays available;
unaccounted, the resulting ask withholds it anyway. The blast radius
of an allow is thereby bounded by the registry's explicit coverage —
commands examined, data placed, writes proven, position direct: within
one line, everything either followed the rules or the waiver was never
spent. A miss — a harmless read command nobody
registered — costs one prompt and a trip through the surprise loop
(§10), never a fence.

The scaffold ships exactly one allow — the commit-message shape — and
documents it as the deliberate exception it is. For the examined-line
release to work out of the box, the engine ships a second defaults
layer beside the wrappers (§3.4): a deliberately minimal set of
**baseline read tools** — the likes of `cat`, `echo`, `printf`, `date`,
`head`, `basename` — registered as examined-silent, because they are
what legitimately appears inside a commit-message substitution. The
same rules as wrappers apply: universal shell knowledge, not policy;
per-name shadowing; anything with a genuinely dangerous form stays out
or carries its rule; and every entry is enumerated in the operator
documentation (§12) — an engine default the operator cannot read is a
rule they never agreed to.

## 7. Failure Handling and Self-Protection

Claude Code's hooks fail open (§2.1), and the guard invites broad allows
(§6.1), so a dead guard is worse than no guard: the operator believes a
boundary exists. This section is the machinery that converts every death
the guard *can* see into a loud deny, and layers external checks over the
deaths it cannot.

### 7.1 Fail closed at runtime

Any failure while loading the configuration or reaching a decision —
an import error, an exception mid-analysis, a malformed registry — must
produce **deny**, with a message that names what broke as precisely as
possible, states that no safe verdict can be produced, and points at the
CLI's liveness diagnostics (§9). This deliberately inverts the choice
made during prototyping — `ask` — which was right then: a guard living
as project code has bugs of its own as likely as config problems. The
shipped engine arrives proven (§8.1), so a runtime failure now points
at the config, and deny forces fixing the boundary rather than handing
a broken one to per-command judgment. Fail loudly rather than proceed
plausibly.

The failure policy layers by reachability: the engine default is deny; a
**machine-level** option (carried by the plugin's user configuration,
§2.2) may relax it to ask — the operator's own choice, readable even
when the project config is not, and organizationally pinnable since
managed settings outrank the user's (§2.2); the **per-project** dial
exists only for the class of §7.2 where the config is readable at all.

### 7.2 Validation on configuration change

When the configuration has changed since last validated (change
detection and caching are free), the hook re-runs, before judging
anything: liveness (§8.2), the project's cases, and the coverage check.
Failure is deny with a message naming the failing case or uncovered
rule. Two classes, distinguished because their escape hatches differ:

| Failure class | Behavior |
|---|---|
| config does not load | deny of every Bash call, unconditional with respect to any *config* dial — the registry is unknown, so nothing can be judged, and no dial inside an unloadable file is reachable; only §7.1's machine-level relaxation, which lives outside the config, still applies — though in a sentinel-adopted project the sentinel's stricter deny prevails over that relaxation (§7.4) |
| config loads, but liveness fails (a structurally invalid declaration, an empty reason, §8.2), cases fail, or coverage has gaps | deny with the failing check named; the *config's own* dial may relax this class to warn-and-proceed **only when the trigger was a config change** — a failure triggered by an engine-version change (§7.3) denies whatever the dial says, since an update that flips recorded verdicts must never be warned past; the machine-level dial of §7.1 does not reach this class either way, because it exists for states where the config is unreadable, and here the project's own recorded stance governs |

When the dial relaxes the second class to warn-and-proceed, the warning
must actually be seen: at minimum it is reflected in the CLI's status
as the last validation outcome, and it surfaces at least once in the
session itself (mechanism free — hooks have non-blocking output
channels). A warning with no surface would be this document's own
definition of a silent failure.

This mechanism makes the hook itself enforce the discipline of §10: a
rule edit without its case does not fail CI later — it stops the line
now.

### 7.3 Validation on engine change

The same mechanism, second trigger (§3.5): when the engine's version
differs from the last validated one, the project suite re-runs before
anything is judged. An engine update that flips any recorded verdict —
or a config declaring an API generation the engine no longer speaks —
is a deny naming the failing case or the mismatch, pointing at the
skill's migration assistance. Never reinterpretation, never silence.

### 7.4 The sentinel

For the deaths the plugin cannot see because it is absent or inert: the
scaffold **offers** (never imposes) a sentinel — a tiny, self-contained
POSIX-shell PreToolUse hook committed to the project's settings, whose
only dependency is a shell, which necessarily exists wherever the Bash
tool runs (§2.3). Its behavior: once per session (the hook payload's
session identifier keys a cache; mechanics free), it **probes by
execution** — it runs the engine's liveness entry, through the same
project entry point and resolution the CLI uses (§9), and requires
success **from a plugin-resolved engine specifically**: the resolution
must expose which door answered, and a pin-answered probe (§9's
repository-installed fallback) is a *failure* for the sentinel's
purpose — a working engine with no installed plugin means no hook is
running, which is exactly the absent-guard state the sentinel exists
to catch. It further requires *that the project's configuration
loads*: a
scaffolded project whose config has vanished fails the probe and gets a
deny naming that, not silent inertness — and on failure denies Bash with a message naming the exits
appropriate
to what the probe observed — install and enable the plugin when it is
absent; fix or install `python3` when the interpreter is what failed; a
*distinct* message when the engine is installed but cannot be located
(§9's cannot-resolve requirement extends to the sentinel — a misleading
"install the plugin" on a resolution failure would send the operator
chasing the wrong fault); and, always, remove the sentinel if this
clone genuinely does not want the guard. While the guard is provably
alive it stays silent. A failed probe is not a one-shot message but the
session's **standing state**: every subsequent Bash call in the session
is denied while the failure stands, and the sentinel may re-probe on
later calls so a mid-session fix lifts the deny — what the session
cache remembers is a *success*, never a failure. The alternative
reading — one deny, then silence — would hand the agent an unguarded
session after a single retry, the exact believed-boundary failure this
section exists to prevent. One precedence consequence is intended and
stated: in a sentinel-adopted project, a broken config denies through
the sentinel *regardless* of §7.1's machine-level relaxation —
committing the sentinel is the project declaring a stricter stance, and
the platform's combination (deny wins) is exactly the mechanism meant
to carry it.

Probing by execution rather than presence is the point: it catches the
plugin missing on a fresh clone (§2.2 — committed settings can enable
but never install), `python3` absent, an interpreter below the floor,
and an engine that cannot load. Accepted trade: a mid-session breakage
surfaces only at the next session. The sentinel is a seatbelt check,
not a lock — the cloner owns their clone; the goal is that absence be
loud, not that use be forced.

**Kill switches.** Both the sentinel and the guard itself must honor an
environment variable that disables them for the launching session
(frisk-prefixed names; exact spelling free): the sentinel's, so an
operator who committed it can run a guardless session
(`FRISK_SENTINEL_DISABLE=1 claude`) without editing shared settings; the
guard's, so a deliberately sandboxed environment — a CI job running
Claude Code in a permissive mode inside a container — can switch frisk
off wholesale; the wholesale switch silences the sentinel too, so a
deliberately guardless session does not fight its own seatbelt (one
variable, not two, for the sandboxed-CI case). Both switches announce
themselves once per session through the non-blocking channel — the
sentinel-only switch included, because a silently absent seatbelt
check is a smaller edition of the same disease. These are launch-environment switches, which is what
keeps them out of the agent's reach: the hook reads its *own* process
environment, supplied by the platform's own process tree — the hook is
not a child of the agent's Bash session, so an `export` run inside a
tool call can never reach it — and a
`FRISK_DISABLE=1 git push` prefix written by the agent sets that
variable for `git`, never for the hook (§4.2 treats such a prefix as
the environment condition it is). A disabled guard must be visibly
disabled **from inside the session it is disabled in**: the hook (or
sentinel) announces it once per session through the non-blocking
channel of §2.1 — the CLI's status cannot be the carrier here, since a
CLI run from another shell does not see the launching environment and
would report the guard enabled while the session runs bare. The honesty
documentation (§12) lists the switches. Without the in-session
announcement, an operator who forgot an export is back to the
silently-absent boundary this section exists to prevent.

### 7.5 The coverage map

Who catches what — kept explicit so no layer's silence is mistaken for
another's coverage:

| Death | Caught by | Residue |
|---|---|---|
| engine error while deciding | fail-closed runtime (§7.1) | — |
| config unloadable | fail-closed runtime (§7.1) | — |
| config edited, cases fail or rule uncovered | on-change validation (§7.2) | dialable, config-readable class only |
| engine updated, verdict flipped or API mismatch | on-change validation (§7.3) | — |
| plugin absent on this machine (fresh clone) | sentinel (§7.4), if adopted | operator declined the sentinel; the sentinel is itself a hook and fails open like any other — a lost executable bit reports nothing |
| config absent where one existed (deleted, renamed, older branch) | sentinel's config-load probe (§7.4), if adopted; otherwise the once-per-session unconfigured notice (§5.4) | without the sentinel, a notice is all there is — the broad allows of §6.1 stay live |
| guard disabled by kill switch | once-per-session in-session announcement (§7.4) | an unnoticed announcement; the sentinel is silenced by the wholesale switch (or disabled by its own), so only the announcement remains |
| engine overruns the platform's hook timeout | the engine's internal time budget (§2.1), converting the overrun into a deny | a hard hang the budget cannot interrupt fails open, caught by nothing but the deny backstop |
| `python3` absent or engine unrunnable | sentinel's execution probe (§7.4) | mid-session breakage until next session |
| plugin installed but hook not firing | reachability probe (§8.3) | only when the probe is run |
| any of the above, worst commands | settings deny backstop (§6.1) | prefix-weak by nature |

The residue column is the honest part: the last two rows are why the
backstop and the probe are requirements and not suggestions.

## 8. Testing and Verification

Three gates, three different questions. None substitutes for another
(§7.5), and together they carry the project's founding discipline:
**every surprise becomes a test** — when the guard does the wrong thing,
the fix is not complete until the exact reported command exists as a
case asserting the corrected verdict, because a rule change with no
reproduction is a regression waiting to happen and the report is the
only evidence of what the rule was for.

### 8.1 Gate one — is the engine correct?

The engine's test suite ships with the plugin and runs in the plugin
repository's CI on every change, at three levels:

- **Behavior cases** asserting every behavior of §4 through the decision
  model of §3.2, against test-only tool declarations — never against
  real-tool starter rules, so that policy changes can never break engine
  tests. The suite must reproduce the verdicts of the **adjudicated
  behavior corpus**: the set of command → verdict rulings accumulated
  during prototyping across three projects, delivered to the
  implementation as reference data at handoff. Each ruling carries its
  **policy context** — the corpus states, in prose, the declarations
  each block of rulings was adjudicated under (the starter-policy
  families, the hypothetical gated-tool fixtures, an infrastructure
  project's policies) — so reproducing a verdict is mechanical, never
  an exercise in reverse-engineering the rules that produced it. The corpus is rulings,
  not design: where a corpus verdict conflicts with this specification,
  the specification wins and the conflict is reported.
- **Unit tests** for the config-facing helpers in their own right, not
  only through end-to-end verdicts — above all the path matcher, whose
  traversal-resolution guarantees (§3.2) are load-bearing for every
  boundary a grant draws — and for the CLI's commands and exit statuses.
- **End-to-end checks**, as far as the harness allows: it would be
  valuable to drive a real Claude Code session in CI and observe the
  hook deciding — and, if the platform's plugin-evaluation tooling
  permits, to exercise the skill — but this depends on facilities
  outside this project's control, so it is a should, explored at
  implementation time, never a substitute for the two layers above.

Users receive the engine proven and never re-prove it.

### 8.2 Gate two — does this project's guard decide correctly?

Two project-facing checks, both invocable through the CLI (§9) from
pre-commit and CI:

- **Liveness** — is the guard alive and well-formed: the config loads,
  every declaration is structurally valid, reasons are non-empty, and a
  hook payload comes back as a well-formed verdict — plus the
  boundary-nullifying shapes that are structurally valid and
  semantically fatal: an unconditional allow on a tool with no grants
  (waives the sandbox for the whole tool), a grant with no conditions
  (matches everything, so the tool is not gated at all), and a
  declaration shadowing a wrapper without re-declaring its handoff (the
  walk through it is silently lost). No behavior cases;
  it stays lint-fast, because it is meant to run before every commit —
  which is where the silent deaths (a broken edit, a rename) happen.
- **Selftest** — liveness, then the project's cases, then **coverage**:
  every rule and every grant in the *effective* registry must be
  reached by at least one case — *reached* meaning the rule **matched**
  or the grant **held** in that case, never merely that it was
  evaluated — supplied by the project, or by the source that
  contributed the rule (collections carry their own cases,
  exactly as the starter registry ships starter cases), so composition
  can never mint uncovered rules or turn a live import into a
  coverage deny. The engine's default layers as shipped carry **no
  rules and no grants** — they are analysis knowledge — so they stand
  outside the coverage gate; the moment a config shadows one into a
  rule-bearing tool, the config is the contributing source and owes
  the cases. An unreached deny/ask is either dead (a path spelled wrong)
  or untested — indistinguishable from outside. An unreached grant is
  the quieter failure: it over-prompts, so nothing goes wrong loudly
  and the proven-safe shape may never have worked at all. Coverage is
  what turns "add a case for every rule" from advice into a gate.

A project harness may also *derive* cases from project structure —
"every playbook under the exempt directory must be silent, every one
outside it gated" — so a file added tomorrow is judged tomorrow without
anyone remembering to write its case; derived cases complement, never
replace, the hand-written surprise corpus. Project CI runs without
Claude Code, so the engine must be installable
from the public repository alone (§2.2 forbids depending on the plugin
cache). Engine identity splits by context: on a machine where Claude
Code runs the hook, §9's same-engine requirement applies in full; in
CI, where no hook exists, the project pins the engine version it tests
against — recorded beside the configuration, so both sides can be
checked — CI installs that pin and states which version answered, and the
compatibility contract (§3.5) covers the drift.

### 8.3 Gate three — is the guard reached?

Nothing in gates one and two can see a guard that never runs: a
disabled plugin, a hook that stopped firing — green lints, absent
boundary. The reachability probe is a live end-to-end check, guided by
the skill and documented for direct use: issue a command the config
refuses and verify it comes back refused **by the guard, citing its
rule**. Merely prompting means the hook is not reaching the tool call
and only the deny backstop is left. The probe should be run at
adoption, after settings changes, and whenever §7's layers report
nothing but doubt remains — it is the one check that exercises the
whole chain.

## 9. The Command-Line Interface

One CLI surface, reachable through several doors — a stable
scaffold-created entry point inside the project, an installed entry point
where the engine was installed from the repository (§8.2), and whatever
the skill uses — all the same commands, because a diagnosis must never
depend on which door was available. The CLI must run without Claude Code:
no dependence on hook-time environment variables or the plugin cache path
(§2.2).

It must provide:

- **explain/check** — given a command line, the verdict the guard would
  return, with the reason and citation of §6.2, against the project's
  actual configuration; exit status usable from scripts. It should also
  show its work — which invocations were found through which walls of
  §4.3 — because "why did this ask?" is the maintenance loop's opening
  question and the answer is the analysis, not just the verdict.
- **liveness** and **selftest** — the two checks of §8.2, exactly as the
  hook runs them (§7.2), so pre-commit, CI, the sentinel and the hook can
  never disagree about what "alive" means.
- **status** — is there a config, which engine and API generation, is
  secure mode on, when was the last validation and its outcome, the
  kill switches *when its own process environment carries them* —
  best-effort by construction, which is enough for the status-line
  sample (a session child) and never the required carrier (§7.4's
  in-session notice is) — and —
  the visibly-inert requirement of §5.4 — an unmissable statement when
  the plugin is enabled but the project is unconfigured.

Output is for humans first, and should be stable enough to script
against — a machine-readable output option (JSON) is the recommended way
to make that promise cheap to keep. One consumer is worth naming: a
Claude Code **status line** script can call the CLI to surface the
guard's state (configured, secure mode, disabled-by-switch, last
validation) at a glance — disabled-by-switch is visible to it precisely
because a status-line script runs as a child of the session and
inherits its environment, where a CLI in a foreign shell does not
(§7.4) — and the documentation should show a working
sample of exactly that (§12) — a useful extra carrier of §5.4's
visibly-inert requirement, whose required carrier is the in-session
notice. Anything the skill needs programmatically should come
from here rather than from a parallel private interface, so the CLI
stays the single accountable answer to "what would frisk do?".

One version question must be designed away rather than endured: a CLI
installed one way (globally, or in CI from the repository) meeting a
project whose plugin runs another engine version. The requirement is the
outcome, not the mechanism, and it splits by context (§8.2): **on a
machine where the hook runs, the CLI must answer with the same engine
the hook runs** — by resolving and loading the project's installed
plugin engine, by matching versions, or by any other means — and when
it cannot, it must say so loudly instead of answering with a different
engine's opinion, which would make gate two prove something the hook
does not run (§11). In CI, where no hook exists, the project's pinned
engine version is the reference, and the CLI states which version
answered. The rule is keyed to an observable condition, not to the
labels "hook machine" and "CI": wherever an installed plugin is
resolvable, its engine answers; wherever none is, the project's pin
does — and in *every* context the CLI states which engine version
answered, so a checked-out repository on a machine without the plugin
gets pin semantics and says so, never a refusal and never an
unattributed answer. Same-configuration is required alongside
same-engine: for a
given project, the CLI and the hook must resolve the *same*
configuration — a nested-`.claude` or monorepo layout must not let a
directory-walking CLI and a project-root-anchored hook silently answer
from different configs — failing loudly when the resolution is
ambiguous, mechanism free.

## 10. The Maintenance Skill

The skill is the required delivery form of frisk's assistance (subagent
use behind it is implementation freedom). Its capabilities:

- **Adoption**: run the scaffold (§5.4), walk the settings pairing
  (§6.1) — asking explicit approval before every settings edit, per
  §6.1 rule 5 — offer the sentinel (§7.4), and finish with the
  reachability probe (§8.3) so adoption ends with proof, not hope.
- **Teaching the model the boundary** (optional, at the operator's
  discretion): generate a short, current summary of what this project's
  guard allows, asks about and refuses, suitable for the project's
  CLAUDE.md or an equivalent model-facing channel. This is steering, not
  enforcement — Claude Code's documentation is explicit that prompt
  guidance shapes what the model tries without changing what is allowed
  — but a model that knows the rules of the road produces fewer denials
  to recover from, and §6.2's steering reasons pick up the cases it
  still gets wrong.
- **The surprise loop**, the skill's central job and the product's
  discipline: when the operator reports a wrong verdict — a prompt on
  something harmless, silence on something that should have been caught,
  a refusal that misfires — the skill explains the verdict (via the CLI's
  citation), drafts the *most precise* rule change that addresses it, and
  drafts the reproducing case asserting the corrected verdict. The fix is
  not complete until the exact reported command is a case (§8). It then
  presents both, stating what would newly be allowed and what newly
  gated, and waits.
- **Migration**: when §7.3 reports an API-generation mismatch or a
  flipped verdict after an engine update, guide the config forward,
  case by case — working on the configuration **as text**: the skill
  reads and rewrites the file itself, so the engine needs no read-only
  mode for dropped generations, and its refusal to load is the loud
  signal that starts the migration, not an obstacle to it.
- **Doctrine enforcement in dialogue**: when an `allow` is proposed,
  present §6.3's doctrine and demand the argument; when a git ground
  rule (§5.4) is in the way, treat "the prompt annoyed me" as a case to
  report upstream, not a rule to weaken — a change needs a reason
  specific to the project, stated out loud (the two worktree asks are
  the one pair a project may reasonably drop, and only if it uses no
  worktrees). When drafting grants, prefer **shapes over lists**: an
  exemption expressed as an enumerated list fails open when the next
  addition is forgotten — nobody remembers to extend it, and forgetting
  makes things exempt — while one expressed as a structural claim (a
  path, a pattern) judges tomorrow's file the day it appears. This is
  prototyping's hardest-won configuration lesson.

One rule governs all of it: **every rule change is the operator's call.**
The skill proposes, explains consequences, and applies only on
agreement. The one exception is scaffold time, covered by the one-pass
review (§5.4). The skill never edits the configuration on its own
initiative — an assistant that could quietly rewrite the boundary would
be the vulnerability this project exists to close.

## 11. Packaging, Distribution and Versioning

- The repository is `cc-frisk`; the plugin, CLI and skill are `frisk`
  (§1). The repository is its own marketplace (§2.2), and the primary
  install source is the git repository itself; a zip archive attached to
  a GitHub release is the supported alternative source — the platform
  versions archives by SHA-256 digest, and release archives should carry
  an explicit pin in the marketplace entry so what users install is
  attestable. No third-party channel is required either way. License
  MIT.
- One codebase, two doors: the plugin (hook + skill + CLI for Claude
  Code use) and the repository-installable engine+CLI (for project CI,
  §8.2). They must be the same code at the same version — a divergence
  would make gate two prove something the hook does not run.
- Versioning is semver on the plugin. The config-facing API generation
  moves only with the major version from 1.0 on (§3.5); **during 0.x,
  it moves on any breaking release**, because pre-1.0 is when breakage
  is most likely and the fail-closed generation check must be reachable
  precisely then — a 0.x tester's config silently reinterpreted by a
  later 0.x engine would be §3.5's forbidden failure in the period the
  testers live in. Behavior-visible
  changes — any change that could move a verdict — must land in a
  changelog and in the engine corpus (§8.1): the surprise-becomes-a-test
  discipline applies to the engine itself.
- The plugin's own CI runs gate one (§8.1) plus packaging validation on
  every change — and packaging validation includes proving the shipped
  starter content: scaffold into a throwaway project, run its selftest,
  so the starter registry's spellings (the force-push denies above all)
  are demonstrated before release rather than by the first adopter,
  without weakening §8.1's engine/policy test separation; and CI should
  run gate one across an interpreter matrix — the floor version and a
  current one at minimum, before any release — so the floor is a proven
  claim, not an asserted one; a release is a version bump that reaches users through
  the marketplace's normal update flow, protected on their side by §7.3.
- Plugin code must treat its installed location as read-only and
  version-unstable (§2.2); anything the plugin persists lives in the
  per-plugin data directory, and nothing frisk does may require network
  access at runtime.

## 12. Documentation Deliverables

Deliverables of the implementation — the specification names what each
must cover and does not write them. A minimal README and SECURITY.md
are due at the first public release, everything in full by the first
stable version (§13); the README's
formatting quality is an explicit requirement, not a nicety: this is an
open-source security-adjacent tool, and the README is where trust starts.

- **README** — what frisk is and is not (the §1 scope statements),
  installation, the scaffold quickstart, the settings pairing with the
  reasoning of §6.1, and pointers to the rest. Good, readable formatting;
  a reader must be able to decide "do I want this in my permission path?"
  from it. It (or the reference it points to) should include a working
  **status-line sample** — a script consuming the CLI's output to
  display the guard's state in Claude Code's status line (§9); useful,
  not owed at first release.
- **Operator configuration reference** — the config surface of §5.2 in
  operator terms: every declaration, its conditions, its fail direction;
  the legibility requirement's public face. It enumerates **every engine
  default layer in full** — wrappers, baseline read tools, walked
  interpreters (§3.4, §4.2, §6.3) — because a default the operator
  cannot read is a rule they never agreed to.
- **The honesty document** — what frisk does not see (§4.4) and the
  residue map (§7.5), stated as plainly as in this specification. The
  document prefers admitting a limit over implying coverage.
- **The platform verification record** — the committed, operator-facing
  outcome of the verification pass (§2.1's open facts and folded-in
  items): what was measured, on which platform version, and what it
  means for the guard's behavior. This is where "record what it found"
  lands.
- **SECURITY.md** — the trust model (§5.1: config is operator-owned
  code; what the guard is and is not a defense against, §15), the
  fail-open residue and its mitigations, and how to report
  vulnerabilities.
- **CONTRIBUTING.md** — how to contribute without degrading the
  boundary: engine changes come with corpus cases, behavior changes are
  changelog-visible (§11), and the doctrine sections of this
  specification are the review bar.

## 13. Release Path

Not everything in this document ships at once, and the staging is itself
a requirement: this section sets the goals per stage; the implementation
plan decides each feature's placement within them — and the plan **opens
by re-inventorying the pre-1.0 bar below**: for each accreted item, a
written assessment of whether its *placement* still earns parity (the
items themselves are requirements and stay owed — only their stage is
challengeable, which is the reading contract's one staging exception),
proposed to the operator, who rules; the re-inventory's written record
is the plan's first artifact. This exists because the bar has only ever
grown and "reviewable by one human" is the premise under load. Two principles govern
those placements. First, **the reviewable surface is a cost even when an
AI implements**: every feature and every side case enlarges what a human
operator must review, test and trust, so shipping a feature without its
side cases is a legitimate staging choice — sometimes a side case is a
quick win taken early, sometimes it waits. Second, **deferral must never
become preclusion**: whatever is postponed, the API and architecture are
designed against the full surface of this document (§5.2), and a staging
choice that would make a later feature expensive to adopt is a wrong
choice — Future Considerations' own test (§14) applies inside the release
path too.

- **First releasable version (pre-1.0).** The bar is **prototype
  parity**: an operator running a prototype-generation project hook can
  replace it with the plugin and lose nothing — same commands judged,
  same verdicts, same test discipline. Concretely, this requires: the
  engine behaviors of §4 at least to the extent the behavior corpus
  exercises them (the corpus is the parity yardstick, §8.1); a
  configuration able to express what the starter registry and the
  corpus's policies need (§5); the hook with fail-closed runtime (§7.1),
  the control-structure routing minimum of §4.3 (keyword-led segments
  treated as unparsed — restated here, not an addition: the obligation
  is §4.3's); both classes of §7.2 — the unloadable-config deny and the
  cases-fail-on-config-change deny, the latter nearly free once §7.3's
  trigger runs the project suite in the hook — and §7.3's
  engine-version trigger — a version comparison in front of the
  already-owed selftest, cheap, and owed at parity because a prototype
  as project code could never change without the operator editing it,
  while the plugin channel updates silently from day one; gates one and two
  runnable (engine suite in the plugin's CI; liveness and selftest
  reachable from the project, §8); the check/explain command in at least
  its verdict-and-citation form (§9); and enough of the scaffold and
  pairing guidance — even in guided-manual form — that adoption is
  possible without archaeology; and, because the first public tag of a
  permission-path tool must not ship without a trust statement, a
  **minimal README** and **SECURITY.md** (at least the trust model and
  the vulnerability-reporting path) from §12. The pre-1.0 audience is
  the operator and prototype users testing the tool, and the README
  must say so prominently: **in development, install only for testing**
  — a warning removed at 1.0. That audience is also why one accepted
  residue is stated here rather than fixed: the once-per-session
  visibly-inert notice of §5.4 is owed at 1.0, not at parity, so a
  vanished config before 1.0 is caught only by the sentinel where
  adopted — acceptable for testers who know the tool's state, not for
  the 1.0 public, which is why 1.0 owes the notice. Everything else may
  ship here as a quick win, but nothing else is owed. Corpus rulings
  superseded by a verification-pass outcome — the allow rulings, if
  open fact (c) retires the verdict — count as satisfied by the
  superseding behavior and do not block the parity declaration.
- **First stable version (1.0).** The full surface of this document at
  requirement tier: the complete CLI, the skill with its whole loop
  (§10), the sentinel offer, secure mode operational, the compatibility
  contract active (§3.5; the multi-generation range and internal
  migrations may still be maturing), the settings-protection pairing,
  and every §12 document in place. Stability names the promise: from
  here, the config-facing API moves only by the rules of §3.5.
- **Beyond 1.0.** The items of §14, in whatever order adoption pressure
  and contribution supply justify.

## 14. Future Considerations

Not required now; must not be architecturally precluded. Each item argues
why deferring is safe — an item whose later adoption would be expensive
would be a present decision in disguise.

- **Rule collections beyond the project: default, community,
  organization, personal.** Two faces of one mechanism. *Default and
  community collections* — maintained rule sets for common tools — are
  the enabler that turns secure mode (§3.2) from an advanced feature
  into an everyday replacement for permissive modes. *Organization and
  personal collections* — distributed by whoever maintains them,
  plausibly as git repositories — let a company or an individual encode
  their workflow's rules and their homemade tools once and import that
  into every project, instead of re-teaching each project the same
  boundary. Deferring both is safe because §3.4 already requires
  composable, importable units with replace/update-with-removal
  override semantics: adopting collections later means adding sources
  and a distribution/trust convention (an imported collection is code
  running in the permission path — its provenance and review story is
  the hard part, and it is a distribution problem, not an engine one).
  The scaffold's starter registry is the interim.
- **A declarative configuration layer** (YAML/JSON or similar),
  conceived as a transpiler regenerating Python declarations on change —
  the natural carrier for community collections, where "data, not code" matters
  because the rules are other people's. Safe to defer: it compiles to the
  same config-facing API, which is version-stable by §3.5.
- **Transcript mining** — a command that reads a session's transcript
  (§2.1 makes this known-feasible), replays its Bash calls against the
  current config, and reports what prompted, what was denied, and which
  rule would have covered each surprise. Safe to defer: Claude Code
  already records the data; nothing accumulates that would be lost.
- **A guard-internal decision log** — complementary to transcript
  mining: transcripts are per-session, an internal log survives and
  aggregates across sessions. Safe to defer: purely additive; a writable
  home already exists (the plugin data directory, §2.2). The two share
  one goal — feeding the surprise loop — and should be designed
  together when taken up.
- **User-global configuration layered under the project's.** Ground
  rules once per machine. Safe to defer: §3.4's shadowing is already
  the needed merge semantics; a user layer is one more source below the
  project's.
- **Native Windows support.** Parsing semantics stay POSIX (the Bash
  tool runs through Git Bash there), so the engine would largely carry
  over; the blocker is dependable `python3` presence, and §7's honesty:
  claiming support that fails open unverified would be a false promise.
  The sentinel, being shell, would at least make the absence loud for
  projects that adopt it.

## 15. Non-Goals

Conscious renunciations, each with its reason and blast radius.

- **frisk is not a sandbox and not a defense against an adversary** —
  neither a malicious model nor a prompt-injected agent determined to
  evade it. It reads the command text the agent *proposes*; content that
  arrives at runtime — `curl … | sh` payloads, file contents, expansion
  output — is invisible by construction (§6.3), and a determined
  obfuscator has other channels. It is a guardrail against the ordinary
  failure mode: a well-meaning agent reaching for a destructive command.
  Blast radius: operators needing adversarial containment need OS-level
  sandboxing and credential scoping; frisk composes with those, and
  SECURITY.md says so plainly.
- **No library of per-tool semantic parsers.** Depth of structural
  analysis over breadth of integrations (§2.4); per-project declarations
  cover per-project tools. Blast radius: a tool with an exotic CLI
  grammar needs its declarations written by its operator (or, later, a
  collection, §14).
- **No auto-approval or allowlist promotion.** The boundary must not
  learn by attrition; frequency is not safety. Blast radius: operators
  wanting that convenience use other tools — hooks stack, and frisk
  composes.
- **The agent never edits the rules.** Restated from §10 as a non-goal
  because it forecloses a feature others might expect: there is no
  "let frisk tune itself" mode, by design.
- **No native Windows before 1.0** (§14). Blast radius: native-Windows
  operators get no guard and, unless they adopt the sentinel, no loud
  absence either — WSL is the supported path.
- **No network access and no telemetry, ever, at runtime.** Code in the
  permission path must be auditable and inert; its only inputs are the
  hook payload and the project's own files. Blast radius: usage
  insight for maintainers comes from issues and contributed cases, not
  measurement.
- **frisk does not replace the permission system.** It pairs with it
  (§6.1): broad allows give it room, the deny backstop outlives it,
  modes still set the default posture. Blast radius: an operator who
  deletes their backstop because "the guard covers it" has removed the
  layer that survives the guard's death — §7.5's last line exists to
  prevent exactly that reading.
