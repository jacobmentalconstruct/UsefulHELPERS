# useful-helpers: Quickstart

useful-helpers is a self-contained instrument you attach to **one directory**. It
installs itself into that directory as a hidden `.useful-helpers/` folder, records durable
evidence about what is there, and lets you or an agent make **governed** file changes
that leave receipts.

Nothing is written anywhere else on your machine. There is no registry, no
home-directory config, and no background process. Remove the folder and the instrument
is gone.

- **Version:** 0.1.0 · state schema 6
- **Requires:** Python 3.10 or newer, and nothing else. No third-party packages.
- **Verified on:** CPython 3.10, 3.11, 3.12 and 3.13, on Linux and Windows 10. macOS has
  no recorded acceptance run.

Compatibility is recorded, not asserted. `status` reports the running interpreter and
whether the test suite has passed on it. An interpreter outside the verified set is not
refused: it runs, and `status` says so. Only versions measured to break are refused, and
none are recorded today.

---

## 1. Install

You need the sealed release archive, `useful-helpers-0.1.0.zip`.

```bash
unzip useful-helpers-0.1.0.zip -d useful-helpers-release
cd useful-helpers-release
python -m factory attach /path/to/your/project
```

On Windows use `py -m factory attach C:\path\to\your\project`.

Or use the launcher scripts, which run from any directory. On Windows you can
also drag a folder from Explorer onto `attach.bat`:

```
attach.bat C:\path\to\your\project
sh attach.sh /path/to/your/project
```

`attach.sh` is invoked with `sh` rather than run directly: the release archive
records every member as non-executable so the artifact stays byte-reproducible,
so the file does not carry an executable bit.

```json
{"front_door": ".useful-helpers/bin/helpers.py", "instance": ".useful-helpers",
 "instance_uuid": "3ffc99b5-bd37-4a0c-a98e-f1f449e6d43f",
 "ok": true, "target_relation": ".."}
```

That created `<your-project>/.useful-helpers/` containing `bin/`, `core/`, `tools/`, an empty
`state/` and `logs/`, and an `instance.json` holding the UUID above. Your own files were
not touched.

**Every later command runs the front door inside your project:**

```bash
python /path/to/your/project/.useful-helpers/bin/helpers.py <command>
```

It is worth making a shell alias:

```bash
alias helpers='python /path/to/your/project/.useful-helpers/bin/helpers.py'
```

The rest of this guide writes `helpers` for that command. Every command prints JSON to
stdout and exits `0` on success, `1` on a refusal or error, `2` on invalid usage.

**Do not move `.useful-helpers` out of your project.** It finds its target by looking at its own
parent directory. You can rename or move the *whole* project freely. The instrument
follows and keeps its UUID.

---

## 2. First use

A five-minute walkthrough on a small project containing `pyproject.toml`, `README.md`,
`src/app.py` and `docs/plan.md`. Output below is real, trimmed for width.

### Check the install

```bash
instance status
```

```json
{
  "bound": true,
  "database_identity_matches": true,
  "database_schema": 6,
  "instance_uuid": "3ffc99b5-bd37-4a0c-a98e-f1f449e6d43f",
  "ok": true,
  "product_version": "0.1.0",
  "python": {"support": "verified", "version": "3.12.3"},
  "limitations": [],
  "target_root": "/home/you/notes-project",
  "tool_count": 5
}
```

### See what it can do

```bash
helpers tools
```

| tool | authority | reads | writes |
|---|---|---|---|
| `inventory` | observe | target | none |
| `read_file` | observe | target | none |
| `search_text` | observe | target | none |
| `hash_file` | observe | target | none |
| `write_file` | **apply** | target | target |

### Observe the directory

Nothing happens automatically. Observation is always an explicit act.

```bash
helpers substrate refresh
```

```json
{"observed": {"resource_count": 6, "observation_count": 7, "claim_count": 2,
  "target_signature": "ec9979ca82e0...", "limitations": [],
  "unknown": "anything not observed by this refresh remains unknown"}, "ok": true}
```

