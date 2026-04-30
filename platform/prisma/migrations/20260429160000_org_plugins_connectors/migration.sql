-- Per-tenant plugin installs + connector registrations

-- PluginRegistration: scope to organization
ALTER TABLE "PluginRegistration" ADD COLUMN "organizationId" UUID;

UPDATE "PluginRegistration" SET "organizationId" = (SELECT "id" FROM "Organization" ORDER BY "createdAt" ASC LIMIT 1) WHERE "organizationId" IS NULL;

ALTER TABLE "PluginRegistration" ALTER COLUMN "organizationId" SET NOT NULL;

DROP INDEX IF EXISTS "PluginRegistration_packageName_key";

CREATE UNIQUE INDEX "PluginRegistration_organizationId_packageName_key" ON "PluginRegistration"("organizationId", "packageName");

CREATE INDEX "PluginRegistration_organizationId_idx" ON "PluginRegistration"("organizationId");

ALTER TABLE "PluginRegistration" ADD CONSTRAINT "PluginRegistration_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- ConnectorRegistration
CREATE TABLE "ConnectorRegistration" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "pluginRegistrationId" UUID,
    "type" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "enabled" BOOLEAN NOT NULL DEFAULT true,
    "settings" JSONB NOT NULL DEFAULT '{}',
    "credentialsEnc" TEXT,
    "healthStatus" TEXT,
    "lastSyncAt" TIMESTAMP(3),
    "lastError" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "ConnectorRegistration_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX "ConnectorRegistration_organizationId_name_key" ON "ConnectorRegistration"("organizationId", "name");

CREATE INDEX "ConnectorRegistration_organizationId_idx" ON "ConnectorRegistration"("organizationId");

CREATE INDEX "ConnectorRegistration_pluginRegistrationId_idx" ON "ConnectorRegistration"("pluginRegistrationId");

ALTER TABLE "ConnectorRegistration" ADD CONSTRAINT "ConnectorRegistration_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "ConnectorRegistration" ADD CONSTRAINT "ConnectorRegistration_pluginRegistrationId_fkey" FOREIGN KEY ("pluginRegistrationId") REFERENCES "PluginRegistration"("id") ON DELETE SET NULL ON UPDATE CASCADE;
