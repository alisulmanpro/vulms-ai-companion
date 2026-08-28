/*
  Warnings:

  - Added the required column `aspSessionId` to the `VulmsAccount` table without a default value. This is not possible if the table is not empty.

*/
-- AlterTable
ALTER TABLE "VulmsAccount" ADD COLUMN     "aspSessionId" TEXT NOT NULL;
