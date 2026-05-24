import { Clock3, EyeOff, FileCheck2, Link2Off, ListChecks, ShieldCheck } from 'lucide-react';

const trustItems = [
  { icon: Clock3, title: 'Temporary files auto-delete', text: 'Uploads and outputs are tied to short-lived jobs.' },
  { icon: EyeOff, title: 'No raw file-content logs', text: 'Reports avoid storing original file contents by default.' },
  { icon: FileCheck2, title: 'Verification scan included', text: 'Cleaned files are re-scanned before download.' },
  { icon: ShieldCheck, title: 'Clear results shown', text: 'Users can review scan results before removing selected data.' },
  { icon: Link2Off, title: 'Short-lived download links', text: 'Downloads use expiring signed tokens.' },
  { icon: ListChecks, title: 'Privacy-first reports', text: 'Findings are summarized in clear categories.' },
];

export function TrustStrip() {
  return (
    <section className="section-pad bg-slate-50/70">
      <div className="site-container">
        <div className="mx-auto max-w-3xl text-center animate-fade-up">
          <span className="eyebrow">Trust and security</span>
          <h2 className="heading-lg mt-4">Designed for file privacy workflows</h2>
          <p className="lead mx-auto mt-4">
            We show what was detected, what can be selected for removal, and what verification reports after cleanup.
          </p>
        </div>
        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {trustItems.map((item, index) => (
            <div key={item.title} className="card p-5 transition hover:-translate-y-1 hover:shadow-lift animate-soft-pop" style={{ animationDelay: `${index * 50}ms` }}>
              <span className="grid h-11 w-11 place-items-center rounded-2xl bg-teal/10 text-teal"><item.icon className="h-5 w-5" /></span>
              <h3 className="mt-4 font-bold text-ink">{item.title}</h3>
              <p className="mt-2 text-sm leading-6 text-subtle">{item.text}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
