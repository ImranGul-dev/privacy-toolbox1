'use client';
import { useEffect } from 'react';
export default function ErrorPage({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => { console.error(error); }, [error]);
  return <main className="py-16 sm:py-24"><div className="site-container"><div className="card mx-auto max-w-xl p-8 text-center"><span className="eyebrow">Error</span><h1 className="heading-lg mt-4">Something went wrong</h1><p className="lead mx-auto mt-3">Please try again. If the issue continues, check the API and worker logs.</p><button className="btn btn-primary mt-6" onClick={reset}>Try again</button></div></div></main>;
}
