from __future__ import annotations

import json
import sys
from collections.abc import Callable
from typing import Any, TextIO

from . import app_journal, awareness, host, mutation, registry, runtime_records, substrate
from .control import ControlPlane
from .instance import InstanceContext

PROTOCOL_VERSION = "2024-11-05"


class McpError(RuntimeError):
    def __init__(self, code: int, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


def serve(
    context: InstanceContext,
    *,
    input_stream: TextIO | None = None,
    output_stream: TextIO | None = None,
) -> int:
    reader = input_stream or sys.stdin
    writer = output_stream or sys.stdout
    while True:
        line = reader.readline()
        if not line:
            return 0
        response = _handle_line(context, line)
        if response is None:
            continue
        _write(writer, response)
        if response.get("result", {}).get("shutdown") is True:
            return 0


def _handle_line(context: InstanceContext, line: str) -> dict | None:
    try:
        request = json.loads(line)
    except json.JSONDecodeError as exc:
        return _error(None, -32700, f"parse error: {exc}")
    request_id = request.get("id") if isinstance(request, dict) else None
    is_notification = isinstance(request, dict) and "id" not in request
    try:
        result = _dispatch(context, request)
    except McpError as exc:
        if is_notification:
            return None
        return _error(request_id, exc.code, exc.message)
    except Exception as exc:
        if is_notification:
            return None
        return _error(request_id, -32000, f"{type(exc).__name__}: {exc}")
    if is_notification:
        return None
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def _dispatch(context: InstanceContext, request: Any) -> dict:
    if not isinstance(request, dict):
        raise McpError(-32600, "request must be a JSON object")
    if request.get("jsonrpc") != "2.0":
        raise McpError(-32600, "jsonrpc must be 2.0")
    method = request.get("method")
    if not isinstance(method, str):
        raise McpError(-32600, "method is required")
    params = request.get("params") or {}
    if not isinstance(params, dict):
        raise McpError(-32602, "params must be an object")
    if method == "initialize":
        return _initialize()
    if method == "notifications/initialized":
        return {}
    if method == "tools/list":
        return {"tools": _tool_descriptors(context)}
    if method == "tools/call":
        return _tools_call(context, params)
    if method == "shutdown":
        return {"shutdown": True}
    raise McpError(-32601, f"unknown method: {method}")


def _initialize() -> dict:
    return {
        "protocolVersion": PROTOCOL_VERSION,
        "serverInfo": {"name": "useful-helpers", "version": "0.1"},
        "capabilities": {"tools": {}},
    }


def _tool_descriptors(context: InstanceContext) -> list[dict]:
    descriptors = [
        _descriptor("helpers.status", "Read installed instance status.", _schema({})),
        _descriptor("receipts.list", "List durable operation receipts.", _schema({"limit": "integer"})),
        _descriptor("receipts.read", "Read one durable operation receipt.", _schema({"receipt_id": "string"}, ["receipt_id"])),
        _descriptor("journal.list", "List deliberate App Journal entries.", _schema({"limit": "integer"})),
        _descriptor("journal.read", "Read one App Journal entry.", _schema({"entry_id": "string"}, ["entry_id"])),
        _descriptor("substrate.status", "Read epistemic substrate table counts.", _schema({})),
        _descriptor("substrate.resources.list", "List substrate resources.", _schema({"limit": "integer"})),
        _descriptor("substrate.trace", "Trace a substrate handle.", _schema({"handle": "string"}, ["handle"])),
        _descriptor("awareness.current", "Read the current awareness revision.", _schema({})),
        _descriptor("awareness.drill", "Drill into an awareness item.", _schema({"item_id": "string"}, ["item_id"])),
        _descriptor("mutation.status", "Read governed mutation state counts.", _schema({})),
        _descriptor(
            "mutation.preview_write",
            "Create a governed write preview.",
            _schema(
                {"path": "string", "content": "string", "overwrite": "boolean"},
                ["path", "content"],
            ),
        ),
        _descriptor(
            "mutation.approve",
            "Approve a governed mutation preview.",
            _schema(
                {"preview_id": "string", "journal_entry_id": "string"},
                ["preview_id"],
            ),
        ),
        _descriptor(
            "mutation.apply",
            "Apply an approved governed mutation.",
            _schema({"approval_id": "string", "preview_id": "string"}, ["approval_id"]),
        ),
        _descriptor("mutation.history", "List governed mutation records.", _schema({"limit": "integer"})),
        _descriptor("mutation.links", "List mutation links for a source id.", _schema({"source_id": "string"}, ["source_id"])),
    ]
    for manifest in registry.discover(context).values():
        descriptors.append(
            {
                "name": f"tool.{manifest.id}",
                "description": manifest.description,
                "inputSchema": _manifest_call_schema(manifest.input_schema),
            }
        )
    return descriptors


def _descriptor(name: str, description: str, schema: dict) -> dict:
    return {"name": name, "description": description, "inputSchema": schema}


def _schema(properties: dict[str, str], required: list[str] | None = None) -> dict:
    return {
        "type": "object",
        "properties": {
            name: {"type": kind}
            for name, kind in properties.items()
        },
        "required": required or [],
        "additionalProperties": False,
    }


def _manifest_call_schema(schema: dict) -> dict:
    projected = json.loads(json.dumps(schema))
    properties = projected.setdefault("properties", {})
    properties["_authority"] = {
        "type": "string",
        "enum": ["observe", "sandbox", "apply"],
        "description": "Optional governed host authority for this MCP call.",
    }
    properties["_timeout"] = {
        "type": "integer",
        "minimum": 1,
        "description": "Optional governed host timeout in seconds.",
    }
    projected["additionalProperties"] = False
    return projected


def _tools_call(context: InstanceContext, params: dict) -> dict:
    name = params.get("name")
    arguments = params.get("arguments") or {}
    if not isinstance(name, str):
        raise McpError(-32602, "tool name is required")
    if not isinstance(arguments, dict):
        raise McpError(-32602, "tool arguments must be an object")
    if name.startswith("tool."):
        structured = _call_manifest_tool(context, name.removeprefix("tool."), arguments, params)
    else:
        structured = _call_projection(context, name, arguments)
    return {
        "content": [{"type": "text", "text": json.dumps(structured, sort_keys=True)}],
        "structuredContent": structured,
        "isError": not bool(structured.get("ok", True)),
    }


def _call_manifest_tool(context: InstanceContext, tool_id: str, arguments: dict, envelope: dict) -> dict:
    tool_arguments = dict(arguments)
    authority = envelope.get("authority", tool_arguments.pop("_authority", "observe"))
    if authority not in {"observe", "sandbox", "apply"}:
        raise McpError(-32602, "authority must be observe, sandbox, or apply")
    timeout_raw = envelope.get("timeout", tool_arguments.pop("_timeout", 30))
    if not isinstance(timeout_raw, int) or isinstance(timeout_raw, bool):
        raise McpError(-32602, "timeout must be an integer")
    return ControlPlane(context).invoke(
        tool_id,
        tool_arguments,
        client="mcp",
        authority=authority,
        timeout_seconds=timeout_raw,
    )


def _call_projection(context: InstanceContext, name: str, arguments: dict) -> dict:
    operations: dict[str, Callable[[dict], dict]] = {
        "helpers.status": lambda _: host.status(context),
        "receipts.list": lambda args: {
            "ok": True,
            "receipts": runtime_records.list_receipts(context, args.get("limit", 50)),
        },
        "receipts.read": lambda args: {
            "ok": True,
            "receipt": runtime_records.read_receipt(context, _required(args, "receipt_id")),
        },
        "journal.list": lambda args: {
            "ok": True,
            "entries": app_journal.list_entries(context, args.get("limit", 50)),
        },
        "journal.read": lambda args: {
            "ok": True,
            **app_journal.read_entry(context, _required(args, "entry_id")),
        },
        "substrate.status": lambda _: substrate.status(context),
        "substrate.resources.list": lambda args: {
            "ok": True,
            "resources": substrate.list_resources(context, args.get("limit", 100)),
        },
        "substrate.trace": lambda args: {
            "ok": True,
            "trace": substrate.trace(context, _required(args, "handle")),
        },
        "awareness.current": lambda _: awareness.current(context),
        "awareness.drill": lambda args: {
            "ok": True,
            "drill": awareness.drill(context, _required(args, "item_id")),
        },
        "mutation.status": lambda _: mutation.status(context),
        "mutation.preview_write": lambda args: mutation.preview_write(
            context,
            path=_required(args, "path"),
            content=_required(args, "content"),
            overwrite=bool(args.get("overwrite", False)),
        ),
        "mutation.approve": lambda args: mutation.approve(
            context,
            _required(args, "preview_id"),
            journal_entry_id=args.get("journal_entry_id"),
        ),
        "mutation.apply": lambda args: mutation.apply(
            context,
            _required(args, "approval_id"),
            preview_id=args.get("preview_id"),
        ),
        "mutation.history": lambda args: {
            "ok": True,
            "mutations": mutation.list_history(context, args.get("limit", 50)),
        },
        "mutation.links": lambda args: {
            "ok": True,
            "links": mutation.links(context, _required(args, "source_id")),
        },
    }
    try:
        operation = operations[name]
    except KeyError as exc:
        raise McpError(-32602, f"unknown tool: {name}") from exc
    return operation(arguments)


def _required(arguments: dict, name: str) -> str:
    value = arguments.get(name)
    if not isinstance(value, str) or not value:
        raise McpError(-32602, f"{name} is required")
    return value


def _error(request_id: object, code: int, message: str) -> dict:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


def _write(writer: TextIO, response: dict) -> None:
    writer.write(json.dumps(response, separators=(",", ":")) + "\n")
    writer.flush()
