"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { CheckCircle2, Loader2, ShieldCheck, Zap } from "lucide-react";
import { createCheckoutSession, getPublicConfig } from "@/lib/api/client";

const DEFAULT_PLANS = [
  { name: 'free', label: 'Free', price_monthly: 0, price_yearly: 0, currency: 'USD', cta: 'Start free', daily_scans: 5, daily_cleans: 3, monthly_files: 60, batch_files: 1, file_mb: { image: 25, pdf: 50, office: 50, zip: 50, audio: 50, video: 100, other: 25 } },
  { name: 'pro', label: 'Pro', price_monthly: 9, price_yearly: 84, currency: 'USD', cta: 'Upgrade to Pro', daily_scans: 100, daily_cleans: 100, monthly_files: 100, batch_files: 10, file_mb: { image: 100, pdf: 200, office: 200, zip: 250, audio: 250, video: 512, other: 100 } },
  { name: 'team', label: 'Team', price_monthly: 19, price_yearly: 180, currency: 'USD', cta: 'Create team workspace', daily_scans: 500, daily_cleans: 500, monthly_files: 500, batch_files: 50, file_mb: { image: 200, pdf: 500, office: 500, zip: 512, audio: 512, video: 512, other: 200 } },
  { name: 'business', label: 'Business/API', price_monthly: 49, price_yearly: 468, currency: 'USD', cta: 'Discuss API access', daily_scans: 2500, daily_cleans: 2500, monthly_files: 2000, batch_files: 100, file_mb: { image: 300, pdf: 512, office: 512, zip: 512, audio: 512, video: 512, other: 300 } },
];

const planText: Record<string, { label: string; bestFor: string; features: string[]; href: string }> = {
  free: { label: "Best for quick checks", bestFor: "Normal users and first-time privacy checks", href: "/tools", features: ["Single-file scan and clean", "Basic verification included", "No account required for core tools", "Temporary auto-delete window", "Standard processing queue"] },
  pro: { label: "Recommended", bestFor: "Freelancers, creators, job seekers, and regular users", href: "/auth/register", features: ["Higher file limits", "Batch workflows ready", "Downloadable audit reports", "Before/after metadata diff", "Advanced PDF cleanup"] },
  team: { label: "For teams", bestFor: "HR, legal, agencies, and businesses", href: "/auth/register", features: ["Team workspace ready", "Shared reports", "Higher monthly usage", "Business document workflows", "Custom retention settings ready"] },
  business: { label: "API and scale", bestFor: "Developers, SaaS products, and automation", href: "/contact", features: ["API access hooks", "Webhooks ready", "Dedicated queue option", "White-label reports ready", "Custom limits and security review"] },
};

function money(value: number, currency = "USD") {
  if (!value) return "$0";
  return new Intl.NumberFormat("en-US", { style: "currency", currency, maximumFractionDigits: 0 }).format(value);
}

function discounted(value: number, percent: number) {
  return Math.max(0, Math.round(value * (100 - percent) / 100));
}

function fileLimits(plan: any) {
  const mb = plan.file_mb || {};
  return [
    `Images ${mb.image || "—"} MB`,
    `PDF/Office ${mb.pdf || "—"}/${mb.office || "—"} MB`,
    `ZIP/Audio ${mb.zip || "—"}/${mb.audio || "—"} MB`,
    `Video ${mb.video >= 1024 ? `${Math.round(mb.video / 1024)} GB` : `${mb.video || "—"} MB`}`,
  ];
}

