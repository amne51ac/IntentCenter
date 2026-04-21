-- Slots (ModuleBay) on device OR on a module (card); cards (Module) seated in a bay; optional FrontPort.moduleId.

-- New columns
ALTER TABLE "Module" ADD COLUMN IF NOT EXISTS "moduleBayId" UUID;
ALTER TABLE "ModuleBay" ADD COLUMN IF NOT EXISTS "parentModuleId" UUID;
ALTER TABLE "FrontPort" ADD COLUMN IF NOT EXISTS "moduleId" UUID;

-- Allow bays that live only on a module (not directly on a device)
ALTER TABLE "ModuleBay" ALTER COLUMN "deviceId" DROP NOT NULL;

-- Replace single unique (deviceId, name) with partial uniques so device vs module hosts don't collide
DROP INDEX IF EXISTS "ModuleBay_deviceId_name_key";

CREATE UNIQUE INDEX "ModuleBay_device_slot_name" ON "ModuleBay"("deviceId", "name") WHERE "deviceId" IS NOT NULL;
CREATE UNIQUE INDEX "ModuleBay_module_slot_name" ON "ModuleBay"("parentModuleId", "name") WHERE "parentModuleId" IS NOT NULL;

ALTER TABLE "ModuleBay" DROP CONSTRAINT IF EXISTS "ModuleBay_slot_parent_check";
ALTER TABLE "ModuleBay" ADD CONSTRAINT "ModuleBay_slot_parent_check" CHECK (
  ("deviceId" IS NOT NULL AND "parentModuleId" IS NULL)
  OR ("deviceId" IS NULL AND "parentModuleId" IS NOT NULL)
);

-- Foreign keys
ALTER TABLE "Module" DROP CONSTRAINT IF EXISTS "Module_moduleBayId_fkey";
ALTER TABLE "Module" ADD CONSTRAINT "Module_moduleBayId_fkey" FOREIGN KEY ("moduleBayId") REFERENCES "ModuleBay"("id") ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE "ModuleBay" DROP CONSTRAINT IF EXISTS "ModuleBay_parentModuleId_fkey";
ALTER TABLE "ModuleBay" ADD CONSTRAINT "ModuleBay_parentModuleId_fkey" FOREIGN KEY ("parentModuleId") REFERENCES "Module"("id") ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "FrontPort" DROP CONSTRAINT IF EXISTS "FrontPort_moduleId_fkey";
ALTER TABLE "FrontPort" ADD CONSTRAINT "FrontPort_moduleId_fkey" FOREIGN KEY ("moduleId") REFERENCES "Module"("id") ON DELETE SET NULL ON UPDATE CASCADE;

CREATE UNIQUE INDEX IF NOT EXISTS "Module_moduleBayId_key" ON "Module"("moduleBayId");

CREATE INDEX IF NOT EXISTS "ModuleBay_parentModuleId_idx" ON "ModuleBay"("parentModuleId");
CREATE INDEX IF NOT EXISTS "FrontPort_moduleId_idx" ON "FrontPort"("moduleId");
