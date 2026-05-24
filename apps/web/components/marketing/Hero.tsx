"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import type { ChangeEvent, DragEvent, ReactNode } from "react";
import { useRef, useState } from "react";
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  Clock3,
  FileArchive,
  FileImage,
  FileText,
  Loader2,
  Lock,
  ShieldCheck,
  UploadCloud,
  X,
} from "lucide-react";
import { uploadFile } from "@/lib/api/client";

const supportedFormats = "JPG, PNG, WebP, PDF, DOCX, XLSX, PPTX, MP4, MP3, ZIP";
const accept = ".jpg,.jpeg,.png,.webp,.tif,.tiff,.pdf,.docx,.xlsx,.pptx,.mp4,.mov,.m4v,.avi,.mkv,.webm,.mp3,.m4a,.wav,.flac,.ogg,.zip";

type StarterTone = "safe" | "warn" | "info" | "error";

type RecommendedTool = {
  slug: string;
  label: string;
  status: string;
  tone: StarterTone;
  icon: ReactNode;
};

function formatBytes(bytes?: number) {
  if (!bytes) return "";
  const mb = bytes / 1024 / 1024;
  return mb >= 1 ? `${mb.toFixed(2)} MB` : `${(bytes / 1024).toFixed(1)} KB`;
}

function extensionOf(fileName: string) {
  const dot = fileName.lastIndexOf(".");
  return dot >= 0 ? fileName.slice(dot + 1).toLowerCase() : "";
}

function recommendTool(file: File): RecommendedTool | null {
  const ext = extensionOf(file.name);
  if (["jpg", "jpeg", "png", "webp", "tif", "tiff"].includes(ext)) {
    return {
      slug: "remove-image-metadata",
      label: "Image privacy tool",
      status: "Ready to scan",
      tone: "info",
      icon: <FileImage className="h-4 w-4" />,
    };
  }
  if (ext === "pdf") {
    return {
      slug: "remove-pdf-metadata",
      label: "PDF metadata remover",
      status: "Ready to scan",
      tone: "info",
      icon: <FileText className="h-4 w-4" />,
    };
  }
  if (["docx", "xlsx"].includes(ext)) {
    return {
      slug: "remove-docx-metadata",
      label: "Office privacy tool",
      status: "Ready to scan",
      tone: "info",
      icon: <FileArchive className="h-4 w-4" />,
    };
  }
  if (ext === "pptx") {
    return { slug: "pptx-remove-notes-hidden-slides", label: "PowerPoint notes cleaner", status: "Ready to scan", tone: "info", icon: <FileArchive className="h-4 w-4" /> };
  }
  if (["mp4", "mov", "m4v", "avi", "mkv", "webm"].includes(ext)) {
    return { slug: "remove-video-metadata", label: "Video privacy tool", status: "Ready to scan", tone: "info", icon: <FileText className="h-4 w-4" /> };
  }
  if (["mp3", "m4a", "wav", "flac", "ogg"].includes(ext)) {
    return { slug: "remove-audio-metadata", label: "Audio privacy tool", status: "Ready to scan", tone: "info", icon: <FileText className="h-4 w-4" /> };
  }
  if (ext === "zip") {
    return { slug: "zip-privacy-scanner", label: "ZIP privacy scanner", status: "Ready to scan", tone: "info", icon: <FileArchive className="h-4 w-4" /> };
  }
  return null;
}

export function Hero() {
  return (
    <section className="relative overflow-hidden py-16 sm:py-20 lg:py-24">
      <div className="absolute left-1/2 top-10 -z-10 h-72 w-72 -translate-x-1/2 rounded-full gradient-orb" />
      <div className="site-container grid items-center gap-12 lg:grid-cols-[1.05fr_.95fr]">
        <div>
          <span className="eyebrow">
            <ShieldCheck className="h-3.5 w-3.5" /> Privacy-first file utility
          </span>
          <h1 className="heading-xl mt-6">
            Remove hidden file data before you share.
          </h1>
          <p className="lead mt-6">
            Scan photos, PDFs, Office files, videos, audio, and ZIPs for hidden metadata, clean
            removable private data where supported, and verify the result before downloading.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <a href="#home-file-starter" className="btn btn-primary">
              Start with a file <ArrowRight className="h-4 w-4" />
            </a>
            <Link href="/tools" className="btn btn-secondary">
              Explore privacy tools
            </Link>
          </div>
          <div className="mt-6 flex flex-wrap gap-2">
            {[
              "No raw file-content logs",
              "Temporary files auto-delete",
              "Verification included",
            ].map((text) => (
              <span key={text} className="badge badge-green">
                <CheckCircle2 className="h-3.5 w-3.5" /> {text}
              </span>
            ))}
          </div>
        </div>
        <UploadPreviewCard />
      </div>
    </section>
  );
}

