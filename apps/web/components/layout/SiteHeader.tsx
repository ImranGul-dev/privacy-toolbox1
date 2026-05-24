"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Archive, ChevronDown, FileAudio, FileCheck2, FileImage, FileText, FileVideo, KeyRound, LogOut, Menu, SearchCheck, ShieldCheck, Sparkles, UserCircle2, X } from "lucide-react";
import { clearAuthToken, getMe, getPublicConfig, logoutUser } from "@/lib/api/client";
import { kindLabels, tools } from "@/lib/seo/tools";
import type { ToolKind } from "@/lib/tools/types";

const groupOrder: ToolKind[] = ["image", "pdf", "office", "media", "archive", "verify", "ai"];
const iconByKind: Record<ToolKind, any> = { image: FileImage, pdf: FileText, office: FileCheck2, media: FileVideo, archive: Archive, verify: ShieldCheck, ai: Sparkles };
const iconBySlug: Record<string, any> = {
  "remove-image-metadata": FileImage, "remove-exif-data": SearchCheck, "remove-gps-from-photo": ShieldCheck,
  "remove-pdf-metadata": FileText, "pdf-privacy-scanner": SearchCheck, "remove-pdf-hidden-data": ShieldCheck, "pdf-redaction-checker": SearchCheck,
  "remove-docx-metadata": FileCheck2, "docx-hidden-data-scanner": FileCheck2, "xlsx-hidden-data-scanner": FileCheck2, "pptx-remove-notes-hidden-slides": FileCheck2,
  "remove-video-metadata": FileVideo, "remove-audio-metadata": FileAudio, "zip-privacy-scanner": Archive, "remove-zip-privacy-risks": Archive,
  "verify-file-metadata": ShieldCheck, "detect-content-credentials": Sparkles,
};
const groups = groupOrder.map((kind) => ({ kind, label: kindLabels[kind], items: tools.filter((tool) => tool.kind === kind) }));

