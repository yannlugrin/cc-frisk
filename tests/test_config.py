"""Where the configuration is, and what loading it refuses (§5.1, §3.5).

Two things are settled here and depended on everywhere afterwards: the
path a project's boundary lives at, and the failure direction when the
file at that path cannot be trusted. §5.1 fixes the shape — a dedicated
directory inside the project's `.claude/`, named for the plugin — and
leaves the name to the implementation; these cases are that choice made
explicit, so a later step cannot quietly move it.

The compatibility contract of §3.5 is the other half: a configuration
declares the API generation it was written against, and a generation the
engine does not speak is a refusal, never a guess. Misreading a
configuration is worse than denying everything, because it is silent and
plausible where deny-all is loud.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from frisk.config import (
    CONFIG_DIRECTORY,
    CONFIG_FILENAME,
    CURRENT_GENERATION,
    DEPRECATED_GENERATIONS,
    SUPPORTED_GENERATIONS,
    config_path,
    load,
    locate,
)
from frisk.errors import ConfigurationError

VALID = """
from frisk.declare import api_generation, ask, tool

api_generation({generation})

tool("git", rules=[ask("push", reason="A push publishes work.")])
"""


class ProjectFixture(unittest.TestCase):
    """A scratch project with a configuration directory in it."""

    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def write(self, body: str, *, root: Path | None = None) -> Path:
        target = config_path(root or self.root)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body)
        return target


class LocationTests(ProjectFixture):
    """One directory, one name, fixed here rather than at the scaffold."""

    def test_the_convention_is_the_plugin_s_own_directory(self) -> None:
        self.assertEqual(CONFIG_DIRECTORY, ".claude/frisk")
        self.assertEqual(CONFIG_FILENAME, "config.py")

    def test_the_path_is_built_from_the_project_root(self) -> None:
        self.assertEqual(
            config_path(Path("/srv/project")),
            Path("/srv/project/.claude/frisk/config.py"),
        )

    def test_it_is_found_from_a_directory_inside_the_project(
        self,
    ) -> None:
        written = self.write(VALID.format(generation=CURRENT_GENERATION))
        deep = self.root / "src" / "engine"
        deep.mkdir(parents=True)
        self.assertEqual(locate(deep), written)

    def test_an_unconfigured_project_is_not_an_error(self) -> None:
        # An enabled plugin with no configuration gates nothing and
        # must say so visibly (§5.4) — a message, not a failure.
        self.assertIsNone(locate(self.root))

    def test_the_nearest_configuration_answers(self) -> None:
        # A nested `.claude` must not let a walk answer from the outer
        # project's boundary (§9's same-configuration requirement).
        self.write(VALID.format(generation=CURRENT_GENERATION))
        inner = self.root / "vendor" / "tool"
        inner.mkdir(parents=True)
        nested = self.write(
            VALID.format(generation=CURRENT_GENERATION), root=inner
        )
        self.assertEqual(locate(inner), nested)


class GenerationTests(ProjectFixture):
    """The compatibility contract's second layer (§3.5)."""

    def test_the_engine_speaks_the_generation_it_writes(self) -> None:
        self.assertIn(CURRENT_GENERATION, SUPPORTED_GENERATIONS)

    def test_the_supported_range_is_contiguous(self) -> None:
        # "Recent older generations still load" is the promise, and a
        # range with a hole in it is not one.
        self.assertEqual(
            list(SUPPORTED_GENERATIONS),
            list(
                range(
                    min(SUPPORTED_GENERATIONS),
                    max(SUPPORTED_GENERATIONS) + 1,
                )
            ),
        )

    def test_a_deprecated_generation_is_still_a_supported_one(
        self,
    ) -> None:
        # Deprecated means accepted with a nudge, not dropped. Stated
        # as a set relation rather than a loop, so that it is an
        # assertion today, with nothing deprecated yet, rather than an
        # empty loop passing for a case.
        self.assertLessEqual(
            set(DEPRECATED_GENERATIONS), set(SUPPORTED_GENERATIONS)
        )

    def test_a_configuration_in_range_loads(self) -> None:
        registry = load(
            self.write(VALID.format(generation=CURRENT_GENERATION))
        )
        self.assertEqual(registry.generation(), CURRENT_GENERATION)
        self.assertIsNotNone(registry.lookup("git"))
        # And the engine's own layers came with it. Composing a real
        # configuration without them is silent by construction — the
        # first symptom would be a walk through `sudo` reaching nothing
        # — and every other case that proves the layers exist builds
        # its registry by hand rather than by loading a file.
        self.assertIsNotNone(registry.lookup("sudo"))

    def test_a_generation_the_engine_does_not_speak_is_refused(
        self,
    ) -> None:
        beyond = max(SUPPORTED_GENERATIONS) + 1
        with self.assertRaises(ConfigurationError) as raised:
            load(self.write(VALID.format(generation=beyond)))
        message = str(raised.exception)
        # Both numbers as numbers, not as digits appearing somewhere in
        # a path or a version string: the operator has to be able to
        # read what they wrote and what this engine speaks.
        self.assertRegex(message, rf"\b{beyond}\b")
        self.assertRegex(message, rf"\b{CURRENT_GENERATION}\b")
        self.assertIn("generation", message.lower())

    def test_the_refusal_points_at_the_migration_help(self) -> None:
        # §3.5: fail closed with a message pointing at the skill's
        # migration assistance. A refusal with no way forward is how an
        # operator ends up deleting the guard instead of upgrading it.
        with self.assertRaises(ConfigurationError) as raised:
            load(self.write(VALID.format(generation=0)))
        # "frisk" would be satisfied by the configuration's own path;
        # what §3.5 requires is a pointer to the migration assistance.
        self.assertIn("migrat", str(raised.exception).lower())

    def test_a_configuration_declaring_no_generation_is_refused(
        self,
    ) -> None:
        # The declaration is how a config says which contract it
        # expects; its absence is not a version.
        with self.assertRaises(ConfigurationError):
            load(self.write("from frisk.declare import tool\n\ntool('git')\n"))

    def test_declaring_the_generation_twice_is_refused(self) -> None:
        body = VALID.format(generation=CURRENT_GENERATION)
        body += f"\napi_generation({CURRENT_GENERATION})\n"
        with self.assertRaises(ConfigurationError):
            load(self.write(body))


