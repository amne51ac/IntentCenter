-- CreateTable
CREATE TABLE "ObjectTemplate" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "resourceType" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "slug" TEXT NOT NULL,
    "description" TEXT,
    "isSystem" BOOLEAN NOT NULL DEFAULT false,
    "isDefault" BOOLEAN NOT NULL DEFAULT false,
    "definition" JSONB NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "ObjectTemplate_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "ResourceExtension" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "resourceType" TEXT NOT NULL,
    "resourceId" UUID NOT NULL,
    "templateId" UUID,
    "data" JSONB NOT NULL DEFAULT '{}',
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "ResourceExtension_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "ObjectTemplate_organizationId_resourceType_idx" ON "ObjectTemplate"("organizationId", "resourceType");

-- CreateIndex
CREATE UNIQUE INDEX "ObjectTemplate_organizationId_resourceType_slug_key" ON "ObjectTemplate"("organizationId", "resourceType", "slug");

-- CreateIndex
CREATE INDEX "ResourceExtension_organizationId_idx" ON "ResourceExtension"("organizationId");

-- CreateIndex
CREATE UNIQUE INDEX "ResourceExtension_organizationId_resourceType_resourceId_key" ON "ResourceExtension"("organizationId", "resourceType", "resourceId");

-- AddForeignKey
ALTER TABLE "ObjectTemplate" ADD CONSTRAINT "ObjectTemplate_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ResourceExtension" ADD CONSTRAINT "ResourceExtension_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "ResourceExtension" ADD CONSTRAINT "ResourceExtension_templateId_fkey" FOREIGN KEY ("templateId") REFERENCES "ObjectTemplate"("id") ON DELETE SET NULL ON UPDATE CASCADE;
