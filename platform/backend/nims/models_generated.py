from typing import Optional
import datetime
import enum
import uuid

from sqlalchemy import ARRAY, Boolean, DateTime, Enum, ForeignKeyConstraint, Integer, PrimaryKeyConstraint, String, Text, Uuid, text
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class Apitokenrole(str, enum.Enum):
    READ = 'READ'
    WRITE = 'WRITE'
    ADMIN = 'ADMIN'


class Changerequeststatus(str, enum.Enum):
    DRAFT = 'DRAFT'
    PENDING_APPROVAL = 'PENDING_APPROVAL'
    APPROVED = 'APPROVED'
    REJECTED = 'REJECTED'
    APPLIED = 'APPLIED'


class Circuitstatus(str, enum.Enum):
    PLANNED = 'PLANNED'
    ACTIVE = 'ACTIVE'
    DECOMMISSIONED = 'DECOMMISSIONED'


class Devicestatus(str, enum.Enum):
    PLANNED = 'PLANNED'
    STAGED = 'STAGED'
    ACTIVE = 'ACTIVE'
    DECOMMISSIONED = 'DECOMMISSIONED'


class Jobrunstatus(str, enum.Enum):
    PENDING = 'PENDING'
    APPROVAL_REQUIRED = 'APPROVAL_REQUIRED'
    APPROVED = 'APPROVED'
    RUNNING = 'RUNNING'
    SUCCEEDED = 'SUCCEEDED'
    FAILED = 'FAILED'
    CANCELLED = 'CANCELLED'


class Observationkind(str, enum.Enum):
    DEVICE = 'DEVICE'
    INTERFACE = 'INTERFACE'
    SERVICE = 'SERVICE'


class Userauthprovider(str, enum.Enum):
    LOCAL = 'LOCAL'
    LDAP = 'LDAP'
    AZURE_AD = 'AZURE_AD'
    OIDC = 'OIDC'


class Webhookevent(str, enum.Enum):
    CREATE = 'CREATE'
    UPDATE = 'UPDATE'
    DELETE = 'DELETE'


class CircuitType(Base):
    __tablename__ = 'CircuitType'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='CircuitType_pkey'),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    Circuit: Mapped[list['Circuit']] = relationship('Circuit', back_populates='CircuitType_')


class DeviceRole(Base):
    __tablename__ = 'DeviceRole'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='DeviceRole_pkey'),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)

    Device: Mapped[list['Device']] = relationship('Device', back_populates='DeviceRole_')


class LocationType(Base):
    __tablename__ = 'LocationType'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='LocationType_pkey'),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    Location: Mapped[list['Location']] = relationship('Location', back_populates='LocationType_')


class Manufacturer(Base):
    __tablename__ = 'Manufacturer'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='Manufacturer_pkey'),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)

    DeviceFamily: Mapped[list['DeviceFamily']] = relationship('DeviceFamily', back_populates='Manufacturer_')
    DeviceType: Mapped[list['DeviceType']] = relationship('DeviceType', back_populates='Manufacturer_')
    ModuleType: Mapped[list['ModuleType']] = relationship('ModuleType', back_populates='Manufacturer_')


class Organization(Base):
    __tablename__ = 'Organization'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='Organization_pkey'),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    ApiToken: Mapped[list['ApiToken']] = relationship('ApiToken', back_populates='Organization_')
    AuditEvent: Mapped[list['AuditEvent']] = relationship('AuditEvent', back_populates='Organization_')
    ChangeRequest: Mapped[list['ChangeRequest']] = relationship('ChangeRequest', back_populates='Organization_')
    CloudNetwork: Mapped[list['CloudNetwork']] = relationship('CloudNetwork', back_populates='Organization_')
    Cluster: Mapped[list['Cluster']] = relationship('Cluster', back_populates='Organization_')
    Contact: Mapped[list['Contact']] = relationship('Contact', back_populates='Organization_')
    DeviceGroup: Mapped[list['DeviceGroup']] = relationship('DeviceGroup', back_populates='Organization_')
    DeviceRedundancyGroup: Mapped[list['DeviceRedundancyGroup']] = relationship('DeviceRedundancyGroup', back_populates='Organization_')
    DynamicGroup: Mapped[list['DynamicGroup']] = relationship('DynamicGroup', back_populates='Organization_')
    InterfaceRedundancyGroup: Mapped[list['InterfaceRedundancyGroup']] = relationship('InterfaceRedundancyGroup', back_populates='Organization_')
    IpamNamespace: Mapped[list['IpamNamespace']] = relationship('IpamNamespace', back_populates='Organization_')
    JobDefinition: Mapped[list['JobDefinition']] = relationship('JobDefinition', back_populates='Organization_')
    Location: Mapped[list['Location']] = relationship('Location', back_populates='Organization_')
    MplsDomain: Mapped[list['MplsDomain']] = relationship('MplsDomain', back_populates='Organization_')
    ObjectTemplate: Mapped[list['ObjectTemplate']] = relationship('ObjectTemplate', back_populates='Organization_')
    Project: Mapped[list['Project']] = relationship('Project', back_populates='Organization_')
    Provider: Mapped[list['Provider']] = relationship('Provider', back_populates='Organization_')
    RackGroup: Mapped[list['RackGroup']] = relationship('RackGroup', back_populates='Organization_')
    ServiceInstance: Mapped[list['ServiceInstance']] = relationship('ServiceInstance', back_populates='Organization_')
    SoftwareImageFile: Mapped[list['SoftwareImageFile']] = relationship('SoftwareImageFile', back_populates='Organization_')
    StatusDefinition: Mapped[list['StatusDefinition']] = relationship('StatusDefinition', back_populates='Organization_')
    Tag: Mapped[list['Tag']] = relationship('Tag', back_populates='Organization_')
    Team: Mapped[list['Team']] = relationship('Team', back_populates='Organization_')
    TenantGroup: Mapped[list['TenantGroup']] = relationship('TenantGroup', back_populates='Organization_')
    User: Mapped[list['User']] = relationship('User', back_populates='Organization_')
    VirtualChassis: Mapped[list['VirtualChassis']] = relationship('VirtualChassis', back_populates='Organization_')
    Vlan: Mapped[list['Vlan']] = relationship('Vlan', back_populates='Organization_')
    Vpn: Mapped[list['Vpn']] = relationship('Vpn', back_populates='Organization_')
    Vrf: Mapped[list['Vrf']] = relationship('Vrf', back_populates='Organization_')
    WebhookSubscription: Mapped[list['WebhookSubscription']] = relationship('WebhookSubscription', back_populates='Organization_')
    WirelessNetwork: Mapped[list['WirelessNetwork']] = relationship('WirelessNetwork', back_populates='Organization_')
    Circuit: Mapped[list['Circuit']] = relationship('Circuit', back_populates='Organization_')
    CircuitDiversityGroup: Mapped[list['CircuitDiversityGroup']] = relationship('CircuitDiversityGroup', back_populates='Organization_')
    CloudService: Mapped[list['CloudService']] = relationship('CloudService', back_populates='Organization_')
    JobRun: Mapped[list['JobRun']] = relationship('JobRun', back_populates='Organization_')
    PowerPanel: Mapped[list['PowerPanel']] = relationship('PowerPanel', back_populates='Organization_')
    Prefix: Mapped[list['Prefix']] = relationship('Prefix', back_populates='Organization_')
    ProviderNetwork: Mapped[list['ProviderNetwork']] = relationship('ProviderNetwork', back_populates='Organization_')
    Rack: Mapped[list['Rack']] = relationship('Rack', back_populates='Organization_')
    ResourceExtension: Mapped[list['ResourceExtension']] = relationship('ResourceExtension', back_populates='Organization_')
    RouteTarget: Mapped[list['RouteTarget']] = relationship('RouteTarget', back_populates='Organization_')
    VirtualMachine: Mapped[list['VirtualMachine']] = relationship('VirtualMachine', back_populates='Organization_')
    CircuitTermination: Mapped[list['CircuitTermination']] = relationship('CircuitTermination', back_populates='Organization_')
    Device: Mapped[list['Device']] = relationship('Device', back_populates='Organization_')
    PowerFeed: Mapped[list['PowerFeed']] = relationship('PowerFeed', back_populates='Organization_')
    RackElevation: Mapped[list['RackElevation']] = relationship('RackElevation', back_populates='Organization_')
    RackReservation: Mapped[list['RackReservation']] = relationship('RackReservation', back_populates='Organization_')
    Controller: Mapped[list['Controller']] = relationship('Controller', back_populates='Organization_')
    InventoryItem: Mapped[list['InventoryItem']] = relationship('InventoryItem', back_populates='Organization_')
    Module: Mapped[list['Module']] = relationship('Module', back_populates='Organization_')
    ObservedResourceState: Mapped[list['ObservedResourceState']] = relationship('ObservedResourceState', back_populates='Organization_')
    VirtualDeviceContext: Mapped[list['VirtualDeviceContext']] = relationship('VirtualDeviceContext', back_populates='Organization_')
    ConsoleConnection: Mapped[list['ConsoleConnection']] = relationship('ConsoleConnection', back_populates='Organization_')
    IpAddress: Mapped[list['IpAddress']] = relationship('IpAddress', back_populates='Organization_')
    PowerConnection: Mapped[list['PowerConnection']] = relationship('PowerConnection', back_populates='Organization_')


