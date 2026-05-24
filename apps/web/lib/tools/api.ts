import { siteConfig } from '@/lib/config/site';
import type { ToolAction } from './types';

async function errorText(r: Response) {
  const text = await r.text();
  try {
    const parsed = JSON.parse(text);
    return typeof parsed.detail === 'string' ? parsed.detail : JSON.stringify(parsed.detail || parsed);
  } catch {
    return text || `Request failed with ${r.status}`;
  }
}

function headers() {
  return { 'Content-Type': 'application/json' };
}

export async function createToolJob(toolId: string, action: ToolAction, fileId: string, options: any = {}) {
  const r = await fetch(`${siteConfig.apiBaseUrl}/api/tools/${toolId}/${action}`, {
    method: 'POST',
    headers: headers(),
    credentials: 'include',
    body: JSON.stringify({ file_id: fileId, options }),
  });
  if (!r.ok) throw new Error(await errorText(r));
  return r.json();
}

export async function getRegisteredTools() {
  const r = await fetch(`${siteConfig.apiBaseUrl}/api/tools`, { credentials: 'include' });
  if (!r.ok) throw new Error(await errorText(r));
  return r.json();
}
