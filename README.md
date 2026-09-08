# useful-helpers

An instrument you attach to one directory. It observes what is there, records
durable evidence, and lets you or an agent make governed file changes that leave
receipts.

Version 0.1.0 · state schema 6 · CPython 3.10 or newer · no third-party dependencies

> **MIT licensed.** Copyright © 2026 Jacob Lambert. Free to use, modify and
> redistribute. See [LICENSE.md](LICENSE.md).

## What it is

useful-helpers installs into a target directory as a hidden `.useful-helpers/`
folder. Everything it knows lives in a single SQLite database inside that
folder. There is no registry, no home-directory configuration, and no background
process. Delete the folder and the instrument is gone, along with everything it
recorded.

It is built around one idea: an instrument that acts on your files should be
able to show its work.

- **Observation is explicit.** Nothing is examined until you ask. Each refresh
  records resources, immutable per-resource versions, deterministic
  observations, content-addressed evidence, and derived claims, joined by typed
  provenance edges you can walk.
- **Orientation is honest.** Awareness is a compact revision built over one
  coherent basis. It reports its own limitations and truncation, and goes stale
  when the target changes underneath it. Anything it could not see is reported
  as unknown rather than omitted.
- **Changes are governed.** A write goes preview, approve, apply. The approval
  binds to one exact preview and basis and is refused if either is stale. The
  result is measured independently of the tool's own success message, and where
  no native check exists the record says `verification: unavailable` rather than
  guessing.
- **Everything leaves a receipt.** Every invocation produces an operation
  receipt and a full artifact envelope, whether it succeeded or was refused.

## Requirements

CPython 3.10 or newer. Nothing else.

Verified on CPython 3.10, 3.11, 3.12 and 3.13, on Linux and Windows 10. macOS
has no recorded acceptance run.

Compatibility is recorded rather than asserted. `status` reports the running
interpreter and whether it is one the test suite has passed on. An interpreter
outside that set is not refused: it runs, and `status` says its behaviour has
not been measured. Only versions measured to break are refused, and none are
recorded today.

## Install

```bash
unzip useful-helpers-0.1.0.zip -d useful-helpers-release
cd useful-helpers-release
python -m factory attach /path/to/your/project
```

On Windows, use `py -m factory attach C:\path\to\your\project`.

Two launcher scripts do the same thing without needing the module form. They
work from any directory, and on Windows you can drag a folder from Explorer
onto `attach.bat`:

```
attach.bat C:\path\to\your\project
sh attach.sh /path/to/your/project
```

The shell script is invoked with `sh` because the release archive records every
file as non-executable, so that the artifact stays byte-reproducible.

Every later command runs the front door inside your project:

```bash
python /path/to/your/project/.useful-helpers/bin/helpers.py status
```

An alias is worth setting up:

```bash
alias helpers='python /path/to/your/project/.useful-helpers/bin/helpers.py'
```

Full walkthrough: [docs/QUICKSTART.md](docs/QUICKSTART.md).

## First use

```bash
helpers status              # identity, schema version, target root, interpreter
helpers substrate refresh   # observe the directory, explicit, never automatic
helpers awareness refresh   # build orientation over what was observed
helpers awareness current   # read it
```

Every command prints JSON to stdout. Exit codes are `0` on success, `1` on a
refusal or error, `2` on invalid usage.

## Command surface

| Command group | Purpose |
|---|---|
| `status`, `tools` | Identity, interpreter support, tool catalog |
| `call <tool>` | Run one tool through the governed host |
| `receipts`, `artifacts` | Durable record of every invocation |
| `journal` | Work memory you write yourself |
| `substrate` | Observation, evidence, claims, provenance tracing |
| `awareness` | Compact orientation over the current basis |
| `mutation` | The governed change loop: preview, approve, apply |
| `mcp` | Agent entrance on stdin and stdout |

Five mechanical tools ship with it: `inventory`, `read_file`, `search_text` and
`hash_file` at observe authority, and `write_file` at apply authority.

## Using it from an agent

`helpers mcp` speaks line-delimited JSON-RPC over stdio, MCP protocol
`2024-11-05`, advertising 21 tools over the same host and database the CLI uses.
A receipt created through MCP appears in `helpers receipts list` immediately.

```json
{
  "mcpServers": {
    "useful-helpers": {
      "command": "python",
      "args": ["/path/to/your/project/.useful-helpers/bin/helpers.py", "mcp"]
    }
  }
}
```

The agent entrance is removable. Delete `.useful-helpers/core/mcp.py` and
everything else keeps working; `helpers mcp` then returns
`{"error": {"code": "mcp_unavailable"}}` rather than failing obscurely.

Agent-facing detail, including how to pass `_authority` inside `arguments`, is in
[docs/QUICKSTART.md](docs/QUICKSTART.md#4-using-it-from-an-agent).

## What is in here

| Path | Holds |
|---|---|
| `product/` | The installed runtime. This is the instrument itself. |
| `factory/` | Attaching, updating, packaging and removing it |
| `docs/` | Product authority and user documentation |

Two rules hold throughout: the shipped runtime never imports from `factory/`, and
`factory` is never imported at runtime by an installed instance.

`RELEASE_MANIFEST.json` records a SHA-256 digest for every file in this release,
so you can verify that what you have is what was published.

This package is built from a separate repository that also holds the test
suite and the full construction record. Neither is distributed here; see
**Provenance** below.

## Documentation

| Document | For |
|---|---|
| [docs/QUICKSTART.md](docs/QUICKSTART.md) | Installing and using it |
| [docs/PRODUCT_CHARTER.md](docs/PRODUCT_CHARTER.md) | What it is for, and what it refuses to do |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | How it is put together |
| [CHANGELOG.md](CHANGELOG.md) | What is in this release, and its known limitations |
| [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md) | Dependency and provenance record |

## Provenance

This was not written in one pass. It was built in nine tranches, T0 through T8,
each declared before it was implemented, gated by an executable check, reviewed
externally, and closed only on explicit approval. The final cumulative gate run
passed 111 of 111 checks on CPython 3.13.

That record, the test suite, and the gates live in the source repository rather
than in this package. What ships here is the instrument and its documentation.

## License

MIT. Copyright © 2026 Jacob Lambert. See [LICENSE.md](LICENSE.md).

Use it, change it, ship it. The licence disclaims warranty and limits
liability, which matters here more than usual: this software writes to your
files. Keep backups.
