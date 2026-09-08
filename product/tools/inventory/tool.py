from __future__ import annotations

import os
from pathlib import Path

from core.tool_runtime import MechanicalContext, run_tool


def _resource(context: MechanicalContext, path: Path, kind: str) -> dict:
    relative = context.target_relative(path)
    record = {
        "handle": f"path:{relative}",
        "path": relative,
        "kind": kind,
    }
    if kind == "file":
        try:
            record["size_bytes"] = path.stat().st_size
        except OSError:
            record["size_bytes"] = None
    return record


def run(arguments: dict, context: MechanicalContext) -> dict:
    limit = int(arguments.get("limit", 5000))
    resources: list[dict] = []
    truncated = False

    for current, directory_names, file_names in os.walk(context.target_root):
        here = Path(current)
        directory_names[:] = sorted(
            name
            for name in directory_names
            if not context.is_excluded(here / name)
        )
        for name in directory_names:
            if len(resources) >= limit:
                truncated = True
                break
            path = here / name
            resources.append(
                _resource(context, path, "symlink" if path.is_symlink() else "directory")
            )
        if truncated:
            break
        for name in sorted(file_names):
            path = here / name
            if context.is_excluded(path):
                continue
            if len(resources) >= limit:
                truncated = True
                break
            resources.append(_resource(context, path, "symlink" if path.is_symlink() else "file"))
        if truncated:
            break

    return {
        "ok": True,
        "tool": "inventory",
        "target": "path:.",
        "returned": len(resources),
        "truncated": truncated,
        "resources": resources,
        "limitations": (["resource limit reached; additional resources are unknown"] if truncated else []),
    }


if __name__ == "__main__":
    raise SystemExit(run_tool(run))
