import Link from 'next/link';
import { Download, RotateCcw, ShieldCheck } from 'lucide-react';
import { downloadUrl } from '@/lib/api/client';

export function DownloadPanel({ token }: { token?: string }) {
  if (!token) return null;
  return (
    <div className="card overflow-hidden p-6">
      <div className="grid gap-5 lg:grid-cols-[1fr_auto] lg:items-center">
        <div className="flex gap-4">
          <span className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-emerald-50 text-success"><ShieldCheck className="h-5 w-5" /></span>
          <div>
            <h3 className="text-xl font-bold tracking-tight text-ink">Cleaned file is ready</h3>
            <p className="mt-1 text-sm leading-6 text-subtle">Download link is short-lived. Verify again anytime by uploading the cleaned file to the verification tool.</p>
          </div>
        </div>
        <div className="flex flex-col gap-3 sm:flex-row">
          <a className="btn btn-primary" href={downloadUrl(token)}><Download className="h-4 w-4" /> Download cleaned file</a>
          <Link className="btn btn-secondary" href="/tools/verify-file-metadata"><RotateCcw className="h-4 w-4" /> Verify again</Link>
        </div>
      </div>
    </div>
  );
}
