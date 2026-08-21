"""The one error the configuration can raise (§7.1, §7.2).

A configuration that cannot be loaded — a rule with no reason, an API
generation outside the accepted range, a name declared twice in one
source — must become a deny that says what broke, never a partially
built registry. One exception type carries every such failure because
the caller's response is the same in every case, and a hook that had to
tell them apart would be a hook that could get the telling wrong.
"""

from __future__ import annotations


class ConfigurationError(Exception):
    """The configuration is not loadable, and here is why."""
