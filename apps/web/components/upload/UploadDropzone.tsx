"use client";

import { useCallback, useRef, useState } from "react";
import { FileUp, ShieldCheck, UploadCloud, X } from "lucide-react";

type SelectedUpload = { name: string; size?: number } | File;


function acceptLabels(accept?: string) {
  const values = (accept || '.jpg,.jpeg,.png,.webp,.pdf,.docx,.xlsx,.pptx')
    .split(',')
    .map((v) => v.trim().replace(/^\./, '').toUpperCase())
    .filter(Boolean);
  const unique = Array.from(new Set(values.map((v) => (v === 'JPEG' ? 'JPG' : v))));
  return unique.slice(0, 8);
}

function formatBytes(bytes?: number) {
  if (!bytes) return "";
  const mb = bytes / 1024 / 1024;
  return mb >= 1 ? `${mb.toFixed(2)} MB` : `${(bytes / 1024).toFixed(1)} KB`;
}

export function UploadDropzone({
  onFile,
  accept,
  selectedFile,
  onClear,
}: {
  onFile: (f: File) => void;
  accept?: string;
  selectedFile?: SelectedUpload | null;
  onClear?: () => void;
}) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement | null>(null);

  const handleFile = useCallback(
    (file?: File) => {
      if (!file) return;
      onFile(file);
    },
    [onFile],
  );

  return (
    <div
      className={`rounded-3xl border-2 border-dashed bg-white p-5 text-center shadow-card transition sm:p-8 ${dragging ? "border-brand bg-blue-50/60" : "border-blue-200 hover:border-brand/60"}`}
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        handleFile(e.dataTransfer.files?.[0]);
      }}
    >
      <input
        ref={inputRef}
        type="file"
        className="sr-only"
        accept={accept}
        onChange={(e) => handleFile(e.target.files?.[0])}
        aria-label="Choose file to upload"
      />
      <span className="mx-auto grid h-14 w-14 place-items-center rounded-3xl bg-gradient-to-br from-blue-50 to-emerald-50 text-brand sm:h-16 sm:w-16">
        <UploadCloud className="h-7 w-7" />
      </span>
      <h3 className="mt-5 text-xl font-bold tracking-tight text-ink sm:text-2xl">
        Drop your file here
      </h3>
      <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-subtle">
        Your file will be processed for this job only. Temporary files are
        scheduled to auto-delete after 10 minutes.
      </p>
      <button
        type="button"
        className="btn btn-primary mt-6 sm:w-auto"
        onClick={() => inputRef.current?.click()}
      >
        <FileUp className="h-4 w-4" /> Choose file
      </button>
      <div className="mt-5 flex flex-wrap justify-center gap-2">
        {acceptLabels(accept).map((label) => (
          <span key={label} className="badge">{label}</span>
        ))}
      </div>
      {selectedFile && (
        <div className="mx-auto mt-5 flex max-w-full items-center gap-3 rounded-2xl border border-line bg-slate-50 p-3 text-left text-sm text-ink sm:max-w-md">
          <ShieldCheck className="h-4 w-4 shrink-0 text-teal" />
          <div className="min-w-0 flex-1">
            <p className="truncate font-semibold" title={selectedFile.name}>
              {selectedFile.name}
            </p>
            <p className="text-xs text-soft">
              {formatBytes(selectedFile.size)}
            </p>
          </div>
          {onClear && (
            <button
              type="button"
              className="grid h-8 w-8 shrink-0 place-items-center rounded-full border border-line bg-white text-soft hover:text-ink"
              onClick={onClear}
              aria-label="Remove selected file"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
      )}
    </div>
  );
}
