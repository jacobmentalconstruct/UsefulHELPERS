from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .constants import INSTANCE_SCHEMA_VERSION, PRODUCT_VERSION

MANIFEST_NAME = "instance.json"


class InstanceError(RuntimeError):
    """Canonical identity is absent, malformed, or structurally untrue."""


@dataclass(frozen=True)
class InstanceContext:
    instance_root: Path
    target_root: Path
    state_root: Path
    logs_root: Path
    instance_uuid: str
    schema_version: int
    product_version: str
    created_at: str
    target_relation: str

def _canonical_uuid(value: object) -> str:
    if not isinstance(value, str):
        raise InstanceError("instance_uuid must be a canonical UUID string")
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError) as exc:
        raise InstanceError("instance_uuid must be a canonical UUID string") from exc
    canonical = str(parsed)
    if value != canonical:
        raise InstanceError("instance_uuid must use canonical lowercase UUID form")
    return canonical


def _validate(instance_root: Path, document: object) -> InstanceContext:
    if not isinstance(document, dict):
        raise InstanceError("instance.json must contain a JSON object")

    required = {
        "schema_version",
        "instance_uuid",
        "target_relation",
        "created_at",
        "product_version",
    }
    missing = sorted(required - set(document))
    if missing:
        raise InstanceError(f"instance.json is missing fields: {', '.join(missing)}")

    schema = document["schema_version"]
    if not isinstance(schema, int) or isinstance(schema, bool):
        raise InstanceError("schema_version must be an integer")
    if schema != INSTANCE_SCHEMA_VERSION:
        raise InstanceError(
            f"unsupported instance schema {schema}; runtime supports {INSTANCE_SCHEMA_VERSION}"
        )

    relation = document["target_relation"]
    if relation != "..":
        raise InstanceError("target_relation must be '..' for a direct-child installation")

    target_root = (instance_root / relation).resolve()
    if not target_root.is_dir():
        raise InstanceError("target_relation does not resolve to an existing directory")
    if instance_root.parent != target_root:
        raise InstanceError("the installed instance must be a direct child of its target")

    created_at = document["created_at"]
    if not isinstance(created_at, str):
        raise InstanceError("created_at must be an ISO-8601 string")
    try:
        parsed_created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise InstanceError("created_at must be an ISO-8601 string") from exc
    if parsed_created_at.tzinfo is None:
        raise InstanceError("created_at must include a timezone")

    product_version = document["product_version"]
    if not isinstance(product_version, str) or not product_version.strip():
        raise InstanceError("product_version must be a non-empty string")

    return InstanceContext(
        instance_root=instance_root,
        target_root=target_root,
        state_root=instance_root / "state",
        logs_root=instance_root / "logs",
        instance_uuid=_canonical_uuid(document["instance_uuid"]),
        schema_version=schema,
        product_version=product_version,
        created_at=created_at,
        target_relation=relation,
    )


def create(instance_root: str | Path, target_root: str | Path) -> InstanceContext:
    instance_path = Path(instance_root).resolve()
    target_path = Path(target_root).resolve()
    if not instance_path.is_dir():
        raise InstanceError("instance root must already exist")
    if not target_path.is_dir():
        raise InstanceError("target root must be an existing directory")
    if instance_path.parent != target_path:
        raise InstanceError("an instance must be created directly inside its target")

    manifest_path = instance_path / MANIFEST_NAME
    if manifest_path.exists():
        raise InstanceError("instance identity already exists; refusing to replace it")

    document = {
        "schema_version": INSTANCE_SCHEMA_VERSION,
        "instance_uuid": str(uuid.uuid4()),
        "target_relation": "..",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "product_version": PRODUCT_VERSION,
    }
    manifest_path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
    return _validate(instance_path, document)


def load(instance_root: str | Path) -> InstanceContext:
    instance_path = Path(instance_root).resolve()
    manifest_path = instance_path / MANIFEST_NAME
    if not manifest_path.is_file():
        raise InstanceError(f"no canonical instance identity at {manifest_path}")
    try:
        document = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InstanceError(f"instance.json is unreadable or invalid JSON: {exc}") from exc
    return _validate(instance_path, document)
