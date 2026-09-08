# Changelog

All notable changes to useful-helpers are recorded here. Dates are
ISO 8601. This project does not yet follow semantic versioning; 0.1.0 is the
first release and the interface should be treated as unstable.

## 0.1.0 - 2026-09-03

First release. State schema 6.

### Added

- **Instrument attachment.** `factory attach` installs the instrument into a
  target directory as `.useful-helpers/`, holding all state in one SQLite database.
  No registry, no home-directory configuration, no background process.
- **Explicit observation.** `substrate refresh` records resources, immutable
  per-resource versions, deterministic observations, content-addressed
  evidence, and derived claims, with typed provenance edges between them.
  Nothing is observed until asked.
- **Orientation.** `awareness refresh` builds a compact revision over one
  coherent substrate basis. Revisions are immutable, report their own
  limitations and truncation, and go stale when the target changes underneath
  them. `awareness drill` resolves any finding back to its evidence.
- **Governed mutation.** `mutation preview-write`, `approve`, and `apply`
  implement a change loop that binds an approval to one exact preview and
  basis, refuses on stale target or stale basis, measures the changed path
  independently of the tool's own success message, and records
  `verification: unavailable` rather than guessing when no native check exists.
- **Durable records.** Every tool invocation leaves an operation receipt and a
  full artifact envelope. `journal` provides deliberate work memory, kept as a
  separate owner from receipts and from epistemic evidence.
- **Five mechanical tools.** `inventory`, `read_file`, `search_text`,
  `hash_file` at observe authority, and `write_file` at apply authority. Tools
  receive only `target_root` and `excluded_roots` and reject unknown context
  fields.
- **Agent entrance.** `helpers mcp` speaks line-delimited JSON-RPC over stdio,
  MCP protocol `2024-11-05`, advertising 21 tools over the same host and
  database the CLI uses. It is removable: delete `core/mcp.py` and the rest
  keeps working.
- **Containment.** Paths are resolved to their real location before the
  boundary check, so symlinks cannot be used to escape the target directory.
- **Launcher scripts.** `attach.bat` and `attach.sh` attach an instance to a
  target directory from any working directory, so the module form is optional.
  They add no capability: each is a wrapper over `factory attach`, and every
  check and refusal remains in the installer.
- **Lifecycle.** `factory update` migrates an installed instance in place;
  `factory detach` removes it. Schema migrations are versioned through
  `PRAGMA user_version`.
- **Recorded interpreter compatibility.** `status` reports the running
  interpreter and whether the test suite has passed on it. Versions outside the
  verified set run and are disclosed as unmeasured rather than refused; only
  versions measured to break are refused, and none are recorded today.

### Known limitations

- macOS has no recorded acceptance run. Verification covers Linux (CPython 3.10,
  3.11, 3.12, 3.13) and Windows 10 only.
- Domain classification uses deterministic file signals only: extensions,
  filenames, and directory markers. It does not read content to infer purpose.
- Weak material (large or binary files, vendor and generated subtrees) is
  recorded as metadata only, with size and mtime change detection rather than
  content hashing.
- Mutation verification is `unavailable` for targets with no native
  verification mechanism. This is reported honestly rather than inferred.
- Authority is a declared intent, not a credential. Anyone able to run the CLI
  can pass `--authority apply`. What it provides is that the level is checked
  before execution and recorded on the receipt either way.
- Issuing the same `mutation preview-write` twice returns an honest failure
  envelope, but with code `IntegrityError` rather than a domain refusal such as
  `duplicate_preview`. The refusal is correct; the code leaks an implementation
  detail. Carried, not repaired, in this release.

See [docs/QUICKSTART.md](docs/QUICKSTART.md) for the full list with workarounds.

### Provenance

Built in nine tranches, T0 through T8, each declared before implementation,
gated by an executable check, externally reviewed, and parked only on explicit
operator approval. Construction reached Product STOP at T8 and was closed by
journal entry `0062`. Post-STOP forensic preflight repairs are recorded in
entry `0061`.
