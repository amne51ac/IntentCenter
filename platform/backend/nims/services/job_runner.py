"""Synchronous job execution (API process). Replace with a real worker queue when scaling out."""

from __future__ import annotations

import uuid
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from nims.models_generated import ConnectorRegistration, JobDefinition, JobRun
from nims.timeutil import utc_now


def execute_job(
    db: Session,
    organization_id: uuid.UUID,
    job_key: str,
    run: JobRun,
    defn: JobDefinition,
) -> tuple[dict[str, Any], str]:
    """Run job logic; returns (output_dict, log_line). On failure, output should include `ok: false`."""
    if job_key == "noop":
        return (
            {"ok": True, "message": "No-op completed", "jobKey": defn.key},
            "Handler: noop (success).",
        )
    if job_key == "connector.sync":
        return _run_connector_sync(db, organization_id, run)
    return (
        {"ok": False, "error": f"no handler registered for job key: {job_key}"},
        f"Unknown job key: {job_key}",
    )


def _run_connector_sync(
    db: Session,
    organization_id: uuid.UUID,
    run: JobRun,
) -> tuple[dict[str, Any], str]:
    inp: dict[str, Any] = run.input if isinstance(run.input, dict) else {}
    cid = inp.get("connectorId")
    if not cid:
        return ({"ok": False, "error": "input.connectorId is required"}, "Missing connectorId in run input")
    try:
        c_uuid = uuid.UUID(str(cid))
    except ValueError:
        return ({"ok": False, "error": "invalid connectorId"}, "Invalid UUID in connectorId")

    row = (
        db.execute(
            select(ConnectorRegistration).where(
                ConnectorRegistration.id == c_uuid,
                ConnectorRegistration.organizationId == organization_id,
            ),
        )
    ).scalar_one_or_none()
    if row is None:
        return ({"ok": False, "error": "connector not found"}, "Connector not found")
    if not row.enabled:
        return ({"ok": False, "error": "connector disabled"}, "Connector disabled")

    t = (row.type or "").lower()
    settings = row.settings if isinstance(row.settings, dict) else {}
    out: dict[str, Any] | None
    log: str

    if t == "webhook_outbound":
        url = settings.get("url")
        if not url or not isinstance(url, str):
            out = {"ok": False, "error": "settings.url is required for webhook_outbound"}
            log = "Invalid settings: missing url"
        else:
            out, log = _http_request("POST", str(url), run)
    elif t in ("http_get", "generic_rest", "http_poll"):
        url = settings.get("url")
        if not url or not isinstance(url, str):
            out = {"ok": False, "error": "settings.url is required"}
            log = "Invalid settings: missing url"
        else:
            out, log = _http_request("GET", str(url), run)
    else:
        out = {
            "ok": True,
            "skipped": True,
            "connectorType": row.type,
            "reason": "No network probe for this type; use webhook_outbound or http_get to exercise outbounds.",
        }
        log = f"Placeholder handler for type {row.type!r} (no outbound HTTP)."

    now = utc_now()
    row.lastSyncAt = now
    row.lastError = None if (out and out.get("ok")) else str(out.get("error", log))[:2000] if out else log[:2000]
    row.healthStatus = "ok" if (out and out.get("ok")) else "error"
    row.updatedAt = now
    db.add(row)
    return out, log


def _http_request(method: str, url: str, run: JobRun) -> tuple[dict[str, Any], str]:
    """Perform a best-effort outbound call (SSRF: restrict to admin-created connectors in production)."""
    try:
        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            if method == "GET":
                r = client.get(url)
            else:
                r = client.post(url, json={})
        body: dict[str, Any] = {
            "ok": 200 <= r.status_code < 300,
            "statusCode": r.status_code,
            "bytes": len(r.content or b""),
        }
        if not body["ok"]:
            body["error"] = f"HTTP {r.status_code}"
        log = f"HTTP {method} {url} -> {r.status_code} ({body['bytes']} bytes)"
        return body, log
    except Exception as e:
        return ({"ok": False, "error": str(e)}), f"Request failed: {e}"
