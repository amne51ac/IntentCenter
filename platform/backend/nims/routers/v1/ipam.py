import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, select
from sqlalchemy.orm import Session, joinedload

from nims.auth_context import AuthContext, auth_actor_from_context, require_write
from nims.crypto_util import new_correlation_id
from nims.deps import get_auth, get_db, require_auth_ctx
from nims.models_generated import Interface, IpAddress, Prefix, Vlan, Vrf
from nims.serialize import (
    columns_dict,
    serialize_ip_address,
    serialize_prefix,
    serialize_vlan,
    serialize_vrf,
)
from nims.services.audit import record_audit
from nims.services.webhooks import dispatch_webhooks
from nims.timeutil import utc_now

router = APIRouter(tags=["ipam"])


class VrfCreate(BaseModel):
    name: str = Field(min_length=1)
    rd: str | None = None


class PrefixCreate(BaseModel):
    vrfId: uuid.UUID
    cidr: str = Field(min_length=1)
    description: str | None = None
    parentId: uuid.UUID | None = None


class IpAddressCreate(BaseModel):
    prefixId: uuid.UUID
    address: str = Field(min_length=1)
    description: str | None = None
    interfaceId: uuid.UUID | None = None


class VlanCreate(BaseModel):
    vid: int = Field(ge=1, le=4094)
    name: str = Field(min_length=1)
    vlanGroupId: uuid.UUID | None = None


class VrfUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    rd: str | None = None


class PrefixUpdate(BaseModel):
    vrfId: uuid.UUID | None = None
    cidr: str | None = Field(default=None, min_length=1)
    description: str | None = None
    parentId: uuid.UUID | None = None


class IpAddressUpdate(BaseModel):
    prefixId: uuid.UUID | None = None
    address: str | None = Field(default=None, min_length=1)
    description: str | None = None
    interfaceId: uuid.UUID | None = None


class VlanUpdate(BaseModel):
    vid: int | None = Field(default=None, ge=1, le=4094)
    name: str | None = Field(default=None, min_length=1)
    vlanGroupId: uuid.UUID | None = None


@router.get("/vrfs")
def list_vrfs(
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, list[dict[str, object]]]:
    ctx = require_auth_ctx(auth)
    items = (
        db.execute(
            select(Vrf)
            .where(and_(Vrf.organizationId == ctx.organization.id, Vrf.deletedAt.is_(None)))
            .order_by(Vrf.name.asc())
        )
        .scalars()
        .all()
    )
    return {"items": [serialize_vrf(i) for i in items]}


