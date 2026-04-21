-- CreateTable
CREATE TABLE "CircuitSegment" (
    "id" UUID NOT NULL,
    "circuitId" UUID NOT NULL,
    "segmentIndex" INTEGER NOT NULL,
    "label" TEXT,
    "providerId" UUID,
    "bandwidthMbps" INTEGER,
    "status" "CircuitStatus" NOT NULL DEFAULT 'PLANNED',
    "aSideNotes" TEXT,
    "zSideNotes" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "CircuitSegment_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "CircuitSegment_circuitId_idx" ON "CircuitSegment"("circuitId");

-- CreateIndex
CREATE UNIQUE INDEX "CircuitSegment_circuitId_segmentIndex_key" ON "CircuitSegment"("circuitId", "segmentIndex");

-- AddForeignKey
ALTER TABLE "CircuitSegment" ADD CONSTRAINT "CircuitSegment_circuitId_fkey" FOREIGN KEY ("circuitId") REFERENCES "Circuit"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "CircuitSegment" ADD CONSTRAINT "CircuitSegment_providerId_fkey" FOREIGN KEY ("providerId") REFERENCES "Provider"("id") ON DELETE SET NULL ON UPDATE CASCADE;
