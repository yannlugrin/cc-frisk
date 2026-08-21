"""Policy fixtures transcribed from `.claude/refs/behavior-corpus.md`.

These are **test-only declarations**. §8.1 forbids the engine suite to
run against the shipped starter registry's real-tool rules, so the
policy contexts the corpus adjudicates are reproduced here, in this
repository's own words, and the shipped collections stay untouched by
anything under `tests/`.

Each module declares one of the corpus's policy contexts and nothing
else: no assertions, no verdicts. What a context is *for* differs by
step — expressibility here, whole-line verdicts once there is an engine
to produce them — and a fixture that carried its own expectations would
have to be rewritten at every one of them.

A context declares inside the collection a caller has open, so it is a
function rather than module-level code: a module declares once and then
sits in `sys.modules` saying nothing to the second composition.
"""