export function UploadPreviewCard() {
  const router = useRouter();
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [dragging, setDragging] = useState(false);
  const [fileName, setFileName] = useState("");
  const [fileSize, setFileSize] = useState(0);
  const [fileId, setFileId] = useState("");
  const [recommended, setRecommended] = useState<RecommendedTool | null>(null);
  const [status, setStatus] = useState<
    "idle" | "uploading" | "ready" | "unsupported" | "error"
  >("idle");
  const [error, setError] = useState("");

  async function handleFile(file?: File) {
    if (!file) return;

    const rec = recommendTool(file);
    setFileName(file.name);
    setFileSize(file.size);
    setRecommended(rec);
    setFileId("");
    setError("");

    if (!rec) {
      setStatus("unsupported");
      setError(
        "This file type is not supported yet. Please use JPG, PNG, WebP, PDF, DOCX, XLSX, PPTX, MP4, MP3, or ZIP.",
      );
      return;
    }

    try {
      setStatus("uploading");
      const uploaded = await uploadFile(file);
      setFileId(uploaded.file_id);
      setFileName(uploaded.filename || file.name);
      setFileSize(uploaded.file_size || file.size);
      setStatus("ready");
    } catch (e: any) {
      setStatus("error");
      setError(
        e?.message ||
          "Upload failed. Please try again from the full tool page.",
      );
    }
  }

  function openRecommendedTool() {
    if (!recommended || !fileId) return;
    const params = new URLSearchParams({
      file_id: fileId,
      file_name: fileName,
      file_size: String(fileSize || 0),
      source: "home",
    });
    router.push(`/tools/${recommended.slug}?${params.toString()}`);
  }

  function clearSelection() {
    setFileName("");
    setFileSize(0);
    setFileId("");
    setRecommended(null);
    setStatus("idle");
    setError("");
    if (inputRef.current) inputRef.current.value = "";
  }

  function onInputChange(event: ChangeEvent<HTMLInputElement>) {
    handleFile(event.target.files?.[0]);
  }

  function onDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setDragging(false);
    handleFile(event.dataTransfer.files?.[0]);
  }

  const selectedStatus =
    status === "uploading"
      ? "Uploading"
      : status === "ready"
        ? "Ready to scan"
        : status === "unsupported"
          ? "Unsupported"
          : status === "error"
            ? "Upload failed"
            : "";
  const selectedTone: StarterTone =
    status === "ready"
      ? "safe"
      : status === "unsupported" || status === "error"
        ? "error"
        : "info";

  return (
    <div
      id="home-file-starter"
      className="relative mx-auto w-full max-w-xl animate-float scroll-mt-28"
    >
      <div className="absolute -right-4 -top-4 h-24 w-24 rounded-3xl bg-violet/15" />
      <div className="absolute -bottom-4 -left-4 h-24 w-24 rounded-full bg-teal/15" />
      <div className="glass-card relative p-4 sm:p-6">
        <div
          className={`rounded-3xl border-2 border-dashed bg-white p-6 text-center transition sm:p-8 ${dragging ? "border-brand bg-blue-50/70" : "border-blue-200 hover:border-brand/60"}`}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
        >
          <input
            ref={inputRef}
            type="file"
            className="sr-only"
            accept={accept}
            onChange={onInputChange}
            aria-label="Choose privacy file"
          />
          <span className="mx-auto grid h-12 w-12 place-items-center rounded-2xl bg-blue-50 text-brand">
            <UploadCloud className="h-6 w-6" />
          </span>
          <h2 className="mt-4 text-xl font-bold tracking-tight text-ink">
            Drag & drop your file
          </h2>
          <p className="mt-2 text-sm text-subtle">{supportedFormats}</p>

          <div className="mt-6 space-y-3 text-left">
            {fileName ? (
              <PreviewRow
                icon={recommended?.icon || <FileText className="h-4 w-4" />}
                name={fileName}
                sublabel={formatBytes(fileSize)}
                status={selectedStatus}
                tone={selectedTone}
                onClear={clearSelection}
              />
            ) : (
              <>
                <PreviewRow
                  icon={<FileText className="h-4 w-4" />}
                  name="client-file.pdf"
                  status="Example: risks found"
                  tone="warn"
                />
                <PreviewRow
                  icon={<FileImage className="h-4 w-4" />}
                  name="photo.jpg"
                  status="Example: GPS removed"
                  tone="safe"
                />
                <PreviewRow
                  icon={<FileArchive className="h-4 w-4" />}
                  name="resume.docx"
                  status="Example: verified"
                  tone="safe"
                />
              </>
            )}
          </div>

          {error && (
            <div className="mt-4 rounded-2xl border border-red-200 bg-red-50 p-3 text-left text-sm leading-6 text-danger">
              <AlertCircle className="mr-2 inline h-4 w-4" />
              {error}
            </div>
          )}

          <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:justify-center">
            <button
              type="button"
              className="btn btn-primary sm:w-auto"
              onClick={() => inputRef.current?.click()}
              disabled={status === "uploading"}
            >
              {status === "uploading" ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <UploadCloud className="h-4 w-4" />
              )}
              {fileName ? "Choose another file" : "Choose file"}
            </button>
            {status === "ready" && recommended && (
              <button
                type="button"
                className="btn btn-primary sm:w-auto"
                onClick={openRecommendedTool}
              >
                Open {recommended.label} <ArrowRight className="h-4 w-4" />
              </button>
            )}
          </div>

          {status === "ready" && recommended && (
            <p className="mx-auto mt-4 max-w-md text-xs leading-5 text-soft">
              File uploaded temporarily. Open the recommended tool to scan it
              immediately; files are scheduled to auto-delete after 10 minutes.
            </p>
          )}
        </div>
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          <MiniTrust icon={<Lock className="h-4 w-4" />} label="Private job" />
          <MiniTrust
            icon={<Clock3 className="h-4 w-4" />}
            label="Auto-delete"
          />
          <MiniTrust
            icon={<ShieldCheck className="h-4 w-4" />}
            label="Verify after"
          />
        </div>
      </div>
    </div>
  );
}

