# What the operator documentation owes

An index, not an explanation. Every entry names a behaviour this
implementation settled that a *user* has to be told about, and where the
ruling is written down. Read it when writing any §12 deliverable; it is
the list of things a reader of the specification alone would not know.

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
| That `--value` prints only the declarations that could answer the value, and that it is a temporary window on three-valued matching which retires when `explain` returns verdicts | `D-046`; `Registry.describe` |
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
| That `explain` on a project with no configuration still reads the line, says on stderr that nothing is gated, and never returns 0 | §5.4; `cli.explain_command` |
