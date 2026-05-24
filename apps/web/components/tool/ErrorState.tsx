import { AlertCircle } from 'lucide-react';
export function ErrorState({ message }: { message: string }) {
  return <div className="rounded-3xl border border-red-200 bg-red-50 p-5 text-danger"><div className="flex gap-3"><AlertCircle className="h-5 w-5" /><div><b>Something went wrong</b><p className="mt-1 text-sm">{message}</p></div></div></div>;
}
