import uuid
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import and_, select
from sqlalchemy.orm import Session, joinedload

from nims.auth_context import AuthContext, auth_actor_from_context, require_write
from nims.crypto_util import new_correlation_id
from nims.deps import get_auth, get_db, require_auth_ctx
from nims.models_generated import (
    Cable,
    Device,
    DeviceRole,
    Devicestatus,
    DeviceType,
    Interface,
    Location,
    LocationType,
    ObjectTemplate,
    Rack,
    ResourceExtension,
)
from nims.serialize import (
    columns_dict,
    serialize_cable,
    serialize_device_full,
    serialize_device_role,
    serialize_device_summary,
    serialize_device_type,
    serialize_interface,
    serialize_location,
    serialize_location_type,
    serialize_rack,
)
from nims.services.audit import record_audit
from nims.services.extensions import (
    delete_extension_for_resource,
    extension_map,
    merge_extension,
    upsert_extension,
)
from nims.services.webhooks import dispatch_webhooks
from nims.timeutil import utc_now

router = APIRouter(tags=["dcim"])


class LocationCreate(BaseModel):
    name: str = Field(min_length=1)
    slug: str = Field(min_length=1)
    locationTypeId: uuid.UUID
    parentId: uuid.UUID | None = None
    description: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    templateId: uuid.UUID | None = None
    customAttributes: dict[str, Any] | None = None

    @model_validator(mode="after")
    def lat_lon_both_or_neither(self) -> "LocationCreate":
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("latitude and longitude must both be set or both omitted")
        return self


class LocationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    slug: str | None = Field(default=None, min_length=1)
    locationTypeId: uuid.UUID | None = None
    parentId: uuid.UUID | None = None
    description: str | None = None
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    templateId: uuid.UUID | None = None
    customAttributes: dict[str, Any] | None = None


class RackCreate(BaseModel):
    name: str = Field(min_length=1)
    locationId: uuid.UUID
    uHeight: int | None = Field(default=None, gt=0)
    templateId: uuid.UUID | None = None
    customAttributes: dict[str, Any] | None = None


class RackUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    locationId: uuid.UUID | None = None
    uHeight: int | None = Field(default=None, gt=0)
    templateId: uuid.UUID | None = None
    customAttributes: dict[str, Any] | None = None


class DeviceCreate(BaseModel):
    name: str = Field(min_length=1)
    deviceTypeId: uuid.UUID
    deviceRoleId: uuid.UUID
    rackId: uuid.UUID | None = None
    serialNumber: str | None = None
    positionU: int | None = None
    face: str | None = None
    status: Literal["PLANNED", "STAGED", "ACTIVE", "DECOMMISSIONED"] | None = None
    templateId: uuid.UUID | None = None
    customAttributes: dict[str, Any] | None = None


class DeviceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    deviceTypeId: uuid.UUID | None = None
    deviceRoleId: uuid.UUID | None = None
    rackId: uuid.UUID | None = None
    serialNumber: str | None = None
    positionU: int | None = None
    face: str | None = None
    status: Literal["PLANNED", "STAGED", "ACTIVE", "DECOMMISSIONED"] | None = None
    templateId: uuid.UUID | None = None
    customAttributes: dict[str, Any] | None = None


class InterfaceCreate(BaseModel):
    name: str = Field(min_length=1)
    type: str = "ethernet"
    macAddress: str | None = None
    mtu: int | None = None


class CableCreate(BaseModel):
    interfaceAId: uuid.UUID
    interfaceBId: uuid.UUID
    label: str | None = None


def _resolve_template_id(
    db: Session,
    organization_id: uuid.UUID,
    resource_type: str,
    template_id: uuid.UUID | None,
) -> uuid.UUID | None:
    if template_id is None:
        return None
    t = db.execute(
        select(ObjectTemplate).where(
            and_(
                ObjectTemplate.id == template_id,
                ObjectTemplate.organizationId == organization_id,
                ObjectTemplate.resourceType == resource_type,
            ),
        ),
    ).scalar_one_or_none()
    if t is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Template not found or wrong type for this resource",
        )
    return template_id


