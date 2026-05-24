import { FileText } from 'lucide-react';

export function FileCard({ name, size }: { name: string; size: number }) {
  return (
    <div className="card flex min-w-0 items-center gap-3 p-4">
      <span className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-blue-50 text-brand"><FileText className="h-4 w-4" /></span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-bold text-ink" title={name}>{name}</p>
        <p className="text-xs text-subtle">{(size / 1024 / 1024).toFixed(2)} MB</p>
      </div>
    </div>
  );
}
