# Deep Research Implementation Notes

This build applies the first wave of recommendations from `Privacy Toolbox Deep Research Report.pdf`.

## Added tool families

- Remove Video Metadata (`/tools/remove-video-metadata`)
- Remove Audio Metadata (`/tools/remove-audio-metadata`)
- Remove PDF Hidden Data (`/tools/remove-pdf-hidden-data`)
- PDF Redaction Checker (`/tools/pdf-redaction-checker`)
- DOCX Hidden Data Scanner (`/tools/docx-hidden-data-scanner`)
- Excel Hidden Data Scanner (`/tools/xlsx-hidden-data-scanner`)
- PowerPoint Notes and Hidden Slides Cleaner (`/tools/pptx-remove-notes-hidden-slides`)
- ZIP Privacy Scanner (`/tools/zip-privacy-scanner`)

## Backend additions

- `apps/api/app/processing/media/*` for ffprobe/FFmpeg media scan-clean-verify.
- `apps/api/app/processing/archives/*` for safe ZIP scan mode.
- `apps/api/app/processing/pdf/redaction.py` for scan-only redaction risk checks.
- New tool plugins in `apps/api/app/tools/plugins/`.
- Registry updates in `apps/api/app/tools/registry.py`.

## SEO/content additions

- AI/search crawler allowances in `apps/web/app/robots.ts`.
- Expanded sitemap in `apps/web/app/sitemap.ts`.
- WebApplication JSON-LD in `apps/web/app/layout.tsx`.
- New use-case pages under `/use-cases/[slug]`.
- New glossary pages under `/glossary/[slug]`.
- Improved comparison page template under `/compare/[slug]`.

## Important limitations

- ZIP is scan-only in this build.
- PDF redaction checker is scan-only and does not provide a legal guarantee.
- Media cleaning uses FFmpeg stream copy with `-map_metadata -1`; some container technical fields remain because they are required for playback.
- AI remains a communication/content opportunity only; OpenAI is not used for metadata detection/removal.
