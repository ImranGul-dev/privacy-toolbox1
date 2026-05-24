'use client';
import { useEffect, useMemo, useState } from 'react';
import { Clock3 } from 'lucide-react';

export function DeletionTimer({ expiresAt }: { expiresAt?: string }) {
  const target = useMemo(() => expiresAt ? new Date(expiresAt).getTime() : Date.now() + 10 * 60 * 1000, [expiresAt]);
  const [remaining, setRemaining] = useState(Math.max(0, target - Date.now()));
  useEffect(() => {
    const id = setInterval(() => setRemaining(Math.max(0, target - Date.now())), 1000);
    return () => clearInterval(id);
  }, [target]);
  const mins = Math.floor(remaining / 60000);
  const secs = Math.floor((remaining % 60000) / 1000);
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-teal/20 bg-teal/5 p-4 text-sm font-semibold text-teal">
      <Clock3 className="h-5 w-5" /> Temporary file deletes in {mins}:{String(secs).padStart(2, '0')}
    </div>
  );
}
