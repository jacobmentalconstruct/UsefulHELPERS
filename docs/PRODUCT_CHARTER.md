# Product Charter

Status: **APPROVED PRODUCT AUTHORITY**

This document owns what useful-helpers is, its consumer-visible invariants,
prototype acceptance conditions, product boundary, and global product non-goals. It
does not own builder workflow, tranche mechanics, implementation status, project
closure, or the meaning of an external development method.

## Constitutional statement

> A self-contained local instrument attached to one directory. It observes that
> directory, builds durable evidence-backed knowledge about it, exposes deterministic
> capabilities over it, and allows humans or agents to make governed changes through
> the same control plane.

The experiential objective is **a calm workbench with receipts**. useful-helpers is
one integrated local project/work instrumentation host. AI is a consumer and possible
source of derived claims, never canonical truth or authority.

Coherent Development is an independent product-neutral method. Its meaning and
state-transition grammar can exist and be used without useful-helpers. The workbench
may support or embody that method, but this product and repository do not own, define,
or make themselves synonymous with it.

## Product invariants

1. One helpers belongs to one target through host-resolved structural, relative identity.
2. Instrument-owned footprint remains inside `.useful-helpers`; approved target work products
   remain when the instrument is removed.
3. CLI, MCP, and future projections are removable entrances to one governed host and do
   not own capabilities.
4. Deterministic manifest-driven mechanical tools own their operations and contracts.
   They may use a minimal shared tool substrate and declared third-party dependencies,
   but do not depend upward on awareness, MCP, GUI, tranche machinery, or other
   projection-specific subsystems.
5. The host owns target binding, resolved roots, identity, state location, authority,
   containment, invocation policy, and context transport. Tools consume that explicit
   context and never infer it independently.
6. SQLite is canonical structured state; immutable large evidence may use a local
   content-addressed object store.
7. Construction history, operational receipts, App Journal memory, epistemic evidence,
   and awareness projections retain distinct owners and meanings even if some share a
   physical database.
8. Resources, observations, evidence, derived claims, and operations remain
   epistemically distinct and provenance-linked.
9. Unobserved means unknown, never absent.
10. Awareness revisions and evidence retain their historical meaning.
11. Important objects have resolvable canonical handles.
12. Independently measured reality outranks a mutating tool's self-report.
13. New runtime state starts blank, compatible updates preserve engagement-owned state,
    and construction history never ships.

## Product topology and dependency direction

```text
CLI / MCP / human projection
             |
        governed host
             |
  host-resolved transported context
             |
      mechanical tools
             |
 minimal shared tool substrate + declared dependencies
```

The host integrates identity, governance, state, receipts/evidence, awareness, entrances,
and safe work loops. Lower mechanical capabilities do not import or require specialized
projections or construction machinery. MCP is removable without removing the host, CLI,
tool manifests, or mechanical operations. A minimal CLI/subprocess entrance is sufficient
for a generic command-capable agent.

This separability is an architectural invariant, not a prototype requirement to publish
separate packages. The prototype does not require extraction into separate distributions;
it must preserve dependency boundaries that leave later extraction reasonably possible.

## Runtime state and history ownership

- **Construction history:** `.builder/journal/` and `.builder/evidence/` record building
  this repository. They never ship and are not runtime input.
- **Operational receipts/event ledger:** runtime calls, attempts, results, changed-path
  measurements, verifications, and related event facts. The governed host records them.
- **App Journal:** durable project-neutral work memory containing entries, decisions,
  related files, backlog, close/park state, and human-readable export. Journal semantics
  do not require awareness, MCP, `.builder/`, or this source repository.
- **Epistemic evidence and substrate:** immutable support plus resources, observations,
  claims, and provenance relations. This is not a synonym for an operational receipt or
  journal entry.
- **Awareness:** compact immutable projections over substrate evidence. Awareness owns
  projections, not source records or journal meaning.

The App Journal is the product journal and begins empty on a clean installation. Runtime
receipts, evidence, awareness, and other target-engagement state also begin empty. Neither
journal stores or projects the other. Updates preserve compatible runtime state; release
assembly excludes construction journals, gates, certification exhaust, and evidence.

