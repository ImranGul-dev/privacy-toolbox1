# Tool Plugin System

This project now uses a plugin-style backend so each privacy tool can be added, inspected, and tested independently.

## Backend layout

```txt
apps/api/app/tools/
  base.py              # ToolPlugin base contract
  registry.py          # Registers all active tools
  schemas.py           # Shared report/action schemas
  plugins/             # One file per tool family

apps/api/app/processing/
  images/              # Image scan/clean implementation
  pdf/                 # PDF scan/clean implementation
  office/              # DOCX/XLSX/PPTX scan/clean implementation
  c2pa/                # C2PA detection implementation
```

## Generic API

```txt
GET  /api/tools
GET  /api/tools/{tool_id}
POST /api/tools/{tool_id}/scan
POST /api/tools/{tool_id}/clean
POST /api/tools/{tool_id}/verify
```

The generic worker is:

```txt
apps/api/app/workers/tasks/process_tool_job.py
```

## Admin dashboard

The admin performance API is:

```txt
GET /api/admin/tool-performance
```

The frontend dashboard is:

```txt
apps/web/app/dashboard/page.tsx
apps/web/components/admin/AdminDashboard.tsx
```

It shows dependency availability, tool health, usage count, success rate, average processing time, failed jobs, and recent job errors.

## Adding a new backend tool

1. Add a processing module under `apps/api/app/processing/<family>/`.
2. Add a plugin class under `apps/api/app/tools/plugins/`.
3. Register the plugin in `apps/api/app/tools/registry.py`.
4. Add a frontend registry item in `apps/web/lib/tools/registry.ts`.
5. Add regression tests that scan → clean → scan the output again.

## Report contract

All tools should return this shape:

```json
{
  "risk_score": 0,
  "risk_level": "low",
  "summary": "No removable private metadata found.",
  "categories": [],
  "findings": [],
  "technical_metadata": [],
  "warnings": [],
  "limitations": [],
  "selectable_items": []
}
```

Only `findings` should represent removable private metadata. Normal file structure, filesystem timestamps, image dimensions, PDF producer fields, and package relationships should be reported as `technical_metadata` so cleaned files are not falsely marked unsafe.