def _apply_extension_on_create(
    db: Session,
    organization_id: uuid.UUID,
    resource_type: str,
    resource_id: uuid.UUID,
    template_id: uuid.UUID | None,
    custom_attributes: dict[str, Any] | None,
) -> None:
    if template_id is None and not custom_attributes:
        return
    tid = _resolve_template_id(db, organization_id, resource_type, template_id)
    upsert_extension(
        db,
        organization_id=organization_id,
        resource_type=resource_type,
        resource_id=resource_id,
        template_id=tid,
        data=dict(custom_attributes or {}),
    )


def _apply_extension_patch(
    db: Session,
    organization_id: uuid.UUID,
    resource_type: str,
    resource_id: uuid.UUID,
    body: LocationUpdate | RackUpdate | DeviceUpdate,
) -> None:
    raw = body.model_dump(exclude_unset=True)
    if "templateId" not in raw and "customAttributes" not in raw:
        return
    existing = db.execute(
        select(ResourceExtension).where(
            and_(
                ResourceExtension.organizationId == organization_id,
                ResourceExtension.resourceType == resource_type,
                ResourceExtension.resourceId == resource_id,
            ),
        ),
    ).scalar_one_or_none()
    cur_tid = existing.templateId if existing else None
    cur_data: dict[str, Any] = dict(existing.data) if existing and isinstance(existing.data, dict) else {}
    new_tid = raw["templateId"] if "templateId" in raw else cur_tid
    new_data = raw["customAttributes"] if "customAttributes" in raw else cur_data
    if not isinstance(new_data, dict):
        new_data = cur_data
    tid = _resolve_template_id(db, organization_id, resource_type, new_tid)
    if tid is None and not new_data:
        if existing:
            delete_extension_for_resource(db, organization_id, resource_type, resource_id)
        return
    upsert_extension(
        db,
        organization_id=organization_id,
        resource_type=resource_type,
        resource_id=resource_id,
        template_id=tid,
        data=new_data,
    )


def _org_where(oid: uuid.UUID):
    return and_(Location.organizationId == oid, Location.deletedAt.is_(None))


@router.get("/location-types")
def list_location_types(
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, list[dict[str, object]]]:
    require_auth_ctx(auth)
    items = db.execute(select(LocationType).order_by(LocationType.name.asc())).scalars().all()
    return {"items": [serialize_location_type(i) for i in items]}


@router.get("/device-roles")
def list_device_roles(
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, list[dict[str, object]]]:
    require_auth_ctx(auth)
    items = db.execute(select(DeviceRole).order_by(DeviceRole.name.asc())).scalars().all()
    return {"items": [serialize_device_role(i) for i in items]}


@router.get("/device-types")
def list_device_types(
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, list[dict[str, object]]]:
    require_auth_ctx(auth)
    items = (
        db.execute(
            select(DeviceType).options(joinedload(DeviceType.Manufacturer_)).order_by(DeviceType.model.asc()),
        )
        .unique()
        .scalars()
        .all()
    )
    return {"items": [serialize_device_type(i) for i in items]}


@router.get("/locations")
def list_locations(
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, list[dict[str, object]]]:
    ctx = require_auth_ctx(auth)
    items = (
        db.execute(
            select(Location)
            .where(_org_where(ctx.organization.id))
            .options(joinedload(Location.LocationType_), joinedload(Location.Location))
            .order_by(Location.name.asc())
        )
        .unique()
        .scalars()
        .all()
    )
    ids = [i.id for i in items]
    ext_by_id = extension_map(db, ctx.organization.id, "Location", ids)
    return {
        "items": [
            merge_extension(serialize_location(i), ext_by_id.get(str(i.id))) for i in items
        ],
    }


