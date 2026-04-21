"""List endpoints for extended catalog resource types."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from nims.auth_context import AuthContext, require_write
from nims.deps import get_auth, get_db, require_auth_ctx
from nims.serialize import columns_dict
from nims.services.catalog_io import CATALOG_TYPES, fetch_catalog_row_for_org, list_catalog_items, patch_catalog_row

router = APIRouter(tags=["catalog"])


@router.get("/catalog/{resource_type}/items")
def catalog_items(
    resource_type: str,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, list[dict[str, Any]]]:
    ctx = require_auth_ctx(auth)
    rt = resource_type.strip()
    if rt not in CATALOG_TYPES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown catalog type: {rt}")
    try:
        items = list_catalog_items(db, ctx.organization.id, rt)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    return {"items": items}


@router.get("/catalog/{resource_type}/items/{item_id}")
def get_catalog_item(
    resource_type: str,
    item_id: uuid.UUID,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, Any]:
    ctx = require_auth_ctx(auth)
    rt = resource_type.strip()
    if rt not in CATALOG_TYPES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown catalog type: {rt}")
    inst = fetch_catalog_row_for_org(db, ctx.organization.id, rt, item_id)
    if inst is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return {"item": columns_dict(inst)}


@router.patch("/catalog/{resource_type}/items/{item_id}")
def patch_catalog_item(
    resource_type: str,
    item_id: uuid.UUID,
    body: dict[str, Any],
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, Any]:
    ctx = require_write(require_auth_ctx(auth))
    rt = resource_type.strip()
    if rt not in CATALOG_TYPES:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Unknown catalog type: {rt}")
    if rt == "Tenant":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant row is not editable via catalog")
    try:
        return {"item": patch_catalog_row(db, ctx, rt, item_id, body)}
    except ValueError as e:
        if str(e) == "not found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found") from e
        raise HTTPException(status_code=400, detail=str(e)) from e
