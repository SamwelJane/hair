"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";

export default function ResetPasswordPage() {
  const params = useSearchParams();
  const router = useRouter();
  const [error, setError] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const password = new FormData(event.currentTarget).get("password");
    const response = await fetch("/api/auth/reset-password", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ token: params.get("token"), password }) });
    if (!response.ok) { setError((await response.json()).error ?? "Unable to reset password."); return; }
    router.push("/login?reset=1");
  }
  return <main className="flex min-h-screen items-center justify-center bg-brand-bg px-6"><section className="w-full max-w-sm rounded-lg border border-brand-border bg-brand-surface p-8"><h1 className="text-2xl font-semibold text-brand-ink">Choose a new password</h1>{error && <p className="mt-4 text-sm text-brand-danger">{error}</p>}<form onSubmit={submit} className="mt-6 flex flex-col gap-3"><input name="password" type="password" minLength={8} required placeholder="New password (8+ characters)" className="rounded border border-brand-border bg-brand-bg px-3 py-2 text-brand-ink" /><button className="rounded-full bg-brand-accent px-3 py-2 font-semibold text-white">Update password</button></form><Link href="/login" className="mt-5 block text-sm text-brand-accent underline">Back to sign in</Link></section></main>;
}
