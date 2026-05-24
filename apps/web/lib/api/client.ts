import { siteConfig } from '@/lib/config/site';

export type JobStatus='queued'|'processing'|'completed'|'failed'|'expired';
export type Job={id:string;status:JobStatus;tool_type:string;input_filename:string;output_filename?:string;download_filename?:string;file_type?:string;file_size:number;progress:number;current_step:string;report:any;download_token?:string;expires_at?:string;created_at?:string;updated_at?:string;error_message?:string;plan?:string;usage?:any};

// Browser auth uses only the secure HttpOnly pt_session cookie.
// These functions remain as no-ops for backward compatibility with older components.
export function getAuthToken(){ return ''; }
export function setAuthToken(_token:string){ /* no localStorage token: protects sessions from XSS token theft */ }
export function clearAuthToken(){ /* no-op */ }

function authHeaders(extra:Record<string,string>={}){ return extra; }
const credentials: RequestCredentials = 'include';

async function errorText(r:Response){
  const text=await r.text();
  try { const parsed=JSON.parse(text); return typeof parsed.detail==='string' ? parsed.detail : JSON.stringify(parsed.detail || parsed); } catch { return text || `Request failed with ${r.status}`; }
}

export async function uploadFile(file:File){const fd=new FormData();fd.append('file',file);const r=await fetch(`${siteConfig.apiBaseUrl}/api/uploads`,{method:'POST',headers:authHeaders(),credentials,body:fd});if(!r.ok)throw new Error(await errorText(r));return r.json();}
export async function createJob(path:string,file_id:string,options:any={}){const r=await fetch(`${siteConfig.apiBaseUrl}${path}`,{method:'POST',headers:authHeaders({'Content-Type':'application/json'}),credentials,body:JSON.stringify({file_id,options})});if(!r.ok)throw new Error(await errorText(r));return r.json();}
export async function getJob(id:string):Promise<Job>{const r=await fetch(`${siteConfig.apiBaseUrl}/api/jobs/${id}`,{headers:authHeaders(),credentials});if(!r.ok)throw new Error(await errorText(r));return r.json();}
export function downloadUrl(token:string){return `${siteConfig.apiBaseUrl}/api/downloads/${token}`}

export async function registerUser(payload:{name:string;email:string;password:string}){const r=await fetch(`${siteConfig.apiBaseUrl}/api/auth/register`,{method:'POST',headers:{'Content-Type':'application/json'},credentials,body:JSON.stringify(payload)});if(!r.ok)throw new Error(await errorText(r));return r.json();}

export async function verifyEmail(payload:{email:string;code:string}){const r=await fetch(`${siteConfig.apiBaseUrl}/api/auth/verify-email`,{method:'POST',headers:{'Content-Type':'application/json'},credentials,body:JSON.stringify(payload)});if(!r.ok)throw new Error(await errorText(r));return r.json();}
export async function resendVerification(payload:{email:string}){const r=await fetch(`${siteConfig.apiBaseUrl}/api/auth/resend-verification`,{method:'POST',headers:{'Content-Type':'application/json'},credentials,body:JSON.stringify(payload)});if(!r.ok)throw new Error(await errorText(r));return r.json();}
export function oauthStartUrl(provider:'google'|'microsoft'|'github'){return `${siteConfig.apiBaseUrl}/api/auth/oauth/${provider}/start`;}
export async function submitContact(payload:{first_name:string;last_name:string;email:string;subject:string;message:string}){const r=await fetch(`${siteConfig.apiBaseUrl}/api/contact`,{method:'POST',headers:{'Content-Type':'application/json'},credentials,body:JSON.stringify(payload)});if(!r.ok)throw new Error(await errorText(r));return r.json();}
export async function adminMarkContactRead(id:string){const r=await fetch(`${siteConfig.apiBaseUrl}/api/admin/contact-messages/${encodeURIComponent(id)}/read`,{method:'POST',headers:authHeaders(),credentials});if(!r.ok)throw new Error(await errorText(r));return r.json();}

