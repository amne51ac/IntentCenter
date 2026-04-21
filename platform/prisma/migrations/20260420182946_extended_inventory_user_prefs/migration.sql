-- AlterTable
ALTER TABLE "User" ADD COLUMN     "preferences" JSONB NOT NULL DEFAULT '{}';

-- CreateTable
CREATE TABLE "DynamicGroup" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "slug" TEXT NOT NULL,
    "description" TEXT,
    "definition" JSONB NOT NULL DEFAULT '{}',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "DynamicGroup_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "VirtualChassis" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "domainId" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "VirtualChassis_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "VirtualChassisMember" (
    "id" UUID NOT NULL,
    "virtualChassisId" UUID NOT NULL,
    "deviceId" UUID NOT NULL,
    "priority" INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT "VirtualChassisMember_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Controller" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "deviceId" UUID,
    "role" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "Controller_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "DeviceRedundancyGroup" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "protocol" TEXT,
    "description" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "DeviceRedundancyGroup_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "DeviceRedundancyGroupMember" (
    "id" UUID NOT NULL,
    "groupId" UUID NOT NULL,
    "deviceId" UUID NOT NULL,
    "role" TEXT,

    CONSTRAINT "DeviceRedundancyGroupMember_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "InterfaceRedundancyGroup" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "protocol" TEXT,
    "description" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "InterfaceRedundancyGroup_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "InterfaceRedundancyGroupMember" (
    "id" UUID NOT NULL,
    "groupId" UUID NOT NULL,
    "interfaceId" UUID NOT NULL,
    "role" TEXT,

    CONSTRAINT "InterfaceRedundancyGroupMember_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "PowerPanel" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "locationId" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "PowerPanel_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "PowerFeed" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "powerPanelId" UUID,
    "name" TEXT NOT NULL,
    "voltage" INTEGER,
    "amperage" INTEGER,
    "description" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "PowerFeed_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "CloudNetwork" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "cloudProvider" TEXT,
    "description" TEXT,
    "metadata" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "CloudNetwork_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "CloudService" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "cloudNetworkId" UUID,
    "name" TEXT NOT NULL,
    "serviceType" TEXT,
    "description" TEXT,
    "metadata" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "CloudService_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "WirelessNetwork" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "ssid" TEXT,
    "description" TEXT,
    "metadata" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "WirelessNetwork_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Vpn" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "vpnType" TEXT NOT NULL,
    "description" TEXT,
    "metadata" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "Vpn_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "Cluster" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "clusterType" TEXT,
    "description" TEXT,
    "metadata" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "Cluster_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "VirtualMachine" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "clusterId" UUID,
    "name" TEXT NOT NULL,
    "description" TEXT,
    "metadata" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "VirtualMachine_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "MplsDomain" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "rd" TEXT,
    "description" TEXT,
    "metadata" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "MplsDomain_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "DynamicGroup_organizationId_idx" ON "DynamicGroup"("organizationId");

-- CreateIndex
CREATE UNIQUE INDEX "DynamicGroup_organizationId_slug_key" ON "DynamicGroup"("organizationId", "slug");

-- CreateIndex
CREATE INDEX "VirtualChassis_organizationId_idx" ON "VirtualChassis"("organizationId");

-- CreateIndex
CREATE INDEX "VirtualChassisMember_deviceId_idx" ON "VirtualChassisMember"("deviceId");

-- CreateIndex
CREATE UNIQUE INDEX "VirtualChassisMember_virtualChassisId_deviceId_key" ON "VirtualChassisMember"("virtualChassisId", "deviceId");

-- CreateIndex
CREATE INDEX "Controller_organizationId_idx" ON "Controller"("organizationId");

-- CreateIndex
CREATE INDEX "Controller_deviceId_idx" ON "Controller"("deviceId");

-- CreateIndex
CREATE INDEX "DeviceRedundancyGroup_organizationId_idx" ON "DeviceRedundancyGroup"("organizationId");

-- CreateIndex
CREATE INDEX "DeviceRedundancyGroupMember_deviceId_idx" ON "DeviceRedundancyGroupMember"("deviceId");

-- CreateIndex
CREATE UNIQUE INDEX "DeviceRedundancyGroupMember_groupId_deviceId_key" ON "DeviceRedundancyGroupMember"("groupId", "deviceId");

-- CreateIndex
CREATE INDEX "InterfaceRedundancyGroup_organizationId_idx" ON "InterfaceRedundancyGroup"("organizationId");

-- CreateIndex
CREATE INDEX "InterfaceRedundancyGroupMember_interfaceId_idx" ON "InterfaceRedundancyGroupMember"("interfaceId");

-- CreateIndex
CREATE UNIQUE INDEX "InterfaceRedundancyGroupMember_groupId_interfaceId_key" ON "InterfaceRedundancyGroupMember"("groupId", "interfaceId");

-- CreateIndex
CREATE INDEX "PowerPanel_organizationId_idx" ON "PowerPanel"("organizationId");

-- CreateIndex
CREATE UNIQUE INDEX "PowerPanel_organizationId_locationId_name_key" ON "PowerPanel"("organizationId", "locationId", "name");

-- CreateIndex
CREATE INDEX "PowerFeed_organizationId_idx" ON "PowerFeed"("organizationId");

-- CreateIndex
CREATE INDEX "PowerFeed_powerPanelId_idx" ON "PowerFeed"("powerPanelId");

-- CreateIndex
CREATE INDEX "CloudNetwork_organizationId_idx" ON "CloudNetwork"("organizationId");

-- CreateIndex
CREATE UNIQUE INDEX "CloudNetwork_organizationId_name_key" ON "CloudNetwork"("organizationId", "name");

-- CreateIndex
CREATE INDEX "CloudService_organizationId_idx" ON "CloudService"("organizationId");

-- CreateIndex
CREATE INDEX "CloudService_cloudNetworkId_idx" ON "CloudService"("cloudNetworkId");

-- CreateIndex
CREATE INDEX "WirelessNetwork_organizationId_idx" ON "WirelessNetwork"("organizationId");

-- CreateIndex
CREATE UNIQUE INDEX "WirelessNetwork_organizationId_name_key" ON "WirelessNetwork"("organizationId", "name");

-- CreateIndex
CREATE INDEX "Vpn_organizationId_idx" ON "Vpn"("organizationId");

-- CreateIndex
CREATE UNIQUE INDEX "Vpn_organizationId_name_key" ON "Vpn"("organizationId", "name");

-- CreateIndex
CREATE INDEX "Cluster_organizationId_idx" ON "Cluster"("organizationId");

-- CreateIndex
CREATE UNIQUE INDEX "Cluster_organizationId_name_key" ON "Cluster"("organizationId", "name");

-- CreateIndex
CREATE INDEX "VirtualMachine_organizationId_idx" ON "VirtualMachine"("organizationId");

-- CreateIndex
CREATE INDEX "VirtualMachine_clusterId_idx" ON "VirtualMachine"("clusterId");

-- CreateIndex
CREATE UNIQUE INDEX "VirtualMachine_organizationId_name_key" ON "VirtualMachine"("organizationId", "name");

-- CreateIndex
CREATE INDEX "MplsDomain_organizationId_idx" ON "MplsDomain"("organizationId");

-- CreateIndex
CREATE UNIQUE INDEX "MplsDomain_organizationId_name_key" ON "MplsDomain"("organizationId", "name");

-- AddForeignKey
ALTER TABLE "DynamicGroup" ADD CONSTRAINT "DynamicGroup_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "VirtualChassis" ADD CONSTRAINT "VirtualChassis_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "VirtualChassisMember" ADD CONSTRAINT "VirtualChassisMember_virtualChassisId_fkey" FOREIGN KEY ("virtualChassisId") REFERENCES "VirtualChassis"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "VirtualChassisMember" ADD CONSTRAINT "VirtualChassisMember_deviceId_fkey" FOREIGN KEY ("deviceId") REFERENCES "Device"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Controller" ADD CONSTRAINT "Controller_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Controller" ADD CONSTRAINT "Controller_deviceId_fkey" FOREIGN KEY ("deviceId") REFERENCES "Device"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "DeviceRedundancyGroup" ADD CONSTRAINT "DeviceRedundancyGroup_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "DeviceRedundancyGroupMember" ADD CONSTRAINT "DeviceRedundancyGroupMember_groupId_fkey" FOREIGN KEY ("groupId") REFERENCES "DeviceRedundancyGroup"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "DeviceRedundancyGroupMember" ADD CONSTRAINT "DeviceRedundancyGroupMember_deviceId_fkey" FOREIGN KEY ("deviceId") REFERENCES "Device"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "InterfaceRedundancyGroup" ADD CONSTRAINT "InterfaceRedundancyGroup_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "InterfaceRedundancyGroupMember" ADD CONSTRAINT "InterfaceRedundancyGroupMember_groupId_fkey" FOREIGN KEY ("groupId") REFERENCES "InterfaceRedundancyGroup"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "InterfaceRedundancyGroupMember" ADD CONSTRAINT "InterfaceRedundancyGroupMember_interfaceId_fkey" FOREIGN KEY ("interfaceId") REFERENCES "Interface"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "PowerPanel" ADD CONSTRAINT "PowerPanel_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "PowerPanel" ADD CONSTRAINT "PowerPanel_locationId_fkey" FOREIGN KEY ("locationId") REFERENCES "Location"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "PowerFeed" ADD CONSTRAINT "PowerFeed_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "PowerFeed" ADD CONSTRAINT "PowerFeed_powerPanelId_fkey" FOREIGN KEY ("powerPanelId") REFERENCES "PowerPanel"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CloudNetwork" ADD CONSTRAINT "CloudNetwork_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CloudService" ADD CONSTRAINT "CloudService_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CloudService" ADD CONSTRAINT "CloudService_cloudNetworkId_fkey" FOREIGN KEY ("cloudNetworkId") REFERENCES "CloudNetwork"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "WirelessNetwork" ADD CONSTRAINT "WirelessNetwork_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Vpn" ADD CONSTRAINT "Vpn_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "Cluster" ADD CONSTRAINT "Cluster_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "VirtualMachine" ADD CONSTRAINT "VirtualMachine_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "VirtualMachine" ADD CONSTRAINT "VirtualMachine_clusterId_fkey" FOREIGN KEY ("clusterId") REFERENCES "Cluster"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "MplsDomain" ADD CONSTRAINT "MplsDomain_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
