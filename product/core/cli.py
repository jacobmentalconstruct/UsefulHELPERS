from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

from . import app_journal, awareness, host, mutation, registry, runtime_records, storage, substrate
from .control import ControlPlane
from .instance import InstanceError, load


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="helpers")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    commands.add_parser("tools")
    commands.add_parser("mcp")

    call = commands.add_parser("call")
    call.add_argument("tool_id")
    call.add_argument("--args", default="{}", help="JSON object of tool arguments")
    call.add_argument("--authority", choices=("observe", "sandbox", "apply"), default="observe")
    call.add_argument("--client", default="cli")
    call.add_argument("--timeout", type=int, default=30)

    receipts = commands.add_parser("receipts")
    receipt_commands = receipts.add_subparsers(dest="receipt_command", required=True)
    receipt_list = receipt_commands.add_parser("list")
    receipt_list.add_argument("--limit", type=int, default=50)
    receipt_read = receipt_commands.add_parser("read")
    receipt_read.add_argument("receipt_id")

    artifacts = commands.add_parser("artifacts")
    artifact_commands = artifacts.add_subparsers(dest="artifact_command", required=True)
    artifact_list = artifact_commands.add_parser("list")
    artifact_list.add_argument("--limit", type=int, default=50)
    artifact_read = artifact_commands.add_parser("read")
    artifact_read.add_argument("artifact_id")

    journal = commands.add_parser("journal")
    journal_commands = journal.add_subparsers(dest="journal_command", required=True)
    journal_list = journal_commands.add_parser("list")
    journal_list.add_argument("--limit", type=int, default=50)
    journal_add = journal_commands.add_parser("add")
    journal_add.add_argument("--type", choices=("entry", "decision", "backlog", "status"), default="entry")
    journal_add.add_argument(
        "--status",
        choices=("open", "closed", "decided", "parked", "blocked"),
        default="open",
    )
    journal_add.add_argument("--title", required=True)
    journal_add.add_argument("--body", default="")
    journal_read = journal_commands.add_parser("read")
    journal_read.add_argument("entry_id")
    journal_link = journal_commands.add_parser("link")
    journal_link.add_argument("entry_id")
    journal_link.add_argument("target_id")

    substrate_parser = commands.add_parser("substrate")
    substrate_commands = substrate_parser.add_subparsers(
        dest="substrate_command",
        required=True,
    )
    substrate_commands.add_parser("status")
    substrate_commands.add_parser("refresh")
    resources = substrate_commands.add_parser("resources")
    resource_commands = resources.add_subparsers(dest="resource_command", required=True)
    resource_list = resource_commands.add_parser("list")
    resource_list.add_argument("--limit", type=int, default=100)
    resource_read = resource_commands.add_parser("read")
    resource_read.add_argument("handle")
    versions = substrate_commands.add_parser("versions")
    version_commands = versions.add_subparsers(dest="version_command", required=True)
    version_list = version_commands.add_parser("list")
    version_list.add_argument("handle", nargs="?")
    version_read = version_commands.add_parser("read")
    version_read.add_argument("version_id")
    observations = substrate_commands.add_parser("observations")
    observation_commands = observations.add_subparsers(
        dest="observation_command",
        required=True,
    )
    observation_list = observation_commands.add_parser("list")
    observation_list.add_argument("--limit", type=int, default=100)
    observation_read = observation_commands.add_parser("read")
    observation_read.add_argument("observation_id")
    evidence = substrate_commands.add_parser("evidence")
    evidence_commands = evidence.add_subparsers(dest="evidence_command", required=True)
    evidence_read = evidence_commands.add_parser("read")
    evidence_read.add_argument("evidence_id")
    claims = substrate_commands.add_parser("claims")
    claim_commands = claims.add_subparsers(dest="claim_command", required=True)
    claim_list = claim_commands.add_parser("list")
    claim_list.add_argument("--limit", type=int, default=100)
    claim_read = claim_commands.add_parser("read")
    claim_read.add_argument("claim_id")
    relations = substrate_commands.add_parser("relations")
    relation_commands = relations.add_subparsers(dest="relation_command", required=True)
    relation_read = relation_commands.add_parser("read")
    relation_read.add_argument("relation_id")
    trace = substrate_commands.add_parser("trace")
    trace.add_argument("handle")

    awareness_parser = commands.add_parser("awareness")
    awareness_commands = awareness_parser.add_subparsers(
        dest="awareness_command",
        required=True,
    )
    awareness_commands.add_parser("status")
    awareness_commands.add_parser("refresh")
    awareness_commands.add_parser("current")
    awareness_revisions = awareness_commands.add_parser("revisions")
    awareness_revision_commands = awareness_revisions.add_subparsers(
        dest="awareness_revision_command",
        required=True,
    )
    awareness_revision_list = awareness_revision_commands.add_parser("list")
    awareness_revision_list.add_argument("--limit", type=int, default=50)
    awareness_revision_read = awareness_revision_commands.add_parser("read")
    awareness_revision_read.add_argument("awareness_id")
    awareness_drill = awareness_commands.add_parser("drill")
    awareness_drill.add_argument("item_id")

    mutation_parser = commands.add_parser("mutation")
    mutation_commands = mutation_parser.add_subparsers(
        dest="mutation_command",
        required=True,
    )
    mutation_commands.add_parser("status")
    preview_write = mutation_commands.add_parser("preview-write")
    preview_write.add_argument("--path", required=True)
    preview_write.add_argument("--content", required=True)
    preview_write.add_argument("--overwrite", action="store_true")
    approve = mutation_commands.add_parser("approve")
    approve.add_argument("preview_id")
    approve.add_argument("--journal-entry")
    apply = mutation_commands.add_parser("apply")
    apply.add_argument("approval_id")
    apply.add_argument("--preview")
    history = mutation_commands.add_parser("history")
    history.add_argument("--limit", type=int, default=50)
    links = mutation_commands.add_parser("links")
    links.add_argument("source_id")
    return parser


