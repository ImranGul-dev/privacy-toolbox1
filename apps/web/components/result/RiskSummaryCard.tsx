function labelFor(score: number) {
  if (score >= 70) return { label: 'High', color: 'text-danger', bg: 'bg-red-50', bar: 'bg-danger' };
  if (score >= 30) return { label: 'Medium', color: 'text-warning', bg: 'bg-amber-50', bar: 'bg-warning' };
  return { label: 'Low', color: 'text-success', bg: 'bg-emerald-50', bar: 'bg-success' };
}

export function RiskSummaryCard({ report }: { report?: any }) {
  const score = Number(report?.risk_score ?? report?.after?.risk_score ?? 0);
  const meta = labelFor(score);
  const summary = report?.summary || report?.after?.summary || 'Waiting for scan result.';
  return (
    <div className="card p-6">
      <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <span className="badge">Verification report</span>
          <h3 className="mt-3 text-2xl font-bold tracking-tight text-ink">Privacy risk: <span className={meta.color}>{meta.label}</span></h3>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-subtle">{summary}</p>
        </div>
        <div className={`grid h-28 w-28 shrink-0 place-items-center rounded-full ${meta.bg}`}>
          <div className="text-center"><div className={`text-3xl font-bold ${meta.color}`}>{score}</div><div className="text-xs font-bold text-soft">/ 100</div></div>
        </div>
      </div>
      <div className="mt-5 h-3 overflow-hidden rounded-full bg-slate-100">
        <div className={`h-full rounded-full ${meta.bar} transition-all`} style={{ width: `${Math.min(100, score)}%` }} />
      </div>
    </div>
  );
}
