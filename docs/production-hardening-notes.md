# Production Hardening Notes

Implemented in this build:

- Image scanner now separates private embedded metadata from filesystem/technical values.
- GPS tool now scans only GPS/location metadata so non-location data does not trigger false GPS warnings.
- Image cleaner verifies output and fails the job if private metadata remains.
- PDF cleaner removes DocumentInfo and XMP metadata and saves with `fix_metadata_version=False` to avoid pikepdf regenerating XMP compatibility metadata.
- PDF scanner separates low-risk technical producer/creator values from private findings.
- Office scanner/cleaner handles DOCX/XLSX/PPTX package properties, comments, people/customXml/revision/external/printer/notes parts, content type cleanup, relationship cleanup, and Word revision markup cleanup.
- C2PA detector uses the official c2patool command syntax and fails clearly if c2patool is missing.
- Generic tool metrics were added for the admin dashboard.

Before public launch:

- Protect `/dashboard` and `/api/admin/*` with real admin authentication.
- Add regression fixtures for every supported file type.
- Run browser tests at 320px, 375px, 390px, 414px, 768px, and desktop widths.
- Run load testing against API + worker concurrency with realistic files.


## Docker base image note for c2patool

The API and worker Dockerfiles use `python:3.12-slim-trixie` because recent official `c2patool` Linux binaries require newer GLIBC symbols than Debian Bookworm provides. Using Bookworm can fail during Docker build with errors such as `GLIBC_2.38 not found` or `GLIBC_2.39 not found`.

## 2026 cleanup hardening update

This version fixes two production issues found during browser testing:

1. Long filenames now preserve their extension during upload, output generation, and browser download. The download token stores a user-facing filename separately from the internal job-scoped output path.
2. Image scan results now classify ExifTool results into privacy findings versus technical image/file values. Findings show real field names such as `GPS latitude`, `Creator tool`, `Camera model`, or `Content Credentials / C2PA metadata` instead of a repeated generic fallback label.

Implementation notes:

- The backend uses ExifTool `-j -a -G1 -s` output for image metadata grouping and tag names.
- Normal filesystem data, image dimensions, MIME type, color profiles, and other compatibility fields are technical diagnostics and do not trigger a privacy risk score.
- C2PA/JUMBF/content-credentials markers are reported separately so generated images with provenance blocks are understandable to users.
- Cleaned downloads are returned with a stable attachment filename through the download-token metadata and FastAPI `FileResponse`.
