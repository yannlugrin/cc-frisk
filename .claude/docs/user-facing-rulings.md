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
| That declaring a grant closes a tool's world, that `closed_world` says so without one, and that dropping the last grant re-opens a world nobody closed on purpose | `D-034`; `declare.amend` |
| That a removal travels inside the list it acts on, and what a label is | `D-034`; `declare.drop` |
| That a value-optional flag can declare what a bare use means, and that without it a condition on its value is unprovable | `D-039`; `declare.may_take_value` |
| That an amendment corrects an arity or narrows a matcher by re-declaring, never by dropping first | `declare.amend`; the composition suite |
| That collections compose in the order the configuration adopts them, and the operator's own declarations always win wherever they sit | §3.4; `registry.py` module docstring |
| That a collection ships the cases for its own rules, and adopting it brings them | §8.2; `Registry.cases` |
| What `frisk registry` prints, field by field — and that `gated:` says *why* | `Registry.describe` |
| That the registry's cases are hidden until `--cases`, and `--no-wrap` exists for whatever parses the output | `D-036`; `cli.py` |
| Which programs the engine walks as wrappers, shells and interpreters, and that the set is a floor | `D-038`; `defaults.py`; the defaults suite |
| That the display and locale variables are excused for every tool, and that nothing which can direct execution is | §3.2; `declare.benign_assignments` |
| Where the configuration lives and what the API generation declaration is for | `D-033`; `config.py` |
| That a configuration which will not load denies rather than proceeds | §7.1; `config.load` |
