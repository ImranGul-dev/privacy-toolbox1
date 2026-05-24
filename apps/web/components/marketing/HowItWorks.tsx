import { CheckCircle2, Download, ScanSearch, UploadCloud } from 'lucide-react';

const steps = [
  { icon: UploadCloud, title: 'Upload', text: 'Choose a photo, PDF, or Office file from your device.' },
  { icon: ScanSearch, title: 'Scan', text: 'Review hidden metadata and privacy-risk categories.' },
  { icon: CheckCircle2, title: 'Select & clean', text: 'Select all detected data or choose specific items before removal.' },
  { icon: Download, title: 'Verify & download', text: 'The cleaned file is scanned again before you download it.' },
];

export function HowItWorks() {
  return (
    <section className="section-pad">
      <div className="site-container">
        <div className="mx-auto max-w-3xl text-center animate-fade-up">
          <h2 className="heading-lg">How it works</h2>
          <p className="lead mx-auto mt-3">A simple upload-first flow for non-technical users.</p>
        </div>
        <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
          {steps.map((step, idx) => (
            <div key={step.title} className="card relative p-6 animate-soft-pop" style={{ animationDelay: `${idx * 55}ms` }}>
              <span className="absolute right-5 top-5 text-5xl font-bold text-slate-100">0{idx + 1}</span>
              <span className="relative grid h-12 w-12 place-items-center rounded-2xl bg-blue-50 text-brand"><step.icon className="h-5 w-5" /></span>
              <h3 className="relative mt-6 text-lg font-bold text-ink">{step.title}</h3>
              <p className="relative mt-2 text-sm leading-6 text-subtle">{step.text}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
