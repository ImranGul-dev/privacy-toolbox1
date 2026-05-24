import Link from 'next/link';
import { ArrowRight, CheckCircle2 } from 'lucide-react';

const names: Record<string, string> = {
  'privacy-toolbox-vs-metadata2go': 'Metadata2Go',
  'privacy-toolbox-vs-jimpl': 'Jimpl',
  'privacy-toolbox-vs-smallpdf': 'Smallpdf',
  'privacy-toolbox-vs-ilovepdf': 'iLovePDF',
  'privacy-toolbox-vs-pdf24': 'PDF24',
};

export function generateStaticParams() { return Object.keys(names).map((slug) => ({ slug })); }

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const competitor = names[slug] || slug.replaceAll('-', ' ');
  return { title: `Privacy Toolbox vs ${competitor}`, description: `Compare Privacy Toolbox with ${competitor} for metadata scanning, cleaning, verification, and file privacy workflows.` };
}

export default async function Compare({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const competitor = names[slug] || slug.replaceAll('-', ' ');
  const rows = [
    ['Primary focus', 'File privacy before sharing', competitor],
    ['Workflow', 'Scan → clean → verify', 'Depends on tool'],
    ['File families', 'Images, PDFs, Office, media, ZIP scan, C2PA', 'Varies'],
    ['Verification', 'Built into cleaner workflow', 'Not always central'],
    ['Best fit', 'Users who want proof of what was found and what remains', 'General file or metadata tasks'],
  ];
  return <main><section className="section-pad"><div className="site-container"><div className="mx-auto max-w-5xl"><span className="eyebrow">Comparison</span><h1 className="heading-xl mt-5">Privacy Toolbox vs {competitor}</h1><p className="lead mt-5">This comparison explains how Privacy Toolbox focuses on privacy-first file sharing: scan hidden data, clean removable metadata where supported, and verify the output before downloading.</p><div className="card mt-8 overflow-hidden"><table className="w-full text-left text-sm"><tbody>{rows.map((row) => <tr key={row[0]} className="border-b border-line last:border-0"><th className="w-1/4 bg-slate-50 p-4 font-bold text-ink">{row[0]}</th><td className="p-4 text-subtle"><CheckCircle2 className="mr-2 inline h-4 w-4 text-teal" />{row[1]}</td><td className="p-4 text-subtle">{row[2]}</td></tr>)}</tbody></table></div><div className="mt-8 flex flex-col gap-3 sm:flex-row"><Link href="/tools" className="btn btn-primary">Explore privacy tools <ArrowRight className="h-4 w-4" /></Link><Link href="/security" className="btn btn-secondary">Read security details</Link></div></div></div></section></main>;
}