class PluginRegistration(Base):
    __tablename__ = 'PluginRegistration'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='PluginRegistration_pkey'),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    packageName: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'))
    registeredAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    manifest: Mapped[Optional[dict]] = mapped_column(JSONB)


class Rir(Base):
    __tablename__ = 'Rir'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='Rir_pkey'),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    Prefix: Mapped[list['Prefix']] = relationship('Prefix', back_populates='Rir_')


class SoftwarePlatform(Base):
    __tablename__ = 'SoftwarePlatform'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='SoftwarePlatform_pkey'),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    SoftwareImageFile: Mapped[list['SoftwareImageFile']] = relationship('SoftwareImageFile', back_populates='SoftwarePlatform_')
    SoftwareVersion: Mapped[list['SoftwareVersion']] = relationship('SoftwareVersion', back_populates='SoftwarePlatform_')


class VlanGroup(Base):
    __tablename__ = 'VlanGroup'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='VlanGroup_pkey'),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)

    Vlan: Mapped[list['Vlan']] = relationship('Vlan', back_populates='VlanGroup_')


class PrismaMigrations(Base):
    __tablename__ = '_prisma_migrations'
    __table_args__ = (
        PrimaryKeyConstraint('id', name='_prisma_migrations_pkey'),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    migration_name: Mapped[str] = mapped_column(String(255), nullable=False)
    started_at: Mapped[datetime.datetime] = mapped_column(DateTime(True), nullable=False, server_default=text('now()'))
    applied_steps_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))
    finished_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))
    logs: Mapped[Optional[str]] = mapped_column(Text)
    rolled_back_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime(True))


class ApiToken(Base):
    __tablename__ = 'ApiToken'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='ApiToken_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='ApiToken_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    tokenHash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[Apitokenrole] = mapped_column(Enum(Apitokenrole, values_callable=lambda cls: [member.value for member in cls], name='ApiTokenRole'), nullable=False, server_default=text('\'WRITE\'::"ApiTokenRole"'))
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    expiresAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))
    lastUsedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='ApiToken')


class AuditEvent(Base):
    __tablename__ = 'AuditEvent'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='AuditEvent_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='AuditEvent_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    actor: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)
    resourceType: Mapped[str] = mapped_column(Text, nullable=False)
    resourceId: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    correlationId: Mapped[Optional[str]] = mapped_column(Text)
    before: Mapped[Optional[dict]] = mapped_column(JSONB)
    after: Mapped[Optional[dict]] = mapped_column(JSONB)

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='AuditEvent')


class ChangeRequest(Base):
    __tablename__ = 'ChangeRequest'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='ChangeRequest_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='ChangeRequest_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[Changerequeststatus] = mapped_column(Enum(Changerequeststatus, values_callable=lambda cls: [member.value for member in cls], name='ChangeRequestStatus'), nullable=False, server_default=text('\'DRAFT\'::"ChangeRequestStatus"'))
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    correlationId: Mapped[Optional[str]] = mapped_column(Text)

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='ChangeRequest')


class CloudNetwork(Base):
    __tablename__ = 'CloudNetwork'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='CloudNetwork_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='CloudNetwork_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    cloudProvider: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    metadata_: Mapped[Optional[dict]] = mapped_column('metadata', JSONB)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='CloudNetwork')
    CloudService: Mapped[list['CloudService']] = relationship('CloudService', back_populates='CloudNetwork_')


class Cluster(Base):
    __tablename__ = 'Cluster'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='Cluster_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='Cluster_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    clusterType: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    metadata_: Mapped[Optional[dict]] = mapped_column('metadata', JSONB)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='Cluster')
    VirtualMachine: Mapped[list['VirtualMachine']] = relationship('VirtualMachine', back_populates='Cluster_')


class Contact(Base):
    __tablename__ = 'Contact'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='Contact_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='Contact_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(Text)
    phone: Mapped[Optional[str]] = mapped_column(Text)
    title: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='Contact')


class DeviceFamily(Base):
    __tablename__ = 'DeviceFamily'
    __table_args__ = (
        ForeignKeyConstraint(['manufacturerId'], ['Manufacturer.id'], ondelete='SET NULL', onupdate='CASCADE', name='DeviceFamily_manufacturerId_fkey'),
        PrimaryKeyConstraint('id', name='DeviceFamily_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    manufacturerId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    description: Mapped[Optional[str]] = mapped_column(Text)

    Manufacturer_: Mapped[Optional['Manufacturer']] = relationship('Manufacturer', back_populates='DeviceFamily')


class DeviceGroup(Base):
    __tablename__ = 'DeviceGroup'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='DeviceGroup_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='DeviceGroup_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='DeviceGroup')
    DeviceGroupMember: Mapped[list['DeviceGroupMember']] = relationship('DeviceGroupMember', back_populates='DeviceGroup_')


class DeviceRedundancyGroup(Base):
    __tablename__ = 'DeviceRedundancyGroup'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='DeviceRedundancyGroup_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='DeviceRedundancyGroup_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    protocol: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='DeviceRedundancyGroup')
    DeviceRedundancyGroupMember: Mapped[list['DeviceRedundancyGroupMember']] = relationship('DeviceRedundancyGroupMember', back_populates='DeviceRedundancyGroup_')


class DeviceType(Base):
    __tablename__ = 'DeviceType'
    __table_args__ = (
        ForeignKeyConstraint(['manufacturerId'], ['Manufacturer.id'], ondelete='RESTRICT', onupdate='CASCADE', name='DeviceType_manufacturerId_fkey'),
        PrimaryKeyConstraint('id', name='DeviceType_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    manufacturerId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    model: Mapped[str] = mapped_column(Text, nullable=False)
    uHeight: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('1'))

    Manufacturer_: Mapped['Manufacturer'] = relationship('Manufacturer', back_populates='DeviceType')
    Device: Mapped[list['Device']] = relationship('Device', back_populates='DeviceType_')


class DynamicGroup(Base):
    __tablename__ = 'DynamicGroup'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='DynamicGroup_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='DynamicGroup_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    definition: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='DynamicGroup')


