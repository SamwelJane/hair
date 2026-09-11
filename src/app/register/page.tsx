"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";

export default function RegisterPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [pending, setPending] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPending(true);
    setError("");
    const form = new FormData(event.currentTarget);
    const response = await fetch("/api/auth/register", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(Object.fromEntries(form)) });
    if (!response.ok) {
      setError((await response.json()).error ?? "Unable to create your account.");
      setPending(false);
      return;
    }
    router.push("/login?registered=1");
  }

  return <main className="flex min-h-screen items-center justify-center bg-brand-bg px-6"><section className="w-full max-w-sm rounded-lg border border-brand-border bg-brand-surface p-8"><p className="text-center text-brand-accent">✦</p><h1 className="mt-2 text-center text-2xl font-semibold text-brand-ink">Create your Hiar account</h1>{error && <p className="mt-4 text-sm text-brand-danger">{error}</p>}<form onSubmit={submit} className="mt-6 flex flex-col gap-3"><input name="name" placeholder="Full name" required className="rounded border border-brand-border bg-brand-bg px-3 py-2 text-brand-ink" /><input name="email" type="email" placeholder="Email" required className="rounded border border-brand-border bg-brand-bg px-3 py-2 text-brand-ink" /><input name="phone" placeholder="WhatsApp phone (optional)" className="rounded border border-brand-border bg-brand-bg px-3 py-2 text-brand-ink" /><input name="password" type="password" minLength={8} placeholder="Password (8+ characters)" required className="rounded border border-brand-border bg-brand-bg px-3 py-2 text-brand-ink" /><button disabled={pending} className="rounded-full bg-brand-accent px-3 py-2 font-semibold text-white disabled:opacity-60">{pending ? "Creating account…" : "Create account"}</button></form><p className="mt-5 text-center text-sm text-brand-muted">Already registered? <Link className="text-brand-accent underline" href="/login">Sign in</Link></p></section></main>;
}
