"""Composable **row-list** reads for the copilot (validated `query` ids; same pattern as `catalog_breakdown`).

Add new list patterns by extending `CATALOG_LIST_QUERY_SPECS` and a branch in `catalog_list_json` — not new top-level tool names.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy import and_, exists, func, select
from sqlalchemy.orm import Session

from nims.models_generated import Device, Interface, Location, Rack

CATALOG_LIST_MAX_ROWS = 200

# Composable list ids: BaseEntity/semantic_filter (add new entries here; wire SQL in catalog_list_json).
CATALOG_LIST_QUERY_SPECS: list[str] = [
    "Device/without_interfaces",
]

_PAIR_ALIASES: dict[str, str] = {
    "device/without_interfaces": "Device/without_interfaces",
    "device/no_interfaces": "Device/without_interfaces",
    "device/withoutinterface": "Device/without_interfaces",
}


def normalize_catalog_list_query(raw: str) -> str | None:
    t0 = (raw or "").strip()
    if not t0:
        return None
    for s in CATALOG_LIST_QUERY_SPECS:
        if s.lower() == t0.lower():
            return s
    t = t0.replace("::", "/").replace(".", "/")
    parts = [p for p in t.split("/") if p.strip()]
    if len(parts) >= 2:
        a, b = parts[0].strip().lower(), parts[1].strip().lower()
        key = f"{a}/{b}"
        if key in _PAIR_ALIASES:
            return _PAIR_ALIASES[key]
        for s in CATALOG_LIST_QUERY_SPECS:
            if s.lower() == key:
                return s
    return None


def _devices_without_interfaces_where(organization_id: uuid.UUID) -> Any:
    return and_(
        Device.organizationId == organization_id,
        Device.deletedAt.is_(None),
        ~exists(
            select(1)
            .select_from(Interface)
            .where(
                Interface.deviceId == Device.id,
                Interface.deletedAt.is_(None),
            )
        ),
    )


def _json_device_without_interfaces(
    db: Session,
    organization_id: uuid.UUID,
    limit: int,
) -> dict[str, Any]:
    lim = max(1, min(int(limit or 100), CATALOG_LIST_MAX_ROWS))
    total = int(
        db.execute(
            select(func.count())
            .select_from(Device)
            .where(_devices_without_interfaces_where(organization_id))
        ).scalar_one()
        or 0
    )
    q = (
        select(
            Device.id,
            Device.name,
            Device.status,
            Location.id,
            Location.name,
        )
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
        .where(_devices_without_interfaces_where(organization_id))
        .order_by(Device.name.asc())
        .limit(lim)
    )
    rows = db.execute(q).all()
    out: list[dict[str, Any]] = []
    for did, dname, dst, loc_id, loc_name in rows:
        st = dst.value if hasattr(dst, "value") else str(dst)
        out.append(
            {
                "id": str(did),
                "name": str(dname or ""),
                "status": str(st),
                "locationId": str(loc_id) if loc_id is not None else None,
                "locationName": (
                    str(loc_name)
                    if loc_id is not None
                    else "Unplaced (no rack or unknown location)"
                ),
            }
        )
    return {
        "readOnly": True,
        "note": (
            "Devices with **no non-deleted `Interface`** rows. `locationName` comes from rack/location when resolvable. "
            "Render as a Markdown table; `totalCount` may exceed `rows` when `truncated` is true."
        ),
        "totalCount": total,
        "rowCount": len(out),
        "truncated": total > len(out),
        "maxReturned": CATALOG_LIST_MAX_ROWS,
        "rows": out,
    }


def catalog_list_json(
    db: Session,
    organization_id: uuid.UUID,
    query: str,
    limit: int = 100,
) -> str:
    spec = normalize_catalog_list_query(query)
    if not spec:
        return json.dumps(
            {
                "error": f"Unknown list query: {query!r}.",
                "readOnly": True,
                "allowedQueries": CATALOG_LIST_QUERY_SPECS,
            }
        )
    if spec == "Device/without_interfaces":
        body = _json_device_without_interfaces(db, organization_id, limit)
        body["query"] = spec
        return json.dumps(body)
    return json.dumps({"error": f"Unimplemented list query: {spec!r}.", "readOnly": True})