class InterfaceRedundancyGroup(Base):
    __tablename__ = 'InterfaceRedundancyGroup'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='InterfaceRedundancyGroup_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='InterfaceRedundancyGroup_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    protocol: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='InterfaceRedundancyGroup')
    InterfaceRedundancyGroupMember: Mapped[list['InterfaceRedundancyGroupMember']] = relationship('InterfaceRedundancyGroupMember', back_populates='InterfaceRedundancyGroup_')


class IpamNamespace(Base):
    __tablename__ = 'IpamNamespace'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='IpamNamespace_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='IpamNamespace_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='IpamNamespace')


class JobDefinition(Base):
    __tablename__ = 'JobDefinition'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='JobDefinition_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='JobDefinition_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    key: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    requiresApproval: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'))
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='JobDefinition')
    JobRun: Mapped[list['JobRun']] = relationship('JobRun', back_populates='JobDefinition_')


class Location(Base):
    __tablename__ = 'Location'
    __table_args__ = (
        ForeignKeyConstraint(['locationTypeId'], ['LocationType.id'], ondelete='RESTRICT', onupdate='CASCADE', name='Location_locationTypeId_fkey'),
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='Location_organizationId_fkey'),
        ForeignKeyConstraint(['parentId'], ['Location.id'], ondelete='SET NULL', onupdate='CASCADE', name='Location_parentId_fkey'),
        PrimaryKeyConstraint('id', name='Location_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    locationTypeId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    parentId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    description: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    LocationType_: Mapped['LocationType'] = relationship('LocationType', back_populates='Location')
    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='Location')
    Location: Mapped[Optional['Location']] = relationship('Location', remote_side=[id], back_populates='Location_reverse')
    Location_reverse: Mapped[list['Location']] = relationship('Location', remote_side=[parentId], back_populates='Location')
    PowerPanel: Mapped[list['PowerPanel']] = relationship('PowerPanel', back_populates='Location_')
    Rack: Mapped[list['Rack']] = relationship('Rack', back_populates='Location_')
    CircuitTermination: Mapped[list['CircuitTermination']] = relationship('CircuitTermination', back_populates='Location_')


class ModuleType(Base):
    __tablename__ = 'ModuleType'
    __table_args__ = (
        ForeignKeyConstraint(['manufacturerId'], ['Manufacturer.id'], ondelete='SET NULL', onupdate='CASCADE', name='ModuleType_manufacturerId_fkey'),
        PrimaryKeyConstraint('id', name='ModuleType_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    model: Mapped[str] = mapped_column(Text, nullable=False)
    manufacturerId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    partNumber: Mapped[Optional[str]] = mapped_column(Text)

    Manufacturer_: Mapped[Optional['Manufacturer']] = relationship('Manufacturer', back_populates='ModuleType')
    Module: Mapped[list['Module']] = relationship('Module', back_populates='ModuleType_')


class MplsDomain(Base):
    __tablename__ = 'MplsDomain'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='MplsDomain_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='MplsDomain_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    rd: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    metadata_: Mapped[Optional[dict]] = mapped_column('metadata', JSONB)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='MplsDomain')


class ObjectTemplate(Base):
    __tablename__ = 'ObjectTemplate'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='ObjectTemplate_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='ObjectTemplate_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    resourceType: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    isSystem: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    isDefault: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    definition: Mapped[dict] = mapped_column(JSONB, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='ObjectTemplate')
    ResourceExtension: Mapped[list['ResourceExtension']] = relationship('ResourceExtension', back_populates='ObjectTemplate_')


class Project(Base):
    __tablename__ = 'Project'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='Project_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='Project_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='Project')


class Provider(Base):
    __tablename__ = 'Provider'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='Provider_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='Provider_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    asn: Mapped[Optional[int]] = mapped_column(Integer)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='Provider')
    Circuit: Mapped[list['Circuit']] = relationship('Circuit', back_populates='Provider_')
    ProviderNetwork: Mapped[list['ProviderNetwork']] = relationship('ProviderNetwork', back_populates='Provider_')
    CircuitSegment: Mapped[list['CircuitSegment']] = relationship('CircuitSegment', back_populates='Provider_')


class RackGroup(Base):
    __tablename__ = 'RackGroup'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='RackGroup_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='RackGroup_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='RackGroup')
    Rack: Mapped[list['Rack']] = relationship('Rack', back_populates='RackGroup_')


class CircuitDiversityGroup(Base):
    __tablename__ = 'CircuitDiversityGroup'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='CircuitDiversityGroup_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='CircuitDiversityGroup_pkey'),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='CircuitDiversityGroup')
    Circuit: Mapped[list['Circuit']] = relationship('Circuit', back_populates='CircuitDiversityGroup_')


class ServiceInstance(Base):
    __tablename__ = 'ServiceInstance'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='ServiceInstance_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='ServiceInstance_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    serviceType: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'active'::text"))
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    customerRef: Mapped[Optional[str]] = mapped_column(Text)
    metadata_: Mapped[Optional[dict]] = mapped_column('metadata', JSONB)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='ServiceInstance')


class SoftwareImageFile(Base):
    __tablename__ = 'SoftwareImageFile'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='SoftwareImageFile_organizationId_fkey'),
        ForeignKeyConstraint(['platformId'], ['SoftwarePlatform.id'], ondelete='SET NULL', onupdate='CASCADE', name='SoftwareImageFile_platformId_fkey'),
        PrimaryKeyConstraint('id', name='SoftwareImageFile_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    platformId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    sha256: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='SoftwareImageFile')
    SoftwarePlatform_: Mapped[Optional['SoftwarePlatform']] = relationship('SoftwarePlatform', back_populates='SoftwareImageFile')


class SoftwareVersion(Base):
    __tablename__ = 'SoftwareVersion'
    __table_args__ = (
        ForeignKeyConstraint(['platformId'], ['SoftwarePlatform.id'], ondelete='CASCADE', onupdate='CASCADE', name='SoftwareVersion_platformId_fkey'),
        PrimaryKeyConstraint('id', name='SoftwareVersion_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    platformId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    version: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    releaseNotes: Mapped[Optional[str]] = mapped_column(Text)

    SoftwarePlatform_: Mapped['SoftwarePlatform'] = relationship('SoftwarePlatform', back_populates='SoftwareVersion')


class StatusDefinition(Base):
    __tablename__ = 'StatusDefinition'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='StatusDefinition_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='StatusDefinition_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    resourceType: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    color: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='StatusDefinition')


class Tag(Base):
    __tablename__ = 'Tag'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='Tag_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='Tag_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    color: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='Tag')
    TagAssignment: Mapped[list['TagAssignment']] = relationship('TagAssignment', back_populates='Tag_')


class Team(Base):
    __tablename__ = 'Team'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='Team_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='Team_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='Team')


class TenantGroup(Base):
    __tablename__ = 'TenantGroup'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='TenantGroup_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='TenantGroup_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    slug: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='TenantGroup')


class User(Base):
    __tablename__ = 'User'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='User_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='User_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    email: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[Apitokenrole] = mapped_column(Enum(Apitokenrole, values_callable=lambda cls: [member.value for member in cls], name='ApiTokenRole'), nullable=False, server_default=text('\'READ\'::"ApiTokenRole"'))
    authProvider: Mapped[Userauthprovider] = mapped_column(Enum(Userauthprovider, values_callable=lambda cls: [member.value for member in cls], name='UserAuthProvider'), nullable=False, server_default=text('\'LOCAL\'::"UserAuthProvider"'))
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    preferences: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    displayName: Mapped[Optional[str]] = mapped_column(Text)
    passwordHash: Mapped[Optional[str]] = mapped_column(Text)
    externalSubject: Mapped[Optional[str]] = mapped_column(Text)

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='User')


