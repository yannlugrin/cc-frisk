"""The package's promises: zero dependencies, a floor, a working door.

All three are silent when broken. A third-party import only fails on a
machine that lacks the package — never on the one that added it; syntax
from a newer Python only fails on an interpreter older than this one,
where it makes the hook fail *open*; and a console-script target that no
longer resolves fails at install time on somebody else's CI.
"""

from __future__ import annotations

import ast
import importlib
import importlib.util
import os
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parent.parent
PACKAGE = REPOSITORY / "src" / "frisk"
PYPROJECT = REPOSITORY / "pyproject.toml"

#: Where this interpreter keeps its standard library. Taken from a
#: module that is unambiguously part of it, because inside a virtual
#: environment sysconfig's "stdlib" path names a directory that does not
#: exist.
STDLIB = Path(os.__file__).resolve().parent

#: The committed interpreter floor (D-029), as `ast.parse` wants it.
FLOOR = (3, 9)


def imported_roots(source: str) -> set[str]:
    """The top-level module names an absolute import would reach for."""
    roots: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        # level > 0 is a relative import: inside this package.
        elif (
            isinstance(node, ast.ImportFrom)
            and node.level == 0
            and node.module
        ):
            roots.add(node.module.split(".")[0])
    return roots


def is_standard_library(name: str) -> bool:
    spec = importlib.util.find_spec(name)
    if spec is None:
        return False
    origin = spec.origin
    if origin is None or origin in ("built-in", "frozen"):
        return True
    resolved = Path(origin).resolve()
    if "site-packages" in resolved.parts:
        return False
    return STDLIB in resolved.parents


def modules() -> list[Path]:
    found = sorted(PACKAGE.rglob("*.py"))
    assert found, "no engine modules found under " + str(PACKAGE)
    return found


class ZeroDependenciesTest(unittest.TestCase):
    def test_the_engine_imports_nothing_outside_the_standard_library(
        self,
    ) -> None:
        for module in modules():
            for root in sorted(imported_roots(module.read_text())):
                if root == "frisk":
                    continue
                with self.subTest(module=module.name, imports=root):
                    self.assertTrue(
                        is_standard_library(root),
                        root + " is not in the standard library",
                    )

    def test_the_check_would_catch_a_third_party_import(self) -> None:
        # The negative control: without it, a scan that found nothing
        # and a scan that looked at nothing read the same.
        roots = imported_roots(
            "import os\nfrom frisk.cli import main\nimport requests\n"
        )
        self.assertEqual(roots, {"os", "frisk", "requests"})
        self.assertTrue(is_standard_library("os"))
        self.assertFalse(is_standard_library("requests"))

    def test_relative_imports_are_not_mistaken_for_dependencies(self) -> None:
        self.assertEqual(imported_roots("from . import __version__\n"), set())


class FloorTest(unittest.TestCase):
    """Syntax, judged against the floor rather than this interpreter.

    A cheap local half of the floor check (D-030): `feature_version`
    makes this interpreter refuse grammar the floor does not have — a
    `match` statement above all, which is exactly what a parsing engine
    invites. It is partial by construction, so CI runs the suite on a
    real floor interpreter as well.
    """

    def test_every_module_parses_as_the_floor_would_parse_it(self) -> None:
        for module in modules() + sorted(Path(__file__).parent.glob("*.py")):
            with self.subTest(module=module.name):
                ast.parse(
                    module.read_text(),
                    filename=str(module),
                    feature_version=FLOOR,
                )

    def test_the_check_would_catch_syntax_the_floor_lacks(self) -> None:
        newer = "match command:\n    case []:\n        pass\n"
        ast.parse(newer)  # this interpreter is happy with it
        with self.assertRaises(SyntaxError):
            ast.parse(newer, feature_version=FLOOR)


class MetadataTest(unittest.TestCase):
    """Read as text, so the floor's own interpreter can run this too.

    `tomllib` arrived in 3.11 and the floor is 3.9, so a TOML parser is
    not available where this suite most needs to run. The three lines
    checked here are exact spellings; `check-toml` in the commit hooks
    answers the parse question.
    """

    def setUp(self) -> None:
        self.pyproject = PYPROJECT.read_text().splitlines()

    def test_the_declared_floor_is_the_committed_one(self) -> None:
        self.assertIn('requires-python = ">=3.9"', self.pyproject)

    def test_the_package_declares_no_dependencies(self) -> None:
        self.assertIn("dependencies = []", self.pyproject)

    def test_the_console_script_resolves(self) -> None:
        self.assertIn('frisk = "frisk.cli:main"', self.pyproject)
        module = importlib.import_module("frisk.cli")
        self.assertTrue(callable(getattr(module, "main", None)))


if __name__ == "__main__":
    unittest.main()
