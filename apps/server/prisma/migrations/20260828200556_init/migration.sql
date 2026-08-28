/*
  Warnings:

  - You are about to drop the `vulms_account` table. If the table is not empty, all the data it contains will be lost.

*/
-- DropForeignKey
ALTER TABLE "vulms_account" DROP CONSTRAINT "vulms_account_userId_fkey";

-- DropTable
DROP TABLE "vulms_account";

-- CreateTable
CREATE TABLE "VulmsAccount" (
    "id" TEXT NOT NULL,
    "userId" TEXT NOT NULL,
    "studentId" TEXT NOT NULL,
    "encryptedPassword" TEXT NOT NULL,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "lastAssignmentHash" TEXT,
    "lastQuizHash" TEXT,
    "lastGdbHash" TEXT NOT NULL,
    "lastPolledAt" TIMESTAMP(3),
    "lastAuthFailedAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,

    CONSTRAINT "VulmsAccount_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "VulmsAccount_userId_key" ON "VulmsAccount"("userId");

-- CreateIndex
CREATE INDEX "VulmsAccount_isActive_idx" ON "VulmsAccount"("isActive");

-- AddForeignKey
ALTER TABLE "VulmsAccount" ADD CONSTRAINT "VulmsAccount_userId_fkey" FOREIGN KEY ("userId") REFERENCES "user"("id") ON DELETE CASCADE ON UPDATE CASCADE;
