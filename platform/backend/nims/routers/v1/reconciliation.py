import uuid
from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import and_, select
from sqlalchemy.orm import Session, joinedload

from nims.auth_context import AuthContext, auth_actor_from_context, require_write
from nims.crypto_util import new_correlation_id
from nims.deps import get_auth, get_db, require_auth_ctx
from nims.json_util import to_input_json
from nims.models_generated import Device, Devicestatus, Observationkind, ObservedResourceState
from nims.serialize import columns_dict, serialize_observed
from nims.services.audit import record_audit
from nims.timeutil import utc_now

router = APIRouter(tags=["reconciliation"])


class ObservedStateBody(BaseModel):
    kind: Literal["DEVICE", "INTERFACE", "SERVICE"]
    deviceId: uuid.UUID | None = None
    lastSeenAt: datetime | None = None
    health: str | None = None
    payload: dict[str, object] | None = None
    driftDetected: bool | None = None
    driftSummary: str | None = None


def _parse_last_seen(body: ObservedStateBody) -> datetime:
    if body.lastSeenAt is not None:
        return body.lastSeenAt
    return utc_now()


@router.post("/observed-state")
def post_observed_state(
    body: ObservedStateBody,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_write(require_auth_ctx(auth))
    if body.kind == "DEVICE" and body.deviceId is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="deviceId required for DEVICE observations")

    correlation_id = new_correlation_id()
    observation_kind = Observationkind[body.kind]

    drift = body.driftDetected if body.driftDetected is not None else False
    summary = body.driftSummary

    if body.deviceId is not None and body.kind == "DEVICE":
        device = db.execute(
            select(Device).where(
                and_(
                    Device.id == body.deviceId,
                    Device.organizationId == ctx.organization.id,
                    Device.deletedAt.is_(None),
                )
            )
        ).scalar_one_or_none()
        if device is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
        if device.status not in (Devicestatus.ACTIVE, Devicestatus.STAGED):
            drift = True
            summary = summary or f"Intent status is {device.status.value}; observed activity suggests mismatch."

    last_seen = _parse_last_seen(body)

    if body.deviceId is not None:
        existing = db.execute(
            select(ObservedResourceState).where(
                and_(
                    ObservedResourceState.organizationId == ctx.organization.id,
                    ObservedResourceState.deviceId == body.deviceId,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            existing.kind = observation_kind
            existing.lastSeenAt = last_seen
            existing.health = body.health
            existing.payload = to_input_json(body.payload) if body.payload is not None else None
            existing.driftDetected = drift
            existing.driftSummary = summary
            existing.updatedAt = utc_now()
            upserted = existing
        else:
            upserted = ObservedResourceState(
                id=uuid.uuid4(),
                organizationId=ctx.organization.id,
                kind=observation_kind,
                deviceId=body.deviceId,
                lastSeenAt=last_seen,
                health=body.health,
                payload=to_input_json(body.payload) if body.payload is not None else None,
                driftDetected=drift,
                driftSummary=summary,
                updatedAt=utc_now(),
            )
            db.add(upserted)
    else:
        upserted = ObservedResourceState(
            id=uuid.uuid4(),
            organizationId=ctx.organization.id,
            kind=observation_kind,
            lastSeenAt=last_seen,
            health=body.health,
            payload=to_input_json(body.payload) if body.payload is not None else None,
            driftDetected=drift,
            driftSummary=summary,
            updatedAt=utc_now(),
        )
        db.add(upserted)

    db.flush()
    record_audit(
        db,
        organization_id=ctx.organization.id,
        actor=auth_actor_from_context(ctx),
        action="observed_state_upsert",
        resourceType="ObservedResourceState",
        resourceId=str(upserted.id),
        correlation_id=correlation_id,
        after=columns_dict(upserted),
    )
    db.commit()
    upserted = (
        db.execute(
            select(ObservedResourceState)
            .where(ObservedResourceState.id == upserted.id)
            .options(joinedload(ObservedResourceState.Device_))
        )
        .unique()
        .scalar_one()
    )
    return {"item": serialize_observed(upserted), "correlationId": correlation_id}


@router.get("/observed-state")
def list_observed_state(
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, list[dict[str, object]]]:
    ctx = require_auth_ctx(auth)
    items = (
        db.execute(
            select(ObservedResourceState)
            .where(ObservedResourceState.organizationId == ctx.organization.id)
            .options(joinedload(ObservedResourceState.Device_))
            .order_by(ObservedResourceState.updatedAt.desc())
            .limit(200)
        )
        .unique()
        .scalars()
        .all()
    )
    return {"items": [serialize_observed(i) for i in items]}
