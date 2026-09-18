// Mirrors src/lib/auth/rbac.ts from the old app, for client-side UI gating
// only (e.g. hiding nav links). The API's own role checks remain the actual
// authorization boundary — never trust this list for security decisions.
export const ADMIN_ROLES = ["ADMIN", "STAFF"] as const;
export const SUPPLIER_ROLES = ["SUPPLIER"] as const;
export const WAREHOUSE_ROLES = ["WAREHOUSE"] as const;
export const KENYA_OPS_ROLES = ["KENYA_OPS"] as const;

export type UserRole = "ADMIN" | "STAFF" | "SUPPLIER" | "CUSTOMER" | "WAREHOUSE" | "KENYA_OPS";

export function isAdminRole(role: UserRole): boolean {
  return (ADMIN_ROLES as readonly string[]).includes(role);
}

export function isStrictAdmin(role: UserRole): boolean {
  return role === "ADMIN";
}

export function isWarehouseRole(role: UserRole): boolean {
  return (WAREHOUSE_ROLES as readonly string[]).includes(role);
}

export function isKenyaOpsRole(role: UserRole): boolean {
  return (KENYA_OPS_ROLES as readonly string[]).includes(role);
}
