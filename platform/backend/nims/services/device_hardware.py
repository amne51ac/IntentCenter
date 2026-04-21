"""Slots (ModuleBay), cards (Module), and ports on a device — nested tree for the object view UI."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import and_, nulls_last, select
from sqlalchemy.orm import Session

from nims.models_generated import Device, FrontPort, Module, ModuleBay, ModuleType


def _bay_dict(b: ModuleBay) -> dict[str, Any]:
    return {
        "id": str(b.id),
        "name": b.name,
        "position": b.position,
    }


def _card_dict(m: Module, mt: ModuleType | None) -> dict[str, Any]:
    out: dict[str, Any] = {
        "id": str(m.id),
        "serial": m.serial,
        "moduleTypeId": str(m.moduleTypeId),
    }
    if mt:
        out["moduleType"] = {"id": str(mt.id), "model": mt.model, "partNumber": mt.partNumber}
    return out


def _port_dict(p: FrontPort) -> dict[str, Any]:
    return {"id": str(p.id), "name": p.name, "label": p.label, "type": p.type}


def _slots_under_module(
    db: Session,
    organization_id: uuid.UUID,
    module_id: uuid.UUID,
) -> list[dict[str, Any]]:
    bays = (
        db.execute(
            select(ModuleBay)
            .join(Module, ModuleBay.parentModuleId == Module.id)
            .where(
                and_(
                    ModuleBay.parentModuleId == module_id,
                    Module.organizationId == organization_id,
                    ModuleBay.deletedAt.is_(None),
                ),
            )
            .order_by(nulls_last(ModuleBay.position.asc()), ModuleBay.name.asc()),
        )
        .scalars()
        .all()
    )
    return [_slot_payload(db, organization_id, b) for b in bays]


def _slot_payload(db: Session, organization_id: uuid.UUID, bay: ModuleBay) -> dict[str, Any]:
    card = db.execute(select(Module).where(Module.moduleBayId == bay.id, Module.deletedAt.is_(None))).scalar_one_or_none()
    payload: dict[str, Any] = {"bay": _bay_dict(bay), "card": None}
    if card is None:
        return payload
    mt = db.get(ModuleType, card.moduleTypeId)
    if card.organizationId != organization_id:
        return payload
    c = _card_dict(card, mt)
    c["slots"] = _slots_under_module(db, organization_id, card.id)
    c["frontPorts"] = [
        _port_dict(p)
        for p in db.execute(
            select(FrontPort).where(
                and_(FrontPort.moduleId == card.id, FrontPort.deviceId == card.deviceId, FrontPort.deletedAt.is_(None)),
            ),
        )
        .scalars()
        .all()
    ]
    payload["card"] = c
    return payload


def build_device_hardware_tree(db: Session, organization_id: uuid.UUID, device_id: uuid.UUID) -> dict[str, Any] | None:
    """Return nested slots/cards/ports for a device, or None if device missing."""
    d = db.execute(
        select(Device).where(
            and_(Device.id == device_id, Device.organizationId == organization_id, Device.deletedAt.is_(None)),
        ),
    ).scalar_one_or_none()
    if d is None:
        return None

    root_bays = (
        db.execute(
            select(ModuleBay).where(
                and_(ModuleBay.deviceId == device_id, ModuleBay.deletedAt.is_(None)),
            ).order_by(nulls_last(ModuleBay.position.asc()), ModuleBay.name.asc()),
        )
        .scalars()
        .all()
    )

    chassis_ports = [
        _port_dict(p)
        for p in db.execute(
            select(FrontPort).where(
                and_(FrontPort.deviceId == device_id, FrontPort.moduleId.is_(None), FrontPort.deletedAt.is_(None)),
            ).order_by(FrontPort.name.asc()),
        )
        .scalars()
        .all()
    ]

    return {
        "deviceId": str(d.id),
        "deviceName": d.name,
        "chassisFrontPorts": chassis_ports,
        "slots": [_slot_payload(db, organization_id, b) for b in root_bays],
    }
