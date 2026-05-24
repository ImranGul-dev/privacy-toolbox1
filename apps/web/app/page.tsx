import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { Hero } from '@/components/marketing/Hero';
import { FeaturedToolsGrid } from '@/components/marketing/FeaturedToolsGrid';
import { TrustStrip } from '@/components/trust/TrustStrip';
import { HowItWorks } from '@/components/marketing/HowItWorks';
import { UseCaseGrid } from '@/components/marketing/UseCaseGrid';
import { FAQAccordion } from '@/components/tool/FAQAccordion';

export default function Home() {
  return (
    <main>
      <Hero />
      <section className="section-pad bg-white/60">
        <div className="site-container">
          <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <span className="eyebrow">Popular tools</span>
              <h2 className="heading-lg mt-4">Choose a privacy tool</h2>
              <p className="lead mt-3">Find the right scanner, cleaner, or verifier for your file.</p>
            </div>
            <Link href="/tools" className="btn btn-secondary w-fit">View all tools <ArrowRight className="h-4 w-4" /></Link>
          </div>
          <FeaturedToolsGrid />
        </div>
      </section>
      <HowItWorks />
      <TrustStrip />
      <UseCaseGrid />
      <section className="section-pad">
        <div className="site-container">
          <div className="overflow-hidden rounded-3xl bg-gradient-to-br from-brand via-teal to-violet p-8 text-white shadow-lift sm:p-10 lg:p-12">
            <div className="grid gap-8 lg:grid-cols-[1fr_auto] lg:items-center">
              <div>
                <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">Need metadata cleaning in your own app?</h2>
                <p className="mt-3 max-w-2xl text-sm leading-6 text-white/80">
                  Developer/API plans are designed for batch jobs, machine-readable reports, team workflows, and future integrations.
                </p>
              </div>
              <div className="flex flex-col gap-3 sm:flex-row">
                <Link href="/api" className="btn bg-white text-brand hover:-translate-y-0.5">View API</Link>
                <Link href="/pricing" className="btn border border-white/30 bg-white/10 text-white hover:bg-white/20">See pricing</Link>
              </div>
            </div>
          </div>
        </div>
      </section>
      <section className="section-pad bg-slate-50/70">
        <div className="site-container">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="heading-lg">Frequently asked questions</h2>
            <p className="lead mx-auto mt-3">Honest answers about privacy, deletion, and verification.</p>
          </div>
          <div className="mt-10"><FAQAccordion /></div>
        </div>
      </section>
    </main>
  );
}
