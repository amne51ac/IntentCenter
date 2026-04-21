"""Generic list/export/import for extended catalog models."""

from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy import inspect as sa_inspect, select
from sqlalchemy.orm import Session

from nims.auth_context import AuthContext, auth_actor_from_context
from nims.crypto_util import new_correlation_id
from nims.models_generated import (
    Cable,
    Circuit,
    CircuitDiversityGroup,
    CircuitSegment,
    CircuitTermination,
    CircuitType,
    CloudNetwork,
    CloudService,
    Cluster,
    ConsoleConnection,
    ConsolePort,
    ConsoleServerPort,
    Contact,
    Controller,
    Device,
    DeviceBay,
    DeviceFamily,
    DeviceGroup,
    DeviceGroupMember,
    DeviceRedundancyGroup,
    DeviceRedundancyGroupMember,
    DeviceRole,
    DeviceType,
    DynamicGroup,
    FrontPort,
    Interface,
    InterfaceRedundancyGroup,
    InterfaceRedundancyGroupMember,
    InventoryItem,
    IpAddress,
    IpamNamespace,
    LocationType,
    Manufacturer,
    Module,
    ModuleBay,
    ModuleType,
    MplsDomain,
    Organization,
    PowerConnection,
    PowerFeed,
    PowerOutlet,
    PowerPanel,
    PowerPort,
    Prefix,
    Project,
    Provider,
    ProviderNetwork,
    RackElevation,
    RackGroup,
    RackReservation,
    RearPort,
    Rir,
    RouteTarget,
    ServiceInstance,
    SoftwareImageFile,
    SoftwarePlatform,
    SoftwareVersion,
    StatusDefinition,
    Tag,
    TagAssignment,
    Team,
    TenantGroup,
    VirtualChassis,
    VirtualChassisMember,
    VirtualDeviceContext,
    VirtualMachine,
    Vlan,
    VlanGroup,
    Vpn,
    WirelessNetwork,
)
from nims.serialize import columns_dict
from nims.services.audit import record_audit
from nims.timeutil import utc_now

CATALOG_MODELS: dict[str, type] = {
    "Tenant": Organization,
    "DynamicGroup": DynamicGroup,
    "VirtualChassis": VirtualChassis,
    "Controller": Controller,
    "DeviceRedundancyGroup": DeviceRedundancyGroup,
    "InterfaceRedundancyGroup": InterfaceRedundancyGroup,
    "PowerPanel": PowerPanel,
    "PowerFeed": PowerFeed,
    "CloudNetwork": CloudNetwork,
    "CloudService": CloudService,
    "WirelessNetwork": WirelessNetwork,
    "Vpn": Vpn,
    "Cluster": Cluster,
    "VirtualMachine": VirtualMachine,
    "MplsDomain": MplsDomain,
    "DeviceType": DeviceType,
    "ServiceInstance": ServiceInstance,
    "Prefix": Prefix,
    "IpAddress": IpAddress,
    "Vlan": Vlan,
    "Provider": Provider,
    # Global / shared catalog (no organizationId)
    "LocationType": LocationType,
    "Manufacturer": Manufacturer,
    "DeviceRole": DeviceRole,
    "VlanGroup": VlanGroup,
    "CircuitType": CircuitType,
    "Rir": Rir,
    "DeviceFamily": DeviceFamily,
    "SoftwarePlatform": SoftwarePlatform,
    "ModuleType": ModuleType,
    "SoftwareVersion": SoftwareVersion,
    # Org-scoped extras
    "Project": Project,
    "Interface": Interface,
    "Cable": Cable,
    "VirtualChassisMember": VirtualChassisMember,
    "DeviceRedundancyGroupMember": DeviceRedundancyGroupMember,
    "InterfaceRedundancyGroupMember": InterfaceRedundancyGroupMember,
    "CircuitDiversityGroup": CircuitDiversityGroup,
    "CircuitSegment": CircuitSegment,
    "Tag": Tag,
    "TagAssignment": TagAssignment,
    "RouteTarget": RouteTarget,
    "ProviderNetwork": ProviderNetwork,
    "RackGroup": RackGroup,
    "RackReservation": RackReservation,
    "TenantGroup": TenantGroup,
    "Contact": Contact,
    "Team": Team,
    "SoftwareImageFile": SoftwareImageFile,
    "IpamNamespace": IpamNamespace,
    "VirtualDeviceContext": VirtualDeviceContext,
    "DeviceGroup": DeviceGroup,
    "DeviceGroupMember": DeviceGroupMember,
    "FrontPort": FrontPort,
    "RearPort": RearPort,
    "ConsolePort": ConsolePort,
    "ConsoleServerPort": ConsoleServerPort,
    "PowerPort": PowerPort,
    "PowerOutlet": PowerOutlet,
    "DeviceBay": DeviceBay,
    "ModuleBay": ModuleBay,
    "InventoryItem": InventoryItem,
    "Module": Module,
    "ConsoleConnection": ConsoleConnection,
    "PowerConnection": PowerConnection,
    "CircuitTermination": CircuitTermination,
    "RackElevation": RackElevation,
    "StatusDefinition": StatusDefinition,
}

