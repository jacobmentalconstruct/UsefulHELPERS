# Phase 1: Identity and Hands

> **PRE-BOOTSTRAP PROVISIONAL REPORT.** This file records what the baseline prototype
> claimed and measured before construction governance existed. It grants no T1 or
> Product STOP credit. T1 may audit, adopt, amend, re-home, or reject these mechanisms.

## Milestone

Phase 1 proves this executable spine:

```text
target
  -> structural instance context
  -> one control plane
  -> live manifest discovery
  -> deterministic child-process tool
  -> SQLite-backed instance state
  -> CLI adapter
```

## Source and installed shape

```text
factory/                 positive installer and development CLI
product/
    bin/                 installed front door
    core/                identity, storage, contracts, containment, registry, runtime
    tools/               five manifest-driven capabilities
tests/                   installed-instance fixtures
docs/                    product authority and milestone boundary
```

Attachment copies only `product/bin`, `product/core`, and `product/tools`, then creates
`instance.json`, `state/workbench.sqlite3`, `state/objects`, and `logs`. It refuses an
existing `.useful-helpers`; update and reinstall semantics are intentionally undefined in this
phase.

## Phase 1 capabilities

- `inventory`: enumerate target resources while excluding the exact instance subtree.
- `read_file`: bounded UTF-8 text read.
- `search_text`: bounded exact line search with explicit skipped-file limitations.
- `hash_file`: SHA-256 of one target file.
- `write_file`: provisional deliberate write requiring Apply authority and
  `confirm: true`.

All user paths are target-relative. Absolute paths, traversal, and paths resolving into
the instrument are refused before process launch. The resolved path is then transported
to the tool; tools never locate their target from working directory or environment.

`run_command` is deliberately deferred. A process can write outside declared roots, and
Phase 1 does not yet own process trees or mutation measurement. Adding a command runner
without those controls would make the stated containment stronger on paper than in
reality.

## SQLite boundary

Phase 1 creates one database with schema versioning and one `instances` row. Startup
checks that the database UUID agrees with `instance.json`. Resource observations,
evidence, journal entries, and the operation ledger belong to later migrations; the
empty tables are not created speculatively.

## Known limitations

The Phase 1 write tool has explicit authority and confirmation but no reviewed preview,
stale-state binding, independent mutation measurement, or durable operation receipt.
It exists to prove that mutation has one route. Phase 2 must replace this provisional
gate with the complete receipt-bearing flow before broader mutating tools are added.

The child process is controlled for timeout and output shape, but descendant process
ownership and cancellation are deferred because Phase 1 ships no command-execution
tool.

## Acceptance evidence

Fixture tests must distinguish the intended architecture from plausible shortcuts by
checking malformed identity refusal, relocation continuity, authority enforcement from
a live manifest, instance-by-path exclusion, SQLite/manifest agreement, actual traversal
refusal reasons, and before/after target snapshots.

Milestone `0.1.0` is verified by ten installed-instance tests under both `unittest` and
`pytest`. The suite includes a supported-host symlink witness and executes each tool from
the payload copied into a fixture target rather than importing tool implementations from
the source tree.
