"""`python3 -m frisk` — the door that needs no installation.

The console script created by `pip install` reaches the same `main`,
but it exists only where the engine was installed from the repository
(§8.2). Wherever frisk arrives as a plugin, nothing is installed and
nothing is built, so the interpreter must be able to run this package
from wherever it happens to sit.
"""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
