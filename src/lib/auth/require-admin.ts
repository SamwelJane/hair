import { auth } from "@/auth";
import { isAdminRole } from "./rbac";

export async function requireAdminSession() {
  const session = await auth();
  if (!session?.user || !isAdminRole(session.user.role)) {
    throw new Error("Forbidden: admin/staff role required");
  }
  return session;
}
