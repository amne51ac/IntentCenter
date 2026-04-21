import uuid
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import select
from sqlalchemy.orm import Session

from nims.auth_context import AuthContext, require_admin, require_write
from nims.crypto_util import generate_raw_token, hash_token
from nims.deps import get_auth, get_db, require_auth_ctx
from nims.models_generated import (
    ApiToken,
    Apitokenrole,
    AuditEvent,
    PluginRegistration,
    User,
    Webhookevent,
    WebhookSubscription,
)
from nims.serialize import serialize_audit_event, serialize_plugin
from nims.services.extensions import extension_map, upsert_extension
from nims.timeutil import utc_now

router = APIRouter(tags=["core"])


class TokenCreateBody(BaseModel):
    name: str = Field(min_length=1)
    role: Literal["READ", "WRITE", "ADMIN"] = "WRITE"


class WebhookCreateBody(BaseModel):
    name: str = Field(min_length=1)
    url: HttpUrl
    secret: str | None = None
    resourceTypes: list[str] = Field(default_factory=list)
    events: list[Literal["CREATE", "UPDATE", "DELETE"]] = Field(min_length=1)


class MePatchBody(BaseModel):
    preferences: dict[str, Any] | None = None


@router.get("/me")
def get_me(
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    if auth is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    a = auth
    organization = {
        "id": str(a.organization.id),
        "name": a.organization.name,
        "slug": a.organization.slug,
    }
    if a.user:
        prefs: dict[str, Any] = {}
        urow = db.execute(select(User).where(User.id == uuid.UUID(str(a.user.id)))).scalar_one_or_none()
        if urow is not None and isinstance(urow.preferences, dict):
            prefs = urow.preferences
        return {
            "organization": organization,
            "preferences": prefs,
            "auth": {
                "mode": "user",
                "user": {
                    "id": a.user.id,
                    "email": a.user.email,
                    "displayName": a.user.displayName,
                    "role": a.role.value,
                    "authProvider": a.user.authProvider,
                },
            },
        }
    if a.api_token:
        return {
            "organization": organization,
            "preferences": {},
            "auth": {
                "mode": "api_token",
                "token": {
                    "id": str(a.api_token.id),
                    "name": a.api_token.name,
                    "role": a.role.value,
                },
            },
        }
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")


@router.patch("/me")
def patch_me(
    body: MePatchBody,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_auth_ctx(auth)
    if ctx.user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Interactive session required")
    user = db.execute(select(User).where(User.id == uuid.UUID(str(ctx.user.id)))).scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if body.preferences is not None:
        cur = dict(user.preferences) if isinstance(user.preferences, dict) else {}
        cur.update(body.preferences)
        user.preferences = cur
        user.updatedAt = utc_now()
    db.commit()
    return get_me(db, auth)


@router.post("/tokens")
def post_tokens(
    body: TokenCreateBody,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_admin(require_auth_ctx(auth))
    raw = generate_raw_token()
    token_hash = hash_token(raw)
    role = Apitokenrole(body.role)
    created = ApiToken(
        id=uuid.uuid4(),
        organizationId=ctx.organization.id,
        name=body.name,
        tokenHash=token_hash,
        role=role,
    )
    db.add(created)
    db.commit()
    db.refresh(created)
    return {
        "id": str(created.id),
        "name": created.name,
        "role": created.role.value,
        "token": raw,
        "message": "Store this token securely; it will not be shown again.",
    }


@router.post("/webhooks")
def post_webhooks(
    body: WebhookCreateBody,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_write(require_auth_ctx(auth))
    ev_map = {
        "CREATE": Webhookevent.CREATE,
        "UPDATE": Webhookevent.UPDATE,
        "DELETE": Webhookevent.DELETE,
    }
    evs = [ev_map[e] for e in body.events]
    from nims.timeutil import utc_now

    now = utc_now()
    created = WebhookSubscription(
        id=uuid.uuid4(),
        organizationId=ctx.organization.id,
        name=body.name,
        url=str(body.url),
        secret=body.secret,
        resourceTypes=body.resourceTypes,
        events=evs,
        createdAt=now,
        updatedAt=now,
    )
    db.add(created)
    db.commit()
    db.refresh(created)
    return {"id": str(created.id), "name": created.name, "url": created.url}


@router.get("/audit-events")
def get_audit_events(
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
    limit: int = Query(default=50, ge=1, le=100),
) -> dict[str, list[dict[str, object]]]:
    ctx = require_auth_ctx(auth)
    take = min(100, limit)
    rows = (
        db.execute(
            select(AuditEvent)
            .where(AuditEvent.organizationId == ctx.organization.id)
            .order_by(AuditEvent.createdAt.desc())
            .limit(take)
        )
        .scalars()
        .all()
    )
    return {"items": [serialize_audit_event(r) for r in rows]}


@router.get("/plugins")
def get_plugins(
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, list[dict[str, object]]]:
    require_auth_ctx(auth)
    items = db.execute(select(PluginRegistration).order_by(PluginRegistration.packageName.asc())).scalars().all()
    return {"items": [serialize_plugin(p) for p in items]}


class ResourceExtensionPut(BaseModel):
    templateId: uuid.UUID | None = None
    customAttributes: dict[str, Any] | None = None


@router.get("/resource-extensions/batch")
def get_resource_extensions_batch(
    resourceType: str = Query(..., min_length=1),
    ids: str = Query(..., description="Comma-separated resource UUIDs"),
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, dict[str, dict[str, Any]]]:
    """Return extension rows for many resources in one round-trip (template + custom JSON)."""
    ctx = require_auth_ctx(auth)
    id_list: list[uuid.UUID] = []
    for part in ids.split(","):
        p = part.strip()
        if not p:
            continue
        try:
            id_list.append(uuid.UUID(p))
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid UUID in ids: {p}") from None
    m = extension_map(db, ctx.organization.id, resourceType, id_list)
    return {"extensions": m}


@router.put("/resource-extensions/{resource_type}/{resource_id}")
def put_resource_extension(
    resource_type: str,
    resource_id: uuid.UUID,
    body: ResourceExtensionPut,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_write(require_auth_ctx(auth))
    upsert_extension(
        db,
        organization_id=ctx.organization.id,
        resource_type=resource_type,
        resource_id=resource_id,
        template_id=body.templateId,
        data=body.customAttributes,
    )
    db.commit()
    return {"ok": True}
