import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, select
from sqlalchemy.orm import Session, joinedload

from nims.auth_context import AuthContext, auth_actor_from_context, require_write
from nims.crypto_util import new_correlation_id
from nims.deps import get_auth, get_db, require_auth_ctx
from nims.json_util import to_input_json
from nims.models_generated import (
    ChangeRequest,
    Changerequeststatus,
    JobDefinition,
    JobRun,
    Jobrunstatus,
    ServiceInstance,
)
from nims.serialize import (
    columns_dict,
    serialize_change_request,
    serialize_job_definition,
    serialize_job_run,
    serialize_service_instance,
)
from nims.services.audit import record_audit
from nims.services.job_runner import execute_job
from nims.timeutil import utc_now

router = APIRouter(tags=["automation"])


class JobCreate(BaseModel):
    key: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str | None = None
    requiresApproval: bool | None = None


class JobRunBody(BaseModel):
    input: dict[str, Any] | None = None
    idempotencyKey: str | None = None


class ChangeRequestCreate(BaseModel):
    title: str = Field(min_length=1)
    description: str | None = None
    payload: dict[str, Any]


class ServiceCreate(BaseModel):
    name: str = Field(min_length=1)
    serviceType: str = Field(min_length=1)
    customerRef: str | None = None
    metadata: dict[str, Any] | None = None


class ServiceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    serviceType: str | None = Field(default=None, min_length=1)
    customerRef: str | None = None
    metadata: dict[str, Any] | None = None


class JobDefinitionUpdate(BaseModel):
    key: str | None = Field(default=None, min_length=1)
    name: str | None = Field(default=None, min_length=1)
    description: str | None = None
    requiresApproval: bool | None = None
    enabled: bool | None = None


@router.get("/jobs")
def list_jobs(
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, list[dict[str, object]]]:
    ctx = require_auth_ctx(auth)
    items = (
        db.execute(
            select(JobDefinition)
            .where(JobDefinition.organizationId == ctx.organization.id)
            .order_by(JobDefinition.key.asc())
        )
        .scalars()
        .all()
    )
    return {"items": [serialize_job_definition(i) for i in items]}