export function PricingPlans() {
  const [config, setConfig] = useState<any>(null);
  const [error, setError] = useState("");
  const [busyPlan, setBusyPlan] = useState("");

  useEffect(() => { getPublicConfig().then(setConfig).catch((e) => setError(e.message || "Could not load pricing.")); }, []);

  const plans = config?.plans || DEFAULT_PLANS;
  const promo = config?.promo;
  const billing = config?.billing || {};
  const percent = promo?.active ? Number(promo.percent || 0) : 0;

  async function startCheckout(planName: string) {
    setError("");
    setBusyPlan(planName);
    try {
      const session = await createCheckoutSession({ plan: planName, interval: 'monthly' });
      if (session?.url) window.location.href = session.url;
      else throw new Error("Stripe did not return a checkout URL.");
    } catch (err: any) {
      const message = err?.message || "Could not start checkout.";
      if (message.toLowerCase().includes("login required")) {
        window.location.href = `/auth/register?plan=${encodeURIComponent(planName)}`;
        return;
      }
      setError(message);
    } finally {
      setBusyPlan("");
    }
  }

  return (
    <section className="py-12 sm:py-16 lg:py-20">
      <div className="site-container">
        <div className="mx-auto max-w-3xl text-center">
          <span className="eyebrow"><ShieldCheck className="h-3.5 w-3.5" /> Pricing</span>
          <h1 className="heading-xl mx-auto mt-5">Start free. Upgrade when you need bigger files, batch cleanup, and proof reports.</h1>
          <p className="lead mx-auto mt-5">Single-file privacy tools stay accessible. Paid plans unlock scale, larger uploads, audit reports, team workflows, and API-ready automation.</p>
          {promo?.active && <div className="mx-auto mt-5 inline-flex rounded-full border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm font-bold text-emerald-800">{promo.display_text} {promo.coupon_code ? `Use ${promo.coupon_code}.` : ""}</div>}
          {error && <p className="mt-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-semibold text-danger">{error}</p>}
        </div>
        <div className="mt-12 grid gap-5 xl:grid-cols-4">
          {plans.map((plan: any) => {
            const copy = planText[plan.name] || planText.free;
            const price = Number(plan.price_monthly || 0);
            const display = percent && price ? money(discounted(price, percent), plan.currency || "USD") : money(price, plan.currency || "USD");
            const isPaid = plan.name !== 'free';
            const checkoutEnabled = Boolean(billing.checkout_enabled);
            return (
              <div key={plan.name} className={`card relative flex h-full flex-col p-6 ${plan.name === 'pro' ? 'ring-2 ring-brand' : ''}`}>
                <p className="text-sm font-bold text-brand">{copy.label}</p>
                <h2 className="mt-3 text-2xl font-bold text-ink">{plan.label}</h2>
                <p className="mt-2 text-sm leading-6 text-subtle">{copy.bestFor}</p>
                <div className="mt-4 flex items-end gap-2">
                  <p className="text-4xl font-bold tracking-tight text-ink">{display}</p>
                  <p className="pb-1 text-sm text-subtle">{price ? "/month" : "free"}</p>
                </div>
                {percent && price ? <p className="mt-1 text-sm text-soft line-through">Normally {money(price, plan.currency || "USD")}/month</p> : null}
                {!isPaid ? (
                  <Link className="btn btn-secondary mt-6 w-full" href={copy.href}>{plan.cta || copy.label}</Link>
                ) : checkoutEnabled ? (
                  <button className={plan.name === 'pro' ? 'btn btn-primary mt-6 w-full' : 'btn btn-secondary mt-6 w-full'} onClick={() => startCheckout(plan.name)} disabled={busyPlan === plan.name}>
                    {busyPlan === plan.name && <Loader2 className="h-4 w-4 animate-spin" />} {plan.cta || copy.label}
                  </button>
                ) : (
                  <Link className={plan.name === 'pro' ? 'btn btn-primary mt-6 w-full' : 'btn btn-secondary mt-6 w-full'} href={plan.name === 'business' ? '/contact' : `/auth/register?plan=${plan.name}`}>{plan.cta || copy.label}</Link>
                )}
                <div className="mt-6 rounded-2xl bg-slate-50 p-4">
                  <p className="text-xs font-bold uppercase tracking-[0.16em] text-soft">File limits</p>
                  <ul className="mt-3 space-y-2 text-sm text-subtle">
                    {fileLimits(plan).map((limit) => <li key={limit} className="flex gap-2"><Zap className="mt-0.5 h-4 w-4 shrink-0 text-brand" /> {limit}</li>)}
                  </ul>
                </div>
                <ul className="mt-6 grow space-y-3 text-sm text-subtle">
                  {copy.features.map((feature) => <li key={feature} className="flex gap-2"><CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" /> {feature}</li>)}
                  <li className="flex gap-2"><CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" /> {plan.daily_scans} scans/day · {plan.daily_cleans} cleans/day</li>
                  <li className="flex gap-2"><CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" /> {plan.monthly_files} files/month</li>
                </ul>
              </div>
            );
          })}
        </div>
        <div className="mx-auto mt-10 max-w-4xl rounded-3xl border border-line bg-white/80 p-6 text-sm leading-7 text-subtle shadow-card">
          <p><strong className="text-ink">Billing-ready setup:</strong> Plan limits are enforced by the backend now. Stripe Checkout, coupons, and subscription webhooks activate automatically when payment keys and price IDs are configured.</p>
          <p className="mt-3"><strong className="text-ink">Cost-safe launch limits:</strong> File-size defaults are tuned for a single low-cost AWS server. Increase them only after moving heavy jobs to larger workers or object storage.</p>
        </div>
      </div>
    </section>
  );
}
