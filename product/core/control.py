from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass

from . import registry, runtime_records, storage
from .constants import CONTROL_PLANE_VERSION, TOOL_CONTRACT_VERSION
from .containment import ContainmentError, resolve_declared_paths
from .contracts import ToolManifest, validate_json
from .instance import InstanceContext

_AUTHORITY_ORDER = {"observe": 0, "sandbox": 1, "apply": 2}


@dataclass(frozen=True)
class ControlPlane:
    context: InstanceContext

    def __post_init__(self) -> None:
        storage.bootstrap(self.context)

    def tools(self) -> list[dict]:
        return [record.public_record() for record in registry.discover(self.context).values()]

    def _envelope(self, tool_id: str, client: str, authority: str, **payload: object) -> dict:
        return {
            **payload,
            "tool_id": tool_id,
            "client": client,
            "authority": authority,
            "control_plane": {
                "version": CONTROL_PLANE_VERSION,
                "tool_contract": TOOL_CONTRACT_VERSION,
            },
        }

    def _failure(
        self,
        tool_id: str,
        client: str,
        authority: str,
        code: str,
        message: str,
        **extra: object,
    ) -> dict:
        return self._envelope(
            tool_id,
            client,
            authority,
            ok=False,
            error={"code": code, "message": message},
            **extra,
        )

    def _receipt_failure(
        self,
        tool_id: str,
        client: str,
        authority: str,
        message: str,
        started: float,
    ) -> dict:
        return self._failure(
            tool_id,
            client,
            authority,
            "receipt_persistence_failed",
            message,
            duration_ms=int((time.monotonic() - started) * 1000),
            durably_governed=False,
        )

    def _complete_receipt(
        self,
        receipt_id: str,
        response: dict,
        status: str,
        started: float,
        *,
        error_code: str | None = None,
        result_ok: bool | None = None,
        exit_code: int | None = None,
        manifest_digest: str | None = None,
        process: dict | None = None,
    ) -> dict:
        duration_ms = int(response.get("duration_ms") or (time.monotonic() - started) * 1000)
        response["receipt_id"] = receipt_id
        response["durably_governed"] = True
        try:
            artifact_id = runtime_records.complete_receipt(
                self.context,
                receipt_id,
                status=status,
                envelope=response,
                error_code=error_code,
                result_ok=result_ok,
                exit_code=exit_code,
                duration_ms=duration_ms,
                manifest_digest=manifest_digest,
                process=process,
            )
        except runtime_records.RecordError as exc:
            return self._receipt_failure(
                str(response.get("tool_id") or "unknown"),
                str(response.get("client") or "unknown"),
                str(response.get("authority") or "unknown"),
                str(exc),
                started,
            )
        response["artifact_id"] = artifact_id
        return response

    def _mechanical_context(self, manifest: ToolManifest) -> dict:
        domains = set(manifest.reads) | set(manifest.writes)
        excluded_roots = [str(self.context.instance_root)] if "target" in domains else []
        return {
            "target_root": str(self.context.target_root),
            "excluded_roots": excluded_roots,
        }

    def invoke(
        self,
        tool_id: str,
        arguments: dict,
        client: str,
        authority: str = "observe",
        timeout_seconds: int = 30,
    ) -> dict:
        started = time.monotonic()
        client = str(client or "").strip()
        authority = str(authority or "").lower()
        receipt_client = client or "unknown"
        receipt_authority = authority or "unknown"
        try:
            receipt_id = runtime_records.begin_receipt(
                self.context,
                tool_id=str(tool_id),
                client=receipt_client,
                authority=receipt_authority,
            )
        except runtime_records.RecordError as exc:
            return self._receipt_failure(
                str(tool_id),
                receipt_client,
                receipt_authority,
                str(exc),
                started,
            )
        if not client:
            response = self._failure(
                tool_id, "unknown", authority, "invalid_client", "client is required"
            )
            return self._complete_receipt(
                receipt_id,
                response,
                "refusal",
                started,
                error_code="invalid_client",
                result_ok=False,
            )
        if authority not in _AUTHORITY_ORDER:
            response = self._failure(
                tool_id, client, authority, "invalid_authority", f"unknown authority: {authority}"
            )
            return self._complete_receipt(
                receipt_id,
                response,
                "refusal",
                started,
                error_code="invalid_authority",
                result_ok=False,
            )
        if not isinstance(arguments, dict):
            response = self._failure(
                tool_id, client, authority, "invalid_arguments", "arguments must be an object"
            )
            return self._complete_receipt(
                receipt_id,
                response,
                "refusal",
                started,
                error_code="invalid_arguments",
                result_ok=False,
            )

        try:
            manifest = registry.get(self.context, tool_id)
        except registry.RegistryError as exc:
            response = self._failure(tool_id, client, authority, "registry_error", str(exc))
            return self._complete_receipt(
                receipt_id,
                response,
                "refusal",
                started,
                error_code="registry_error",
                result_ok=False,
            )

        if _AUTHORITY_ORDER[authority] < _AUTHORITY_ORDER[manifest.authority]:
            response = self._failure(
                tool_id,
                client,
                authority,
                "authority_denied",
                f"{tool_id} requires {manifest.authority} authority; caller supplied {authority}",
                required_authority=manifest.authority,
                manifest_digest=manifest.digest,
            )
            return self._complete_receipt(
                receipt_id,
                response,
                "refusal",
                started,
                error_code="authority_denied",
                result_ok=False,
                manifest_digest=manifest.digest,
            )

        input_errors = validate_json(arguments, manifest.input_schema)
        if input_errors:
            response = self._failure(
                tool_id,
                client,
                authority,
                "input_contract",
                "; ".join(input_errors),
                manifest_digest=manifest.digest,
            )
            return self._complete_receipt(
                receipt_id,
                response,
                "refusal",
                started,
                error_code="input_contract",
                result_ok=False,
                manifest_digest=manifest.digest,
            )
        try:
            resolved_arguments = resolve_declared_paths(self.context, manifest, arguments)
        except ContainmentError as exc:
            response = self._failure(
                tool_id,
                client,
                authority,
                "containment_refusal",
                str(exc),
                manifest_digest=manifest.digest,
            )
            return self._complete_receipt(
                receipt_id,
                response,
                "refusal",
                started,
                error_code="containment_refusal",
                result_ok=False,
                manifest_digest=manifest.digest,
            )

        request = {
            "args": resolved_arguments,
            "context": self._mechanical_context(manifest),
        }
        environment = _child_environment(self.context)
        environment["PYTHONUTF8"] = "1"

        timeout = max(1, min(int(timeout_seconds), 300))
        try:
            process = subprocess.run(
                [sys.executable, str(manifest.entry)],
                input=json.dumps(request),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                cwd=self.context.target_root,
                env=environment,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            response = self._failure(
                tool_id,
                client,
                authority,
                "timeout",
                f"tool exceeded {timeout} seconds",
                duration_ms=int((time.monotonic() - started) * 1000),
                manifest_digest=manifest.digest,
            )
            return self._complete_receipt(
                receipt_id,
                response,
                "failure",
                started,
                error_code="timeout",
                result_ok=False,
                manifest_digest=manifest.digest,
            )
        except OSError as exc:
            response = self._failure(
                tool_id,
                client,
                authority,
                "process_error",
                str(exc),
                duration_ms=int((time.monotonic() - started) * 1000),
                manifest_digest=manifest.digest,
            )
            return self._complete_receipt(
                receipt_id,
                response,
                "failure",
                started,
                error_code="process_error",
                result_ok=False,
                manifest_digest=manifest.digest,
            )

        duration_ms = int((time.monotonic() - started) * 1000)
        try:
            result = json.loads(process.stdout)
        except json.JSONDecodeError as exc:
            response = self._failure(
                tool_id,
                client,
                authority,
                "output_contract",
                f"tool output is not valid JSON: {exc}",
                duration_ms=duration_ms,
                exit_code=process.returncode,
                manifest_digest=manifest.digest,
            )
            return self._complete_receipt(
                receipt_id,
                response,
                "failure",
                started,
                error_code="output_contract",
                result_ok=False,
                exit_code=process.returncode,
                manifest_digest=manifest.digest,
                process={"stdout": process.stdout, "stderr": process.stderr},
            )
        if not isinstance(result, dict):
            response = self._failure(
                tool_id,
                client,
                authority,
                "output_contract",
                "tool output must be a JSON object",
                duration_ms=duration_ms,
                exit_code=process.returncode,
                manifest_digest=manifest.digest,
            )
            return self._complete_receipt(
                receipt_id,
                response,
                "failure",
                started,
                error_code="output_contract",
                result_ok=False,
                exit_code=process.returncode,
                manifest_digest=manifest.digest,
                process={"stdout": process.stdout, "stderr": process.stderr},
            )

        output_errors = validate_json(result, manifest.output_schema)
        if output_errors:
            response = self._failure(
                tool_id,
                client,
                authority,
                "output_contract",
                "; ".join(output_errors),
                duration_ms=duration_ms,
                exit_code=process.returncode,
                manifest_digest=manifest.digest,
                untrusted_result=result,
            )
            return self._complete_receipt(
                receipt_id,
                response,
                "failure",
                started,
                error_code="output_contract",
                result_ok=False,
                exit_code=process.returncode,
                manifest_digest=manifest.digest,
                process={"stdout": process.stdout, "stderr": process.stderr},
            )
        if process.returncode != 0:
            response = self._failure(
                tool_id,
                client,
                authority,
                "tool_process_failed",
                result.get("error") or process.stderr.strip() or f"exit code {process.returncode}",
                duration_ms=duration_ms,
                exit_code=process.returncode,
                manifest_digest=manifest.digest,
                result=result,
            )
            return self._complete_receipt(
                receipt_id,
                response,
                "failure",
                started,
                error_code="tool_process_failed",
                result_ok=False,
                exit_code=process.returncode,
                manifest_digest=manifest.digest,
                process={"stdout": process.stdout, "stderr": process.stderr},
            )

        response = self._envelope(
            tool_id,
            client,
            authority,
            ok=bool(result.get("ok")),
            result=result,
            duration_ms=duration_ms,
            exit_code=process.returncode,
            manifest_digest=manifest.digest,
        )
        return self._complete_receipt(
            receipt_id,
            response,
            "success" if response["ok"] else "failure",
            started,
            error_code=None if response["ok"] else "tool_result_not_ok",
            result_ok=bool(result.get("ok")),
            exit_code=process.returncode,
            manifest_digest=manifest.digest,
            process={"stdout": process.stdout, "stderr": process.stderr},
        )


def _child_environment(context: InstanceContext) -> dict[str, str]:
    allow = {
        "COMSPEC",
        "HOME",
        "LANG",
        "PATH",
        "PATHEXT",
        "SYSTEMDRIVE",
        "SYSTEMROOT",
        "TEMP",
        "TMP",
        "TMPDIR",
        "USERPROFILE",
        "WINDIR",
    }
    environment = {
        name: value
        for name, value in os.environ.items()
        if name.upper() in allow and not name.startswith("USEFUL_HELPERS_IDENTITY_")
    }
    environment["PYTHONPATH"] = str(context.instance_root)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return environment