@router.get("/jobs/{job_definition_id}")
def get_job_definition(
    job_definition_id: uuid.UUID,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_auth_ctx(auth)
    row = db.execute(
        select(JobDefinition).where(
            and_(JobDefinition.id == job_definition_id, JobDefinition.organizationId == ctx.organization.id),
        ),
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job definition not found")
    return {"item": serialize_job_definition(row)}


@router.patch("/jobs/{job_definition_id}")
def update_job_definition(
    job_definition_id: uuid.UUID,
    body: JobDefinitionUpdate,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_write(require_auth_ctx(auth))
    row = db.execute(
        select(JobDefinition).where(
            and_(JobDefinition.id == job_definition_id, JobDefinition.organizationId == ctx.organization.id),
        ),
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job definition not found")
    raw = body.model_dump(exclude_unset=True)
    if "key" in raw:
        clash = db.execute(
            select(JobDefinition).where(
                and_(
                    JobDefinition.organizationId == ctx.organization.id,
                    JobDefinition.key == raw["key"],
                    JobDefinition.id != job_definition_id,
                ),
            ),
        ).scalar_one_or_none()
        if clash is not None:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Job key already in use")
        row.key = raw["key"]
    if "name" in raw:
        row.name = raw["name"]
    if "description" in raw:
        row.description = raw["description"]
    if "requiresApproval" in raw:
        row.requiresApproval = raw["requiresApproval"]
    if "enabled" in raw:
        row.enabled = raw["enabled"]
    row.updatedAt = utc_now()
    db.commit()
    db.refresh(row)
    return {"item": serialize_job_definition(row)}


@router.post("/jobs")
def create_job(
    body: JobCreate,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_write(require_auth_ctx(auth))
    now = utc_now()
    created = JobDefinition(
        id=uuid.uuid4(),
        organizationId=ctx.organization.id,
        key=body.key,
        name=body.name,
        description=body.description,
        requiresApproval=body.requiresApproval if body.requiresApproval is not None else False,
        createdAt=now,
        updatedAt=now,
    )
    db.add(created)
    db.commit()
    db.refresh(created)
    return {"item": serialize_job_definition(created)}


@router.post("/jobs/{key}/run")
def run_job(
    key: str,
    body: JobRunBody,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_write(require_auth_ctx(auth))
    defn = db.execute(
        select(JobDefinition).where(
            and_(
                JobDefinition.organizationId == ctx.organization.id,
                JobDefinition.key == key,
                JobDefinition.enabled.is_(True),
            )
        )
    ).scalar_one_or_none()
    if defn is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    correlation_id = new_correlation_id()
    status_val = Jobrunstatus.APPROVAL_REQUIRED if defn.requiresApproval else Jobrunstatus.PENDING

    if body.idempotencyKey:
        existing = db.execute(
            select(JobRun).where(
                and_(
                    JobRun.organizationId == ctx.organization.id,
                    JobRun.idempotencyKey == body.idempotencyKey,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            return {"item": serialize_job_run(existing), "deduped": True}

    now = utc_now()
    run = JobRun(
        id=uuid.uuid4(),
        organizationId=ctx.organization.id,
        jobDefinitionId=defn.id,
        status=status_val,
        input=to_input_json(body.input) if body.input is not None else None,
        idempotencyKey=body.idempotencyKey,
        correlationId=correlation_id,
        createdAt=now,
        updatedAt=now,
    )
    db.add(run)
    db.flush()

    if not defn.requiresApproval:
        run.status = Jobrunstatus.RUNNING
        run.updatedAt = utc_now()
        db.flush()
        output, log_line = execute_job(db, ctx.organization.id, defn.key, run, defn)
        run.output = to_input_json(output)
        run.logs = log_line
        if output.get("ok") is False:
            run.status = Jobrunstatus.FAILED
        else:
            run.status = Jobrunstatus.SUCCEEDED
        run.updatedAt = utc_now()
        db.flush()
        record_audit(
            db,
            organization_id=ctx.organization.id,
            actor=auth_actor_from_context(ctx),
            action="job_run",
            resourceType="JobRun",
            resourceId=str(run.id),
            correlation_id=correlation_id,
            after=columns_dict(run),
        )
        db.commit()
        updated = (
            db.execute(select(JobRun).where(JobRun.id == run.id).options(joinedload(JobRun.JobDefinition_)))
            .unique()
            .scalar_one()
        )
        return {"item": serialize_job_run(updated), "correlationId": correlation_id}

    record_audit(
        db,
        organization_id=ctx.organization.id,
        actor=auth_actor_from_context(ctx),
        action="job_run_pending_approval",
        resourceType="JobRun",
        resourceId=str(run.id),
        correlation_id=correlation_id,
        after=columns_dict(run),
    )
    db.commit()
    updated = (
        db.execute(select(JobRun).where(JobRun.id == run.id).options(joinedload(JobRun.JobDefinition_)))
        .unique()
        .scalar_one()
    )
    return {
        "item": serialize_job_run(updated),
        "correlationId": correlation_id,
        "message": "Approval required before execution.",
    }


@router.get("/job-runs")
def list_job_runs(
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, list[dict[str, object]]]:
    ctx = require_auth_ctx(auth)
    items = (
        db.execute(
            select(JobRun)
            .where(JobRun.organizationId == ctx.organization.id)
            .options(joinedload(JobRun.JobDefinition_))
            .order_by(JobRun.createdAt.desc())
            .limit(100)
        )
        .unique()
        .scalars()
        .all()
    )
    return {"items": [serialize_job_run(i) for i in items]}


@router.post("/change-requests")
def create_change_request(
    body: ChangeRequestCreate,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_write(require_auth_ctx(auth))
    correlation_id = new_correlation_id()
    now = utc_now()
    cr = ChangeRequest(
        id=uuid.uuid4(),
        organizationId=ctx.organization.id,
        title=body.title,
        description=body.description,
        payload=to_input_json(body.payload),
        status=Changerequeststatus.DRAFT,
        correlationId=correlation_id,
        createdAt=now,
        updatedAt=now,
    )
    db.add(cr)
    db.flush()
    record_audit(
        db,
        organization_id=ctx.organization.id,
        actor=auth_actor_from_context(ctx),
        action="create",
        resourceType="ChangeRequest",
        resourceId=str(cr.id),
        correlation_id=correlation_id,
        after=columns_dict(cr),
    )
    db.commit()
    db.refresh(cr)
    return {"item": serialize_change_request(cr), "correlationId": correlation_id}


@router.get("/change-requests")
def list_change_requests(
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, list[dict[str, object]]]:
    ctx = require_auth_ctx(auth)
    items = (
        db.execute(
            select(ChangeRequest)
            .where(ChangeRequest.organizationId == ctx.organization.id)
            .order_by(ChangeRequest.createdAt.desc())
            .limit(100)
        )
        .scalars()
        .all()
    )
    return {"items": [serialize_change_request(i) for i in items]}


@router.get("/services")
def list_services(
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, list[dict[str, object]]]:
    ctx = require_auth_ctx(auth)
    items = (
        db.execute(
            select(ServiceInstance)
            .where(and_(ServiceInstance.organizationId == ctx.organization.id, ServiceInstance.deletedAt.is_(None)))
            .order_by(ServiceInstance.name.asc())
        )
        .scalars()
        .all()
    )
    return {"items": [serialize_service_instance(i) for i in items]}


@router.post("/services")
def create_service(
    body: ServiceCreate,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_write(require_auth_ctx(auth))
    now = utc_now()
    created = ServiceInstance(
        id=uuid.uuid4(),
        organizationId=ctx.organization.id,
        name=body.name,
        serviceType=body.serviceType,
        customerRef=body.customerRef,
        metadata_=to_input_json(body.metadata) if body.metadata is not None else None,
        createdAt=now,
        updatedAt=now,
    )
    db.add(created)
    db.commit()
    db.refresh(created)
    return {"item": serialize_service_instance(created)}


@router.get("/services/{service_id}")
def get_service(
    service_id: uuid.UUID,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_auth_ctx(auth)
    row = db.execute(
        select(ServiceInstance).where(
            and_(ServiceInstance.id == service_id, ServiceInstance.organizationId == ctx.organization.id, ServiceInstance.deletedAt.is_(None)),
        ),
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    return {"item": serialize_service_instance(row)}


@router.patch("/services/{service_id}")
def update_service(
    service_id: uuid.UUID,
    body: ServiceUpdate,
    db: Session = Depends(get_db),
    auth: Annotated[AuthContext | None, Depends(get_auth)] = None,
) -> dict[str, object]:
    ctx = require_write(require_auth_ctx(auth))
    row = db.execute(
        select(ServiceInstance).where(
            and_(ServiceInstance.id == service_id, ServiceInstance.organizationId == ctx.organization.id, ServiceInstance.deletedAt.is_(None)),
        ),
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found")
    raw = body.model_dump(exclude_unset=True)
    if "name" in raw:
        row.name = raw["name"]
    if "serviceType" in raw:
        row.serviceType = raw["serviceType"]
    if "customerRef" in raw:
        row.customerRef = raw["customerRef"]
    if "metadata" in raw:
        row.metadata_ = to_input_json(raw["metadata"]) if raw["metadata"] is not None else None
    row.updatedAt = utc_now()
    db.commit()
    db.refresh(row)
    return {"item": serialize_service_instance(row)}
