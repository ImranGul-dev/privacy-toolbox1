import { CheckCircle2, FileSearch, ShieldCheck, Sparkles } from 'lucide-react';

const values = [
  { icon: FileSearch, title: 'Clear scanning', text: 'We help users understand hidden metadata before files are shared externally.' },
  { icon: Sparkles, title: 'Simple cleanup', text: 'The interface keeps technical file privacy tasks easy for non-technical users.' },
  { icon: ShieldCheck, title: 'Verification first', text: 'After cleanup, users can review a verification report and download the cleaned file.' },
];

export const metadata = { title: 'About us', description: 'About Privacy Toolbox and the mission behind safer file sharing.' };

export default function AboutPage() {
  return (
    <main>
      <section className="py-12 sm:py-16 lg:py-20">
        <div className="site-container">
          <div className="mx-auto max-w-3xl text-center animate-fade-up">
            <span className="eyebrow"><ShieldCheck className="h-3.5 w-3.5" /> About us</span>
            <h1 className="heading-xl mx-auto mt-5">Helping people share cleaner, safer files.</h1>
            <p className="lead mx-auto mt-5">Privacy Toolbox is a file utility platform focused on scanning, cleaning, and verifying hidden metadata before files are shared with clients, teams, employers, or the public.</p>
          </div>

          <div className="mt-12 grid gap-5 md:grid-cols-3">
            {values.map((item, index) => (
              <div key={item.title} className="card p-6 animate-soft-pop" style={{ animationDelay: `${index * 60}ms` }}>
                <span className="grid h-12 w-12 place-items-center rounded-2xl bg-blue-50 text-brand"><item.icon className="h-5 w-5" /></span>
                <h2 className="mt-5 text-lg font-bold text-ink">{item.title}</h2>
                <p className="mt-2 text-sm leading-6 text-subtle">{item.text}</p>
              </div>
            ))}
          </div>

          <div className="mt-10 grid gap-5 lg:grid-cols-[1fr_1fr]">
            <div className="card p-6 sm:p-8">
              <h2 className="heading-md">Our mission</h2>
              <p className="mt-4 text-sm leading-7 text-subtle">We are building a modern privacy toolkit for everyday file sharing. The goal is to make hidden metadata visible, give users control before removal, and provide a verification-focused workflow that feels simple and professional.</p>
            </div>
            <div className="card p-6 sm:p-8">
              <h2 className="heading-md">What we care about</h2>
              <ul className="mt-4 space-y-3 text-sm leading-6 text-subtle">
                {['Simple tools for images, PDFs, and Office files.', 'Short-lived file processing and clear deletion messaging.', 'Professional reports that users can understand quickly.', 'A clean SaaS experience that works well on mobile and desktop.'].map((item) => (
                  <li key={item} className="flex gap-3"><CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0 text-success" /> {item}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
