-- CreateTable
CREATE TABLE "PluginPlacement" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "pluginRegistrationId" UUID NOT NULL,
    "pageId" TEXT NOT NULL,
    "slot" TEXT NOT NULL,
    "widgetKey" TEXT NOT NULL,
    "priority" INTEGER NOT NULL DEFAULT 0,
    "enabled" BOOLEAN NOT NULL DEFAULT true,
    "filters" JSONB,
    "macroBindings" JSONB,
    "requiredPermissions" JSONB,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "PluginPlacement_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "PluginPlacement_organizationId_pageId_idx" ON "PluginPlacement"("organizationId", "pageId");

-- CreateIndex
CREATE INDEX "PluginPlacement_pluginRegistrationId_idx" ON "PluginPlacement"("pluginRegistrationId");

-- AddForeignKey
ALTER TABLE "PluginPlacement" ADD CONSTRAINT "PluginPlacement_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "PluginPlacement" ADD CONSTRAINT "PluginPlacement_pluginRegistrationId_fkey" FOREIGN KEY ("pluginRegistrationId") REFERENCES "PluginRegistration"("id") ON DELETE CASCADE ON UPDATE CASCADE;
