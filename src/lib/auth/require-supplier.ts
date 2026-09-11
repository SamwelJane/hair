import { auth } from "@/auth";
import { requireRole } from "./rbac";

export async function requireSupplierSession() {
  const session = await auth();
  if (!session?.user) throw new Error("Unauthorized");
  requireRole(session.user.role, ["SUPPLIER"]);
  return session;
}
