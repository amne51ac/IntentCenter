"""Load a single inventory object as a flat dict for the resource view page."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import and_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from nims.models_generated import (
    Cable,
    ChangeRequest,
    Circuit,
    CircuitSegment,
    CircuitTermination,
    ConsolePort,
    ConsoleServerPort,
    Device,
    DeviceBay,
    DeviceGroup,
    DeviceGroupMember,
    DeviceRedundancyGroup,
    DeviceRedundancyGroupMember,
    FrontPort,
    Interface,
    InterfaceRedundancyGroup,
    InterfaceRedundancyGroupMember,
    JobDefinition,
    JobRun,
    Location,
    Module,
    ModuleBay,
    ObjectTemplate,
    Organization,
    PowerOutlet,
    PowerPort,
    Rack,
    RearPort,
    ServiceInstance,
    Tag,
    TagAssignment,
    VirtualChassis,
    VirtualChassisMember,
    VirtualDeviceContext,
    Vrf,
)
from nims.serialize import columns_dict, serialize_circuit
from nims.services.catalog_io import _GLOBAL_CATALOG_TYPES, CATALOG_MODELS, _cable_ids_visible_to_org


def _cd(inst: Any) -> dict[str, Any]:
    return columns_dict(inst)


def load_resource_instance(
    db: Session,
    organization_id: uuid.UUID,
    resource_type: str,
    resource_id: uuid.UUID,
) -> Any | None:
    """Return the SQLAlchemy model instance for this resource, or None."""
    rt = resource_type.strip()
    if rt == "Service":
        rt = "ServiceInstance"

    if rt == "Tenant":
        if resource_id != organization_id:
            return None
        return db.execute(select(Organization).where(Organization.id == organization_id)).scalar_one_or_none()

    if rt == "Location":
        return db.execute(
            select(Location).where(
                and_(Location.id == resource_id, Location.organizationId == organization_id, Location.deletedAt.is_(None)),
            ),
        ).scalar_one_or_none()

    if rt == "Rack":
        return db.execute(
            select(Rack).where(
                and_(Rack.id == resource_id, Rack.organizationId == organization_id, Rack.deletedAt.is_(None)),
            ),
        ).scalar_one_or_none()

    if rt == "Device":
        return db.execute(
            select(Device).where(
                and_(Device.id == resource_id, Device.organizationId == organization_id, Device.deletedAt.is_(None)),
            ),
        ).scalar_one_or_none()

    if rt == "Vrf":
        return db.execute(
            select(Vrf).where(
                and_(Vrf.id == resource_id, Vrf.organizationId == organization_id, Vrf.deletedAt.is_(None)),
            ),
        ).scalar_one_or_none()

    if rt == "JobDefinition":
        return db.execute(
            select(JobDefinition).where(
                and_(JobDefinition.id == resource_id, JobDefinition.organizationId == organization_id),
            ),
        ).scalar_one_or_none()

    if rt == "JobRun":
        return db.execute(
            select(JobRun).where(and_(JobRun.id == resource_id, JobRun.organizationId == organization_id)),
        ).scalar_one_or_none()

    if rt == "ServiceInstance":
        return db.execute(
            select(ServiceInstance).where(
                and_(
                    ServiceInstance.id == resource_id,
                    ServiceInstance.organizationId == organization_id,
                    ServiceInstance.deletedAt.is_(None),
                ),
            ),
        ).scalar_one_or_none()

    if rt == "Circuit":
        return db.execute(
            select(Circuit).where(
                and_(Circuit.id == resource_id, Circuit.organizationId == organization_id, Circuit.deletedAt.is_(None)),
            ),
        ).scalar_one_or_none()

    if rt == "ChangeRequest":
        return db.execute(
            select(ChangeRequest).where(
                and_(ChangeRequest.id == resource_id, ChangeRequest.organizationId == organization_id),
            ),
        ).scalar_one_or_none()

    if rt == "ObjectTemplate":
        return db.execute(
            select(ObjectTemplate).where(ObjectTemplate.id == resource_id, ObjectTemplate.organizationId == organization_id),
        ).scalar_one_or_none()

    if rt == "Cable":
        visible = _cable_ids_visible_to_org(db, organization_id)
        if resource_id not in visible:
            return None
        return db.execute(select(Cable).where(Cable.id == resource_id)).scalar_one_or_none()

    if rt == "Interface":
        return db.execute(
            select(Interface)
            .join(Device, Interface.deviceId == Device.id)
            .where(
                and_(
                    Interface.id == resource_id,
                    Device.organizationId == organization_id,
                    Interface.deletedAt.is_(None),
                ),
            ),
        ).scalar_one_or_none()

    if rt == "CircuitSegment":
        return db.execute(
            select(CircuitSegment)
            .join(Circuit, CircuitSegment.circuitId == Circuit.id)
            .where(CircuitSegment.id == resource_id, Circuit.organizationId == organization_id),
        ).scalar_one_or_none()

    if rt == "VirtualChassisMember":
        return db.execute(
            select(VirtualChassisMember)
            .join(VirtualChassis, VirtualChassisMember.virtualChassisId == VirtualChassis.id)
            .where(VirtualChassisMember.id == resource_id, VirtualChassis.organizationId == organization_id),
        ).scalar_one_or_none()

    if rt == "DeviceRedundancyGroupMember":
        return db.execute(
            select(DeviceRedundancyGroupMember)
            .join(DeviceRedundancyGroup, DeviceRedundancyGroupMember.groupId == DeviceRedundancyGroup.id)
            .where(DeviceRedundancyGroupMember.id == resource_id, DeviceRedundancyGroup.organizationId == organization_id),
        ).scalar_one_or_none()

    if rt == "InterfaceRedundancyGroupMember":
        return db.execute(
            select(InterfaceRedundancyGroupMember)
            .join(InterfaceRedundancyGroup, InterfaceRedundancyGroupMember.groupId == InterfaceRedundancyGroup.id)
            .where(InterfaceRedundancyGroupMember.id == resource_id, InterfaceRedundancyGroup.organizationId == organization_id),
        ).scalar_one_or_none()

    if rt == "TagAssignment":
        return db.execute(
            select(TagAssignment)
            .join(Tag, TagAssignment.tagId == Tag.id)
            .where(TagAssignment.id == resource_id, Tag.organizationId == organization_id),
        ).scalar_one_or_none()

    if rt == "DeviceGroupMember":
        return db.execute(
            select(DeviceGroupMember)
            .join(DeviceGroup, DeviceGroupMember.groupId == DeviceGroup.id)
            .where(DeviceGroupMember.id == resource_id, DeviceGroup.organizationId == organization_id),
        ).scalar_one_or_none()

    if rt == "FrontPort":
        return db.execute(
            select(FrontPort)
            .join(Device, FrontPort.deviceId == Device.id)
            .where(FrontPort.id == resource_id, Device.organizationId == organization_id),
        ).scalar_one_or_none()

    if rt == "RearPort":
        return db.execute(
            select(RearPort)
            .join(Device, RearPort.deviceId == Device.id)
            .where(RearPort.id == resource_id, Device.organizationId == organization_id),
        ).scalar_one_or_none()

    if rt == "ConsolePort":
        return db.execute(
            select(ConsolePort)
            .join(Device, ConsolePort.deviceId == Device.id)
            .where(ConsolePort.id == resource_id, Device.organizationId == organization_id),
        ).scalar_one_or_none()

    if rt == "ConsoleServerPort":
        return db.execute(
            select(ConsoleServerPort)
            .join(Device, ConsoleServerPort.deviceId == Device.id)
            .where(ConsoleServerPort.id == resource_id, Device.organizationId == organization_id),
        ).scalar_one_or_none()

    if rt == "PowerPort":
        return db.execute(
            select(PowerPort)
            .join(Device, PowerPort.deviceId == Device.id)
            .where(PowerPort.id == resource_id, Device.organizationId == organization_id),
        ).scalar_one_or_none()

    if rt == "PowerOutlet":
        return db.execute(
            select(PowerOutlet)
            .join(Device, PowerOutlet.deviceId == Device.id)
            .where(PowerOutlet.id == resource_id, Device.organizationId == organization_id),
        ).scalar_one_or_none()

    if rt == "ModuleBay":
        mb = db.get(ModuleBay, resource_id)
        if mb is None or mb.deletedAt is not None:
            return None
        if mb.deviceId is not None:
            d = db.get(Device, mb.deviceId)
            return mb if d and d.organizationId == organization_id and d.deletedAt is None else None
        if mb.parentModuleId is not None:
            parent = db.get(Module, mb.parentModuleId)
            if parent is None or parent.deletedAt is not None:
                return None
            d = db.get(Device, parent.deviceId)
            return mb if d and d.organizationId == organization_id and d.deletedAt is None else None
        return None

    if rt == "VirtualDeviceContext":
        return db.execute(
            select(VirtualDeviceContext)
            .join(Device, VirtualDeviceContext.deviceId == Device.id)
            .where(VirtualDeviceContext.id == resource_id, Device.organizationId == organization_id),
        ).scalar_one_or_none()

    if rt == "DeviceBay":
        return db.execute(
            select(DeviceBay)
            .join(Device, DeviceBay.parentDeviceId == Device.id)
            .where(DeviceBay.id == resource_id, Device.organizationId == organization_id),
        ).scalar_one_or_none()

    if rt not in CATALOG_MODELS:
        return None

    model = CATALOG_MODELS[rt]
    if rt in _GLOBAL_CATALOG_TYPES:
        return db.execute(select(model).where(model.id == resource_id)).scalar_one_or_none()

    if hasattr(model, "organizationId"):
        q = select(model).where(model.id == resource_id, model.organizationId == organization_id)
        if hasattr(model, "deletedAt"):
            q = q.where(model.deletedAt.is_(None))
        return db.execute(q).scalar_one_or_none()

    return None


def load_resource_item(
    db: Session,
    organization_id: uuid.UUID,
    resource_type: str,
    resource_id: uuid.UUID,
) -> dict[str, Any] | None:
    rt = resource_type.strip()
    if rt == "Service":
        rt = "ServiceInstance"
    if rt == "Circuit":
        c = db.execute(
            select(Circuit)
            .where(
                and_(
                    Circuit.id == resource_id,
                    Circuit.organizationId == organization_id,
                    Circuit.deletedAt.is_(None),
                ),
            )
            .options(
                joinedload(Circuit.Provider_),
                joinedload(Circuit.CircuitDiversityGroup_),
                selectinload(Circuit.CircuitSegment).joinedload(CircuitSegment.Provider_),
                selectinload(Circuit.CircuitTermination).joinedload(CircuitTermination.Location_),
            ),
        ).unique().scalar_one_or_none()
        return serialize_circuit(c) if c is not None else None

    row = load_resource_instance(db, organization_id, resource_type, resource_id)
    return _cd(row) if row else None