### Orient

```bash
helpers awareness refresh
```

```json
{
  "awareness_id": "awareness:4e9fc6e37e764080852baa83b65b391b",
  "freshness": "current",
  "basis": {"status": "observed", "signature": "2a4ba751d29f..."},
  "summary": {"domain_profile": "software", "target_state": "observed_non_empty",
              "resource_count": 6, "claim_count": 2},
  "limitations": [
    "awareness is a compact projection over the latest substrate refresh, not a complete target scan",
    "domain profile is derived from deterministic substrate signals only",
    "software profile is based on deterministic file and marker signals only",
    "language symbols and imports have not been analyzed by T7"
  ],
  "unknowns": ["anything not represented in substrate observations remains unknown"],
  "findings": [
    {"item_id": "awareness:item:5f2924...", "title": "target_has_text_files"},
    {"item_id": "awareness:item:4bf997...", "title": "target_profile_software"},
    {"item_id": "awareness:item:2848f8...", "title": "observed_resources"}
  ]
}
```

Read the `limitations` and `unknowns`. They are the point. The instrument states what it
did **not** establish as plainly as what it did.

### Ask why it thinks that

```bash
helpers awareness drill awareness:item:4bf997...
```

Returns the claim, the observations it was derived from, the content-addressed evidence
behind those, and the target files concerned, with typed edges (`derived_from`,
`supported_by`, `concerns`). Every statement traces back to a file on disk.

### Use a tool

```bash
helpers call read_file --args '{"path":"src/app.py"}'
```

```json
{"ok": true, "tool_id": "read_file", "client": "cli", "authority": "observe",
 "receipt_id": "operation:b7fd7229...", "artifact_id": "artifact:4870ba0e...",
 "durably_governed": true, "result": {"content": "def main():\n    return 1\n"}}
```

Every call, whether it succeeds or is refused, leaves a receipt.

```bash
helpers call search_text --args '{"query":"def main"}'
helpers call inventory   --args '{"limit":50}'
helpers call hash_file   --args '{"path":"src/app.py"}'
```

### Record a decision

The App Journal is your work memory. It is never written automatically.

```bash
helpers journal add --type decision --status decided \
  --title "Bump app.py return value" --body "Agreed with reviewer."
```

```json
{"entry_id": "journal:1", "entry_type": "decision", "status": "decided",
 "title": "Bump app.py return value", "created_at": "2026-09-06T21:29:48+00:00"}
```

`--type` is one of `entry`, `decision`, `backlog`, `status`.
`--status` is one of `open`, `closed`, `decided`, `parked`, `blocked`.

### Make a governed change

Four steps, always in this order. **Preview requires current awareness**, so refresh
first if anything has changed on disk.

**Preview** records the proposed change without touching anything:

```bash
helpers mutation preview-write --path src/app.py \
  --content 'def main():
    return 2
' --overwrite
```

```json
{"preview": {"preview_id": "mutation:preview:ac6b05ad...", "operation": "write_file",
 "path": "src/app.py", "before_exists": true,
 "expected_changed_paths": ["src/app.py"],
 "awareness_id": "awareness:4e9fc6e3...", "status": "previewed"}}
```

**Approve** binds to that exact preview, optionally to a journal entry:

```bash
helpers mutation approve mutation:preview:ac6b05ad... --journal-entry journal:1
```

**Apply**:

```bash
helpers mutation apply mutation:approval:cf3223cf...
```

```json
{"mutation": {
  "status": "applied",
  "receipt_id": "operation:314ff26e...", "artifact_id": "artifact:5587bae0...",
  "measurement": {"changed_paths": ["src/app.py"], "source": "independent_target_snapshot"},
  "verification": {"status": "unavailable",
                   "detail": "No target-native verification mechanism is available."},
  "pre_awareness_id": "awareness:2acc145e...", "post_awareness_id": "awareness:f6c0088b..."}}
```