export async function loginUser(payload:{email:string;password:string}){const r=await fetch(`${siteConfig.apiBaseUrl}/api/auth/login`,{method:'POST',headers:{'Content-Type':'application/json'},credentials,body:JSON.stringify(payload)});if(!r.ok)throw new Error(await errorText(r));return r.json();}
export async function logoutUser(){const r=await fetch(`${siteConfig.apiBaseUrl}/api/auth/logout`,{method:'POST',headers:authHeaders(),credentials}); clearAuthToken(); return r.ok ? r.json() : {ok:false};}
export async function getMe(){const r=await fetch(`${siteConfig.apiBaseUrl}/api/auth/me`,{headers:authHeaders(),credentials});if(!r.ok)throw new Error(await errorText(r));return r.json();}
export async function getPlans(){const r=await fetch(`${siteConfig.apiBaseUrl}/api/plans`,{credentials});if(!r.ok)throw new Error(await errorText(r));return r.json();}
export async function getPublicConfig(){const r=await fetch(`${siteConfig.apiBaseUrl}/api/public/config`,{credentials,cache:'no-store'});if(!r.ok)throw new Error(await errorText(r));return r.json();}

export async function createCheckoutSession(payload:{plan:string;interval?:'monthly'|'yearly'}){const r=await fetch(`${siteConfig.apiBaseUrl}/api/billing/checkout`,{method:'POST',headers:authHeaders({'Content-Type':'application/json'}),credentials,body:JSON.stringify(payload)});if(!r.ok)throw new Error(await errorText(r));return r.json();}
export async function createCustomerPortalSession(){const r=await fetch(`${siteConfig.apiBaseUrl}/api/billing/customer-portal`,{method:'POST',headers:authHeaders(),credentials});if(!r.ok)throw new Error(await errorText(r));return r.json();}
export async function analyticsEvent(payload:any){try{await fetch(`${siteConfig.apiBaseUrl}/api/analytics/event`,{method:'POST',headers:authHeaders({'Content-Type':'application/json'}),credentials,body:JSON.stringify(payload),keepalive:true});}catch{}}

export async function adminGetOverview(){const r=await fetch(`${siteConfig.apiBaseUrl}/api/admin/overview`,{headers:authHeaders(),credentials,cache:'no-store'});if(!r.ok)throw new Error(await errorText(r));return r.json();}
export async function adminUpdateSettings(settings:any){const r=await fetch(`${siteConfig.apiBaseUrl}/api/admin/settings`,{method:'PUT',headers:authHeaders({'Content-Type':'application/json'}),credentials,body:JSON.stringify({settings})});if(!r.ok)throw new Error(await errorText(r));return r.json();}
export async function adminSetPromo(payload:any){const r=await fetch(`${siteConfig.apiBaseUrl}/api/admin/promo`,{method:'POST',headers:authHeaders({'Content-Type':'application/json'}),credentials,body:JSON.stringify(payload)});if(!r.ok)throw new Error(await errorText(r));return r.json();}
export async function adminCreateUser(payload:any){const r=await fetch(`${siteConfig.apiBaseUrl}/api/admin/users`,{method:'POST',headers:authHeaders({'Content-Type':'application/json'}),credentials,body:JSON.stringify(payload)});if(!r.ok)throw new Error(await errorText(r));return r.json();}
export async function adminUpdateUser(payload:any){const r=await fetch(`${siteConfig.apiBaseUrl}/api/admin/users`,{method:'PUT',headers:authHeaders({'Content-Type':'application/json'}),credentials,body:JSON.stringify(payload)});if(!r.ok)throw new Error(await errorText(r));return r.json();}
export async function adminCreateCoupon(payload:any){const r=await fetch(`${siteConfig.apiBaseUrl}/api/admin/coupons`,{method:'POST',headers:authHeaders({'Content-Type':'application/json'}),credentials,body:JSON.stringify(payload)});if(!r.ok)throw new Error(await errorText(r));return r.json();}
export async function adminDeleteCoupon(id:string){const r=await fetch(`${siteConfig.apiBaseUrl}/api/admin/coupons/${encodeURIComponent(id)}`,{method:'DELETE',headers:authHeaders(),credentials});if(!r.ok)throw new Error(await errorText(r));return r.json();}
export async function adminCreateAffiliate(payload:any){const r=await fetch(`${siteConfig.apiBaseUrl}/api/admin/affiliates`,{method:'POST',headers:authHeaders({'Content-Type':'application/json'}),credentials,body:JSON.stringify(payload)});if(!r.ok)throw new Error(await errorText(r));return r.json();}
export async function adminDeleteAffiliate(id:string){const r=await fetch(`${siteConfig.apiBaseUrl}/api/admin/affiliates/${encodeURIComponent(id)}`,{method:'DELETE',headers:authHeaders(),credentials});if(!r.ok)throw new Error(await errorText(r));return r.json();}
