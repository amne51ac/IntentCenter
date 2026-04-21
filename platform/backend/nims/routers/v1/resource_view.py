"""Combined item payload + relationship graph for the object view page."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from nims.auth_context import AuthContext
from nims.deps import get_auth, get_db, require_auth_ctx
from nims.services.device_hardware import build_device_hardware_tree
from nims.services.resource_item import load_resource_item
from nims.services.resource_relationships import build_relationship_graph

router = APIRouter(tags=["resource-view"])


@router.get("/resource-view/{resource_type}/{resource_id}")
def get_resource_view(
    resource_type: str,
    resource_id: uuid.UUID,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, Any]:
    ctx = require_auth_ctx(auth)
    oid = ctx.organization.id
    rt = resource_type.strip()
    if rt == "Service":
        rt = "ServiceInstance"

    item = load_resource_item(db, oid, rt, resource_id)
    graph = build_relationship_graph(db, oid, rt, resource_id)

    if item is None and graph is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Object not found")

    if item is None and graph is not None:
        root = graph["root"]
        item = {"id": root["id"], "label": root.get("label")}
        if root.get("meta"):
            item["meta"] = root["meta"]

    hardware = None
    if rt == "Device" and item is not None:
        hardware = build_device_hardware_tree(db, oid, resource_id)

    return {"item": item, "graph": graph, "hardware": hardware}
