"""Build relationship graph (nodes + edges + tree) for inventory objects."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import and_, or_, select
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.orm import Session, joinedload, selectinload

from nims.models_generated import (
    Cable,
    Circuit,
    CircuitSegment,
    CircuitTermination,
    Device,
    DeviceType,
    FrontPort,
    Interface,
    IpAddress,
    Location,
    Module,
    ModuleBay,
    ModuleType,
    Prefix,
    Provider,
    Rack,
    Vrf,
)
from nims.services.catalog_io import CATALOG_MODELS
from nims.services.resource_item import load_resource_instance

# Richer hand-tuned graphs (keep these first).
_SPECIAL_GRAPH_TYPES = frozenset(
    {
        "Device",
        "Location",
        "Rack",
        "Vrf",
        "Prefix",
        "IpAddress",
        "Interface",
        "Circuit",
        "Provider",
    },
)

_CLASS_TO_API_NAME: dict[str, str] = {}
for _api_name, _model in CATALOG_MODELS.items():
    _CLASS_TO_API_NAME.setdefault(_model.__name__, _api_name)

# Core DCIM / IPAM types exposed by object view routes but not listed in CATALOG_MODELS (catalog uses other keys, e.g. Controller).
for _api_name, _model in (
    ("Device", Device),
    ("Location", Location),
    ("Rack", Rack),
    ("Circuit", Circuit),
    ("Vrf", Vrf),
):
    _CLASS_TO_API_NAME.setdefault(_model.__name__, _api_name)


def _label_for_orm(obj: Any) -> str:
    for key in (
        "name",
        "cid",
        "cidr",
        "address",
        "label",
        "slug",
        "title",
        "filename",
        "displayName",
        "email",
    ):
        v = getattr(obj, key, None)
        if v is not None and str(v).strip():
            return str(v)
    rid = getattr(obj, "id", None)
    return str(rid)[:12] if rid is not None else "?"


def _node_for_catalog_orm(obj: Any) -> tuple[str | None, dict[str, Any] | None]:
    cls_name = obj.__class__.__name__
    api = _CLASS_TO_API_NAME.get(cls_name)
    if api is None:
        return None, None
    rid = getattr(obj, "id", None)
    if rid is None:
        return None, None
    return api, _node(api, rid, _label_for_orm(obj))


def _graph_from_orm_relationships(
    organization_id: uuid.UUID,
    api_resource_type: str,
    inst: Any,
) -> dict[str, Any]:
    """Build nodes/edges by walking SQLAlchemy relationships (covers catalog types without hand-tuned graphs)."""
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    root = _node(api_resource_type, inst.id, _label_for_orm(inst))
    nodes.append(root)

    oid = getattr(inst, "organizationId", None)
    if oid is not None and oid == organization_id:
        org_n = _node("Organization", organization_id, "Organization")
        nodes.append(org_n)
        edges.append(_edge(root, org_n, kind="belongs_to", label="organization"))

    mapper = sa_inspect(inst).mapper
    tree_children: list[dict[str, Any]] = []

    for prop in mapper.relationships:
        key = prop.key
        try:
            related = getattr(inst, key, None)
        except Exception:
            continue
        if related is None:
            continue
        label = key.replace("_", " ")
        if prop.uselist:
            try:
                batch = list(related)[:40]
            except Exception:
                continue
            for child in batch:
                if child is None:
                    continue
                api, sub = _node_for_catalog_orm(child)
                if sub is None or api is None:
                    continue
                nodes.append(sub)
                edges.append(_edge(root, sub, kind=key, label=label))
                tree_children.append({"node": sub, "children": []})
        else:
            api, sub = _node_for_catalog_orm(related)
            if sub is None or api is None:
                continue
            nodes.append(sub)
            edges.append(_edge(root, sub, kind=key, label=label))
            tree_children.insert(0, {"node": sub, "children": []})

    tree = {"node": root, "children": tree_children[:50]}
    return {"root": root, "nodes": _dedupe_nodes(nodes), "edges": edges, "tree": tree}


def _node(resource_type: str, rid: uuid.UUID, label: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    n: dict[str, Any] = {"resourceType": resource_type, "id": str(rid), "label": label}
    if extra:
        n["meta"] = extra
    return n


def _edge(
    fr: dict[str, Any],
    to: dict[str, Any],
    *,
    kind: str,
    label: str | None = None,
) -> dict[str, Any]:
    return {
        "kind": kind,
        "label": label or kind,
        "from": {"resourceType": fr["resourceType"], "id": fr["id"]},
        "to": {"resourceType": to["resourceType"], "id": to["id"]},
    }


def build_relationship_graph(
    db: Session,
    organization_id: uuid.UUID,
    resource_type: str,
    resource_id: uuid.UUID,
) -> dict[str, Any] | None:
    """Return { root, nodes, edges, tree } or None if not found."""
    rt = resource_type.strip()
    if rt == "Service":
        rt = "ServiceInstance"

    if rt in _SPECIAL_GRAPH_TYPES:
        if rt == "Device":
            g = _graph_device(db, organization_id, resource_id)
        elif rt == "Location":
            g = _graph_location(db, organization_id, resource_id)
        elif rt == "Rack":
            g = _graph_rack(db, organization_id, resource_id)
        elif rt == "Vrf":
            g = _graph_vrf(db, organization_id, resource_id)
        elif rt == "Prefix":
            g = _graph_prefix(db, organization_id, resource_id)
        elif rt == "IpAddress":
            g = _graph_ip_address(db, organization_id, resource_id)
        elif rt == "Interface":
            g = _graph_interface(db, organization_id, resource_id)
        elif rt == "Circuit":
            g = _graph_circuit(db, organization_id, resource_id)
        elif rt == "Provider":
            g = _graph_provider(db, organization_id, resource_id)
        else:
            g = None
        if g is not None:
            return g

    inst = load_resource_instance(db, organization_id, rt, resource_id)
    if inst is None:
        return None
    return _graph_from_orm_relationships(organization_id, rt, inst)


def _graph_device(db: Session, organization_id: uuid.UUID, resource_id: uuid.UUID) -> dict[str, Any] | None:
    d = db.execute(
        select(Device)
        .where(
            and_(
                Device.id == resource_id,
                Device.organizationId == organization_id,
                Device.deletedAt.is_(None),
            ),
        )
        .options(
            joinedload(Device.Rack_).joinedload(Rack.Location_),
            joinedload(Device.DeviceType_).joinedload(DeviceType.Manufacturer_),
            joinedload(Device.DeviceRole_),
            joinedload(Device.Interface),
            joinedload(Device.ModuleBay),
            joinedload(Device.Module).joinedload(Module.ModuleType_),
            joinedload(Device.FrontPort),
        ),
    ).unique().scalar_one_or_none()
    if d is None:
        return None
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    root = _node("Device", d.id, d.name, {"status": d.status.value if hasattr(d.status, "value") else str(d.status)})
    nodes.append(root)

    org_node = _node("Organization", organization_id, "Organization")
    nodes.append(org_node)
    edges.append(_edge(root, org_node, kind="belongs_to", label="organization"))

    dt = d.DeviceType_
    if dt:
        n = _node("DeviceType", dt.id, f"{dt.Manufacturer_.name} {dt.model}" if dt.Manufacturer_ else dt.model)
        nodes.append(n)
        edges.append(_edge(root, n, kind="device_type", label="device type"))

    dr = d.DeviceRole_
    if dr:
        n = _node("DeviceRole", dr.id, dr.name)
        nodes.append(n)
        edges.append(_edge(root, n, kind="device_role", label="role"))

    if d.Rack_:
        rk = d.Rack_
        rn = _node("Rack", rk.id, rk.name)
        nodes.append(rn)
        edges.append(_edge(root, rn, kind="in_rack", label="rack"))
        loc = rk.Location_
        if loc:
            ln = _node("Location", loc.id, loc.name)
            nodes.append(ln)
            edges.append(_edge(rn, ln, kind="at_location", label="location"))

    children: list[dict[str, Any]] = []

    def add_nested_slots(
        parent_mod: Module,
        parent_module_label: str,
        parent_tree_children: list[dict[str, Any]],
    ) -> None:
        """Recurse slots on a card (module); edges originate from the parent module node already in `nodes`."""
        pm_node = _node("Module", parent_mod.id, parent_module_label)
        sub_bays = (
            db.execute(
                select(ModuleBay)
                .where(
                    and_(
                        ModuleBay.parentModuleId == parent_mod.id,
                        ModuleBay.deletedAt.is_(None),
                    ),
                )
                .order_by(ModuleBay.name.asc()),
            )
            .scalars()
            .all()
        )
        for sb in sub_bays:
            sbn = _node("ModuleBay", sb.id, sb.name or "slot")
            nodes.append(sbn)
            edges.append(_edge(pm_node, sbn, kind="has_slot", label="slot"))
            sm = db.execute(select(Module).where(Module.moduleBayId == sb.id, Module.deletedAt.is_(None))).scalar_one_or_none()
            sub_children: list[dict[str, Any]] = []
            if sm:
                smt = db.get(ModuleType, sm.moduleTypeId)
                sm_base = f"{smt.model}" if smt else "module"
                sm_label = sm.serial or sm_base
                smn = _node("Module", sm.id, sm_label)
                nodes.append(smn)
                edges.append(_edge(sbn, smn, kind="has_card", label="card"))
                add_nested_slots(sm, sm_label, sub_children)
                for fp in (
                    db.execute(
                        select(FrontPort).where(
                            and_(FrontPort.moduleId == sm.id, FrontPort.deletedAt.is_(None)),
                        ),
                    )
                    .scalars()
                    .all()
                ):
                    pn = _node("FrontPort", fp.id, fp.name)
                    nodes.append(pn)
                    edges.append(_edge(smn, pn, kind="has_front_port", label="front port"))
                    sub_children.append({"node": pn, "children": []})
            parent_tree_children.append({"node": sbn, "children": sub_children})

    for iface in d.Interface or []:
        if iface.deletedAt is not None:
            continue
        inode = _node("Interface", iface.id, iface.name)
        nodes.append(inode)
        edges.append(_edge(root, inode, kind="has_interface", label="interface"))
        children.append({"node": inode, "children": []})

    for bay in d.ModuleBay or []:
        if bay.deletedAt is not None or bay.parentModuleId is not None or bay.deviceId != d.id:
            continue
        bn = _node("ModuleBay", bay.id, bay.name or "slot")
        nodes.append(bn)
        edges.append(_edge(root, bn, kind="has_slot", label="slot"))
        mod = db.execute(select(Module).where(Module.moduleBayId == bay.id, Module.deletedAt.is_(None))).scalar_one_or_none()
        bay_children: list[dict[str, Any]] = []
        if mod:
            mt = db.get(ModuleType, mod.moduleTypeId)
            mlab = f"{mt.model}" if mt else "module"
            mod_label = mod.serial or mlab
            mn = _node("Module", mod.id, mod_label)
            nodes.append(mn)
            edges.append(_edge(bn, mn, kind="has_card", label="card"))
            add_nested_slots(mod, mod_label, bay_children)
            for fp in (
                db.execute(
                    select(FrontPort).where(
                        and_(FrontPort.moduleId == mod.id, FrontPort.deletedAt.is_(None)),
                    ),
                )
                .scalars()
                .all()
            ):
                pn = _node("FrontPort", fp.id, fp.name)
                nodes.append(pn)
                edges.append(_edge(mn, pn, kind="has_front_port", label="front port"))
                bay_children.append({"node": pn, "children": []})
        children.append({"node": bn, "children": bay_children})

    for fp in d.FrontPort or []:
        if fp.deletedAt is not None or fp.moduleId is not None:
            continue
        pn = _node("FrontPort", fp.id, fp.name)
        nodes.append(pn)
        edges.append(_edge(root, pn, kind="has_front_port", label="chassis front port"))
        children.append({"node": pn, "children": []})

    tree = {"node": root, "children": children}
    return {"root": root, "nodes": _dedupe_nodes(nodes), "edges": edges, "tree": tree}


def _graph_location(db: Session, organization_id: uuid.UUID, resource_id: uuid.UUID) -> dict[str, Any] | None:
    loc = db.execute(
        select(Location)
        .where(
            and_(
                Location.id == resource_id,
                Location.organizationId == organization_id,
                Location.deletedAt.is_(None),
            ),
        )
        .options(joinedload(Location.Location), joinedload(Location.Rack)),
    ).unique().scalar_one_or_none()
    if loc is None:
        return None
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    root = _node("Location", loc.id, loc.name)
    nodes.append(root)
    par = loc.Location
    if par is not None:
        pn = _node("Location", par.id, par.name)
        nodes.append(pn)
        edges.append(_edge(root, pn, kind="parent", label="parent location"))
    for ch in db.execute(select(Location).where(and_(Location.parentId == loc.id, Location.deletedAt.is_(None)))).scalars():
        cn = _node("Location", ch.id, ch.name)
        nodes.append(cn)
        edges.append(_edge(root, cn, kind="child", label="child location"))
    for r in loc.Rack or []:
        if r.deletedAt is not None:
            continue
        rn = _node("Rack", r.id, r.name)
        nodes.append(rn)
        edges.append(_edge(root, rn, kind="has_rack", label="rack"))
    tree = {
        "node": root,
        "children": [{"node": n, "children": []} for n in nodes if n["id"] != str(loc.id)][
            :50
        ],  # cap for UI
    }
    return {"root": root, "nodes": _dedupe_nodes(nodes), "edges": edges, "tree": tree}


def _graph_rack(db: Session, organization_id: uuid.UUID, resource_id: uuid.UUID) -> dict[str, Any] | None:
    r = db.execute(
        select(Rack)
        .where(
            and_(
                Rack.id == resource_id,
                Rack.organizationId == organization_id,
                Rack.deletedAt.is_(None),
            ),
        )
        .options(joinedload(Rack.Location_), joinedload(Rack.Device)),
    ).unique().scalar_one_or_none()
    if r is None:
        return None
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    root = _node("Rack", r.id, r.name)
    nodes.append(root)
    if r.Location_:
        ln = _node("Location", r.Location_.id, r.Location_.name)
        nodes.append(ln)
        edges.append(_edge(root, ln, kind="at_location", label="location"))
    for d in r.Device or []:
        if d.deletedAt is not None:
            continue
        dn = _node("Device", d.id, d.name)
        nodes.append(dn)
        edges.append(_edge(root, dn, kind="has_device", label="device"))
    tree = {"node": root, "children": [{"node": n, "children": []} for n in nodes if n["id"] != str(r.id)][:50]}
    return {"root": root, "nodes": _dedupe_nodes(nodes), "edges": edges, "tree": tree}


def _graph_vrf(db: Session, organization_id: uuid.UUID, resource_id: uuid.UUID) -> dict[str, Any] | None:
    v = db.execute(
        select(Vrf).where(and_(Vrf.id == resource_id, Vrf.organizationId == organization_id, Vrf.deletedAt.is_(None))),
    ).scalar_one_or_none()
    if v is None:
        return None
    nodes = [_node("Vrf", v.id, v.name)]
    edges: list[dict[str, Any]] = []
    pref_rows = (
        db.execute(
            select(Prefix).where(and_(Prefix.vrfId == v.id, Prefix.organizationId == organization_id, Prefix.deletedAt.is_(None))),
        )
        .scalars()
        .all()
    )
    children: list[dict[str, Any]] = []
    for p in pref_rows[:40]:
        pn = _node("Prefix", p.id, p.cidr)
        nodes.append(pn)
        edges.append(_edge(nodes[0], pn, kind="has_prefix", label="prefix"))
        children.append({"node": pn, "children": []})
    tree = {"node": nodes[0], "children": children}
    return {"root": nodes[0], "nodes": _dedupe_nodes(nodes), "edges": edges, "tree": tree}


def _graph_prefix(db: Session, organization_id: uuid.UUID, resource_id: uuid.UUID) -> dict[str, Any] | None:
    p = db.execute(
        select(Prefix)
        .where(and_(Prefix.id == resource_id, Prefix.organizationId == organization_id, Prefix.deletedAt.is_(None)))
        .options(joinedload(Prefix.Vrf_), joinedload(Prefix.parent)),
    ).scalar_one_or_none()
    if p is None:
        return None
    nodes = [_node("Prefix", p.id, p.cidr)]
    edges: list[dict[str, Any]] = []
    root = nodes[0]
    if p.Vrf_:
        vn = _node("Vrf", p.Vrf_.id, p.Vrf_.name)
        nodes.append(vn)
        edges.append(_edge(root, vn, kind="in_vrf", label="VRF"))
    parent_p = p.Prefix
    if parent_p is not None:
        pn = _node("Prefix", parent_p.id, parent_p.cidr)
        nodes.append(pn)
        edges.append(_edge(root, pn, kind="parent_prefix", label="parent"))
    for ip in db.execute(
        select(IpAddress).where(
            and_(IpAddress.prefixId == p.id, IpAddress.organizationId == organization_id, IpAddress.deletedAt.is_(None)),
        ),
    ).scalars():
        inode = _node("IpAddress", ip.id, ip.address)
        nodes.append(inode)
        edges.append(_edge(root, inode, kind="has_ip", label="IP"))
    tree = {"node": root, "children": [{"node": n, "children": []} for n in nodes[1:][:30]]}
    return {"root": root, "nodes": _dedupe_nodes(nodes), "edges": edges, "tree": tree}


def _graph_ip_address(db: Session, organization_id: uuid.UUID, resource_id: uuid.UUID) -> dict[str, Any] | None:
    ip = db.execute(
        select(IpAddress)
        .where(
            and_(IpAddress.id == resource_id, IpAddress.organizationId == organization_id, IpAddress.deletedAt.is_(None)),
        )
        .options(joinedload(IpAddress.Prefix_).joinedload(Prefix.Vrf_), joinedload(IpAddress.Interface_)),
    ).scalar_one_or_none()
    if ip is None:
        return None
    nodes = [_node("IpAddress", ip.id, ip.address)]
    edges: list[dict[str, Any]] = []
    root = nodes[0]
    if ip.Prefix_:
        pr = ip.Prefix_
        pn = _node("Prefix", pr.id, pr.cidr)
        nodes.append(pn)
        edges.append(_edge(root, pn, kind="in_prefix", label="prefix"))
        if pr.Vrf_:
            vn = _node("Vrf", pr.Vrf_.id, pr.Vrf_.name)
            nodes.append(vn)
            edges.append(_edge(pn, vn, kind="in_vrf", label="VRF"))
    if ip.Interface_:
        iface = ip.Interface_
        inode = _node("Interface", iface.id, iface.name)
        nodes.append(inode)
        edges.append(_edge(root, inode, kind="assigned_interface", label="interface"))
        dev = db.execute(select(Device).where(Device.id == iface.deviceId)).scalar_one_or_none()
        if dev:
            dn = _node("Device", dev.id, dev.name)
            nodes.append(dn)
            edges.append(_edge(inode, dn, kind="on_device", label="device"))
    tree = {"node": root, "children": [{"node": n, "children": []} for n in nodes[1:]]}
    return {"root": root, "nodes": _dedupe_nodes(nodes), "edges": edges, "tree": tree}


def _graph_interface(db: Session, organization_id: uuid.UUID, resource_id: uuid.UUID) -> dict[str, Any] | None:
    iface = db.execute(
        select(Interface).where(and_(Interface.id == resource_id, Interface.deletedAt.is_(None))),
    ).scalar_one_or_none()
    if iface is None:
        return None
    dev = db.execute(
        select(Device).where(and_(Device.id == iface.deviceId, Device.organizationId == organization_id, Device.deletedAt.is_(None))),
    ).scalar_one_or_none()
    if dev is None:
        return None
    nodes = [_node("Interface", iface.id, iface.name)]
    edges: list[dict[str, Any]] = []
    root = nodes[0]
    dn = _node("Device", dev.id, dev.name)
    nodes.append(dn)
    edges.append(_edge(root, dn, kind="on_device", label="device"))
    for c in db.execute(
        select(Cable).where(
            and_(
                or_(Cable.interfaceAId == iface.id, Cable.interfaceBId == iface.id),
                Cable.deletedAt.is_(None),
            ),
        ),
    ).scalars():
        other = c.interfaceBId if c.interfaceAId == iface.id else c.interfaceAId
        oi = db.execute(select(Interface).where(Interface.id == other)).scalar_one_or_none()
        if oi:
            on = _node("Interface", oi.id, oi.name)
            nodes.append(on)
            edges.append(_edge(root, on, kind="cable", label="cable"))
    for ip in db.execute(
        select(IpAddress).where(
            and_(IpAddress.interfaceId == iface.id, IpAddress.organizationId == organization_id, IpAddress.deletedAt.is_(None)),
        ),
    ).scalars():
        inode = _node("IpAddress", ip.id, ip.address)
        nodes.append(inode)
        edges.append(_edge(root, inode, kind="has_ip", label="IP"))
    tree = {"node": root, "children": [{"node": n, "children": []} for n in nodes[1:][:20]]}
    return {"root": root, "nodes": _dedupe_nodes(nodes), "edges": edges, "tree": tree}


def _graph_circuit(db: Session, organization_id: uuid.UUID, resource_id: uuid.UUID) -> dict[str, Any] | None:
    c = db.execute(
        select(Circuit)
        .where(and_(Circuit.id == resource_id, Circuit.organizationId == organization_id, Circuit.deletedAt.is_(None)))
        .options(
            joinedload(Circuit.Provider_),
            joinedload(Circuit.CircuitDiversityGroup_),
            selectinload(Circuit.CircuitSegment).joinedload(CircuitSegment.Provider_),
            selectinload(Circuit.CircuitTermination).joinedload(CircuitTermination.Location_),
        ),
    ).unique().scalar_one_or_none()
    if c is None:
        return None
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    root = _node("Circuit", c.id, c.cid)
    nodes.append(root)

    if c.CircuitDiversityGroup_:
        dgn = _node("CircuitDiversityGroup", c.CircuitDiversityGroup_.id, c.CircuitDiversityGroup_.name)
        nodes.append(dgn)
        edges.append(_edge(root, dgn, kind="diversity_group", label="diversity group"))

    if c.Provider_:
        pn = _node("Provider", c.Provider_.id, c.Provider_.name)
        nodes.append(pn)
        edges.append(_edge(root, pn, kind="billing_provider", label="billing / contract"))

    segs = sorted(c.CircuitSegment or [], key=lambda s: s.segmentIndex)
    seg_nodes: list[dict[str, Any]] = []
    for seg in segs:
        sn = _node("CircuitSegment", seg.id, seg.label or f"Leg {seg.segmentIndex}")
        nodes.append(sn)
        seg_nodes.append(sn)
        if seg.Provider_:
            spn = _node("Provider", seg.Provider_.id, seg.Provider_.name)
            nodes.append(spn)
            edges.append(_edge(sn, spn, kind="segment_carrier", label="carrier"))

    ta = next((t for t in (c.CircuitTermination or []) if (t.side or "").upper() == "A"), None)
    tz = next((t for t in (c.CircuitTermination or []) if (t.side or "").upper() == "Z"), None)

    def _term_endpoint(t: CircuitTermination | None, side_label: str) -> dict[str, Any] | None:
        if t is None:
            return None
        if t.Location_:
            return _node("Location", t.Location_.id, t.Location_.name)
        return _node("CircuitTermination", t.id, f"{side_label} termination")

    an = _term_endpoint(ta, "A")
    zn = _term_endpoint(tz, "Z")
    if an:
        nodes.append(an)
    if zn:
        nodes.append(zn)

    if seg_nodes:
        if an:
            edges.append(_edge(an, seg_nodes[0], kind="ingress", label="A-side → first leg"))
        else:
            edges.append(_edge(root, seg_nodes[0], kind="path", label="legs"))
        for i in range(len(seg_nodes) - 1):
            edges.append(_edge(seg_nodes[i], seg_nodes[i + 1], kind="handoff", label="carrier handoff"))
        if zn:
            edges.append(_edge(seg_nodes[-1], zn, kind="egress", label="last leg → Z-side"))
    else:
        if an and zn:
            edges.append(_edge(an, zn, kind="path", label="end-to-end (no segments)"))
        elif an:
            edges.append(_edge(root, an, kind="termination", label="A-side"))
        elif zn:
            edges.append(_edge(root, zn, kind="termination", label="Z-side"))

    children: list[dict[str, Any]] = []
    for n in nodes[1:][:24]:
        children.append({"node": n, "children": []})
    tree = {"node": root, "children": children}
    return {"root": root, "nodes": _dedupe_nodes(nodes), "edges": edges, "tree": tree}


def _graph_provider(db: Session, organization_id: uuid.UUID, resource_id: uuid.UUID) -> dict[str, Any] | None:
    p = db.execute(
        select(Provider).where(
            and_(Provider.id == resource_id, Provider.organizationId == organization_id, Provider.deletedAt.is_(None)),
        ),
    ).scalar_one_or_none()
    if p is None:
        return None
    nodes = [_node("Provider", p.id, p.name)]
    edges: list[dict[str, Any]] = []
    root = nodes[0]
    for c in db.execute(
        select(Circuit).where(
            and_(Circuit.providerId == p.id, Circuit.organizationId == organization_id, Circuit.deletedAt.is_(None)),
        ),
    ).scalars():
        cn = _node("Circuit", c.id, c.cid)
        nodes.append(cn)
        edges.append(_edge(root, cn, kind="circuit", label="circuit"))
    tree = {"node": root, "children": [{"node": n, "children": []} for n in nodes[1:][:30]]}
    return {"root": root, "nodes": _dedupe_nodes(nodes), "edges": edges, "tree": tree}


def _dedupe_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[tuple[str, str]] = set()
    out: list[dict[str, Any]] = []
    for n in nodes:
        key = (n["resourceType"], n["id"])
        if key in seen:
            continue
        seen.add(key)
        out.append(n)
    return out
