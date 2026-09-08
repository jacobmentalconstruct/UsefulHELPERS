from __future__ import annotations

from pathlib import Path

from core.tool_runtime import MechanicalContext, run_tool


def run(arguments: dict, context: MechanicalContext) -> dict:
    path = Path(arguments["path"])
    if not path.is_file():
        return {"ok": False, "error": "path is not a file"}
    maximum = int(arguments.get("max_bytes", 1_000_000))
    with path.open("rb") as stream:
        content = stream.read(maximum + 1)
    truncated = len(content) > maximum
    if truncated:
        content = content[:maximum]
    return {
        "ok": True,
        "tool": "read_file",
        "handle": f"path:{context.target_relative(path)}",
        "content": content.decode("utf-8", errors="replace"),
        "bytes_returned": len(content),
        "truncated": truncated,
    }


if __name__ == "__main__":
    raise SystemExit(run_tool(run))
