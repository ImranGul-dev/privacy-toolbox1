'use client';

import { useState } from 'react';
import { ChevronDown } from 'lucide-react';

const defaultFaqs = [
  { q: 'Is my file private?', a: 'Files are processed for the selected job. The app avoids raw file-content logs and temporary files are scheduled for automatic cleanup.' },
  { q: 'Do you remove every metadata field?', a: 'The tools target common removable metadata categories and show a verification report so you can review the result.' },
  { q: 'When are files deleted?', a: 'The default project setting schedules temporary files, outputs, and short-lived job files for deletion after 10 minutes.' },
  { q: 'Can I verify the cleaned file?', a: 'Yes. Verification is part of the cleaning flow, and you can also use the standalone verification tool.' },
  { q: 'Can I select specific data to remove?', a: 'Yes. After scanning, select all detected data or choose specific categories before starting removal.' },
];

export function FAQAccordion({ items = defaultFaqs }: { items?: { q: string; a: string }[] }) {
  const [open, setOpen] = useState<number | null>(0);

  return (
    <div className="mx-auto w-full max-w-3xl space-y-3" id="faq">
      {items.map((item, idx) => {
        const isOpen = open === idx;
        return (
          <div key={item.q} className="overflow-hidden rounded-2xl border border-line bg-white shadow-sm transition hover:shadow-card">
            <button
              type="button"
              className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left text-sm font-bold text-ink"
              onClick={() => setOpen(isOpen ? null : idx)}
              aria-expanded={isOpen}
            >
              <span>{item.q}</span>
              <ChevronDown className={`h-4 w-4 shrink-0 text-soft transition duration-300 ${isOpen ? 'rotate-180' : ''}`} />
            </button>
            <div className={`grid transition-all duration-300 ease-out ${isOpen ? 'grid-rows-[1fr] opacity-100' : 'grid-rows-[0fr] opacity-0'}`}>
              <div className="overflow-hidden">
                <p className="border-t border-line px-5 py-4 text-sm leading-6 text-subtle">{item.a}</p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
