import { NextResponse } from "next/server";
import bcrypt from "bcryptjs";
import { z } from "zod";
import { db } from "@/lib/db";
import { rateLimit } from "@/lib/security/rate-limit";

const schema = z.object({
  name: z.string().trim().min(2).max(80),
  email: z.string().trim().toLowerCase().email(),
  password: z.string().min(8).max(128),
  phone: z.string().trim().min(7).max(24).optional(),
});

export async function POST(request: Request) {
  const limit = await rateLimit(`register:${request.headers.get("x-forwarded-for") ?? "unknown"}`, 5, 60 * 60);
  if (!limit.allowed) return NextResponse.json({ error: "Too many registration attempts." }, { status: 429 });

  const parsed = schema.safeParse(await request.json());
  if (!parsed.success) return NextResponse.json({ error: "Please provide valid registration details." }, { status: 400 });

  const existing = await db.user.findUnique({ where: { email: parsed.data.email } });
  if (existing) return NextResponse.json({ error: "Unable to create this account." }, { status: 400 });

  const { password, ...userData } = parsed.data;
  const passwordHash = await bcrypt.hash(password, 12);
  await db.user.create({ data: { ...userData, passwordHash } });
  return NextResponse.json({ ok: true }, { status: 201 });
}