## Product and factory boundary

`product/` is the positive installed-runtime source boundary. Runtime identity,
orientation, control-plane behavior, tool contracts and shared substrate, journal
semantics, receipts, substrate behavior, adapters, and installed capabilities belong
there. Installed product code may not import `factory/`, `.builder/`, or `tests/`.

`factory/` owns manufacture, installation, packaging, compatible replacement assembly,
and release only. It does not own runtime attach, host invocation, journal, awareness, or
target behavior. Artifact format is deliberately undecided. Release composition must
positively select product surfaces; it must not ship construction history by subtracting
an ever-growing denylist.

## Prototype acceptance conditions

- **P1 Lifecycle:** Attach one host-owned, structurally identified helpers to an arbitrary
  target; transport its resolved roots and policy to capabilities; relocate it with the
  target; minimally update compatible code while preserving UUID and engagement state;
  remove the instrument cleanly.
- **P2 Mechanical hands and governed use:** Discover manifest-defined deterministic
  mechanical tools whose operation/contracts depend only on a minimal tool substrate and
  declared dependencies; invoke them through one host authority, containment, process,
  attribution, context-transport, and result-validation boundary exposed by CLI.
- **P3 Distinct durable memory:** Persist operational receipts/events, immutable evidence,
  a blank-start independently coherent App Journal, resources, versions, observations,
  claims, and typed provenance relations without collapsing their ownership or meaning.
- **P4 Orientation:** Produce compact immutable awareness revisions with freshness,
  limitations, provenance, and stable round-tripping handles; unknown remains explicit,
  and lower tools/journal semantics do not depend on awareness.
- **P5 Governed mutation:** Preview and diff before approval, bind approval to reviewed
  reality, reject stale previews, measure actual changed paths, verify honestly, refresh,
  and retain linked but distinct receipts, evidence, and App Journal decisions.
- **P6 Entrance parity and removability:** CLI and MCP expose the same host catalog,
  authority, substrate, awareness, receipts, and App Journal rather than parallel
  implementations; removing MCP leaves CLI, host, and mechanical capabilities usable.
- **P7 Truthful breadth:** Degrade usefully across a substantial software target, a
  mixed records/document target, and an empty or nascent target; calibrate discriminating
  behavior with separate known-answer fixtures.
- **P8 Releasability:** One sealed release artifact passes the consumer walk on clean
  Windows and Linux environments; proves lower layers do not depend upward on projections
  or construction machinery; and contains no construction history, parent lineage,
  sandbox paths, temporary fixtures, or construction state. macOS is UNSCORED.

## Acceptance walk

Install the same artifact into each target class; confirm blank engagement state; observe;
orient; resolve handles; drill into evidence; propose, preview, and approve one exact
change; apply and independently measure it; verify or report unavailable; refresh while
preserving the prior revision; distinguish receipts from App Journal decisions; inspect
the same world through CLI and MCP; remove MCP and repeat a mechanical CLI call; perform
a compatible update preserving runtime state; remove the instrument; inspect the target,
dependency direction, and artifact boundaries.

## Product STOP

Product STOP is satisfied only when P1-P8 are each supported by declared consumer-visible
evidence. The integrated useful-helpers must prove installation, governed hands,
distinct receipts/evidence/journal memory, awareness, stale-safe mutation, CLI/MCP parity,
truthful degradation, compatible update, removal, and clean distribution. Structural
checks must additionally prove that mechanical tools and App Journal semantics do not
depend upward on specialized projections or construction machinery. Actual extraction
into standalone distributions is not required. Missing or inapplicable evidence is
UNSCORED, not PASS. Product STOP does not by itself close construction; project closure
is owned by the Tranche Plan.

## Global non-goals

The prototype excludes a GUI/IDE, autonomous or multi-agent runtime, workflow language,
graph database, vector-centered authority, universal plugin system, marketplace, remote
service, global helpers registry, broad local-model platform, every parent capability,
every possible cartridge, speculative extension infrastructure, optimization without
measurement, and T0 extraction of a standalone Tool Pack, App Journal distribution,
scaffold kit, Coherent Development application, or updater subsystem.
