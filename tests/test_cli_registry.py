"""`frisk registry` — the door onto §3.4's inspection requirement.

Composition must never be able to hide a rule, which makes the effective
registry something an operator has to be able to *read*, not something
the engine merely holds. This is that surface, and it is also how every
later step's manual test is performed: write a configuration by hand,
print what it composed, and see whether it is what was meant.

Three outcomes and three statuses, because the difference between them
is the difference between a boundary and the absence of one: a registry
printed, no configuration at all (§5.4's visibly inert case), and a
configuration that would not load (§7.1). The channel discipline of the
existing command line holds here too — stdout carries answers, stderr
carries failures — so a script that captures stdout never mistakes a
failure for an empty registry.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from test_cli import run

from frisk import __version__
from frisk.cli import EXIT_CONFIG_ERROR, EXIT_NO_CONFIG
from frisk.config import CURRENT_GENERATION, config_path

CONFIG = f"""
from frisk.declare import (
    DENY,
    api_generation,
    ask,
    case,
    deny,
    flag,
    one_of,
    tool,
)

api_generation({CURRENT_GENERATION})

tool(
    "stubtool",
    default=ask(reason="stubtool changes infrastructure."),
    rules=[
        deny(
            "wipe",
            reason="Wiping has no authorized use here.",
            label="wipe denies",
        ),
        ask(
            "apply",
            when=flag("--mode", one_of("destroy")),
            reason="A destroying mode.",
        ),
    ],
    cases=[case("stubtool wipe", DENY)],
)
"""


class RegistryCommandTests(unittest.TestCase):
    """What the command answers, and on which stream."""

    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def write(self, body: str) -> None:
        target = config_path(self.root)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body)

    def test_a_configured_project_prints_its_registry(self) -> None:
        self.write(CONFIG)
        status, out, err = run("registry", "--project", str(self.root))
        self.assertEqual(status, 0)
        self.assertIn("stubtool", out)
        self.assertIn("wipe denies", out)
        self.assertEqual(err, "")

    def test_the_header_is_three_lines_in_a_fixed_order(self) -> None:
        # Engine, configuration, generation — which engine answered,
        # from which file, against which contract. §9 asks for the
        # first in every context; the other two are what make a
        # registry an answer about a known project.
        self.write(CONFIG)
        _, out, _ = run("registry", "--project", str(self.root))
        lines = out.splitlines()
        self.assertEqual(lines[0], f"frisk {__version__}")
        self.assertEqual(lines[1], f"config: {config_path(self.root)}")
        self.assertEqual(lines[2], f"generation: {CURRENT_GENERATION}")
        self.assertEqual(lines[3], "")

    def test_an_unconfigured_project_is_unmissable(self) -> None:
        # §5.4: an installed guard silently implying coverage is the
        # false-safety failure §7 exists to prevent. An empty registry
        # on stdout would be exactly that.
        status, out, err = run("registry", "--project", str(self.root))
        self.assertEqual(status, EXIT_NO_CONFIG)
        self.assertEqual(out, "")
        self.assertIn("no configuration", err.lower())

    def test_a_configuration_that_will_not_load_is_loud(self) -> None:
        # An out-of-range generation, not a config that fails to
        # import: both are loud, and only one is the refusal §3.5 asks
        # for. Without the import this reads like the first and is the
        # second.
        self.write(
            "from frisk.declare import api_generation\n\napi_generation(0)\n"
        )
        status, out, err = run("registry", "--project", str(self.root))
        self.assertEqual(status, EXIT_CONFIG_ERROR)
        self.assertEqual(out, "")
        self.assertTrue(err.strip())

    def test_a_value_shows_what_each_matcher_answers(self) -> None:
        self.write(CONFIG)
        _, out, _ = run(
            "registry", "--project", str(self.root), "--value", "destroy"
        )
        self.assertIn("[satisfied]", out)
        _, other, _ = run(
            "registry", "--project", str(self.root), "--value", "check"
        )
        self.assertIn("[unsatisfied]", other)
        self.assertNotIn("[satisfied]", other)

    def test_the_flags_reach_the_registry(self) -> None:
        # The three the layout contract defines: cases hidden until
        # asked for, the composed list alone, and one record per line
        # for whatever reads this without a JSON option (D-036).
        self.write(CONFIG)
        project = str(self.root)
        _, plain, _ = run("registry", "--project", project)
        self.assertNotIn("cases:", plain)

        _, shown, _ = run("registry", "--project", project, "--cases")
        self.assertIn("cases:", shown)

        _, only, _ = run("registry", "--project", project, "--cases-only")
        self.assertNotIn("tool(stubtool)", only)

        _, unwrapped, _ = run("registry", "--project", project, "--no-wrap")
        for line in unwrapped.splitlines():
            with self.subTest(line=line):
                self.assertFalse(line.startswith("        "))

    def test_the_output_is_ascii_and_escapes_what_it_prints(
        self,
    ) -> None:
        # A reason is text the configuration supplies, and this output
        # is read by a human deciding what their boundary is: a newline
        # or a terminal escape inside a reason must not be able to
        # forge a line of frisk's own output.
        self.write(
            f"from frisk.declare import api_generation, ask, tool\n\n"
            f"api_generation({CURRENT_GENERATION})\n\n"
            'tool("stubtool", default=ask(reason="one\\ntwo\\x1b[2K"))\n'
        )
        _, out, _ = run("registry", "--project", str(self.root))
        self.assertTrue(out.isascii())
        self.assertNotIn("\x1b", out)
        # The reason survives as one escaped line: its newline must not
        # have become a line break in frisk's own output, which is what
        # forging a line means here.
        self.assertIn("one\\ntwo", out)
        self.assertNotIn("one\ntwo", out)
