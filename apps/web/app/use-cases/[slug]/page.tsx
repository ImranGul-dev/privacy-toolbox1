import Link from 'next/link';
import { notFound } from 'next/navigation';
import { ArrowRight, ShieldCheck } from 'lucide-react';

const useCases: Record<string, { title: string; audience: string; problem: string; tools: { href: string; label: string }[]; checklist: string[] }> = {
  'resume-metadata-cleaner': {
    title: 'Resume Metadata Cleaner', audience: 'Job seekers, recruiters, and career coaches',
    problem: 'Resumes can expose author names, old company information, comments, tracked changes, PDF creator tools, or timestamps before you send them to employers.',
    tools: [{ href: '/tools/remove-docx-metadata', label: 'Clean Office resume' }, { href: '/tools/remove-pdf-metadata', label: 'Clean PDF resume' }, { href: '/tools/verify-file-metadata', label: 'Verify cleaned resume' }],
    checklist: ['Scan the original DOCX or PDF before sending.', 'Remove document properties, comments, and tracked changes where detected.', 'Export a clean PDF copy when practical.', 'Verify the final file before uploading to job portals.'],
  },
  'legal-document-metadata-cleaner': {
    title: 'Legal Document Metadata Cleaner', audience: 'Legal teams, consultants, and compliance users',
    problem: 'Legal files may contain authors, revision history, comments, attachments, redaction mistakes, and hidden PDF data that should be checked before external sharing.',
    tools: [{ href: '/tools/remove-pdf-hidden-data', label: 'Remove PDF hidden data' }, { href: '/tools/pdf-redaction-checker', label: 'Check redactions' }, { href: '/tools/docx-hidden-data-scanner', label: 'Scan DOCX hidden data' }],
    checklist: ['Scan documents before client or court sharing.', 'Check for comments, attachments, forms, and redaction risk.', 'Use aggressive cleanup only when you understand it may change interactive PDF behavior.', 'Verify the cleaned file and keep a copy of the report.'],
  },
  'business-proposal-metadata-cleaner': {
    title: 'Business Proposal Metadata Cleaner', audience: 'Agencies, freelancers, sales teams, and founders',
    problem: 'Proposals can leak template history, previous client names, author fields, speaker notes, hidden slides, or internal comments.',
    tools: [{ href: '/tools/remove-docx-metadata', label: 'Clean Office proposal' }, { href: '/tools/pptx-remove-notes-hidden-slides', label: 'Clean presentation notes' }, { href: '/tools/remove-pdf-metadata', label: 'Clean proposal PDF' }],
    checklist: ['Scan the proposal in its source format.', 'Remove comments, notes, hidden slides, and document properties.', 'Export a final PDF and scan again.', 'Share the verified copy, not the editable draft.'],
  },
  'social-media-image-privacy-checker': {
    title: 'Social Media Image Privacy Checker', audience: 'Creators, photographers, and everyday users',
    problem: 'Images can contain GPS data, camera details, editing software, timestamps, author tags, and AI provenance metadata before posting.',
    tools: [{ href: '/tools/remove-image-metadata', label: 'Remove image metadata' }, { href: '/tools/remove-gps-from-photo', label: 'Remove GPS from photo' }, { href: '/tools/detect-content-credentials', label: 'Check Content Credentials' }],
    checklist: ['Scan the image before posting.', 'Remove GPS/location fields if present.', 'Review camera, software, and author metadata.', 'Check whether AI provenance metadata is present.'],
  },
  'safe-file-sharing-for-hr': {
    title: 'Safe File Sharing for HR', audience: 'HR teams, recruiters, and operations teams',
    problem: 'HR files often move between applicants, managers, vendors, and job boards, increasing the chance of hidden comments, tracked changes, or author data leaking.',
    tools: [{ href: '/tools/docx-hidden-data-scanner', label: 'Scan Word documents' }, { href: '/tools/remove-pdf-metadata', label: 'Clean PDF files' }, { href: '/tools/zip-privacy-scanner', label: 'Scan ZIP packages' }],
    checklist: ['Scan resumes and evaluation documents.', 'Remove hidden document properties and comments.', 'Avoid sharing editable source files when a verified PDF is enough.', 'Scan ZIP packages before forwarding.'],
  },
  'safe-file-sharing-for-journalists': {
    title: 'Safe File Sharing for Journalists', audience: 'Journalists, editors, researchers, and publishers',
    problem: 'Files can expose location, device, software, author, provenance, and document history before publication or source review.',
    tools: [{ href: '/tools/remove-image-metadata', label: 'Clean images' }, { href: '/tools/remove-video-metadata', label: 'Clean videos' }, { href: '/tools/pdf-redaction-checker', label: 'Check PDF redactions' }],
    checklist: ['Remove GPS from photos and videos before publishing.', 'Check PDFs for hidden text, annotations, and attachments.', 'Use C2PA/provenance checks as an informational signal, not a final authenticity verdict.', 'Verify files after cleanup.'],
  },
};

export function generateStaticParams() { return Object.keys(useCases).map((slug) => ({ slug })); }

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const item = useCases[slug];
  if (!item) return {};
  return { title: item.title, description: item.problem, alternates: { canonical: `/use-cases/${slug}` } };
}

export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const item = useCases[slug];
  if (!item) notFound();
  return <main><section className="section-pad"><div className="site-container"><div className="mx-auto max-w-5xl"><span className="eyebrow"><ShieldCheck className="h-3.5 w-3.5" /> Use case</span><h1 className="heading-xl mt-5">{item.title}</h1><p className="lead mt-5">{item.problem}</p><p className="mt-3 text-sm font-semibold text-subtle">Best for: {item.audience}</p><div className="mt-8 grid gap-5 lg:grid-cols-[1fr_.8fr]"><div className="card p-6"><h2 className="text-2xl font-bold text-ink">Recommended workflow</h2><ol className="mt-5 space-y-3 text-sm leading-6 text-subtle">{item.checklist.map((step, i) => <li key={step} className="flex gap-3"><span className="grid h-6 w-6 shrink-0 place-items-center rounded-full bg-blue-50 text-xs font-bold text-brand">{i+1}</span><span>{step}</span></li>)}</ol></div><div className="card p-6"><h2 className="text-2xl font-bold text-ink">Start with these tools</h2><div className="mt-5 space-y-3">{item.tools.map((tool) => <Link key={tool.href} href={tool.href} className="flex items-center justify-between rounded-2xl border border-line bg-slate-50 p-4 text-sm font-bold text-ink hover:bg-white hover:shadow-card">{tool.label}<ArrowRight className="h-4 w-4 text-brand" /></Link>)}</div></div></div></div></div></section></main>;
}
