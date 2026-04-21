"""Batch load and persist ResourceExtension rows (custom template attributes per object)."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import and_, delete, select
from sqlalchemy.orm import Session

from nims.models_generated import ResourceExtension
from nims.timeutil import utc_now


def extension_map(
    db: Session,
    organization_id: uuid.UUID,
    resource_type: str,
    resource_ids: list[uuid.UUID],
) -> dict[str, dict[str, Any]]:
    """Map resource id (str) -> { templateId, customAttributes }."""
    if not resource_ids:
        return {}
    rows = (
        db.execute(
            select(ResourceExtension).where(
                and_(
                    ResourceExtension.organizationId == organization_id,
                    ResourceExtension.resourceType == resource_type,
                    ResourceExtension.resourceId.in_(resource_ids),
                ),
            ),
        )
        .scalars()
        .all()
    )
    out: dict[str, dict[str, Any]] = {}
    for r in rows:
        data = r.data if isinstance(r.data, dict) else {}
        out[str(r.resourceId)] = {
            "templateId": str(r.templateId) if r.templateId else None,
            "customAttributes": data,
        }
    return out


def merge_extension(
    item: dict[str, Any],
    ext: dict[str, Any] | None,
) -> dict[str, Any]:
    if not ext:
        item["templateId"] = None
        item["customAttributes"] = {}
        return item
    item["templateId"] = ext.get("templateId")
    item["customAttributes"] = ext.get("customAttributes") or {}
    return item


def upsert_extension(
    db: Session,
    *,
    organization_id: uuid.UUID,
    resource_type: str,
    resource_id: uuid.UUID,
    template_id: uuid.UUID | None,
    data: dict[str, Any] | None,
) -> None:
    now = utc_now()
    existing = db.execute(
        select(ResourceExtension).where(
            and_(
                ResourceExtension.organizationId == organization_id,
                ResourceExtension.resourceType == resource_type,
                ResourceExtension.resourceId == resource_id,
            ),
        ),
    ).scalar_one_or_none()
    payload = dict(data or {})
    if existing is None:
        db.add(
            ResourceExtension(
                id=uuid.uuid4(),
                organizationId=organization_id,
                resourceType=resource_type,
                resourceId=resource_id,
                templateId=template_id,
                data=payload,
                createdAt=now,
                updatedAt=now,
            ),
        )
    else:
        existing.templateId = template_id
        existing.data = payload
        existing.updatedAt = now


def delete_extension_for_resource(
    db: Session,
    organization_id: uuid.UUID,
    resource_type: str,
    resource_id: uuid.UUID,
) -> None:
    db.execute(
        delete(ResourceExtension).where(
            and_(
                ResourceExtension.organizationId == organization_id,
                ResourceExtension.resourceType == resource_type,
                ResourceExtension.resourceId == resource_id,
            ),
        ),
    )
