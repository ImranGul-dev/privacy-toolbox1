import { Inbox } from 'lucide-react';
export function EmptyState() {
  return <div className="card p-6 text-center"><span className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-slate-50 text-soft"><Inbox className="h-5 w-5" /></span><b className="mt-4 block text-ink">No job selected</b><p className="mt-1 text-sm text-subtle">Upload a file to begin.</p></div>;
}
