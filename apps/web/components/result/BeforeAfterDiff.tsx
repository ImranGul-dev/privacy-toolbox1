import { CheckCircle2, CircleAlert, Info } from 'lucide-react';
import { MetadataTagList } from './MetadataTagList';

type ReportMode = 'scan' | 'clean';

export function BeforeAfterDiff({ report, mode }: { report?: any; mode?: ReportMode }) {
  const isCleanReport = mode === 'clean' || Boolean(report?.before || report?.after);
  const findings = report?.findings || [];
  const technical = report?.technical_metadata || [];

  if (!isCleanReport) {
    return (
      <div className="grid gap-5 lg:grid-cols-2">
        <div className="card p-6">
          <div className="flex items-center gap-2 text-brand"><Info className="h-5 w-5" /><h3 className="font-bold text-ink">Detected metadata</h3></div>
          <p className="mt-2 text-sm text-subtle">{report?.summary || 'Scan result will appear here.'}</p>
          <div className="mt-4">
            <MetadataTagList items={findings} emptyText="No removable private metadata found by current scanners." />
          </div>
        </div>
        <div className="card p-6">
          <div className="flex items-center gap-2 text-success"><CheckCircle2 className="h-5 w-5" /><h3 className="font-bold text-ink">Technical / compatibility data</h3></div>
          <p className="mt-2 text-sm text-subtle">Technical fields are shown for transparency and are not treated as private metadata by default.</p>
          <div className="mt-4">
            <MetadataTagList items={technical} emptyText="No notable technical metadata was reported." />
          </div>
        </div>
        <details className="card p-5 lg:col-span-2">
          <summary className="cursor-pointer text-sm font-bold text-ink">Advanced details</summary>
          <pre className="mt-4 max-h-80 overflow-auto rounded-2xl bg-slate-950 p-4 text-xs leading-5 text-slate-100">{JSON.stringify(report || {}, null, 2)}</pre>
        </details>
      </div>
    );
  }

  const before = report?.before;
  const after = report?.after || report;
  const beforeFindings = before?.findings || [];
  const afterFindings = after?.findings || [];
  const removed = report?.removed_items || [];
  return (
    <div className="grid gap-5 lg:grid-cols-2">
      <div className="card p-6">
        <div className="flex items-center gap-2 text-amber-700"><CircleAlert className="h-5 w-5" /><h3 className="font-bold text-ink">Before cleaning</h3></div>
        <p className="mt-2 text-sm text-subtle">{before ? before.summary : 'Before scan available after a cleaning job.'}</p>
        <div className="mt-4"><MetadataTagList items={beforeFindings} /></div>
      </div>
      <div className="card p-6">
        <div className="flex items-center gap-2 text-success"><CheckCircle2 className="h-5 w-5" /><h3 className="font-bold text-ink">After verification</h3></div>
        <p className="mt-2 text-sm text-subtle">{after?.summary || 'Verification result will appear here.'}</p>
        <div className="mt-4"><MetadataTagList items={afterFindings} emptyText="No removable private metadata remains after verification." /></div>
        {removed.length > 0 && <p className="mt-4 text-sm font-semibold text-success">Removed or reduced: {removed.slice(0, 6).join(', ')}</p>}
      </div>
      <details className="card p-5 lg:col-span-2">
        <summary className="cursor-pointer text-sm font-bold text-ink">Advanced details</summary>
        <pre className="mt-4 max-h-80 overflow-auto rounded-2xl bg-slate-950 p-4 text-xs leading-5 text-slate-100">{JSON.stringify(report || {}, null, 2)}</pre>
      </details>
    </div>
  );
}