class VirtualChassis(Base):
    __tablename__ = 'VirtualChassis'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='VirtualChassis_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='VirtualChassis_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    domainId: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='VirtualChassis')
    VirtualChassisMember: Mapped[list['VirtualChassisMember']] = relationship('VirtualChassisMember', back_populates='VirtualChassis_')


class Vlan(Base):
    __tablename__ = 'Vlan'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='Vlan_organizationId_fkey'),
        ForeignKeyConstraint(['vlanGroupId'], ['VlanGroup.id'], ondelete='SET NULL', onupdate='CASCADE', name='Vlan_vlanGroupId_fkey'),
        PrimaryKeyConstraint('id', name='Vlan_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    vid: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    vlanGroupId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='Vlan')
    VlanGroup_: Mapped[Optional['VlanGroup']] = relationship('VlanGroup', back_populates='Vlan')


class Vpn(Base):
    __tablename__ = 'Vpn'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='Vpn_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='Vpn_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    vpnType: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    metadata_: Mapped[Optional[dict]] = mapped_column('metadata', JSONB)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='Vpn')


class Vrf(Base):
    __tablename__ = 'Vrf'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='Vrf_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='Vrf_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    rd: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='Vrf')
    Prefix: Mapped[list['Prefix']] = relationship('Prefix', back_populates='Vrf_')
    RouteTarget: Mapped[list['RouteTarget']] = relationship('RouteTarget', back_populates='Vrf_')


class WebhookSubscription(Base):
    __tablename__ = 'WebhookSubscription'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='WebhookSubscription_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='WebhookSubscription_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'))
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    secret: Mapped[Optional[str]] = mapped_column(Text)
    resourceTypes: Mapped[Optional[list[str]]] = mapped_column(ARRAY(Text()))
    events: Mapped[Optional[list[Webhookevent]]] = mapped_column(ARRAY(Enum(Webhookevent, values_callable=lambda cls: [member.value for member in cls], name='WebhookEvent')))

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='WebhookSubscription')


class WirelessNetwork(Base):
    __tablename__ = 'WirelessNetwork'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='WirelessNetwork_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='WirelessNetwork_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    ssid: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    metadata_: Mapped[Optional[dict]] = mapped_column('metadata', JSONB)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='WirelessNetwork')


class Circuit(Base):
    __tablename__ = 'Circuit'
    __table_args__ = (
        ForeignKeyConstraint(['circuitDiversityGroupId'], ['CircuitDiversityGroup.id'], ondelete='SET NULL', onupdate='CASCADE', name='Circuit_circuitDiversityGroupId_fkey'),
        ForeignKeyConstraint(['circuitTypeId'], ['CircuitType.id'], ondelete='SET NULL', onupdate='CASCADE', name='Circuit_circuitTypeId_fkey'),
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='Circuit_organizationId_fkey'),
        ForeignKeyConstraint(['providerId'], ['Provider.id'], ondelete='RESTRICT', onupdate='CASCADE', name='Circuit_providerId_fkey'),
        PrimaryKeyConstraint('id', name='Circuit_pkey'),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    providerId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    cid: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[Circuitstatus] = mapped_column(Enum(Circuitstatus, values_callable=lambda cls: [member.value for member in cls], name='CircuitStatus'), nullable=False, server_default=text('\'PLANNED\'::"CircuitStatus"'))
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    bandwidthMbps: Mapped[Optional[int]] = mapped_column(Integer)
    aSideNotes: Mapped[Optional[str]] = mapped_column(Text)
    zSideNotes: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))
    circuitTypeId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    circuitDiversityGroupId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)

    CircuitDiversityGroup_: Mapped[Optional['CircuitDiversityGroup']] = relationship('CircuitDiversityGroup', back_populates='Circuit')
    CircuitType_: Mapped[Optional['CircuitType']] = relationship('CircuitType', back_populates='Circuit')
    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='Circuit')
    Provider_: Mapped['Provider'] = relationship('Provider', back_populates='Circuit')
    CircuitSegment: Mapped[list['CircuitSegment']] = relationship('CircuitSegment', back_populates='Circuit_')
    CircuitTermination: Mapped[list['CircuitTermination']] = relationship('CircuitTermination', back_populates='Circuit_')


class CloudService(Base):
    __tablename__ = 'CloudService'
    __table_args__ = (
        ForeignKeyConstraint(['cloudNetworkId'], ['CloudNetwork.id'], ondelete='SET NULL', onupdate='CASCADE', name='CloudService_cloudNetworkId_fkey'),
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='CloudService_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='CloudService_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    cloudNetworkId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    serviceType: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    metadata_: Mapped[Optional[dict]] = mapped_column('metadata', JSONB)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    CloudNetwork_: Mapped[Optional['CloudNetwork']] = relationship('CloudNetwork', back_populates='CloudService')
    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='CloudService')


class JobRun(Base):
    __tablename__ = 'JobRun'
    __table_args__ = (
        ForeignKeyConstraint(['jobDefinitionId'], ['JobDefinition.id'], ondelete='RESTRICT', onupdate='CASCADE', name='JobRun_jobDefinitionId_fkey'),
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='JobRun_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='JobRun_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    jobDefinitionId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    status: Mapped[Jobrunstatus] = mapped_column(Enum(Jobrunstatus, values_callable=lambda cls: [member.value for member in cls], name='JobRunStatus'), nullable=False, server_default=text('\'PENDING\'::"JobRunStatus"'))
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    idempotencyKey: Mapped[Optional[str]] = mapped_column(Text)
    input: Mapped[Optional[dict]] = mapped_column(JSONB)
    output: Mapped[Optional[dict]] = mapped_column(JSONB)
    logs: Mapped[Optional[str]] = mapped_column(Text)
    correlationId: Mapped[Optional[str]] = mapped_column(Text)

    JobDefinition_: Mapped['JobDefinition'] = relationship('JobDefinition', back_populates='JobRun')
    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='JobRun')


class PowerPanel(Base):
    __tablename__ = 'PowerPanel'
    __table_args__ = (
        ForeignKeyConstraint(['locationId'], ['Location.id'], ondelete='RESTRICT', onupdate='CASCADE', name='PowerPanel_locationId_fkey'),
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='PowerPanel_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='PowerPanel_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    locationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Location_: Mapped['Location'] = relationship('Location', back_populates='PowerPanel')
    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='PowerPanel')
    PowerFeed: Mapped[list['PowerFeed']] = relationship('PowerFeed', back_populates='PowerPanel_')


class Prefix(Base):
    __tablename__ = 'Prefix'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='Prefix_organizationId_fkey'),
        ForeignKeyConstraint(['parentId'], ['Prefix.id'], ondelete='SET NULL', onupdate='CASCADE', name='Prefix_parentId_fkey'),
        ForeignKeyConstraint(['rirId'], ['Rir.id'], ondelete='SET NULL', onupdate='CASCADE', name='Prefix_rirId_fkey'),
        ForeignKeyConstraint(['vrfId'], ['Vrf.id'], ondelete='RESTRICT', onupdate='CASCADE', name='Prefix_vrfId_fkey'),
        PrimaryKeyConstraint('id', name='Prefix_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    vrfId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    cidr: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    parentId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))
    rirId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='Prefix')
    Prefix: Mapped[Optional['Prefix']] = relationship('Prefix', remote_side=[id], back_populates='Prefix_reverse')
    Prefix_reverse: Mapped[list['Prefix']] = relationship('Prefix', remote_side=[parentId], back_populates='Prefix')
    Rir_: Mapped[Optional['Rir']] = relationship('Rir', back_populates='Prefix')
    Vrf_: Mapped['Vrf'] = relationship('Vrf', back_populates='Prefix')
    IpAddress: Mapped[list['IpAddress']] = relationship('IpAddress', back_populates='Prefix_')