_GLOBAL_CATALOG_TYPES = frozenset(
    {
        "DeviceType",
        "LocationType",
        "Manufacturer",
        "DeviceRole",
        "VlanGroup",
        "CircuitType",
        "Rir",
        "DeviceFamily",
        "SoftwarePlatform",
        "ModuleType",
        "SoftwareVersion",
    },
)

CATALOG_TYPES: frozenset[str] = frozenset(CATALOG_MODELS.keys())


def _cable_ids_visible_to_org(db: Session, organization_id: uuid.UUID) -> set[uuid.UUID]:
    q_a = (
        select(Cable.id)
        .join(Interface, Cable.interfaceAId == Interface.id)
        .join(Device, Interface.deviceId == Device.id)
        .where(Device.organizationId == organization_id)
    )
    q_b = (
        select(Cable.id)
        .join(Interface, Cable.interfaceBId == Interface.id)
        .join(Device, Interface.deviceId == Device.id)
        .where(Device.organizationId == organization_id)
    )
    a = {r[0] for r in db.execute(q_a).all()}
    b = {r[0] for r in db.execute(q_b).all()}
    return a | b


def list_catalog_items(db: Session, organization_id: uuid.UUID, resource_type: str) -> list[dict[str, Any]]:
    rt = resource_type.strip()
    if rt not in CATALOG_MODELS:
        raise ValueError(f"Unknown catalog type: {rt}")
    if rt == "Tenant":
        org = db.execute(select(Organization).where(Organization.id == organization_id)).scalar_one_or_none()
        if org is None:
            return []
        return [columns_dict(org)]
    model = CATALOG_MODELS[rt]
    if rt in _GLOBAL_CATALOG_TYPES:
        if hasattr(model, "name"):
            order_col = model.name.asc()
        elif hasattr(model, "version"):
            order_col = model.version.asc()
        else:
            order_col = model.id.asc()
        rows = db.execute(select(model).order_by(order_col)).scalars().all()
        return [columns_dict(x) for x in rows]
    if rt == "Project":
        q = (
            select(Project)
            .where(Project.organizationId == organization_id)
            .where(Project.deletedAt.is_(None))
            .order_by(Project.name.asc())
        )
        rows = db.execute(q).scalars().all()
        return [columns_dict(x) for x in rows]
    if rt == "Interface":
        q = (
            select(Interface)
            .join(Device, Interface.deviceId == Device.id)
            .where(Device.organizationId == organization_id)
            .where(Interface.deletedAt.is_(None))
            .order_by(Interface.name.asc())
        )
        rows = db.execute(q).scalars().all()
        return [columns_dict(x) for x in rows]
    if rt == "Cable":
        ids = _cable_ids_visible_to_org(db, organization_id)
        if not ids:
            return []
        rows = db.execute(select(Cable).where(Cable.id.in_(ids)).order_by(Cable.id.asc())).scalars().all()
        return [columns_dict(x) for x in rows]
    if rt == "VirtualChassisMember":
        q = (
            select(VirtualChassisMember)
            .join(VirtualChassis, VirtualChassisMember.virtualChassisId == VirtualChassis.id)
            .where(VirtualChassis.organizationId == organization_id)
            .order_by(VirtualChassisMember.virtualChassisId.asc(), VirtualChassisMember.priority.asc())
        )
        rows = db.execute(q).scalars().all()
        return [columns_dict(x) for x in rows]
    if rt == "DeviceRedundancyGroupMember":
        q = (
            select(DeviceRedundancyGroupMember)
            .join(DeviceRedundancyGroup, DeviceRedundancyGroupMember.groupId == DeviceRedundancyGroup.id)
            .where(DeviceRedundancyGroup.organizationId == organization_id)
            .order_by(DeviceRedundancyGroupMember.groupId.asc(), DeviceRedundancyGroupMember.deviceId.asc())
        )
        rows = db.execute(q).scalars().all()
        return [columns_dict(x) for x in rows]
    if rt == "InterfaceRedundancyGroupMember":
        q = (
            select(InterfaceRedundancyGroupMember)
            .join(InterfaceRedundancyGroup, InterfaceRedundancyGroupMember.groupId == InterfaceRedundancyGroup.id)
            .where(InterfaceRedundancyGroup.organizationId == organization_id)
            .order_by(InterfaceRedundancyGroupMember.groupId.asc(), InterfaceRedundancyGroupMember.interfaceId.asc())
        )
        rows = db.execute(q).scalars().all()
        return [columns_dict(x) for x in rows]
    if rt == "CircuitSegment":
        q = (
            select(CircuitSegment)
            .join(Circuit, CircuitSegment.circuitId == Circuit.id)
            .where(Circuit.organizationId == organization_id)
            .order_by(CircuitSegment.circuitId.asc(), CircuitSegment.segmentIndex.asc())
        )
        rows = db.execute(q).scalars().all()
        return [columns_dict(x) for x in rows]
    if rt == "TagAssignment":
        q = (
            select(TagAssignment)
            .join(Tag, TagAssignment.tagId == Tag.id)
            .where(Tag.organizationId == organization_id)
            .order_by(TagAssignment.resourceType.asc(), TagAssignment.resourceId.asc())
        )
        rows = db.execute(q).scalars().all()
        return [columns_dict(x) for x in rows]
    if rt == "DeviceGroupMember":
        q = (
            select(DeviceGroupMember)
            .join(DeviceGroup, DeviceGroupMember.groupId == DeviceGroup.id)
            .where(DeviceGroup.organizationId == organization_id)
            .order_by(DeviceGroupMember.groupId.asc(), DeviceGroupMember.deviceId.asc())
        )
        rows = db.execute(q).scalars().all()
        return [columns_dict(x) for x in rows]
    if rt in (
        "FrontPort",
        "RearPort",
        "ConsolePort",
        "ConsoleServerPort",
        "PowerPort",
        "PowerOutlet",
        "ModuleBay",
    ):
        sub = {
            "FrontPort": FrontPort,
            "RearPort": RearPort,
            "ConsolePort": ConsolePort,
            "ConsoleServerPort": ConsoleServerPort,
            "PowerPort": PowerPort,
            "PowerOutlet": PowerOutlet,
            "ModuleBay": ModuleBay,
        }[rt]
        q = (
            select(sub)
            .join(Device, sub.deviceId == Device.id)
            .where(Device.organizationId == organization_id)
            .where(sub.deletedAt.is_(None))
            .order_by(sub.name.asc())
        )
        rows = db.execute(q).scalars().all()
        return [columns_dict(x) for x in rows]
    if rt == "VirtualDeviceContext":
        q = (
            select(VirtualDeviceContext)
            .join(Device, VirtualDeviceContext.deviceId == Device.id)
            .where(Device.organizationId == organization_id)
            .where(VirtualDeviceContext.deletedAt.is_(None))
            .order_by(VirtualDeviceContext.name.asc())
        )
        rows = db.execute(q).scalars().all()
        return [columns_dict(x) for x in rows]
    if rt == "DeviceBay":
        q = (
            select(DeviceBay)
            .join(Device, DeviceBay.parentDeviceId == Device.id)
            .where(Device.organizationId == organization_id)
            .where(DeviceBay.deletedAt.is_(None))
            .order_by(DeviceBay.name.asc())
        )
        rows = db.execute(q).scalars().all()
        return [columns_dict(x) for x in rows]
    q = select(model).where(model.organizationId == organization_id)
    if hasattr(model, "deletedAt"):
        q = q.where(model.deletedAt.is_(None))
    if hasattr(model, "name"):
        q = q.order_by(model.name.asc())
    else:
        q = q.order_by(model.id.asc())
    rows = db.execute(q).scalars().all()
    return [columns_dict(x) for x in rows]


