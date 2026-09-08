from __future__ import annotations

from pathlib import Path

from core.tool_runtime import MechanicalContext, run_tool


def run(arguments: dict, context: MechanicalContext) -> dict:
    if arguments.get("confirm") is not True:
        return {"ok": False, "error": "confirm must be true"}
    path = Path(arguments["path"])
    existed = path.exists()
    if existed and path.is_dir():
        return {"ok": False, "error": "path is a directory"}
    if existed and not bool(arguments.get("overwrite", False)):
        return {"ok": False, "error": "file exists and overwrite is false"}

    content = arguments["content"]
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = content.encode("utf-8")
    path.write_bytes(encoded)
    return {
        "ok": True,
        "tool": "write_file",
        "handle": f"path:{context.target_relative(path)}",
        "bytes_written": len(encoded),
        "created": not existed,
        "overwritten": existed,
    }


if __name__ == "__main__":
    raise SystemExit(run_tool(run))