Two things to notice. `measurement` comes from an **independent before/after snapshot of
the target**, not from the tool's own success message, so it tells you what actually
changed. And `verification` says `unavailable` rather than inventing a PASS, because
there is no target-native check to run.

**If anything changed on disk since you previewed, apply refuses before touching
anything:**

```json
{"ok": false, "error": {"code": "stale_target",
   "message": "target signature differs from reviewed preview"},
 "mutation": {"status": "refused",
   "measurement": {"changed_paths": [], "source": "not_launched"}}}
```

That is correct behaviour, not a bug. Re-observe, re-orient, re-preview.

### Read the audit trail

```bash
helpers mutation links mutation:record:fac7ed98...
```

```
preview      -> mutation:preview:7b107ae9...
approval     -> mutation:approval:cf3223cf...
verification -> mutation:verification:66c3c731...
operation    -> operation:314ff26e...
artifact     -> artifact:5587bae0...
awareness    -> awareness:2acc145e...   (before)
awareness    -> awareness:f6c0088b...   (after)
journal      -> journal:1
```

```bash
helpers receipts list --limit 10
helpers receipts read operation:314ff26e...
helpers artifacts read artifact:5587bae0...
helpers mutation history
```

---

## 3. Command reference

| Command | What it does |
|---|---|
| `status` | Identity, schema version, target root, tool count |
| `tools` | Full tool catalog with authority, domains and schemas |
| `call <tool> --args '<json>' [--authority observe\|sandbox\|apply] [--timeout N]` | Run one tool through the governed host |
| `receipts list [--limit N]` / `receipts read <id>` | Durable record of every invocation |
| `artifacts list [--limit N]` / `artifacts read <id>` | The full envelope behind a receipt |
| `journal list` / `add` / `read <id>` / `link <entry> <target>` | Your work memory |
| `substrate status` / `refresh` | Table counts; explicit re-observation |
| `substrate resources list` / `read <handle>` | What was observed |
| `substrate versions list [handle]` / `read <id>` | Immutable history per resource |
| `substrate observations list` / `read <id>` | Deterministic producer statements |
| `substrate evidence read <id>` | Content-addressed support |
| `substrate claims list` / `read <id>` | Derived interpretations, with confidence |
| `substrate trace <handle>` | Walk the provenance graph from any handle |
| `awareness status` / `refresh` / `current` | Compact orientation over the latest basis |
| `awareness revisions list` / `read <id>` | Prior revisions, never overwritten |
| `awareness drill <item-id>` | Resolve a finding back to its evidence |
| `mutation status` / `preview-write` / `approve` / `apply` / `history` / `links <id>` | The governed change loop |
| `mcp` | Start the agent entrance on stdin/stdout |

Authority is a declaration of intent, not a credential. Anyone who can run the CLI can
pass `--authority apply`. What it buys you is that the level is checked before anything
runs and recorded on the receipt either way.

---

## 4. Using it from an agent

`helpers mcp` speaks line-delimited JSON-RPC on stdin/stdout (MCP protocol
`2024-11-05`). A typical client config:

```json
{
  "mcpServers": {
    "helpers": {
      "command": "python",
      "args": ["/path/to/your/project/.useful-helpers/bin/helpers.py", "mcp"]
    }
  }
}
```

It advertises 21 tools over the same host and the same database the CLI uses, so a receipt
created through MCP appears in `helpers receipts list` immediately.

- **16 projections:** `helpers.status`, `receipts.list`, `receipts.read`, `journal.list`,
  `journal.read`, `substrate.status`, `substrate.resources.list`, `substrate.trace`,
  `awareness.current`, `awareness.drill`, `mutation.status`, `mutation.preview_write`,
  `mutation.approve`, `mutation.apply`, `mutation.history`, `mutation.links`
- **5 manifest tools:** `tool.inventory`, `tool.read_file`, `tool.search_text`,
  `tool.hash_file`, `tool.write_file`

