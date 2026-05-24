import { AdminDashboard } from '@/components/admin/AdminDashboard';

export const metadata = {
  title: 'Admin dashboard | Privacy Toolbox',
  description: 'Private admin dashboard.',
  robots: { index: false, follow: false },
};

export default function Page() {
  return <AdminDashboard />;
}
