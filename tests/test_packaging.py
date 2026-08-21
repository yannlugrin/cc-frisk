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
import sys
import tempfile
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parent.parent
PACKAGE = REPOSITORY / "src" / "frisk"
PYPROJECT = REPOSITORY / "pyproject.toml"
WORKFLOW = REPOSITORY / ".github" / "workflows" / "ci.yml"

#: Where this interpreter keeps its standard library. Taken from a
#: module that is unambiguously part of it, because inside a virtual
#: environment sysconfig's "stdlib" path names a directory that does not
#: exist.
STDLIB = Path(os.__file__).resolve().parent

#: The committed interpreter floor (D-029), as `ast.parse` wants it.
FLOOR = (3, 9)


def imported_roots(source: str) -> set[str]:
    """The top-level module names an absolute import would reach for.

    An AST scan, so an import performed at run time through
    `importlib.import_module(name)` is invisible to it. The engine has
    no reason to do that, and this is the line being drawn.
    """
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
    if origin in ("built-in", "frozen"):
        return True
    if origin is None:
        # A namespace package has no origin either — the `google.*`,
        # `zope.*` shape — and calling that standard library would let a
        # whole class of third-party import through.
        return False
    resolved = Path(origin).resolve()
    if "site-packages" in resolved.parts:
        return False
    return STDLIB in resolved.parents


def modules() -> list[Path]:
    found = sorted(PACKAGE.rglob("*.py"))
    if not found:
        # Not an assert: `python -O` would delete it, and a scan that
        # looked at nothing would then read exactly like a clean one.
        raise AssertionError(f"no engine modules found under {PACKAGE}")
    return found


class ZeroDependenciesTest(unittest.TestCase):
    def test_the_engine_imports_nothing_outside_the_standard_library(
        self,
    ) -> None:
        for module in modules():
            source = module.read_text(encoding="utf-8")
            for root in sorted(imported_roots(source)):
                if root == "frisk":
                    continue
                with self.subTest(module=module.name, imports=root):
                    self.assertTrue(
                        is_standard_library(root),
                        f"{root} is not in the standard library",
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

    def test_an_importable_module_outside_the_stdlib_is_rejected(
        self,
    ) -> None:
        # The control above only proves that a *missing* name is not
        # standard library — nothing here installs `requests`. This one
        # makes a module that really imports, so the path comparison
        # that decides the question is the part under test.
        with tempfile.TemporaryDirectory() as elsewhere:
            (Path(elsewhere) / "frisk_probe_module.py").write_text(
                "value = 1\n", encoding="utf-8"
            )
            sys.path.insert(0, elsewhere)
            importlib.invalidate_caches()
            try:
                self.assertIsNotNone(
                    importlib.util.find_spec("frisk_probe_module")
                )
                self.assertFalse(is_standard_library("frisk_probe_module"))
            finally:
                sys.path.remove(elsewhere)
                sys.modules.pop("frisk_probe_module", None)
                importlib.invalidate_caches()

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
        here = sorted(Path(__file__).parent.rglob("*.py"))
        for module in modules() + here:
            with self.subTest(module=module.name):
                ast.parse(
                    module.read_text(encoding="utf-8"),
                    filename=str(module),
                    feature_version=FLOOR,
                )

    def test_the_check_would_catch_syntax_the_floor_lacks(self) -> None:
        newer = "match command:\n    case []:\n        pass\n"
        if sys.version_info >= (3, 10):
            # Where the grammar exists, the probe string is valid — so a
            # rejection below is `feature_version` doing its work and
            # not a typo in the probe. On the floor itself the first
            # parse would raise for the very reason under test.
            ast.parse(newer)
        with self.assertRaises(SyntaxError):
            ast.parse(newer, feature_version=FLOOR)


class MetadataTest(unittest.TestCase):
    """Read as text, so the floor's own interpreter can run this too.

    `tomllib` arrived in 3.11 and the floor is 3.9, so a TOML parser is
    not available where this suite most needs to run. Each assertion
    below is therefore whole-line membership, not a substring match, and
    `check-toml` in the commit hooks answers the parse question.
    """

    def setUp(self) -> None:
        self.pyproject_lines = PYPROJECT.read_text(
            encoding="utf-8"
        ).splitlines()
        self.workflow_lines = WORKFLOW.read_text(encoding="utf-8").splitlines()

    def test_every_spelling_of_the_floor_agrees(self) -> None:
        floor = f"{FLOOR[0]}.{FLOOR[1]}"
        # Four places, one floor. Any of them left behind would leave a
        # checker judging code against a version the package no longer
        # claims — green everywhere, and the floor unguarded.
        self.assertIn(f'requires-python = ">={floor}"', self.pyproject_lines)
        self.assertIn(
            f'target-version = "py{FLOOR[0]}{FLOOR[1]}"', self.pyproject_lines
        )
        self.assertIn(f'python_version = "{floor}"', self.pyproject_lines)
        self.assertIn(
            f'          python-version: "{floor}"', self.workflow_lines
        )

    def test_the_package_declares_no_dependencies(self) -> None:
        # The import scan above proves the engine takes none; this is
        # the other half — that the metadata does not declare one, which
        # would make the install stop being build-free.
        self.assertIn("dependencies = []", self.pyproject_lines)

    def test_the_version_has_a_single_source(self) -> None:
        self.assertIn(
            'version = { attr = "frisk.__version__" }', self.pyproject_lines
        )

    def test_the_console_script_resolves(self) -> None:
        self.assertIn('frisk = "frisk.cli:main"', self.pyproject_lines)
        module = importlib.import_module("frisk.cli")
        self.assertTrue(callable(getattr(module, "main", None)))


if __name__ == "__main__":
    unittest.main()
