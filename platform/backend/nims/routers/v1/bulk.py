"""Bulk import/export for inventory objects (CSV / JSON). Empty export = header-only template."""

from __future__ import annotations

import csv
import io
import uuid
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import and_, select
from sqlalchemy.orm import Session, joinedload

from nims.auth_context import AuthContext, auth_actor_from_context, require_write
from nims.crypto_util import new_correlation_id
from nims.deps import get_auth, get_db, require_auth_ctx
from nims.models_generated import (
    Devicestatus,
    Device,
    Location,
    Rack,
    Vrf,
)
from nims.serialize import columns_dict, j
from nims.services.audit import record_audit
from nims.services.catalog_io import CATALOG_TYPES, catalog_export_rows, catalog_import_rows, row_for_csv
from nims.services.extensions import upsert_extension
from nims.timeutil import utc_now

router = APIRouter(tags=["bulk"])


SUPPORTED = frozenset({"Location", "Rack", "Device", "Vrf"})
ALL_BULK_TYPES = SUPPORTED | CATALOG_TYPES


def _location_template_headers() -> list[str]:
    return ["name", "slug", "locationTypeId", "parentId", "description", "templateId"]


def _rack_template_headers() -> list[str]:
    return ["name", "locationId", "uHeight", "templateId"]


def _device_template_headers() -> list[str]:
    return [
        "name",
        "deviceTypeId",
        "deviceRoleId",
        "rackId",
        "serialNumber",
        "positionU",
        "face",
        "status",
        "templateId",
    ]


def _vrf_template_headers() -> list[str]:
    return ["name", "rd"]


@router.get("/bulk/{resource_type}/export")
def bulk_export(
    resource_type: str,
    format: Literal["csv", "json"] = Query("csv"),
    template: bool = Query(False, description="If true, return headers / empty template only"),
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, Any] | dict[str, str]:
    ctx = require_auth_ctx(auth)
    rt = resource_type.strip()
    if rt not in ALL_BULK_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported resource type for bulk: {rt}")
    oid = ctx.organization.id

    if rt in CATALOG_TYPES:
        headers, rows_out = catalog_export_rows(db, oid, rt, template)
        flat_rows = [row_for_csv({h: rr.get(h) for h in headers}) for rr in rows_out]
        csv_text = _rows_to_csv(headers, flat_rows)
        items_json = [{h: j(rr.get(h)) for h in headers} for rr in rows_out]
        return _export_payload(rt, format, template, headers, items_json, csv_text)

    if rt == "Location":
        headers = _location_template_headers()
        rows_out: list[dict[str, Any]] = []
        if not template:
            locs = (
                db.execute(
                    select(Location)
                    .where(and_(Location.organizationId == oid, Location.deletedAt.is_(None)))
                    .order_by(Location.name.asc()),
                )
                .scalars()
                .all()
            )
            for loc in locs:
                d = columns_dict(loc)
                rows_out.append(
                    {
                        "name": d.get("name"),
                        "slug": d.get("slug"),
                        "locationTypeId": str(d.get("locationTypeId")),
                        "parentId": str(d["parentId"]) if d.get("parentId") else "",
                        "description": d.get("description") or "",
                        "templateId": "",
                    },
                )
        csv_text = _rows_to_csv(headers, rows_out)
        return _export_payload(rt, format, template, headers, rows_out, csv_text)

    if rt == "Rack":
        headers = _rack_template_headers()
        rows_out = []
        if not template:
            racks = (
                db.execute(
                    select(Rack).where(and_(Rack.organizationId == oid, Rack.deletedAt.is_(None))).order_by(Rack.name.asc()),
                )
                .scalars()
                .all()
            )
            for r in racks:
                d = columns_dict(r)
                rows_out.append(
                    {
                        "name": d.get("name"),
                        "locationId": str(d.get("locationId")),
                        "uHeight": d.get("uHeight"),
                        "templateId": "",
                    },
                )
        csv_text = _rows_to_csv(headers, rows_out)
        return _export_payload(rt, format, template, headers, rows_out, csv_text)

    if rt == "Device":
        headers = _device_template_headers()
        rows_out = []
        if not template:
            devs = (
                db.execute(
                    select(Device)
                    .where(and_(Device.organizationId == oid, Device.deletedAt.is_(None)))
                    .options(joinedload(Device.Rack_))
                    .order_by(Device.name.asc()),
                )
                .scalars()
                .all()
            )
            for d in devs:
                cd = columns_dict(d)
                rows_out.append(
                    {
                        "name": cd.get("name"),
                        "deviceTypeId": str(cd.get("deviceTypeId")),
                        "deviceRoleId": str(cd.get("deviceRoleId")),
                        "rackId": str(cd["rackId"]) if cd.get("rackId") else "",
                        "serialNumber": cd.get("serialNumber") or "",
                        "positionU": cd.get("positionU") if cd.get("positionU") is not None else "",
                        "face": cd.get("face") or "",
                        "status": d.status.value if hasattr(d.status, "value") else str(d.status),
                        "templateId": "",
                    },
                )
        csv_text = _rows_to_csv(headers, rows_out)
        return _export_payload(rt, format, template, headers, rows_out, csv_text)

    if rt == "Vrf":
        headers = _vrf_template_headers()
        rows_out = []
        if not template:
            vrfs = (
                db.execute(
                    select(Vrf).where(and_(Vrf.organizationId == oid, Vrf.deletedAt.is_(None))).order_by(Vrf.name.asc()),
                )
                .scalars()
                .all()
            )
            for v in vrfs:
                d = columns_dict(v)
                rows_out.append({"name": d.get("name"), "rd": d.get("rd") or ""})
        csv_text = _rows_to_csv(headers, rows_out)
        return _export_payload(rt, format, template, headers, rows_out, csv_text)

    raise HTTPException(status_code=400, detail="Unsupported")


