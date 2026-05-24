import Link from 'next/link';
export default function NotFound() {
  return <main className="py-16 sm:py-24"><div className="site-container"><div className="card mx-auto max-w-xl p-8 text-center"><span className="eyebrow">404</span><h1 className="heading-lg mt-4">Page not found</h1><p className="lead mx-auto mt-3">The page you are looking for does not exist or has moved.</p><Link className="btn btn-primary mt-6" href="/tools">Browse tools</Link></div></div></main>;
}
