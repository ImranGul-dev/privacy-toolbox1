import { Briefcase, Camera, Code2, FileUser, Landmark, UsersRound } from 'lucide-react';

const useCases = [
  { icon: Briefcase, title: 'Freelancers sharing client files', text: 'Clean files before handing off work.' },
  { icon: FileUser, title: 'Job seekers sharing resumes', text: 'Remove author and app details from documents.' },
  { icon: Camera, title: 'Photographers sharing images', text: 'Remove camera, date, and location metadata.' },
  { icon: Landmark, title: 'Businesses sharing PDFs', text: 'Scan PDFs before external distribution.' },
  { icon: Code2, title: 'Developers using API', text: 'Add metadata checks to your own product workflow.' },
  { icon: UsersRound, title: 'Teams handling documents', text: 'Use repeatable reports for shared files.' },
];

export function UseCaseGrid() {
  return (
    <section className="section-pad">
      <div className="site-container">
        <div className="mx-auto max-w-3xl text-center">
          <h2 className="heading-lg">Useful for everyday sharing</h2>
          <p className="lead mx-auto mt-3">For people and teams who need safer files without technical complexity.</p>
        </div>
        <div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {useCases.map((item) => (
            <div key={item.title} className="card p-6 transition hover:-translate-y-1 hover:shadow-lift">
              <span className="grid h-11 w-11 place-items-center rounded-2xl bg-blue-50 text-brand"><item.icon className="h-5 w-5" /></span>
              <h3 className="mt-5 font-bold text-ink">{item.title}</h3>
              <p className="mt-2 text-sm leading-6 text-subtle">{item.text}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