class ProviderNetwork(Base):
    __tablename__ = 'ProviderNetwork'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='ProviderNetwork_organizationId_fkey'),
        ForeignKeyConstraint(['providerId'], ['Provider.id'], ondelete='RESTRICT', onupdate='CASCADE', name='ProviderNetwork_providerId_fkey'),
        PrimaryKeyConstraint('id', name='ProviderNetwork_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    providerId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='ProviderNetwork')
    Provider_: Mapped['Provider'] = relationship('Provider', back_populates='ProviderNetwork')


class Rack(Base):
    __tablename__ = 'Rack'
    __table_args__ = (
        ForeignKeyConstraint(['locationId'], ['Location.id'], ondelete='RESTRICT', onupdate='CASCADE', name='Rack_locationId_fkey'),
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='Rack_organizationId_fkey'),
        ForeignKeyConstraint(['rackGroupId'], ['RackGroup.id'], ondelete='SET NULL', onupdate='CASCADE', name='Rack_rackGroupId_fkey'),
        PrimaryKeyConstraint('id', name='Rack_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    locationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    uHeight: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('42'))
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))
    rackGroupId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)

    Location_: Mapped['Location'] = relationship('Location', back_populates='Rack')
    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='Rack')
    RackGroup_: Mapped[Optional['RackGroup']] = relationship('RackGroup', back_populates='Rack')
    Device: Mapped[list['Device']] = relationship('Device', back_populates='Rack_')
    RackElevation: Mapped[list['RackElevation']] = relationship('RackElevation', back_populates='Rack_')
    RackReservation: Mapped[list['RackReservation']] = relationship('RackReservation', back_populates='Rack_')


class ResourceExtension(Base):
    __tablename__ = 'ResourceExtension'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='ResourceExtension_organizationId_fkey'),
        ForeignKeyConstraint(['templateId'], ['ObjectTemplate.id'], ondelete='SET NULL', onupdate='CASCADE', name='ResourceExtension_templateId_fkey'),
        PrimaryKeyConstraint('id', name='ResourceExtension_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    resourceType: Mapped[str] = mapped_column(Text, nullable=False)
    resourceId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, server_default=text("'{}'::jsonb"))
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    templateId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='ResourceExtension')
    ObjectTemplate_: Mapped[Optional['ObjectTemplate']] = relationship('ObjectTemplate', back_populates='ResourceExtension')


class RouteTarget(Base):
    __tablename__ = 'RouteTarget'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='RouteTarget_organizationId_fkey'),
        ForeignKeyConstraint(['vrfId'], ['Vrf.id'], ondelete='SET NULL', onupdate='CASCADE', name='RouteTarget_vrfId_fkey'),
        PrimaryKeyConstraint('id', name='RouteTarget_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    vrfId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    description: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='RouteTarget')
    Vrf_: Mapped[Optional['Vrf']] = relationship('Vrf', back_populates='RouteTarget')


class TagAssignment(Base):
    __tablename__ = 'TagAssignment'
    __table_args__ = (
        ForeignKeyConstraint(['tagId'], ['Tag.id'], ondelete='CASCADE', onupdate='CASCADE', name='TagAssignment_tagId_fkey'),
        PrimaryKeyConstraint('id', name='TagAssignment_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    tagId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    resourceType: Mapped[str] = mapped_column(Text, nullable=False)
    resourceId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)

    Tag_: Mapped['Tag'] = relationship('Tag', back_populates='TagAssignment')


class VirtualMachine(Base):
    __tablename__ = 'VirtualMachine'
    __table_args__ = (
        ForeignKeyConstraint(['clusterId'], ['Cluster.id'], ondelete='SET NULL', onupdate='CASCADE', name='VirtualMachine_clusterId_fkey'),
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='VirtualMachine_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='VirtualMachine_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    clusterId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    description: Mapped[Optional[str]] = mapped_column(Text)
    metadata_: Mapped[Optional[dict]] = mapped_column('metadata', JSONB)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Cluster_: Mapped[Optional['Cluster']] = relationship('Cluster', back_populates='VirtualMachine')
    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='VirtualMachine')


class CircuitSegment(Base):
    __tablename__ = 'CircuitSegment'
    __table_args__ = (
        ForeignKeyConstraint(['circuitId'], ['Circuit.id'], ondelete='CASCADE', onupdate='CASCADE', name='CircuitSegment_circuitId_fkey'),
        ForeignKeyConstraint(['providerId'], ['Provider.id'], ondelete='SET NULL', onupdate='CASCADE', name='CircuitSegment_providerId_fkey'),
        PrimaryKeyConstraint('id', name='CircuitSegment_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    circuitId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    segmentIndex: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[Circuitstatus] = mapped_column(Enum(Circuitstatus, values_callable=lambda cls: [member.value for member in cls], name='CircuitStatus'), nullable=False, server_default=text('\'PLANNED\'::"CircuitStatus"'))
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    label: Mapped[Optional[str]] = mapped_column(Text)
    providerId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    bandwidthMbps: Mapped[Optional[int]] = mapped_column(Integer)
    aSideNotes: Mapped[Optional[str]] = mapped_column(Text)
    zSideNotes: Mapped[Optional[str]] = mapped_column(Text)

    Circuit_: Mapped['Circuit'] = relationship('Circuit', back_populates='CircuitSegment')
    Provider_: Mapped[Optional['Provider']] = relationship('Provider', back_populates='CircuitSegment')


class CircuitTermination(Base):
    __tablename__ = 'CircuitTermination'
    __table_args__ = (
        ForeignKeyConstraint(['circuitId'], ['Circuit.id'], ondelete='CASCADE', onupdate='CASCADE', name='CircuitTermination_circuitId_fkey'),
        ForeignKeyConstraint(['locationId'], ['Location.id'], ondelete='SET NULL', onupdate='CASCADE', name='CircuitTermination_locationId_fkey'),
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='CircuitTermination_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='CircuitTermination_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    circuitId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    side: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    locationId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    portName: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Circuit_: Mapped['Circuit'] = relationship('Circuit', back_populates='CircuitTermination')
    Location_: Mapped[Optional['Location']] = relationship('Location', back_populates='CircuitTermination')
    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='CircuitTermination')


class Device(Base):
    __tablename__ = 'Device'
    __table_args__ = (
        ForeignKeyConstraint(['deviceRoleId'], ['DeviceRole.id'], ondelete='RESTRICT', onupdate='CASCADE', name='Device_deviceRoleId_fkey'),
        ForeignKeyConstraint(['deviceTypeId'], ['DeviceType.id'], ondelete='RESTRICT', onupdate='CASCADE', name='Device_deviceTypeId_fkey'),
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='Device_organizationId_fkey'),
        ForeignKeyConstraint(['rackId'], ['Rack.id'], ondelete='SET NULL', onupdate='CASCADE', name='Device_rackId_fkey'),
        PrimaryKeyConstraint('id', name='Device_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    deviceTypeId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    deviceRoleId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[Devicestatus] = mapped_column(Enum(Devicestatus, values_callable=lambda cls: [member.value for member in cls], name='DeviceStatus'), nullable=False, server_default=text('\'PLANNED\'::"DeviceStatus"'))
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    rackId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    serialNumber: Mapped[Optional[str]] = mapped_column(Text)
    positionU: Mapped[Optional[int]] = mapped_column(Integer)
    face: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    DeviceRole_: Mapped['DeviceRole'] = relationship('DeviceRole', back_populates='Device')
    DeviceType_: Mapped['DeviceType'] = relationship('DeviceType', back_populates='Device')
    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='Device')
    Rack_: Mapped[Optional['Rack']] = relationship('Rack', back_populates='Device')
    ConsolePort: Mapped[list['ConsolePort']] = relationship('ConsolePort', back_populates='Device_')
    ConsoleServerPort: Mapped[list['ConsoleServerPort']] = relationship('ConsoleServerPort', back_populates='Device_')
    Controller: Mapped[list['Controller']] = relationship('Controller', back_populates='Device_')
    DeviceBay_installedDeviceId: Mapped[list['DeviceBay']] = relationship('DeviceBay', foreign_keys='[DeviceBay.installedDeviceId]', back_populates='Device_')
    DeviceBay_parentDeviceId: Mapped[list['DeviceBay']] = relationship('DeviceBay', foreign_keys='[DeviceBay.parentDeviceId]', back_populates='Device1')
    DeviceGroupMember: Mapped[list['DeviceGroupMember']] = relationship('DeviceGroupMember', back_populates='Device_')
    DeviceRedundancyGroupMember: Mapped[list['DeviceRedundancyGroupMember']] = relationship('DeviceRedundancyGroupMember', back_populates='Device_')
    FrontPort: Mapped[list['FrontPort']] = relationship('FrontPort', back_populates='Device_')
    Interface: Mapped[list['Interface']] = relationship('Interface', back_populates='Device_')
    InventoryItem: Mapped[list['InventoryItem']] = relationship('InventoryItem', back_populates='Device_')
    Module: Mapped[list['Module']] = relationship('Module', back_populates='Device_')
    ModuleBay: Mapped[list['ModuleBay']] = relationship('ModuleBay', back_populates='Device_')
    ObservedResourceState: Mapped[list['ObservedResourceState']] = relationship('ObservedResourceState', back_populates='Device_')
    PowerOutlet: Mapped[list['PowerOutlet']] = relationship('PowerOutlet', back_populates='Device_')
    PowerPort: Mapped[list['PowerPort']] = relationship('PowerPort', back_populates='Device_')
    RearPort: Mapped[list['RearPort']] = relationship('RearPort', back_populates='Device_')
    VirtualChassisMember: Mapped[list['VirtualChassisMember']] = relationship('VirtualChassisMember', back_populates='Device_')
    VirtualDeviceContext: Mapped[list['VirtualDeviceContext']] = relationship('VirtualDeviceContext', back_populates='Device_')


