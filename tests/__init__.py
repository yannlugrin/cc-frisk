"""The engine's own suite.

A package, so that `unittest discover` can be told to root the test
tree at the repository rather than at this directory — which is what
an editor's test explorer does, and what it cannot be argued out of.
Modules here import each other by their full path (`tests.corpus`) for
the same reason: it is the one spelling that works whichever of the two
directories discovery starts from.
"""
