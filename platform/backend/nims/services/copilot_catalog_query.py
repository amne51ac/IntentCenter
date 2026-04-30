"""Composable, org-scoped catalog aggregates for the copilot (validated query ids; server-side SQL only)."""

from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy import and_, distinct, func, select
from sqlalchemy.orm import Session

from nims.models_generated import (
    Circuit,
    CircuitTermination,
    Device,
    DeviceRole,
    DeviceType,
    Location,
    Manufacturer,
    Provider,
    Rack,
)

CATALOG_MAX_BREAKDOWN = 200

# Exposed to OpenAI: BaseEntity / dimension. Single namespace for composable tools.
CATALOG_QUERY_SPECS: list[str] = [
    "Device/location",
    "Device/device_type",
    "Device/device_role",
    "Device/status",
    "Circuit/location",
    "Circuit/provider",
    "Circuit/status",
    "Rack/location",
]

_PAIR_ALIASES: dict[str, str] = {
    "device/location": "Device/location",
    "device/devicetype": "Device/device_type",
    "device/device_type": "Device/device_type",
    "device/type": "Device/device_type",
    "device/role": "Device/device_role",
    "device/device_role": "Device/device_role",
    "device/status": "Device/status",
    "circuit/location": "Circuit/location",
    "circuit/provider": "Circuit/provider",
    "circuit/status": "Circuit/status",
    "rack/location": "Rack/location",
}


def normalize_catalog_query_spec(raw: str) -> str | None:
    """Map user/model input to a canonical CATALOG_QUERY_SPECS entry; None if not allowed."""
    t0 = (raw or "").strip()
    if not t0:
        return None
    # Direct match first (case fold)
    low = t0.lower()
    for s in CATALOG_QUERY_SPECS:
        if s.lower() == low:
            return s
    t = t0.replace("::", "/").replace(".", "/")
    parts = [p for p in t.split("/") if p.strip()]
    if len(parts) >= 2:
        a, b = parts[0].strip().lower(), parts[1].strip().lower()
        if f"{a}/{b}" in _PAIR_ALIASES:
            return _PAIR_ALIASES[f"{a}/{b}"]
        for s in CATALOG_QUERY_SPECS:
            if s.lower() == f"{a}/{b}":
                return s
    return None


def legacy_device_group_to_spec(group_by: str) -> str | None:
    """`device_count_breakdown` group_by string → composable spec."""
    b = (group_by or "").strip().lower()
    m = {
        "location": "Device/location",
        "loc": "Device/location",
        "site": "Device/location",
        "device_type": "Device/device_type",
        "devicetype": "Device/device_type",
        "type": "Device/device_type",
        "model": "Device/device_type",
        "device_role": "Device/device_role",
        "devicerole": "Device/device_role",
        "role": "Device/device_role",
        "status": "Device/status",
        "device_status": "Device/status",
        "circuits_by_location": "Circuit/location",
        "circuit_by_location": "Circuit/location",
        "circuits_per_location": "Circuit/location",
        "circuits_location": "Circuit/location",
    }
    return m.get(b)