def _emit(document: dict) -> None:
    print(json.dumps(document, indent=2, sort_keys=True))


def main(instance_root: str | Path, argv: list[str] | None = None) -> int:
    try:
        arguments = _parser().parse_args(argv)
        context = load(instance_root)
        if arguments.command == "status":
            response = host.status(context)
        elif arguments.command == "tools":
            response = {"ok": True, "tools": ControlPlane(context).tools()}
        elif arguments.command == "mcp":
            try:
                from . import mcp
            except ImportError as exc:
                _emit(
                    {
                        "ok": False,
                        "error": {
                            "code": "mcp_unavailable",
                            "message": f"MCP adapter is not installed or cannot be loaded: {exc}",
                        },
                    }
                )
                return 1

            return mcp.serve(context)
        elif arguments.command == "call":
            try:
                tool_arguments = json.loads(arguments.args)
            except json.JSONDecodeError as exc:
                _emit({"ok": False, "error": {"code": "bad_json", "message": str(exc)}})
                return 2
            response = ControlPlane(context).invoke(
                arguments.tool_id,
                tool_arguments,
                client=arguments.client,
                authority=arguments.authority,
                timeout_seconds=arguments.timeout,
            )
        elif arguments.command == "receipts":
            if arguments.receipt_command == "list":
                response = {
                    "ok": True,
                    "receipts": runtime_records.list_receipts(context, arguments.limit),
                }
            else:
                response = {
                    "ok": True,
                    "receipt": runtime_records.read_receipt(context, arguments.receipt_id),
                }
        elif arguments.command == "artifacts":
            if arguments.artifact_command == "list":
                response = {
                    "ok": True,
                    "artifacts": runtime_records.list_artifacts(context, arguments.limit),
                }
            else:
                response = {
                    "ok": True,
                    "artifact": runtime_records.read_artifact(context, arguments.artifact_id),
                }
        elif arguments.command == "journal":
            if arguments.journal_command == "list":
                response = {
                    "ok": True,
                    "entries": app_journal.list_entries(context, arguments.limit),
                }
            elif arguments.journal_command == "add":
                response = {
                    "ok": True,
                    "entry": app_journal.add_entry(
                        context,
                        entry_type=arguments.type,
                        status=arguments.status,
                        title=arguments.title,
                        body=arguments.body,
                    ),
                }
            elif arguments.journal_command == "read":
                response = {"ok": True, **app_journal.read_entry(context, arguments.entry_id)}
            else:
                response = {
                    "ok": True,
                    "link": app_journal.link_entry(
                        context,
                        arguments.entry_id,
                        arguments.target_id,
                    ),
                }
        elif arguments.command == "substrate":
            if arguments.substrate_command == "status":
                response = substrate.status(context)
            elif arguments.substrate_command == "refresh":
                response = substrate.refresh(context)
            elif arguments.substrate_command == "resources":
                if arguments.resource_command == "list":
                    response = {
                        "ok": True,
                        "resources": substrate.list_resources(context, arguments.limit),
                    }
                else:
                    response = {
                        "ok": True,
                        "resource": substrate.read_resource(context, arguments.handle),
                    }
            elif arguments.substrate_command == "versions":
                if arguments.version_command == "list":
                    response = {
                        "ok": True,
                        "versions": substrate.list_versions(context, arguments.handle),
                    }
                else:
                    response = {
                        "ok": True,
                        "version": substrate.read_version(context, arguments.version_id),
                    }
            elif arguments.substrate_command == "observations":
                if arguments.observation_command == "list":
                    response = {
                        "ok": True,
                        "observations": substrate.list_observations(context, arguments.limit),
                    }
                else:
                    response = {
                        "ok": True,
                        "observation": substrate.read_observation(
                            context,
                            arguments.observation_id,
                        ),
                    }
            elif arguments.substrate_command == "evidence":
                response = {
                    "ok": True,
                    "evidence": substrate.read_evidence(context, arguments.evidence_id),
                }
            elif arguments.substrate_command == "claims":
                if arguments.claim_command == "list":
                    response = {
                        "ok": True,
                        "claims": substrate.list_claims(context, arguments.limit),
                    }
                else:
                    response = {
                        "ok": True,
                        "claim": substrate.read_claim(context, arguments.claim_id),
                    }
            elif arguments.substrate_command == "relations":
                response = {
                    "ok": True,
                    "relation": substrate.read_relation(context, arguments.relation_id),
                }
            else:
                response = {"ok": True, "trace": substrate.trace(context, arguments.handle)}
        elif arguments.command == "awareness":
            if arguments.awareness_command == "status":
                response = awareness.status(context)
            elif arguments.awareness_command == "refresh":
                response = awareness.refresh(context)
            elif arguments.awareness_command == "current":
                response = awareness.current(context)
            elif arguments.awareness_command == "revisions":
                if arguments.awareness_revision_command == "list":
                    response = {
                        "ok": True,
                        "revisions": awareness.list_revisions(context, arguments.limit),
                    }
                else:
                    response = {
                        "ok": True,
                        "revision": awareness.read_revision(context, arguments.awareness_id),
                    }
            else:
                response = {"ok": True, "drill": awareness.drill(context, arguments.item_id)}
        elif arguments.command == "mutation":
            if arguments.mutation_command == "status":
                response = mutation.status(context)
            elif arguments.mutation_command == "preview-write":
                response = mutation.preview_write(
                    context,
                    path=arguments.path,
                    content=arguments.content,
                    overwrite=arguments.overwrite,
                )
            elif arguments.mutation_command == "approve":
                response = mutation.approve(
                    context,
                    arguments.preview_id,
                    journal_entry_id=arguments.journal_entry,
                )
            elif arguments.mutation_command == "apply":
                response = mutation.apply(
                    context,
                    arguments.approval_id,
                    preview_id=arguments.preview,
                )
            elif arguments.mutation_command == "history":
                response = {
                    "ok": True,
                    "mutations": mutation.list_history(context, arguments.limit),
                }
            else:
                response = {"ok": True, "links": mutation.links(context, arguments.source_id)}
        else:
            response = {"ok": False, "error": {"code": "unknown_command"}}
    except (
        InstanceError,
        storage.StorageError,
        registry.RegistryError,
        runtime_records.RecordError,
        app_journal.JournalError,
        substrate.SubstrateError,
        awareness.AwarenessError,
        mutation.MutationError,
        sqlite3.Error,
        OSError,
        ValueError,
    ) as exc:
        _emit(
            {
                "ok": False,
                "error": {"code": type(exc).__name__, "message": str(exc)},
            }
        )
        return 1

    _emit(response)
    return 0 if response.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main(Path(__file__).resolve().parents[1], sys.argv[1:]))
