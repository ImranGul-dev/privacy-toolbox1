import { Clock3, EyeOff, KeyRound, Lock, ServerCog, ShieldCheck, Trash2 } from 'lucide-react';

const sections = [
  { icon: ShieldCheck, title: 'Privacy-first processing', text: 'Files are processed for the selected job only. Reports are designed to summarize metadata findings without exposing original file content.' },
  { icon: Clock3, title: 'Automatic cleanup', text: 'Temporary uploads, generated outputs, and short-lived job files are scheduled for automatic deletion after the configured retention window.' },
  { icon: EyeOff, title: 'Safer logging approach', text: 'The platform is designed to log job status, timing, and safe error messages instead of raw file contents.' },
  { icon: KeyRound, title: 'Expiring downloads', text: 'Cleaned files use short-lived download tokens instead of permanent public file links.' },
  { icon: ServerCog, title: 'Worker-based processing', text: 'File processing runs in background workers so heavy jobs stay separate from the web interface.' },
  { icon: Trash2, title: 'Control before removal', text: 'Users can review detected data categories, select all, or choose specific items before starting a cleanup job.' },
];

const trustSteps = [
  'Scan first so users can see detected metadata categories before cleaning.',
  'Show clear progress and verification results directly under the upload area.',
  'Use short-lived files and auto-cleanup defaults to reduce long-term storage exposure.',
  'Keep account, billing, and API areas separated from the simple file tool flow.',
];

export const metadata = { title: 'Security', description: 'How Privacy Toolbox handles file privacy, deletion, verification, and trust.' };

export default function SecurityPage() {
  return (
    <main>
      <section className="py-12 sm:py-16 lg:py-20">
        <div className="site-container">
          <div className="mx-auto max-w-3xl text-center animate-fade-up">
            <span className="eyebrow"><Lock className="h-3.5 w-3.5" /> Security and trust</span>
            <h1 className="heading-xl mx-auto mt-5">Built to make private file sharing safer.</h1>
            <p className="lead mx-auto mt-5">Privacy Toolbox helps users scan, clean, verify, and download files through a transparent workflow with short-lived processing records.</p>
          </div>

          <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {sections.map((item, index) => (
              <div key={item.title} className="card p-6 animate-soft-pop" style={{ animationDelay: `${index * 55}ms` }}>
                <span className="grid h-12 w-12 place-items-center rounded-2xl bg-blue-50 text-brand"><item.icon className="h-5 w-5" /></span>
                <h2 className="mt-5 text-lg font-bold text-ink">{item.title}</h2>
                <p className="mt-2 text-sm leading-6 text-subtle">{item.text}</p>
              </div>
            ))}
          </div>

          <div className="mt-10 grid gap-5 lg:grid-cols-[.9fr_1.1fr] lg:items-start">
            <div className="card p-6">
              <span className="eyebrow">User trust workflow</span>
              <h2 className="heading-md mt-4">Clear steps before every download</h2>
              <p className="mt-3 text-sm leading-6 text-subtle">The product flow is designed to avoid confusion: upload, scan, review, remove selected data, verify, and then download.</p>
            </div>
            <div className="card p-6">
              <ul className="space-y-4">
                {trustSteps.map((step) => (
                  <li key={step} className="flex gap-3 text-sm leading-6 text-subtle">
                    <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-success" />
                    <span>{step}</span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
