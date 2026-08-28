/*
  Warnings:

  - You are about to drop the column `isActive` on the `vulms_account` table. All the data in the column will be lost.
  - You are about to drop the column `whatsappNumber` on the `vulms_account` table. All the data in the column will be lost.
  - Added the required column `whatsappNumber` to the `user` table without a default value. This is not possible if the table is not empty.

*/
-- AlterTable
ALTER TABLE "user" ADD COLUMN     "whatsappNumber" TEXT NOT NULL;

-- AlterTable
ALTER TABLE "vulms_account" DROP COLUMN "isActive",
DROP COLUMN "whatsappNumber";
