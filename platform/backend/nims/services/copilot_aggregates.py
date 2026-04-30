"""Read-only org-wide aggregates and hierarchy data for the AI assistant tools."""

from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from nims.models_generated import Location
from nims.services.copilot_catalog_query import (
    CATALOG_MAX_BREAKDOWN,
    CATALOG_QUERY_SPECS,
    catalog_query_json,
    legacy_device_group_to_spec,
)

# Back-compat for imports
_MAX_BREAKDOWN = CATALOG_MAX_BREAKDOWN


def location_hierarchy_json(db: Session, organization_id: uuid.UUID) -> str:
    rows = db.execute(
        select(
            Location.id,
            Location.name,
            Location.parentId,
            Location.slug,
            Location.latitude,
            Location.longitude,
        )
        .where(Location.organizationId == organization_id, Location.deletedAt.is_(None))
        .order_by(Location.name.asc())
    ).all()
    locs: list[dict[str, Any]] = []
    for rid, name, parent_id, slug, lat, lon in rows:
        has_coords = lat is not None and lon is not None
        locs.append(
            {
                "id": str(rid),
                "name": str(name),
                "parentId": str(parent_id) if parent_id is not None else None,
                "slug": str(slug) if slug is not None else "",
                "latitude": float(lat) if lat is not None else None,
                "longitude": float(lon) if lon is not None else None,
                "hasCoordinates": has_coords,
            }
        )
    n_coords = sum(1 for L in locs if L.get("hasCoordinates"))
    return json.dumps(
        {
            "count": len(locs),
            "locationsWithCoordinates": n_coords,
            "locations": locs,
            "note": (
                "Build a tree: roots have parentId null. Each row may include latitude/longitude (WGS84) when set in "
                "the catalog—use those for a Markdown `map` fenced block (markers with lat, lng, label). "
                "Omit or skip locations with null coordinates. This is the full org location set; read-only."
            ),
        }
    )


def device_breakdown_json(db: Session, organization_id: uuid.UUID, group_by: str) -> str:
    spec = legacy_device_group_to_spec(group_by)
    if not spec:
        return json.dumps(
            {
                "error": f"Unknown group_by: {group_by!r}.",
                "readOnly": True,
                "useCatalogBreakdown": True,
                "allowedCatalogQueries": CATALOG_QUERY_SPECS,
            }
        )
    return catalog_query_json(db, organization_id, spec, legacy_group_by=group_by.strip().lower())