To call a manifest tool above `observe`, pass `_authority` **inside `arguments`**. It is
advertised in each tool's `inputSchema`:

```json
{"jsonrpc": "2.0", "id": 1, "method": "tools/call",
 "params": {"name": "tool.write_file",
            "arguments": {"path": "notes.txt", "content": "hi\n",
                          "confirm": true, "_authority": "apply"}}}
```

`_timeout` (integer seconds) works the same way. Omit `_authority` and a write is
correctly refused with `authority_denied`.

**Removing the agent entrance is supported.** Delete `.useful-helpers/core/mcp.py` and
everything else keeps working; `helpers mcp` then returns a truthful
`{"error": {"code": "mcp_unavailable"}}`.

---

## 5. Update and remove

Both run from the extracted release directory, not from the front door.

```bash
# Replace the installed code, keep identity and all engagement state
python -m factory update /path/to/your/project

# Remove the instrument entirely
python -m factory uninstall /path/to/your/project
```

`update` replaces `bin/`, `core/` and `tools/` only. Your UUID, journal, receipts,
substrate, awareness and mutation history all survive, and the state database migrates
forward automatically.

`uninstall` deletes `.useful-helpers` and nothing else. Your files are byte-identical
afterwards.

> **`uninstall` is permanent and total.** It destroys every journal entry, receipt,
> observation and mutation record along with the instrument. There is no export command.
> If any of that matters, capture it first:
> ```bash
> helpers journal list --limit 500  > journal-backup.json
> helpers receipts list --limit 500 > receipts-backup.json
> helpers mutation history          > mutations-backup.json
> ```

`attach` refuses if `.useful-helpers` already exists, so you cannot install over yourself by
accident.

---

## 6. When something goes wrong

Every failure prints JSON with an `error.code`. Find yours here.

| `error.code` / message | What happened | What to do |
|---|---|---|
| `current awareness is not fresh enough to preview mutation` | The directory changed since your last `awareness refresh` | `helpers substrate refresh && helpers awareness refresh`, then preview again |
| `stale_target`, *target signature differs from reviewed preview* | Something on disk changed between preview and apply | Re-observe, re-orient, re-preview. Working as designed |
| `stale_basis` | Awareness moved on since the preview | Same as above |
| `approval_preview_mismatch` | The `--preview` you named is not the one the approval is bound to | Drop `--preview`, or pass the right one from `mutation history` |
| `approval_not_found` | No such approval id | Check `helpers mutation history` for the real id |
| `authority_denied` | The tool needs `apply`, you asked for `observe` | Add `--authority apply` (CLI) or `"_authority": "apply"` (MCP) |
| `containment_refusal` | The path escapes the project, or points inside `.useful-helpers` | Use a path relative to the project root. This is the safety boundary |
| `registry_error` | A tool manifest is missing or malformed | One bad manifest disables the whole catalog. Remove it, or re-run `factory update` |
| `mcp_unavailable` | `core/mcp.py` is absent | Expected if you removed it. Re-run `factory update` to restore |
| `InstanceError` | `instance.json` is missing, malformed, or `.useful-helpers` was moved | Restore the file from backup, or uninstall and re-attach |
| `StorageError`, *identity does not agree* | The database and `instance.json` disagree on the UUID | The database belongs to a different install. Restore the right one, or re-attach into a clean directory |
| `DatabaseError` / `OperationalError` | The state database is corrupt or is not ours | See below |
| `ModuleNotFoundError: No module named 'core'` (a traceback, not JSON) | An update was interrupted partway | Re-run `python -m factory update <project>`. Verified to fully restore the install and keep all state |

### Recovering a corrupt state database

`.useful-helpers/state/workbench.sqlite3` holds everything the instrument knows. If it is
corrupted, no command will run.

1. Copy the whole `.useful-helpers/state/` directory somewhere safe first.
2. If you have the `sqlite3` command-line tool, SQLite's own recovery is worth one
   attempt: `sqlite3 workbench.sqlite3 ".recover" | sqlite3 repaired.db`, then swap
   `repaired.db` in and check with `instance status`. How much it salvages depends on the
   damage, and the product does not do this for you.
