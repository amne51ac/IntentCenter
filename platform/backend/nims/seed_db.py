"""Idempotent demo data for local development and CI."""

from __future__ import annotations

import os
import uuid

import bcrypt
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from nims.crypto_util import generate_raw_token, hash_token
from nims.db import SessionLocal
from nims.models_generated import (
    ApiToken,
    Apitokenrole,
    ChangeRequest,
    Changerequeststatus,
    Circuit,
    CircuitDiversityGroup,
    CircuitSegment,
    Circuitstatus,
    CircuitTermination,
    CircuitType,
    Device,
    DeviceRole,
    Devicestatus,
    DeviceType,
    Interface,
    IpAddress,
    JobDefinition,
    JobRun,
    Jobrunstatus,
    Location,
    LocationType,
    Manufacturer,
    ObjectTemplate,
    Organization,
    PluginRegistration,
    Prefix,
    Project,
    Provider,
    Rack,
    Rir,
    ServiceInstance,
    Tag,
    TagAssignment,
    User,
    Userauthprovider,
    Vlan,
    VlanGroup,
    Vrf,
    Webhookevent,
    WebhookSubscription,
)
from nims.seed_demo_comprehensive import run_comprehensive_demo_inventory
from nims.template_defaults import BASE_TEMPLATE_DEFINITIONS
from nims.timeutil import utc_now

_BCRYPT_ROUNDS = 12


def _hash_password(plain: str) -> str:
    return bcrypt.hashpw(
        plain.encode("utf-8"),
        bcrypt.gensalt(rounds=_BCRYPT_ROUNDS),
    ).decode("utf-8")


