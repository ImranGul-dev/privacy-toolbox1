import { VerifyEmailForm } from '@/components/auth/VerifyEmailForm';
export const metadata = { title: 'Verify email', description: 'Verify your Privacy Toolbox account email.', robots: { index: false, follow: false } };
export default function VerifyPage(){ return <main className='py-12 sm:py-16 lg:py-20'><div className='site-container'><VerifyEmailForm /></div></main>; }
