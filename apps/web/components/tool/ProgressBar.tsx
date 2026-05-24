export function ProgressBar({ value = 0 }: { value?: number }) {
  const safe = Math.max(0, Math.min(100, value || 0));
  return (
    <div className="rounded-2xl border border-line bg-white p-4 shadow-sm" aria-label={`Progress ${safe}%`}>
      <div className="flex items-center justify-between text-sm font-bold text-ink"><span>Processing progress</span><span>{safe}%</span></div>
      <div className="mt-3 h-3 overflow-hidden rounded-full bg-slate-100">
        <div className="h-full rounded-full bg-gradient-to-r from-brand to-teal transition-all duration-500" style={{ width: `${safe}%` }} />
      </div>
    </div>
  );
}
