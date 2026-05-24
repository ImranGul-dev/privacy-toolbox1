import { CheckCircle2, Download, Loader2, ScanSearch, ShieldCheck, UploadCloud } from 'lucide-react';

const steps = [
  { key: 'upload', label: 'Upload', icon: UploadCloud },
  { key: 'scan', label: 'Scan', icon: ScanSearch },
  { key: 'clean', label: 'Clean', icon: ShieldCheck },
  { key: 'verify', label: 'Verify', icon: CheckCircle2 },
  { key: 'download', label: 'Download', icon: Download },
];

function stepIndex(current?: string) {
  const c = (current || '').toLowerCase();
  if (c.includes('download') || c.includes('complete') || c.includes('verified')) return 4;
  if (c.includes('verify')) return 3;
  if (c.includes('clean') || c.includes('processing')) return 2;
  if (c.includes('scan')) return 1;
  return 0;
}

export function ProgressStepper({ step }: { step?: string }) {
  const active = stepIndex(step);
  return (
    <div className="grid gap-3 sm:grid-cols-5" aria-label="Processing steps">
      {steps.map((item, idx) => {
        const Icon = idx === active && active < 4 ? Loader2 : item.icon;
        const done = idx < active;
        const current = idx === active;
        return (
          <div key={item.key} className={`rounded-2xl border p-3 text-sm ${done || current ? 'border-brand/20 bg-blue-50 text-brand' : 'border-line bg-white text-soft'}`}>
            <div className="flex items-center gap-2 font-bold">
              <Icon className={`h-4 w-4 ${idx === active && active < 4 ? 'animate-spin' : ''}`} /> {item.label}
            </div>
          </div>
        );
      })}
    </div>
  );
}