@router.post("/vrfs")
def create_vrf(
    body: VrfCreate,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_write(require_auth_ctx(auth))
    correlation_id = new_correlation_id()
    now = utc_now()
    created = Vrf(
        id=uuid.uuid4(),
        organizationId=ctx.organization.id,
        name=body.name,
        rd=body.rd,
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
        resource_type="Vrf",
        resource_id=str(created.id),
        correlation_id=correlation_id,
        after=columns_dict(created),
    )
    db.commit()
    db.refresh(created)
    dispatch_webhooks(
        db,
        organization_id=ctx.organization.id,
        resource_type="Vrf",
        resource_id=str(created.id),
        event="create",
    )
    return {"item": serialize_vrf(created), "correlationId": correlation_id}


@router.get("/vrfs/{vrf_id}")
def get_vrf(
    vrf_id: uuid.UUID,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_auth_ctx(auth)
    row = db.execute(
        select(Vrf).where(
            and_(Vrf.id == vrf_id, Vrf.organizationId == ctx.organization.id, Vrf.deletedAt.is_(None)),
        ),
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VRF not found")
    return {"item": serialize_vrf(row)}


@router.patch("/vrfs/{vrf_id}")
def update_vrf(
    vrf_id: uuid.UUID,
    body: VrfUpdate,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_write(require_auth_ctx(auth))
    row = db.execute(
        select(Vrf).where(
            and_(Vrf.id == vrf_id, Vrf.organizationId == ctx.organization.id, Vrf.deletedAt.is_(None)),
        ),
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VRF not found")
    correlation_id = new_correlation_id()
    before = columns_dict(row)
    raw = body.model_dump(exclude_unset=True)
    if "name" in raw:
        row.name = raw["name"]
    if "rd" in raw:
        row.rd = raw["rd"]
    row.updatedAt = utc_now()
    record_audit(
        db,
        organization_id=ctx.organization.id,
        actor=auth_actor_from_context(ctx),
        action="update",
        resource_type="Vrf",
        resource_id=str(row.id),
        correlation_id=correlation_id,
        before=before,
        after=columns_dict(row),
    )
    db.commit()
    db.refresh(row)
    dispatch_webhooks(
        db,
        organization_id=ctx.organization.id,
        resource_type="Vrf",
        resource_id=str(row.id),
        event="update",
    )
    return {"item": serialize_vrf(row), "correlationId": correlation_id}


@router.get("/prefixes")
def list_prefixes(
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, list[dict[str, object]]]:
    ctx = require_auth_ctx(auth)
    items = (
        db.execute(
            select(Prefix)
            .where(and_(Prefix.organizationId == ctx.organization.id, Prefix.deletedAt.is_(None)))
            .options(joinedload(Prefix.Vrf_))
            .order_by(Prefix.cidr.asc())
        )
        .unique()
        .scalars()
        .all()
    )
    return {"items": [serialize_prefix(i) for i in items]}


@router.post("/prefixes")
def create_prefix(
    body: PrefixCreate,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_write(require_auth_ctx(auth))
    correlation_id = new_correlation_id()
    now = utc_now()
    created = Prefix(
        id=uuid.uuid4(),
        organizationId=ctx.organization.id,
        vrfId=body.vrfId,
        cidr=body.cidr,
        description=body.description,
        parentId=body.parentId,
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
        resource_type="Prefix",
        resource_id=str(created.id),
        correlation_id=correlation_id,
        after=columns_dict(created),
    )
    db.commit()
    created = (
        db.execute(select(Prefix).where(Prefix.id == created.id).options(joinedload(Prefix.Vrf_))).unique().scalar_one()
    )
    dispatch_webhooks(
        db,
        organization_id=ctx.organization.id,
        resource_type="Prefix",
        resource_id=str(created.id),
        event="create",
    )
    return {"item": serialize_prefix(created), "correlationId": correlation_id}


@router.get("/prefixes/{prefix_id}")
def get_prefix(
    prefix_id: uuid.UUID,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_auth_ctx(auth)
    row = db.execute(
        select(Prefix)
        .where(
            and_(Prefix.id == prefix_id, Prefix.organizationId == ctx.organization.id, Prefix.deletedAt.is_(None)),
        )
        .options(joinedload(Prefix.Vrf_)),
    ).unique().scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prefix not found")
    return {"item": serialize_prefix(row)}


@router.patch("/prefixes/{prefix_id}")
def update_prefix(
    prefix_id: uuid.UUID,
    body: PrefixUpdate,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_write(require_auth_ctx(auth))
    row = db.execute(
        select(Prefix).where(
            and_(Prefix.id == prefix_id, Prefix.organizationId == ctx.organization.id, Prefix.deletedAt.is_(None)),
        ),
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Prefix not found")
    correlation_id = new_correlation_id()
    before = columns_dict(row)
    raw = body.model_dump(exclude_unset=True)
    if "vrfId" in raw:
        row.vrfId = raw["vrfId"]
    if "cidr" in raw:
        row.cidr = raw["cidr"]
    if "description" in raw:
        row.description = raw["description"]
    if "parentId" in raw:
        row.parentId = raw["parentId"]
    row.updatedAt = utc_now()
    record_audit(
        db,
        organization_id=ctx.organization.id,
        actor=auth_actor_from_context(ctx),
        action="update",
        resource_type="Prefix",
        resource_id=str(row.id),
        correlation_id=correlation_id,
        before=before,
        after=columns_dict(row),
    )
    db.commit()
    row = db.execute(
        select(Prefix).where(Prefix.id == prefix_id).options(joinedload(Prefix.Vrf_)),
    ).unique().scalar_one()
    dispatch_webhooks(
        db,
        organization_id=ctx.organization.id,
        resource_type="Prefix",
        resource_id=str(row.id),
        event="update",
    )
    return {"item": serialize_prefix(row), "correlationId": correlation_id}


@router.get("/ip-addresses")
def list_ip_addresses(
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, list[dict[str, object]]]:
    ctx = require_auth_ctx(auth)
    items = (
        db.execute(
            select(IpAddress)
            .where(and_(IpAddress.organizationId == ctx.organization.id, IpAddress.deletedAt.is_(None)))
            .options(
                joinedload(IpAddress.Prefix_),
                joinedload(IpAddress.Interface_).joinedload(Interface.Device_),
            )
            .order_by(IpAddress.address.asc())
            .limit(500)
        )
        .unique()
        .scalars()
        .all()
    )
    return {"items": [serialize_ip_address(i) for i in items]}


@router.post("/ip-addresses")
def create_ip_address(
    body: IpAddressCreate,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_write(require_auth_ctx(auth))
    correlation_id = new_correlation_id()
    now = utc_now()
    created = IpAddress(
        id=uuid.uuid4(),
        organizationId=ctx.organization.id,
        prefixId=body.prefixId,
        address=body.address,
        description=body.description,
        interfaceId=body.interfaceId,
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
        resource_type="IpAddress",
        resource_id=str(created.id),
        correlation_id=correlation_id,
        after=columns_dict(created),
    )
    db.commit()
    created = (
        db.execute(
            select(IpAddress)
            .where(IpAddress.id == created.id)
            .options(
                joinedload(IpAddress.Prefix_),
                joinedload(IpAddress.Interface_).joinedload(Interface.Device_),
            )
        )
        .unique()
        .scalar_one()
    )
    dispatch_webhooks(
        db,
        organization_id=ctx.organization.id,
        resource_type="IpAddress",
        resource_id=str(created.id),
        event="create",
    )
    return {"item": serialize_ip_address(created), "correlationId": correlation_id}


@router.get("/ip-addresses/{ip_address_id}")
def get_ip_address(
    ip_address_id: uuid.UUID,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_auth_ctx(auth)
    row = db.execute(
        select(IpAddress)
        .where(
            and_(
                IpAddress.id == ip_address_id,
                IpAddress.organizationId == ctx.organization.id,
                IpAddress.deletedAt.is_(None),
            ),
        )
        .options(
            joinedload(IpAddress.Prefix_),
            joinedload(IpAddress.Interface_).joinedload(Interface.Device_),
        ),
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="IP address not found")
    return {"item": serialize_ip_address(row)}


@router.patch("/ip-addresses/{ip_address_id}")
def update_ip_address(
    ip_address_id: uuid.UUID,
    body: IpAddressUpdate,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_write(require_auth_ctx(auth))
    row = db.execute(
        select(IpAddress).where(
            and_(
                IpAddress.id == ip_address_id,
                IpAddress.organizationId == ctx.organization.id,
                IpAddress.deletedAt.is_(None),
            ),
        ),
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="IP address not found")
    correlation_id = new_correlation_id()
    before = columns_dict(row)
    raw = body.model_dump(exclude_unset=True)
    if "prefixId" in raw:
        row.prefixId = raw["prefixId"]
    if "address" in raw:
        row.address = raw["address"]
    if "description" in raw:
        row.description = raw["description"]
    if "interfaceId" in raw:
        row.interfaceId = raw["interfaceId"]
    row.updatedAt = utc_now()
    record_audit(
        db,
        organization_id=ctx.organization.id,
        actor=auth_actor_from_context(ctx),
        action="update",
        resource_type="IpAddress",
        resource_id=str(row.id),
        correlation_id=correlation_id,
        before=before,
        after=columns_dict(row),
    )
    db.commit()
    row = db.execute(
        select(IpAddress)
        .where(IpAddress.id == ip_address_id)
        .options(
            joinedload(IpAddress.Prefix_),
            joinedload(IpAddress.Interface_).joinedload(Interface.Device_),
        ),
    ).unique().scalar_one()
    dispatch_webhooks(
        db,
        organization_id=ctx.organization.id,
        resource_type="IpAddress",
        resource_id=str(row.id),
        event="update",
    )
    return {"item": serialize_ip_address(row), "correlationId": correlation_id}


@router.get("/vlans")
def list_vlans(
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, list[dict[str, object]]]:
    ctx = require_auth_ctx(auth)
    items = (
        db.execute(
            select(Vlan)
            .where(and_(Vlan.organizationId == ctx.organization.id, Vlan.deletedAt.is_(None)))
            .options(joinedload(Vlan.VlanGroup_))
            .order_by(Vlan.vid.asc())
        )
        .unique()
        .scalars()
        .all()
    )
    return {"items": [serialize_vlan(i) for i in items]}


@router.post("/vlans")
def create_vlan(
    body: VlanCreate,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_write(require_auth_ctx(auth))
    correlation_id = new_correlation_id()
    now = utc_now()
    created = Vlan(
        id=uuid.uuid4(),
        organizationId=ctx.organization.id,
        vid=body.vid,
        name=body.name,
        vlanGroupId=body.vlanGroupId,
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
        resource_type="Vlan",
        resource_id=str(created.id),
        correlation_id=correlation_id,
        after=columns_dict(created),
    )
    db.commit()
    created = (
        db.execute(select(Vlan).where(Vlan.id == created.id).options(joinedload(Vlan.VlanGroup_))).unique().scalar_one()
    )
    dispatch_webhooks(
        db,
        organization_id=ctx.organization.id,
        resource_type="Vlan",
        resource_id=str(created.id),
        event="create",
    )
    return {"item": serialize_vlan(created), "correlationId": correlation_id}


@router.get("/vlans/{vlan_id}")
def get_vlan(
    vlan_id: uuid.UUID,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_auth_ctx(auth)
    row = db.execute(
        select(Vlan)
        .where(and_(Vlan.id == vlan_id, Vlan.organizationId == ctx.organization.id, Vlan.deletedAt.is_(None)))
        .options(joinedload(Vlan.VlanGroup_)),
    ).unique().scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VLAN not found")
    return {"item": serialize_vlan(row)}


@router.patch("/vlans/{vlan_id}")
def update_vlan(
    vlan_id: uuid.UUID,
    body: VlanUpdate,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_write(require_auth_ctx(auth))
    row = db.execute(
        select(Vlan).where(
            and_(Vlan.id == vlan_id, Vlan.organizationId == ctx.organization.id, Vlan.deletedAt.is_(None)),
        ),
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="VLAN not found")
    correlation_id = new_correlation_id()
    before = columns_dict(row)
    raw = body.model_dump(exclude_unset=True)
    if "vid" in raw:
        row.vid = raw["vid"]
    if "name" in raw:
        row.name = raw["name"]
    if "vlanGroupId" in raw:
        row.vlanGroupId = raw["vlanGroupId"]
    row.updatedAt = utc_now()
    record_audit(
        db,
        organization_id=ctx.organization.id,
        actor=auth_actor_from_context(ctx),
        action="update",
        resource_type="Vlan",
        resource_id=str(row.id),
        correlation_id=correlation_id,
        before=before,
        after=columns_dict(row),
    )
    db.commit()
    row = db.execute(
        select(Vlan).where(Vlan.id == vlan_id).options(joinedload(Vlan.VlanGroup_)),
    ).unique().scalar_one()
    dispatch_webhooks(
        db,
        organization_id=ctx.organization.id,
        resource_type="Vlan",
        resource_id=str(row.id),
        event="update",
    )
    return {"item": serialize_vlan(row), "correlationId": correlation_id}
