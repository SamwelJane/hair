"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";

export default function ForgotPasswordPage() {
  const [sent, setSent] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const email = new FormData(event.currentTarget).get("email");
    await fetch("/api/auth/forgot-password", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email }) });
    setSent(true);
  }
  return <main className="flex min-h-screen items-center justify-center bg-brand-bg px-6"><section className="w-full max-w-sm rounded-lg border border-brand-border bg-brand-surface p-8"><h1 className="text-2xl font-semibold text-brand-ink">Reset your password</h1>{sent ? <p className="mt-4 text-sm text-brand-muted">If an account exists for that email, a reset link is on its way.</p> : <form onSubmit={submit} className="mt-6 flex flex-col gap-3"><input name="email" type="email" placeholder="Email" required className="rounded border border-brand-border bg-brand-bg px-3 py-2 text-brand-ink" /><button className="rounded-full bg-brand-accent px-3 py-2 font-semibold text-white">Email reset link</button></form>}<Link href="/login" className="mt-5 block text-sm text-brand-accent underline">Back to sign in</Link></section></main>;
}
