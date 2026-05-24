"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import type { ComponentType } from "react";
import { AlertCircle, CheckCircle2, Eye, EyeOff, Loader2, ShieldCheck } from "lucide-react";
import { loginUser, oauthStartUrl, registerUser, getPublicConfig } from "@/lib/api/client";

type Provider = "google" | "microsoft" | "github";
type OAuthStatus = Record<Provider, boolean>;

function GoogleIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="h-5 w-5" focusable="false">
      <path fill="#4285F4" d="M23.49 12.27c0-.79-.07-1.54-.2-2.27H12v4.29h6.47a5.53 5.53 0 0 1-2.4 3.63v3.02h3.89c2.28-2.1 3.53-5.2 3.53-8.67Z" />
      <path fill="#34A853" d="M12 24c3.24 0 5.95-1.07 7.94-2.91l-3.89-3.02c-1.08.72-2.46 1.15-4.05 1.15-3.12 0-5.77-2.11-6.71-4.95H1.27v3.05A11.99 11.99 0 0 0 12 24Z" />
      <path fill="#FBBC05" d="M5.29 14.27A7.2 7.2 0 0 1 4.91 12c0-.79.14-1.56.38-2.27V6.68H1.27A11.93 11.93 0 0 0 0 12c0 1.92.46 3.73 1.27 5.32l4.02-3.05Z" />
      <path fill="#EA4335" d="M12 4.78c1.76 0 3.34.61 4.58 1.8l3.44-3.44A11.47 11.47 0 0 0 12 0 11.99 11.99 0 0 0 1.27 6.68l4.02 3.05C6.23 6.89 8.88 4.78 12 4.78Z" />
    </svg>
  );
}

function MicrosoftIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 23 23" className="h-5 w-5" focusable="false">
      <path fill="#f25022" d="M1 1h10v10H1z" />
      <path fill="#7fba00" d="M12 1h10v10H12z" />
      <path fill="#00a4ef" d="M1 12h10v10H1z" />
      <path fill="#ffb900" d="M12 12h10v10H12z" />
    </svg>
  );
}

function GithubIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 24 24" className="h-5 w-5 text-ink" fill="currentColor" focusable="false">
      <path fillRule="evenodd" clipRule="evenodd" d="M12 .5A11.5 11.5 0 0 0 8.36 22.9c.58.11.79-.25.79-.56v-2.15c-3.2.7-3.88-1.36-3.88-1.36-.53-1.34-1.29-1.7-1.29-1.7-1.05-.72.08-.7.08-.7 1.16.08 1.78 1.2 1.78 1.2 1.04 1.77 2.72 1.26 3.38.96.11-.75.41-1.26.74-1.55-2.56-.29-5.26-1.28-5.26-5.7 0-1.26.45-2.3 1.19-3.1-.12-.3-.52-1.47.11-3.07 0 0 .97-.31 3.18 1.18A11.1 11.1 0 0 1 12 5.96c.98 0 1.96.13 2.88.39 2.2-1.49 3.17-1.18 3.17-1.18.63 1.6.24 2.78.12 3.07.74.8 1.18 1.84 1.18 3.1 0 4.43-2.7 5.4-5.27 5.69.42.36.8 1.08.8 2.18v3.13c0 .31.2.67.8.56A11.5 11.5 0 0 0 12 .5Z" />
    </svg>
  );
}

const providerMeta: Record<Provider, { label: string; Icon: ComponentType }> = {
  google: { label: "Google", Icon: GoogleIcon },
  microsoft: { label: "Microsoft", Icon: MicrosoftIcon },
  github: { label: "GitHub", Icon: GithubIcon },
};

