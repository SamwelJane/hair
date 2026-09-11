import { signIn } from "@/auth";
import { AuthError } from "next-auth";
import { redirect } from "next/navigation";

async function authenticate(formData: FormData) {
  "use server";

  const email = formData.get("email") as string;
  const password = formData.get("password") as string;
  const callbackUrl = (formData.get("callbackUrl") as string) || "/";

  try {
    await signIn("credentials", { email, password, redirectTo: callbackUrl });
  } catch (error) {
    if (error instanceof AuthError) {
      const code = (error as AuthError & { code?: string }).code === "rate_limited" ? "rate_limited" : "invalid";
      redirect(`/login?error=${code}&callbackUrl=${encodeURIComponent(callbackUrl)}`);
    }
    throw error;
  }
}

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string; callbackUrl?: string }>;
}) {
  const { error, callbackUrl } = await searchParams;

  return (
    <div className="flex min-h-screen items-center justify-center bg-brand-bg px-6">
      <div className="w-full max-w-sm rounded-lg border border-brand-border bg-brand-surface p-8">
        <p className="text-center text-brand-accent">✦</p>
        <h1 className="mt-2 text-center text-2xl font-semibold text-brand-ink">Sign in to Hiar Business</h1>
        {error === "rate_limited" && (
          <p className="mt-4 text-sm text-brand-danger">Too many login attempts. Please wait a few minutes and try again.</p>
        )}
        {error === "invalid" && <p className="mt-4 text-sm text-brand-danger">Invalid email or password.</p>}
        <form action={authenticate} className="mt-6 flex flex-col gap-3">
          <input type="hidden" name="callbackUrl" value={callbackUrl ?? "/"} />
          <input
            type="email"
            name="email"
            placeholder="Email"
            required
            className="rounded border border-brand-border bg-brand-bg px-3 py-2 text-brand-ink"
          />
          <input
            type="password"
            name="password"
            placeholder="Password"
            required
            className="rounded border border-brand-border bg-brand-bg px-3 py-2 text-brand-ink"
          />
          <button type="submit" className="rounded-full bg-brand-accent px-3 py-2 font-semibold text-white hover:bg-brand-accent-hover">
            Sign in
          </button>
        </form>
      </div>
    </div>
  );
}
