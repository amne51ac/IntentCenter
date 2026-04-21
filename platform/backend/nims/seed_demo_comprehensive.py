"""Large-scale, catalog-complete demo inventory for the default `demo` organization.

Idempotent: the heavy device fleet is created once (detected via device names ``dfleet-*``).
Re-running seed skips the fleet but still expands global catalog rows if below targets.

Environment (all optional)::

  SEED_DEMO_FLEET=1           # 0 disables this module entirely
  SEED_DEVICE_COUNT=2500      # fleet routers/switches
  SEED_IFACE_PER_DEVICE=4
  SEED_IP_COUNT=12000         # unique host addresses in dfleet space
  SEED_CABLE_COUNT=6000
  SEED_VLAN_COUNT=600
  SEED_JOB_RUNS=250
  SEED_SERVICE_COUNT=300
"""

from __future__ import annotations

import ipaddress
import os
import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from nims.models_generated import (
    Cable,
    ChangeRequest,
    Changerequeststatus,
    Circuit,
    CircuitSegment,
    Circuitstatus,
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
    DeviceGroup,
    DeviceGroupMember,
    DeviceRedundancyGroup,
    DeviceRedundancyGroupMember,
    DeviceRole,
    Devicestatus,
    DeviceType,
    DynamicGroup,
    FrontPort,
    Interface,
    InterfaceRedundancyGroup,
    InterfaceRedundancyGroupMember,
    InventoryItem,
    IpAddress,
    IpamNamespace,
    JobDefinition,
    JobRun,
    Jobrunstatus,
    Location,
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
    Rack,
    RackGroup,
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
    Vrf,
    WirelessNetwork,
)


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or str(raw).strip() == "":
        return default
    return int(raw)


def _fleet_already_seeded(session: Session, org_id: uuid.UUID) -> bool:
    c = session.execute(
        select(func.count())
        .select_from(Device)
        .where(Device.organizationId == org_id, Device.name.like("dfleet-%")),
    ).scalar_one()
    return int(c) >= 50