function OAuthButton({ provider, enabled }: { provider: Provider; enabled?: boolean }) {
  const { label, Icon } = providerMeta[provider];
  const className = "btn btn-secondary w-full justify-center gap-3 border-slate-200 bg-white text-ink shadow-sm hover:border-blue-200 hover:bg-blue-50";
  if (enabled === false) {
    return (
      <button type="button" className={`${className} cursor-not-allowed opacity-60`} disabled title={`${label} OAuth is not configured yet.`}>
        <Icon /> Continue with {label}
      </button>
    );
  }
  return (
    <a className={className} href={oauthStartUrl(provider)} aria-label={`Continue with ${label}`}>
      <Icon /> Continue with {label}
    </a>
  );
}

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const isRegister = mode === "register";
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [queryError, setQueryError] = useState("");
  const [oauthStatus, setOauthStatus] = useState<OAuthStatus | undefined>();

  useEffect(() => {
    setQueryError(new URLSearchParams(window.location.search).get("error") || "");
    getPublicConfig()
      .then((cfg) => setOauthStatus(cfg?.auth?.oauth_providers || undefined))
      .catch(() => setOauthStatus(undefined));
  }, []);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setError("");
    setSuccess("");
    if (isRegister && password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    setBusy(true);
    try {
      if (isRegister) {
        await registerUser({ name, email, password });
        setSuccess("Account created. Enter the verification code sent to your email.");
        window.setTimeout(() => {
          window.location.href = `/auth/verify?email=${encodeURIComponent(email)}`;
        }, 650);
      } else {
        const res = await loginUser({ email, password });
        setSuccess("Logged in successfully.");
        window.setTimeout(() => {
          window.location.href = res?.user?.role === "admin" ? "/dashboard" : "/tools";
        }, 450);
      }
    } catch (err: any) {
      setError(err.message || "Authentication failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card mx-auto max-w-md p-6 sm:p-8 animate-soft-pop">
      <span className="grid h-12 w-12 place-items-center rounded-2xl bg-blue-50 text-brand"><ShieldCheck className="h-5 w-5" /></span>
      <h1 className="mt-5 text-3xl font-bold tracking-tight text-ink">{isRegister ? "Create your account" : "Welcome back"}</h1>
      <p className="mt-2 text-sm leading-6 text-subtle">
        {isRegister ? "Create an account to manage plan limits, reports, and future team or API access. Email verification is required before login." : "Log in to continue with your plan limits, saved settings, and account access."}
      </p>

      <div className="mt-6 grid gap-3">
        <OAuthButton provider="google" enabled={oauthStatus?.google} />
        <OAuthButton provider="microsoft" enabled={oauthStatus?.microsoft} />
        <OAuthButton provider="github" enabled={oauthStatus?.github} />
      </div>
      <div className="my-6 flex items-center gap-3"><span className="h-px flex-1 bg-line"/><span className="text-xs font-bold uppercase tracking-[0.16em] text-soft">or use email</span><span className="h-px flex-1 bg-line"/></div>

      <form className="space-y-4" onSubmit={submit}>
        {isRegister && <label className="block text-sm font-semibold text-ink">Full name<input className="input mt-2" value={name} onChange={(e)=>setName(e.target.value)} type="text" placeholder="Your name" /></label>}
        <label className="block text-sm font-semibold text-ink">Email<input className="input mt-2" value={email} onChange={(e)=>setEmail(e.target.value)} type="email" placeholder="you@example.com" autoComplete="email" required /></label>
        <label className="block text-sm font-semibold text-ink">Password<div className="relative mt-2"><input className="input pr-12" value={password} onChange={(e)=>setPassword(e.target.value)} minLength={10} type={showPassword ? "text" : "password"} placeholder="Minimum 10 characters" autoComplete={isRegister ? "new-password" : "current-password"} required /><button type="button" onClick={()=>setShowPassword(v=>!v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-soft" aria-label={showPassword ? "Hide password" : "Show password"}>{showPassword ? <EyeOff className="h-4 w-4"/> : <Eye className="h-4 w-4"/>}</button></div></label>
        {isRegister && <label className="block text-sm font-semibold text-ink">Re-enter password<div className="relative mt-2"><input className="input pr-12" value={confirmPassword} onChange={(e)=>setConfirmPassword(e.target.value)} minLength={10} type={showConfirm ? "text" : "password"} placeholder="Confirm password" autoComplete="new-password" required /><button type="button" onClick={()=>setShowConfirm(v=>!v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-soft" aria-label={showConfirm ? "Hide confirm password" : "Show confirm password"}>{showConfirm ? <EyeOff className="h-4 w-4"/> : <Eye className="h-4 w-4"/>}</button></div></label>}
        {(error || queryError) && <div className="rounded-2xl border border-red-200 bg-red-50 p-3 text-sm font-semibold text-danger"><AlertCircle className="mr-2 inline h-4 w-4" />{error || queryError}</div>}
        {success && <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-3 text-sm font-semibold text-emerald-800"><CheckCircle2 className="mr-2 inline h-4 w-4" />{success}</div>}
        <button className="btn btn-primary w-full" type="submit" disabled={busy}>{busy && <Loader2 className="h-4 w-4 animate-spin" />}{isRegister ? "Create account" : "Login"}</button>
      </form>
      {!isRegister && <p className="mt-4 text-center text-sm"><Link className="font-bold text-brand" href="/auth/verify">Have a code? Verify your email</Link></p>}
      <p className="mt-5 text-center text-sm text-subtle">{isRegister ? "Already have an account?" : "No account?"} <Link className="font-bold text-brand" href={isRegister ? "/auth/login" : "/auth/register"}>{isRegister ? "Login" : "Create one"}</Link></p>
    </div>
  );
}
