import type { UserRole } from "@/generated/prisma/client";

export const ADMIN_ROLES: UserRole[] = ["ADMIN", "STAFF"];

export function isAdminRole(role: UserRole | undefined | null): boolean {
  return !!role && ADMIN_ROLES.includes(role);
}

export function requireRole(role: UserRole | undefined | null, allowed: UserRole[]): void {
  if (!role || !allowed.includes(role)) {
    throw new Error("Forbidden: insufficient role");
  }
}