@router.post("/locations")
def create_location(
    body: LocationCreate,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_write(require_auth_ctx(auth))
    correlation_id = new_correlation_id()
    now = utc_now()
    created = Location(
        id=uuid.uuid4(),
        organizationId=ctx.organization.id,
        name=body.name,
        slug=body.slug,
        locationTypeId=body.locationTypeId,
        parentId=body.parentId,
        description=body.description,
        latitude=body.latitude,
        longitude=body.longitude,
        createdAt=now,
        updatedAt=now,
    )
    db.add(created)
    db.flush()
    _apply_extension_on_create(
        db,
        ctx.organization.id,
        "Location",
        created.id,
        body.templateId,
        body.customAttributes,
    )
    record_audit(
        db,
        organization_id=ctx.organization.id,
        actor=auth_actor_from_context(ctx),
        action="create",
        resource_type="Location",
        resource_id=str(created.id),
        correlation_id=correlation_id,
        after=columns_dict(created),
    )
    db.commit()
    created = (
        db.execute(
            select(Location)
            .where(Location.id == created.id)
            .options(joinedload(Location.LocationType_), joinedload(Location.Location))
        )
        .unique()
        .scalar_one()
    )
    dispatch_webhooks(
        db,
        organization_id=ctx.organization.id,
        resource_type="Location",
        resource_id=str(created.id),
        event="create",
    )
    ext_by_id = extension_map(db, ctx.organization.id, "Location", [created.id])
    return {
        "item": merge_extension(serialize_location(created), ext_by_id.get(str(created.id))),
        "correlationId": correlation_id,
    }


@router.get("/locations/{location_id}")
def get_location(
    location_id: uuid.UUID,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, dict[str, object]]:
    ctx = require_auth_ctx(auth)
    loc = (
        db.execute(
            select(Location)
            .where(
                and_(
                    Location.id == location_id,
                    Location.organizationId == ctx.organization.id,
                    Location.deletedAt.is_(None),
                ),
            )
            .options(joinedload(Location.LocationType_), joinedload(Location.Location))
        )
        .unique()
        .scalar_one_or_none()
    )
    if loc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    ext_by_id = extension_map(db, ctx.organization.id, "Location", [location_id])
    return {"item": merge_extension(serialize_location(loc), ext_by_id.get(str(location_id)))}


@router.patch("/locations/{location_id}")
def update_location(
    location_id: uuid.UUID,
    body: LocationUpdate,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_write(require_auth_ctx(auth))
    loc = db.execute(
        select(Location).where(
            and_(
                Location.id == location_id,
                Location.organizationId == ctx.organization.id,
                Location.deletedAt.is_(None),
            ),
        ),
    ).scalar_one_or_none()
    if loc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    correlation_id = new_correlation_id()
    before = columns_dict(loc)
    raw = body.model_dump(exclude_unset=True)
    if "name" in raw:
        loc.name = raw["name"]
    if "slug" in raw:
        loc.slug = raw["slug"]
    if "locationTypeId" in raw:
        loc.locationTypeId = raw["locationTypeId"]
    if "parentId" in raw:
        loc.parentId = raw["parentId"]
    if "description" in raw:
        loc.description = raw["description"]
    if "latitude" in raw or "longitude" in raw:
        if "latitude" not in raw or "longitude" not in raw:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="latitude and longitude must be updated together",
            )
        la = raw["latitude"]
        lo = raw["longitude"]
        if (la is None) != (lo is None):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="latitude and longitude must both be set or both cleared",
            )
        loc.latitude = la
        loc.longitude = lo
    loc.updatedAt = utc_now()
    _apply_extension_patch(db, ctx.organization.id, "Location", location_id, body)
    record_audit(
        db,
        organization_id=ctx.organization.id,
        actor=auth_actor_from_context(ctx),
        action="update",
        resource_type="Location",
        resource_id=str(loc.id),
        correlation_id=correlation_id,
        before=before,
        after=columns_dict(loc),
    )
    db.commit()
    loc = (
        db.execute(
            select(Location)
            .where(Location.id == location_id)
            .options(joinedload(Location.LocationType_), joinedload(Location.Location))
        )
        .unique()
        .scalar_one()
    )
    dispatch_webhooks(
        db,
        organization_id=ctx.organization.id,
        resource_type="Location",
        resource_id=str(loc.id),
        event="update",
    )
    ext_by_id = extension_map(db, ctx.organization.id, "Location", [location_id])
    return {
        "item": merge_extension(serialize_location(loc), ext_by_id.get(str(location_id))),
        "correlationId": correlation_id,
    }


