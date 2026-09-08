from __future__ import annotations

import hashlib
from pathlib import Path

from core.tool_runtime import MechanicalContext, run_tool


def run(arguments: dict, context: MechanicalContext) -> dict:
    path = Path(arguments["path"])
    if not path.is_file():
        return {"ok": False, "error": "path is not a file"}
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
            size += len(block)
    return {
        "ok": True,
        "tool": "hash_file",
        "handle": f"path:{context.target_relative(path)}",
        "algorithm": "sha256",
        "digest": digest.hexdigest(),
        "size_bytes": size,
    }


if __name__ == "__main__":
    raise SystemExit(run_tool(run))