class PowerFeed(Base):
    __tablename__ = 'PowerFeed'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='PowerFeed_organizationId_fkey'),
        ForeignKeyConstraint(['powerPanelId'], ['PowerPanel.id'], ondelete='SET NULL', onupdate='CASCADE', name='PowerFeed_powerPanelId_fkey'),
        PrimaryKeyConstraint('id', name='PowerFeed_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    powerPanelId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    voltage: Mapped[Optional[int]] = mapped_column(Integer)
    amperage: Mapped[Optional[int]] = mapped_column(Integer)
    description: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='PowerFeed')
    PowerPanel_: Mapped[Optional['PowerPanel']] = relationship('PowerPanel', back_populates='PowerFeed')


class RackElevation(Base):
    __tablename__ = 'RackElevation'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='RackElevation_organizationId_fkey'),
        ForeignKeyConstraint(['rackId'], ['Rack.id'], ondelete='RESTRICT', onupdate='CASCADE', name='RackElevation_rackId_fkey'),
        PrimaryKeyConstraint('id', name='RackElevation_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    rackId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    imageUrl: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='RackElevation')
    Rack_: Mapped['Rack'] = relationship('Rack', back_populates='RackElevation')


class RackReservation(Base):
    __tablename__ = 'RackReservation'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='RackReservation_organizationId_fkey'),
        ForeignKeyConstraint(['rackId'], ['Rack.id'], ondelete='RESTRICT', onupdate='CASCADE', name='RackReservation_rackId_fkey'),
        PrimaryKeyConstraint('id', name='RackReservation_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    rackId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    label: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    startsAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))
    endsAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))
    description: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='RackReservation')
    Rack_: Mapped['Rack'] = relationship('Rack', back_populates='RackReservation')


