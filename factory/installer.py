from __future__ import annotations

import shutil
import uuid
from pathlib import Path

from product.core import instance, storage


class AttachError(RuntimeError):
    pass


_PAYLOAD_DIRECTORIES = ("bin", "core", "tools")


def _product_root() -> Path:
    return Path(__file__).resolve().parents[1] / "product"


def attach(target: str | Path) -> dict:
    """Positively assemble one new instrument inside an existing target."""
    target_root = Path(target).expanduser().resolve()
    if not target_root.is_dir():
        raise AttachError(f"target must be an existing directory: {target_root}")

    instance_root = target_root / ".useful-helpers"
    if instance_root.exists():
        raise AttachError(f"an entry already exists at {instance_root}; refusing to overwrite it")

    product_root = _product_root()
    missing = [name for name in _PAYLOAD_DIRECTORIES if not (product_root / name).is_dir()]
    if missing:
        raise AttachError(f"product payload is incomplete: missing {', '.join(missing)}")

    instance_root.mkdir()
    try:
        for name in _PAYLOAD_DIRECTORIES:
            shutil.copytree(
                product_root / name,
                instance_root / name,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
        (instance_root / "state" / "objects").mkdir(parents=True)
        (instance_root / "logs").mkdir()
        context = instance.create(instance_root, target_root)
        storage.bootstrap(context)
    except Exception as exc:
        shutil.rmtree(instance_root, ignore_errors=True)
        if isinstance(exc, AttachError):
            raise
        raise AttachError(f"attachment failed: {exc}") from exc

    return {
        "instance_uuid": context.instance_uuid,
        "instance": ".useful-helpers",
        "target_relation": context.target_relation,
        "front_door": ".useful-helpers/bin/helpers.py",
    }


def update(target: str | Path) -> dict:
    """Replace installed runtime payload while preserving instance identity and state."""
    target_root = Path(target).expanduser().resolve()
    instance_root = target_root / ".useful-helpers"
    if not target_root.is_dir():
        raise AttachError(f"target must be an existing directory: {target_root}")
    if not instance_root.is_dir():
        raise AttachError(f"no installed .useful-helpers exists at {instance_root}")

    context = instance.load(instance_root)
    storage.bootstrap(context)
    product_root = _product_root()
    missing = [name for name in _PAYLOAD_DIRECTORIES if not (product_root / name).is_dir()]
    if missing:
        raise AttachError(f"product payload is incomplete: missing {', '.join(missing)}")

    token = uuid.uuid4().hex
    staging_root = instance_root / f".update-{token}"
    backups: list[tuple[Path, Path]] = []
    try:
        staging_root.mkdir()
        for name in _PAYLOAD_DIRECTORIES:
            shutil.copytree(
                product_root / name,
                staging_root / name,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
            )
        for name in _PAYLOAD_DIRECTORIES:
            current = instance_root / name
            backup = instance_root / f".old-{name}-{token}"
            if current.exists():
                current.rename(backup)
                backups.append((current, backup))
            shutil.copytree(staging_root / name, current)
            shutil.rmtree(staging_root / name, ignore_errors=True)
        for _, backup in backups:
            shutil.rmtree(backup, ignore_errors=True)
        shutil.rmtree(staging_root, ignore_errors=True)
    except Exception as exc:
        for current, backup in reversed(backups):
            if not current.exists() and backup.exists():
                backup.rename(current)
        shutil.rmtree(staging_root, ignore_errors=True)
        raise AttachError(f"update failed: {exc}") from exc

    storage.bootstrap(context)
    return {
        "instance_uuid": context.instance_uuid,
        "instance": ".useful-helpers",
        "target_relation": context.target_relation,
        "front_door": ".useful-helpers/bin/helpers.py",
        "updated": True,
    }


def uninstall(target: str | Path) -> dict:
    """Remove the instrument footprint without touching target-owned work products."""
    target_root = Path(target).expanduser().resolve()
    instance_root = target_root / ".useful-helpers"
    if not target_root.is_dir():
        raise AttachError(f"target must be an existing directory: {target_root}")
    if not instance_root.exists():
        raise AttachError(f"no installed .useful-helpers exists at {instance_root}")
    shutil.rmtree(instance_root)
    return {"removed": ".useful-helpers"}
