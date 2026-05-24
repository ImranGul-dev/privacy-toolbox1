import { notFound } from 'next/navigation';

const terms: Record<string, { title: string; definition: string; details: string[] }> = {
  exif: { title: 'EXIF metadata', definition: 'EXIF metadata is camera and capture information stored inside many image files.', details: ['It can include camera make, model, lens, timestamps, image settings, and sometimes GPS coordinates.', 'Removing EXIF can reduce privacy risk before posting or sending photos.'] },
  xmp: { title: 'XMP metadata', definition: 'XMP is an extensible metadata format used by images, PDFs, and creative software.', details: ['It can store title, creator, description, keywords, software, dates, and workflow information.', 'XMP can appear even when basic EXIF fields are removed.'] },
  iptc: { title: 'IPTC metadata', definition: 'IPTC metadata is often used by photographers, newsrooms, and media libraries to store captions, credits, and keywords.', details: ['It can expose author, copyright, location, source, and editorial notes.', 'Image privacy tools should scan IPTC separately from EXIF.'] },
  'gps-metadata': { title: 'GPS metadata', definition: 'GPS metadata is location information embedded in a file, often in photos or videos.', details: ['It can include latitude, longitude, altitude, direction, and timestamps.', 'Removing GPS metadata does not remove visible landmarks inside an image.'] },
  'pdf-metadata': { title: 'PDF metadata', definition: 'PDF metadata is hidden or semi-hidden information stored in PDF document properties, XMP packets, annotations, attachments, forms, or actions.', details: ['It can reveal author names, software, dates, comments, embedded files, or JavaScript indicators.', 'A good PDF privacy workflow scans, cleans, and verifies the output.'] },
  'document-inspector': { title: 'Document Inspector', definition: 'Document Inspector is the name many users associate with checking Office files for hidden data before sharing.', details: ['Office files can contain comments, tracked changes, custom properties, hidden sheets, notes, and external links.', 'Privacy Toolbox mirrors this idea with web-based scan and clean workflows for modern Office files.'] },
  'tracked-changes': { title: 'Tracked changes', definition: 'Tracked changes are edits and revision data stored in documents, especially Word files.', details: ['They may reveal deleted text, reviewers, edit history, or internal discussion.', 'Before sharing externally, tracked changes should be accepted, removed, or inspected.'] },
  'content-credentials': { title: 'Content Credentials', definition: 'Content Credentials are provenance metadata used to describe how a file was created or edited when a C2PA manifest is present.', details: ['They can be useful for transparency, but they may also reveal tool and workflow information.', 'Absence of Content Credentials does not prove that a file is human-made.'] },
  c2pa: { title: 'C2PA', definition: 'C2PA is a standard for content provenance metadata and manifests.', details: ['C2PA manifests can be inspected with c2patool.', 'A C2PA result should be treated as provenance information, not a full authenticity guarantee.'] },
  'file-sanitization': { title: 'File sanitization', definition: 'File sanitization is the process of removing hidden data, active content, comments, or metadata before sharing a file.', details: ['Sanitization can be simple for metadata and more complex for PDFs, Office files, and archives.', 'Verification after cleanup is important because some technical data may remain.'] },
  'metadata-verification': { title: 'Metadata verification', definition: 'Metadata verification means re-scanning a cleaned file to check whether removable private metadata is still detected.', details: ['Verification helps separate successful cleanup from false confidence.', 'Technical compatibility data may remain without being a privacy failure.'] },
};

export function generateStaticParams() { return Object.keys(terms).map((slug) => ({ slug })); }

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const term = terms[slug];
  if (!term) return {};
  return { title: `${term.title} explained`, description: term.definition, alternates: { canonical: `/glossary/${slug}` } };
}

export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const term = terms[slug];
  if (!term) notFound();
  return <main><section className="section-pad"><div className="site-container"><article className="card mx-auto max-w-4xl p-8 sm:p-10"><span className="eyebrow">Glossary</span><h1 className="heading-lg mt-4">{term.title}</h1><p className="lead mt-4">{term.definition}</p><div className="mt-8 space-y-4 text-base leading-8 text-subtle">{term.details.map((d) => <p key={d}>{d}</p>)}</div><div className="mt-8 rounded-2xl bg-blue-50 p-5 text-sm leading-6 text-brand">Privacy Toolbox uses glossary pages like this to explain file privacy terms in clear language and link them to practical scan, clean, and verification tools.</div></article></div></section></main>;
}