def run_comprehensive_demo_inventory(session: Session, org: Organization, now: Any) -> dict[str, Any]:
    """Populate globals + (once) thousands of fleet devices, interfaces, IPs, cables, etc."""
    if os.environ.get("SEED_DEMO_FLEET", "1").strip().lower() in ("0", "false", "no"):
        return {"skipped": True, "reason": "SEED_DEMO_FLEET disabled"}

    oid = org.id
    stats: dict[str, Any] = {"globals": 0, "fleet": False}

    # --- Global catalog (always try to enrich; idempotent by unique names) ---
    mfg_ids: list[uuid.UUID] = []
    for i in range(24):
        name = f"Seed OEM {i + 1:02d}"
        m = session.execute(select(Manufacturer).where(Manufacturer.name == name)).scalar_one_or_none()
        if m is None:
            m = Manufacturer(id=uuid.uuid4(), name=name)
            session.add(m)
            session.flush()
        mfg_ids.append(m.id)
        stats["globals"] += 1

    dt_ids: list[uuid.UUID] = []
    for mi, mfg in enumerate(mfg_ids[:12]):
        for k in range(3):
            model = f"XR-{mi + 1}-{k + 1}RU"
            dt = session.execute(
                select(DeviceType).where(DeviceType.manufacturerId == mfg, DeviceType.model == model),
            ).scalar_one_or_none()
            if dt is None:
                dt = DeviceType(id=uuid.uuid4(), manufacturerId=mfg, model=model, uHeight=k + 1)
                session.add(dt)
                session.flush()
            dt_ids.append(dt.id)

    role_names = ["pe", "p", "ce", "spine", "leaf", "oob", "border", "storage", "hypervisor", "wan"]
    role_ids: list[uuid.UUID] = []
    for rn in role_names:
        r = session.execute(select(DeviceRole).where(DeviceRole.name == rn)).scalar_one_or_none()
        if r is None:
            r = DeviceRole(id=uuid.uuid4(), name=rn)
            session.add(r)
            session.flush()
        role_ids.append(r.id)

    rir_specs = [
        ("RIPE NCC", "ripe", "Europe"),
        ("APNIC", "apnic", "Asia-Pacific"),
        ("LACNIC", "lacnic", "Latin America"),
        ("AFRINIC", "afrinic", "Africa"),
    ]
    for nm, slug, desc in rir_specs:
        if session.execute(select(Rir).where(Rir.slug == slug)).scalar_one_or_none() is None:
            session.add(Rir(id=uuid.uuid4(), name=nm, slug=slug, description=desc))

    for slug, title in (
        ("wave-100g", "100G Wave"),
        ("mpls-l3vpn", "MPLS L3VPN"),
        ("evpn-vxlan", "EVPN/VXLAN fabric"),
        ("dark-fiber-ring", "Dark fiber ring"),
    ):
        if session.execute(select(CircuitType).where(CircuitType.slug == slug)).scalar_one_or_none() is None:
            session.add(
                CircuitType(
                    id=uuid.uuid4(),
                    name=title,
                    slug=slug,
                    description="Demo circuit taxonomy",
                ),
            )

    for vg_name in ("Metro access", "Data center", "OOB / management", "Storage fabric"):
        if session.execute(select(VlanGroup).where(VlanGroup.name == vg_name)).scalar_one_or_none() is None:
            session.add(VlanGroup(id=uuid.uuid4(), name=vg_name))

    plat_slugs = [("junos", "Junos"), ("eos", "EOS"), ("nxos", "NX-OS"), ("sonic", "SONiC")]
    plat_ids: list[uuid.UUID] = []
    for slug, title in plat_slugs:
        p = session.execute(select(SoftwarePlatform).where(SoftwarePlatform.slug == slug)).scalar_one_or_none()
        if p is None:
            p = SoftwarePlatform(id=uuid.uuid4(), name=title, slug=slug, description="Demo platform")
            session.add(p)
            session.flush()
        plat_ids.append(p.id)
        for ver in ("23.4R1", "4.30.1F", "10.3(3)", "20241115"):
            if (
                session.execute(
                    select(SoftwareVersion).where(SoftwareVersion.platformId == p.id, SoftwareVersion.version == ver),
                ).scalar_one_or_none()
                is None
            ):
                session.add(
                    SoftwareVersion(
                        id=uuid.uuid4(),
                        platformId=p.id,
                        version=ver,
                        releaseNotes="Seed build",
                        updatedAt=now,
                    ),
                )

    for i in range(8):
        mm = f"MOD-T-{i + 1:03d}"
        if session.execute(select(ModuleType).where(ModuleType.model == mm)).scalar_one_or_none() is None:
            session.add(
                ModuleType(
                    id=uuid.uuid4(),
                    manufacturerId=mfg_ids[i % len(mfg_ids)],
                    model=mm,
                    partNumber=f"PN-{i + 1:05d}",
                ),
            )

    session.flush()

    lt_site = session.execute(select(LocationType).where(LocationType.name == "Site")).scalar_one()
    lt_region = session.execute(select(LocationType).where(LocationType.name == "Region")).scalar_one_or_none()
    if lt_region is None:
        lt_region = LocationType(id=uuid.uuid4(), name="Region", description="Region")
        session.add(lt_region)
        session.flush()

    if not _fleet_already_seeded(session, oid):
        n_dev = _env_int("SEED_DEVICE_COUNT", 2500)
        n_iface = max(2, min(12, _env_int("SEED_IFACE_PER_DEVICE", 4)))
        n_ip = _env_int("SEED_IP_COUNT", 12000)
        n_cable = _env_int("SEED_CABLE_COUNT", 6000)
        n_vlan = _env_int("SEED_VLAN_COUNT", 600)
        n_job_runs = _env_int("SEED_JOB_RUNS", 250)
        n_svc = _env_int("SEED_SERVICE_COUNT", 300)
        
        # Facilities: region + many sites + racks
        region_loc = session.execute(
            select(Location).where(Location.organizationId == oid, Location.slug == "dfleet-region"),
        ).scalar_one_or_none()
        if region_loc is None:
            region_loc = Location(
                id=uuid.uuid4(),
                organizationId=oid,
                locationTypeId=lt_region.id,
                name="DFleet Americas",
                slug="dfleet-region",
                updatedAt=now,
                deletedAt=None,
            )
            session.add(region_loc)
            session.flush()
        
        n_sites = min(40, max(10, n_dev // 80))
        site_ids: list[uuid.UUID] = []
        for s in range(n_sites):
            slug = f"dfleet-site-{s:02d}"
            loc = session.execute(
                select(Location).where(Location.organizationId == oid, Location.slug == slug),
            ).scalar_one_or_none()
            if loc is None:
                loc = Location(
                    id=uuid.uuid4(),
                    organizationId=oid,
                    locationTypeId=lt_site.id,
                    parentId=region_loc.id,
                    name=f"POP {s:02d}",
                    slug=slug,
                    updatedAt=now,
                    deletedAt=None,
                )
                session.add(loc)
                session.flush()
            site_ids.append(loc.id)
        
        rack_ids: list[uuid.UUID] = []
        ridx = 0
        for site in site_ids:
            for _ in range(max(1, n_dev // max(1, len(site_ids) * 8))):
                rack_name = f"R-{ridx:04d}"
                rk = session.execute(
                    select(Rack).where(
                        Rack.organizationId == oid,
                        Rack.locationId == site,
                        Rack.name == rack_name,
                    ),
                ).scalar_one_or_none()
                if rk is None:
                    rk = Rack(
                        id=uuid.uuid4(),
                        organizationId=oid,
                        locationId=site,
                        name=rack_name,
                        uHeight=42,
                        updatedAt=now,
                        deletedAt=None,
                    )
                    session.add(rk)
                    session.flush()
                rack_ids.append(rk.id)
                ridx += 1
                if len(rack_ids) >= n_dev // 2:
                    break
            if len(rack_ids) >= n_dev // 2:
                break
        
        vrf_fleet = session.execute(
            select(Vrf).where(Vrf.organizationId == oid, Vrf.name == "dfleet-ip"),
        ).scalar_one_or_none()
        if vrf_fleet is None:
            vrf_fleet = Vrf(
                id=uuid.uuid4(),
                organizationId=oid,
                name="dfleet-ip",
                rd="65000:1",
                updatedAt=now,
                deletedAt=None,
            )
            session.add(vrf_fleet)
            session.flush()
        
        rir = session.execute(select(Rir).where(Rir.slug == "arin")).scalar_one()
        pfx_big = session.execute(
            select(Prefix).where(Prefix.organizationId == oid, Prefix.cidr == "172.16.0.0/12"),
        ).scalar_one_or_none()
        if pfx_big is None:
            pfx_big = Prefix(
                id=uuid.uuid4(),
                organizationId=oid,
                vrfId=vrf_fleet.id,
                cidr="172.16.0.0/12",
                description="Fleet demo aggregate",
                rirId=rir.id,
                updatedAt=now,
                deletedAt=None,
            )
            session.add(pfx_big)
            session.flush()
        
        net = ipaddress.ip_network("172.16.0.0/12")
        hosts = [str(h) for h in net.hosts()]
        if n_ip > len(hosts):
            n_ip = len(hosts)
        
        prov_bulk = session.execute(
            select(Provider).where(Provider.organizationId == oid, Provider.name == "dfleet-transit-1"),
        ).scalar_one_or_none()
        if prov_bulk is None:
            prov_bulk = Provider(
                id=uuid.uuid4(),
                organizationId=oid,
                name="dfleet-transit-1",
                asn=65000,
                updatedAt=now,
                deletedAt=None,
            )
            session.add(prov_bulk)
            session.flush()
        
        ct_eth = session.execute(select(CircuitType).where(CircuitType.slug == "wave-100g")).scalar_one()
        
        devices: list[tuple[uuid.UUID, uuid.UUID]] = []  # id, rack_id
        for i in range(n_dev):
            name = f"dfleet-{i:05d}"
            rack_id = rack_ids[i % len(rack_ids)]
            dt_id = dt_ids[i % len(dt_ids)]
            role_id = role_ids[i % len(role_ids)]
            d = Device(
                id=uuid.uuid4(),
                organizationId=oid,
                rackId=rack_id,
                deviceTypeId=dt_id,
                deviceRoleId=role_id,
                name=name,
                status=Devicestatus.ACTIVE,
                positionU=(i % 40) + 1,
                face="front",
                serialNumber=f"SN{i:010d}",
                updatedAt=now,
                deletedAt=None,
            )
            session.add(d)
            devices.append((d.id, rack_id))
            if (i + 1) % 400 == 0:
                session.flush()
        
        session.flush()
        
        ifaces: list[uuid.UUID] = []
        for idx, (did, _) in enumerate(devices):
            for j in range(n_iface):
                iface = Interface(
                    id=uuid.uuid4(),
                    deviceId=did,
                    name=f"eth{j}",
                    type="ethernet",
                    enabled=True,
                    updatedAt=now,
                    deletedAt=None,
                )
                session.add(iface)
                ifaces.append(iface.id)
            if (idx + 1) % 200 == 0:
                session.flush()
        session.flush()
        
        for i in range(n_ip):
            session.add(
                IpAddress(
                    id=uuid.uuid4(),
                    organizationId=oid,
                    prefixId=pfx_big.id,
                    address=hosts[i],
                    description=f"auto {i}",
                    interfaceId=ifaces[i % len(ifaces)] if ifaces else None,
                    updatedAt=now,
                    deletedAt=None,
                ),
            )
            if (i + 1) % 500 == 0:
                session.flush()
        session.flush()
        
        vg = session.execute(select(VlanGroup).where(VlanGroup.name == "Metro access")).scalar_one()
        for v in range(min(n_vlan, 3900)):
            vid = 100 + v
            if (
                session.execute(select(Vlan).where(Vlan.organizationId == oid, Vlan.vid == vid)).scalar_one_or_none()
                is None
            ):
                session.add(
                    Vlan(
                        id=uuid.uuid4(),
                        organizationId=oid,
                        vid=vid,
                        name=f"VLAN-{vid}",
                        vlanGroupId=vg.id,
                        updatedAt=now,
                        deletedAt=None,
                    ),
                )
            if (v + 1) % 400 == 0:
                session.flush()
        session.flush()
        
        for i in range(min(n_cable, len(ifaces) // 2)):
            a = ifaces[i * 2]
            b = ifaces[i * 2 + 1]
            session.add(
                Cable(
                    id=uuid.uuid4(),
                    interfaceAId=a,
                    interfaceBId=b,
                    label=f"patch-{i:05d}",
                    updatedAt=now,
                    deletedAt=None,
                ),
            )
            if (i + 1) % 500 == 0:
                session.flush()
        session.flush()
        
        jd = session.execute(select(JobDefinition).where(JobDefinition.organizationId == oid, JobDefinition.key == "noop")).scalar_one()
        for jr in range(n_job_runs):
            session.add(
                JobRun(
                    id=uuid.uuid4(),
                    organizationId=oid,
                    jobDefinitionId=jd.id,
                    status=Jobrunstatus.SUCCEEDED,
                    input={"batch": jr},
                    output={"ok": True},
                    logs=f"Simulated run {jr}",
                    correlationId=f"dfleet-jr-{jr:05d}",
                    updatedAt=now,
                ),
            )
            if (jr + 1) % 100 == 0:
                session.flush()
        session.flush()
        
        for si in range(n_svc):
            session.add(
                ServiceInstance(
                    id=uuid.uuid4(),
                    organizationId=oid,
                    name=f"dfleet-svc-{si:04d}",
                    serviceType="l3vpn" if si % 2 == 0 else "internet",
                    status="active",
                    customerRef=f"CUST-{si % 500:04d}",
                    updatedAt=now,
                    deletedAt=None,
                ),
            )
            if (si + 1) % 200 == 0:
                session.flush()
        session.flush()
        
        tag = session.execute(select(Tag).where(Tag.organizationId == oid, Tag.slug == "dfleet")).scalar_one_or_none()
        if tag is None:
            tag = Tag(
                id=uuid.uuid4(),
                organizationId=oid,
                name="dfleet",
                slug="dfleet",
                color="#888888",
                description="Mass fleet tag",
                updatedAt=now,
                deletedAt=None,
            )
            session.add(tag)
            session.flush()
        for di, (dev_id, _) in enumerate(devices[: min(4000, len(devices))]):
            if (
                session.execute(
                    select(TagAssignment).where(
                        TagAssignment.tagId == tag.id,
                        TagAssignment.resourceType == "Device",
                        TagAssignment.resourceId == dev_id,
                    ),
                ).scalar_one_or_none()
                is None
            ):
                session.add(TagAssignment(id=uuid.uuid4(), tagId=tag.id, resourceType="Device", resourceId=dev_id))
            if (di + 1) % 500 == 0:
                session.flush()
        
        # Circuits + segments + terminations (bulk)
        for ci in range(min(400, n_dev // 6)):
            cid = f"dfleet-circ-{ci:05d}"
            if session.execute(select(Circuit).where(Circuit.organizationId == oid, Circuit.cid == cid)).scalar_one_or_none():
                continue
            c = Circuit(
                id=uuid.uuid4(),
                organizationId=oid,
                providerId=prov_bulk.id,
                cid=cid,
                status=Circuitstatus.ACTIVE,
                bandwidthMbps=10000,
                circuitTypeId=ct_eth.id,
                updatedAt=now,
                deletedAt=None,
            )
            session.add(c)
            session.flush()
            session.add(
                CircuitSegment(
                    id=uuid.uuid4(),
                    circuitId=c.id,
                    segmentIndex=0,
                    status=Circuitstatus.ACTIVE,
                    providerId=prov_bulk.id,
                    label="primary path",
                    bandwidthMbps=10000,
                    updatedAt=now,
                ),
            )
            loc = site_ids[ci % len(site_ids)]
            session.add(
                CircuitTermination(
                    id=uuid.uuid4(),
                    organizationId=oid,
                    circuitId=c.id,
                    side="A",
                    locationId=loc,
                    portName="xe-0/0/0",
                    updatedAt=now,
                    deletedAt=None,
                ),
            )
            session.add(
                CircuitTermination(
                    id=uuid.uuid4(),
                    organizationId=oid,
                    circuitId=c.id,
                    side="Z",
                    locationId=site_ids[(ci + 1) % len(site_ids)],
                    portName="xe-0/0/1",
                    updatedAt=now,
                    deletedAt=None,
                ),
            )
            if (ci + 1) % 50 == 0:
                session.flush()
        session.flush()
        stats["fleet"] = True
        stats["devices"] = n_dev
        stats["interfaces"] = len(ifaces)
        stats["ips"] = n_ip
        stats["cables"] = min(n_cable, len(ifaces) // 2)
        stats["vlans"] = min(n_vlan, 3900)
    else:
        stats["fleet"] = False
        stats["note"] = "dfleet fleet already present; skipped heavy insert."

    _ensure_coverage_extras(session, oid, now, lt_site, lt_region, plat_ids[0])
    return stats


def _ensure_coverage_extras(
    session: Session,
    oid: uuid.UUID,
    now: Any,
    lt_site: LocationType,
    lt_region: LocationType,
    platform_id: uuid.UUID,
) -> None:
    """One-time style rows for every catalog area not filled by the fleet block."""

    def _proj(slug: str, title: str) -> None:
        if session.execute(select(Project).where(Project.organizationId == oid, Project.slug == slug)).scalar_one_or_none():
            return
        session.add(Project(id=uuid.uuid4(), organizationId=oid, name=title, slug=slug, updatedAt=now, deletedAt=None))

    for slug, title in (
        ("dfleet-project-a", "DFleet Project A"),
        ("dfleet-project-b", "DFleet Project B"),
    ):
        _proj(slug, title)

    for name, slug in (("NOC On-call", "noc-oncall"), ("Field Techs East", "field-east")):
        if session.execute(select(Team).where(Team.organizationId == oid, Team.slug == slug)).scalar_one_or_none() is None:
            session.add(Team(id=uuid.uuid4(), organizationId=oid, name=name, slug=slug, updatedAt=now, deletedAt=None))

    for i in range(40):
        em = f"coverage.contact.{i:03d}@demo.local"
        if session.execute(select(Contact).where(Contact.organizationId == oid, Contact.email == em)).scalar_one_or_none() is None:
            session.add(
                Contact(
                    id=uuid.uuid4(),
                    organizationId=oid,
                    name=f"Contact {i:03d}",
                    email=em,
                    title="Engineer",
                    updatedAt=now,
                    deletedAt=None,
                ),
            )

    for slug, title in (("tenant-grp-a", "Enterprise tenants"), ("tenant-grp-b", "Lab tenants")):
        if session.execute(select(TenantGroup).where(TenantGroup.organizationId == oid, TenantGroup.slug == slug)).scalar_one_or_none() is None:
            session.add(
                TenantGroup(id=uuid.uuid4(), organizationId=oid, name=title, slug=slug, updatedAt=now, deletedAt=None),
            )

    if session.execute(select(DynamicGroup).where(DynamicGroup.organizationId == oid, DynamicGroup.slug == "dg-routers")).scalar_one_or_none() is None:
        session.add(
            DynamicGroup(
                id=uuid.uuid4(),
                organizationId=oid,
                name="All PE routers",
                slug="dg-routers",
                definition={"resourceType": "Device", "role": "pe"},
                updatedAt=now,
                deletedAt=None,
            ),
        )

    for i in range(5):
        slug = f"dfleet-rg-{i}"
        if session.execute(select(RackGroup).where(RackGroup.organizationId == oid, RackGroup.slug == slug)).scalar_one_or_none() is None:
            session.add(
                RackGroup(id=uuid.uuid4(), organizationId=oid, name=f"Rack group {i}", slug=slug, updatedAt=now, deletedAt=None),
            )

    for rt, sn in (("Device", "staged"), ("Rack", "reserved")):
        if (
            session.execute(
                select(StatusDefinition).where(
                    StatusDefinition.organizationId == oid,
                    StatusDefinition.resourceType == rt,
                    StatusDefinition.slug == sn,
                ),
            ).scalar_one_or_none()
            is None
        ):
            session.add(
                StatusDefinition(
                    id=uuid.uuid4(),
                    organizationId=oid,
                    resourceType=rt,
                    name=sn.title(),
                    slug=sn,
                    updatedAt=now,
                ),
            )

    for i in range(6):
        slug = f"ns-{i}"
        if session.execute(select(IpamNamespace).where(IpamNamespace.organizationId == oid, IpamNamespace.slug == slug)).scalar_one_or_none() is None:
            session.add(
                IpamNamespace(
                    id=uuid.uuid4(),
                    organizationId=oid,
                    name=f"Namespace {i}",
                    slug=slug,
                    updatedAt=now,
                    deletedAt=None,
                ),
            )

    vrf_mpls = session.execute(select(Vrf).where(Vrf.organizationId == oid, Vrf.name == "dfleet-mpls")).scalar_one_or_none()
    if vrf_mpls is None:
        vrf_mpls = Vrf(
            id=uuid.uuid4(),
            organizationId=oid,
            name="dfleet-mpls",
            rd="65000:100",
            updatedAt=now,
            deletedAt=None,
        )
        session.add(vrf_mpls)
        session.flush()

    if session.execute(select(MplsDomain).where(MplsDomain.organizationId == oid, MplsDomain.name == "dfleet-mpls-domain")).scalar_one_or_none() is None:
        session.add(
            MplsDomain(
                id=uuid.uuid4(),
                organizationId=oid,
                name="dfleet-mpls-domain",
                rd="65000:0",
                description="Demo MPLS core",
                updatedAt=now,
                deletedAt=None,
            ),
        )

    if (
        session.execute(
            select(RouteTarget).where(RouteTarget.organizationId == oid, RouteTarget.name == "65000:1000"),
        ).scalar_one_or_none()
        is None
    ):
        session.add(
            RouteTarget(
                id=uuid.uuid4(),
                organizationId=oid,
                vrfId=vrf_mpls.id,
                name="65000:1000",
                description="VPN-A RT",
                updatedAt=now,
                deletedAt=None,
            ),
        )

    cn = session.execute(select(CloudNetwork).where(CloudNetwork.organizationId == oid, CloudNetwork.name == "dfleet-aws")).scalar_one_or_none()
    if cn is None:
        cn = CloudNetwork(
            id=uuid.uuid4(),
            organizationId=oid,
            name="dfleet-aws",
            cloudProvider="aws",
            description="Simulated VPC space",
            updatedAt=now,
            deletedAt=None,
        )
        session.add(cn)
        session.flush()
    if session.execute(select(CloudService).where(CloudService.organizationId == oid, CloudService.name == "eks-demo")).scalar_one_or_none() is None:
        session.add(
            CloudService(
                id=uuid.uuid4(),
                organizationId=oid,
                name="eks-demo",
                cloudNetworkId=cn.id,
                serviceType="kubernetes",
                updatedAt=now,
                deletedAt=None,
            ),
        )

    if session.execute(select(WirelessNetwork).where(WirelessNetwork.organizationId == oid, WirelessNetwork.name == "dfleet-wifi")).scalar_one_or_none() is None:
        session.add(
            WirelessNetwork(
                id=uuid.uuid4(),
                organizationId=oid,
                name="dfleet-wifi",
                ssid="CORP-WIFI",
                updatedAt=now,
                deletedAt=None,
            ),
        )

    if session.execute(select(Vpn).where(Vpn.organizationId == oid, Vpn.name == "dfleet-site-vpn")).scalar_one_or_none() is None:
        session.add(
            Vpn(
                id=uuid.uuid4(),
                organizationId=oid,
                name="dfleet-site-vpn",
                vpnType="ipsec",
                updatedAt=now,
                deletedAt=None,
            ),
        )

    cl = session.execute(select(Cluster).where(Cluster.organizationId == oid, Cluster.name == "dfleet-k8s")).scalar_one_or_none()
    if cl is None:
        cl = Cluster(
            id=uuid.uuid4(),
            organizationId=oid,
            name="dfleet-k8s",
            clusterType="kubernetes",
            updatedAt=now,
            deletedAt=None,
        )
        session.add(cl)
        session.flush()

    for vm_i in range(120):
        nm = f"dfleet-vm-{vm_i:04d}"
        if session.execute(select(VirtualMachine).where(VirtualMachine.organizationId == oid, VirtualMachine.name == nm)).scalar_one_or_none() is None:
            session.add(
                VirtualMachine(
                    id=uuid.uuid4(),
                    organizationId=oid,
                    name=nm,
                    clusterId=cl.id,
                    updatedAt=now,
                    deletedAt=None,
                ),
            )

    # Virtual chassis + redundancy (small)
    devs = session.execute(
        select(Device.id).where(Device.organizationId == oid, Device.name.like("dfleet-%")).limit(8),
    ).scalars().all()
    if len(devs) >= 4:
        vc = session.execute(select(VirtualChassis).where(VirtualChassis.organizationId == oid, VirtualChassis.name == "dfleet-vc-1")).scalar_one_or_none()
        if vc is None:
            vc = VirtualChassis(id=uuid.uuid4(), organizationId=oid, name="dfleet-vc-1", domainId="DF1", updatedAt=now, deletedAt=None)
            session.add(vc)
            session.flush()
            for prio, did in enumerate(devs[:2]):
                session.add(
                    VirtualChassisMember(
                        id=uuid.uuid4(),
                        virtualChassisId=vc.id,
                        deviceId=did,
                        priority=prio,
                    ),
                )

    drg = session.execute(
        select(DeviceRedundancyGroup).where(DeviceRedundancyGroup.organizationId == oid, DeviceRedundancyGroup.name == "dfleet-ha"),
    ).scalar_one_or_none()
    if drg is None and len(devs) >= 2:
        drg = DeviceRedundancyGroup(
            id=uuid.uuid4(),
            organizationId=oid,
            name="dfleet-ha",
            protocol="mc-lag",
            updatedAt=now,
            deletedAt=None,
        )
        session.add(drg)
        session.flush()
        for did in devs[:2]:
            session.add(DeviceRedundancyGroupMember(id=uuid.uuid4(), groupId=drg.id, deviceId=did, role="member"))

    # Device group + members
    dg = session.execute(select(DeviceGroup).where(DeviceGroup.organizationId == oid, DeviceGroup.slug == "dfleet-edge")).scalar_one_or_none()
    if dg is None and len(devs) >= 3:
        dg = DeviceGroup(
            id=uuid.uuid4(),
            organizationId=oid,
            name="DFleet edge",
            slug="dfleet-edge",
            updatedAt=now,
            deletedAt=None,
        )
        session.add(dg)
        session.flush()
        for did in devs[:5]:
            if (
                session.execute(
                    select(DeviceGroupMember).where(DeviceGroupMember.groupId == dg.id, DeviceGroupMember.deviceId == did),
                ).scalar_one_or_none()
                is None
            ):
                session.add(DeviceGroupMember(id=uuid.uuid4(), groupId=dg.id, deviceId=did))

    # Ports + connections (subset)
    if len(devs) >= 2:
        d1 = devs[0]
        d2 = devs[1]
        cp1 = session.execute(select(ConsolePort).where(ConsolePort.deviceId == d1, ConsolePort.name == "console")).scalar_one_or_none()
        if cp1 is None:
            cp1 = ConsolePort(id=uuid.uuid4(), deviceId=d1, name="console", updatedAt=now, deletedAt=None)
            session.add(cp1)
            session.flush()
        sp = session.execute(select(ConsoleServerPort).where(ConsoleServerPort.deviceId == d2, ConsoleServerPort.name == "ttyS1")).scalar_one_or_none()
        if sp is None:
            sp = ConsoleServerPort(id=uuid.uuid4(), deviceId=d2, name="ttyS1", updatedAt=now, deletedAt=None)
            session.add(sp)
            session.flush()
        if (
            session.execute(
                select(ConsoleConnection).where(
                    ConsoleConnection.organizationId == oid,
                    ConsoleConnection.clientPortId == cp1.id,
                ),
            ).scalar_one_or_none()
            is None
        ):
            session.add(
                ConsoleConnection(
                    id=uuid.uuid4(),
                    organizationId=oid,
                    clientPortId=cp1.id,
                    serverPortId=sp.id,
                    updatedAt=now,
                    deletedAt=None,
                ),
            )

        pp = session.execute(select(PowerPort).where(PowerPort.deviceId == d1, PowerPort.name == "psu0")).scalar_one_or_none()
        po = session.execute(select(PowerOutlet).where(PowerOutlet.deviceId == d2, PowerOutlet.name == "out1")).scalar_one_or_none()
        if pp is None:
            pp = PowerPort(id=uuid.uuid4(), deviceId=d1, name="psu0", updatedAt=now, deletedAt=None)
            session.add(pp)
            session.flush()
        if po is None:
            po = PowerOutlet(id=uuid.uuid4(), deviceId=d2, name="out1", updatedAt=now, deletedAt=None)
            session.add(po)
            session.flush()
        if (
            session.execute(
                select(PowerConnection).where(PowerConnection.organizationId == oid, PowerConnection.portId == pp.id),
            ).scalar_one_or_none()
            is None
        ):
            session.add(
                PowerConnection(
                    id=uuid.uuid4(),
                    organizationId=oid,
                    portId=pp.id,
                    outletId=po.id,
                    updatedAt=now,
                    deletedAt=None,
                ),
            )

    # Power panel + feed (first site location)
    loc0 = session.execute(select(Location).where(Location.organizationId == oid, Location.slug == "dfleet-site-00")).scalar_one_or_none()
    if loc0:
        ppanel = session.execute(
            select(PowerPanel).where(PowerPanel.organizationId == oid, PowerPanel.name == "dfleet-panel-1"),
        ).scalar_one_or_none()
        if ppanel is None:
            ppanel = PowerPanel(
                id=uuid.uuid4(),
                organizationId=oid,
                locationId=loc0.id,
                name="dfleet-panel-1",
                updatedAt=now,
                deletedAt=None,
            )
            session.add(ppanel)
            session.flush()
            session.add(
                PowerFeed(
                    id=uuid.uuid4(),
                    organizationId=oid,
                    powerPanelId=ppanel.id,
                    name="feed-a",
                    updatedAt=now,
                    deletedAt=None,
                ),
            )

    # Software image files
    for fn in ("junos-arm64.tgz", "eos.swi"):
        if session.execute(select(SoftwareImageFile).where(SoftwareImageFile.organizationId == oid, SoftwareImageFile.filename == fn)).scalar_one_or_none() is None:
            session.add(
                SoftwareImageFile(
                    id=uuid.uuid4(),
                    organizationId=oid,
                    filename=fn,
                    platformId=platform_id,
                    sha256="0" * 64,
                    updatedAt=now,
                    deletedAt=None,
                ),
            )

    # Inventory + module bays (prefer a dfleet device; else core-01 from base seed)
    d0 = session.execute(select(Device.id).where(Device.organizationId == oid, Device.name.like("dfleet-%")).limit(1)).scalar_one_or_none()
    if d0 is None:
        d0 = session.execute(
            select(Device.id).where(Device.organizationId == oid, Device.name == "core-01"),
        ).scalar_one_or_none()
    mt0 = session.execute(select(ModuleType).limit(1)).scalar_one_or_none()
    if d0 and mt0:
        mb = session.execute(select(ModuleBay).where(ModuleBay.deviceId == d0, ModuleBay.name == "0")).scalar_one_or_none()
        if mb is None:
            mb = ModuleBay(id=uuid.uuid4(), deviceId=d0, name="0", position=0, updatedAt=now, deletedAt=None)
            session.add(mb)
            session.flush()
        mod_row = session.execute(select(Module).where(Module.organizationId == oid, Module.deviceId == d0)).scalar_one_or_none()
        if mod_row is None:
            session.add(
                Module(
                    id=uuid.uuid4(),
                    organizationId=oid,
                    deviceId=d0,
                    moduleTypeId=mt0.id,
                    moduleBayId=mb.id,
                    serial="MODSERIAL1",
                    updatedAt=now,
                    deletedAt=None,
                ),
            )
            session.flush()
            mod_row = session.execute(select(Module).where(Module.organizationId == oid, Module.deviceId == d0)).scalar_one()
        elif mod_row.moduleBayId is None:
            mod_row.moduleBayId = mb.id
            mod_row.updatedAt = now
        # Nested slot on the line card → sub-card with a front port (demo tree)
        if mod_row:
            nb = session.execute(
                select(ModuleBay).where(ModuleBay.parentModuleId == mod_row.id, ModuleBay.name == "nested-0"),
            ).scalar_one_or_none()
            if nb is None:
                nb = ModuleBay(
                    id=uuid.uuid4(),
                    parentModuleId=mod_row.id,
                    name="nested-0",
                    position=0,
                    updatedAt=now,
                    deletedAt=None,
                )
                session.add(nb)
                session.flush()
            if session.execute(select(Module).where(Module.moduleBayId == nb.id)).scalar_one_or_none() is None:
                sub = Module(
                    id=uuid.uuid4(),
                    organizationId=oid,
                    deviceId=d0,
                    moduleTypeId=mt0.id,
                    moduleBayId=nb.id,
                    serial="MODSERIAL2",
                    updatedAt=now,
                    deletedAt=None,
                )
                session.add(sub)
                session.flush()
                if session.execute(
                    select(FrontPort).where(FrontPort.deviceId == d0, FrontPort.name == "lc-nested-fp1"),
                ).scalar_one_or_none() is None:
                    session.add(
                        FrontPort(
                            id=uuid.uuid4(),
                            deviceId=d0,
                            moduleId=sub.id,
                            name="lc-nested-fp1",
                            type="lc",
                            updatedAt=now,
                            deletedAt=None,
                        ),
                    )
        if session.execute(select(InventoryItem).where(InventoryItem.organizationId == oid, InventoryItem.name == "dfleet-spare-fan")).scalar_one_or_none() is None:
            session.add(
                InventoryItem(
                    id=uuid.uuid4(),
                    organizationId=oid,
                    deviceId=d0,
                    name="dfleet-spare-fan",
                    assetTag="AT-00001",
                    updatedAt=now,
                    deletedAt=None,
                ),
            )

    # Front/rear ports
    if d0:
        if session.execute(select(FrontPort).where(FrontPort.deviceId == d0, FrontPort.name == "fp1")).scalar_one_or_none() is None:
            session.add(FrontPort(id=uuid.uuid4(), deviceId=d0, name="fp1", type="lc", updatedAt=now, deletedAt=None))
        if session.execute(select(RearPort).where(RearPort.deviceId == d0, RearPort.name == "rp1")).scalar_one_or_none() is None:
            session.add(RearPort(id=uuid.uuid4(), deviceId=d0, name="rp1", type="lc", updatedAt=now, deletedAt=None))

    # Provider networks
    prov = session.execute(select(Provider).where(Provider.organizationId == oid, Provider.name == "dfleet-transit-1")).scalar_one_or_none()
    if prov and session.execute(
        select(ProviderNetwork).where(ProviderNetwork.organizationId == oid, ProviderNetwork.name == "dfleet-asn-set"),
    ).scalar_one_or_none() is None:
        session.add(
            ProviderNetwork(
                id=uuid.uuid4(),
                organizationId=oid,
                providerId=prov.id,
                name="dfleet-asn-set",
                description="BGP peers",
                updatedAt=now,
                deletedAt=None,
            ),
        )

    # Controllers + VDC + device bay
    if d0:
        if session.execute(select(Controller).where(Controller.organizationId == oid, Controller.name == "dfleet-bmc-1")).scalar_one_or_none() is None:
            session.add(
                Controller(
                    id=uuid.uuid4(),
                    organizationId=oid,
                    deviceId=d0,
                    name="dfleet-bmc-1",
                    role="oob",
                    updatedAt=now,
                    deletedAt=None,
                ),
            )
        if session.execute(select(VirtualDeviceContext).where(VirtualDeviceContext.deviceId == d0, VirtualDeviceContext.name == "vdc0")).scalar_one_or_none() is None:
            session.add(
                VirtualDeviceContext(
                    id=uuid.uuid4(),
                    organizationId=oid,
                    deviceId=d0,
                    name="vdc0",
                    updatedAt=now,
                    deletedAt=None,
                ),
            )
        if session.execute(select(DeviceBay).where(DeviceBay.parentDeviceId == d0, DeviceBay.name == "slot-0")).scalar_one_or_none() is None:
            session.add(DeviceBay(id=uuid.uuid4(), parentDeviceId=d0, name="slot-0", updatedAt=now, deletedAt=None))

    # IRG (needs two interfaces)
    ifaces_ir = session.execute(
        select(Interface.id)
        .join(Device, Interface.deviceId == Device.id)
        .where(Device.organizationId == oid)
        .limit(2),
    ).scalars().all()
    if len(ifaces_ir) >= 2:
        irg = session.execute(
            select(InterfaceRedundancyGroup).where(InterfaceRedundancyGroup.organizationId == oid, InterfaceRedundancyGroup.name == "dfleet-lag"),
        ).scalar_one_or_none()
        if irg is None:
            irg = InterfaceRedundancyGroup(
                id=uuid.uuid4(),
                organizationId=oid,
                name="dfleet-lag",
                protocol="lacp",
                updatedAt=now,
                deletedAt=None,
            )
            session.add(irg)
            session.flush()
            for iid in ifaces_ir[:2]:
                session.add(InterfaceRedundancyGroupMember(id=uuid.uuid4(), groupId=irg.id, interfaceId=iid, role="active"))

    # Change requests
    for i in range(25):
        title = f"dfleet-change-{i:03d}"
        if session.execute(select(ChangeRequest).where(ChangeRequest.organizationId == oid, ChangeRequest.title == title)).scalar_one_or_none() is None:
            session.add(
                ChangeRequest(
                    id=uuid.uuid4(),
                    organizationId=oid,
                    title=title,
                    description="Scheduled maintenance window",
                    payload={"ticket": i},
                    status=Changerequeststatus.DRAFT,
                    updatedAt=now,
                ),
            )

    session.flush()