def run_catalog_aggregation(
    db: Session,
    organization_id: uuid.UUID,
    spec: str,
) -> list[dict[str, Any]] | str:
    s = (spec or "").strip()
    canon = next((c for c in CATALOG_QUERY_SPECS if c.lower() == s.lower()), None) or normalize_catalog_query_spec(
        s
    )
    if not canon:
        return f"Unknown query: {spec!r}."

    if canon == "Device/location":
        q = (
            select(Location.id, Location.name, func.count(Device.id))
            .select_from(Device)
            .outerjoin(
                Rack,
                and_(
                    Device.rackId == Rack.id,
                    Rack.organizationId == organization_id,
                    Rack.deletedAt.is_(None),
                ),
            )
            .outerjoin(
                Location,
                and_(
                    Rack.locationId == Location.id,
                    Location.organizationId == organization_id,
                    Location.deletedAt.is_(None),
                ),
            )
            .where(Device.organizationId == organization_id, Device.deletedAt.is_(None))
            .group_by(Location.id, Location.name)
        )
        rows = db.execute(q).all()
        out: list[dict[str, Any]] = []
        for loc_id, loc_name, cnt in rows:
            c = int(cnt or 0)
            if c == 0:
                continue
            if loc_id is None:
                out.append({"label": "Unplaced (no rack or unknown location)", "id": None, "count": c})
            else:
                out.append({"label": str(loc_name or ""), "id": str(loc_id), "count": c})
        out.sort(key=lambda r: -r["count"])
        return out[:CATALOG_MAX_BREAKDOWN]

    if canon == "Device/device_type":
        q = (
            select(
                DeviceType.id,
                Manufacturer.name,
                DeviceType.model,
                func.count(Device.id),
            )
            .select_from(Device)
            .join(DeviceType, Device.deviceTypeId == DeviceType.id)
            .join(Manufacturer, DeviceType.manufacturerId == Manufacturer.id)
            .where(Device.organizationId == organization_id, Device.deletedAt.is_(None))
            .group_by(DeviceType.id, Manufacturer.name, DeviceType.model)
            .order_by(func.count(Device.id).desc())
            .limit(CATALOG_MAX_BREAKDOWN)
        )
        rows = db.execute(q).all()
        r2: list[dict[str, Any]] = []
        for dt_id, mname, dmodel, cnt in rows:
            mfr = str(mname or "")
            mdl = str(dmodel or "")
            label = f"{mfr} {mdl}".strip() or mdl
            r2.append({"label": label, "id": str(dt_id), "count": int(cnt or 0)})
        return r2

    if canon == "Device/device_role":
        q = (
            select(DeviceRole.id, DeviceRole.name, func.count(Device.id))
            .select_from(Device)
            .join(DeviceRole, Device.deviceRoleId == DeviceRole.id)
            .where(Device.organizationId == organization_id, Device.deletedAt.is_(None))
            .group_by(DeviceRole.id, DeviceRole.name)
            .order_by(func.count(Device.id).desc())
            .limit(CATALOG_MAX_BREAKDOWN)
        )
        rows = db.execute(q).all()
        return [{"label": str(n or ""), "id": str(dr_id), "count": int(cnt or 0)} for dr_id, n, cnt in rows]

    if canon == "Device/status":
        q = (
            select(Device.status, func.count(Device.id))
            .where(Device.organizationId == organization_id, Device.deletedAt.is_(None))
            .group_by(Device.status)
            .order_by(func.count(Device.id).desc())
            .limit(CATALOG_MAX_BREAKDOWN)
        )
        rows = db.execute(q).all()
        r3: list[dict[str, Any]] = []
        for st, cnt in rows:
            lab = st.value if hasattr(st, "value") else str(st)
            r3.append({"label": str(lab), "id": None, "count": int(cnt or 0)})
        return r3

    if canon == "Circuit/location":
        q = (
            select(Location.id, Location.name, func.count(distinct(Circuit.id)))
            .select_from(CircuitTermination)
            .join(
                Circuit,
                and_(
                    CircuitTermination.circuitId == Circuit.id,
                    Circuit.organizationId == organization_id,
                    Circuit.deletedAt.is_(None),
                ),
            )
            .join(
                Location,
                and_(
                    CircuitTermination.locationId == Location.id,
                    Location.organizationId == organization_id,
                    Location.deletedAt.is_(None),
                ),
            )
            .where(
                CircuitTermination.organizationId == organization_id,
                CircuitTermination.deletedAt.is_(None),
                CircuitTermination.locationId.isnot(None),
            )
            .group_by(Location.id, Location.name)
            .order_by(func.count(distinct(Circuit.id)).desc())
            .limit(CATALOG_MAX_BREAKDOWN)
        )
        rows = db.execute(q).all()
        return [
            {"label": str(ln or ""), "id": str(lid), "count": int(n or 0)}
            for lid, ln, n in rows
            if int(n or 0) > 0
        ]

    if canon == "Circuit/provider":
        q = (
            select(Provider.id, Provider.name, func.count(Circuit.id))
            .select_from(Circuit)
            .join(Provider, Circuit.providerId == Provider.id)
            .where(
                Circuit.organizationId == organization_id,
                Circuit.deletedAt.is_(None),
                Provider.organizationId == organization_id,
                Provider.deletedAt.is_(None),
            )
            .group_by(Provider.id, Provider.name)
            .order_by(func.count(Circuit.id).desc())
            .limit(CATALOG_MAX_BREAKDOWN)
        )
        rows = db.execute(q).all()
        return [
            {"label": str(n or ""), "id": str(pr_id), "count": int(cnt or 0)}
            for pr_id, n, cnt in rows
        ]

    if canon == "Circuit/status":
        q = (
            select(Circuit.status, func.count(Circuit.id))
            .where(
                Circuit.organizationId == organization_id,
                Circuit.deletedAt.is_(None),
            )
            .group_by(Circuit.status)
            .order_by(func.count(Circuit.id).desc())
            .limit(CATALOG_MAX_BREAKDOWN)
        )
        rows = db.execute(q).all()
        r4: list[dict[str, Any]] = []
        for st, cnt in rows:
            lab = st.value if hasattr(st, "value") else str(st)
            r4.append({"label": str(lab), "id": None, "count": int(cnt or 0)})
        return r4

    if canon == "Rack/location":
        q = (
            select(Location.id, Location.name, func.count(Rack.id))
            .select_from(Rack)
            .join(
                Location,
                and_(
                    Rack.locationId == Location.id,
                    Location.organizationId == organization_id,
                    Location.deletedAt.is_(None),
                ),
            )
            .where(Rack.organizationId == organization_id, Rack.deletedAt.is_(None))
            .group_by(Location.id, Location.name)
            .order_by(func.count(Rack.id).desc())
            .limit(CATALOG_MAX_BREAKDOWN)
        )
        rows = db.execute(q).all()
        return [
            {"label": str(ln or ""), "id": str(lid), "count": int(n or 0)}
            for lid, ln, n in rows
        ]

    return f"Unimplemented: {canon!r}."


def _canonical_query_label(raw: str) -> str:
    q = (raw or "").strip()
    if not q:
        return q
    return next((c for c in CATALOG_QUERY_SPECS if c.lower() == q.lower()), None) or normalize_catalog_query_spec(q) or q


def catalog_query_json(
    db: Session,
    organization_id: uuid.UUID,
    query: str,
    legacy_group_by: str | None = None,
) -> str:
    result = run_catalog_aggregation(db, organization_id, query)
    if isinstance(result, str) and "Unknown query" in result:
        return json.dumps(
            {
                "error": result,
                "readOnly": True,
                "allowedQueries": CATALOG_QUERY_SPECS,
            }
        )
    if isinstance(result, str):
        return json.dumps({"error": result, "readOnly": True})
    n = len(result)
    body: dict[str, Any] = {
        "query": _canonical_query_label(query),
        "rows": result,
        "truncated": n >= CATALOG_MAX_BREAKDOWN,
        "rowCount": n,
        "readOnly": True,
        "note": (
            "Composed aggregate: non-deleted org rows, validated server-side. `Circuit/location` counts each distinct "
            "circuit at every site with a circuit termination. Use for tables and `chart` in Markdown. "
            "For multi-step answers, call other read tools, then merge results; do not invent numbers."
        ),
    }
    if legacy_group_by is not None:
        body["groupBy"] = legacy_group_by
    return json.dumps(body)