@router.delete("/locations/{location_id}")
def delete_location(
    location_id: uuid.UUID,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, str]:
    ctx = require_write(require_auth_ctx(auth))
    loc = db.execute(
        select(Location).where(
            and_(
                Location.id == location_id,
                Location.organizationId == ctx.organization.id,
                Location.deletedAt.is_(None),
            ),
        ),
    ).scalar_one_or_none()
    if loc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    child = db.execute(
        select(Location).where(
            and_(
                Location.organizationId == ctx.organization.id,
                Location.parentId == location_id,
                Location.deletedAt.is_(None),
            ),
        ),
    ).scalar_one_or_none()
    if child is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Location has child locations; remove or reassign them first.",
        )
    rack_here = db.execute(
        select(Rack).where(
            and_(
                Rack.organizationId == ctx.organization.id,
                Rack.locationId == location_id,
                Rack.deletedAt.is_(None),
            ),
        ),
    ).scalar_one_or_none()
    if rack_here is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Location has racks; move or delete them first.",
        )
    correlation_id = new_correlation_id()
    before = columns_dict(loc)
    now = utc_now()
    loc.deletedAt = now
    loc.updatedAt = now
    delete_extension_for_resource(db, ctx.organization.id, "Location", location_id)
    record_audit(
        db,
        organization_id=ctx.organization.id,
        actor=auth_actor_from_context(ctx),
        action="delete",
        resource_type="Location",
        resource_id=str(loc.id),
        correlation_id=correlation_id,
        before=before,
        after=columns_dict(loc),
    )
    db.commit()
    dispatch_webhooks(
        db,
        organization_id=ctx.organization.id,
        resource_type="Location",
        resource_id=str(location_id),
        event="delete",
    )
    return {"status": "ok", "correlationId": correlation_id}


@router.get("/racks")
def list_racks(
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, list[dict[str, object]]]:
    ctx = require_auth_ctx(auth)
    items = (
        db.execute(
            select(Rack)
            .where(and_(Rack.organizationId == ctx.organization.id, Rack.deletedAt.is_(None)))
            .options(
                joinedload(Rack.Location_).joinedload(Location.LocationType_),
                joinedload(Rack.Location_).joinedload(Location.Location),
            )
            .order_by(Rack.name.asc())
        )
        .unique()
        .scalars()
        .all()
    )
    ids = [i.id for i in items]
    ext_by_id = extension_map(db, ctx.organization.id, "Rack", ids)
    return {
        "items": [
            merge_extension(serialize_rack(i), ext_by_id.get(str(i.id))) for i in items
        ],
    }