3. Otherwise, delete `.useful-helpers` and re-attach. **Your project files are untouched; your
   journal, receipts and observation history are lost.**

Take a copy of `.useful-helpers/state/` before anything risky. It is the only thing that is not
reproducible.

### Leftover `.old-*` and `.update-*` folders

An interrupted update leaves full copies of the previous code inside `.useful-helpers`. They are
inert but they are never cleaned up, and `instance status` will not mention them. Once
`status` reports `ok: true`, delete anything matching `.useful-helpers/.old-*` or
`.useful-helpers/.update-*`.

---

## 7. Known limitations

Honest list. None of these will lose your work; all of them are better to hear now.

**Scope**

- **One directory per install.** No multi-project view, no aggregation.
- **The only change it can make is writing one file.** No delete, move, rename or patch.
- **`verification` is always `unavailable`.** The product does not invent a PASS it
  cannot substantiate. Verify changes yourself.
- **Domain classification is deterministic file signals only**: extensions, filenames
  and project markers. It does not read or understand your code. A directory with a
  single `.txt` file is reported as a "records/document collection".

**Behaviour worth knowing**

- **State grows on every refresh.** An unchanged 500-file target adds about 1,000
  observations and 4,000 relations per `substrate refresh`. Evidence and versions are
  content-addressed and do not grow, but the database does, with no pruning. On a large
  target, refresh deliberately rather than in a loop.
- **`awareness revisions list` slows as revisions accumulate**, because it recomputes
  freshness against the live directory once per row. Use `--limit`.
- **`product_version` in `status` is not updated by `update`.** After updating to a newer
  build it still reports the version you originally installed. Check
  `.useful-helpers/core/constants.py` for the truth.
- **A directory the instrument cannot read is disclosed, but mislabelled.** A
  permission-denied folder appears under the caption *"vendor, generated, or
  version-control subtree(s) … not traversed"*. The per-resource limitation next to it
  states the real cause (`access failed; unobserved contents remain unknown`). Trust
  that one.
- **Any SQLite file left at `.useful-helpers/state/workbench.sqlite3` is adopted** and gets the
  product's tables added to it. Do not put another database there.
- **Interrupted updates** leave the install broken until you re-run `update`, and leave
  debris behind. See §6.

**Agent entrance**

- No `ping`, no protocol-version negotiation (it always answers `2024-11-05` regardless
  of what the client requests), and no JSON-RPC batching. Clients that require any of
  these will not work.
- `_authority` inside `arguments` is a useful-helpers extension, not standard MCP. It is
  properly advertised in the tool schema, so well-behaved clients will surface it.

**Boundaries**

- **Receipts prove what useful-helpers did, not what happened to your directory.** Anything else
  on your machine can edit the same files with no record. The instrument *will* notice on
  the next refresh. It just cannot attribute the change.
- **Authority is not access control.** `--authority apply` requires no credential. It
  records intent; it does not restrict a local actor.
- **Anything under `.useful-helpers/tools/` is executed as code.** Only install tools you trust.
- **macOS is unscored.** It may work; nobody has tested it.

---

## 8. Where things live

```
your-project/
├── your files …                      ← never touched except by an approved change
└── .useful-helpers/
    ├── instance.json                 ← UUID + structural link to the target
    ├── bin/helpers.py                ← the front door
    ├── core/                         ← runtime
    ├── tools/<id>/                   ← manifest + implementation per tool
    ├── logs/
    └── state/
        ├── workbench.sqlite3         ← everything it knows. Back this up.
        └── objects/
```

Ownership stays separate inside that database: **operation receipts** (what ran),
**App Journal** (what you decided), **epistemic evidence** (what was observed), and
**awareness revisions** (what it currently thinks). They link to each other and are never
collapsed into one another.
