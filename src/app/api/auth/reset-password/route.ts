import { NextResponse } from "next/server";
import { createHash } from "node:crypto";
import bcrypt from "bcryptjs";
import { z } from "zod";
import { db } from "@/lib/db";

const schema = z.object({ token: z.string().length(64), password: z.string().min(8).max(128) });

export async function POST(request: Request) {
  const parsed = schema.safeParse(await request.json());
  if (!parsed.success) return NextResponse.json({ error: "Invalid reset request." }, { status: 400 });
  const tokenHash = createHash("sha256").update(parsed.data.token).digest("hex");
  const reset = await db.passwordResetToken.findUnique({ where: { tokenHash } });
  if (!reset || reset.usedAt || reset.expiresAt < new Date()) {
    return NextResponse.json({ error: "This reset link is invalid or expired." }, { status: 400 });
  }

  const passwordHash = await bcrypt.hash(parsed.data.password, 12);
  await db.$transaction([
    db.user.update({ where: { id: reset.userId }, data: { passwordHash } }),
    db.passwordResetToken.update({ where: { id: reset.id }, data: { usedAt: new Date() } }),
    db.passwordResetToken.deleteMany({ where: { userId: reset.userId, id: { not: reset.id } } }),
  ]);
  return NextResponse.json({ ok: true });
}
