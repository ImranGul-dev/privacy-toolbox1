import Link from 'next/link';
import { ShieldCheck } from 'lucide-react';

const columns = [
  { title: 'Product', links: [['All tools', '/tools'], ['Image Privacy', '/tools?category=image'], ['PDF Privacy', '/tools?category=pdf'], ['Office Privacy', '/tools?category=office'], ['Media Privacy', '/tools?category=media'], ['ZIP Scanner', '/tools/zip-privacy-scanner'], ['Verify Metadata', '/tools/verify-file-metadata']] },
  { title: 'Company', links: [['Pricing', '/pricing'], ['Security', '/security'], ['About us', '/about'], ['Contact us', '/contact']] },
  { title: 'Resources', links: [['FAQ', '/#faq'], ['How metadata works', '/blog/how-metadata-works'], ['File privacy guide', '/blog/file-privacy-guide'], ['Clean before sharing', '/clean-file-before-sharing'], ['What is EXIF', '/glossary/exif'], ['Resume cleaner', '/use-cases/resume-metadata-cleaner']] },
  { title: 'Legal', links: [['Privacy Policy', '/privacy'], ['Terms of Use', '/terms']] },
];

export function SiteFooter() {
  return (
    <footer className="border-t border-slate-800 bg-slate-950 text-slate-300">
      <div className="site-container py-12 sm:py-16">
        <div className="grid gap-10 lg:grid-cols-[1.25fr_2fr]">
          <div>
            <Link href="/" className="flex items-center gap-3 text-white">
              <span className="grid h-10 w-10 place-items-center rounded-2xl bg-gradient-to-br from-blue-500 to-teal"><ShieldCheck className="h-5 w-5" /></span>
              <span className="text-lg font-bold tracking-tight">Privacy Toolbox</span>
            </Link>
            <p className="mt-4 max-w-sm text-sm leading-6 text-slate-400">
              Scan, clean, and verify hidden file data before you share. Your files are scheduled for automatic deletion after the temporary processing window.
            </p>
            <div className="mt-5 inline-flex rounded-full border border-slate-800 bg-slate-900 px-3 py-1 text-xs font-semibold text-teal">
              Temporary files auto-delete
            </div>
          </div>
          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {columns.map((col) => (
              <div key={col.title}>
                <h3 className="text-sm font-bold text-white">{col.title}</h3>
                <ul className="mt-4 space-y-3 text-sm">
                  {col.links.map(([label, href]) => (
                    <li key={href}><Link className="text-slate-400 transition hover:text-white" href={href}>{label}</Link></li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
        <div className="mt-10 flex flex-col gap-3 border-t border-slate-800 pt-6 text-xs text-slate-500 sm:flex-row sm:items-center sm:justify-between">
          <p>© Privacy Toolbox. Privacy-first file scanning, cleaning, and verification.</p>
          <p>Temporary uploads and generated files are scheduled for cleanup.</p>
        </div>
      </div>
    </footer>
  );
}
