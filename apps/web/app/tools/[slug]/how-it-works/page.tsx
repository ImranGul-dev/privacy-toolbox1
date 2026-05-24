import Link from 'next/link';
import { notFound } from 'next/navigation';
import { ArrowRight, CheckCircle2, FileSearch, ShieldCheck } from 'lucide-react';
import { getTool, tools } from '@/lib/seo/tools';
import { siteConfig } from '@/lib/config/site';

export function generateStaticParams(){ return tools.map((tool)=>({slug: tool.slug})); }

export async function generateMetadata({params}:{params:Promise<{slug:string}>}){
  const {slug}=await params;
  try{ const tool=getTool(slug); return { title: `How ${tool.shortTitle} works`, description: `Learn how ${tool.shortTitle} scans files, reports metadata findings, protects temporary uploads, and helps verify safer sharing.`, alternates:{canonical:`/tools/${tool.slug}/how-it-works`} }; } catch { return {}; }
}

function steps(tool:any){
  const clean = tool.supportsClean;
  return [
    ['Upload privately', `Choose a supported ${tool.formats} file. The file is used for this job only and temporary uploads are scheduled for deletion.`],
    ['Scan metadata', `${tool.shortTitle} checks file-specific metadata indicators and separates private findings from routine technical data.`],
    [clean ? 'Review and clean' : 'Review the report', clean ? 'Select the detected metadata categories you want to remove, then run the cleaner for that file type.' : 'Use the scan-only report to decide whether the file is ready to share or needs a cleaner tool.'],
    ['Verify before sharing', clean ? 'The cleaned output is scanned again so you can confirm whether removable private metadata is still detected.' : 'Use the verification tool or a matching cleaner if the report shows privacy-risk metadata.'],
  ];
}

export default async function HowToolWorksPage({params}:{params:Promise<{slug:string}>}){
  const {slug}=await params; let tool:any; try{ tool=getTool(slug); }catch{ notFound(); }
  const jsonLd = {'@context':'https://schema.org','@type':'Article',headline:`How ${tool.shortTitle} works`,description:`A clear explanation of how ${tool.shortTitle} helps scan, clean, or verify file metadata before sharing.`,author:{'@type':'Organization',name:'Privacy Toolbox'},publisher:{'@type':'Organization',name:'Privacy Toolbox'},mainEntityOfPage:`${siteConfig.url}/tools/${tool.slug}/how-it-works`};
  return <main><script type="application/ld+json" dangerouslySetInnerHTML={{__html:JSON.stringify(jsonLd)}}/><section className="py-12 sm:py-16 lg:py-20"><div className="site-container"><div className="mx-auto max-w-4xl text-center"><span className="eyebrow"><FileSearch className="h-3.5 w-3.5"/> Tool guide</span><h1 className="heading-xl mx-auto mt-5">How {tool.shortTitle} works</h1><p className="lead mx-auto mt-5">{tool.desc} This guide explains the workflow in plain language so you know what happens before you upload, scan, clean, verify, and download.</p><div className="mt-6 flex justify-center"><Link href={`/tools/${tool.slug}`} className="btn btn-primary">Open {tool.shortTitle}<ArrowRight className="h-4 w-4"/></Link></div></div><div className="mx-auto mt-12 grid max-w-5xl gap-5 md:grid-cols-2">{steps(tool).map(([title,body],i)=><div key={title} className="card p-6"><span className="grid h-12 w-12 place-items-center rounded-2xl bg-blue-50 text-brand font-bold">{i+1}</span><h2 className="mt-5 text-xl font-bold text-ink">{title}</h2><p className="mt-3 text-sm leading-7 text-subtle">{body}</p></div>)}</div><section className="mx-auto mt-12 max-w-5xl rounded-[2rem] border border-line bg-white p-6 shadow-card"><h2 className="text-2xl font-bold text-ink">What this tool checks</h2><div className="mt-5 grid gap-4 md:grid-cols-3"><div className="rounded-2xl bg-slate-50 p-4"><h3 className="font-bold text-ink">Private metadata</h3><p className="mt-2 text-sm leading-6 text-subtle">Author names, device fields, timestamps, location data, document properties, hidden comments, or provenance data depending on file type.</p></div><div className="rounded-2xl bg-slate-50 p-4"><h3 className="font-bold text-ink">Technical data</h3><p className="mt-2 text-sm leading-6 text-subtle">Format, size, codec, dimensions, page count, and other compatibility data may remain because files need it to open correctly.</p></div><div className="rounded-2xl bg-slate-50 p-4"><h3 className="font-bold text-ink">Verification status</h3><p className="mt-2 text-sm leading-6 text-subtle">Cleaner tools re-scan outputs and show whether removable private metadata is still detected by the current scanners.</p></div></div></section><section className="mx-auto mt-8 max-w-5xl rounded-[2rem] border border-emerald-200 bg-emerald-50 p-6"><h2 className="flex items-center gap-2 text-2xl font-bold text-ink"><ShieldCheck className="h-5 w-5 text-success"/> Privacy-first workflow</h2><ul className="mt-5 grid gap-3 text-sm leading-7 text-emerald-950 md:grid-cols-2"><li className="flex gap-2"><CheckCircle2 className="mt-1 h-4 w-4 shrink-0 text-success"/> Temporary files are scheduled for deletion after the processing window.</li><li className="flex gap-2"><CheckCircle2 className="mt-1 h-4 w-4 shrink-0 text-success"/> Reports focus on metadata categories instead of exposing your file content.</li><li className="flex gap-2"><CheckCircle2 className="mt-1 h-4 w-4 shrink-0 text-success"/> Scan-only tools do not modify your original file.</li><li className="flex gap-2"><CheckCircle2 className="mt-1 h-4 w-4 shrink-0 text-success"/> Cleaner tools create a new output file and keep the original separate.</li></ul></section></div></section></main>;
}
