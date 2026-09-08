from __future__ import annotations

import hashlib
import json
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from product.core.constants import PRODUCT_VERSION


class ReleaseError(RuntimeError):
    pass


RELEASE_SCHEMA_VERSION = 1
ARCHIVE_NAME = f"useful-helpers-{PRODUCT_VERSION}.zip"
MANIFEST_NAME = "RELEASE_MANIFEST.json"
_FIXED_ZIP_TIME = (2026, 1, 1, 0, 0, 0)
_INCLUDED_ROOTS = ("product", "factory", "docs")
_INCLUDED_FILES = (
    "README.md",
    "CHANGELOG.md",
    "LICENSE.md",
    "THIRD-PARTY-NOTICES.md",
    "pyproject.toml",
    "attach.bat",
    "attach.sh",
)
_EXCLUDED_PARTS = {
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".git",
    ".builder",
    "tests",
    "release",
    "_projectmapper",
    "_exports",
}
_EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".7z", ".zip", ".sqlite", ".sqlite3", ".db"}


def build(output_dir: str | Path, *, source_root: str | Path | None = None) -> dict:
    root = Path(source_root).resolve() if source_root else Path(__file__).resolve().parents[1]
    destination = Path(output_dir).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    archive_path = destination / ARCHIVE_NAME
    manifest_path = destination / f"{ARCHIVE_NAME}.manifest.json"

    members = _release_members(root)
    manifest = {
        "schema_version": RELEASE_SCHEMA_VERSION,
        "product": "useful-helpers",
        "product_version": PRODUCT_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": {
            "head_commit": _git(root, "rev-parse", "HEAD"),
            "working_tree": _git(root, "status", "--short"),
        },
        "artifact": {
            "name": ARCHIVE_NAME,
            "format": "zip",
            "install_command": "python -m factory attach <target>",
            "update_command": "python -m factory update <target>",
            "uninstall_command": "python -m factory uninstall <target>",
        },
        "files": [
            {
                "path": relative,
                "size": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
            for relative, data in members
        ],
        "excluded_roots": sorted(_EXCLUDED_PARTS),
    }
    manifest_bytes = _canonical_json(manifest)
    archive_members = [*members, (MANIFEST_NAME, manifest_bytes)]
    _write_zip(archive_path, archive_members)
    artifact_sha256 = _sha256_file(archive_path)
    final_manifest = {
        **manifest,
        "artifact": {
            **manifest["artifact"],
            "sha256": artifact_sha256,
            "size": archive_path.stat().st_size,
            "manifest_path": MANIFEST_NAME,
        },
        "files": [
            *manifest["files"],
            {
                "path": MANIFEST_NAME,
                "size": len(manifest_bytes),
                "sha256": hashlib.sha256(manifest_bytes).hexdigest(),
            },
        ],
    }
    manifest_path.write_bytes(_canonical_json(final_manifest))
    return {
        "ok": True,
        "artifact": str(archive_path),
        "manifest": str(manifest_path),
        "artifact_sha256": artifact_sha256,
        "file_count": len(final_manifest["files"]),
        "source": final_manifest["source"],
    }


def inspect_archive(archive: str | Path) -> dict:
    archive_path = Path(archive).resolve()
    if not archive_path.is_file():
        raise ReleaseError(f"release artifact does not exist: {archive_path}")
    with zipfile.ZipFile(archive_path) as bundle:
        names = sorted(bundle.namelist())
        if MANIFEST_NAME not in names:
            raise ReleaseError("release artifact lacks RELEASE_MANIFEST.json")
        manifest = json.loads(bundle.read(MANIFEST_NAME).decode("utf-8"))
    return {
        "ok": True,
        "artifact": str(archive_path),
        "sha256": _sha256_file(archive_path),
        "files": names,
        "manifest": manifest,
    }


def _release_members(root: Path) -> list[tuple[str, bytes]]:
    members: list[tuple[str, bytes]] = []
    for folder in _INCLUDED_ROOTS:
        base = root / folder
        if not base.is_dir():
            raise ReleaseError(f"missing release root: {folder}")
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            relative = path.relative_to(root).as_posix()
            if _excluded(path.relative_to(root)):
                continue
            members.append((relative, path.read_bytes()))
    for filename in _INCLUDED_FILES:
        path = root / filename
        if path.is_file():
            members.append((filename, path.read_bytes()))
    if not any(relative == "factory/__main__.py" for relative, _ in members):
        raise ReleaseError("release artifact would not be factory-executable")
    if not any(relative == "product/bin/helpers.py" for relative, _ in members):
        raise ReleaseError("release artifact lacks installed front door")
    return sorted(members, key=lambda item: item[0])


def _excluded(relative: Path) -> bool:
    parts = set(relative.parts)
    if parts & _EXCLUDED_PARTS:
        return True
    return relative.suffix.lower() in _EXCLUDED_SUFFIXES


def _write_zip(path: Path, members: list[tuple[str, bytes]]) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as bundle:
        for relative, data in members:
            info = zipfile.ZipInfo(relative, _FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            bundle.writestr(info, data)


def _canonical_json(document: Any) -> bytes:
    return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(root: Path, *arguments: str) -> str:
    process = subprocess.run(
        ["git", *arguments],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if process.returncode:
        return "unavailable"
    return process.stdout.strip()
