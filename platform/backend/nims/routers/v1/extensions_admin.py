"""Admin-only: plugin UI placements (org-scoped, multi-tenant)."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, select
from sqlalchemy.orm import Session, joinedload

from nims.auth_context import AuthContext, require_admin
from nims.deps import get_auth, get_db, require_auth_ctx
from nims.models_generated import PluginPlacement, PluginRegistration
from nims.timeutil import utc_now

router = APIRouter(prefix="/admin", tags=["extensions-admin"])


def _assert_plugin_org(
    db: Session,
    organization_id: uuid.UUID,
    plugin_registration_id: uuid.UUID,
) -> PluginRegistration:
    row = db.execute(
        select(PluginRegistration).where(
            and_(
                PluginRegistration.id == plugin_registration_id,
                PluginRegistration.organizationId == organization_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plugin registration not found for this organization",
        )
    return row


class PlacementCreate(BaseModel):
    pluginRegistrationId: uuid.UUID
    pageId: str = Field(min_length=1)
    slot: str = Field(min_length=1)
    widgetKey: str = Field(min_length=1)
    priority: int = 0
    enabled: bool = True
    filters: dict[str, Any] | None = None
    macroBindings: dict[str, Any] | None = None
    requiredPermissions: list[str] | None = None


class PlacementUpdate(BaseModel):
    pageId: str | None = Field(default=None, min_length=1)
    slot: str | None = Field(default=None, min_length=1)
    widgetKey: str | None = Field(default=None, min_length=1)
    priority: int | None = None
    enabled: bool | None = None
    filters: dict[str, Any] | None = None
    macroBindings: dict[str, Any] | None = None
    requiredPermissions: list[str] | None = None


def _serialize(p: PluginPlacement, pkg: str | None = None) -> dict[str, object]:
    out: dict[str, object] = {
        "id": str(p.id),
        "organizationId": str(p.organizationId),
        "pluginRegistrationId": str(p.pluginRegistrationId),
        "pageId": p.pageId,
        "slot": p.slot,
        "widgetKey": p.widgetKey,
        "priority": p.priority,
        "enabled": p.enabled,
        "filters": p.filters,
        "macroBindings": p.macroBindings,
        "requiredPermissions": p.requiredPermissions,
    }
    if pkg is not None:
        out["packageName"] = pkg
    return out


@router.get("/plugin-placements")
def list_placements(
    page_id: str | None = Query(default=None, alias="pageId"),
    include_disabled: bool = Query(default=True, alias="includeDisabled"),
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, list[dict[str, object]]]:
    ctx = require_admin(require_auth_ctx(auth))
    q = select(PluginPlacement).where(PluginPlacement.organizationId == ctx.organization.id)
    if page_id:
        q = q.where(PluginPlacement.pageId == page_id)
    q = q.options(joinedload(PluginPlacement.PluginRegistration_)).order_by(
        PluginPlacement.pageId.asc(), PluginPlacement.slot.asc(), PluginPlacement.priority.desc()
    )
    rows = db.execute(q).unique().scalars().all()
    items: list[dict[str, object]] = []
    for p in rows:
        if not include_disabled and not p.enabled:
            continue
        reg = p.PluginRegistration_
        if reg is not None and reg.organizationId != ctx.organization.id:
            continue
        items.append(_serialize(p, pkg=reg.packageName if reg is not None else None))
    return {"items": items}


@router.post("/plugin-placements", status_code=status.HTTP_201_CREATED)
def create_placement(
    body: PlacementCreate,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_admin(require_auth_ctx(auth))
    _assert_plugin_org(db, ctx.organization.id, body.pluginRegistrationId)
    now = utc_now()
    row = PluginPlacement(
        id=uuid.uuid4(),
        organizationId=ctx.organization.id,
        pluginRegistrationId=body.pluginRegistrationId,
        pageId=body.pageId,
        slot=body.slot,
        widgetKey=body.widgetKey,
        priority=body.priority,
        enabled=body.enabled,
        filters=body.filters,
        macroBindings=body.macroBindings,
        requiredPermissions=body.requiredPermissions,
        createdAt=now,
        updatedAt=now,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    reg = db.get(PluginRegistration, row.pluginRegistrationId)
    return {
        "item": _serialize(row, pkg=reg.packageName if reg is not None else None),
    }


@router.patch("/plugin-placements/{placement_id}")
def patch_placement(
    placement_id: uuid.UUID,
    body: PlacementUpdate,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_admin(require_auth_ctx(auth))
    p = (
        db.execute(
            select(PluginPlacement)
            .where(
                and_(
                    PluginPlacement.id == placement_id,
                    PluginPlacement.organizationId == ctx.organization.id,
                )
            )
            .options(joinedload(PluginPlacement.PluginRegistration_)),
        )
        .unique()
        .scalar_one_or_none()
    )
    if p is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Placement not found")
    raw = body.model_dump(exclude_unset=True)
    for k, v in raw.items():
        if k in ("pageId", "slot", "widgetKey", "priority", "enabled", "filters", "macroBindings", "requiredPermissions"):
            setattr(p, k, v)
    p.updatedAt = utc_now()
    db.commit()
    db.refresh(p)
    reg = p.PluginRegistration_
    return {"item": _serialize(p, pkg=reg.packageName if reg is not None else None)}


@router.delete("/plugin-placements/{placement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_placement(
    placement_id: uuid.UUID,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> Response:
    ctx = require_admin(require_auth_ctx(auth))
    p = (
        db.execute(
            select(PluginPlacement).where(
                and_(
                    PluginPlacement.id == placement_id,
                    PluginPlacement.organizationId == ctx.organization.id,
                )
            )
        )
        .scalar_one_or_none()
    )
    if p is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Placement not found")
    db.delete(p)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
