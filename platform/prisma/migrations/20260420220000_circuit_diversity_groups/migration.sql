-- CreateTable
CREATE TABLE "CircuitDiversityGroup" (
    "id" UUID NOT NULL,
    "organizationId" UUID NOT NULL,
    "name" TEXT NOT NULL,
    "slug" TEXT NOT NULL,
    "description" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "deletedAt" TIMESTAMP(3),

    CONSTRAINT "CircuitDiversityGroup_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "CircuitDiversityGroup_organizationId_slug_key" ON "CircuitDiversityGroup"("organizationId", "slug");

-- CreateIndex
CREATE INDEX "CircuitDiversityGroup_organizationId_idx" ON "CircuitDiversityGroup"("organizationId");

-- AddForeignKey
ALTER TABLE "CircuitDiversityGroup" ADD CONSTRAINT "CircuitDiversityGroup_organizationId_fkey" FOREIGN KEY ("organizationId") REFERENCES "Organization"("id") ON DELETE RESTRICT ON UPDATE CASCADE;

-- AlterTable
ALTER TABLE "Circuit" ADD COLUMN "circuitDiversityGroupId" UUID;

-- CreateIndex
CREATE INDEX "Circuit_circuitDiversityGroupId_idx" ON "Circuit"("circuitDiversityGroupId");

-- AddForeignKey
ALTER TABLE "Circuit" ADD CONSTRAINT "Circuit_circuitDiversityGroupId_fkey" FOREIGN KEY ("circuitDiversityGroupId") REFERENCES "CircuitDiversityGroup"("id") ON DELETE SET NULL ON UPDATE CASCADE;
