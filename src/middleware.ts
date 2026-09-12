import NextAuth from "next-auth";
import { NextResponse } from "next/server";
import { authConfig } from "./auth.config";

const ADMIN_ROLES = ["ADMIN", "STAFF"];
const SUPPLIER_ROLES = ["SUPPLIER"];

const { auth } = NextAuth(authConfig);

export default auth((req) => {
  const { pathname } = req.nextUrl;
  const role = req.auth?.user?.role;

  if (pathname.startsWith("/admin")) {
    if (!req.auth) {
      return NextResponse.redirect(new URL(`/login?callbackUrl=${pathname}`, req.url));
    }
    if (!role || !ADMIN_ROLES.includes(role)) {
      return NextResponse.redirect(new URL("/", req.url));
    }
  }

  if (pathname.startsWith("/supplier")) {
    if (!req.auth) {
      return NextResponse.redirect(new URL(`/login?callbackUrl=${pathname}`, req.url));
    }
    if (!role || !SUPPLIER_ROLES.includes(role)) {
      return NextResponse.redirect(new URL("/", req.url));
    }
  }

  if (pathname.startsWith("/account") || pathname.startsWith("/checkout")) {
    if (!req.auth) {
      return NextResponse.redirect(new URL(`/login?callbackUrl=${pathname}`, req.url));
    }
  }

  return NextResponse.next();
});

export const config = {
  matcher: ["/admin/:path*", "/supplier/:path*", "/account/:path*", "/checkout/:path*"],
};
