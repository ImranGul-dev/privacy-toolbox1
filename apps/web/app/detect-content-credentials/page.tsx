import { ToolTemplate } from '@/components/tool/ToolTemplate';
import { getTool } from '@/lib/seo/tools';

export const metadata = { title: 'Detect Content Credentials', description: 'Scan for C2PA / Content Credentials manifest indicators in supported files.' };

export default function Page() {
  return <ToolTemplate tool={getTool('detect-content-credentials')} />;
}