class LoadFailureTests(ProjectFixture):
    """Nothing half-loaded ever reaches the engine (§7.1)."""

    def test_a_configuration_that_raises_is_a_configuration_error(
        self,
    ) -> None:
        body = VALID.format(generation=CURRENT_GENERATION)
        body += "\nraise ValueError('boom')\n"
        with self.assertRaises(ConfigurationError) as raised:
            load(self.write(body))
        self.assertIn("boom", str(raised.exception))

    def test_a_configuration_that_exits_is_refused(self) -> None:
        # Added during implementation, not at the gate. `SystemExit` is
        # a `BaseException`, so it walked out of the loader untouched
        # and ended the process with the status the *configuration*
        # chose — exit 0, no registry, no message, for a boundary
        # nothing composed. §7.1 asks for a deny; a config that grew
        # out of a script and kept its `sys.exit(main())` got silence.
        body = VALID.format(generation=CURRENT_GENERATION)
        body += "\nraise SystemExit(0)\n"
        with self.assertRaises(ConfigurationError):
            load(self.write(body))

    def test_a_configuration_that_will_not_parse_is_refused(
        self,
    ) -> None:
        with self.assertRaises(ConfigurationError):
            load(self.write("tool('git'\n"))

    def test_a_missing_configuration_is_refused_by_name(self) -> None:
        with self.assertRaises(ConfigurationError) as raised:
            load(config_path(self.root))
        self.assertIn(CONFIG_FILENAME, str(raised.exception))

    def test_a_collection_beside_the_configuration_is_adopted(
        self,
    ) -> None:
        # `use()` resolves against the configuration's own directory,
        # which is the only place the engine executes files from.
        written = self.write(
            "from frisk.declare import api_generation, use\n\n"
            f"api_generation({CURRENT_GENERATION})\n"
            "use('starter')\n"
        )
        (written.parent / "starter.py").write_text(
            "from frisk.declare import ask, tool\n\n"
            "tool('docker', rules=[ask('push', reason='A registry.')])\n"
        )
        registry = load(written)
        self.assertIsNotNone(registry.lookup("docker"))
