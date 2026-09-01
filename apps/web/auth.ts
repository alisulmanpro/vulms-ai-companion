import NextAuth from "next-auth";
import { authConfig } from "./auth.config";
import { CustomPrismaAdapter } from "./lib/auth-adapter";

export const { handlers, signIn, signOut, auth } = NextAuth({
  ...authConfig,
  adapter: CustomPrismaAdapter(),
});
