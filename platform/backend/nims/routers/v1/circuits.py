import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from nims.auth_context import AuthContext, auth_actor_from_context, require_write
from nims.crypto_util import new_correlation_id
from nims.deps import get_auth, get_db, require_auth_ctx
from nims.models_generated import Circuit, CircuitDiversityGroup, CircuitSegment, Circuitstatus, CircuitTermination, Provider
from nims.serialize import columns_dict, serialize_circuit, serialize_circuit_segment, serialize_provider
from nims.services.audit import record_audit
from nims.services.webhooks import dispatch_webhooks
from nims.timeutil import utc_now

router = APIRouter(tags=["circuits"])


class ProviderCreate(BaseModel):
    name: str = Field(min_length=1)
    asn: int | None = None


class CircuitCreate(BaseModel):
    providerId: uuid.UUID
    cid: str = Field(min_length=1)
    bandwidthMbps: int | None = Field(default=None, gt=0)
    status: Literal["PLANNED", "ACTIVE", "DECOMMISSIONED"] | None = None
    aSideNotes: str | None = None
    zSideNotes: str | None = None
    circuitDiversityGroupId: uuid.UUID | None = None


class CircuitSegmentCreate(BaseModel):
    """Add a leg to a multi-segment circuit. Omit segmentIndex to append after the last leg."""

    label: str | None = None
    segmentIndex: int | None = Field(default=None, ge=0)
    providerId: uuid.UUID | None = None
    bandwidthMbps: int | None = Field(default=None, gt=0)
    status: Literal["PLANNED", "ACTIVE", "DECOMMISSIONED"] | None = None
    aSideNotes: str | None = None
    zSideNotes: str | None = None


class ProviderUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    asn: int | None = None


class CircuitUpdate(BaseModel):
    providerId: uuid.UUID | None = None
    cid: str | None = Field(default=None, min_length=1)
    bandwidthMbps: int | None = Field(default=None, gt=0)
    status: Literal["PLANNED", "ACTIVE", "DECOMMISSIONED"] | None = None
    aSideNotes: str | None = None
    zSideNotes: str | None = None
    circuitDiversityGroupId: uuid.UUID | None = None


@router.get("/providers")
def list_providers(
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, list[dict[str, object]]]:
    ctx = require_auth_ctx(auth)
    items = (
        db.execute(
            select(Provider)
            .where(and_(Provider.organizationId == ctx.organization.id, Provider.deletedAt.is_(None)))
            .order_by(Provider.name.asc())
        )
        .scalars()
        .all()
    )
    return {"items": [serialize_provider(i) for i in items]}


