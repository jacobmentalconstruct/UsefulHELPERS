# Third-Party Notices

**useful-helpers** — Copyright © 2026 Jacob Lambert. MIT licensed.
See [`LICENSE.md`](LICENSE.md) for the terms governing this software.

## Summary

**This software contains no third-party code.** Every file in it is original work
of the copyright holder. There are no bundled libraries, no vendored source
fragments, and no copied snippets carrying another party's copyright or
attribution requirement.

This matters in both directions. It means no third party's terms constrained the
choice of licence, and it means a recipient of this software acquires no
obligation to anyone beyond the MIT terms in `LICENSE.md`. There is no other
copyright holder to satisfy and no attribution owed to anyone else.

## How this was determined

The following checks were run against the shipped surface (`product/` and
`factory/`) and against the sealed release artifact:

| Check | Method | Result |
|---|---|---|
| Third-party imports | AST walk of every `.py` file, each import root compared against `sys.stdlib_module_names` | **None.** Only the Python standard library, `__future__`, first-party packages (`core`, `product`, `factory`), and intra-package relative imports. |
| Declared runtime dependencies | `pyproject.toml` `[project].dependencies` | `[]` (empty) |
| Vendored or adapted code | Repository-wide search for `vendored`, `adapted from`, `derived from`, `based on`, `taken from`, `github.com`, `stackoverflow`, `http://`, `https://` | No code matches. Only product prose describing signals "derived from" other signals. No external URLs anywhere in shipped code. |
| Foreign copyright notices | Repository-wide search for `copyright`, `SPDX`, `licen[cs]e`, `(c) 20`, `all rights reserved`, `Apache`, `GPL`, `BSD`, `MIT` | None. All matches were SQL `LIMIT`, the English word "limitations", a filename-stem list in `substrate.py`, and a test fixture that writes the literal string `MIT`. |
| Release artifact contents | Enumeration of all 51 members of `useful-helpers-0.1.0.zip` | 36 `.py` files, five tool `manifest.json` files, four documents under `docs/`, and `README.md`, `CHANGELOG.md`, `LICENSE.md`, `THIRD-PARTY-NOTICES.md`, `pyproject.toml` and `RELEASE_MANIFEST.json`. No bundled binaries or libraries. |
| Archived project snapshot | Full member listing and AST import scan of `.UsefulHELPERS.7z` (237 entries) | An earlier snapshot of this same project at tranche T4, dated 2026-08-25 to 2026-08-27. First-party throughout; no non-stdlib imports, no foreign notices. Excluded from the release artifact by `_EXCLUDED_SUFFIXES` in `factory/release.py`. |

## Runtime prerequisites — required, not distributed

**CPython 3.11 or later** must be installed separately by the user. Python is
licensed under the [Python Software Foundation License](https://docs.python.org/3/license.html).
useful-helpers does not bundle, embed, statically link, or redistribute Python
or its standard library; it requires only that a suitable interpreter be present
on the host.

Two external programs are invoked as separate processes. Neither is bundled and
neither is linked:

- **The running Python interpreter** (`sys.executable`) — used to launch
  mechanical tools as child processes (`product/core/control.py`).
- **`git`** — used only to record release provenance (`factory/release.py`). If
  `git` is absent, the provenance field degrades to the literal string
  `"unavailable"` and the release still completes. Git is licensed under
  GPL-2.0; invoking a program as a separate process does not create a derivative
  work of it, and no part of git is distributed with this software.

## Development-only tooling — not distributed

These packages appear in `[project.optional-dependencies].dev`. They are used to
test and lint the project. They are **not** imported by shipped code, **not**
included in the release artifact, and **not** redistributed by the Owner. Their
licenses are recorded for completeness; no notice obligation attaches to this
distribution.

| Package | Version verified | License | Why present |
|---|---|---|---|
| pytest | 8.4.2 | MIT | Test runner (direct dev dependency) |
| ruff | 0.15.22 | MIT | Linter (direct dev dependency) |
| pluggy | 1.6.0 | MIT | Transitive — pytest plugin system |
| iniconfig | 2.3.0 | MIT | Transitive — pytest configuration parsing |
| packaging | 24.0 / 26.1 | Apache-2.0 OR BSD-2-Clause | Transitive — pytest version handling |

Versions and license fields were read from installed distribution metadata at
audit time, not recalled from memory. Resolved transitive versions may differ in
other environments; the license terms above are stable across the pinned ranges
(`pytest>=8,<9`, `ruff>=0.15,<0.16`).

All of these are permissively licensed and imposed no restriction on the choice
of MIT for this software.

---

*Audit performed against the repository at commit `5810404` and the sealed
artifact `useful-helpers-0.1.0.zip`. The repository has since advanced to
`b2f3b02`; re-run the checks above if dependencies or the shipped file set
change.*
