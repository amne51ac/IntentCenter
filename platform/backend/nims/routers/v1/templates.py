"""CRUD for ObjectTemplate (forms + custom fields) per tenant."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from nims.auth_context import AuthContext, auth_actor_from_context, require_write
from nims.crypto_util import new_correlation_id
from nims.deps import get_auth, get_db, require_auth_ctx
from nims.models_generated import ObjectTemplate
from nims.serialize import columns_dict
from nims.services.audit import record_audit
from nims.template_defaults import BASE_TEMPLATE_DEFINITIONS, SUPPORTED_RESOURCE_TYPES
from nims.timeutil import utc_now

router = APIRouter(tags=["templates"])


def _serialize_template(t: ObjectTemplate) -> dict[str, Any]:
    out = columns_dict(t)
    return out


class TemplateCreate(BaseModel):
    resourceType: str = Field(min_length=1)
    name: str = Field(min_length=1)
    slug: str = Field(min_length=1, pattern=r"^[a-z0-9][a-z0-9_-]*$")
    description: str | None = None
    definition: dict[str, Any]
    isDefault: bool | None = False


class TemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    description: str | None = None
    definition: dict[str, Any] | None = None
    isDefault: bool | None = None


@router.get("/templates/resource-types")
def list_resource_types(
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, list[str]]:
    require_auth_ctx(auth)
    return {"items": list(SUPPORTED_RESOURCE_TYPES)}


@router.get("/templates")
def list_templates(
    resourceType: str | None = None,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, list[dict[str, Any]]]:
    ctx = require_auth_ctx(auth)
    q = select(ObjectTemplate).where(ObjectTemplate.organizationId == ctx.organization.id)
    if resourceType:
        q = q.where(ObjectTemplate.resourceType == resourceType)
    q = q.order_by(ObjectTemplate.resourceType.asc(), ObjectTemplate.name.asc())
    items = db.execute(q).scalars().all()
    return {"items": [_serialize_template(i) for i in items]}


@router.get("/templates/{template_id}")
def get_template(
    template_id: uuid.UUID,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, dict[str, Any]]:
    ctx = require_auth_ctx(auth)
    t = db.execute(
        select(ObjectTemplate).where(
            and_(ObjectTemplate.id == template_id, ObjectTemplate.organizationId == ctx.organization.id),
        ),
    ).scalar_one_or_none()
    if t is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    return {"item": _serialize_template(t)}


def _clear_default_for_type(db: Session, organization_id: uuid.UUID, resource_type: str) -> None:
    for row in db.execute(
        select(ObjectTemplate).where(
            and_(
                ObjectTemplate.organizationId == organization_id,
                ObjectTemplate.resourceType == resource_type,
                ObjectTemplate.isDefault.is_(True),
            ),
        ),
    ).scalars():
        row.isDefault = False


@router.post("/templates")
def create_template(
    body: TemplateCreate,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, Any]:
    ctx = require_write(require_auth_ctx(auth))
    if body.resourceType not in BASE_TEMPLATE_DEFINITIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported resourceType: {body.resourceType}")
    clash = db.execute(
        select(ObjectTemplate).where(
            and_(
                ObjectTemplate.organizationId == ctx.organization.id,
                ObjectTemplate.resourceType == body.resourceType,
                ObjectTemplate.slug == body.slug,
            ),
        ),
    ).scalar_one_or_none()
    if clash is not None:
        raise HTTPException(status_code=409, detail="slug already exists for this resource type")
    correlation_id = new_correlation_id()
    now = utc_now()
    if body.isDefault:
        _clear_default_for_type(db, ctx.organization.id, body.resourceType)
    created = ObjectTemplate(
        id=uuid.uuid4(),
        organizationId=ctx.organization.id,
        resourceType=body.resourceType,
        name=body.name,
        slug=body.slug,
        description=body.description,
        isSystem=False,
        isDefault=bool(body.isDefault),
        definition=body.definition,
        createdAt=now,
        updatedAt=now,
    )
    db.add(created)
    db.flush()
    record_audit(
        db,
        organization_id=ctx.organization.id,
        actor=auth_actor_from_context(ctx),
        action="create",
        resource_type="ObjectTemplate",
        resource_id=str(created.id),
        correlation_id=correlation_id,
        after=columns_dict(created),
    )
    db.commit()
    db.refresh(created)
    return {"item": _serialize_template(created), "correlationId": correlation_id}


@router.patch("/templates/{template_id}")
def update_template(
    template_id: uuid.UUID,
    body: TemplateUpdate,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, Any]:
    ctx = require_write(require_auth_ctx(auth))
    t = db.execute(
        select(ObjectTemplate).where(
            and_(ObjectTemplate.id == template_id, ObjectTemplate.organizationId == ctx.organization.id),
        ),
    ).scalar_one_or_none()
    if t is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    if t.isSystem and body.definition is not None:
        # Allow editing definition of system template for flexibility; name/slug locked
        pass
    correlation_id = new_correlation_id()
    before = columns_dict(t)
    if body.name is not None:
        t.name = body.name
    if body.description is not None:
        t.description = body.description
    if body.definition is not None:
        t.definition = body.definition
    if body.isDefault is True:
        _clear_default_for_type(db, ctx.organization.id, t.resourceType)
        t.isDefault = True
    elif body.isDefault is False:
        t.isDefault = False
    t.updatedAt = utc_now()
    record_audit(
        db,
        organization_id=ctx.organization.id,
        actor=auth_actor_from_context(ctx),
        action="update",
        resource_type="ObjectTemplate",
        resource_id=str(t.id),
        correlation_id=correlation_id,
        before=before,
        after=columns_dict(t),
    )
    db.commit()
    db.refresh(t)
    return {"item": _serialize_template(t), "correlationId": correlation_id}


@router.post("/templates/{template_id}/set-default")
def set_default_template(
    template_id: uuid.UUID,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, Any]:
    ctx = require_write(require_auth_ctx(auth))
    t = db.execute(
        select(ObjectTemplate).where(
            and_(ObjectTemplate.id == template_id, ObjectTemplate.organizationId == ctx.organization.id),
        ),
    ).scalar_one_or_none()
    if t is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    correlation_id = new_correlation_id()
    _clear_default_for_type(db, ctx.organization.id, t.resourceType)
    t.isDefault = True
    t.updatedAt = utc_now()
    record_audit(
        db,
        organization_id=ctx.organization.id,
        actor=auth_actor_from_context(ctx),
        action="set_default",
        resource_type="ObjectTemplate",
        resource_id=str(t.id),
        correlation_id=correlation_id,
        after=columns_dict(t),
    )
    db.commit()
    return {"item": _serialize_template(t), "correlationId": correlation_id}


@router.delete("/templates/{template_id}")
def delete_template(
    template_id: uuid.UUID,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, Any]:
    ctx = require_write(require_auth_ctx(auth))
    t = db.execute(
        select(ObjectTemplate).where(
            and_(ObjectTemplate.id == template_id, ObjectTemplate.organizationId == ctx.organization.id),
        ),
    ).scalar_one_or_none()
    if t is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
    if t.isSystem:
        raise HTTPException(status_code=400, detail="System templates cannot be deleted")
    correlation_id = new_correlation_id()
    before = columns_dict(t)
    db.delete(t)
    record_audit(
        db,
        organization_id=ctx.organization.id,
        actor=auth_actor_from_context(ctx),
        action="delete",
        resource_type="ObjectTemplate",
        resource_id=str(template_id),
        correlation_id=correlation_id,
        before=before,
    )
    db.commit()
    return {"ok": True, "correlationId": correlation_id}
