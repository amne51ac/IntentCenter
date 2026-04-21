"""Cross-resource search (name / slug / key fields)."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from nims.auth_context import AuthContext
from nims.deps import get_auth, get_db, require_auth_ctx
from nims.models_generated import (
    Circuit,
    Device,
    IpAddress,
    Location,
    Prefix,
    Provider,
    Rack,
    Vrf,
)

router = APIRouter(tags=["search"])


def _path_for(rt: str, rid: str) -> str:
    """Open object view (details + relationships), not the edit form."""
    return f"/o/{rt}/{rid}"


@router.get("/search")
def global_search(
    q: str = Query("", min_length=0, max_length=200),
    limit: int = Query(15, ge=1, le=50),
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, list[dict[str, Any]]]:
    ctx = require_auth_ctx(auth)
    term = (q or "").strip()
    if not term:
        return {"items": []}
    pat = f"%{term.replace('%', '').replace('_', '')}%"
    oid = ctx.organization.id
    items: list[dict[str, Any]] = []

    def add(rt: str, rid: uuid.UUID, label: str, sub: str | None = None) -> None:
        if len(items) >= limit:
            return
        d: dict[str, Any] = {
            "resourceType": rt,
            "id": str(rid),
            "label": label,
            "path": _path_for(rt, str(rid)),
        }
        if sub:
            d["subtitle"] = sub
        items.append(d)

    locs = (
        db.execute(
            select(Location).where(
                and_(
                    Location.organizationId == oid,
                    Location.deletedAt.is_(None),
                    or_(Location.name.ilike(pat), Location.slug.ilike(pat)),
                ),
            ).limit(8),
        )
        .scalars()
        .all()
    )
    for loc in locs:
        add("Location", loc.id, loc.name, loc.slug)

    racks = (
        db.execute(
            select(Rack).where(
                and_(
                    Rack.organizationId == oid,
                    Rack.deletedAt.is_(None),
                    Rack.name.ilike(pat),
                ),
            ).limit(8),
        )
        .scalars()
        .all()
    )
    for r in racks:
        add("Rack", r.id, r.name)

    devs = (
        db.execute(
            select(Device).where(
                and_(
                    Device.organizationId == oid,
                    Device.deletedAt.is_(None),
                    or_(Device.name.ilike(pat), Device.serialNumber.ilike(pat)),
                ),
            ).limit(8),
        )
        .scalars()
        .all()
    )
    for d in devs:
        add("Device", d.id, d.name, d.serialNumber)

    vrfs = (
        db.execute(
            select(Vrf).where(
                and_(
                    Vrf.organizationId == oid,
                    Vrf.deletedAt.is_(None),
                    or_(Vrf.name.ilike(pat), func.coalesce(Vrf.rd, "").ilike(pat)),
                ),
            ).limit(6),
        )
        .scalars()
        .all()
    )
    for v in vrfs:
        sub = v.rd or None
        add("Vrf", v.id, v.name, sub)

    prefs = (
        db.execute(
            select(Prefix).where(
                and_(
                    Prefix.organizationId == oid,
                    Prefix.deletedAt.is_(None),
                    Prefix.cidr.ilike(pat),
                ),
            ).limit(6),
        )
        .scalars()
        .all()
    )
    for p in prefs:
        add("Prefix", p.id, p.cidr)

    ips = (
        db.execute(
            select(IpAddress).where(
                and_(
                    IpAddress.organizationId == oid,
                    IpAddress.deletedAt.is_(None),
                    IpAddress.address.ilike(pat),
                ),
            ).limit(6),
        )
        .scalars()
        .all()
    )
    for ip in ips:
        add("IpAddress", ip.id, ip.address)

    provs = (
        db.execute(
            select(Provider).where(
                and_(
                    Provider.organizationId == oid,
                    Provider.deletedAt.is_(None),
                    Provider.name.ilike(pat),
                ),
            ).limit(5),
        )
        .scalars()
        .all()
    )
    for pr in provs:
        add("Provider", pr.id, pr.name)

    circs = (
        db.execute(
            select(Circuit).where(
                and_(
                    Circuit.organizationId == oid,
                    Circuit.deletedAt.is_(None),
                    Circuit.cid.ilike(pat),
                ),
            ).limit(5),
        )
        .scalars()
        .all()
    )
    for c in circs:
        add("Circuit", c.id, c.cid)

    return {"items": items[:limit]}