def _ensure_demo_extended_graph(session: Session, org: Organization, now) -> None:
    """Add linked demo rows (interfaces, IPs, VLANs, circuits, tags, …) so object views and graphs resolve."""
    session.flush()

    dev = session.execute(
        select(Device).where(
            Device.organizationId == org.id,
            Device.name == "core-01",
            Device.deletedAt.is_(None),
        ),
    ).scalar_one_or_none()
    vrf = session.execute(
        select(Vrf).where(Vrf.organizationId == org.id, Vrf.name == "default", Vrf.deletedAt.is_(None)),
    ).scalar_one_or_none()
    pfx = session.execute(
        select(Prefix).where(
            Prefix.organizationId == org.id,
            Prefix.cidr == "10.0.0.0/16",
            Prefix.deletedAt.is_(None),
        ),
    ).scalar_one_or_none()
    jd = session.execute(
        select(JobDefinition).where(JobDefinition.organizationId == org.id, JobDefinition.key == "noop"),
    ).scalar_one_or_none()

    if dev is None or vrf is None or pfx is None:
        return

    rir = session.execute(select(Rir).where(Rir.slug == "arin")).scalar_one_or_none()
    if rir is None:
        rir = Rir(id=uuid.uuid4(), name="ARIN", slug="arin", description="American Registry for Internet Numbers")
        session.add(rir)
        session.flush()
    if pfx.rirId is None:
        pfx.rirId = rir.id
        pfx.updatedAt = now

    iface = session.execute(
        select(Interface).where(
            Interface.deviceId == dev.id,
            Interface.name == "eth0",
            Interface.deletedAt.is_(None),
        ),
    ).scalar_one_or_none()
    if iface is None:
        iface = Interface(
            id=uuid.uuid4(),
            deviceId=dev.id,
            name="eth0",
            type="ethernet",
            enabled=True,
            macAddress="00:11:22:33:44:55",
            updatedAt=now,
            deletedAt=None,
        )
        session.add(iface)
        session.flush()

    ip = session.execute(
        select(IpAddress).where(
            IpAddress.organizationId == org.id,
            IpAddress.address == "10.0.0.1",
            IpAddress.deletedAt.is_(None),
        ),
    ).scalar_one_or_none()
    if ip is None:
        session.add(
            IpAddress(
                id=uuid.uuid4(),
                organizationId=org.id,
                prefixId=pfx.id,
                address="10.0.0.1",
                description="Loopback / router ID (demo)",
                interfaceId=iface.id,
                updatedAt=now,
                deletedAt=None,
            ),
        )

    vg = session.execute(select(VlanGroup).where(VlanGroup.name == "Demo VLANs")).scalar_one_or_none()
    if vg is None:
        vg = VlanGroup(id=uuid.uuid4(), name="Demo VLANs")
        session.add(vg)
        session.flush()

    vlan = session.execute(
        select(Vlan).where(Vlan.organizationId == org.id, Vlan.vid == 100, Vlan.deletedAt.is_(None)),
    ).scalar_one_or_none()
    if vlan is None:
        session.add(
            Vlan(
                id=uuid.uuid4(),
                organizationId=org.id,
                vid=100,
                name="CORP",
                vlanGroupId=vg.id,
                updatedAt=now,
                deletedAt=None,
            ),
        )

    ct = session.execute(select(CircuitType).where(CircuitType.slug == "metro-ethernet")).scalar_one_or_none()
    if ct is None:
        ct = CircuitType(
            id=uuid.uuid4(),
            name="Metro Ethernet",
            slug="metro-ethernet",
            description="Demo seed circuit type",
        )
        session.add(ct)
        session.flush()

    prov = session.execute(
        select(Provider).where(Provider.organizationId == org.id, Provider.name == "Demo Carrier", Provider.deletedAt.is_(None)),
    ).scalar_one_or_none()
    if prov is None:
        prov = Provider(
            id=uuid.uuid4(),
            organizationId=org.id,
            name="Demo Carrier",
            asn=65001,
            updatedAt=now,
            deletedAt=None,
        )
        session.add(prov)
        session.flush()

    cdg = session.execute(
        select(CircuitDiversityGroup).where(
            CircuitDiversityGroup.organizationId == org.id,
            CircuitDiversityGroup.slug == "demo-hq-primary",
            CircuitDiversityGroup.deletedAt.is_(None),
        ),
    ).scalar_one_or_none()
    if cdg is None:
        cdg = CircuitDiversityGroup(
            id=uuid.uuid4(),
            organizationId=org.id,
            name="HQ primary path diversity",
            slug="demo-hq-primary",
            description="Demo: paired WAN paths modeled as one diversity group",
            updatedAt=now,
            deletedAt=None,
        )
        session.add(cdg)
        session.flush()

    circ = session.execute(
        select(Circuit).where(
            Circuit.organizationId == org.id,
            Circuit.cid == "DEMO-TRANSIT-01",
            Circuit.deletedAt.is_(None),
        ),
    ).scalar_one_or_none()
    if circ is None:
        session.add(
            Circuit(
                id=uuid.uuid4(),
                organizationId=org.id,
                providerId=prov.id,
                cid="DEMO-TRANSIT-01",
                status=Circuitstatus.ACTIVE,
                bandwidthMbps=1000,
                circuitTypeId=ct.id,
                circuitDiversityGroupId=cdg.id,
                aSideNotes="HQ demarc",
                zSideNotes="Carrier POP",
                updatedAt=now,
                deletedAt=None,
            ),
        )

    loc_hq = session.execute(
        select(Location).where(Location.organizationId == org.id, Location.slug == "hq", Location.deletedAt.is_(None)),
    ).scalar_one_or_none()
    lt_site_row = session.execute(select(LocationType).where(LocationType.name == "Site")).scalar_one_or_none()
    loc_pop = session.execute(
        select(Location).where(Location.organizationId == org.id, Location.slug == "pop-east", Location.deletedAt.is_(None)),
    ).scalar_one_or_none()
    if loc_pop is None and loc_hq is not None and lt_site_row is not None:
        loc_pop = Location(
            id=uuid.uuid4(),
            organizationId=org.id,
            locationTypeId=lt_site_row.id,
            name="East carrier POP",
            slug="pop-east",
            updatedAt=now,
            deletedAt=None,
        )
        session.add(loc_pop)
        session.flush()

    prov_wholesale = session.execute(
        select(Provider).where(Provider.organizationId == org.id, Provider.name == "Wholesale Transport", Provider.deletedAt.is_(None)),
    ).scalar_one_or_none()
    if prov_wholesale is None:
        prov_wholesale = Provider(
            id=uuid.uuid4(),
            organizationId=org.id,
            name="Wholesale Transport",
            asn=65002,
            updatedAt=now,
            deletedAt=None,
        )
        session.add(prov_wholesale)
        session.flush()

    mh = session.execute(
        select(Circuit).where(
            Circuit.organizationId == org.id,
            Circuit.cid == "DEMO-MULTI-HOP-01",
            Circuit.deletedAt.is_(None),
        ),
    ).scalar_one_or_none()
    if mh is None and loc_hq is not None and loc_pop is not None:
        mh_id = uuid.uuid4()
        session.add(
            Circuit(
                id=mh_id,
                organizationId=org.id,
                providerId=prov.id,
                cid="DEMO-MULTI-HOP-01",
                status=Circuitstatus.ACTIVE,
                bandwidthMbps=1000,
                circuitTypeId=ct.id,
                circuitDiversityGroupId=cdg.id,
                aSideNotes="Multi-segment sample: access + long-haul + metro",
                zSideNotes="Remote POP demarc",
                updatedAt=now,
                deletedAt=None,
            ),
        )
        session.flush()
        session.add(
            CircuitSegment(
                id=uuid.uuid4(),
                circuitId=mh_id,
                segmentIndex=0,
                label="Access tail",
                providerId=prov.id,
                bandwidthMbps=1000,
                status=Circuitstatus.ACTIVE,
                aSideNotes="Customer demarc",
                zSideNotes="Carrier meet-me",
                updatedAt=now,
            ),
        )
        session.add(
            CircuitSegment(
                id=uuid.uuid4(),
                circuitId=mh_id,
                segmentIndex=1,
                label="DWDM long haul",
                providerId=prov_wholesale.id,
                bandwidthMbps=1000,
                status=Circuitstatus.ACTIVE,
                updatedAt=now,
            ),
        )
        session.add(
            CircuitSegment(
                id=uuid.uuid4(),
                circuitId=mh_id,
                segmentIndex=2,
                label="Metro / last mile",
                providerId=prov.id,
                bandwidthMbps=1000,
                status=Circuitstatus.ACTIVE,
                updatedAt=now,
            ),
        )
        session.add(
            CircuitTermination(
                id=uuid.uuid4(),
                organizationId=org.id,
                circuitId=mh_id,
                side="A",
                locationId=loc_hq.id,
                portName="xe-0/0/0",
                description="HQ router hand-off",
                updatedAt=now,
                deletedAt=None,
            ),
        )
        session.add(
            CircuitTermination(
                id=uuid.uuid4(),
                organizationId=org.id,
                circuitId=mh_id,
                side="Z",
                locationId=loc_pop.id,
                portName="0/2/0",
                description="POP demarc",
                updatedAt=now,
                deletedAt=None,
            ),
        )

    for demo_cid in ("DEMO-TRANSIT-01", "DEMO-MULTI-HOP-01"):
        c_fix = session.execute(
            select(Circuit).where(
                Circuit.organizationId == org.id,
                Circuit.cid == demo_cid,
                Circuit.deletedAt.is_(None),
            ),
        ).scalar_one_or_none()
        if c_fix is not None and c_fix.circuitDiversityGroupId is None:
            c_fix.circuitDiversityGroupId = cdg.id
            c_fix.updatedAt = now

    svc = session.execute(
        select(ServiceInstance).where(
            ServiceInstance.organizationId == org.id,
            ServiceInstance.name == "Core routing",
            ServiceInstance.deletedAt.is_(None),
        ),
    ).scalar_one_or_none()
    if svc is None:
        session.add(
            ServiceInstance(
                id=uuid.uuid4(),
                organizationId=org.id,
                name="Core routing",
                serviceType="internal",
                status="active",
                customerRef="demo",
                updatedAt=now,
                deletedAt=None,
            ),
        )

    tag = session.execute(
        select(Tag).where(Tag.organizationId == org.id, Tag.slug == "production", Tag.deletedAt.is_(None)),
    ).scalar_one_or_none()
    if tag is None:
        tag = Tag(
            id=uuid.uuid4(),
            organizationId=org.id,
            name="production",
            slug="production",
            color="#2d6a4f",
            description="Demo tag",
            updatedAt=now,
            deletedAt=None,
        )
        session.add(tag)
        session.flush()

    ta = session.execute(
        select(TagAssignment).where(
            TagAssignment.tagId == tag.id,
            TagAssignment.resourceType == "Device",
            TagAssignment.resourceId == dev.id,
        ),
    ).scalar_one_or_none()
    if ta is None:
        session.add(TagAssignment(id=uuid.uuid4(), tagId=tag.id, resourceType="Device", resourceId=dev.id))

    if jd is not None:
        has_run = session.execute(select(JobRun).where(JobRun.organizationId == org.id).limit(1)).scalar_one_or_none()
        if has_run is None:
            session.add(
                JobRun(
                    id=uuid.uuid4(),
                    organizationId=org.id,
                    jobDefinitionId=jd.id,
                    status=Jobrunstatus.SUCCEEDED,
                    input={"seed": True},
                    output={"ok": True, "message": "Demo job run"},
                    logs="Seed: simulated successful run.",
                    correlationId="seed-noop-1",
                    updatedAt=now,
                ),
            )

    cr = session.execute(
        select(ChangeRequest).where(
            ChangeRequest.organizationId == org.id,
            ChangeRequest.title == "Demo change request",
        ),
    ).scalar_one_or_none()
    if cr is None:
        session.add(
            ChangeRequest(
                id=uuid.uuid4(),
                organizationId=org.id,
                title="Demo change request",
                description="Illustrates the change workflow (draft).",
                payload={"intent": "noop", "seed": True},
                status=Changerequeststatus.DRAFT,
                updatedAt=now,
            ),
        )


