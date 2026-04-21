"""Relationship graph for a single inventory object."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from nims.auth_context import AuthContext
from nims.deps import get_auth, get_db, require_auth_ctx
from nims.services.resource_relationships import build_relationship_graph

router = APIRouter(tags=["resource-graph"])


@router.get("/resource-graph/{resource_type}/{resource_id}")
def get_resource_graph(
    resource_type: str,
    resource_id: uuid.UUID,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, Any]:
    ctx = require_auth_ctx(auth)
    g = build_relationship_graph(db, ctx.organization.id, resource_type, resource_id)
    if g is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Object not found or graph not available")
    return g
