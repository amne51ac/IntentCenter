from __future__ import annotations

import datetime
import enum
import uuid
from typing import Any

from sqlalchemy.inspection import inspect as sa_inspect

from nims.models_generated import (
    Cable,
    ChangeRequest,
    Circuit,
    CircuitDiversityGroup,
    CircuitSegment,
    CircuitTermination,
    Device,
    DeviceRole,
    DeviceType,
    Interface,
    IpAddress,
    JobDefinition,
    JobRun,
    Location,
    LocationType,
    Manufacturer,
    ObservedResourceState,
    Prefix,
    Provider,
    Rack,
    ServiceInstance,
    Vlan,
    Vrf,
)


def j(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, uuid.UUID):
        return str(v)
    if isinstance(v, datetime.datetime):
        return v.isoformat()
    if isinstance(v, enum.Enum):
        return v.value
    if isinstance(v, dict):
        return {k: j(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [j(x) for x in v]
    return v


def columns_dict(inst: Any) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for col in sa_inspect(inst).mapper.column_attrs:
        key = col.key
        val = getattr(inst, key)
        if key == "metadata_":
            out["metadata"] = j(val)
        else:
            out[key] = j(val)
    return out


def serialize_location_type(lt: LocationType) -> dict[str, Any]:
    return columns_dict(lt)


def serialize_manufacturer(m: Manufacturer) -> dict[str, Any]:
    return columns_dict(m)


def serialize_device_type(dt: DeviceType) -> dict[str, Any]:
    out = columns_dict(dt)
    out["manufacturer"] = serialize_manufacturer(dt.Manufacturer_)
    return out


def serialize_device_role(dr: DeviceRole) -> dict[str, Any]:
    return columns_dict(dr)


def serialize_location(loc: Location) -> dict[str, Any]:
    """Match Prisma `include: { locationType: true, parent: true }` (single parent hop)."""
    out = columns_dict(loc)
    out["locationType"] = serialize_location_type(loc.LocationType_)
    par = loc.Location
    if par is not None:
        out["parent"] = {
            **columns_dict(par),
            "locationType": serialize_location_type(par.LocationType_),
            "parent": None,
        }
    else:
        out["parent"] = None
    return out


def serialize_rack(r: Rack) -> dict[str, Any]:
    out = columns_dict(r)
    out["location"] = serialize_location(r.Location_)
    return out


def serialize_interface(i: Interface) -> dict[str, Any]:
    return columns_dict(i)


def serialize_device_summary(d: Device) -> dict[str, Any]:
    out = columns_dict(d)
    out["deviceType"] = serialize_device_type(d.DeviceType_)
    out["deviceRole"] = serialize_device_role(d.DeviceRole_)
    if d.Rack_ is not None:
        out["rack"] = serialize_rack(d.Rack_)
    else:
        out["rack"] = None
    return out


def serialize_device_full(d: Device) -> dict[str, Any]:
    out = serialize_device_summary(d)
    ifaces = [i for i in d.Interface if i.deletedAt is None]
    out["interfaces"] = [serialize_interface(i) for i in sorted(ifaces, key=lambda x: x.name)]
    out["observed"] = [serialize_observed(s) for s in d.ObservedResourceState]
    return out


def serialize_cable(c: Cable) -> dict[str, Any]:
    return columns_dict(c)


def serialize_prefix(p: Prefix) -> dict[str, Any]:
    out = columns_dict(p)
    out["vrf"] = columns_dict(p.Vrf_)
    return out


def serialize_ip_address(ia: IpAddress) -> dict[str, Any]:
    out = columns_dict(ia)
    out["prefix"] = columns_dict(ia.Prefix_)
    if ia.Interface_ is not None:
        iface = ia.Interface_
        iface_out = serialize_interface(iface)
        iface_out["device"] = columns_dict(iface.Device_)
        out["interface"] = iface_out
    else:
        out["interface"] = None
    return out


def serialize_vlan(v: Vlan) -> dict[str, Any]:
    out = columns_dict(v)
    if v.VlanGroup_ is not None:
        out["vlanGroup"] = columns_dict(v.VlanGroup_)
    else:
        out["vlanGroup"] = None
    return out


def serialize_vrf(v: Vrf) -> dict[str, Any]:
    return columns_dict(v)


def serialize_provider(p: Provider) -> dict[str, Any]:
    return columns_dict(p)


def serialize_circuit_diversity_group(g: CircuitDiversityGroup) -> dict[str, Any]:
    return columns_dict(g)


def serialize_circuit_segment(seg: CircuitSegment, fallback_provider: Provider) -> dict[str, Any]:
    out = columns_dict(seg)
    prov = seg.Provider_ or fallback_provider
    out["provider"] = serialize_provider(prov)
    return out


def serialize_circuit_termination(t: CircuitTermination) -> dict[str, Any]:
    out = columns_dict(t)
    out["location"] = columns_dict(t.Location_) if t.Location_ is not None else None
    return out


def serialize_circuit(c: Circuit) -> dict[str, Any]:
    out = columns_dict(c)
    out["circuitDiversityGroup"] = (
        serialize_circuit_diversity_group(c.CircuitDiversityGroup_) if c.CircuitDiversityGroup_ is not None else None
    )
    out["provider"] = serialize_provider(c.Provider_)
    segs = sorted(c.CircuitSegment, key=lambda s: s.segmentIndex)
    out["segments"] = [serialize_circuit_segment(s, c.Provider_) for s in segs]
    terms = sorted(
        c.CircuitTermination,
        key=lambda t: (0 if (t.side or "").upper() == "A" else 1 if (t.side or "").upper() == "Z" else 2, t.side or ""),
    )
    out["terminations"] = [serialize_circuit_termination(t) for t in terms]
    return out


def serialize_job_definition(jd: JobDefinition) -> dict[str, Any]:
    return columns_dict(jd)


def serialize_job_run(jr: JobRun) -> dict[str, Any]:
    out = columns_dict(jr)
    out["jobDefinition"] = serialize_job_definition(jr.JobDefinition_)
    return out


def serialize_change_request(cr: ChangeRequest) -> dict[str, Any]:
    return columns_dict(cr)


def serialize_service_instance(si: ServiceInstance) -> dict[str, Any]:
    return columns_dict(si)


def serialize_observed(o: ObservedResourceState) -> dict[str, Any]:
    out = columns_dict(o)
    if o.Device_ is not None:
        out["device"] = columns_dict(o.Device_)
    else:
        out["device"] = None
    return out


def serialize_audit_event(row: Any) -> dict[str, Any]:
    return columns_dict(row)


def serialize_plugin(row: Any) -> dict[str, Any]:
    return columns_dict(row)