function PreviewRow({
  icon,
  name,
  status,
  tone,
  sublabel,
  onClear,
}: {
  icon: ReactNode;
  name: string;
  status: string;
  tone: StarterTone;
  sublabel?: string;
  onClear?: () => void;
}) {
  const badgeClass =
    tone === "safe"
      ? "badge badge-green"
      : tone === "warn"
        ? "badge badge-amber"
        : tone === "error"
          ? "badge border-red-100 bg-red-50 text-danger"
          : "badge badge-blue";
  return (
    <div className="flex items-center gap-3 rounded-2xl border border-line bg-slate-50 px-4 py-3">
      <span className="shrink-0 text-brand">{icon}</span>
      <span className="min-w-0 flex-1">
        <span
          className="block truncate text-sm font-semibold text-ink"
          title={name}
        >
          {name}
        </span>
        {sublabel && (
          <span className="mt-0.5 block text-xs text-soft">{sublabel}</span>
        )}
      </span>
      <span className={badgeClass}>{status}</span>
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
  );
}

function MiniTrust({ icon, label }: { icon: ReactNode; label: string }) {
  return (
    <div className="flex items-center justify-center gap-2 rounded-2xl bg-slate-50 px-3 py-2 text-xs font-bold text-subtle">
      <span className="text-teal">{icon}</span>
      {label}
    </div>
  );
}
