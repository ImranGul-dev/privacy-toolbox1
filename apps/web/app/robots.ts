import { siteConfig } from '@/lib/config/site';

export default function robots() {
  return {
    rules: [
      { userAgent: '*', allow: '/', disallow: ['/dashboard', '/dashboard/', '/auth/login', '/auth/register', '/auth/verify'] },
      { userAgent: 'OAI-SearchBot', allow: '/' },
      { userAgent: 'ChatGPT-User', allow: '/' },
      { userAgent: 'PerplexityBot', allow: '/' },
      { userAgent: 'Perplexity-User', allow: '/' },
      { userAgent: 'bingbot', allow: '/' },
    ],
    sitemap: `${siteConfig.url}/sitemap.xml`,
  };
}
