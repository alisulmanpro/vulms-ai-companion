-- CreateTable
CREATE TABLE "vulms_account" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "studentId" TEXT NOT NULL,
    "password" TEXT NOT NULL,
    "aspSessionId" TEXT,
    "isBrowserOpen" BOOLEAN NOT NULL DEFAULT false,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "lastSyncedAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "vulms_account_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "vulms_account_userId_idx" ON "vulms_account"("userId");

-- AddForeignKey
ALTER TABLE "vulms_account" ADD CONSTRAINT "vulms_account_userId_fkey" FOREIGN KEY ("userId") REFERENCES "user"("id") ON DELETE CASCADE ON UPDATE CASCADE;
