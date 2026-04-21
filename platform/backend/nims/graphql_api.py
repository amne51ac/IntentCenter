import uuid
from typing import Any

import strawberry
from sqlalchemy import select
from sqlalchemy.orm import Session
from strawberry.fastapi import GraphQLRouter

from nims.crypto_util import hash_token
from nims.db import SessionLocal
from nims.deps import resolve_auth
from nims.models_generated import ApiToken, Device, IpAddress, Location, Organization, Prefix, Rack


@strawberry.type
class GqlOrganization:
    id: strawberry.ID
    name: str
    slug: str


@strawberry.type
class GqlLocation:
    id: strawberry.ID
    name: str
    slug: str
    parentId: strawberry.ID | None


@strawberry.type
class GqlRack:
    id: strawberry.ID
    name: str
    uHeight: int
    locationId: strawberry.ID


@strawberry.type
class GqlDevice:
    id: strawberry.ID
    name: str
    status: str
    rackId: strawberry.ID | None


@strawberry.type
class GqlPrefix:
    id: strawberry.ID
    cidr: str
    vrfId: strawberry.ID


@strawberry.type
class GqlIpAddress:
    id: strawberry.ID
    address: str
    prefixId: strawberry.ID


@strawberry.type
class Query:
    @strawberry.field
    def organization(self, info: strawberry.Info) -> GqlOrganization | None:
        db: Session = info.context["db"]
        org_id: str | None = info.context.get("org_id")
        if not org_id:
            return None
        oid = uuid.UUID(org_id)
        row = db.execute(select(Organization).where(Organization.id == oid)).scalar_one_or_none()
        if row is None:
            return None
        return GqlOrganization(id=str(row.id), name=row.name, slug=row.slug)

    @strawberry.field
    def locations(self, info: strawberry.Info) -> list[GqlLocation]:
        db: Session = info.context["db"]
        org_id: str | None = info.context.get("org_id")
        if not org_id:
            return []
        oid = uuid.UUID(org_id)
        rows = (
            db.execute(
                select(Location)
                .where(Location.organizationId == oid, Location.deletedAt.is_(None))
                .order_by(Location.name.asc())
            )
            .scalars()
            .all()
        )
        return [
            GqlLocation(
                id=str(r.id),
                name=r.name,
                slug=r.slug,
                parentId=str(r.parentId) if r.parentId else None,
            )
            for r in rows
        ]

    @strawberry.field
    def racks(self, info: strawberry.Info) -> list[GqlRack]:
        db: Session = info.context["db"]
        org_id: str | None = info.context.get("org_id")
        if not org_id:
            return []
        oid = uuid.UUID(org_id)
        rows = (
            db.execute(
                select(Rack).where(Rack.organizationId == oid, Rack.deletedAt.is_(None)).order_by(Rack.name.asc())
            )
            .scalars()
            .all()
        )
        return [
            GqlRack(
                id=str(r.id),
                name=r.name,
                uHeight=r.uHeight,
                locationId=str(r.locationId),
            )
            for r in rows
        ]

    @strawberry.field
    def devices(self, info: strawberry.Info) -> list[GqlDevice]:
        db: Session = info.context["db"]
        org_id: str | None = info.context.get("org_id")
        if not org_id:
            return []
        oid = uuid.UUID(org_id)
        rows = (
            db.execute(
                select(Device)
                .where(Device.organizationId == oid, Device.deletedAt.is_(None))
                .order_by(Device.name.asc())
            )
            .scalars()
            .all()
        )
        return [
            GqlDevice(
                id=str(r.id),
                name=r.name,
                status=r.status.value,
                rackId=str(r.rackId) if r.rackId else None,
            )
            for r in rows
        ]

    @strawberry.field
    def prefixes(self, info: strawberry.Info) -> list[GqlPrefix]:
        db: Session = info.context["db"]
        org_id: str | None = info.context.get("org_id")
        if not org_id:
            return []
        oid = uuid.UUID(org_id)
        rows = (
            db.execute(
                select(Prefix)
                .where(Prefix.organizationId == oid, Prefix.deletedAt.is_(None))
                .order_by(Prefix.cidr.asc())
            )
            .scalars()
            .all()
        )
        return [GqlPrefix(id=str(r.id), cidr=r.cidr, vrfId=str(r.vrfId)) for r in rows]

    @strawberry.field
    def ipAddresses(self, info: strawberry.Info) -> list[GqlIpAddress]:
        db: Session = info.context["db"]
        org_id: str | None = info.context.get("org_id")
        if not org_id:
            return []
        oid = uuid.UUID(org_id)
        rows = (
            db.execute(
                select(IpAddress)
                .where(IpAddress.organizationId == oid, IpAddress.deletedAt.is_(None))
                .order_by(IpAddress.address.asc())
                .limit(500)
            )
            .scalars()
            .all()
        )
        return [
            GqlIpAddress(
                id=str(r.id),
                address=r.address,
                prefixId=str(r.prefixId),
            )
            for r in rows
        ]


schema = strawberry.Schema(query=Query)


async def graphql_context(request: Any) -> dict[str, Any]:
    db = SessionLocal()
    request.state.graphql_db = db
    auth = resolve_auth(db, request)
    org_id: str | None = None
    if auth and auth.organization:
        org_id = str(auth.organization.id)
    else:
        h = request.headers.get("authorization")
        if h and h.startswith("Bearer "):
            raw = h[7:].strip()
            tok = db.execute(select(ApiToken).where(ApiToken.tokenHash == hash_token(raw))).scalar_one_or_none()
            if tok is not None:
                org_id = str(tok.organizationId)
    return {"request": request, "db": db, "org_id": org_id}


graphql_router = GraphQLRouter(
    schema,
    context_getter=graphql_context,
)