def run_seed(session: Session) -> tuple[Organization, str, str, str, str]:
    now = utc_now()
    admin_password = os.environ.get("SEED_ADMIN_PASSWORD", "ChangeMe!Admin")
    admin_email = (os.environ.get("SEED_ADMIN_EMAIL", "admin@demo.local")).lower()
    password_hash = _hash_password(admin_password)

    org = session.execute(select(Organization).where(Organization.slug == "demo")).scalar_one_or_none()
    if org is None:
        org = Organization(
            id=uuid.uuid4(),
            name="Demo Organization",
            slug="demo",
            updatedAt=now,
            deletedAt=None,
        )
        session.add(org)
        session.flush()

    user = session.execute(
        select(User).where(User.organizationId == org.id, User.email == admin_email),
    ).scalar_one_or_none()
    if user is None:
        session.add(
            User(
                id=uuid.uuid4(),
                organizationId=org.id,
                email=admin_email,
                displayName="Demo Administrator",
                passwordHash=password_hash,
                role=Apitokenrole.ADMIN,
                authProvider=Userauthprovider.LOCAL,
                updatedAt=now,
            ),
        )
    else:
        user.passwordHash = password_hash
        user.role = Apitokenrole.ADMIN
        user.updatedAt = now

    proj = session.execute(
        select(Project).where(Project.organizationId == org.id, Project.slug == "default"),
    ).scalar_one_or_none()
    if proj is None:
        session.add(
            Project(
                id=uuid.uuid4(),
                organizationId=org.id,
                name="Default",
                slug="default",
                updatedAt=now,
                deletedAt=None,
            ),
        )

    lt_site = session.execute(select(LocationType).where(LocationType.name == "Site")).scalar_one_or_none()
    if lt_site is None:
        lt_site = LocationType(
            id=uuid.uuid4(),
            name="Site",
            description="Campus or facility site",
        )
        session.add(lt_site)
        session.flush()

    lt_region = session.execute(select(LocationType).where(LocationType.name == "Region")).scalar_one_or_none()
    if lt_region is None:
        session.add(
            LocationType(
                id=uuid.uuid4(),
                name="Region",
                description="Geographic region",
            ),
        )

    loc = session.execute(
        select(Location).where(Location.organizationId == org.id, Location.slug == "hq"),
    ).scalar_one_or_none()
    if loc is None:
        loc = Location(
            id=uuid.uuid4(),
            organizationId=org.id,
            locationTypeId=lt_site.id,
            name="Headquarters",
            slug="hq",
            updatedAt=now,
            deletedAt=None,
        )
        session.add(loc)
        session.flush()

    rack = session.execute(
        select(Rack).where(
            Rack.organizationId == org.id,
            Rack.locationId == loc.id,
            Rack.name == "RACK-01",
        ),
    ).scalar_one_or_none()
    if rack is None:
        rack = Rack(
            id=uuid.uuid4(),
            organizationId=org.id,
            locationId=loc.id,
            name="RACK-01",
            uHeight=42,
            updatedAt=now,
            deletedAt=None,
        )
        session.add(rack)
        session.flush()

    mfg = session.execute(select(Manufacturer).where(Manufacturer.name == "Generic")).scalar_one_or_none()
    if mfg is None:
        mfg = Manufacturer(id=uuid.uuid4(), name="Generic")
        session.add(mfg)
        session.flush()

    dt = session.execute(
        select(DeviceType).where(DeviceType.manufacturerId == mfg.id, DeviceType.model == "Router-1U"),
    ).scalar_one_or_none()
    if dt is None:
        dt = DeviceType(id=uuid.uuid4(), manufacturerId=mfg.id, model="Router-1U", uHeight=1)
        session.add(dt)
        session.flush()

    role = session.execute(select(DeviceRole).where(DeviceRole.name == "router")).scalar_one_or_none()
    if role is None:
        role = DeviceRole(id=uuid.uuid4(), name="router")
        session.add(role)
        session.flush()

    dev = session.execute(
        select(Device).where(Device.organizationId == org.id, Device.name == "core-01"),
    ).scalar_one_or_none()
    if dev is None:
        session.add(
            Device(
                id=uuid.uuid4(),
                organizationId=org.id,
                rackId=rack.id,
                deviceTypeId=dt.id,
                deviceRoleId=role.id,
                name="core-01",
                status=Devicestatus.ACTIVE,
                positionU=20,
                face="front",
                updatedAt=now,
                deletedAt=None,
            ),
        )

    vrf = session.execute(
        select(Vrf).where(Vrf.organizationId == org.id, Vrf.name == "default"),
    ).scalar_one_or_none()
    if vrf is None:
        vrf = Vrf(
            id=uuid.uuid4(),
            organizationId=org.id,
            name="default",
            updatedAt=now,
            deletedAt=None,
        )
        session.add(vrf)
        session.flush()

    pfx = session.execute(
        select(Prefix).where(
            Prefix.organizationId == org.id,
            Prefix.vrfId == vrf.id,
            Prefix.cidr == "10.0.0.0/16",
        ),
    ).scalar_one_or_none()
    if pfx is None:
        session.add(
            Prefix(
                id=uuid.uuid4(),
                organizationId=org.id,
                vrfId=vrf.id,
                cidr="10.0.0.0/16",
                description="Seed prefix",
                updatedAt=now,
                deletedAt=None,
            ),
        )

    jd = session.execute(
        select(JobDefinition).where(JobDefinition.organizationId == org.id, JobDefinition.key == "noop"),
    ).scalar_one_or_none()
    if jd is None:
        session.add(
            JobDefinition(
                id=uuid.uuid4(),
                organizationId=org.id,
                key="noop",
                name="No-op job",
                description="Placeholder until worker pool is wired",
                requiresApproval=False,
                updatedAt=now,
            ),
        )

    plug = session.execute(
        select(PluginRegistration).where(PluginRegistration.packageName == "nims.builtin.reporting"),
    ).scalar_one_or_none()
    if plug is None:
        session.add(
            PluginRegistration(
                id=uuid.uuid4(),
                packageName="nims.builtin.reporting",
                version="0.1.0",
                enabled=True,
                manifest={"panels": ["inventory-summary"]},
            ),
        )
    else:
        plug.version = "0.1.0"
        plug.enabled = True
        plug.manifest = {"panels": ["inventory-summary"]}

    admin_raw = generate_raw_token()
    write_raw = generate_raw_token()

    session.execute(
        delete(ApiToken).where(
            ApiToken.organizationId == org.id,
            ApiToken.name.in_(["seed-admin", "seed-write"]),
        ),
    )
    session.add_all(
        [
            ApiToken(
                id=uuid.uuid4(),
                organizationId=org.id,
                name="seed-admin",
                tokenHash=hash_token(admin_raw),
                role=Apitokenrole.ADMIN,
            ),
            ApiToken(
                id=uuid.uuid4(),
                organizationId=org.id,
                name="seed-write",
                tokenHash=hash_token(write_raw),
                role=Apitokenrole.WRITE,
            ),
        ],
    )

    session.execute(
        delete(WebhookSubscription).where(
            WebhookSubscription.organizationId == org.id,
            WebhookSubscription.name == "seed-example",
        ),
    )
    session.add(
        WebhookSubscription(
            id=uuid.uuid4(),
            organizationId=org.id,
            name="seed-example",
            url="https://example.com/webhooks/nims",
            resourceTypes=[],
            events=[Webhookevent.CREATE, Webhookevent.UPDATE],
            updatedAt=now,
        ),
    )

    for rt, definition in BASE_TEMPLATE_DEFINITIONS.items():
        existing = session.execute(
            select(ObjectTemplate).where(
                ObjectTemplate.organizationId == org.id,
                ObjectTemplate.resourceType == rt,
                ObjectTemplate.slug == "base",
            ),
        ).scalar_one_or_none()
        if existing is None:
            session.add(
                ObjectTemplate(
                    id=uuid.uuid4(),
                    organizationId=org.id,
                    resourceType=rt,
                    name=f"{rt} (base)",
                    slug="base",
                    description="System default form template",
                    isSystem=True,
                    isDefault=True,
                    definition=definition,
                    createdAt=now,
                    updatedAt=now,
                ),
            )
        else:
            existing.definition = definition
            existing.isSystem = True
            existing.isDefault = True
            existing.updatedAt = now

    _ensure_demo_extended_graph(session, org, now)
    run_comprehensive_demo_inventory(session, org, now)

    return org, admin_email, admin_password, admin_raw, write_raw


def main() -> None:
    session = SessionLocal()
    try:
        org, admin_email, admin_password, admin_raw, write_raw = run_seed(session)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

    print("\n=== Seed complete ===")
    print(f"Organization: {org.slug} ({org.id})")
    print("\nWeb UI sign-in (POST /v1/auth/login or /app/login):")
    print(f"  Email:    {admin_email}")
    print(f"  Password: {admin_password}  (override with SEED_ADMIN_PASSWORD)")
    print("\nAPI tokens (use Authorization: Bearer <token>):")
    print(f"  ADMIN:  {admin_raw}")
    print(f"  WRITE:  {write_raw}")
    print('\nExample: curl -H "Authorization: Bearer ${ADMIN}" http://localhost:8080/v1/me\n')


if __name__ == "__main__":
    main()
