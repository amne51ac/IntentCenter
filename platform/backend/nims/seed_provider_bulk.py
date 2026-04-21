"""Synthetic carrier-scale inventory for load testing and demos.

Creates organization ``provider-bulk`` (override with ``PROVIDER_BULK_ORG_SLUG``) with
hierarchical regions/POPs, PDUs, core/edge/OOB roles, virtual chassis, MC-LAG /
interface redundancy groups, device bays with line-card children, patched console
and power feeds, tags, VLANs, MPLS/RT artifacts, circuits (including multi-segment
and ring closure), and IP addressing (loopbacks + link / management).

Large loads (10k+ devices) require PROVIDER_BULK_CONFIRM=yes.

Examples::

  PROVIDER_BULK_LITE=1 uv run --directory backend python -m nims.seed_provider_bulk --purge
  PROVIDER_BULK_CONFIRM=yes uv run --directory backend python -m nims.seed_provider_bulk --purge
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import uuid
from collections.abc import Iterator
from typing import Any, Literal

from sqlalchemy import delete, func, insert, select
from sqlalchemy.orm import Session

from nims.db import SessionLocal
from nims.models_generated import (
    Cable,
    Circuit,
    CircuitSegment,
    Circuitstatus,
    CircuitTermination,
    CircuitType,
    ConsoleConnection,
    ConsolePort,
    ConsoleServerPort,
    Controller,
    Device,
    DeviceBay,
    DeviceGroup,
    DeviceGroupMember,
    DeviceRedundancyGroup,
    DeviceRedundancyGroupMember,
    DeviceRole,
    Devicestatus,
    DeviceType,
    FrontPort,
    Interface,
    InterfaceRedundancyGroup,
    InterfaceRedundancyGroupMember,
    InventoryItem,
    IpAddress,
    Location,
    LocationType,
    Manufacturer,
    Module,
    ModuleBay,
    ModuleType,
    MplsDomain,
    Observationkind,
    ObservedResourceState,
    Organization,
    PowerConnection,
    PowerOutlet,
    PowerPort,
    Prefix,
    Provider,
    ProviderNetwork,
    Rack,
    RearPort,
    Rir,
    RouteTarget,
    Tag,
    TagAssignment,
    VirtualChassis,
    VirtualChassisMember,
    Vlan,
    VlanGroup,
    Vrf,
)
from nims.timeutil import utc_now

Kind = Literal["pdu", "core", "edge", "oob", "blade"]


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


def _chunked(items: list[Any], size: int) -> Iterator[list[Any]]:
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _purge_bulk_org(session: Session, org_id: uuid.UUID) -> None:
    """Remove DCIM/IPAM rows for this organization (FK-safe order)."""

    dev_ids = select(Device.id).where(Device.organizationId == org_id).scalar_subquery()
    iface_ids = select(Interface.id).where(Interface.deviceId.in_(dev_ids)).scalar_subquery()
    tag_ids = select(Tag.id).where(Tag.organizationId == org_id).scalar_subquery()
    irg_ids = select(InterfaceRedundancyGroup.id).where(
        InterfaceRedundancyGroup.organizationId == org_id,
    ).scalar_subquery()
    drg_ids = select(DeviceRedundancyGroup.id).where(
        DeviceRedundancyGroup.organizationId == org_id,
    ).scalar_subquery()
    dg_ids = select(DeviceGroup.id).where(DeviceGroup.organizationId == org_id).scalar_subquery()
    vc_ids = select(VirtualChassis.id).where(VirtualChassis.organizationId == org_id).scalar_subquery()

    session.execute(delete(ConsoleConnection).where(ConsoleConnection.organizationId == org_id))
    session.execute(delete(PowerConnection).where(PowerConnection.organizationId == org_id))

    session.execute(
        delete(InterfaceRedundancyGroupMember).where(InterfaceRedundancyGroupMember.groupId.in_(irg_ids)),
    )
    session.execute(delete(InterfaceRedundancyGroup).where(InterfaceRedundancyGroup.organizationId == org_id))

    session.execute(
        delete(DeviceRedundancyGroupMember).where(DeviceRedundancyGroupMember.groupId.in_(drg_ids)),
    )
    session.execute(delete(DeviceRedundancyGroup).where(DeviceRedundancyGroup.organizationId == org_id))

    session.execute(delete(VirtualChassisMember).where(VirtualChassisMember.virtualChassisId.in_(vc_ids)))
    session.execute(delete(VirtualChassis).where(VirtualChassis.organizationId == org_id))

    session.execute(delete(DeviceGroupMember).where(DeviceGroupMember.groupId.in_(dg_ids)))
    session.execute(delete(DeviceGroup).where(DeviceGroup.organizationId == org_id))

    session.execute(delete(TagAssignment).where(TagAssignment.tagId.in_(tag_ids)))
    session.execute(delete(Tag).where(Tag.organizationId == org_id))

    session.execute(delete(Controller).where(Controller.organizationId == org_id))
    session.execute(delete(InventoryItem).where(InventoryItem.organizationId == org_id))

    session.execute(delete(DeviceBay).where(DeviceBay.parentDeviceId.in_(dev_ids)))

    session.execute(delete(Cable).where(Cable.interfaceAId.in_(iface_ids), Cable.interfaceBId.in_(iface_ids)))
    session.execute(delete(IpAddress).where(IpAddress.organizationId == org_id))
    session.execute(delete(ObservedResourceState).where(ObservedResourceState.organizationId == org_id))

    session.execute(delete(Vlan).where(Vlan.organizationId == org_id))
    session.execute(delete(RouteTarget).where(RouteTarget.organizationId == org_id))
    session.execute(delete(MplsDomain).where(MplsDomain.organizationId == org_id))

    session.execute(delete(Circuit).where(Circuit.organizationId == org_id))
    session.execute(delete(ProviderNetwork).where(ProviderNetwork.organizationId == org_id))
    session.execute(delete(Provider).where(Provider.organizationId == org_id))

    session.execute(delete(Interface).where(Interface.deviceId.in_(dev_ids)))

    session.execute(delete(Module).where(Module.organizationId == org_id))
    session.execute(delete(ModuleBay).where(ModuleBay.deviceId.in_(dev_ids)))
    session.execute(delete(FrontPort).where(FrontPort.deviceId.in_(dev_ids)))
    session.execute(delete(RearPort).where(RearPort.deviceId.in_(dev_ids)))
    session.execute(delete(ConsolePort).where(ConsolePort.deviceId.in_(dev_ids)))
    session.execute(delete(ConsoleServerPort).where(ConsoleServerPort.deviceId.in_(dev_ids)))
    session.execute(delete(PowerPort).where(PowerPort.deviceId.in_(dev_ids)))
    session.execute(delete(PowerOutlet).where(PowerOutlet.deviceId.in_(dev_ids)))

    session.execute(delete(Device).where(Device.organizationId == org_id))
    session.execute(delete(Rack).where(Rack.organizationId == org_id))

    session.execute(delete(Prefix).where(Prefix.organizationId == org_id))
    session.execute(delete(Vrf).where(Vrf.organizationId == org_id))

    session.execute(
        delete(Location).where(Location.organizationId == org_id, Location.parentId.isnot(None)),
    )
    session.execute(delete(Location).where(Location.organizationId == org_id))


def _iface_names(kind: Kind, n_phys: int) -> list[tuple[str, str]]:
    """Return (name, type) rows: loopback first when applicable."""
    if kind == "pdu":
        return [("mgmt0", "ethernet")]
    if kind == "blade":
        return [(f"xe-0/0/{i}", "ethernet") for i in range(n_phys)]
    rows: list[tuple[str, str]] = []
    if kind in ("core", "edge", "oob"):
        rows.append(("lo0", "loopback"))
    if kind == "core":
        rows.extend((f"xe-0/0/{i}", "ethernet") for i in range(n_phys))
    elif kind == "edge":
        rows.extend((f"xe-0/0/{i}", "ethernet") for i in range(n_phys))
    elif kind == "oob":
        rows.extend(
            [
                ("eth0", "ethernet"),
                ("eth1", "ethernet"),
                ("ttyS0", "other"),
                ("aux0", "other"),
            ],
        )
    return rows


def _fake_mac(site: int, rack: int, slot: int, iface: int) -> str:
    h = hashlib.sha256(f"{site}:{rack}:{slot}:{iface}".encode()).hexdigest()
    return f"00:1c:73:{h[0:2]}:{h[2:4]}:{h[4:6]}"


def run_bulk_seed(session: Session, *, purge: bool) -> dict[str, object]:
    now = utc_now()
    batch = _env_int("PROVIDER_BULK_INSERT_BATCH", 3000)

    if os.environ.get("PROVIDER_BULK_LITE") == "1":
        num_regions = 2
        num_sites_per_region = 4
        racks_per_site = 2
        # pdu + 2×PE + 2×agg + OOB (needs ≥6 for OOB branch)
        devices_per_rack = 6
    else:
        num_regions = _env_int("NUM_REGIONS", 25)
        num_sites_per_region = _env_int("NUM_SITES_PER_REGION", 100)
        racks_per_site = _env_int("RACKS_PER_SITE", 2)
        devices_per_rack = _env_int("DEVICES_PER_RACK", 10)

    iata_codes = [
        "IAD",
        "ORD",
        "DFW",
        "LAX",
        "SJC",
        "SEA",
        "MIA",
        "ATL",
        "JFK",
        "EWR",
        "DEN",
        "PHX",
        "MSP",
        "BOS",
        "PDX",
        "YYZ",
        "LHR",
        "FRA",
        "AMS",
        "CDG",
        "SIN",
        "NRT",
        "SYD",
        "GRU",
        "DXB",
    ]
    region_labels = [
        "NAM-US-East",
        "NAM-US-Central",
        "NAM-US-West",
        "NAM-CA",
        "LATAM",
        "EMEA-North",
        "EMEA-Central",
        "EMEA-UK",
        "APAC-North",
        "APAC-SE",
        "APAC-IN",
        "MEA",
    ]

    total_sites = num_regions * num_sites_per_region
    # +1 PDU per rack; +2 blade children per rack (one bay per core)
    total_devices_estimate = total_sites * racks_per_site * (devices_per_rack + 1 + 2)

    if total_devices_estimate > 10_000 and os.environ.get("PROVIDER_BULK_CONFIRM", "").lower() not in (
        "1",
        "true",
        "yes",
    ):
        print(
            "Refusing to create more than ~10,000 devices without PROVIDER_BULK_CONFIRM=yes "
            f"(estimated {total_devices_estimate} devices). "
            "Use PROVIDER_BULK_LITE=1 for a small sample.",
            file=sys.stderr,
        )
        sys.exit(1)

    org_slug = os.environ.get("PROVIDER_BULK_ORG_SLUG", "provider-bulk")
    org = session.execute(select(Organization).where(Organization.slug == org_slug)).scalar_one_or_none()
    if org is None:
        org = Organization(
            id=uuid.uuid4(),
            name="NorthStar Transit — synthetic inventory",
            slug=org_slug,
            updatedAt=now,
            deletedAt=None,
        )
        session.add(org)
        session.flush()
    else:
        if purge:
            _purge_bulk_org(session, org.id)
            session.flush()
        else:
            n_dev = session.execute(
                select(func.count()).select_from(Device).where(Device.organizationId == org.id),
            ).scalar_one()
            if int(n_dev) > 0:
                print(
                    "Bulk org already contains devices. Re-run with --purge or PROVIDER_BULK_PURGE=1 "
                    "to replace data, or use a different PROVIDER_BULK_ORG_SLUG.",
                    file=sys.stderr,
                )
                sys.exit(1)

    org_id = org.id

    lt_region = session.execute(select(LocationType).where(LocationType.name == "Region")).scalar_one_or_none()
    if lt_region is None:
        lt_region = LocationType(id=uuid.uuid4(), name="Region", description="Geographic region")
        session.add(lt_region)
        session.flush()
    lt_site = session.execute(select(LocationType).where(LocationType.name == "Site")).scalar_one_or_none()
    if lt_site is None:
        lt_site = LocationType(id=uuid.uuid4(), name="Site", description="POP / colocation facility")
        session.add(lt_site)
        session.flush()

    for slug, title in (
        ("ethernet-wan", "Ethernet WAN / DIA"),
        ("dark-fiber", "Dark fiber / wave"),
    ):
        ct = session.execute(select(CircuitType).where(CircuitType.slug == slug)).scalar_one_or_none()
        if ct is None:
            session.add(
                CircuitType(
                    id=uuid.uuid4(),
                    name=title,
                    slug=slug,
                    description="Bulk seed circuit type",
                ),
            )
    session.flush()
    ct_eth = session.execute(select(CircuitType).where(CircuitType.slug == "ethernet-wan")).scalar_one()
    ct_dark = session.execute(select(CircuitType).where(CircuitType.slug == "dark-fiber")).scalar_one()

    mfg_j = session.execute(select(Manufacturer).where(Manufacturer.name == "Juniper (sim)")).scalar_one_or_none()
    if mfg_j is None:
        mfg_j = Manufacturer(id=uuid.uuid4(), name="Juniper (sim)")
        session.add(mfg_j)
        session.flush()
    mfg_a = session.execute(select(Manufacturer).where(Manufacturer.name == "Arista (sim)")).scalar_one_or_none()
    if mfg_a is None:
        mfg_a = Manufacturer(id=uuid.uuid4(), name="Arista (sim)")
        session.add(mfg_a)
        session.flush()
    mfg_apc = session.execute(select(Manufacturer).where(Manufacturer.name == "APC (sim)")).scalar_one_or_none()
    if mfg_apc is None:
        mfg_apc = Manufacturer(id=uuid.uuid4(), name="APC (sim)")
        session.add(mfg_apc)
        session.flush()

    def _ensure_dt(mfg: uuid.UUID, model: str, u_h: int) -> uuid.UUID:
        row = session.execute(
            select(DeviceType).where(DeviceType.manufacturerId == mfg, DeviceType.model == model),
        ).scalar_one_or_none()
        if row is None:
            row = DeviceType(id=uuid.uuid4(), manufacturerId=mfg, model=model, uHeight=u_h)
            session.add(row)
            session.flush()
        return row.id

    dt_mx = _ensure_dt(mfg_j.id, "MX204", 4)
    dt_qfx = _ensure_dt(mfg_a.id, "7280SR3-48YC6", 1)
    dt_oob = _ensure_dt(mfg_j.id, "ACX7024", 1)
    dt_pdu = _ensure_dt(mfg_apc.id, "AP8959EU3", 2)
    dt_blade = _ensure_dt(mfg_j.id, "MPC7E-10G-40G", 1)

    def _ensure_role(name: str) -> uuid.UUID:
        row = session.execute(select(DeviceRole).where(DeviceRole.name == name)).scalar_one_or_none()
        if row is None:
            row = DeviceRole(id=uuid.uuid4(), name=name)
            session.add(row)
            session.flush()
        return row.id

    role_core = _ensure_role("pe-router")
    role_edge = _ensure_role("aggregation")
    role_oob = _ensure_role("oob-console")
    role_pdu = _ensure_role("pdu")
    role_blade = _ensure_role("line-card")

    mt_line = session.execute(
        select(ModuleType).where(ModuleType.model == "MPC7E-10G-40G-SFP"),
    ).scalar_one_or_none()
    if mt_line is None:
        mt_line = ModuleType(
            id=uuid.uuid4(),
            manufacturerId=mfg_j.id,
            model="MPC7E-10G-40G-SFP",
            partNumber="750-063190",
        )
        session.add(mt_line)
        session.flush()

    rir = session.execute(select(Rir).where(Rir.slug == "arin")).scalar_one_or_none()
    if rir is None:
        rir = Rir(id=uuid.uuid4(), name="ARIN", slug="arin", description="Registry (simulated)")
        session.add(rir)
        session.flush()

    vrf = session.execute(select(Vrf).where(Vrf.organizationId == org_id, Vrf.name == "inet.0")).scalar_one_or_none()
    if vrf is None:
        vrf = Vrf(
            id=uuid.uuid4(),
            organizationId=org_id,
            name="inet.0",
            rd="65001:1",
            updatedAt=now,
            deletedAt=None,
        )
        session.add(vrf)
        session.flush()

    vrf_mpls = session.execute(
        select(Vrf).where(Vrf.organizationId == org_id, Vrf.name == "cust-vpn-1"),
    ).scalar_one_or_none()
    if vrf_mpls is None:
        vrf_mpls = Vrf(
            id=uuid.uuid4(),
            organizationId=org_id,
            name="cust-vpn-1",
            rd="65001:100",
            updatedAt=now,
            deletedAt=None,
        )
        session.add(vrf_mpls)
        session.flush()

    pfx = session.execute(
        select(Prefix).where(Prefix.organizationId == org_id, Prefix.vrfId == vrf.id, Prefix.cidr == "10.0.0.0/8"),
    ).scalar_one_or_none()
    if pfx is None:
        pfx = Prefix(
            id=uuid.uuid4(),
            organizationId=org_id,
            vrfId=vrf.id,
            cidr="10.0.0.0/8",
            description="Global infrastructure aggregate (RFC1918 sim)",
            rirId=rir.id,
            updatedAt=now,
            deletedAt=None,
        )
        session.add(pfx)
        session.flush()

    pfx_lo = session.execute(
        select(Prefix).where(Prefix.organizationId == org_id, Prefix.cidr == "10.255.0.0/16"),
    ).scalar_one_or_none()
    if pfx_lo is None:
        pfx_lo = Prefix(
            id=uuid.uuid4(),
            organizationId=org_id,
            vrfId=vrf.id,
            cidr="10.255.0.0/16",
            description="Loopbacks / router-ids",
            parentId=pfx.id,
            rirId=rir.id,
            updatedAt=now,
            deletedAt=None,
        )
        session.add(pfx_lo)
        session.flush()

    mpls = session.execute(
        select(MplsDomain).where(MplsDomain.organizationId == org_id, MplsDomain.name == "backbone-mpls"),
    ).scalar_one_or_none()
    if mpls is None:
        mpls = MplsDomain(
            id=uuid.uuid4(),
            organizationId=org_id,
            name="backbone-mpls",
            rd="65001:0",
            description="Core RSVP-TE / LDP domain (sim)",
            updatedAt=now,
            deletedAt=None,
        )
        session.add(mpls)
        session.flush()

    session.add(
        RouteTarget(
            id=uuid.uuid4(),
            organizationId=org_id,
            vrfId=vrf_mpls.id,
            name="65001:1000",
            description="VPN-A route target",
            updatedAt=now,
            deletedAt=None,
        ),
    )

    vg = session.execute(select(VlanGroup).where(VlanGroup.name == "Backbone transport")).scalar_one_or_none()
    if vg is None:
        vg = VlanGroup(id=uuid.uuid4(), name="Backbone transport")
        session.add(vg)
        session.flush()

    wholesale: list[tuple[str, int]] = [
        ("Cogent Communications", 174),
        ("NTT America", 2914),
        ("Telia Carrier", 1299),
        ("GTT", 3257),
        ("Zayo", 6461),
        ("Lumen / Level3", 3356),
        ("Arelion", 12956),
        ("DE-CIX Route Server", 6695),
    ]
    provider_ids: list[uuid.UUID] = []
    for name, asn in wholesale:
        existing = session.execute(
            select(Provider).where(Provider.organizationId == org_id, Provider.name == name),
        ).scalar_one_or_none()
        if existing:
            pid = existing.id
        else:
            pid = uuid.uuid4()
            session.add(
                Provider(
                    id=pid,
                    organizationId=org_id,
                    name=name,
                    asn=asn,
                    updatedAt=now,
                    deletedAt=None,
                ),
            )
        provider_ids.append(pid)
    session.flush()

    for pid in provider_ids:
        existing = session.execute(
            select(ProviderNetwork).where(
                ProviderNetwork.organizationId == org_id,
                ProviderNetwork.providerId == pid,
                ProviderNetwork.name == "IP Transit",
            ),
        ).scalar_one_or_none()
        if existing is None:
            session.add(
                ProviderNetwork(
                    id=uuid.uuid4(),
                    organizationId=org_id,
                    providerId=pid,
                    name="IP Transit",
                    description="BGP transit / DIA handoff",
                    updatedAt=now,
                    deletedAt=None,
                ),
            )
    session.flush()

    tag_specs = [
        ("production", "prod", "2ecc71", "In-service"),
        ("staging", "stg", "f39c12", "Pre-prod / change window"),
        ("managed", "managed", "3498db", "NMS monitored"),
        ("backbone", "bb", "9b59b6", "Core / aggregation"),
    ]
    tag_ids: dict[str, uuid.UUID] = {}
    for name, slug, color, desc in tag_specs:
        t = session.execute(
            select(Tag).where(Tag.organizationId == org_id, Tag.slug == slug),
        ).scalar_one_or_none()
        if t is None:
            tid = uuid.uuid4()
            session.add(
                Tag(
                    id=tid,
                    organizationId=org_id,
                    name=name,
                    slug=slug,
                    color=color,
                    description=desc,
                    createdAt=now,
                    updatedAt=now,
                    deletedAt=None,
                ),
            )
            tag_ids[slug] = tid
        else:
            tag_ids[slug] = t.id
    session.flush()

    region_rows: list[dict[str, object]] = []
    region_ids: list[uuid.UUID] = []
    for r in range(num_regions):
        rid = uuid.uuid4()
        region_ids.append(rid)
        rlabel = region_labels[r % len(region_labels)]
        region_rows.append(
            {
                "id": rid,
                "organizationId": org_id,
                "parentId": None,
                "locationTypeId": lt_region.id,
                "name": f"{rlabel} ({r + 1:02d})",
                "slug": f"reg-{rlabel.lower().replace(' ', '-')}-{r + 1:03d}",
                "description": "Regional aggregation (sim)",
                "createdAt": now,
                "updatedAt": now,
                "deletedAt": None,
            },
        )
    for chunk in _chunked(region_rows, batch):
        session.execute(insert(Location), chunk)

    site_rows: list[dict[str, object]] = []
    site_ids: list[uuid.UUID] = []
    site_codes: list[str] = []
    gidx = 0
    for r in range(num_regions):
        for s in range(num_sites_per_region):
            sid = uuid.uuid4()
            site_ids.append(sid)
            # Monotonic index in the slug — do NOT use (gidx % 900) or slugs repeat every 900 POPs.
            iata = iata_codes[gidx % len(iata_codes)]
            code = f"{iata.lower()}-mmr-{gidx:05d}"
            site_codes.append(code)
            # Slug must be unique per org: monotonic index first (never reuse patterns like pop-{iata}-mmr-{n}).
            site_slug = f"pb-{gidx:06d}-{iata.lower()}"
            gidx += 1
            site_rows.append(
                {
                    "id": sid,
                    "organizationId": org_id,
                    "parentId": region_ids[r],
                    "locationTypeId": lt_site.id,
                    "name": f"POP {iata.upper()}-MMR-{gidx - 1:05d}",
                    "slug": site_slug,
                    "description": "Meet-me room / backbone POP",
                    "createdAt": now,
                    "updatedAt": now,
                    "deletedAt": None,
                },
            )
    for chunk in _chunked(site_rows, batch):
        session.execute(insert(Location), chunk)

    rack_rows: list[dict[str, object]] = []
    rack_ids: list[uuid.UUID] = []
    rack_site_idx: list[int] = []
    for si, _loc in enumerate(site_ids):
        for rk in range(racks_per_site):
            rack_id = uuid.uuid4()
            rack_ids.append(rack_id)
            rack_site_idx.append(si)
            rack_rows.append(
                {
                    "id": rack_id,
                    "organizationId": org_id,
                    "locationId": site_ids[si],
                    "name": f"R{rk + 1:02d}-{site_codes[si].upper()}-A",
                    "uHeight": 45,
                    "createdAt": now,
                    "updatedAt": now,
                    "deletedAt": None,
                    "rackGroupId": None,
                },
            )
    for chunk in _chunked(rack_rows, batch):
        session.execute(insert(Rack), chunk)

    device_rows: list[dict[str, object]] = []
    # meta: site_idx, rack_in_site, slot_in_rack, device_id, kind, iface_tuples list len
    device_meta: list[tuple[int, int, int, uuid.UUID, Kind, int]] = []

    def add_device(
        *,
        rack_id: uuid.UUID,
        si: int,
        rk_in_site: int,
        slot: int,
        name: str,
        kind: Kind,
        dtid: uuid.UUID,
        drid: uuid.UUID,
        pos_u: int,
        n_phys: int,
    ) -> uuid.UUID:
        did = uuid.uuid4()
        device_rows.append(
            {
                "id": did,
                "organizationId": org_id,
                "rackId": rack_id,
                "deviceTypeId": dtid,
                "deviceRoleId": drid,
                "name": name,
                "serialNumber": f"SN-{did.hex[:14].upper()}",
                "positionU": pos_u,
                "face": "front",
                "status": Devicestatus.ACTIVE,
                "createdAt": now,
                "updatedAt": now,
                "deletedAt": None,
            },
        )
        device_meta.append((si, rk_in_site, slot, did, kind, n_phys))
        return did

    for ri, rack_id in enumerate(rack_ids):
        si = rack_site_idx[ri]
        rk_in_site = ri % racks_per_site
        sc = site_codes[si]
        # position: PDU bottom, cores high, OOB mid
        add_device(
            rack_id=rack_id,
            si=si,
            rk_in_site=rk_in_site,
            slot=0,
            name=f"pdu-{sc}-r{rk_in_site + 1}",
            kind="pdu",
            dtid=dt_pdu,
            drid=role_pdu,
            pos_u=42,
            n_phys=1,
        )
        for c in range(2):
            add_device(
                rack_id=rack_id,
                si=si,
                rk_in_site=rk_in_site,
                slot=1 + c,
                name=f"pe-{sc}-r{rk_in_site + 1}-cr0{c + 1}",
                kind="core",
                dtid=dt_mx,
                drid=role_core,
                pos_u=36 - c * 4,
                n_phys=12,
            )
        n_edge = devices_per_rack - 4
        if devices_per_rack >= 6:
            n_edge = devices_per_rack - 4
        else:
            n_edge = max(0, devices_per_rack - 3)
        for e in range(n_edge):
            add_device(
                rack_id=rack_id,
                si=si,
                rk_in_site=rk_in_site,
                slot=3 + e,
                name=f"ag-{sc}-r{rk_in_site + 1}-sw{e + 1:02d}",
                kind="edge",
                dtid=dt_qfx,
                drid=role_edge,
                pos_u=20 - e,
                n_phys=8,
            )
        if devices_per_rack >= 6:
            add_device(
                rack_id=rack_id,
                si=si,
                rk_in_site=rk_in_site,
                slot=devices_per_rack - 1,
                name=f"oob-{sc}-r{rk_in_site + 1}",
                kind="oob",
                dtid=dt_oob,
                drid=role_oob,
                pos_u=8,
                n_phys=4,
            )

    for chunk in _chunked(device_rows, batch):
        session.execute(insert(Device), chunk)

    blade_devices: list[tuple[uuid.UUID, uuid.UUID]] = []
    blade_rows: list[dict[str, object]] = []
    for ri, rack_id in enumerate(rack_ids):
        si = rack_site_idx[ri]
        rk_in_site = ri % racks_per_site
        sc = site_codes[si]
        rack_cores = [m[3] for m in device_meta if m[0] == si and m[1] == rk_in_site and m[4] == "core"]
        for ci, parent in enumerate(rack_cores[:2]):
            bid = uuid.uuid4()
            blade_devices.append((parent, bid))
            blade_rows.append(
                {
                    "id": bid,
                    "organizationId": org_id,
                    "rackId": rack_id,
                    "deviceTypeId": dt_blade,
                    "deviceRoleId": role_blade,
                    "name": f"lc-{sc}-r{rk_in_site + 1}-cr0{ci + 1}-fpc0",
                    "serialNumber": f"SN-{bid.hex[:14].upper()}",
                    "positionU": None,
                    "face": "front",
                    "status": Devicestatus.STAGED,
                    "createdAt": now,
                    "updatedAt": now,
                    "deletedAt": None,
                },
            )
            device_meta.append((si, rk_in_site, 100 + ci, bid, "blade", 4))

    for chunk in _chunked(blade_rows, batch):
        session.execute(insert(Device), chunk)

    iface_rows: list[dict[str, object]] = []
    iface_by_dev: dict[uuid.UUID, list[uuid.UUID]] = {}
    lo_iface_by_dev: dict[uuid.UUID, uuid.UUID] = {}

    idx = 0
    for si, rk, _sl, did, kind, n_phys in device_meta:
        pairs = _iface_names(kind, n_phys)
        ifaces: list[uuid.UUID] = []
        for iname, itype in pairs:
            iid = uuid.uuid4()
            ifaces.append(iid)
            mac = _fake_mac(si, rk, idx, len(ifaces))
            iface_rows.append(
                {
                    "id": iid,
                    "deviceId": did,
                    "name": iname,
                    "type": itype,
                    "macAddress": mac if itype == "ethernet" else None,
                    "mtu": 9100 if itype == "ethernet" and iname != "mgmt0" else 1500,
                    "enabled": True,
                    "createdAt": now,
                    "updatedAt": now,
                    "deletedAt": None,
                },
            )
            if iname == "lo0":
                lo_iface_by_dev[did] = iid
        iface_by_dev[did] = ifaces
        idx += 1

    for chunk in _chunked(iface_rows, batch):
        session.execute(insert(Interface), chunk)

    # --- Device bays (parent core -> blade) ---
    bay_rows: list[dict[str, object]] = []
    for parent_id, blade_id in blade_devices:
        bay_rows.append(
            {
                "id": uuid.uuid4(),
                "parentDeviceId": parent_id,
                "name": "FPC-0",
                "installedDeviceId": blade_id,
                "createdAt": now,
                "updatedAt": now,
                "deletedAt": None,
            },
        )
    for chunk in _chunked(bay_rows, batch):
        session.execute(insert(DeviceBay), chunk)

    rack_net_lists: list[list[uuid.UUID]] = [[] for _ in rack_ids]
    for si, rk, _sl, did, kind, _n in device_meta:
        if kind in ("pdu", "blade"):
            continue
        ridx = si * racks_per_site + rk
        rack_net_lists[ridx].append(did)

    cable_rows: list[dict[str, object]] = []
    for devices_in_rack in rack_net_lists:
        m = len(devices_in_rack)
        if m < 2:
            continue
        for k in range(m):
            a = devices_in_rack[k]
            b = devices_in_rack[(k + 1) % m]
            ia = iface_by_dev[a][1]
            ib = iface_by_dev[b][1]
            cable_rows.append(
                {
                    "id": uuid.uuid4(),
                    "interfaceAId": ia,
                    "interfaceBId": ib,
                    "label": "SMF-OS2 / fabric ring",
                    "createdAt": now,
                    "updatedAt": now,
                    "deletedAt": None,
                },
            )

    for si in range(len(site_ids)):
        r0 = si * racks_per_site
        r1 = r0 + 1
        if racks_per_site < 2:
            continue
        devs0 = rack_net_lists[r0]
        devs1 = rack_net_lists[r1]
        if len(devs0) < 2 or len(devs1) < 2:
            continue
        c0 = next((d for d in devs0 if d in lo_iface_by_dev), devs0[0])
        c1 = next((d for d in devs1 if d in lo_iface_by_dev), devs1[0])
        ia = iface_by_dev[c0][5]
        ib = iface_by_dev[c1][5]
        cable_rows.append(
            {
                "id": uuid.uuid4(),
                "interfaceAId": ia,
                "interfaceBId": ib,
                "label": "inter-rack / MLAG peer",
                "createdAt": now,
                "updatedAt": now,
                "deletedAt": None,
            },
        )

    for chunk in _chunked(cable_rows, batch):
        session.execute(insert(Cable), chunk)

    # --- Virtual chassis + MC-LAG + AE bundle ---
    vc_rows: list[dict[str, object]] = []
    vcm_rows: list[dict[str, object]] = []
    drg_rows: list[dict[str, object]] = []
    drgm_rows: list[dict[str, object]] = []
    irg_rows: list[dict[str, object]] = []
    irgm_rows: list[dict[str, object]] = []

    for ri, rack_id in enumerate(rack_ids):
        si = rack_site_idx[ri]
        sc = site_codes[si]
        rk_in_site = ri % racks_per_site
        cores = [m[3] for m in device_meta if m[0] == si and m[1] == rk_in_site and m[4] == "core"]
        if len(cores) < 2:
            continue
        vcid = uuid.uuid4()
        vc_rows.append(
            {
                "id": vcid,
                "organizationId": org_id,
                "name": f"VC-{sc}-r{rk_in_site + 1}",
                "description": "Virtual chassis pair (sim)",
                "domainId": f"VC-{vcid.hex[:8]}",
                "createdAt": now,
                "updatedAt": now,
                "deletedAt": None,
            },
        )
        for pri, cid in enumerate(cores[:2]):
            vcm_rows.append(
                {
                    "id": uuid.uuid4(),
                    "virtualChassisId": vcid,
                    "deviceId": cid,
                    "priority": pri,
                },
            )
        dgid = uuid.uuid4()
        drg_rows.append(
            {
                "id": dgid,
                "organizationId": org_id,
                "name": f"MC-LAG-{sc}-r{rk_in_site + 1}",
                "protocol": "lacp",
                "description": "Multi-chassis LAG to aggregation",
                "createdAt": now,
                "updatedAt": now,
                "deletedAt": None,
            },
        )
        for cid in cores[:2]:
            drgm_rows.append(
                {
                    "id": uuid.uuid4(),
                    "groupId": dgid,
                    "deviceId": cid,
                    "role": "member",
                },
            )
        igid = uuid.uuid4()
        irg_rows.append(
            {
                "id": igid,
                "organizationId": org_id,
                "name": f"ae0-{sc}-r{rk_in_site + 1}",
                "protocol": "lacp",
                "description": "Bundle toward aggregation tier",
                "createdAt": now,
                "updatedAt": now,
                "deletedAt": None,
            },
        )
        for cid in cores[:2]:
            irgm_rows.append(
                {
                    "id": uuid.uuid4(),
                    "groupId": igid,
                    "interfaceId": iface_by_dev[cid][7],
                    "role": "active",
                },
            )

    for chunk in _chunked(vc_rows, batch):
        session.execute(insert(VirtualChassis), chunk)
    for chunk in _chunked(vcm_rows, batch):
        session.execute(insert(VirtualChassisMember), chunk)
    for chunk in _chunked(drg_rows, batch):
        session.execute(insert(DeviceRedundancyGroup), chunk)
    for chunk in _chunked(drgm_rows, batch):
        session.execute(insert(DeviceRedundancyGroupMember), chunk)
    for chunk in _chunked(irg_rows, batch):
        session.execute(insert(InterfaceRedundancyGroup), chunk)
    for chunk in _chunked(irgm_rows, batch):
        session.execute(insert(InterfaceRedundancyGroupMember), chunk)

    # --- Modules / bays on MX (line cards in chassis slots) ---
    mb_rows: list[dict[str, object]] = []
    mod_rows: list[dict[str, object]] = []
    for si, rk, _sl, did, kind, n_phys in device_meta:
        if kind != "core":
            continue
        for slot in range(4):
            mb_rows.append(
                {
                    "id": uuid.uuid4(),
                    "deviceId": did,
                    "name": f"PIC/{slot}/0",
                    "position": slot,
                    "createdAt": now,
                    "updatedAt": now,
                    "deletedAt": None,
                },
            )
            if slot < 2:
                mod_rows.append(
                    {
                        "id": uuid.uuid4(),
                        "organizationId": org_id,
                        "deviceId": did,
                        "moduleTypeId": mt_line.id,
                        "serial": f"LC-{did.hex[:8].upper()}-{slot}",
                        "createdAt": now,
                        "updatedAt": now,
                        "deletedAt": None,
                    },
                )
    for chunk in _chunked(mb_rows, batch):
        session.execute(insert(ModuleBay), chunk)
    for chunk in _chunked(mod_rows, batch):
        session.execute(insert(Module), chunk)

    # --- Patch field ports on edge ---
    fp_rows: list[dict[str, object]] = []
    rp_rows: list[dict[str, object]] = []
    for si, rk, _sl, did, kind, _n in device_meta:
        if kind != "edge":
            continue
        for p in range(24):
            fp_rows.append(
                {
                    "id": uuid.uuid4(),
                    "deviceId": did,
                    "name": f"1/{p // 12 + 1}/{p % 12 + 1}",
                    "label": f"PATCH-{p + 1:02d}",
                    "type": "lc",
                    "createdAt": now,
                    "updatedAt": now,
                    "deletedAt": None,
                },
            )
            rp_rows.append(
                {
                    "id": uuid.uuid4(),
                    "deviceId": did,
                    "name": f"RP-{p + 1:02d}",
                    "label": None,
                    "type": "lc",
                    "createdAt": now,
                    "updatedAt": now,
                    "deletedAt": None,
                },
            )
    for chunk in _chunked(fp_rows, batch):
        session.execute(insert(FrontPort), chunk)
    for chunk in _chunked(rp_rows, batch):
        session.execute(insert(RearPort), chunk)

    # --- PDU outlets + device power ports + connections ---
    po_rows: list[dict[str, object]] = []
    pp_rows: list[dict[str, object]] = []
    pwr_conn: list[dict[str, object]] = []
    rack_pdu_outlets: dict[int, list[uuid.UUID]] = {}

    for ri, _rack_id in enumerate(rack_ids):
        si = rack_site_idx[ri]
        rk_in_site = ri % racks_per_site
        pdu_id = next(
            (m[3] for m in device_meta if m[0] == si and m[1] == rk_in_site and m[4] == "pdu"),
            None,
        )
        if pdu_id is None:
            continue
        outs: list[uuid.UUID] = []
        for o in range(48):
            oid = uuid.uuid4()
            outs.append(oid)
            po_rows.append(
                {
                    "id": oid,
                    "deviceId": pdu_id,
                    "name": f"OUT-{o + 1:02d}",
                    "label": f"{208 + (o % 2) * 4}V/16A",
                    "createdAt": now,
                    "updatedAt": now,
                    "deletedAt": None,
                },
            )
        rack_pdu_outlets[ri] = outs

    for ri, _rack_id in enumerate(rack_ids):
        if ri not in rack_pdu_outlets:
            continue
        outs = rack_pdu_outlets[ri]
        si = rack_site_idx[ri]
        rk_in_site = ri % racks_per_site
        powered = [
            m[3]
            for m in device_meta
            if m[0] == si and m[1] == rk_in_site and m[4] not in ("pdu", "blade")
        ]
        for j, did in enumerate(powered):
            oid = outs[j % len(outs)]
            port_id = uuid.uuid4()
            pp_rows.append(
                {
                    "id": port_id,
                    "deviceId": did,
                    "name": "PSU0",
                    "label": "C14 inlet",
                    "createdAt": now,
                    "updatedAt": now,
                    "deletedAt": None,
                },
            )
            pwr_conn.append(
                {
                    "id": uuid.uuid4(),
                    "organizationId": org_id,
                    "outletId": oid,
                    "portId": port_id,
                    "name": f"A-feed-{did.hex[:6]}",
                    "createdAt": now,
                    "updatedAt": now,
                    "deletedAt": None,
                },
            )

    for chunk in _chunked(po_rows, batch):
        session.execute(insert(PowerOutlet), chunk)
    for chunk in _chunked(pp_rows, batch):
        session.execute(insert(PowerPort), chunk)
    for chunk in _chunked(pwr_conn, batch):
        session.execute(insert(PowerConnection), chunk)

    # --- OOB console server: map ttyS* on OOB to console on each peer ---
    csp_rows: list[dict[str, object]] = []
    cp_rows: list[dict[str, object]] = []
    cc_rows: list[dict[str, object]] = []

    for ri, rack_id in enumerate(rack_ids):
        si = rack_site_idx[ri]
        rk_in_site = ri % racks_per_site
        peers = [m[3] for m in device_meta if m[0] == si and m[1] == rk_in_site and m[4] != "oob"]
        oob = next((m[3] for m in device_meta if m[0] == si and m[1] == rk_in_site and m[4] == "oob"), None)
        if oob is None or not peers:
            continue
        for j, tgt in enumerate(peers):
            spid = uuid.uuid4()
            csp_rows.append(
                {
                    "id": spid,
                    "deviceId": oob,
                    "name": f"ttyS{j}",
                    "label": None,
                    "createdAt": now,
                    "updatedAt": now,
                    "deletedAt": None,
                },
            )
            cpid = uuid.uuid4()
            cp_rows.append(
                {
                    "id": cpid,
                    "deviceId": tgt,
                    "name": "console",
                    "label": None,
                    "createdAt": now,
                    "updatedAt": now,
                    "deletedAt": None,
                },
            )
            cc_rows.append(
                {
                    "id": uuid.uuid4(),
                    "organizationId": org_id,
                    "serverPortId": spid,
                    "clientPortId": cpid,
                    "name": f"con-{tgt.hex[:6]}",
                    "createdAt": now,
                    "updatedAt": now,
                    "deletedAt": None,
                },
            )

    for chunk in _chunked(csp_rows, batch):
        session.execute(insert(ConsoleServerPort), chunk)
    for chunk in _chunked(cp_rows, batch):
        session.execute(insert(ConsolePort), chunk)
    for chunk in _chunked(cc_rows, batch):
        session.execute(insert(ConsoleConnection), chunk)

    # --- BMC controllers on PE routers ---
    ctl_rows: list[dict[str, object]] = []
    for si, rk, _sl, did, kind, _n in device_meta:
        if kind != "core":
            continue
        ctl_rows.append(
            {
                "id": uuid.uuid4(),
                "organizationId": org_id,
                "deviceId": did,
                "name": "re0-mgmt",
                "description": "Routing Engine out-of-band",
                "role": "routing-engine",
                "createdAt": now,
                "updatedAt": now,
                "deletedAt": None,
            },
        )
    for chunk in _chunked(ctl_rows, batch):
        session.execute(insert(Controller), chunk)

    # --- Circuits: sequential + ring + multi-segment sample ---
    circ_rows: list[dict[str, object]] = []
    seg_rows: list[dict[str, object]] = []
    term_rows: list[dict[str, object]] = []

    def add_circuit(
        *,
        g: int,
        h: int,
        pid: uuid.UUID,
        cid_str: str,
        bw: int,
        ct: Any,
        seg_count: int,
        a_note: str,
        z_note: str,
    ) -> None:
        cid = uuid.uuid4()
        circ_rows.append(
            {
                "id": cid,
                "organizationId": org_id,
                "providerId": pid,
                "circuitTypeId": ct.id,
                "cid": cid_str,
                "bandwidthMbps": bw,
                "status": Circuitstatus.ACTIVE,
                "aSideNotes": a_note,
                "zSideNotes": z_note,
                "createdAt": now,
                "updatedAt": now,
                "deletedAt": None,
            },
        )
        for s in range(seg_count):
            seg_rows.append(
                {
                    "id": uuid.uuid4(),
                    "circuitId": cid,
                    "segmentIndex": s,
                    "label": "primary" if s == 0 else f"diverse-{s}",
                    "providerId": provider_ids[(g + s) % len(provider_ids)],
                    "bandwidthMbps": bw,
                    "status": Circuitstatus.ACTIVE,
                    "aSideNotes": None,
                    "zSideNotes": None,
                    "createdAt": now,
                    "updatedAt": now,
                },
            )
        loc_a = site_ids[g]
        loc_b = site_ids[h]
        term_rows.append(
            {
                "id": uuid.uuid4(),
                "organizationId": org_id,
                "circuitId": cid,
                "side": "A",
                "locationId": loc_a,
                "portName": "xe-0/0/6",
                "description": "NNI handoff — toward backbone",
                "createdAt": now,
                "updatedAt": now,
                "deletedAt": None,
            },
        )
        term_rows.append(
            {
                "id": uuid.uuid4(),
                "organizationId": org_id,
                "circuitId": cid,
                "side": "Z",
                "locationId": loc_b,
                "portName": "xe-0/0/6",
                "description": "NNI handoff — toward backbone",
                "createdAt": now,
                "updatedAt": now,
                "deletedAt": None,
            },
        )

    ns = len(site_ids)
    for g in range(ns - 1):
        pid = provider_ids[g % len(provider_ids)]
        add_circuit(
            g=g,
            h=g + 1,
            pid=pid,
            cid_str=f"NNI-{site_codes[g].upper()}-TO-{site_codes[g + 1].upper()}",
            bw=10_000 if g % 4 == 0 else 1_000,
            ct=ct_eth,
            seg_count=2 if g % 11 == 0 else 1,
            a_note=f"POP {site_codes[g]}",
            z_note=f"POP {site_codes[g + 1]}",
        )
    if ns > 2:
        add_circuit(
            g=ns - 1,
            h=0,
            pid=provider_ids[0],
            cid_str=f"RING-CLOSE-{site_codes[-1].upper()}-TO-{site_codes[0].upper()}",
            bw=40_000,
            ct=ct_dark,
            seg_count=1,
            a_note="Ring diversity",
            z_note="Ring diversity",
        )

    for chunk in _chunked(circ_rows, batch):
        session.execute(insert(Circuit), chunk)
    for chunk in _chunked(seg_rows, batch):
        session.execute(insert(CircuitSegment), chunk)
    for chunk in _chunked(term_rows, batch):
        session.execute(insert(CircuitTermination), chunk)

    # --- VLANs ---
    vlan_rows: list[dict[str, object]] = []
    for vid, label in ((100, "TRANSPORT-INNER"), (666, "PEERING-IX"), (4093, "OOB-MGMT-NATIVE")):
        vlan_rows.append(
            {
                "id": uuid.uuid4(),
                "organizationId": org_id,
                "vlanGroupId": vg.id,
                "vid": vid,
                "name": label,
                "createdAt": now,
                "updatedAt": now,
                "deletedAt": None,
            },
        )
    for chunk in _chunked(vlan_rows, batch):
        session.execute(insert(Vlan), chunk)

    # --- IP addressing: loopbacks from 10.255/16; link IPs from 10.0/8 tree ---
    ip_rows: list[dict[str, object]] = []
    ip_i = 1
    for si, rk, _sl, did, kind, _n in device_meta:
        if kind == "pdu":
            continue
        if did in lo_iface_by_dev:
            lo = lo_iface_by_dev[did]
            a = (ip_i >> 8) & 255
            b = ip_i & 255
            ip_rows.append(
                {
                    "id": uuid.uuid4(),
                    "organizationId": org_id,
                    "prefixId": pfx_lo.id,
                    "address": f"10.255.{a}.{b}",
                    "description": "Loopback / system",
                    "interfaceId": lo,
                    "createdAt": now,
                    "updatedAt": now,
                    "deletedAt": None,
                },
            )
            ip_i += 1
        for j in range(1, min(4, len(iface_by_dev[did]))):
            iid = iface_by_dev[did][j]
            x = (ip_i >> 16) & 255
            y = (ip_i >> 8) & 255
            z = ip_i & 255
            ip_rows.append(
                {
                    "id": uuid.uuid4(),
                    "organizationId": org_id,
                    "prefixId": pfx.id,
                    "address": f"10.{x}.{y}.{z}",
                    "description": "Unit / link",
                    "interfaceId": iid,
                    "createdAt": now,
                    "updatedAt": now,
                    "deletedAt": None,
                },
            )
            ip_i += 1

    for chunk in _chunked(ip_rows, batch):
        session.execute(insert(IpAddress), chunk)

    # --- Tags on devices ---
    ta_rows: list[dict[str, object]] = []
    seen_tags: set[tuple[uuid.UUID, uuid.UUID]] = set()
    for si, rk, _sl, did, kind, _n in device_meta:
        if kind == "blade":
            continue
        if kind == "core":
            slugs = ("managed", "prod", "bb")
        elif kind == "edge":
            slugs = ("managed", "prod")
        elif kind == "oob":
            slugs = ("managed", "stg")
        elif kind == "pdu":
            slugs = ("managed", "prod")
        else:
            slugs = ("managed",)
        for slug in slugs:
            tid = tag_ids[slug]
            key = (tid, did)
            if key in seen_tags:
                continue
            seen_tags.add(key)
            ta_rows.append(
                {
                    "id": uuid.uuid4(),
                    "tagId": tid,
                    "resourceType": "Device",
                    "resourceId": did,
                },
            )
    for chunk in _chunked(ta_rows, batch):
        session.execute(insert(TagAssignment), chunk)

    # --- Device groups (one per site) ---
    dg_site: list[dict[str, object]] = []
    dgm_site: list[dict[str, object]] = []
    for si, loc in enumerate(site_ids):
        gid = uuid.uuid4()
        dg_site.append(
            {
                "id": gid,
                "organizationId": org_id,
                "name": f"Fabric — {site_codes[si].upper()}",
                "slug": f"fabric-{site_codes[si]}",
                "description": "All devices in POP (sim)",
                "createdAt": now,
                "updatedAt": now,
                "deletedAt": None,
            },
        )
        for m in device_meta:
            if m[0] == si and m[4] != "blade":
                dgm_site.append(
                    {
                        "id": uuid.uuid4(),
                        "groupId": gid,
                        "deviceId": m[3],
                    },
                )
    for chunk in _chunked(dg_site, batch):
        session.execute(insert(DeviceGroup), chunk)
    for chunk in _chunked(dgm_site, batch):
        session.execute(insert(DeviceGroupMember), chunk)

    # --- Inventory optics ---
    inv_rows: list[dict[str, object]] = []
    for si, rk, _sl, did, kind, _n in device_meta:
        if kind not in ("core", "edge"):
            continue
        if hash(str(did)) % 3 != 0:
            continue
        inv_rows.append(
            {
                "id": uuid.uuid4(),
                "organizationId": org_id,
                "deviceId": did,
                "name": "SFP-10G-SR",
                "serial": f"OPT-{did.hex[:10].upper()}",
                "assetTag": f"AT-{did.hex[:8]}",
                "description": "10GBASE-SR optic (sim)",
                "createdAt": now,
                "updatedAt": now,
                "deletedAt": None,
            },
        )
    for chunk in _chunked(inv_rows, batch):
        session.execute(insert(InventoryItem), chunk)

    # --- Observed telemetry ---
    obs_rows: list[dict[str, object]] = []
    for si, rk, _sl, did, kind, _n in device_meta:
        if kind == "blade":
            continue
        obs_rows.append(
            {
                "id": uuid.uuid4(),
                "organizationId": org_id,
                "kind": Observationkind.DEVICE,
                "deviceId": did,
                "lastSeenAt": now,
                "health": "ok",
                "payload": {"telemetry": "streaming", "snmp": "v3", "pop": site_codes[si]},
                "driftDetected": False,
                "driftSummary": None,
                "updatedAt": now,
            },
        )
    for chunk in _chunked(obs_rows, batch):
        session.execute(insert(ObservedResourceState), chunk)

    return {
        "organization_id": str(org_id),
        "organization_slug": org_slug,
        "regions": num_regions,
        "sites": total_sites,
        "racks": len(rack_ids),
        "devices": len(device_meta),
        "interfaces": len(iface_rows),
        "cables": len(cable_rows),
        "circuits": len(circ_rows),
        "circuit_segments": len(seg_rows),
        "ip_addresses": len(ip_rows),
        "virtual_chassis": len(vc_rows),
        "mc_lag_groups": len(drg_rows),
        "ae_bundles": len(irg_rows),
        "power_connections": len(pwr_conn),
        "console_connections": len(cc_rows),
        "tags_assigned": len(ta_rows),
        "device_group_memberships": len(dgm_site),
        "inventory_items": len(inv_rows),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed synthetic carrier-scale inventory.")
    parser.add_argument(
        "--purge",
        action="store_true",
        help="Delete existing data for the bulk org before inserting (same slug).",
    )
    args = parser.parse_args()
    purge = args.purge or os.environ.get("PROVIDER_BULK_PURGE", "").lower() in ("1", "true", "yes")

    session = SessionLocal()
    try:
        stats = run_bulk_seed(session, purge=purge)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    print("\n=== Provider bulk seed complete ===")
    for k, v in stats.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
