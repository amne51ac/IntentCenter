-- AlterTable
ALTER TABLE "Circuit" ADD COLUMN     "circuitTypeId" UUID;

-- AlterTable
ALTER TABLE "Prefix" ADD COLUMN     "rirId" UUID;

-- AlterTable
ALTER TABLE "Rack" ADD COLUMN     "rackGroupId" UUID;

-- CreateTable
CREATE TABLE "CircuitType" (
    "id" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "slug" TEXT NOT NULL,
    "description" TEXT,

    CONSTRAINT "CircuitType_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Rir" (
    "id" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "slug" TEXT NOT NULL,
    "description" TEXT,

    CONSTRAINT "Rir_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Tag" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "slug" TEXT NOT NULL,
    "color" TEXT,
    "description" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "Tag_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "TagAssignment" (
    "id" UUID NOT NULL,
    "tagId" UUID NOT NULL,
    "resourceType" TEXT NOT NULL,
    "resourceId" UUID NOT NULL,

    CONSTRAINT "TagAssignment_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "RouteTarget" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "vrfId" UUID,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "RouteTarget_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ProviderNetwork" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "providerId" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "ProviderNetwork_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "RackGroup" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "slug" TEXT NOT NULL,
    "description" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "RackGroup_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "RackReservation" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "rackId" UUID NOT NULL,
    "label" TEXT NOT NULL,
    "startsAt" TIMESTAMP(3),
    "endsAt" TIMESTAMP(3),
    "description" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "RackReservation_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "TenantGroup" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "slug" TEXT NOT NULL,
    "description" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "TenantGroup_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Contact" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "email" TEXT,
    "phone" TEXT,
    "title" TEXT,
    "description" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "Contact_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Team" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "slug" TEXT NOT NULL,
    "description" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "Team_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "DeviceFamily" (
    "id" UUID NOT NULL,
    "manufacturerId" UUID,
    "name" TEXT NOT NULL,
    "slug" TEXT NOT NULL,
    "description" TEXT,

    CONSTRAINT "DeviceFamily_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "SoftwarePlatform" (
    "id" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "slug" TEXT NOT NULL,
    "description" TEXT,

    CONSTRAINT "SoftwarePlatform_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "SoftwareVersion" (
    "id" UUID NOT NULL,
    "platformId" UUID NOT NULL,
    "version" TEXT NOT NULL,
    "releaseNotes" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "SoftwareVersion_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "SoftwareImageFile" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "platformId" UUID,
    "filename" TEXT NOT NULL,
    "sha256" TEXT,
    "description" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "SoftwareImageFile_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "IpamNamespace" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "slug" TEXT NOT NULL,
    "description" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "IpamNamespace_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "VirtualDeviceContext" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "deviceId" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "identifier" TEXT,
    "description" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "VirtualDeviceContext_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "DeviceGroup" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "slug" TEXT NOT NULL,
    "description" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "DeviceGroup_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "DeviceGroupMember" (
    "id" UUID NOT NULL,
    "groupId" UUID NOT NULL,
    "deviceId" UUID NOT NULL,

    CONSTRAINT "DeviceGroupMember_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "FrontPort" (
    "id" UUID NOT NULL,
    "deviceId" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "label" TEXT,
    "type" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "FrontPort_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "RearPort" (
    "id" UUID NOT NULL,
    "deviceId" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "label" TEXT,
    "type" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "RearPort_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ConsolePort" (
    "id" UUID NOT NULL,
    "deviceId" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "label" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "ConsolePort_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ConsoleServerPort" (
    "id" UUID NOT NULL,
    "deviceId" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "label" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "ConsoleServerPort_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "PowerPort" (
    "id" UUID NOT NULL,
    "deviceId" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "label" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "PowerPort_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "PowerOutlet" (
    "id" UUID NOT NULL,
    "deviceId" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "label" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "PowerOutlet_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "DeviceBay" (
    "id" UUID NOT NULL,
    "parentDeviceId" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "installedDeviceId" UUID,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "DeviceBay_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ModuleBay" (
    "id" UUID NOT NULL,
    "deviceId" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "position" INTEGER,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "ModuleBay_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "InventoryItem" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "deviceId" UUID,
    "name" TEXT NOT NULL,
    "serial" TEXT,
    "assetTag" TEXT,
    "description" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "InventoryItem_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ModuleType" (
    "id" UUID NOT NULL,
    "manufacturerId" UUID,
    "model" TEXT NOT NULL,
    "partNumber" TEXT,

    CONSTRAINT "ModuleType_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Module" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "deviceId" UUID NOT NULL,
    "moduleTypeId" UUID NOT NULL,
    "serial" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "Module_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ConsoleConnection" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "name" TEXT,
    "serverPortId" UUID NOT NULL,
    "clientPortId" UUID NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "ConsoleConnection_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "PowerConnection" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "name" TEXT,
    "outletId" UUID NOT NULL,
    "portId" UUID NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "PowerConnection_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "CircuitTermination" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "circuitId" UUID NOT NULL,
    "side" TEXT NOT NULL,
    "locationId" UUID,
    "portName" TEXT,
    "description" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "CircuitTermination_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "RackElevation" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "rackId" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "imageUrl" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "RackElevation_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "StatusDefinition" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "resourceType" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "slug" TEXT NOT NULL,
    "color" TEXT,
    "description" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "StatusDefinition_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "CircuitType_name_key" ON "CircuitType"("name");

-- CreateIndex
CREATE UNIQUE INDEX "CircuitType_slug_key" ON "CircuitType"("slug");

-- CreateIndex
CREATE UNIQUE INDEX "Rir_name_key" ON "Rir"("name");

-- CreateIndex
CREATE UNIQUE INDEX "Rir_slug_key" ON "Rir"("slug");

-- CreateIndex
CREATE INDEX "Tag_organizationId_idx" ON "Tag"("organizationId");

-- CreateIndex
CREATE UNIQUE INDEX "Tag_organizationId_slug_key" ON "Tag"("organizationId", "slug");

-- CreateIndex
CREATE INDEX "TagAssignment_resourceType_resourceId_idx" ON "TagAssignment"("resourceType", "resourceId");

-- CreateIndex
CREATE UNIQUE INDEX "TagAssignment_tagId_resourceType_resourceId_key" ON "TagAssignment"("tagId", "resourceType", "resourceId");

-- CreateIndex
CREATE INDEX "RouteTarget_organizationId_idx" ON "RouteTarget"("organizationId");

-- CreateIndex
CREATE INDEX "RouteTarget_vrfId_idx" ON "RouteTarget"("vrfId");

-- CreateIndex
CREATE UNIQUE INDEX "RouteTarget_organizationId_name_key" ON "RouteTarget"("organizationId", "name");

-- CreateIndex
CREATE INDEX "ProviderNetwork_organizationId_idx" ON "ProviderNetwork"("organizationId");

-- CreateIndex
CREATE UNIQUE INDEX "ProviderNetwork_organizationId_providerId_name_key" ON "ProviderNetwork"("organizationId", "providerId", "name");

-- CreateIndex
CREATE INDEX "RackGroup_organizationId_idx" ON "RackGroup"("organizationId");

-- CreateIndex
CREATE UNIQUE INDEX "RackGroup_organizationId_slug_key" ON "RackGroup"("organizationId", "slug");

-- CreateIndex
CREATE INDEX "RackReservation_organizationId_idx" ON "RackReservation"("organizationId");

-- CreateIndex
CREATE INDEX "RackReservation_rackId_idx" ON "RackReservation"("rackId");

-- CreateIndex
CREATE INDEX "TenantGroup_organizationId_idx" ON "TenantGroup"("organizationId");

-- CreateIndex
CREATE UNIQUE INDEX "TenantGroup_organizationId_slug_key" ON "TenantGroup"("organizationId", "slug");

-- CreateIndex
CREATE INDEX "Contact_organizationId_idx" ON "Contact"("organizationId");

-- CreateIndex
CREATE INDEX "Team_organizationId_idx" ON "Team"("organizationId");

-- CreateIndex
CREATE UNIQUE INDEX "Team_organizationId_slug_key" ON "Team"("organizationId", "slug");

-- CreateIndex
CREATE UNIQUE INDEX "DeviceFamily_slug_key" ON "DeviceFamily"("slug");

-- CreateIndex
CREATE UNIQUE INDEX "SoftwarePlatform_name_key" ON "SoftwarePlatform"("name");

-- CreateIndex
CREATE UNIQUE INDEX "SoftwarePlatform_slug_key" ON "SoftwarePlatform"("slug");

-- CreateIndex
CREATE INDEX "SoftwareVersion_platformId_idx" ON "SoftwareVersion"("platformId");

-- CreateIndex
CREATE UNIQUE INDEX "SoftwareVersion_platformId_version_key" ON "SoftwareVersion"("platformId", "version");

-- CreateIndex
CREATE INDEX "SoftwareImageFile_organizationId_idx" ON "SoftwareImageFile"("organizationId");

-- CreateIndex
CREATE INDEX "IpamNamespace_organizationId_idx" ON "IpamNamespace"("organizationId");

-- CreateIndex
CREATE UNIQUE INDEX "IpamNamespace_organizationId_slug_key" ON "IpamNamespace"("organizationId", "slug");

-- CreateIndex
CREATE INDEX "VirtualDeviceContext_deviceId_idx" ON "VirtualDeviceContext"("deviceId");

-- CreateIndex
CREATE UNIQUE INDEX "VirtualDeviceContext_organizationId_deviceId_name_key" ON "VirtualDeviceContext"("organizationId", "deviceId", "name");

-- CreateIndex
CREATE INDEX "DeviceGroup_organizationId_idx" ON "DeviceGroup"("organizationId");

-- CreateIndex
CREATE UNIQUE INDEX "DeviceGroup_organizationId_slug_key" ON "DeviceGroup"("organizationId", "slug");

-- CreateIndex
CREATE INDEX "DeviceGroupMember_deviceId_idx" ON "DeviceGroupMember"("deviceId");

-- CreateIndex
CREATE UNIQUE INDEX "DeviceGroupMember_groupId_deviceId_key" ON "DeviceGroupMember"("groupId", "deviceId");

-- CreateIndex
CREATE INDEX "FrontPort_deviceId_idx" ON "FrontPort"("deviceId");

-- CreateIndex
CREATE UNIQUE INDEX "FrontPort_deviceId_name_key" ON "FrontPort"("deviceId", "name");

-- CreateIndex
CREATE INDEX "RearPort_deviceId_idx" ON "RearPort"("deviceId");

-- CreateIndex
CREATE UNIQUE INDEX "RearPort_deviceId_name_key" ON "RearPort"("deviceId", "name");

-- CreateIndex
CREATE INDEX "ConsolePort_deviceId_idx" ON "ConsolePort"("deviceId");

-- CreateIndex
CREATE UNIQUE INDEX "ConsolePort_deviceId_name_key" ON "ConsolePort"("deviceId", "name");

-- CreateIndex
CREATE INDEX "ConsoleServerPort_deviceId_idx" ON "ConsoleServerPort"("deviceId");

-- CreateIndex
CREATE UNIQUE INDEX "ConsoleServerPort_deviceId_name_key" ON "ConsoleServerPort"("deviceId", "name");

-- CreateIndex
CREATE INDEX "PowerPort_deviceId_idx" ON "PowerPort"("deviceId");

-- CreateIndex
CREATE UNIQUE INDEX "PowerPort_deviceId_name_key" ON "PowerPort"("deviceId", "name");

-- CreateIndex
CREATE INDEX "PowerOutlet_deviceId_idx" ON "PowerOutlet"("deviceId");

-- CreateIndex
CREATE UNIQUE INDEX "PowerOutlet_deviceId_name_key" ON "PowerOutlet"("deviceId", "name");

-- CreateIndex
CREATE INDEX "DeviceBay_parentDeviceId_idx" ON "DeviceBay"("parentDeviceId");

-- CreateIndex
CREATE INDEX "DeviceBay_installedDeviceId_idx" ON "DeviceBay"("installedDeviceId");

-- CreateIndex
CREATE UNIQUE INDEX "DeviceBay_parentDeviceId_name_key" ON "DeviceBay"("parentDeviceId", "name");

-- CreateIndex
CREATE INDEX "ModuleBay_deviceId_idx" ON "ModuleBay"("deviceId");

-- CreateIndex
CREATE UNIQUE INDEX "ModuleBay_deviceId_name_key" ON "ModuleBay"("deviceId", "name");

-- CreateIndex
CREATE INDEX "InventoryItem_organizationId_idx" ON "InventoryItem"("organizationId");

-- CreateIndex
CREATE INDEX "InventoryItem_deviceId_idx" ON "InventoryItem"("deviceId");

-- CreateIndex
CREATE UNIQUE INDEX "ModuleType_manufacturerId_model_key" ON "ModuleType"("manufacturerId", "model");

-- CreateIndex
CREATE INDEX "Module_organizationId_idx" ON "Module"("organizationId");

-- CreateIndex
CREATE INDEX "Module_deviceId_idx" ON "Module"("deviceId");

-- CreateIndex
CREATE UNIQUE INDEX "ConsoleConnection_serverPortId_key" ON "ConsoleConnection"("serverPortId");

-- CreateIndex
CREATE UNIQUE INDEX "ConsoleConnection_clientPortId_key" ON "ConsoleConnection"("clientPortId");

-- CreateIndex
CREATE INDEX "ConsoleConnection_organizationId_idx" ON "ConsoleConnection"("organizationId");

-- CreateIndex
CREATE UNIQUE INDEX "PowerConnection_outletId_key" ON "PowerConnection"("outletId");

-- CreateIndex
CREATE UNIQUE INDEX "PowerConnection_portId_key" ON "PowerConnection"("portId");

-- CreateIndex
CREATE INDEX "PowerConnection_organizationId_idx" ON "PowerConnection"("organizationId");

-- CreateIndex
CREATE INDEX "CircuitTermination_organizationId_idx" ON "CircuitTermination"("organizationId");

-- CreateIndex
CREATE INDEX "CircuitTermination_locationId_idx" ON "CircuitTermination"("locationId");

-- CreateIndex
CREATE UNIQUE INDEX "CircuitTermination_circuitId_side_key" ON "CircuitTermination"("circuitId", "side");

-- CreateIndex
CREATE INDEX "RackElevation_organizationId_idx" ON "RackElevation"("organizationId");

-- CreateIndex
CREATE INDEX "RackElevation_rackId_idx" ON "RackElevation"("rackId");

-- CreateIndex
CREATE INDEX "StatusDefinition_organizationId_idx" ON "StatusDefinition"("organizationId");

-- CreateIndex
CREATE UNIQUE INDEX "StatusDefinition_organizationId_resourceType_slug_key" ON "StatusDefinition"("organizationId", "resourceType", "slug");

-- CreateIndex
CREATE INDEX "Circuit_circuitTypeId_idx" ON "Circuit"("circuitTypeId");

-- CreateIndex
CREATE INDEX "Rack_rackGroupId_idx" ON "Rack"("rackGroupId");

-- AddForeignKey
ALTER TABLE "Rack" ADD CONSTRAINT "Rack_rackGroupId_fkey" FOREIGN KEY ("rackGroupId") REFERENCES "RackGroup"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Prefix" ADD CONSTRAINT "Prefix_rirId_fkey" FOREIGN KEY ("rirId") REFERENCES "Rir"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Circuit" ADD CONSTRAINT "Circuit_circuitTypeId_fkey" FOREIGN KEY ("circuitTypeId") REFERENCES "CircuitType"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Tag" ADD CONSTRAINT "Tag_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "TagAssignment" ADD CONSTRAINT "TagAssignment_tagId_fkey" FOREIGN KEY ("tagId") REFERENCES "Tag"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "RouteTarget" ADD CONSTRAINT "RouteTarget_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "RouteTarget" ADD CONSTRAINT "RouteTarget_vrfId_fkey" FOREIGN KEY ("vrfId") REFERENCES "Vrf"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ProviderNetwork" ADD CONSTRAINT "ProviderNetwork_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ProviderNetwork" ADD CONSTRAINT "ProviderNetwork_providerId_fkey" FOREIGN KEY ("providerId") REFERENCES "Provider"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "RackGroup" ADD CONSTRAINT "RackGroup_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "RackReservation" ADD CONSTRAINT "RackReservation_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "RackReservation" ADD CONSTRAINT "RackReservation_rackId_fkey" FOREIGN KEY ("rackId") REFERENCES "Rack"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "TenantGroup" ADD CONSTRAINT "TenantGroup_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Contact" ADD CONSTRAINT "Contact_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Team" ADD CONSTRAINT "Team_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "DeviceFamily" ADD CONSTRAINT "DeviceFamily_manufacturerId_fkey" FOREIGN KEY ("manufacturerId") REFERENCES "Manufacturer"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "SoftwareVersion" ADD CONSTRAINT "SoftwareVersion_platformId_fkey" FOREIGN KEY ("platformId") REFERENCES "SoftwarePlatform"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "SoftwareImageFile" ADD CONSTRAINT "SoftwareImageFile_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "SoftwareImageFile" ADD CONSTRAINT "SoftwareImageFile_platformId_fkey" FOREIGN KEY ("platformId") REFERENCES "SoftwarePlatform"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "IpamNamespace" ADD CONSTRAINT "IpamNamespace_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "VirtualDeviceContext" ADD CONSTRAINT "VirtualDeviceContext_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "VirtualDeviceContext" ADD CONSTRAINT "VirtualDeviceContext_deviceId_fkey" FOREIGN KEY ("deviceId") REFERENCES "Device"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "DeviceGroup" ADD CONSTRAINT "DeviceGroup_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "DeviceGroupMember" ADD CONSTRAINT "DeviceGroupMember_groupId_fkey" FOREIGN KEY ("groupId") REFERENCES "DeviceGroup"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "DeviceGroupMember" ADD CONSTRAINT "DeviceGroupMember_deviceId_fkey" FOREIGN KEY ("deviceId") REFERENCES "Device"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "FrontPort" ADD CONSTRAINT "FrontPort_deviceId_fkey" FOREIGN KEY ("deviceId") REFERENCES "Device"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "RearPort" ADD CONSTRAINT "RearPort_deviceId_fkey" FOREIGN KEY ("deviceId") REFERENCES "Device"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ConsolePort" ADD CONSTRAINT "ConsolePort_deviceId_fkey" FOREIGN KEY ("deviceId") REFERENCES "Device"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ConsoleServerPort" ADD CONSTRAINT "ConsoleServerPort_deviceId_fkey" FOREIGN KEY ("deviceId") REFERENCES "Device"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "PowerPort" ADD CONSTRAINT "PowerPort_deviceId_fkey" FOREIGN KEY ("deviceId") REFERENCES "Device"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "PowerOutlet" ADD CONSTRAINT "PowerOutlet_deviceId_fkey" FOREIGN KEY ("deviceId") REFERENCES "Device"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "DeviceBay" ADD CONSTRAINT "DeviceBay_parentDeviceId_fkey" FOREIGN KEY ("parentDeviceId") REFERENCES "Device"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "DeviceBay" ADD CONSTRAINT "DeviceBay_installedDeviceId_fkey" FOREIGN KEY ("installedDeviceId") REFERENCES "Device"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ModuleBay" ADD CONSTRAINT "ModuleBay_deviceId_fkey" FOREIGN KEY ("deviceId") REFERENCES "Device"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "InventoryItem" ADD CONSTRAINT "InventoryItem_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "InventoryItem" ADD CONSTRAINT "InventoryItem_deviceId_fkey" FOREIGN KEY ("deviceId") REFERENCES "Device"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ModuleType" ADD CONSTRAINT "ModuleType_manufacturerId_fkey" FOREIGN KEY ("manufacturerId") REFERENCES "Manufacturer"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Module" ADD CONSTRAINT "Module_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Module" ADD CONSTRAINT "Module_deviceId_fkey" FOREIGN KEY ("deviceId") REFERENCES "Device"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Module" ADD CONSTRAINT "Module_moduleTypeId_fkey" FOREIGN KEY ("moduleTypeId") REFERENCES "ModuleType"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ConsoleConnection" ADD CONSTRAINT "ConsoleConnection_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ConsoleConnection" ADD CONSTRAINT "ConsoleConnection_serverPortId_fkey" FOREIGN KEY ("serverPortId") REFERENCES "ConsoleServerPort"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ConsoleConnection" ADD CONSTRAINT "ConsoleConnection_clientPortId_fkey" FOREIGN KEY ("clientPortId") REFERENCES "ConsolePort"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "PowerConnection" ADD CONSTRAINT "PowerConnection_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "PowerConnection" ADD CONSTRAINT "PowerConnection_outletId_fkey" FOREIGN KEY ("outletId") REFERENCES "PowerOutlet"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "PowerConnection" ADD CONSTRAINT "PowerConnection_portId_fkey" FOREIGN KEY ("portId") REFERENCES "PowerPort"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CircuitTermination" ADD CONSTRAINT "CircuitTermination_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CircuitTermination" ADD CONSTRAINT "CircuitTermination_circuitId_fkey" FOREIGN KEY ("circuitId") REFERENCES "Circuit"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CircuitTermination" ADD CONSTRAINT "CircuitTermination_locationId_fkey" FOREIGN KEY ("locationId") REFERENCES "Location"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "RackElevation" ADD CONSTRAINT "RackElevation_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "RackElevation" ADD CONSTRAINT "RackElevation_rackId_fkey" FOREIGN KEY ("rackId") REFERENCES "Rack"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "StatusDefinition" ADD CONSTRAINT "StatusDefinition_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
