import { AuthForm } from '@/components/auth/AuthForm';
export const metadata = { title: 'Sign up', description: 'Create a Privacy Toolbox account.', robots: { index: false, follow: false } };
export default function RegisterPage() { return <main className="py-12 sm:py-16 lg:py-20"><div className="site-container"><AuthForm mode="register" /></div></main>; }
