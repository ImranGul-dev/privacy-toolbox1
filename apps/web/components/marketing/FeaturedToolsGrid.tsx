'use client';

import Link from 'next/link';
import type { ElementType } from 'react';
import { useMemo, useState } from 'react';
import {
  ArrowRight,
  FileCheck2,
  FileImage,
  FileSearch,
  FileText,
  MapPinOff,
  Search,
  ShieldCheck,
  Sparkles,
} from 'lucide-react';
import { kindLabels, ToolKind, tools } from '@/lib/seo/tools';

const categories: Array<'all' | ToolKind> = ['all', 'image', 'pdf', 'office', 'media', 'archive', 'verify', 'ai'];

const iconBySlug: Record<string, ElementType> = {
  'remove-image-metadata': FileImage,
  'remove-exif-data': Sparkles,
  'remove-gps-from-photo': MapPinOff,
  'remove-pdf-metadata': FileText,
  'pdf-privacy-scanner': FileSearch,
  'remove-docx-metadata': FileCheck2,
  'verify-file-metadata': ShieldCheck,
  'remove-video-metadata': FileText,
  'remove-audio-metadata': FileText,
  'remove-pdf-hidden-data': FileText,
  'pdf-redaction-checker': FileText,
  'docx-hidden-data-scanner': FileCheck2,
  'xlsx-hidden-data-scanner': FileCheck2,
  'pptx-remove-notes-hidden-slides': FileCheck2,
  'zip-privacy-scanner': FileCheck2,
  'detect-content-credentials': Sparkles,
};

export function FeaturedToolsGrid({ compact = false }: { compact?: boolean }) {
  const [category, setCategory] = useState<'all' | ToolKind>('all');
  const [query, setQuery] = useState('');

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();

    return tools.filter((tool) => {
      const matchesCategory = category === 'all' || tool.kind === category;
      const matchesSearch =
        !q || `${tool.title} ${tool.desc} ${tool.formats}`.toLowerCase().includes(q);

      return matchesCategory && matchesSearch;
    });
  }, [category, query]);

  return (
    <div className="animate-fade-up">
      <div className="mb-7 flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div
          className="flex gap-2 overflow-x-auto pb-1 scrollbar-thin"
          role="tablist"
          aria-label="Tool categories"
        >
          {categories.map((cat) => (
            <button
              key={cat}
              type="button"
              onClick={() => setCategory(cat)}
              className={
                cat === category
                  ? 'btn btn-primary h-10 w-auto whitespace-nowrap px-4 text-xs'
                  : 'btn btn-secondary h-10 w-auto whitespace-nowrap px-4 text-xs'
              }
              aria-pressed={cat === category}
            >
              {cat === 'all' ? 'All' : kindLabels[cat]}
            </button>
          ))}
        </div>

        <label className="relative w-full max-w-md">
          <span className="sr-only">Search tools</span>
          <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-soft" />
          <input
            className="input pl-11"
            placeholder="Search tools..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
        </label>
      </div>

      <div
        className={
          compact
            ? 'grid items-stretch gap-4 sm:grid-cols-2 lg:grid-cols-3'
            : 'grid items-stretch gap-5 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4'
        }
      >
        {filtered.map((tool, index) => {
          const Icon = iconBySlug[tool.slug] || ShieldCheck;

          return (
            <Link
              key={tool.slug}
              href={`/tools/${tool.slug}`}
              className="tool-card group animate-soft-pop"
              style={{ animationDelay: `${Math.min(index * 45, 240)}ms` }}
            >
              <div className="tool-card-top">
                <span className="tool-card-icon">
                  <Icon className="h-5 w-5" />
                </span>

                {tool.badge && <span className="badge badge-blue">{tool.badge}</span>}
              </div>

              <div className="tool-card-body">
                <div className="tool-card-category">
                  <span className="badge">{kindLabels[tool.kind]}</span>
                </div>

                <h3 className="tool-card-title">{tool.shortTitle}</h3>

                <p className="tool-card-desc">{tool.desc}</p>
              </div>

              <div className="tool-card-footer">
                <span className="tool-card-formats">{tool.formats}</span>

                <span className="tool-card-action">
                  Use tool
                  <ArrowRight className="h-4 w-4 transition group-hover:translate-x-1" />
                </span>
              </div>
            </Link>
          );
        })}
      </div>

      {filtered.length === 0 && (
        <div className="card p-8 text-center text-subtle">
          No tools match your search. Try PDF, image, GPS, or verify.
        </div>
      )}
    </div>
  );
}