def _headers_from_model(model_cls: type) -> list[str]:
    return sorted({c.key for c in sa_inspect(model_cls).mapper.column_attrs})


def row_for_csv(d: dict[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in d.items():
        if v is None:
            out[k] = ""
        elif isinstance(v, (dict, list)):
            out[k] = json.dumps(v, default=str)
        else:
            out[k] = str(v)
    return out


def catalog_export_rows(
    db: Session,
    organization_id: uuid.UUID,
    resource_type: str,
    template: bool,
) -> tuple[list[str], list[dict[str, Any]]]:
    rt = resource_type.strip()
    model = CATALOG_MODELS.get(rt)
    if model is None:
        raise ValueError(rt)
    headers = _headers_from_model(model)
    if template:
        return headers, []
    items = list_catalog_items(db, organization_id, rt)
    rows_out: list[dict[str, Any]] = []
    for d in items:
        rows_out.append({h: d.get(h) for h in headers})
    return headers, rows_out


def _parse_cell(model_cls: type, key: str, raw: Any) -> Any:
    if raw is None:
        return None
    if isinstance(raw, str) and raw.strip() == "":
        return None
    insp = sa_inspect(model_cls)
    col = insp.mapper.columns.get(key)
    if col is None:
        return raw
    t = col.type
    tn = type(t).__name__
    if "Uuid" in tn or "UUID" in tn:
        return uuid.UUID(str(raw))
    if "Integer" in tn or "SmallInteger" in tn:
        return int(raw)
    if "Boolean" in tn:
        return str(raw).lower() in ("1", "true", "yes", "y")
    if "JSON" in tn or "JSONB" in tn:
        if isinstance(raw, (dict, list)):
            return raw
        s = str(raw).strip()
        if not s:
            return None
        return json.loads(s)
    return raw


def _instance_from_row(model_cls: type, row: dict[str, Any], organization_id: uuid.UUID, now: Any) -> Any:
    insp = sa_inspect(model_cls)
    kwargs: dict[str, Any] = {}
    for col in insp.mapper.column_attrs:
        key = col.key
        if key == "id":
            continue
        if key == "organizationId" and hasattr(model_cls, "organizationId"):
            kwargs[key] = organization_id
            continue
        if key in ("createdAt", "updatedAt"):
            kwargs[key] = now
            continue
        if key == "deletedAt":
            kwargs[key] = None
            continue
        if key not in row:
            continue
        kwargs[key] = _parse_cell(model_cls, key, row[key])

    if model_cls is DynamicGroup and kwargs.get("definition") is None:
        kwargs["definition"] = {}

    return model_cls(id=uuid.uuid4(), **kwargs)


def catalog_import_rows(
    db: Session,
    ctx: AuthContext,
    resource_type: str,
    rows: list[dict[str, Any]],
    skip_errors: bool,
) -> tuple[int, list[dict[str, Any]]]:
    rt = resource_type.strip()
    if rt == "Tenant":
        raise ValueError("Import not supported for Tenant")
    model = CATALOG_MODELS.get(rt)
    if model is None:
        raise ValueError(rt)
    oid = ctx.organization.id
    now = utc_now()
    created = 0
    errors: list[dict[str, Any]] = []

    for i, row in enumerate(rows):
        try:
            if rt == "DeviceType":
                inst = DeviceType(
                    id=uuid.uuid4(),
                    manufacturerId=uuid.UUID(str(row["manufacturerId"])),
                    model=str(row.get("model", "")).strip(),
                    uHeight=int(row.get("uHeight") or 1),
                )
            else:
                inst = _instance_from_row(model, row, oid, now)
            db.add(inst)
            db.flush()
            record_audit(
                db,
                organization_id=oid,
                actor=auth_actor_from_context(ctx),
                action="bulk_import",
                resource_type=rt,
                resource_id=str(inst.id),
                correlation_id=new_correlation_id(),
                after=columns_dict(inst),
            )
            db.commit()
            created += 1
        except Exception as e:  # noqa: BLE001
            db.rollback()
            errors.append({"index": i, "error": str(e)})
            if not skip_errors:
                raise e
    return created, errors


PATCH_BLOCKED = frozenset({"id", "createdAt", "organizationId"})


def fetch_catalog_row_for_org(
    db: Session,
    organization_id: uuid.UUID,
    resource_type: str,
    item_id: uuid.UUID,
) -> Any | None:
    """Load one catalog row if it belongs to the org (or is global catalog)."""
    rt = resource_type.strip()
    if rt not in CATALOG_MODELS or rt == "Tenant":
        return None
    model = CATALOG_MODELS[rt]
    if rt in _GLOBAL_CATALOG_TYPES:
        return db.execute(select(model).where(model.id == item_id)).scalar_one_or_none()
    if hasattr(model, "organizationId"):
        q = select(model).where(model.id == item_id, model.organizationId == organization_id)
        if hasattr(model, "deletedAt"):
            q = q.where(model.deletedAt.is_(None))
        return db.execute(q).scalar_one_or_none()
    for row in list_catalog_items(db, organization_id, rt):
        if str(row.get("id")) == str(item_id):
            return db.get(model, item_id)
    return None


def patch_catalog_row(
    db: Session,
    ctx: AuthContext,
    resource_type: str,
    item_id: uuid.UUID,
    body: dict[str, Any],
) -> dict[str, Any]:
    """Partial update for catalog rows; blocked keys are ignored."""
    rt = resource_type.strip()
    if rt not in CATALOG_MODELS or rt == "Tenant":
        raise ValueError("unsupported resource type")
    inst = fetch_catalog_row_for_org(db, ctx.organization.id, rt, item_id)
    if inst is None:
        raise ValueError("not found")
    model = CATALOG_MODELS[rt]
    before = columns_dict(inst)
    for k, v in body.items():
        if k in PATCH_BLOCKED:
            continue
        attr = "metadata_" if k == "metadata" and hasattr(inst, "metadata_") else k
        if not hasattr(inst, attr):
            continue
        setattr(inst, attr, _parse_cell(model, attr, v))
    if hasattr(inst, "updatedAt"):
        inst.updatedAt = utc_now()
    correlation_id = new_correlation_id()
    record_audit(
        db,
        organization_id=ctx.organization.id,
        actor=auth_actor_from_context(ctx),
        action="update",
        resource_type=rt,
        resource_id=str(item_id),
        correlation_id=correlation_id,
        before=before,
        after=columns_dict(inst),
    )
    db.commit()
    db.refresh(inst)
    return columns_dict(inst)
