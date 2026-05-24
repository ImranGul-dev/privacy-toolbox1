import { notFound } from 'next/navigation';
import { ToolTemplate } from '@/components/tool/ToolTemplate';
import { getTool, tools } from '@/lib/seo/tools';

export function generateStaticParams() {
  return tools.map((tool) => ({ slug: tool.slug }));
}

export async function generateMetadata({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  try {
    const tool = getTool(slug);
    return {
      title: tool.title,
      description: tool.desc,
      alternates: { canonical: `/tools/${tool.slug}` },
    };
  } catch {
    return {};
  }
}

export default async function Page({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  try {
    const tool = getTool(slug);
    return <ToolTemplate tool={tool} />;
  } catch {
    notFound();
  }
}