@router.post("/providers")
def create_provider(
    body: ProviderCreate,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_write(require_auth_ctx(auth))
    correlation_id = new_correlation_id()
    now = utc_now()
    created = Provider(
        id=uuid.uuid4(),
        organizationId=ctx.organization.id,
        name=body.name,
        asn=body.asn,
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
        resource_type="Provider",
        resource_id=str(created.id),
        correlation_id=correlation_id,
        after=columns_dict(created),
    )
    db.commit()
    db.refresh(created)
    dispatch_webhooks(
        db,
        organization_id=ctx.organization.id,
        resource_type="Provider",
        resource_id=str(created.id),
        event="create",
    )
    return {"item": serialize_provider(created), "correlationId": correlation_id}


@router.get("/providers/{provider_id}")
def get_provider(
    provider_id: uuid.UUID,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_auth_ctx(auth)
    row = db.execute(
        select(Provider).where(
            and_(Provider.id == provider_id, Provider.organizationId == ctx.organization.id, Provider.deletedAt.is_(None)),
        ),
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    return {"item": serialize_provider(row)}


@router.patch("/providers/{provider_id}")
def update_provider(
    provider_id: uuid.UUID,
    body: ProviderUpdate,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_write(require_auth_ctx(auth))
    row = db.execute(
        select(Provider).where(
            and_(Provider.id == provider_id, Provider.organizationId == ctx.organization.id, Provider.deletedAt.is_(None)),
        ),
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider not found")
    correlation_id = new_correlation_id()
    before = columns_dict(row)
    raw = body.model_dump(exclude_unset=True)
    if "name" in raw:
        row.name = raw["name"]
    if "asn" in raw:
        row.asn = raw["asn"]
    row.updatedAt = utc_now()
    record_audit(
        db,
        organization_id=ctx.organization.id,
        actor=auth_actor_from_context(ctx),
        action="update",
        resource_type="Provider",
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
        resource_type="Provider",
        resource_id=str(row.id),
        event="update",
    )
    return {"item": serialize_provider(row), "correlationId": correlation_id}


@router.get("/circuits")
def list_circuits(
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, list[dict[str, object]]]:
    ctx = require_auth_ctx(auth)
    items = (
        db.execute(
            select(Circuit)
            .where(and_(Circuit.organizationId == ctx.organization.id, Circuit.deletedAt.is_(None)))
            .options(
                joinedload(Circuit.Provider_),
                joinedload(Circuit.CircuitDiversityGroup_),
                selectinload(Circuit.CircuitSegment).joinedload(CircuitSegment.Provider_),
                selectinload(Circuit.CircuitTermination).joinedload(CircuitTermination.Location_),
            )
            .order_by(Circuit.cid.asc())
        )
        .unique()
        .scalars()
        .all()
    )
    return {"items": [serialize_circuit(i) for i in items]}


@router.post("/circuits")
def create_circuit(
    body: CircuitCreate,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_write(require_auth_ctx(auth))
    correlation_id = new_correlation_id()
    now = utc_now()
    st = Circuitstatus(body.status) if body.status else Circuitstatus.PLANNED
    div_id: uuid.UUID | None = None
    if body.circuitDiversityGroupId is not None:
        dg = _diversity_group_in_org(db, ctx.organization.id, body.circuitDiversityGroupId)
        if dg is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Diversity group not found")
        div_id = body.circuitDiversityGroupId
    created = Circuit(
        id=uuid.uuid4(),
        organizationId=ctx.organization.id,
        providerId=body.providerId,
        cid=body.cid,
        bandwidthMbps=body.bandwidthMbps,
        status=st,
        aSideNotes=body.aSideNotes,
        zSideNotes=body.zSideNotes,
        circuitDiversityGroupId=div_id,
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
        resource_type="Circuit",
        resource_id=str(created.id),
        correlation_id=correlation_id,
        after=columns_dict(created),
    )
    db.commit()
    created = (
        db.execute(
            select(Circuit)
            .where(Circuit.id == created.id)
            .options(
                joinedload(Circuit.Provider_),
                joinedload(Circuit.CircuitDiversityGroup_),
                selectinload(Circuit.CircuitSegment).joinedload(CircuitSegment.Provider_),
                selectinload(Circuit.CircuitTermination).joinedload(CircuitTermination.Location_),
            ),
        )
        .unique()
        .scalar_one()
    )
    dispatch_webhooks(
        db,
        organization_id=ctx.organization.id,
        resource_type="Circuit",
        resource_id=str(created.id),
        event="create",
    )
    return {"item": serialize_circuit(created), "correlationId": correlation_id}


@router.get("/circuits/{circuit_id}")
def get_circuit(
    circuit_id: uuid.UUID,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_auth_ctx(auth)
    row = db.execute(
        select(Circuit)
        .where(
            and_(Circuit.id == circuit_id, Circuit.organizationId == ctx.organization.id, Circuit.deletedAt.is_(None)),
        )
        .options(
            joinedload(Circuit.Provider_),
            joinedload(Circuit.CircuitDiversityGroup_),
            selectinload(Circuit.CircuitSegment).joinedload(CircuitSegment.Provider_),
            selectinload(Circuit.CircuitTermination).joinedload(CircuitTermination.Location_),
        ),
    ).unique().scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Circuit not found")
    return {"item": serialize_circuit(row)}


@router.patch("/circuits/{circuit_id}")
def update_circuit(
    circuit_id: uuid.UUID,
    body: CircuitUpdate,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_write(require_auth_ctx(auth))
    row = db.execute(
        select(Circuit).where(
            and_(Circuit.id == circuit_id, Circuit.organizationId == ctx.organization.id, Circuit.deletedAt.is_(None)),
        ),
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Circuit not found")
    correlation_id = new_correlation_id()
    before = columns_dict(row)
    raw = body.model_dump(exclude_unset=True)
    if "providerId" in raw:
        p = _provider_in_org(db, ctx.organization.id, raw["providerId"])
        if p is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provider not found")
        row.providerId = raw["providerId"]
    if "cid" in raw:
        row.cid = raw["cid"]
    if "bandwidthMbps" in raw:
        row.bandwidthMbps = raw["bandwidthMbps"]
    if "status" in raw:
        row.status = Circuitstatus(raw["status"])
    if "aSideNotes" in raw:
        row.aSideNotes = raw["aSideNotes"]
    if "zSideNotes" in raw:
        row.zSideNotes = raw["zSideNotes"]
    if "circuitDiversityGroupId" in raw:
        div = raw["circuitDiversityGroupId"]
        if div is not None:
            dg = _diversity_group_in_org(db, ctx.organization.id, div)
            if dg is None:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Diversity group not found")
        row.circuitDiversityGroupId = div
    row.updatedAt = utc_now()
    record_audit(
        db,
        organization_id=ctx.organization.id,
        actor=auth_actor_from_context(ctx),
        action="update",
        resource_type="Circuit",
        resource_id=str(row.id),
        correlation_id=correlation_id,
        before=before,
        after=columns_dict(row),
    )
    db.commit()
    row = (
        db.execute(
            select(Circuit)
            .where(Circuit.id == circuit_id)
            .options(
                joinedload(Circuit.Provider_),
                joinedload(Circuit.CircuitDiversityGroup_),
                selectinload(Circuit.CircuitSegment).joinedload(CircuitSegment.Provider_),
                selectinload(Circuit.CircuitTermination).joinedload(CircuitTermination.Location_),
            ),
        )
        .unique()
        .scalar_one()
    )
    dispatch_webhooks(
        db,
        organization_id=ctx.organization.id,
        resource_type="Circuit",
        resource_id=str(row.id),
        event="update",
    )
    return {"item": serialize_circuit(row), "correlationId": correlation_id}


def _diversity_group_in_org(db: Session, organization_id: uuid.UUID, group_id: uuid.UUID) -> CircuitDiversityGroup | None:
    return db.execute(
        select(CircuitDiversityGroup).where(
            and_(
                CircuitDiversityGroup.id == group_id,
                CircuitDiversityGroup.organizationId == organization_id,
                CircuitDiversityGroup.deletedAt.is_(None),
            ),
        ),
    ).scalar_one_or_none()


def _get_circuit_for_org(db: Session, organization_id: uuid.UUID, circuit_id: uuid.UUID) -> Circuit:
    c = db.execute(
        select(Circuit).where(
            and_(
                Circuit.id == circuit_id,
                Circuit.organizationId == organization_id,
                Circuit.deletedAt.is_(None),
            ),
        ),
    ).scalar_one_or_none()
    if c is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Circuit not found")
    return c


def _provider_in_org(db: Session, organization_id: uuid.UUID, provider_id: uuid.UUID) -> Provider | None:
    return db.execute(
        select(Provider).where(
            and_(
                Provider.id == provider_id,
                Provider.organizationId == organization_id,
                Provider.deletedAt.is_(None),
            ),
        ),
    ).scalar_one_or_none()


@router.post("/circuits/{circuit_id}/segments")
def create_circuit_segment(
    circuit_id: uuid.UUID,
    body: CircuitSegmentCreate,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_write(require_auth_ctx(auth))
    circuit = _get_circuit_for_org(db, ctx.organization.id, circuit_id)
    if body.providerId is not None:
        p = _provider_in_org(db, ctx.organization.id, body.providerId)
        if p is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Provider not found")

    if body.segmentIndex is not None:
        next_idx = body.segmentIndex
        clash = db.execute(
            select(CircuitSegment).where(
                and_(CircuitSegment.circuitId == circuit.id, CircuitSegment.segmentIndex == next_idx),
            ),
        ).scalar_one_or_none()
        if clash is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="segmentIndex already in use for this circuit",
            )
    else:
        max_idx = db.execute(
            select(func.coalesce(func.max(CircuitSegment.segmentIndex), -1)).where(
                CircuitSegment.circuitId == circuit.id,
            ),
        ).scalar_one()
        next_idx = int(max_idx) + 1

    correlation_id = new_correlation_id()
    now = utc_now()
    st = Circuitstatus(body.status) if body.status else Circuitstatus.PLANNED
    seg = CircuitSegment(
        id=uuid.uuid4(),
        circuitId=circuit.id,
        segmentIndex=next_idx,
        label=body.label,
        providerId=body.providerId,
        bandwidthMbps=body.bandwidthMbps,
        status=st,
        aSideNotes=body.aSideNotes,
        zSideNotes=body.zSideNotes,
        createdAt=now,
        updatedAt=now,
    )
    db.add(seg)
    db.flush()
    record_audit(
        db,
        organization_id=ctx.organization.id,
        actor=auth_actor_from_context(ctx),
        action="create",
        resource_type="CircuitSegment",
        resource_id=str(seg.id),
        correlation_id=correlation_id,
        after=columns_dict(seg),
    )
    db.commit()
    seg = db.execute(
        select(CircuitSegment)
        .where(CircuitSegment.id == seg.id)
        .options(
            joinedload(CircuitSegment.Provider_),
            joinedload(CircuitSegment.Circuit_).joinedload(Circuit.Provider_),
        ),
    ).scalar_one()
    circuit_parent = seg.Circuit_
    dispatch_webhooks(
        db,
        organization_id=ctx.organization.id,
        resource_type="CircuitSegment",
        resource_id=str(seg.id),
        event="create",
    )
    return {
        "item": serialize_circuit_segment(seg, circuit_parent.Provider_),
        "correlationId": correlation_id,
    }


@router.delete("/circuits/{circuit_id}/segments/{segment_id}")
def delete_circuit_segment(
    circuit_id: uuid.UUID,
    segment_id: uuid.UUID,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_write(require_auth_ctx(auth))
    circuit = _get_circuit_for_org(db, ctx.organization.id, circuit_id)
    seg = db.execute(
        select(CircuitSegment).where(
            and_(CircuitSegment.id == segment_id, CircuitSegment.circuitId == circuit.id),
        ),
    ).scalar_one_or_none()
    if seg is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Segment not found")
    correlation_id = new_correlation_id()
    before = columns_dict(seg)
    db.delete(seg)
    record_audit(
        db,
        organization_id=ctx.organization.id,
        actor=auth_actor_from_context(ctx),
        action="delete",
        resource_type="CircuitSegment",
        resource_id=str(segment_id),
        correlation_id=correlation_id,
        before=before,
    )
    db.commit()
    dispatch_webhooks(
        db,
        organization_id=ctx.organization.id,
        resource_type="CircuitSegment",
        resource_id=str(segment_id),
        event="delete",
    )
    return {"ok": True, "correlationId": correlation_id}
