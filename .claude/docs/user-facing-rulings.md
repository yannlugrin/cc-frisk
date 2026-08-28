# What the operator documentation owes

An index, not an explanation. Every entry names a behaviour this
implementation settled that a *user* has to be told about, and where the
ruling is written down. Read it when writing any §12 deliverable; it is
the list of things a reader of the specification alone would not know.

One standing lesson, learned when `explain` printed `unproven:
unreadable` and the operator had to ask what it meant: **an internal
name is never an explanation**. Every word frisk prints is read by
someone deciding whether to allow something, and they do not know the
engine's vocabulary. A category tells them which bucket; they need what
was wrong and what would fix it. This binds §6.2's reasons and
citations as much as any §12 page.

Nothing here restates a reason — `DECISIONS.md` holds those, and the
contracts hold the rest. An entry that stops being true is deleted, not
corrected: the source it points at is the copy that matters.

§12's own list (the honesty document's blind spots, the `$VAR` policy,
the enumerated default layers) is a requirement and lives in the
specification. This file is what accumulated *beside* it.

| What the user must be told | Where the ruling lives |
|---|---|
| Why a boundary can answer "cannot decide", and that it costs a prompt rather than a refusal | §3.2; `matchers.py` module docstring |
| That an absolute path is judged against a relative boundary by asking what any working directory could make true — so `/etc/passwd` is *outside* `.scratch` but merely *unknown* against `./etc` | `D-037`; §3.2 as amended |
| That a `cd` earlier on the line makes later relative paths unprovable, subshells included, and that pattern matchers are untouched by it | §3.2; `matchers.py` |
| That `~` is expanded from the environment, and `~other` cannot be | `D-035` (3) |
| That `path_under` is a boundary and `path_matching` is not — what is under a matched path is not itself matched | `D-035` (1) |
| That a command with no operands never satisfies "every operand" | `D-035` (2); `declare.every_operand` |
| That a tool is named once, and a separator in the name is what makes it a path — `./deploy.py` for a script at the project root | `D-034`; `declare.tool` |
| Why an absolute path is refused in a declaration | `D-034`; `declare.tool` |
| That a declared path *may* leave the project — `../shared/deploy.py` for a neighbouring checkout — and what makes that narrow: it holds only while the two keep their relative positions, and matches only a command line spelled with the same prefix | `D-044`; `declare.tool` |
| That declaring a grant closes a tool's world, that `closed_world` says so without one, and that dropping the last grant re-opens a world nobody closed on purpose | `D-034`; `declare.amend` |
| That a removal travels inside the list it acts on, and what a label is | `D-034`; `declare.drop` |
| That a value-optional flag can declare what a bare use means, and that without it a condition on its value is unprovable | `D-039`; `declare.may_take_value` |
| That an amendment corrects an arity or narrows a matcher by re-declaring, never by dropping first | `declare.amend`; the composition suite |
| That collections compose in the order the configuration adopts them, and the operator's own declarations always win wherever they sit | §3.4; `registry.py` module docstring |
| That a collection ships the cases for its own rules, and adopting it brings them | §8.2; `Registry.cases` |
| That a collection may adopt another, and composes *over* what it adopted — whoever adopts decides, the same rule that puts the operator last | `Recording.adopt`; `registry.py` module docstring |
| What `frisk registry` prints, field by field — and that `gated:` says *why* | `Registry.describe` |
| That the registry's cases are hidden until `--cases`, and `--no-wrap` exists for whatever parses the output | `D-036`; `cli.py` |
| Which programs the engine walks as wrappers, shells and interpreters, and that the set is a floor | `D-038`; `defaults.py`; the defaults suite |
| That the display and locale variables are excused for every tool, and that nothing which can direct execution is | §3.2; `declare.benign_assignments` |
| That a `drop(...)` naming something no layer beneath declares is refused, exactly as an `amend` of an undeclared name is — a removal that silently does nothing is a boundary the operator believes they have | `registry.py` composition; the composition suite |
| That the API generation is declared once for a whole configuration, adopted collections included | `config.py`; `declare.api_generation` |
| Where the configuration lives and what the API generation declaration is for | `D-033`; `config.py` |
| That a deprecated generation still loads and every rule in it still holds, and that the nudge to migrate goes to stderr so a script reading the registry never meets it | §3.5; `config.deprecation` |
| That a `predicate()` callable runs on the decision path and is the one matcher frisk cannot promise touches no filesystem — it is the configuration's code | `declare.predicate`; `matchers.py` module docstring |
| That a regular expression a configuration declares is run against agent-supplied text with no backtracking bound, since the configuration is trusted code (§5.1) | `matchers.compiled`; §12's blind-spot list |
| That a configuration which will not load denies rather than proceeds | §7.1; `config.load` |
| That a rule naming one spelling of a flag misses the other — `flag("--force")` does not match `-f` — because a `FlagSet` groups names by *arity*, never by identity, and `any_flag("-f", "--force")` is how either spelling is written | `declare.any_flag`; `Entry.flags` |
| That bundling is on by default and `bundled=False` turns it off, and that the residue is a run mixing declared and undeclared letters — `-fq` with `-q` undeclared stays one unaccounted flag, so declaring the letters a rule cares about is what closes it | `D-050`; `declare.tool`; §8.2's coverage gate |
| That `explain` on a project with no configuration still reads the line and prints a verdict, says on stderr that nothing is gated, and answers 4 rather than the verdict's own status — a verdict reached against no boundary is not one a script may trust | `D-055`; §5.4; `cli.explain_command` |
| What each `explain` exit status means, and that **silence is 0** because silence is a real answer — so `frisk explain "$cmd" \|\| refuse` refuses exactly where frisk objected or could not answer | `D-055`; `cli.py` |
| That an `ask` or `deny` reason is steering text the *model* reads, so it names the acceptable path and not only the objection | §6.2; `judging.py` module docstring |
| That a verdict names every declaration at the deciding rank across the whole line, and never the weaker matches beneath it | §6.2; `judging.judge` |
| That a tool's declared flag list is an **opt-in list the operator steers by editing**: on a gated tool a flag outside it asks in its own right, so taking a flag out is how you make it ask | `D-056`; `declare.tool` |
| That a tool's default verdict is a **fallback**, not a floor — a rule the operator wrote is never undercut by it, and an unconditional `deny()` rule is how a floor is spelled | `D-059`; `judging._default` |
| That an undeclared flag's arity is an ambiguity, so a rule is matched against every operand alignment it admits and the strictest verdict stands — declaring the options is what makes an answer exact rather than the strictest of several readings | `D-060`; §4.2 as amended |
| That an unparseable line asks when it names a tool carrying rules or grants, and is silent otherwise — and that this is the one place frisk scans raw text | §4.1; `judging._unparseable` |
| That `$VAR` in command position is silence in the default posture, and the global default in secure mode | §4.2; `judging._unregistered`; §12 owes this one by name |
| That secure mode exists as an engine capability with no switch to turn it on until `033`, so no configuration can reach it yet | `PLAN.md` `033`; `judging.judge` |
| That a line earning an `allow` answers silence until the hedges ship, so `allow` is declarable and never returned | `D-051`; `judging.combined` |
| That `--` is structure rather than a flag, so a gated tool does not have to declare it and `deploy --check -- file.yml` stays provable | `D-061`; `judging._unaccounted_flags` |
| That a reason **frisk itself** writes explains what is wrong and never tells the agent to remove a token — an unaccounted flag may be the one protecting the deploy | `D-062`; `judging.py`'s reason constants |
| That an unproven tool identity (a relative spelling after a `cd`) defeats grants and caps a deny at ask, but adds no verdict of its own — a line nothing gates stays silent, and the unresolved token is named only where something else objected | `D-054`; `D-063`; `judging._doubts` |
| That the engine's own failure answers 6, distinct from every verdict, because 1 is `ask` and a dead guard must not read as a prompt | `D-055`; `cli.EXIT_ENGINE_ERROR` |
