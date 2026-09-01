import type { Adapter, AdapterAccount, AdapterSession, AdapterUser, VerificationToken } from "next-auth/adapters";
import { prisma } from "./prisma";

export function CustomPrismaAdapter(): Adapter {
  return {
    async createUser(user: Omit<AdapterUser, "id">): Promise<AdapterUser> {
      const created = await prisma.user.create({
        data: {
          name: user.name ?? user.email.split("@")[0] ?? "User",
          email: user.email,
          image: user.image ?? null,
          emailVerified: !!user.emailVerified,
        },
      });

      return {
        id: created.id,
        name: created.name,
        email: created.email,
        emailVerified: created.emailVerified ? new Date(created.updatedAt) : null,
        image: created.image,
      };
    },

    async getUser(id: string): Promise<AdapterUser | null> {
      const user = await prisma.user.findUnique({
        where: { id },
      });
      if (!user) return null;

      return {
        id: user.id,
        name: user.name,
        email: user.email,
        emailVerified: user.emailVerified ? new Date(user.updatedAt) : null,
        image: user.image,
      };
    },

    async getUserByEmail(email: string): Promise<AdapterUser | null> {
      const user = await prisma.user.findUnique({
        where: { email },
      });
      if (!user) return null;

      return {
        id: user.id,
        name: user.name,
        email: user.email,
        emailVerified: user.emailVerified ? new Date(user.updatedAt) : null,
        image: user.image,
      };
    },

    async getUserByAccount({
      provider,
      providerAccountId,
    }: {
      provider: string;
      providerAccountId: string;
    }): Promise<AdapterUser | null> {
      const account = await prisma.account.findFirst({
        where: {
          providerId: provider,
          accountId: providerAccountId,
        },
        include: {
          user: true,
        },
      });

      if (!account || !account.user) return null;

      return {
        id: account.user.id,
        name: account.user.name,
        email: account.user.email,
        emailVerified: account.user.emailVerified ? new Date(account.user.updatedAt) : null,
        image: account.user.image,
      };
    },

    async updateUser(user: Partial<AdapterUser> & Pick<AdapterUser, "id">): Promise<AdapterUser> {
      const updated = await prisma.user.update({
        where: { id: user.id },
        data: {
          name: user.name ?? undefined,
          email: user.email ?? undefined,
          image: user.image ?? undefined,
          emailVerified: user.emailVerified !== undefined ? !!user.emailVerified : undefined,
        },
      });

      return {
        id: updated.id,
        name: updated.name,
        email: updated.email,
        emailVerified: updated.emailVerified ? new Date(updated.updatedAt) : null,
        image: updated.image,
      };
    },

    async deleteUser(userId: string) {
      await prisma.user.delete({
        where: { id: userId },
      });
    },

    async linkAccount(account: AdapterAccount): Promise<AdapterAccount | null | undefined> {
      await prisma.account.create({
        data: {
          userId: account.userId,
          providerId: account.provider,
          accountId: account.providerAccountId,
          accessToken: account.access_token ?? null,
          refreshToken: account.refresh_token ?? null,
          idToken: account.id_token ?? null,
          scope: account.scope ?? null,
          accessTokenExpiresAt: account.expires_at ? new Date(account.expires_at * 1000) : null,
        },
      });

      return account;
    },

    async unlinkAccount({
      provider,
      providerAccountId,
    }: {
      provider: string;
      providerAccountId: string;
    }) {
      const account = await prisma.account.findFirst({
        where: {
          providerId: provider,
          accountId: providerAccountId,
        },
      });

      if (account) {
        await prisma.account.delete({
          where: { id: account.id },
        });
      }
    },

    async createSession({
      sessionToken,
      userId,
      expires,
    }: {
      sessionToken: string;
      userId: string;
      expires: Date;
    }): Promise<AdapterSession> {
      const session = await prisma.session.create({
        data: {
          token: sessionToken,
          userId,
          expiresAt: expires,
        },
      });

      return {
        sessionToken: session.token,
        userId: session.userId,
        expires: session.expiresAt,
      };
    },

    async getSessionAndUser(sessionToken: string): Promise<{
      session: AdapterSession;
      user: AdapterUser;
    } | null> {
      const sessionAndUser = await prisma.session.findUnique({
        where: { token: sessionToken },
        include: { user: true },
      });

      if (!sessionAndUser) return null;

      const { user, ...session } = sessionAndUser;

      return {
        session: {
          sessionToken: session.token,
          userId: session.userId,
          expires: session.expiresAt,
        },
        user: {
          id: user.id,
          name: user.name,
          email: user.email,
          emailVerified: user.emailVerified ? new Date(user.updatedAt) : null,
          image: user.image,
        },
      };
    },

    async updateSession(
      session: Partial<AdapterSession> & Pick<AdapterSession, "sessionToken">
    ): Promise<AdapterSession | null | undefined> {
      const updated = await prisma.session.update({
        where: { token: session.sessionToken },
        data: {
          expiresAt: session.expires,
        },
      });

      return {
        sessionToken: updated.token,
        userId: updated.userId,
        expires: updated.expiresAt,
      };
    },

    async deleteSession(sessionToken: string) {
      await prisma.session.delete({
        where: { token: sessionToken },
      });
    },

    async createVerificationToken(verificationToken: VerificationToken): Promise<VerificationToken | null | undefined> {
      const created = await prisma.verification.create({
        data: {
          identifier: verificationToken.identifier,
          value: verificationToken.token,
          expiresAt: verificationToken.expires,
        },
      });

      return {
        identifier: created.identifier,
        token: created.value,
        expires: created.expiresAt,
      };
    },

    async useVerificationToken({
      identifier,
      token,
    }: {
      identifier: string;
      token: string;
    }): Promise<VerificationToken | null> {
      const existing = await prisma.verification.findFirst({
        where: {
          identifier,
          value: token,
        },
      });

      if (!existing) return null;

      await prisma.verification.delete({
        where: { id: existing.id },
      });

      return {
        identifier: existing.identifier,
        token: existing.value,
        expires: existing.expiresAt,
      };
    },
  };
}
