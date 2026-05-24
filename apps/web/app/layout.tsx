import './globals.css';
import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import { Suspense } from 'react';
import { SiteHeader } from '@/components/layout/SiteHeader';
import { SiteFooter } from '@/components/layout/SiteFooter';
import { AnalyticsTracker } from '@/components/analytics/AnalyticsTracker';
import { siteConfig } from '@/lib/config/site';

export const metadata: Metadata = {
  title: { default: siteConfig.name, template: '%s | Privacy Toolbox' },
  description: siteConfig.promise,
  metadataBase: new URL(siteConfig.url),
  openGraph: { title: siteConfig.name, description: siteConfig.promise, type: 'website' },
  twitter: { card: 'summary_large_image' },
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <script
          type="application/ld+json"
          suppressHydrationWarning
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              '@context': 'https://schema.org',
              '@type': 'WebApplication',
              name: siteConfig.name,
              url: siteConfig.url,
              applicationCategory: 'SecurityApplication',
              operatingSystem: 'Web',
              description: siteConfig.promise,
              offers: { '@type': 'Offer', price: '0', priceCurrency: 'USD' },
            }),
          }}
        />
        <Suspense fallback={null}><AnalyticsTracker /></Suspense>
        <SiteHeader />
        {children}
        <SiteFooter />
      </body>
    </html>
  );
}
