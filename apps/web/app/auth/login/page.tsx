import { AuthForm } from '@/components/auth/AuthForm';
export const metadata = { title: 'Login', description: 'Login to Privacy Toolbox.', robots: { index: false, follow: false } };
export default function LoginPage() { return <main className="py-12 sm:py-16 lg:py-20"><div className="site-container"><AuthForm mode="login" /></div></main>; }
