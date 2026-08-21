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

**Loading fails closed.** A configuration that raises, declares no API
generation, or declares one outside the range the engine speaks does not
produce a partial registry: it raises `ConfigurationError`, and §7.1
turns that into a deny that says what broke. Misreading a configuration
is worse than refusing it, because it is silent and plausible where
deny-all is loud.
"""

from __future__ import annotations

from pathlib import Path

from .registry import Registry

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
    raise NotImplementedError


def locate(start: Path) -> Path | None:
    """The configuration governing `start`, or None if unconfigured.

    The walk goes upward from `start` and stops at the first
    `.claude/frisk/config.py` it finds. An unconfigured project is not
    an error here: an enabled plugin with no configuration gates
    nothing and must say so visibly (§5.4), which is a message, not a
    failure.
    """
    raise NotImplementedError


def load(path: Path) -> Registry:
    """Execute a configuration and compose its effective registry.

    Raises `ConfigurationError` for anything that makes the boundary
    unreadable — a declaration error, a missing or out-of-range API
    generation, a collection that is not beside the config.
    """
    raise NotImplementedError
