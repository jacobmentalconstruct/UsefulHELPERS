from __future__ import annotations

import os
from pathlib import Path

from core.tool_runtime import MechanicalContext, run_tool

_MAX_FILE_BYTES = 2_000_000


def run(arguments: dict, context: MechanicalContext) -> dict:
    query = arguments["query"]
    case_sensitive = bool(arguments.get("case_sensitive", False))
    needle = query if case_sensitive else query.casefold()
    limit = int(arguments.get("limit", 100))
    matches: list[dict] = []
    considered = 0
    skipped_binary = 0
    skipped_large = 0
    skipped_symlinks = 0
    read_errors = 0
    truncated = False

    for current, directory_names, file_names in os.walk(context.target_root):
        here = Path(current)
        visible_directories = []
        for name in sorted(directory_names):
            path = here / name
            if context.is_excluded(path):
                continue
            if path.is_symlink():
                skipped_symlinks += 1
                continue
            visible_directories.append(name)
        directory_names[:] = visible_directories
        for name in sorted(file_names):
            path = here / name
            if context.is_excluded(path):
                continue
            if path.is_symlink():
                skipped_symlinks += 1
                continue
            try:
                size = path.stat().st_size
                if size > _MAX_FILE_BYTES:
                    skipped_large += 1
                    continue
                raw = path.read_bytes()
            except OSError:
                read_errors += 1
                continue
            if b"\x00" in raw[:8192]:
                skipped_binary += 1
                continue
            considered += 1
            text = raw.decode("utf-8", errors="replace")
            for line_number, line in enumerate(text.splitlines(), start=1):
                haystack = line if case_sensitive else line.casefold()
                if needle in haystack:
                    relative = context.target_relative(path)
                    matches.append(
                        {
                            "handle": f"path:{relative}#L{line_number}",
                            "path": relative,
                            "line": line_number,
                            "text": line[:500],
                        }
                    )
                    if len(matches) >= limit:
                        truncated = True
                        break
            if truncated:
                break
        if truncated:
            break

    limitations = []
    if skipped_binary:
        limitations.append(f"{skipped_binary} binary files were not searched")
    if skipped_large:
        limitations.append(f"{skipped_large} files over {_MAX_FILE_BYTES} bytes were not searched")
    if skipped_symlinks:
        limitations.append(f"{skipped_symlinks} symbolic links were not followed")
    if read_errors:
        limitations.append(f"{read_errors} files could not be read")
    if truncated:
        limitations.append("match limit reached; additional matches are unknown")
    return {
        "ok": True,
        "tool": "search_text",
        "query": query,
        "case_sensitive": case_sensitive,
        "files_considered": considered,
        "matches": matches,
        "returned": len(matches),
        "truncated": truncated,
        "limitations": limitations,
    }


if __name__ == "__main__":
    raise SystemExit(run_tool(run))
