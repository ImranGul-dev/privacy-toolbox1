"use client";

import Link from "next/link";
import { FormEvent, useMemo, useState } from "react";
import { AlertCircle, CheckCircle2, Eye, EyeOff, Loader2, ShieldCheck } from "lucide-react";
import { loginUser, oauthStartUrl, registerUser } from "@/lib/api/client";

function MicrosoftIcon(){return <span className="grid h-4 w-4 grid-cols-2 gap-0.5"><span className="bg-orange-500"/><span className="bg-emerald-500"/><span className="bg-blue-500"/><span className="bg-yellow-400"/></span>}
function GoogleIcon(){return <span className="text-sm font-black text-brand">G</span>}
function GithubIcon(){return <span className="text-sm font-black text-ink">GH</span>}

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

  const queryError = useMemo(() => { if (typeof window === 'undefined') return ''; return new URLSearchParams(window.location.search).get('error') || ''; }, []);

  async function submit(e: FormEvent) {
    e.preventDefault(); setError(""); setSuccess("");
    if (isRegister && password !== confirmPassword) { setError("Passwords do not match."); return; }
    setBusy(true);
    try {
      if (isRegister) {
        await registerUser({ name, email, password });
        setSuccess("Account created. Enter the verification code sent to your email.");
        window.setTimeout(() => { window.location.href = `/auth/verify?email=${encodeURIComponent(email)}`; }, 650);
      } else {
        const res = await loginUser({ email, password });
        setSuccess("Logged in successfully.");
        window.setTimeout(() => { window.location.href = res?.user?.role === "admin" ? "/dashboard" : "/tools"; }, 450);
      }
    } catch (err: any) { setError(err.message || "Authentication failed."); }
    finally { setBusy(false); }
  }

  return <div className="card mx-auto max-w-md p-6 sm:p-8 animate-soft-pop">
    <span className="grid h-12 w-12 place-items-center rounded-2xl bg-blue-50 text-brand"><ShieldCheck className="h-5 w-5" /></span>
    <h1 className="mt-5 text-3xl font-bold tracking-tight text-ink">{isRegister ? "Create your account" : "Welcome back"}</h1>
    <p className="mt-2 text-sm leading-6 text-subtle">{isRegister ? "Create an account to manage plan limits, reports, and future team or API access. Email verification is required before login." : "Log in to continue with your plan limits, saved settings, and account access."}</p>

    <div className="mt-6 grid gap-3">
      <a className="btn btn-secondary w-full" href={oauthStartUrl('google')}><GoogleIcon /> Continue with Google</a>
      <a className="btn btn-secondary w-full" href={oauthStartUrl('microsoft')}><MicrosoftIcon /> Continue with Microsoft</a>
      <a className="btn btn-secondary w-full" href={oauthStartUrl('github')}><GithubIcon /> Continue with GitHub</a>
    </div>
    <div className="my-6 flex items-center gap-3"><span className="h-px flex-1 bg-line"/><span className="text-xs font-bold uppercase tracking-[0.16em] text-soft">or use email</span><span className="h-px flex-1 bg-line"/></div>

    <form className="space-y-4" onSubmit={submit}>
      {isRegister && <label className="block text-sm font-semibold text-ink">Full name<input className="input mt-2" value={name} onChange={(e)=>setName(e.target.value)} type="text" placeholder="Your name" /></label>}
      <label className="block text-sm font-semibold text-ink">Email<input className="input mt-2" value={email} onChange={(e)=>setEmail(e.target.value)} type="email" placeholder="you@example.com" required /></label>
      <label className="block text-sm font-semibold text-ink">Password<div className="relative mt-2"><input className="input pr-12" value={password} onChange={(e)=>setPassword(e.target.value)} minLength={10} type={showPassword ? 'text' : 'password'} placeholder="Minimum 10 characters" required /><button type="button" onClick={()=>setShowPassword(v=>!v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-soft" aria-label="Show password">{showPassword ? <EyeOff className="h-4 w-4"/> : <Eye className="h-4 w-4"/>}</button></div></label>
      {isRegister && <label className="block text-sm font-semibold text-ink">Re-enter password<div className="relative mt-2"><input className="input pr-12" value={confirmPassword} onChange={(e)=>setConfirmPassword(e.target.value)} minLength={10} type={showConfirm ? 'text' : 'password'} placeholder="Confirm password" required /><button type="button" onClick={()=>setShowConfirm(v=>!v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-soft" aria-label="Show confirm password">{showConfirm ? <EyeOff className="h-4 w-4"/> : <Eye className="h-4 w-4"/>}</button></div></label>}
      {(error || queryError) && <div className="rounded-2xl border border-red-200 bg-red-50 p-3 text-sm font-semibold text-danger"><AlertCircle className="mr-2 inline h-4 w-4" />{error || queryError}</div>}
      {success && <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-3 text-sm font-semibold text-emerald-800"><CheckCircle2 className="mr-2 inline h-4 w-4" />{success}</div>}
      <button className="btn btn-primary w-full" type="submit" disabled={busy}>{busy && <Loader2 className="h-4 w-4 animate-spin" />}{isRegister ? "Create account" : "Login"}</button>
    </form>
    {!isRegister && <p className="mt-4 text-center text-sm"><Link className="font-bold text-brand" href="/auth/verify">Have a code? Verify your email</Link></p>}
    <p className="mt-5 text-center text-sm text-subtle">{isRegister ? "Already have an account?" : "No account?"} <Link className="font-bold text-brand" href={isRegister ? "/auth/login" : "/auth/register"}>{isRegister ? "Login" : "Create one"}</Link></p>
  </div>;
}
