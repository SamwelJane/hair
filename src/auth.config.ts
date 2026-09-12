import type { NextAuthConfig } from "next-auth";

// Edge-safe base config used directly by middleware.ts. It must not import
// anything that touches Node-only APIs (Prisma client, bcryptjs, pg) —
// those live in the Credentials provider defined in auth.ts instead, which
// is only ever used from route handlers / server components (Node runtime).
export const authConfig = {
  secret: process.env.AUTH_SECRET ?? process.env.NEXTAUTH_SECRET,
  pages: { signIn: "/login" },
  session: { strategy: "jwt" },
  providers: [],
  callbacks: {
    jwt: async ({ token, user }) => {
      if (user) {
        token.role = (user as { role: string }).role;
        token.id = user.id as string;
      }
      return token;
    },
    session: async ({ session, token }) => {
      if (session.user) {
        session.user.id = token.id as string;
        session.user.role = token.role as "ADMIN" | "STAFF" | "SUPPLIER" | "CUSTOMER";
      }
      return session;
    },
  },
} satisfies NextAuthConfig;
