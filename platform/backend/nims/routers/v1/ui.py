"""UI extensibility: static page registry and per-org widget placements (Phase 0–1)."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from nims.auth_context import AuthContext
from nims.deps import get_auth, get_db, require_auth_ctx
from nims.models_generated import Apitokenrole, PluginPlacement, User

router = APIRouter(tags=["ui"])

# Core routes only; plugin apps can extend the registry in a later phase.
_PAGE_REGISTRY: dict[str, Any] = {
    "version": 1,
    "pages": [
        {
            "pageId": "inventory.objectView",
            "routePattern": "/o/:resourceType/:resourceId",
            "contextSchema": {
                "type": "object",
                "description": "Object detail / graph view. Macros may use page, resource, user, organization.",
                "properties": {
                    "pageId": {"const": "inventory.objectView"},
                    "page": {
                        "type": "object",
                        "properties": {
                            "params": {"type": "object"},
                            "resourceType": {"type": "string"},
                            "resourceId": {"type": "string"},
                        },
                    },
                    "resource": {"type": ["object", "null"]},
                },
            },
        },
    ],
}


def _matches_filters(row: PluginPlacement, resource_type: str | None) -> bool:
    f = row.filters
    if not f or not isinstance(f, dict):
        return True
    rts = f.get("resourceTypes")
    if rts is None or rts is False:
        return True
    if not isinstance(rts, list) or not rts:
        return True
    if not resource_type:
        return False
    return resource_type in rts


def _user_meets_required_permissions(roles: set[str], perms: Any) -> bool:
    if perms is None or perms is False:
        return True
    if not isinstance(perms, list) or not perms:
        return True
    for p in perms:
        if not isinstance(p, str):
            continue
        if p == "READ" and not (roles & {"READ", "WRITE", "ADMIN"}):
            return False
        if p == "WRITE" and not (roles & {"WRITE", "ADMIN"}):
            return False
        if p == "ADMIN" and "ADMIN" not in roles:
            return False
    return True


@router.get("/ui/page-registry")
def get_page_registry(
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, Any]:
    """Returns stable pageIds and route metadata for the web shell. Authenticated (session or API token)."""
    require_auth_ctx(auth)
    return _PAGE_REGISTRY


@router.get("/ui/placements")
def list_placements(
    page_id: str = Query(..., min_length=1, alias="pageId"),
    resource_type: str | None = Query(default=None, alias="resourceType"),
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, list[dict[str, Any]]]:
    """List enabled widget placements for the current organization and page."""
    ctx = require_auth_ctx(auth)
    if ctx.user:
        u = db.execute(select(User).where(User.id == uuid.UUID(str(ctx.user.id)))).scalar_one_or_none()
        role: Apitokenrole = u.role if u is not None else ctx.role
    else:
        role = ctx.role
    user_roles: set[str] = {role.value} if isinstance(role, Apitokenrole) else {str(role)}

    rows = (
        db.execute(
            select(PluginPlacement)
            .where(PluginPlacement.organizationId == ctx.organization.id)
            .where(PluginPlacement.pageId == page_id)
            .where(PluginPlacement.enabled.is_(True))
            .order_by(PluginPlacement.priority.desc(), PluginPlacement.id.asc())
            .options(
                joinedload(PluginPlacement.PluginRegistration_),
            ),
        )
        .scalars()
        .all()
    )

    items: list[dict[str, Any]] = []
    for r in rows:
        reg = r.PluginRegistration_
        if reg is not None and not reg.enabled:
            continue
        if not _matches_filters(r, resource_type):
            continue
        if not _user_meets_required_permissions(user_roles, r.requiredPermissions):
            continue
        items.append(
            {
                "id": str(r.id),
                "pageId": r.pageId,
                "slot": r.slot,
                "widgetKey": r.widgetKey,
                "priority": r.priority,
                "macroBindings": r.macroBindings if isinstance(r.macroBindings, dict) else {},
                "filters": r.filters,
                "requiredPermissions": r.requiredPermissions,
                "pluginPackageName": reg.packageName if reg is not None else None,
            }
        )
    return {"items": items}