class ConsolePort(Base):
    __tablename__ = 'ConsolePort'
    __table_args__ = (
        ForeignKeyConstraint(['deviceId'], ['Device.id'], ondelete='RESTRICT', onupdate='CASCADE', name='ConsolePort_deviceId_fkey'),
        PrimaryKeyConstraint('id', name='ConsolePort_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    deviceId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    label: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Device_: Mapped['Device'] = relationship('Device', back_populates='ConsolePort')
    ConsoleConnection: Mapped[list['ConsoleConnection']] = relationship('ConsoleConnection', back_populates='ConsolePort_')


class ConsoleServerPort(Base):
    __tablename__ = 'ConsoleServerPort'
    __table_args__ = (
        ForeignKeyConstraint(['deviceId'], ['Device.id'], ondelete='RESTRICT', onupdate='CASCADE', name='ConsoleServerPort_deviceId_fkey'),
        PrimaryKeyConstraint('id', name='ConsoleServerPort_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    deviceId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    label: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Device_: Mapped['Device'] = relationship('Device', back_populates='ConsoleServerPort')
    ConsoleConnection: Mapped[list['ConsoleConnection']] = relationship('ConsoleConnection', back_populates='ConsoleServerPort_')


class Controller(Base):
    __tablename__ = 'Controller'
    __table_args__ = (
        ForeignKeyConstraint(['deviceId'], ['Device.id'], ondelete='SET NULL', onupdate='CASCADE', name='Controller_deviceId_fkey'),
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='Controller_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='Controller_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    deviceId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    role: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Device_: Mapped[Optional['Device']] = relationship('Device', back_populates='Controller')
    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='Controller')


class DeviceBay(Base):
    __tablename__ = 'DeviceBay'
    __table_args__ = (
        ForeignKeyConstraint(['installedDeviceId'], ['Device.id'], ondelete='SET NULL', onupdate='CASCADE', name='DeviceBay_installedDeviceId_fkey'),
        ForeignKeyConstraint(['parentDeviceId'], ['Device.id'], ondelete='RESTRICT', onupdate='CASCADE', name='DeviceBay_parentDeviceId_fkey'),
        PrimaryKeyConstraint('id', name='DeviceBay_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    parentDeviceId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    installedDeviceId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Device_: Mapped[Optional['Device']] = relationship('Device', foreign_keys=[installedDeviceId], back_populates='DeviceBay_installedDeviceId')
    Device1: Mapped['Device'] = relationship('Device', foreign_keys=[parentDeviceId], back_populates='DeviceBay_parentDeviceId')


class DeviceGroupMember(Base):
    __tablename__ = 'DeviceGroupMember'
    __table_args__ = (
        ForeignKeyConstraint(['deviceId'], ['Device.id'], ondelete='RESTRICT', onupdate='CASCADE', name='DeviceGroupMember_deviceId_fkey'),
        ForeignKeyConstraint(['groupId'], ['DeviceGroup.id'], ondelete='CASCADE', onupdate='CASCADE', name='DeviceGroupMember_groupId_fkey'),
        PrimaryKeyConstraint('id', name='DeviceGroupMember_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    groupId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    deviceId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)

    Device_: Mapped['Device'] = relationship('Device', back_populates='DeviceGroupMember')
    DeviceGroup_: Mapped['DeviceGroup'] = relationship('DeviceGroup', back_populates='DeviceGroupMember')


class DeviceRedundancyGroupMember(Base):
    __tablename__ = 'DeviceRedundancyGroupMember'
    __table_args__ = (
        ForeignKeyConstraint(['deviceId'], ['Device.id'], ondelete='RESTRICT', onupdate='CASCADE', name='DeviceRedundancyGroupMember_deviceId_fkey'),
        ForeignKeyConstraint(['groupId'], ['DeviceRedundancyGroup.id'], ondelete='CASCADE', onupdate='CASCADE', name='DeviceRedundancyGroupMember_groupId_fkey'),
        PrimaryKeyConstraint('id', name='DeviceRedundancyGroupMember_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    groupId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    deviceId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    role: Mapped[Optional[str]] = mapped_column(Text)

    Device_: Mapped['Device'] = relationship('Device', back_populates='DeviceRedundancyGroupMember')
    DeviceRedundancyGroup_: Mapped['DeviceRedundancyGroup'] = relationship('DeviceRedundancyGroup', back_populates='DeviceRedundancyGroupMember')


class FrontPort(Base):
    __tablename__ = 'FrontPort'
    __table_args__ = (
        ForeignKeyConstraint(['deviceId'], ['Device.id'], ondelete='RESTRICT', onupdate='CASCADE', name='FrontPort_deviceId_fkey'),
        ForeignKeyConstraint(['moduleId'], ['Module.id'], ondelete='SET NULL', onupdate='CASCADE', name='FrontPort_moduleId_fkey'),
        PrimaryKeyConstraint('id', name='FrontPort_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    deviceId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    moduleId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    label: Mapped[Optional[str]] = mapped_column(Text)
    type: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Device_: Mapped['Device'] = relationship('Device', back_populates='FrontPort')
    Module_: Mapped[Optional['Module']] = relationship('Module', back_populates='FrontPort')


class Interface(Base):
    __tablename__ = 'Interface'
    __table_args__ = (
        ForeignKeyConstraint(['deviceId'], ['Device.id'], ondelete='RESTRICT', onupdate='CASCADE', name='Interface_deviceId_fkey'),
        PrimaryKeyConstraint('id', name='Interface_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    deviceId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('true'))
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    macAddress: Mapped[Optional[str]] = mapped_column(Text)
    mtu: Mapped[Optional[int]] = mapped_column(Integer)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Device_: Mapped['Device'] = relationship('Device', back_populates='Interface')
    Cable_interfaceAId: Mapped[list['Cable']] = relationship('Cable', foreign_keys='[Cable.interfaceAId]', back_populates='Interface_')
    Cable_interfaceBId: Mapped[list['Cable']] = relationship('Cable', foreign_keys='[Cable.interfaceBId]', back_populates='Interface1')
    InterfaceRedundancyGroupMember: Mapped[list['InterfaceRedundancyGroupMember']] = relationship('InterfaceRedundancyGroupMember', back_populates='Interface_')
    IpAddress: Mapped[list['IpAddress']] = relationship('IpAddress', back_populates='Interface_')


class InventoryItem(Base):
    __tablename__ = 'InventoryItem'
    __table_args__ = (
        ForeignKeyConstraint(['deviceId'], ['Device.id'], ondelete='SET NULL', onupdate='CASCADE', name='InventoryItem_deviceId_fkey'),
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='InventoryItem_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='InventoryItem_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    deviceId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    serial: Mapped[Optional[str]] = mapped_column(Text)
    assetTag: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Device_: Mapped[Optional['Device']] = relationship('Device', back_populates='InventoryItem')
    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='InventoryItem')


class Module(Base):
    __tablename__ = 'Module'
    __table_args__ = (
        ForeignKeyConstraint(['deviceId'], ['Device.id'], ondelete='RESTRICT', onupdate='CASCADE', name='Module_deviceId_fkey'),
        ForeignKeyConstraint(['moduleBayId'], ['ModuleBay.id'], ondelete='SET NULL', onupdate='CASCADE', name='Module_moduleBayId_fkey'),
        ForeignKeyConstraint(['moduleTypeId'], ['ModuleType.id'], ondelete='RESTRICT', onupdate='CASCADE', name='Module_moduleTypeId_fkey'),
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='Module_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='Module_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    deviceId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    moduleTypeId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    moduleBayId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    serial: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Device_: Mapped['Device'] = relationship('Device', back_populates='Module')
    ModuleType_: Mapped['ModuleType'] = relationship('ModuleType', back_populates='Module')
    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='Module')
    ModuleBay_seatedIn: Mapped[Optional['ModuleBay']] = relationship(
        'ModuleBay',
        foreign_keys=[moduleBayId],
        back_populates='seatedModule',
    )
    ModuleBay_slotsOnCard: Mapped[list['ModuleBay']] = relationship(
        'ModuleBay',
        foreign_keys='[ModuleBay.parentModuleId]',
        back_populates='parentModule_',
    )
    FrontPort: Mapped[list['FrontPort']] = relationship('FrontPort', back_populates='Module_')


class ModuleBay(Base):
    __tablename__ = 'ModuleBay'
    __table_args__ = (
        ForeignKeyConstraint(['deviceId'], ['Device.id'], ondelete='RESTRICT', onupdate='CASCADE', name='ModuleBay_deviceId_fkey'),
        ForeignKeyConstraint(['parentModuleId'], ['Module.id'], ondelete='CASCADE', onupdate='CASCADE', name='ModuleBay_parentModuleId_fkey'),
        PrimaryKeyConstraint('id', name='ModuleBay_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    deviceId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    parentModuleId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    position: Mapped[Optional[int]] = mapped_column(Integer)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Device_: Mapped[Optional['Device']] = relationship('Device', back_populates='ModuleBay')
    parentModule_: Mapped[Optional['Module']] = relationship(
        'Module',
        foreign_keys=[parentModuleId],
        back_populates='ModuleBay_slotsOnCard',
    )
    seatedModule: Mapped[Optional['Module']] = relationship(
        'Module',
        foreign_keys='[Module.moduleBayId]',
        back_populates='ModuleBay_seatedIn',
    )


class ObservedResourceState(Base):
    __tablename__ = 'ObservedResourceState'
    __table_args__ = (
        ForeignKeyConstraint(['deviceId'], ['Device.id'], ondelete='SET NULL', onupdate='CASCADE', name='ObservedResourceState_deviceId_fkey'),
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='ObservedResourceState_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='ObservedResourceState_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    kind: Mapped[Observationkind] = mapped_column(Enum(Observationkind, values_callable=lambda cls: [member.value for member in cls], name='ObservationKind'), nullable=False)
    driftDetected: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text('false'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    deviceId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    lastSeenAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))
    health: Mapped[Optional[str]] = mapped_column(Text)
    payload: Mapped[Optional[dict]] = mapped_column(JSONB)
    driftSummary: Mapped[Optional[str]] = mapped_column(Text)

    Device_: Mapped[Optional['Device']] = relationship('Device', back_populates='ObservedResourceState')
    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='ObservedResourceState')


class PowerOutlet(Base):
    __tablename__ = 'PowerOutlet'
    __table_args__ = (
        ForeignKeyConstraint(['deviceId'], ['Device.id'], ondelete='RESTRICT', onupdate='CASCADE', name='PowerOutlet_deviceId_fkey'),
        PrimaryKeyConstraint('id', name='PowerOutlet_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    deviceId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    label: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Device_: Mapped['Device'] = relationship('Device', back_populates='PowerOutlet')
    PowerConnection: Mapped[list['PowerConnection']] = relationship('PowerConnection', back_populates='PowerOutlet_')


class PowerPort(Base):
    __tablename__ = 'PowerPort'
    __table_args__ = (
        ForeignKeyConstraint(['deviceId'], ['Device.id'], ondelete='RESTRICT', onupdate='CASCADE', name='PowerPort_deviceId_fkey'),
        PrimaryKeyConstraint('id', name='PowerPort_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    deviceId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    label: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Device_: Mapped['Device'] = relationship('Device', back_populates='PowerPort')
    PowerConnection: Mapped[list['PowerConnection']] = relationship('PowerConnection', back_populates='PowerPort_')


class RearPort(Base):
    __tablename__ = 'RearPort'
    __table_args__ = (
        ForeignKeyConstraint(['deviceId'], ['Device.id'], ondelete='RESTRICT', onupdate='CASCADE', name='RearPort_deviceId_fkey'),
        PrimaryKeyConstraint('id', name='RearPort_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    deviceId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    label: Mapped[Optional[str]] = mapped_column(Text)
    type: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Device_: Mapped['Device'] = relationship('Device', back_populates='RearPort')


class VirtualChassisMember(Base):
    __tablename__ = 'VirtualChassisMember'
    __table_args__ = (
        ForeignKeyConstraint(['deviceId'], ['Device.id'], ondelete='RESTRICT', onupdate='CASCADE', name='VirtualChassisMember_deviceId_fkey'),
        ForeignKeyConstraint(['virtualChassisId'], ['VirtualChassis.id'], ondelete='CASCADE', onupdate='CASCADE', name='VirtualChassisMember_virtualChassisId_fkey'),
        PrimaryKeyConstraint('id', name='VirtualChassisMember_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    virtualChassisId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    deviceId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text('0'))

    Device_: Mapped['Device'] = relationship('Device', back_populates='VirtualChassisMember')
    VirtualChassis_: Mapped['VirtualChassis'] = relationship('VirtualChassis', back_populates='VirtualChassisMember')


class VirtualDeviceContext(Base):
    __tablename__ = 'VirtualDeviceContext'
    __table_args__ = (
        ForeignKeyConstraint(['deviceId'], ['Device.id'], ondelete='RESTRICT', onupdate='CASCADE', name='VirtualDeviceContext_deviceId_fkey'),
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='VirtualDeviceContext_organizationId_fkey'),
        PrimaryKeyConstraint('id', name='VirtualDeviceContext_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    deviceId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    identifier: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Device_: Mapped['Device'] = relationship('Device', back_populates='VirtualDeviceContext')
    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='VirtualDeviceContext')


class Cable(Base):
    __tablename__ = 'Cable'
    __table_args__ = (
        ForeignKeyConstraint(['interfaceAId'], ['Interface.id'], ondelete='RESTRICT', onupdate='CASCADE', name='Cable_interfaceAId_fkey'),
        ForeignKeyConstraint(['interfaceBId'], ['Interface.id'], ondelete='RESTRICT', onupdate='CASCADE', name='Cable_interfaceBId_fkey'),
        PrimaryKeyConstraint('id', name='Cable_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    interfaceAId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    interfaceBId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    label: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Interface_: Mapped['Interface'] = relationship('Interface', foreign_keys=[interfaceAId], back_populates='Cable_interfaceAId')
    Interface1: Mapped['Interface'] = relationship('Interface', foreign_keys=[interfaceBId], back_populates='Cable_interfaceBId')


class ConsoleConnection(Base):
    __tablename__ = 'ConsoleConnection'
    __table_args__ = (
        ForeignKeyConstraint(['clientPortId'], ['ConsolePort.id'], ondelete='RESTRICT', onupdate='CASCADE', name='ConsoleConnection_clientPortId_fkey'),
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='ConsoleConnection_organizationId_fkey'),
        ForeignKeyConstraint(['serverPortId'], ['ConsoleServerPort.id'], ondelete='RESTRICT', onupdate='CASCADE', name='ConsoleConnection_serverPortId_fkey'),
        PrimaryKeyConstraint('id', name='ConsoleConnection_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    serverPortId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    clientPortId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    ConsolePort_: Mapped['ConsolePort'] = relationship('ConsolePort', back_populates='ConsoleConnection')
    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='ConsoleConnection')
    ConsoleServerPort_: Mapped['ConsoleServerPort'] = relationship('ConsoleServerPort', back_populates='ConsoleConnection')


class InterfaceRedundancyGroupMember(Base):
    __tablename__ = 'InterfaceRedundancyGroupMember'
    __table_args__ = (
        ForeignKeyConstraint(['groupId'], ['InterfaceRedundancyGroup.id'], ondelete='CASCADE', onupdate='CASCADE', name='InterfaceRedundancyGroupMember_groupId_fkey'),
        ForeignKeyConstraint(['interfaceId'], ['Interface.id'], ondelete='RESTRICT', onupdate='CASCADE', name='InterfaceRedundancyGroupMember_interfaceId_fkey'),
        PrimaryKeyConstraint('id', name='InterfaceRedundancyGroupMember_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    groupId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    interfaceId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    role: Mapped[Optional[str]] = mapped_column(Text)

    InterfaceRedundancyGroup_: Mapped['InterfaceRedundancyGroup'] = relationship('InterfaceRedundancyGroup', back_populates='InterfaceRedundancyGroupMember')
    Interface_: Mapped['Interface'] = relationship('Interface', back_populates='InterfaceRedundancyGroupMember')


class IpAddress(Base):
    __tablename__ = 'IpAddress'
    __table_args__ = (
        ForeignKeyConstraint(['interfaceId'], ['Interface.id'], ondelete='SET NULL', onupdate='CASCADE', name='IpAddress_interfaceId_fkey'),
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='IpAddress_organizationId_fkey'),
        ForeignKeyConstraint(['prefixId'], ['Prefix.id'], ondelete='RESTRICT', onupdate='CASCADE', name='IpAddress_prefixId_fkey'),
        PrimaryKeyConstraint('id', name='IpAddress_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    prefixId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    interfaceId: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Interface_: Mapped[Optional['Interface']] = relationship('Interface', back_populates='IpAddress')
    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='IpAddress')
    Prefix_: Mapped['Prefix'] = relationship('Prefix', back_populates='IpAddress')


class PowerConnection(Base):
    __tablename__ = 'PowerConnection'
    __table_args__ = (
        ForeignKeyConstraint(['organizationId'], ['Organization.id'], ondelete='RESTRICT', onupdate='CASCADE', name='PowerConnection_organizationId_fkey'),
        ForeignKeyConstraint(['outletId'], ['PowerOutlet.id'], ondelete='RESTRICT', onupdate='CASCADE', name='PowerConnection_outletId_fkey'),
        ForeignKeyConstraint(['portId'], ['PowerPort.id'], ondelete='RESTRICT', onupdate='CASCADE', name='PowerConnection_portId_fkey'),
        PrimaryKeyConstraint('id', name='PowerConnection_pkey')
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    organizationId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    outletId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    portId: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    createdAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    updatedAt: Mapped[datetime.datetime] = mapped_column(TIMESTAMP(precision=3), nullable=False)
    name: Mapped[Optional[str]] = mapped_column(Text)
    deletedAt: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP(precision=3))

    Organization_: Mapped['Organization'] = relationship('Organization', back_populates='PowerConnection')
    PowerOutlet_: Mapped['PowerOutlet'] = relationship('PowerOutlet', back_populates='PowerConnection')
    PowerPort_: Mapped['PowerPort'] = relationship('PowerPort', back_populates='PowerConnection')
