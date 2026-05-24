import { siteConfig } from '@/lib/config/site';
import { tools } from '@/lib/seo/tools';

const useCases = [
  '/use-cases/resume-metadata-cleaner',
  '/use-cases/legal-document-metadata-cleaner',
  '/use-cases/business-proposal-metadata-cleaner',
  '/use-cases/social-media-image-privacy-checker',
  '/use-cases/safe-file-sharing-for-hr',
  '/use-cases/safe-file-sharing-for-journalists',
];

const compare = [
  '/compare/privacy-toolbox-vs-metadata2go',
  '/compare/privacy-toolbox-vs-jimpl',
  '/compare/privacy-toolbox-vs-smallpdf',
  '/compare/privacy-toolbox-vs-ilovepdf',
  '/compare/privacy-toolbox-vs-pdf24',
];

const glossary = [
  '/glossary/exif',
  '/glossary/xmp',
  '/glossary/iptc',
  '/glossary/gps-metadata',
  '/glossary/pdf-metadata',
  '/glossary/document-inspector',
  '/glossary/tracked-changes',
  '/glossary/content-credentials',
  '/glossary/c2pa',
  '/glossary/file-sanitization',
  '/glossary/metadata-verification',
];

export default function sitemap() {
  const base = siteConfig.url;
  return [
    '',
    '/tools',
    '/security',
    '/pricing',
    '/about',
    '/contact',
    '/privacy',
    '/terms',
    '/blog',
    '/clean-file-before-sharing',
    ...tools.map((tool) => `/tools/${tool.slug}`),
    ...tools.map((tool) => `/tools/${tool.slug}/how-it-works`),
    ...useCases,
    ...compare,
    ...glossary,
  ].map((url) => ({ url: base + url, lastModified: new Date('2026-05-23') }));
}
