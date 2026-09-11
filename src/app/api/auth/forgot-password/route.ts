import { NextResponse } from "next/server";
import { createHash, randomBytes } from "node:crypto";
import { z } from "zod";
import { db } from "@/lib/db";
import { sendEmail } from "@/lib/notifications/email";

const schema = z.object({ email: z.string().trim().toLowerCase().email() });

export async function POST(request: Request) {
  const parsed = schema.safeParse(await request.json());
  if (!parsed.success) return NextResponse.json({ ok: true });

  const user = await db.user.findUnique({ where: { email: parsed.data.email } });
  if (user) {
    const token = randomBytes(32).toString("hex");
    const tokenHash = createHash("sha256").update(token).digest("hex");
    await db.passwordResetToken.deleteMany({ where: { userId: user.id, usedAt: null } });
    await db.passwordResetToken.create({
      data: { userId: user.id, tokenHash, expiresAt: new Date(Date.now() + 30 * 60 * 1000) },
    });
    const origin = process.env.NEXTAUTH_URL ?? `https://${process.env.VERCEL_URL ?? "localhost:3000"}`;
    await sendEmail({
      to: user.email,
      subject: "Reset your Hiar Business password",
      html: `<p>Hello ${user.name},</p><p>Use this link to reset your password. It expires in 30 minutes.</p><p><a href="${origin}/reset-password?token=${token}">Reset password</a></p><p>If you did not request this, you can ignore this email.</p>`,
    });
  }

  return NextResponse.json({ ok: true });
}
