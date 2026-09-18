import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router";
import type { UserRole } from "@hiar-business/shared-types";
import { useAuth } from "../lib/auth/AuthContext";

// Client-side stand-in for the old app's src/middleware.ts server-side
// redirect. This is inherently weaker (a flash of redirect vs. a page that
// never renders) - the API enforces every real authorization decision
// itself regardless of what this component does.
export function RequireAuth({ children, roles }: { children: ReactNode; roles?: readonly UserRole[] }) {
  const { user, isAuthenticated, initializing } = useAuth();
  const location = useLocation();

  if (initializing) return null;
  if (!isAuthenticated) {
    const callbackUrl = encodeURIComponent(location.pathname + location.search);
    return <Navigate to={`/login?callbackUrl=${callbackUrl}`} replace />;
  }
  if (roles && (!user || !roles.includes(user.role as UserRole))) {
    return <Navigate to="/" replace />;
  }
  return <>{children}</>;
}