export function SiteHeader() {
  const [megaOpen, setMegaOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [user, setUser] = useState<any>(null);
  const [promo, setPromo] = useState<any>(null);
  const timer = useRef<number | null>(null);
  useEffect(() => { getMe().then((d)=>setUser(d.user || null)).catch(()=>setUser(null)); getPublicConfig().then((d)=>setPromo(d.promo || null)).catch(()=>setPromo(null)); }, []);
  function clearTimer(){ if(timer.current){ window.clearTimeout(timer.current); timer.current=null; } }
  function openMenu(){ clearTimer(); setMegaOpen(true); }
  function closeSoon(){ clearTimer(); timer.current = window.setTimeout(()=>setMegaOpen(false), 240); }
  useEffect(()=>()=>clearTimer(),[]);
  useEffect(()=>{ if(!mobileOpen) return; const old=document.body.style.overflow; document.body.style.overflow='hidden'; return()=>{document.body.style.overflow=old};},[mobileOpen]);
  async function logout(){ await logoutUser(); clearAuthToken(); setUser(null); window.location.href='/'; }

  return <header className="sticky top-0 z-[9998] border-b border-line/80 bg-white/90 backdrop-blur-xl">
    {promo?.active && <div className="border-b border-blue-100 bg-gradient-to-r from-brand to-teal px-4 py-2 text-center text-sm font-bold text-white">{promo.display_text}{promo.coupon_code && <span className="ml-2 rounded-full bg-white/20 px-2 py-0.5">Code: {promo.coupon_code}</span>}{promo.affiliate_url && <a className="ml-3 underline" href={promo.affiliate_url}>Claim offer</a>}</div>}
    <div className="site-container"><div className="flex h-16 items-center justify-between gap-4 lg:h-20">
      <Link href="/" className="flex items-center gap-3 font-bold tracking-tight text-ink" aria-label="Privacy Toolbox home"><span className="grid h-10 w-10 place-items-center rounded-2xl bg-gradient-to-br from-brand to-teal text-white shadow-card"><ShieldCheck className="h-5 w-5" /></span><span className="text-base leading-tight sm:text-lg">Privacy<br className="hidden sm:block" /> Toolbox</span></Link>
      <nav className="hidden items-center gap-1 text-sm font-semibold text-subtle lg:flex" aria-label="Main navigation">
        <div className="relative" onMouseEnter={openMenu} onMouseLeave={closeSoon} onFocus={openMenu}>
          <button className="btn btn-ghost h-10 w-auto px-3" type="button" aria-expanded={megaOpen} aria-haspopup="true" onClick={()=>setMegaOpen(v=>!v)}>All Tools <ChevronDown className={`h-4 w-4 transition ${megaOpen?'rotate-180':''}`} /></button>
          {megaOpen && <MegaMenu onMouseEnter={openMenu} onMouseLeave={closeSoon} onNavigate={()=>setMegaOpen(false)} />}
        </div>
        <Link className="btn btn-ghost h-10 w-auto px-3" href="/security">Security</Link><Link className="btn btn-ghost h-10 w-auto px-3" href="/pricing">Pricing</Link><Link className="btn btn-ghost h-10 w-auto px-3" href="/about">About us</Link><Link className="btn btn-ghost h-10 w-auto px-3" href="/contact">Contact us</Link>
      </nav>
      <div className="hidden items-center gap-2 lg:flex">{user ? <><Link className="btn btn-secondary h-10 w-auto px-4" href={user.role === 'admin' ? '/dashboard' : '/tools'}><UserCircle2 className="h-4 w-4" /> {user.name || user.email.split('@')[0]}</Link><button className="btn btn-primary h-10 w-auto px-4" onClick={logout} type="button"><LogOut className="h-4 w-4" /> Logout</button></> : <><Link className="btn btn-secondary h-10 w-auto px-4" href="/auth/login">Login</Link><Link className="btn btn-primary h-10 w-auto px-5" href="/auth/register">Sign up</Link></>}</div>
      <button className="grid h-11 w-11 place-items-center rounded-2xl border border-line bg-white text-ink shadow-sm lg:hidden" type="button" onClick={()=>setMobileOpen(true)} aria-label="Open menu"><Menu className="h-5 w-5" /></button>
    </div></div>
    {mobileOpen && <MobileMenuPortal onClose={()=>setMobileOpen(false)} user={user} onLogout={logout} />}
  </header>;
}

function MegaMenu({onMouseEnter,onMouseLeave,onNavigate}:{onMouseEnter:()=>void;onMouseLeave:()=>void;onNavigate:()=>void}){
  const [active,setActive]=useState<ToolKind>('image');
  const current = groups.find(g=>g.kind===active) || groups[0];
  const popular = tools.filter(t=>['remove-image-metadata','remove-pdf-metadata','remove-docx-metadata','remove-video-metadata','zip-privacy-scanner','verify-file-metadata'].includes(t.slug));
  const ActiveIcon = iconByKind[active];
  return <div className="fixed left-1/2 top-[4.6rem] z-[99999] w-[min(980px,calc(100vw-2rem))] -translate-x-1/2 pt-4" onMouseEnter={onMouseEnter} onMouseLeave={onMouseLeave}>
    <div className="overflow-hidden rounded-[1.75rem] border border-line bg-white shadow-lift animate-soft-pop">
      <div className="grid max-h-[calc(100vh-7rem)] grid-cols-[250px_1fr] overflow-hidden">
        <aside className="border-r border-line bg-gradient-to-b from-blue-50 to-emerald-50 p-4">
          <p className="px-2 text-xs font-bold uppercase tracking-[0.18em] text-brand">Tool categories</p>
          <div className="mt-4 grid gap-1.5">{groups.map(g=>{const Icon=iconByKind[g.kind]; return <button key={g.kind} onMouseEnter={()=>setActive(g.kind)} onClick={()=>setActive(g.kind)} className={`flex w-full items-center gap-3 rounded-2xl px-3 py-2.5 text-left text-sm font-bold transition ${active===g.kind?'bg-white text-brand shadow-sm':'text-ink hover:bg-white/70'}`}><span className="grid h-8 w-8 place-items-center rounded-xl bg-white text-brand shadow-sm"><Icon className="h-4 w-4" /></span>{g.label}</button>})}</div>
          <div className="mt-5 rounded-2xl bg-white/75 p-3"><p className="text-xs font-bold uppercase tracking-[0.14em] text-soft">Popular</p><div className="mt-2 grid gap-1">{popular.slice(0,4).map(item=><SmallToolLink key={item.slug} item={item} onNavigate={onNavigate}/>)}</div></div>
        </aside>
        <section className="overflow-y-auto p-5">
          <div className="flex items-center justify-between gap-4"><div className="flex items-center gap-3"><span className="grid h-11 w-11 place-items-center rounded-2xl bg-blue-50 text-brand"><ActiveIcon className="h-5 w-5" /></span><div><h2 className="text-lg font-bold text-ink">{current.label}</h2><p className="text-sm text-subtle">Choose a tool to scan, clean, or verify before sharing.</p></div></div><Link href="/tools" onClick={onNavigate} className="btn btn-secondary h-10 px-4 text-xs">View all</Link></div>
          <div className="mt-5 grid gap-3 sm:grid-cols-2">{current.items.map(item=><ToolCardLink key={item.slug} item={item} onNavigate={onNavigate}/>)}</div>
          <div className="mt-5 grid gap-3 rounded-3xl border border-line bg-slate-50 p-4 sm:grid-cols-3"><Link href="/clean-file-before-sharing" onClick={onNavigate} className="text-sm font-bold text-brand">Safe sharing guide</Link><Link href="/security" onClick={onNavigate} className="text-sm font-bold text-brand">Security</Link><Link href="/contact" onClick={onNavigate} className="text-sm font-bold text-brand">Need help?</Link></div>
        </section>
      </div>
    </div>
  </div>;
}

function ToolCardLink({item,onNavigate}:{item:any;onNavigate:()=>void}){ const Icon=iconBySlug[item.slug]||iconByKind[item.kind as ToolKind]||ShieldCheck; return <Link href={`/tools/${item.slug}`} onClick={onNavigate} className="group flex items-center gap-3 rounded-2xl border border-line bg-white p-3 transition hover:-translate-y-0.5 hover:border-brand/30 hover:shadow-card"><span className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl bg-blue-50 text-brand"><Icon className="h-4 w-4" /></span><span className="min-w-0"><span className="block truncate text-sm font-bold text-ink">{item.shortTitle}</span><span className="mt-0.5 block text-xs text-soft">{item.supportsClean ? 'Scan + clean + verify' : 'Scan-only report'}</span></span></Link> }
function SmallToolLink({item,onNavigate}:{item:any;onNavigate:()=>void}){ const Icon=iconBySlug[item.slug]||ShieldCheck; return <Link href={`/tools/${item.slug}`} onClick={onNavigate} className="flex items-center gap-2 rounded-xl px-2 py-2 text-sm font-bold text-ink hover:bg-blue-50"><Icon className="h-4 w-4 shrink-0 text-brand" /><span className="truncate">{item.shortTitle}</span></Link> }

function MobileMenuPortal({onClose,user,onLogout}:{onClose:()=>void;user:any;onLogout:()=>void}){ const [mounted,setMounted]=useState(false); useEffect(()=>setMounted(true),[]); if(!mounted)return null; return createPortal(<MobileMenu onClose={onClose} user={user} onLogout={onLogout}/>, document.body); }
function MobileMenu({onClose,user,onLogout}:{onClose:()=>void;user:any;onLogout:()=>void}){ return <div className="fixed inset-0 z-[99999] lg:hidden" role="dialog" aria-modal="true"><button className="absolute inset-0 h-full w-full bg-slate-950/45 backdrop-blur-sm" onClick={onClose} aria-label="Close menu"/><aside className="absolute right-0 top-0 h-[100dvh] w-[min(92vw,430px)] overflow-y-auto bg-white p-5 shadow-lift"><div className="flex items-center justify-between gap-4"><Link href="/" onClick={onClose} className="flex items-center gap-3 font-bold text-ink"><span className="grid h-10 w-10 place-items-center rounded-2xl bg-gradient-to-br from-brand to-teal text-white"><ShieldCheck className="h-5 w-5"/></span>Privacy Toolbox</Link><button className="grid h-10 w-10 place-items-center rounded-2xl border border-line bg-white" onClick={onClose}><X className="h-5 w-5"/></button></div><div className="mt-6 space-y-5 pb-8"><div className="grid gap-3">{[['All tools','/tools'],['Security','/security'],['Pricing','/pricing'],['About us','/about'],['Contact us','/contact']].map(([label,href])=><Link key={href} onClick={onClose} href={href} className="btn btn-secondary justify-start">{label}</Link>)}</div>{groups.map(group=><section key={group.kind}><h3 className="mb-2 text-xs font-bold uppercase tracking-[0.16em] text-soft">{group.label}</h3><div className="grid gap-2">{group.items.map(item=><ToolCardLink key={item.slug} item={item} onNavigate={onClose}/>)}</div></section>)}<div className="grid grid-cols-2 gap-3 border-t border-line pt-5">{user ? <><Link onClick={onClose} href={user.role==='admin'?'/dashboard':'/tools'} className="btn btn-secondary"><UserCircle2 className="h-4 w-4"/> Account</Link><button onClick={()=>{onClose(); onLogout();}} className="btn btn-primary" type="button"><LogOut className="h-4 w-4"/> Logout</button></> : <><Link onClick={onClose} href="/auth/login" className="btn btn-secondary"><KeyRound className="h-4 w-4"/> Login</Link><Link onClick={onClose} href="/auth/register" className="btn btn-primary">Sign up</Link></>}</div></div></aside></div> }
