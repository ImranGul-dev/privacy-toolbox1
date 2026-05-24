export function ResultSummary({ job }: { job: any }) {
  return <div className="card p-5"><h3 className="text-lg font-bold text-ink">{job.status}</h3><p className="mt-1 text-sm text-subtle">{job.current_step}</p></div>;
}
