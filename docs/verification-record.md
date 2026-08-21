# The platform verification record

What frisk's implementation measured about the platforms it runs on,
when, and what each measurement means for the guard's behaviour. It is
the operator-facing record required by §12 of `SPECIFICATIONS.md`: every
open fact of §2.1 lands here once it is settled, with its date and its
method, so that a claim frisk makes about a platform can be re-checked
rather than believed.

Facts age. Each entry carries the date it was taken and enough method to
take it again.

## Status

| # | Fact | Status |
|---|---|---|
| 1 | Hook `allow` and the sandbox waiver | not yet measured |
| 2 | Settings deny/ask precedence over hook decisions | not yet measured |
| 3 | The substitution-prompt trigger | not yet measured |
| 4 | Hook deny/ask survival per permission mode | not yet measured |
| 5 | The platform hook-timeout default | not yet measured |
| 6 | The per-plugin persistent data directory | not yet measured |
| 7 | Plugin configuration delivered to hooks as environment | not yet measured |
| 8 | Project-recommended-plugin prompting | not yet measured |
| 9 | Settings deny/ask under each permissive mode | not yet measured |
| 10 | Prefix-rule word-boundary behaviour | not yet measured |
| 11 | The platform's built-in read-only command handling | not yet measured |
| 12 | **The Python floor: OS-shipped interpreters** | **settled 2026-08-21** |
| 13 | Whether the Bash tool persists shell state across calls | not yet measured |

The unmeasured rows are taken during the verification pass, which runs
against a live Claude Code and needs the operator's consent; they are
filled in here as they settle.

## 12 — The Python floor: what each platform's `python3` is

**Taken 2026-08-21, from vendor documentation.** frisk's engine is
Python, standard library only, and it runs on whatever `python3` the
operator's OS shipped (§2.3, §3.1). A floor set above what a platform
ships is the worst kind of wrong: the hook's engine fails to parse, a
failing hook fails *open*, and nothing in the permission path says so.

| Platform | system `python3` |
|---|---|
| macOS 26 (Tahoe), Xcode / Command Line Tools 26.x | 3.9.6 |
| RHEL 9, and AlmaLinux / Rocky Linux 9 | 3.9 — for the whole RHEL 9 life cycle |
| Amazon Linux 2023 | 3.9 — "always Python 3.9", for the life of AL2023 |
| Ubuntu 22.04 / 24.04 / 26.04 LTS | 3.10 / 3.12 / 3.14 |
| Debian 12 / 13 | 3.11 / 3.13 |
| SLES 16 | 3.13 |
| SLES 15 SP7, openSUSE Leap 15 | **3.6** |
| RHEL 8 (maintenance support until 2029-05-31) | **3.6** |

**The floor is 3.9**, which every platform above the rule covers and
which three of them are pinned to for their entire supported life.

**What it means where the floor is not met.** On SLES 15 / Leap 15 and
RHEL 8, the system `python3` is 3.6 and frisk's engine will not parse.
The hook then fails open: Claude Code's normal permission flow decides
the call, and frisk gates nothing. This is a limitation frisk documents
rather than covers — the alternative was to deny the engine every
language feature from 3.7 to 3.9 for its whole life, since §3.1 forbids
a second code path for newer interpreters. Both vendors ship a current
Python beside the system one (SUSE's Python 3 module, RHEL 8's
`python3.11`/`python3.12` package suites); pointing frisk at one of
those is the supported way to run it there, and the sentinel of §7.4 is
what tells an operator the engine is not answering.

**Re-verifying.** Each row is a vendor statement about the *unversioned*
`/usr/bin/python3`, not about the newest Python the platform can
install — the distinction is the whole point, since the hook runs
whatever `python3` resolves to. On a machine of the platform itself,
`python3 -V` answers directly. Otherwise the vendor's own documentation
is the source: Red Hat's *Installing and using dynamic programming
languages* for RHEL, AWS's *Python in AL2023*, SUSE's release notes and
Python module announcements, `packages.debian.org` and
`packages.ubuntu.com` for the `python3` metapackage, and Apple's
`/Library/Developer/CommandLineTools/Library/Frameworks/Python3.framework`
for the command-line tools.
