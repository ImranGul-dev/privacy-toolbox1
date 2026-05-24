import { FeaturedToolsGrid } from '@/components/marketing/FeaturedToolsGrid';
import { ShieldCheck } from 'lucide-react';

export const metadata = { title: 'All Privacy Tools', description: 'Scan, clean, and verify hidden metadata in photos, PDFs, Office files, videos, audio, and ZIP archives.' };

export default function ToolsPage() {
  return (
    <main>
      <section className="py-12 sm:py-16 lg:py-20">
        <div className="site-container">
          <div className="mx-auto max-w-3xl text-center">
            <span className="eyebrow"><ShieldCheck className="h-3.5 w-3.5" /> All privacy tools</span>
            <h1 className="heading-xl mx-auto mt-5">Scan, clean, and verify hidden metadata.</h1>
            <p className="lead mx-auto mt-5">Choose a tool for photos, PDFs, Office files, videos, audio, ZIP archives, AI provenance, or post-cleaning verification.</p>
          </div>
          <div className="mt-12"><FeaturedToolsGrid compact /></div>
          <div className="card mt-8 p-6 text-center">
            <h2 className="text-xl font-bold text-ink">Not sure which tool to use?</h2>
            <p className="mx-auto mt-2 max-w-2xl text-sm leading-6 text-subtle">Use PDF tools for documents, image tools for photos, Office tools for DOCX/XLSX/PPTX, media tools for video/audio, ZIP Privacy Scanner for archives, or Verify Cleaned File after any cleanup.</p>
          </div>
        </div>
      </section>
    </main>
  );
}
