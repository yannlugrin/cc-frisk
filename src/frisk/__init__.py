"""frisk — a parsing-based guard for Claude Code's Bash tool.

The engine is the generic half of frisk: it parses a command line,
walks through whatever hides an invocation, and judges what it finds
against a per-project configuration it never writes to.

Two properties of this package are load-bearing rather than stylistic,
and both are requirements of `SPECIFICATIONS.md` §3.1:

* **Standard library only, zero dependencies.** This code sits in the
  permission path, so what a user can read is what they are trusting,
  and the install channel is build-free.
* **Python 3.9 or later, with no second code path for newer
  interpreters.** The interpreter is whatever the operator's OS
  shipped; an engine it cannot parse makes the hook fail *open*, and a
  dual path would let the test suite vouch for a branch the hook never
  runs.
"""

__all__ = ["__version__"]

#: The engine's version, and the plugin's (§11: one codebase, two
#: doors, the same version). This assignment is the single source:
#: `pyproject.toml` reads it at build time, and the CLI reports it
#: without the package being installed at all, which the plugin door
#: requires. There is nothing to bump anywhere else.
__version__ = "0.1.0"
