"use client";
import { FormEvent, useState } from "react";
import { AlertCircle, CheckCircle2, Loader2, Send } from "lucide-react";
import { submitContact } from "@/lib/api/client";

export function ContactForm(){
  const [form,setForm]=useState({first_name:'',last_name:'',email:'',subject:'',message:''});
  const [busy,setBusy]=useState(false); const [error,setError]=useState(''); const [success,setSuccess]=useState('');
  async function onSubmit(e:FormEvent){ e.preventDefault(); setError(''); setSuccess(''); setBusy(true); try{ await submitContact(form); setSuccess('Message received. We will reply from gulimran980@gmail.com or a Privacy Toolbox support address.'); setForm({first_name:'',last_name:'',email:'',subject:'',message:''}); }catch(err:any){setError(err.message||'Could not submit message.')} finally{setBusy(false);} }
  return <form className="card p-6 sm:p-8 animate-soft-pop" onSubmit={onSubmit}>
    <div className="grid gap-4 sm:grid-cols-2"><label className="block text-sm font-semibold text-ink">First name<input className="input mt-2" value={form.first_name} onChange={(e)=>setForm({...form,first_name:e.target.value})} type="text" placeholder="Your first name" /></label><label className="block text-sm font-semibold text-ink">Last name<input className="input mt-2" value={form.last_name} onChange={(e)=>setForm({...form,last_name:e.target.value})} type="text" placeholder="Your last name" /></label></div>
    <label className="mt-4 block text-sm font-semibold text-ink">Email<input className="input mt-2" value={form.email} onChange={(e)=>setForm({...form,email:e.target.value})} type="email" placeholder="you@example.com" required /></label>
    <label className="mt-4 block text-sm font-semibold text-ink">Subject<input className="input mt-2" value={form.subject} onChange={(e)=>setForm({...form,subject:e.target.value})} type="text" placeholder="How can we help?" required /></label>
    <label className="mt-4 block text-sm font-semibold text-ink">Message<textarea className="input mt-2 min-h-36 resize-y" value={form.message} onChange={(e)=>setForm({...form,message:e.target.value})} placeholder="Write your message..." required /></label>
    {error && <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 p-3 text-sm font-semibold text-danger"><AlertCircle className="mr-2 inline h-4 w-4"/>{error}</div>}
    {success && <div className="mt-4 rounded-2xl border border-emerald-200 bg-emerald-50 p-3 text-sm font-semibold text-emerald-800"><CheckCircle2 className="mr-2 inline h-4 w-4"/>{success}</div>}
    <button className="btn btn-primary mt-6 sm:w-auto" disabled={busy}>{busy ? <Loader2 className="h-4 w-4 animate-spin"/> : <Send className="h-4 w-4"/>} Send message</button>
    <p className="mt-4 text-xs leading-5 text-soft">Messages are stored in the admin dashboard so support requests are not lost. Do not include passwords, payment details, or highly sensitive file contents.</p>
  </form>
}