def _rows_to_csv(headers: list[str], rows_out: list[dict[str, Any]]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=headers, extrasaction="ignore")
    w.writeheader()
    for r in rows_out:
        w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in headers})
    return buf.getvalue()


def _export_payload(
    rt: str,
    format: str,
    template: bool,
    headers: list[str],
    rows_out: list[dict[str, Any]],
    csv_text: str,
) -> dict[str, Any]:
    return {
        "resourceType": rt,
        "format": format,
        "template": template,
        "headers": headers,
        "items": rows_out,
        "csvText": csv_text,
        "filename": f"{rt.lower()}-export.csv",
    }


class BulkJsonImportBody(BaseModel):
    rows: list[dict[str, Any]] = Field(default_factory=list)
    skipErrors: bool = False


@router.post("/bulk/{resource_type}/import/json")
def bulk_import_json(
    resource_type: str,
    body: BulkJsonImportBody,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, Any]:
    ctx = require_write(require_auth_ctx(auth))
    rt = resource_type.strip()
    if rt not in ALL_BULK_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported resource type: {rt}")
    oid = ctx.organization.id
    created = 0
    errors: list[dict[str, Any]] = []
    now = utc_now()

    if rt == "Location":
        for i, row in enumerate(body.rows):
            try:
                name = str(row.get("name", "")).strip()
                slug = str(row.get("slug", "")).strip()
                lt = uuid.UUID(str(row.get("locationTypeId")))
                parent = row.get("parentId")
                parent_id = uuid.UUID(str(parent)) if parent else None
                desc = row.get("description")
                loc = Location(
                    id=uuid.uuid4(),
                    organizationId=oid,
                    name=name,
                    slug=slug,
                    locationTypeId=lt,
                    parentId=parent_id,
                    description=str(desc) if desc else None,
                    createdAt=now,
                    updatedAt=now,
                )
                db.add(loc)
                db.flush()
                tid = row.get("templateId")
                if tid:
                    upsert_extension(
                        db,
                        organization_id=oid,
                        resource_type="Location",
                        resource_id=loc.id,
                        template_id=uuid.UUID(str(tid)),
                        data={},
                    )
                record_audit(
                    db,
                    organization_id=oid,
                    actor=auth_actor_from_context(ctx),
                    action="bulk_import",
                    resource_type="Location",
                    resource_id=str(loc.id),
                    correlation_id=new_correlation_id(),
                    after=columns_dict(loc),
                )
                created += 1
            except Exception as e:  # noqa: BLE001
                db.rollback()
                errors.append({"index": i, "error": str(e)})
                if not body.skipErrors:
                    raise HTTPException(status_code=400, detail={"message": str(e), "index": i}) from e
        db.commit()
        return {"created": created, "errors": errors}

    if rt == "Rack":
        for i, row in enumerate(body.rows):
            try:
                r = Rack(
                    id=uuid.uuid4(),
                    organizationId=oid,
                    name=str(row.get("name", "")).strip(),
                    locationId=uuid.UUID(str(row.get("locationId"))),
                    uHeight=int(row.get("uHeight") or 42),
                    createdAt=now,
                    updatedAt=now,
                )
                db.add(r)
                db.flush()
                tid = row.get("templateId")
                if tid:
                    upsert_extension(
                        db,
                        organization_id=oid,
                        resource_type="Rack",
                        resource_id=r.id,
                        template_id=uuid.UUID(str(tid)),
                        data={},
                    )
                record_audit(
                    db,
                    organization_id=oid,
                    actor=auth_actor_from_context(ctx),
                    action="bulk_import",
                    resource_type="Rack",
                    resource_id=str(r.id),
                    correlation_id=new_correlation_id(),
                    after=columns_dict(r),
                )
                created += 1
            except Exception as e:  # noqa: BLE001
                db.rollback()
                errors.append({"index": i, "error": str(e)})
                if not body.skipErrors:
                    raise HTTPException(status_code=400, detail={"message": str(e), "index": i}) from e
        db.commit()
        return {"created": created, "errors": errors}

    if rt == "Device":
        for i, row in enumerate(body.rows):
            try:
                st = str(row.get("status") or "PLANNED")
                d = Device(
                    id=uuid.uuid4(),
                    organizationId=oid,
                    name=str(row.get("name", "")).strip(),
                    deviceTypeId=uuid.UUID(str(row.get("deviceTypeId"))),
                    deviceRoleId=uuid.UUID(str(row.get("deviceRoleId"))),
                    rackId=uuid.UUID(str(row["rackId"])) if row.get("rackId") else None,
                    serialNumber=str(row["serialNumber"]) if row.get("serialNumber") else None,
                    positionU=int(row["positionU"]) if row.get("positionU") not in (None, "") else None,
                    face=str(row["face"]) if row.get("face") else None,
                    status=Devicestatus(st),
                    createdAt=now,
                    updatedAt=now,
                )
                db.add(d)
                db.flush()
                tid = row.get("templateId")
                if tid:
                    upsert_extension(
                        db,
                        organization_id=oid,
                        resource_type="Device",
                        resource_id=d.id,
                        template_id=uuid.UUID(str(tid)),
                        data={},
                    )
                record_audit(
                    db,
                    organization_id=oid,
                    actor=auth_actor_from_context(ctx),
                    action="bulk_import",
                    resource_type="Device",
                    resource_id=str(d.id),
                    correlation_id=new_correlation_id(),
                    after=columns_dict(d),
                )
                created += 1
            except Exception as e:  # noqa: BLE001
                db.rollback()
                errors.append({"index": i, "error": str(e)})
                if not body.skipErrors:
                    raise HTTPException(status_code=400, detail={"message": str(e), "index": i}) from e
        db.commit()
        return {"created": created, "errors": errors}

    if rt == "Vrf":
        for i, row in enumerate(body.rows):
            try:
                v = Vrf(
                    id=uuid.uuid4(),
                    organizationId=oid,
                    name=str(row.get("name", "")).strip(),
                    rd=str(row["rd"]) if row.get("rd") else None,
                    createdAt=now,
                    updatedAt=now,
                )
                db.add(v)
                db.flush()
                record_audit(
                    db,
                    organization_id=oid,
                    actor=auth_actor_from_context(ctx),
                    action="bulk_import",
                    resource_type="Vrf",
                    resource_id=str(v.id),
                    correlation_id=new_correlation_id(),
                    after=columns_dict(v),
                )
                created += 1
            except Exception as e:  # noqa: BLE001
                db.rollback()
                errors.append({"index": i, "error": str(e)})
                if not body.skipErrors:
                    raise HTTPException(status_code=400, detail={"message": str(e), "index": i}) from e
        db.commit()
        return {"created": created, "errors": errors}

    if rt in CATALOG_TYPES:
        try:
            created, errors = catalog_import_rows(db, ctx, rt, body.rows, body.skipErrors)
            return {"created": created, "errors": errors}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e)) from e

    raise HTTPException(status_code=400, detail="Unsupported")


@router.post("/bulk/{resource_type}/import/csv")
async def bulk_import_csv(
    resource_type: str,
    file: UploadFile = File(...),
    skipErrors: bool = Query(False),
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, Any]:
    raw = (await file.read()).decode("utf-8", errors="replace")
    reader = csv.DictReader(io.StringIO(raw))
    rows = [dict(r) for r in reader]
    return bulk_import_json(
        resource_type,
        BulkJsonImportBody(rows=rows, skipErrors=skipErrors),
        db,
        auth,
    )
