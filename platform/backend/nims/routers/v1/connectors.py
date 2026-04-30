"""Connector registrations — credentials are server-only (never in list; detail redacts for non-admins)."""

from __future__ import annotations

import json
import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, select
from sqlalchemy.orm import Session, joinedload

from nims.auth_context import AuthContext, require_admin
from nims.deps import get_auth, get_db, require_auth_ctx
from nims.models_generated import Apitokenrole, ConnectorRegistration, PluginRegistration, User
from nims.timeutil import utc_now

router = APIRouter(prefix="/connectors", tags=["connectors"])


def _plugin_for_org(
    db: Session,
    organization_id: uuid.UUID,
    plugin_id: uuid.UUID | None,
) -> PluginRegistration | None:
    if plugin_id is None:
        return None
    p = (
        db.execute(
            select(PluginRegistration).where(
                and_(
                    PluginRegistration.id == plugin_id,
                    PluginRegistration.organizationId == organization_id,
                )
            )
        )
    ).scalar_one_or_none()
    if p is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plugin not found in this organization")
    return p


def _is_admin_user(db: Session, ctx: AuthContext) -> bool:
    if ctx.api_token is not None:
        return ctx.api_token.role == Apitokenrole.ADMIN
    if ctx.user is None:
        return False
    u = (
        db.execute(
            select(User).where(
                and_(User.id == uuid.UUID(str(ctx.user.id)), User.organizationId == ctx.organization.id)
            )
        )
    ).scalar_one_or_none()
    if u is None:
        return False
    return u.role == Apitokenrole.ADMIN


def _serialize_list_row(c: ConnectorRegistration) -> dict[str, object]:
    plug = c.PluginRegistration_
    return {
        "id": str(c.id),
        "organizationId": str(c.organizationId),
        "pluginRegistrationId": str(c.pluginRegistrationId) if c.pluginRegistrationId is not None else None,
        "packageName": plug.packageName if plug is not None else None,
        "type": c.type,
        "name": c.name,
        "enabled": c.enabled,
        "settings": c.settings if isinstance(c.settings, dict) else {},
        "hasCredentials": bool(c.credentialsEnc and str(c.credentialsEnc).strip()),
        "healthStatus": c.healthStatus,
        "lastSyncAt": c.lastSyncAt.isoformat() if c.lastSyncAt is not None else None,
        "lastError": c.lastError,
        "createdAt": c.createdAt.isoformat() if c.createdAt is not None else None,
    }


def _serialize_admin_detail(c: ConnectorRegistration) -> dict[str, object]:
    out = _serialize_list_row(c)
    if c.credentialsEnc:
        try:
            out["credentials"] = json.loads(c.credentialsEnc)
        except json.JSONDecodeError:
            out["credentials"] = None
    else:
        out["credentials"] = None
    return out


class ConnectorCreate(BaseModel):
    name: str = Field(min_length=1)
    type: str = Field(min_length=1, description="e.g. webhook_outbound, http_get, generic_rest")
    pluginRegistrationId: uuid.UUID | None = None
    enabled: bool = True
    settings: dict[str, Any] = Field(default_factory=dict)
    credentials: dict[str, Any] | None = None


class ConnectorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    type: str | None = Field(default=None, min_length=1)
    pluginRegistrationId: uuid.UUID | None = None
    enabled: bool | None = None
    settings: dict[str, Any] | None = None
    credentials: dict[str, Any] | None = None


@router.get("")
def list_connectors(
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, list[dict[str, object]]]:
    ctx = require_auth_ctx(auth)
    rows = (
        db.execute(
            select(ConnectorRegistration)
            .where(ConnectorRegistration.organizationId == ctx.organization.id)
            .options(joinedload(ConnectorRegistration.PluginRegistration_))
            .order_by(ConnectorRegistration.name.asc())
        )
        .scalars()
        .unique()
        .all()
    )
    return {"items": [_serialize_list_row(c) for c in rows]}


@router.get("/{connector_id}")
def get_connector(
    connector_id: uuid.UUID,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_auth_ctx(auth)
    c = (
        db.execute(
            select(ConnectorRegistration)
            .where(
                and_(
                    ConnectorRegistration.id == connector_id,
                    ConnectorRegistration.organizationId == ctx.organization.id,
                )
            )
            .options(joinedload(ConnectorRegistration.PluginRegistration_)),
        )
        .unique()
        .scalar_one_or_none()
    )
    if c is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found")
    if not _is_admin_user(db, ctx):
        return {"item": _serialize_list_row(c)}
    return {"item": _serialize_admin_detail(c)}


@router.post("", status_code=status.HTTP_201_CREATED)
def create_connector(
    body: ConnectorCreate,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_admin(require_auth_ctx(auth))
    _ = _plugin_for_org(db, ctx.organization.id, body.pluginRegistrationId) if body.pluginRegistrationId else None
    now = utc_now()
    enc: str | None
    if body.credentials is not None and len(body.credentials) > 0:
        enc = json.dumps(body.credentials, separators=(",", ":"), sort_keys=True)
    else:
        enc = None
    c = ConnectorRegistration(
        id=uuid.uuid4(),
        organizationId=ctx.organization.id,
        pluginRegistrationId=body.pluginRegistrationId,
        type=body.type,
        name=body.name,
        enabled=body.enabled,
        settings=body.settings or {},
        credentialsEnc=enc,
        healthStatus=None,
        lastError=None,
        lastSyncAt=None,
        createdAt=now,
        updatedAt=now,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    c2 = (
        db.execute(
            select(ConnectorRegistration)
            .where(ConnectorRegistration.id == c.id)
            .options(joinedload(ConnectorRegistration.PluginRegistration_)),
        )
        .unique()
        .scalar_one()
    )
    return {"item": _serialize_list_row(c2)}


@router.patch("/{connector_id}")
def update_connector(
    connector_id: uuid.UUID,
    body: ConnectorUpdate,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_admin(require_auth_ctx(auth))
    c = (
        db.execute(
            select(ConnectorRegistration).where(
                and_(
                    ConnectorRegistration.id == connector_id,
                    ConnectorRegistration.organizationId == ctx.organization.id,
                )
            )
        )
    ).scalar_one_or_none()
    if c is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found")
    if body.name is not None:
        c.name = body.name
    if body.type is not None:
        c.type = body.type
    if body.enabled is not None:
        c.enabled = body.enabled
    if body.settings is not None:
        c.settings = body.settings
    if body.pluginRegistrationId is not None:
        _ = _plugin_for_org(db, ctx.organization.id, body.pluginRegistrationId)
        c.pluginRegistrationId = body.pluginRegistrationId
    if body.credentials is not None:
        c.credentialsEnc = (
            json.dumps(body.credentials, separators=(",", ":"), sort_keys=True)
            if len(body.credentials) > 0
            else None
        )
    c.updatedAt = utc_now()
    db.commit()
    db.refresh(c)
    c2 = (
        db.execute(
            select(ConnectorRegistration)
            .where(ConnectorRegistration.id == c.id)
            .options(joinedload(ConnectorRegistration.PluginRegistration_)),
        )
        .unique()
        .scalar_one()
    )
    return {"item": _serialize_list_row(c2)}


@router.delete("/{connector_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_connector(
    connector_id: uuid.UUID,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> Response:
    ctx = require_admin(require_auth_ctx(auth))
    c = (
        db.execute(
            select(ConnectorRegistration).where(
                and_(
                    ConnectorRegistration.id == connector_id,
                    ConnectorRegistration.organizationId == ctx.organization.id,
                )
            )
        )
    ).scalar_one_or_none()
    if c is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Connector not found")
    db.delete(c)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
