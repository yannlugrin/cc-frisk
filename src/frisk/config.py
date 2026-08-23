"""Where the configuration lives, and how it is loaded (§5.1, §3.5).

**The location is a convention, fixed once.** The configuration lives in
`.claude/frisk/` inside the project, and the file the engine executes is
`config.py` in it. §5.1 requires a dedicated directory inside the
project's `.claude/` whose name carries the plugin's name, and leaves the
exact name to the implementation; this is that choice, made here rather
than at the scaffold because every later step's test instructions, the
hook's resolution and the CLI's same-configuration requirement (§9) all
presuppose a path. The scaffold creates the directory; it does not get to
invent where it goes.

**The configuration is trusted code**, executed by the hook and the CLI
(§5.1). It sits at exactly the trust level of a hand-written hook in the
same directory — which is what it replaces — and frisk must not enlarge
that surface: nothing here executes anything received over a network,
and the only file executed is the project's own, plus the collections it
adopts from beside it.

**Loading a configuration is linear in its size, and re-parsed every
time.** `exec(compile(source))` writes no `__pycache__`, so what an
imported module pays once this pays on every load. Measured on this
workstation (Python 3.14.4, 2026-08-23) with a generated configuration
of N deny rules spread over T tools, twenty loads averaged: 100 rules
over 10 tools, 1.01 ms with 0.35 ms of it compiling; 1000 rules over 50
tools, 11.23 ms with 4.51 ms compiling. Composition is the rest and is
cheap. §4.5 budgets a per-call decision in single-digit milliseconds,
so a large configuration spends it before anything is judged — which is
a question for the step that builds the hook door (`PLAN.md` `021`),
not for this one: `frisk registry` can afford it and there is no hook
yet. The remedy, if `021` wants one, is to import the configuration as
a module (`importlib.util.spec_from_file_location`) and let CPython
cache its bytecode, at the cost of a `__pycache__` beside the
operator's config and an entry in `sys.modules`. Re-measure by
regenerating such a configuration and timing `load()` against
`compile()` alone.

**Loading fails closed.** A configuration that raises, declares no API
generation, or declares one outside the range the engine speaks does not
produce a partial registry: it raises `ConfigurationError`, and §7.1
turns that into a deny that says what broke. Misreading a configuration
is worse than refusing it, because it is silent and plausible where
deny-all is loud.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .errors import ConfigurationError
from .registry import PROJECT_LAYER, Registry, collecting

#: The directory, relative to the project root, and the file in it.
CONFIG_DIRECTORY = ".claude/frisk"
CONFIG_FILENAME = "config.py"

#: The API generation this engine writes, and the contiguous range it
#: speaks (§3.5). The range is contiguous by construction — a tuple of
#: consecutive integers — because "recent older generations still
#: load" is the promise, and a range with a hole in it is not one.
#: Deprecated generations still load, with a visible nudge toward
#: migration; outside the range the engine refuses.
CURRENT_GENERATION = 1
SUPPORTED_GENERATIONS = (1,)
DEPRECATED_GENERATIONS: tuple[int, ...] = ()


def config_path(project_root: Path) -> Path:
    """The configuration file for a project root."""
    return project_root / CONFIG_DIRECTORY / CONFIG_FILENAME


def locate(start: Path) -> Path | None:
    """The configuration governing `start`, or None if unconfigured.

    The walk goes upward from `start` and stops at the first
    `.claude/frisk/config.py` it finds. An unconfigured project is not
    an error here: an enabled plugin with no configuration gates
    nothing and must say so visibly (§5.4), which is a message, not a
    failure.
    """
    for directory in [start, *start.parents]:
        candidate = config_path(directory)
        if candidate.is_file():
            return candidate
    return None


def load(path: Path) -> Registry:
    """Execute a configuration and compose its effective registry.

    Raises `ConfigurationError` for anything that makes the boundary
    unreadable — a declaration error, a missing or out-of-range API
    generation, a collection that is not beside the config.
    """
    if not path.is_file():
        raise ConfigurationError(
            f"no configuration at '{path}': frisk reads "
            f"{CONFIG_FILENAME} in {CONFIG_DIRECTORY}/ inside the "
            "project."
        )
    namespace: dict[str, Any] = {
        "__name__": "frisk_configuration",
        "__file__": str(path),
    }
    with collecting(
        PROJECT_LAYER, base_dir=path.parent, with_defaults=True
    ) as declared:
        try:
            # The bytes, not the text: Python source is UTF-8 by
            # definition (PEP 3120), and `read_text()` would decode it
            # with whatever the locale prefers — so a configuration
            # holding one accented reason would load on a workstation
            # and deny everything under `LC_ALL=C`. Handing `compile`
            # the bytes is what CPython does for a source file: the
            # BOM and a coding cookie are its business, not ours.
            exec(compile(path.read_bytes(), str(path), "exec"), namespace)
        except ConfigurationError:
            raise
        except SystemExit as failure:
            # `SystemExit` is a `BaseException`, so it would otherwise
            # walk straight out of here and end the process with the
            # status the *configuration* chose — exit 0 for a boundary
            # nothing composed, which is the one direction §7.1
            # forbids. A config that grew out of a script and kept its
            # `sys.exit(main())` is all it takes.
            raise ConfigurationError(
                f"the configuration at '{path}' exited instead of "
                f"loading (status {failure.code!r}). A configuration "
                "declares; it does not end the process."
            ) from failure
        except Exception as failure:
            # Everything else a configuration can do — a syntax error,
            # a name it misspelled, an exception of its own — is one
            # event to the caller: the boundary cannot be read.
            raise ConfigurationError(
                f"the configuration at '{path}' did not load: "
                f"{failure.__class__.__name__}: {failure}"
            ) from failure
    registry = declared.registry()
    _speakable(path, registry.generation())
    return registry


def _speakable(path: Path, generation: int | None) -> None:
    """Refuse a contract this engine does not know, and say so.

    Misreading a configuration is worse than refusing it: a refusal is
    loud where a misreading is silent and plausible. The message names
    both numbers and points at the migration help, because a refusal
    with no way forward is how an operator ends up deleting the guard
    instead of upgrading it (§3.5).
    """
    spoken = (
        f"this frisk speaks generation {CURRENT_GENERATION}"
        if len(SUPPORTED_GENERATIONS) == 1
        else (
            f"this frisk speaks generations {min(SUPPORTED_GENERATIONS)} "
            f"to {max(SUPPORTED_GENERATIONS)}, and writes "
            f"{CURRENT_GENERATION}"
        )
    )
    forward = (
        "The frisk skill migrates a configuration between generations; "
        "ask it rather than editing blind."
    )
    if generation is None:
        raise ConfigurationError(
            f"the configuration at '{path}' declares no API generation. "
            "It is how a configuration says which contract it expects, "
            f"and its absence is not a version: {spoken}. {forward}"
        )
    if generation not in SUPPORTED_GENERATIONS:
        raise ConfigurationError(
            f"the configuration at '{path}' declares API generation "
            f"{generation}, and {spoken}. {forward}"
        )