@router.post("/racks")
def create_rack(
    body: RackCreate,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_write(require_auth_ctx(auth))
    correlation_id = new_correlation_id()
    now = utc_now()
    created = Rack(
        id=uuid.uuid4(),
        organizationId=ctx.organization.id,
        name=body.name,
        locationId=body.locationId,
        uHeight=body.uHeight if body.uHeight is not None else 42,
        createdAt=now,
        updatedAt=now,
    )
    db.add(created)
    db.flush()
    _apply_extension_on_create(
        db,
        ctx.organization.id,
        "Rack",
        created.id,
        body.templateId,
        body.customAttributes,
    )
    record_audit(
        db,
        organization_id=ctx.organization.id,
        actor=auth_actor_from_context(ctx),
        action="create",
        resource_type="Rack",
        resource_id=str(created.id),
        correlation_id=correlation_id,
        after=columns_dict(created),
    )
    db.commit()
    db.refresh(created)
    db.refresh(created, ["Location_"])
    dispatch_webhooks(
        db,
        organization_id=ctx.organization.id,
        resource_type="Rack",
        resource_id=str(created.id),
        event="create",
    )
    ext_by_id = extension_map(db, ctx.organization.id, "Rack", [created.id])
    return {
        "item": merge_extension(serialize_rack(created), ext_by_id.get(str(created.id))),
        "correlationId": correlation_id,
    }


@router.get("/racks/{rack_id}")
def get_rack(
    rack_id: uuid.UUID,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, dict[str, object]]:
    ctx = require_auth_ctx(auth)
    r = (
        db.execute(
            select(Rack)
            .where(
                and_(
                    Rack.id == rack_id,
                    Rack.organizationId == ctx.organization.id,
                    Rack.deletedAt.is_(None),
                ),
            )
            .options(
                joinedload(Rack.Location_).joinedload(Location.LocationType_),
                joinedload(Rack.Location_).joinedload(Location.Location),
            ),
        )
        .unique()
        .scalar_one_or_none()
    )
    if r is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    ext_by_id = extension_map(db, ctx.organization.id, "Rack", [rack_id])
    return {"item": merge_extension(serialize_rack(r), ext_by_id.get(str(rack_id)))}


@router.patch("/racks/{rack_id}")
def update_rack(
    rack_id: uuid.UUID,
    body: RackUpdate,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_write(require_auth_ctx(auth))
    r = db.execute(
        select(Rack).where(
            and_(
                Rack.id == rack_id,
                Rack.organizationId == ctx.organization.id,
                Rack.deletedAt.is_(None),
            ),
        ),
    ).scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    correlation_id = new_correlation_id()
    before = columns_dict(r)
    raw = body.model_dump(exclude_unset=True)
    if "name" in raw:
        r.name = raw["name"]
    if "locationId" in raw:
        r.locationId = raw["locationId"]
    if "uHeight" in raw:
        r.uHeight = raw["uHeight"]
    r.updatedAt = utc_now()
    _apply_extension_patch(db, ctx.organization.id, "Rack", rack_id, body)
    record_audit(
        db,
        organization_id=ctx.organization.id,
        actor=auth_actor_from_context(ctx),
        action="update",
        resource_type="Rack",
        resource_id=str(r.id),
        correlation_id=correlation_id,
        before=before,
        after=columns_dict(r),
    )
    db.commit()
    r = (
        db.execute(
            select(Rack)
            .where(Rack.id == rack_id)
            .options(
                joinedload(Rack.Location_).joinedload(Location.LocationType_),
                joinedload(Rack.Location_).joinedload(Location.Location),
            ),
        )
        .unique()
        .scalar_one()
    )
    dispatch_webhooks(
        db,
        organization_id=ctx.organization.id,
        resource_type="Rack",
        resource_id=str(r.id),
        event="update",
    )
    ext_by_id = extension_map(db, ctx.organization.id, "Rack", [rack_id])
    return {
        "item": merge_extension(serialize_rack(r), ext_by_id.get(str(rack_id))),
        "correlationId": correlation_id,
    }


@router.delete("/racks/{rack_id}")
def delete_rack(
    rack_id: uuid.UUID,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, str]:
    ctx = require_write(require_auth_ctx(auth))
    r = db.execute(
        select(Rack).where(
            and_(
                Rack.id == rack_id,
                Rack.organizationId == ctx.organization.id,
                Rack.deletedAt.is_(None),
            ),
        ),
    ).scalar_one_or_none()
    if r is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    dev_here = db.execute(
        select(Device).where(
            and_(
                Device.organizationId == ctx.organization.id,
                Device.rackId == rack_id,
                Device.deletedAt.is_(None),
            ),
        ),
    ).scalar_one_or_none()
    if dev_here is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Rack has devices; move or delete them first.",
        )
    correlation_id = new_correlation_id()
    before = columns_dict(r)
    now = utc_now()
    r.deletedAt = now
    r.updatedAt = now
    delete_extension_for_resource(db, ctx.organization.id, "Rack", rack_id)
    record_audit(
        db,
        organization_id=ctx.organization.id,
        actor=auth_actor_from_context(ctx),
        action="delete",
        resource_type="Rack",
        resource_id=str(r.id),
        correlation_id=correlation_id,
        before=before,
        after=columns_dict(r),
    )
    db.commit()
    dispatch_webhooks(
        db,
        organization_id=ctx.organization.id,
        resource_type="Rack",
        resource_id=str(rack_id),
        event="delete",
    )
    return {"status": "ok", "correlationId": correlation_id}


@router.get("/devices")
def list_devices(
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, list[dict[str, object]]]:
    ctx = require_auth_ctx(auth)
    items = (
        db.execute(
            select(Device)
            .where(and_(Device.organizationId == ctx.organization.id, Device.deletedAt.is_(None)))
            .options(
                joinedload(Device.DeviceType_).joinedload(DeviceType.Manufacturer_),
                joinedload(Device.DeviceRole_),
                joinedload(Device.Rack_).joinedload(Rack.Location_),
            )
            .order_by(Device.name.asc())
        )
        .unique()
        .scalars()
        .all()
    )
    ids = [i.id for i in items]
    ext_by_id = extension_map(db, ctx.organization.id, "Device", ids)
    return {
        "items": [
            merge_extension(serialize_device_summary(i), ext_by_id.get(str(i.id))) for i in items
        ],
    }


@router.post("/devices")
def create_device(
    body: DeviceCreate,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_write(require_auth_ctx(auth))
    correlation_id = new_correlation_id()
    now = utc_now()
    st = Devicestatus(body.status) if body.status else Devicestatus.PLANNED
    created = Device(
        id=uuid.uuid4(),
        organizationId=ctx.organization.id,
        name=body.name,
        deviceTypeId=body.deviceTypeId,
        deviceRoleId=body.deviceRoleId,
        rackId=body.rackId,
        serialNumber=body.serialNumber,
        positionU=body.positionU,
        face=body.face,
        status=st,
        createdAt=now,
        updatedAt=now,
    )
    db.add(created)
    db.flush()
    _apply_extension_on_create(
        db,
        ctx.organization.id,
        "Device",
        created.id,
        body.templateId,
        body.customAttributes,
    )
    record_audit(
        db,
        organization_id=ctx.organization.id,
        actor=auth_actor_from_context(ctx),
        action="create",
        resource_type="Device",
        resource_id=str(created.id),
        correlation_id=correlation_id,
        after=columns_dict(created),
    )
    db.commit()
    created = (
        db.execute(
            select(Device)
            .where(Device.id == created.id)
            .options(
                joinedload(Device.DeviceType_).joinedload(DeviceType.Manufacturer_),
                joinedload(Device.DeviceRole_),
                joinedload(Device.Rack_),
            )
        )
        .unique()
        .scalar_one()
    )
    dispatch_webhooks(
        db,
        organization_id=ctx.organization.id,
        resource_type="Device",
        resource_id=str(created.id),
        event="create",
    )
    ext_by_id = extension_map(db, ctx.organization.id, "Device", [created.id])
    return {
        "item": merge_extension(serialize_device_summary(created), ext_by_id.get(str(created.id))),
        "correlationId": correlation_id,
    }


@router.get("/devices/{device_id}")
def get_device(
    device_id: uuid.UUID,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, dict[str, object]]:
    ctx = require_auth_ctx(auth)
    dev = (
        db.execute(
            select(Device)
            .where(
                and_(
                    Device.id == device_id,
                    Device.organizationId == ctx.organization.id,
                    Device.deletedAt.is_(None),
                )
            )
            .options(
                joinedload(Device.DeviceType_).joinedload(DeviceType.Manufacturer_),
                joinedload(Device.DeviceRole_),
                joinedload(Device.Rack_),
                joinedload(Device.Interface),
                joinedload(Device.ObservedResourceState),
            )
        )
        .unique()
        .scalar_one_or_none()
    )
    if dev is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    ext_by_id = extension_map(db, ctx.organization.id, "Device", [device_id])
    return {
        "item": merge_extension(serialize_device_full(dev), ext_by_id.get(str(device_id))),
    }


@router.patch("/devices/{device_id}")
def update_device(
    device_id: uuid.UUID,
    body: DeviceUpdate,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_write(require_auth_ctx(auth))
    dev = db.execute(
        select(Device).where(
            and_(
                Device.id == device_id,
                Device.organizationId == ctx.organization.id,
                Device.deletedAt.is_(None),
            ),
        ),
    ).scalar_one_or_none()
    if dev is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    correlation_id = new_correlation_id()
    before = columns_dict(dev)
    raw = body.model_dump(exclude_unset=True)
    if "name" in raw:
        dev.name = raw["name"]
    if "deviceTypeId" in raw:
        dev.deviceTypeId = raw["deviceTypeId"]
    if "deviceRoleId" in raw:
        dev.deviceRoleId = raw["deviceRoleId"]
    if "rackId" in raw:
        dev.rackId = raw["rackId"]
    if "serialNumber" in raw:
        dev.serialNumber = raw["serialNumber"]
    if "positionU" in raw:
        dev.positionU = raw["positionU"]
    if "face" in raw:
        dev.face = raw["face"]
    if "status" in raw and raw["status"] is not None:
        dev.status = Devicestatus(raw["status"])
    dev.updatedAt = utc_now()
    _apply_extension_patch(db, ctx.organization.id, "Device", device_id, body)
    record_audit(
        db,
        organization_id=ctx.organization.id,
        actor=auth_actor_from_context(ctx),
        action="update",
        resource_type="Device",
        resource_id=str(dev.id),
        correlation_id=correlation_id,
        before=before,
        after=columns_dict(dev),
    )
    db.commit()
    dev = (
        db.execute(
            select(Device)
            .where(Device.id == device_id)
            .options(
                joinedload(Device.DeviceType_).joinedload(DeviceType.Manufacturer_),
                joinedload(Device.DeviceRole_),
                joinedload(Device.Rack_),
            ),
        )
        .unique()
        .scalar_one()
    )
    dispatch_webhooks(
        db,
        organization_id=ctx.organization.id,
        resource_type="Device",
        resource_id=str(dev.id),
        event="update",
    )
    ext_by_id = extension_map(db, ctx.organization.id, "Device", [device_id])
    return {
        "item": merge_extension(serialize_device_summary(dev), ext_by_id.get(str(device_id))),
        "correlationId": correlation_id,
    }


@router.delete("/devices/{device_id}")
def delete_device(
    device_id: uuid.UUID,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, str]:
    ctx = require_write(require_auth_ctx(auth))
    dev = db.execute(
        select(Device).where(
            and_(
                Device.id == device_id,
                Device.organizationId == ctx.organization.id,
                Device.deletedAt.is_(None),
            ),
        ),
    ).scalar_one_or_none()
    if dev is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    iface_here = db.execute(
        select(Interface).where(
            and_(Interface.deviceId == device_id, Interface.deletedAt.is_(None)),
        ),
    ).scalar_one_or_none()
    if iface_here is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Device has interfaces; remove them first.",
        )
    correlation_id = new_correlation_id()
    before = columns_dict(dev)
    now = utc_now()
    dev.deletedAt = now
    dev.updatedAt = now
    delete_extension_for_resource(db, ctx.organization.id, "Device", device_id)
    record_audit(
        db,
        organization_id=ctx.organization.id,
        actor=auth_actor_from_context(ctx),
        action="delete",
        resource_type="Device",
        resource_id=str(dev.id),
        correlation_id=correlation_id,
        before=before,
        after=columns_dict(dev),
    )
    db.commit()
    dispatch_webhooks(
        db,
        organization_id=ctx.organization.id,
        resource_type="Device",
        resource_id=str(device_id),
        event="delete",
    )
    return {"status": "ok", "correlationId": correlation_id}


@router.post("/devices/{device_id}/interfaces")
def create_interface(
    device_id: uuid.UUID,
    body: InterfaceCreate,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_write(require_auth_ctx(auth))
    dev = db.execute(
        select(Device).where(
            and_(
                Device.id == device_id,
                Device.organizationId == ctx.organization.id,
                Device.deletedAt.is_(None),
            )
        )
    ).scalar_one_or_none()
    if dev is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    correlation_id = new_correlation_id()
    now = utc_now()
    created = Interface(
        id=uuid.uuid4(),
        deviceId=device_id,
        name=body.name,
        type=body.type,
        macAddress=body.macAddress,
        mtu=body.mtu,
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
        resource_type="Interface",
        resource_id=str(created.id),
        correlation_id=correlation_id,
        after=columns_dict(created),
    )
    db.commit()
    db.refresh(created)
    dispatch_webhooks(
        db,
        organization_id=ctx.organization.id,
        resource_type="Interface",
        resource_id=str(created.id),
        event="create",
    )
    return {"item": serialize_interface(created), "correlationId": correlation_id}


@router.post("/cables")
def create_cable(
    body: CableCreate,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_write(require_auth_ctx(auth))
    correlation_id = new_correlation_id()
    now = utc_now()
    created = Cable(
        id=uuid.uuid4(),
        interfaceAId=body.interfaceAId,
        interfaceBId=body.interfaceBId,
        label=body.label,
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
        resource_type="Cable",
        resource_id=str(created.id),
        correlation_id=correlation_id,
        after=columns_dict(created),
    )
    db.commit()
    db.refresh(created)
    dispatch_webhooks(
        db,
        organization_id=ctx.organization.id,
        resource_type="Cable",
        resource_id=str(created.id),
        event="create",
    )
    return {"item": serialize_cable(created), "correlationId": correlation_id}
