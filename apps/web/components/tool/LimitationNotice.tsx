import { Clock3 } from 'lucide-react';

export function LimitationNotice() {
  return (
    <div className="rounded-3xl border border-emerald-200 bg-emerald-50 p-5 text-emerald-900">
      <div className="flex gap-3">
        <Clock3 className="mt-0.5 h-5 w-5 shrink-0" />
        <p className="text-sm leading-6">
          Your file is used only for the selected job. Temporary uploads and generated files are scheduled to auto-delete after 10 minutes.
        </p>
      </div>
    </div>
  );
}
