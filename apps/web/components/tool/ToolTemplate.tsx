"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  AlertCircle,
  CheckCircle2,
  FileText,
  Loader2,
  ShieldCheck,
  Trash2,
} from "lucide-react";
import { uploadFile, createJob, getJob, Job } from "@/lib/api/client";
import { createToolJob } from "@/lib/tools/api";
import type { ToolAction, ToolInfo } from "@/lib/tools/types";
import { UploadDropzone } from "@/components/upload/UploadDropzone";
import { ProgressStepper } from "@/components/tool/ProgressStepper";
import { ProgressBar } from "@/components/tool/ProgressBar";
import { LimitationNotice } from "@/components/tool/LimitationNotice";
import { RiskSummaryCard } from "@/components/result/RiskSummaryCard";
import { DownloadPanel } from "@/components/result/DownloadPanel";
import { DeletionTimer } from "@/components/result/DeletionTimer";
import { FAQAccordion } from "@/components/tool/FAQAccordion";
import { BeforeAfterDiff } from "@/components/result/BeforeAfterDiff";

type Finding = {
  id: string;
  label: string;
  detail: string;
  raw: any;
  removable?: boolean;
};

type SelectedUpload =
  | File
  | { name: string; size: number; preloaded?: boolean };

function scanEndpointFor(endpoint: string) {
  if (endpoint.includes("clean-image") || endpoint.includes("remove-gps"))
    return "/api/jobs/scan-image";
  if (endpoint.includes("clean-pdf")) return "/api/jobs/scan-pdf";
  if (endpoint.includes("clean-office")) return "/api/jobs/verify";
  return endpoint;
}

function canRemoveAfterScan(endpoint: string) {
  return !endpoint.includes("scan-pdf") && !endpoint.includes("verify");
}

function acceptedListFor(tool?: ToolInfo, fallback?: string) {
  if (tool?.acceptedFileTypes?.length) return tool.acceptedFileTypes.join(",");
  return fallback || ".jpg,.jpeg,.png,.webp,.tif,.tiff,.pdf,.docx,.xlsx,.pptx";
}

function extractFindings(report: any): Finding[] {
  const rawItems = report?.selectable_items || report?.findings || [];
  if (!Array.isArray(rawItems)) return [];

  return rawItems.slice(0, 10).map((item: any, idx: number) => {
    const raw = item?.raw || item;
    const label =
      item?.label ||
      (item?.category && item?.key
        ? `${item.category}: ${item.key}`
        : item?.category ||
          item?.key ||
          item?.type ||
          `Metadata item ${idx + 1}`);
    const detail =
      item?.detail ||
      item?.value_preview ||
      item?.description ||
      "Detected metadata category";
    return {
      id: item?.id || `${label}-${idx}`,
      label,
      detail,
      raw,
      removable: item?.removable ?? raw?.removable ?? true,
    };
  });
}

function niceStatus(job?: Job | null) {
  if (!job) return "Upload";
  if (job.status === "completed") return job.current_step || "Completed";
  if (job.status === "failed") return "Failed";
  return job.current_step || "Processing";
}

export function ToolTemplate({
  tool,
  title,
  desc,
  endpoint,
  formats,
  faq,
}: {
  tool?: ToolInfo;
  title?: string;
  desc?: string;
  endpoint?: string;
  formats?: string;
  faq?: { q: string; a: string }[];
}) {
  const resolvedTitle = tool?.title || title || "Privacy tool";
  const resolvedDesc =
    tool?.desc ||
    desc ||
    "Scan, clean, and verify hidden file data before sharing.";
  const resolvedEndpoint = tool?.endpoint || endpoint || "";
  const resolvedFormats = tool?.formats || formats;
  const resolvedFaq = tool?.faq || faq;
  const apiToolId = tool?.apiToolId || tool?.slug || "";
  const scanAction = (tool?.scanAction || "scan") as ToolAction;
  const cleanAction = (tool?.cleanAction || "clean") as ToolAction;
  const [selectedFile, setSelectedFile] = useState<SelectedUpload | null>(null);
  const [fileId, setFileId] = useState("");
  const [scanJob, setScanJob] = useState<Job | null>(null);
  const [cleanJob, setCleanJob] = useState<Job | null>(null);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [selectionInitializedFor, setSelectionInitializedFor] = useState("");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const accepts = useMemo(() => acceptedListFor(tool), [tool]);
  const resultsRef = useRef<HTMLDivElement | null>(null);
  const preloadAppliedRef = useRef(false);

  const scanEndpoint = useMemo(
    () => scanEndpointFor(resolvedEndpoint),
    [resolvedEndpoint],
  );
  const removeEnabled = tool
    ? tool.supportsClean
    : canRemoveAfterScan(resolvedEndpoint);
  const isScanOnly = !removeEnabled;
  const activeJob = cleanJob || scanJob;
  const scanCompleted = scanJob?.status === "completed";
  const cleanCompleted = cleanJob?.status === "completed";
  const isFailed = activeJob?.status === "failed";
  const findings = useMemo(() => {
    const items = extractFindings(scanJob?.report);
    if (
      tool?.slug !== "remove-gps-from-photo" &&
      !resolvedEndpoint.includes("remove-gps")
    )
      return items;
    const gpsItems = items.filter(
      (item) =>
        `${item.label} ${item.detail}`.toLowerCase().includes("gps") ||
        `${item.label} ${item.detail}`.toLowerCase().includes("location"),
    );
    return gpsItems.length ? gpsItems : items;
  }, [tool?.slug, resolvedEndpoint, scanJob?.report]);
  const removableFindings = findings.filter(
    (finding) => finding.removable !== false,
  );
  const hasFindings = findings.length > 0;
  const allSelected =
    removableFindings.length > 0 &&
    selectedIds.length === removableFindings.length;

  useEffect(() => {
    if (preloadAppliedRef.current || typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const preloadedFileId = params.get("file_id");
    if (!preloadedFileId) return;

    const preloadedName = params.get("file_name") || "uploaded-file";
    const parsedSize = Number(params.get("file_size") || 0);
    preloadAppliedRef.current = true;
    setFileId(preloadedFileId);
    setSelectedFile({
      name: preloadedName,
      size: Number.isFinite(parsedSize) ? parsedSize : 0,
      preloaded: true,
    });
    setErr("");
  }, []);

  useEffect(() => {
    if (
      scanJob?.status === "completed" &&
      scanJob.id !== selectionInitializedFor
    ) {
      const ids = removableFindings.map((item) => item.id);
      setSelectedIds(ids);
      setSelectionInitializedFor(scanJob.id);
    }
  }, [removableFindings, scanJob, selectionInitializedFor]);

  useEffect(() => {
    const shouldScroll =
      cleanJob?.status === "completed" || cleanJob?.status === "failed";
    if (shouldScroll) {
      window.setTimeout(
        () =>
          resultsRef.current?.scrollIntoView({
            behavior: "smooth",
            block: "start",
          }),
        150,
      );
    }
  }, [cleanJob?.status]);

  function resetForFile(file: SelectedUpload | null) {
    setSelectedFile(file);
    setFileId("");
    setScanJob(null);
    setCleanJob(null);
    setSelectedIds([]);
    setSelectionInitializedFor("");
    setErr("");
  }

  async function pollJob(jobId: string, setter: (job: Job) => void) {
    return new Promise<void>((resolve) => {
      const timer = window.setInterval(async () => {
        try {
          const next = await getJob(jobId);
          setter(next);
          if (["completed", "failed", "expired"].includes(next.status)) {
            window.clearInterval(timer);
            resolve();
          }
        } catch (e: any) {
          window.clearInterval(timer);
          setErr(e.message || "Job polling failed");
          resolve();
        }
      }, 1100);
    });
  }

  async function ensureUploaded(file: SelectedUpload) {
    if (fileId) return fileId;
    if (!(file instanceof File)) {
      throw new Error(
        "The selected file is no longer available. Please choose it again.",
      );
    }
    const up = await uploadFile(file);
    setFileId(up.file_id);
    return up.file_id;
  }

  async function createAction(
    action: ToolAction,
    uploadedId: string,
    options: any = {},
  ) {
    if (apiToolId) return createToolJob(apiToolId, action, uploadedId, options);
    const fallbackPath =
      action === "scan" || action === "verify"
        ? scanEndpoint
        : resolvedEndpoint;
    return createJob(fallbackPath, uploadedId, options);
  }

  async function startScan() {
    if (!selectedFile || busy) return;

    try {
      setErr("");
      setBusy(true);
      setCleanJob(null);
      setSelectedIds([]);
      setSelectionInitializedFor("");
      const optimisticJob = {
        id: "local-scan",
        status: "queued",
        tool_type: scanEndpoint,
        input_filename: selectedFile.name,
        file_size: selectedFile.size,
        progress: 2,
        current_step: "Upload",
        report: {},
      } as Job;
      setScanJob(optimisticJob);

      const uploadedId = await ensureUploaded(selectedFile);
      const created = await createAction(scanAction, uploadedId);
      setScanJob(created);
      await pollJob(created.id, setScanJob);
    } catch (e: any) {
      const message = e.message || "Upload or scan failed";
      setErr(message);
      if (selectedFile) {
        setScanJob({
          id: "local-scan-failed",
          status: "failed",
          tool_type: scanEndpoint,
          input_filename: selectedFile.name,
          file_size: selectedFile.size,
          progress: 100,
          current_step: "Failed",
          report: { risk_score: 0, risk_level: "low", summary: "Scan failed before processing." },
          error_message: message,
        } as Job);
      }
    } finally {
      setBusy(false);
    }
  }

  async function removeSelectedData() {
    if (
      !selectedFile ||
      !fileId ||
      busy ||
      !removeEnabled ||
      removableFindings.length === 0
    )
      return;

    try {
      setErr("");
      setBusy(true);
      const optimisticJob = {
        id: "local-clean",
        status: "queued",
        tool_type: resolvedEndpoint,
        input_filename: selectedFile.name,
        file_size: selectedFile.size,
        progress: 2,
        current_step: "Preparing cleanup",
        report: {},
      } as Job;
      setCleanJob(optimisticJob);
      const selectedFindings = removableFindings
        .filter((finding) => selectedIds.includes(finding.id))
        .map((finding) => finding.raw);
      const created = await createAction(cleanAction, fileId, {
        selected_items: selectedFindings,
      });
      setCleanJob(created);
      await pollJob(created.id, setCleanJob);
    } catch (e: any) {
      const message = e.message || "Removal failed";
      setErr(message);
      if (selectedFile) {
        setCleanJob({
          id: "local-clean-failed",
          status: "failed",
          tool_type: resolvedEndpoint,
          input_filename: selectedFile.name,
          file_size: selectedFile.size,
          progress: 100,
          current_step: "Failed",
          report: { risk_score: scanJob?.report?.risk_score || 0, risk_level: scanJob?.report?.risk_level || "low", summary: "Removal failed before completion." },
          error_message: message,
        } as Job);
      }
    } finally {
      setBusy(false);
    }
  }

  function toggleFinding(id: string) {
    setSelectedIds((current) =>
      current.includes(id)
        ? current.filter((item) => item !== id)
        : [...current, id],
    );
  }

  function toggleAll() {
    setSelectedIds(allSelected ? [] : removableFindings.map((item) => item.id));
  }

  return (
    <main>
      <section className="relative overflow-hidden py-12 sm:py-16 lg:py-20">
        <div className="absolute right-0 top-0 -z-10 h-72 w-72 rounded-full gradient-orb" />
        <div className="site-container">
          <div className="grid gap-8 lg:grid-cols-[.9fr_1.1fr] lg:items-start">
            <div className="animate-fade-up">
              <span className="eyebrow">
                <ShieldCheck className="h-3.5 w-3.5" /> Upload-first privacy
                tool
              </span>
              <h1 className="heading-xl mt-5">{resolvedTitle}</h1>
              <p className="lead mt-5">{resolvedDesc}</p>
              <div className="mt-6 flex flex-wrap gap-2">
                <span className="badge badge-green">
                  <CheckCircle2 className="h-3.5 w-3.5" /> Verification included
                </span>
                <span className="badge">
                  <FileText className="h-3.5 w-3.5" />{" "}
                  {resolvedFormats || "Common file types"}
                </span>
                <span className="badge badge-blue">
                  Auto-delete after 10 minutes
                </span>
              </div>
              <div className="mt-6 flex flex-wrap gap-3">
                {tool?.slug && (
                  <Link href={`/tools/${tool.slug}/how-it-works`} className="btn btn-secondary sm:w-auto">
                    How this tool works
                  </Link>
                )}
              </div>
              <div className="mt-5">
                <LimitationNotice />
              </div>
            </div>

            <div className="space-y-5 animate-soft-pop">
              <UploadDropzone
                onFile={resetForFile}
                accept={accepts}
                selectedFile={selectedFile}
                onClear={() => resetForFile(null)}
              />

              <div className="card p-4 sm:p-5">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div>
                    <h2 className="text-lg font-bold text-ink">
                      Start scanning
                    </h2>
                    <p className="mt-1 text-sm leading-6 text-subtle">
                      {isScanOnly
                        ? "Scan the file and review detected metadata without changing it."
                        : "First scan the file, then review the detected data before removal."}
                    </p>
                  </div>
                  <button
                    className="btn btn-primary sm:w-auto"
                    type="button"
                    onClick={startScan}
                    disabled={!selectedFile || busy}
                  >
                    {busy && !cleanJob ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <ShieldCheck className="h-4 w-4" />
                    )}
                    Start scanning
                  </button>
                </div>
              </div>

              {activeJob && (
                <div className="space-y-4" ref={resultsRef}>
                  <ProgressStepper step={niceStatus(activeJob)} />
                  <ProgressBar value={activeJob.progress} />

                  {scanCompleted && !cleanJob && (
                    <ScanFindingsPanel
                      findings={findings}
                      selectedIds={selectedIds}
                      allSelected={allSelected}
                      removeEnabled={removeEnabled}
                      isScanOnly={isScanOnly}
                      busy={busy}
                      onToggle={toggleFinding}
                      onToggleAll={toggleAll}
                      onRemove={removeSelectedData}
                    />
                  )}

                  {cleanJob && (
                    <div className="card p-5 animate-soft-pop">
                      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                        <div>
                          <span className="badge badge-green">
                            Cleanup result
                          </span>
                          <h2 className="mt-3 text-xl font-bold text-ink">
                            Cleaned file verification
                          </h2>
                          <p className="mt-2 text-sm leading-6 text-subtle">
                            Your cleaned file was re-scanned after cleanup.
                            Download is available only when verification
                            completes.
                          </p>
                        </div>
                        {cleanJob.expires_at && (
                          <DeletionTimer expiresAt={cleanJob.expires_at} />
                        )}
                      </div>
                      <div className="mt-5 space-y-5">
                        <RiskSummaryCard report={cleanJob.report} />
                        {cleanCompleted && (
                          <DownloadPanel token={cleanJob.download_token} />
                        )}
                      </div>
                    </div>
                  )}

                  {isFailed && (
                    <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm font-semibold text-danger">
                      <AlertCircle className="mr-2 inline h-4 w-4" />
                      {activeJob.error_message || "Processing failed."}
                    </div>
                  )}
                </div>
              )}

              {err && (
                <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-sm font-semibold text-danger">
                  <AlertCircle className="mr-2 inline h-4 w-4" />
                  {err}
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {(scanJob || cleanJob) && (
        <section className="section-pad bg-slate-50/80">
          <div className="site-container space-y-5">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <span className="eyebrow">Detailed report</span>
                <h2 className="heading-lg mt-3">
                  {cleanJob
                    ? "Cleaning verification details"
                    : "Scan report details"}
                </h2>
              </div>
              {activeJob?.expires_at && (
                <DeletionTimer expiresAt={activeJob.expires_at} />
              )}
            </div>
            <RiskSummaryCard report={activeJob?.report} />
            {activeJob?.report && (
              <BeforeAfterDiff
                report={activeJob.report}
                mode={cleanJob ? "clean" : "scan"}
              />
            )}
          </div>
        </section>
      )}

      <section className="section-pad">
        <div className="site-container">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="heading-lg">Tool questions</h2>
            <p className="lead mx-auto mt-3">
              Clear answers before you upload private files.
            </p>
          </div>
          <div className="mt-10">
            <FAQAccordion items={resolvedFaq} />
          </div>
        </div>
      </section>
    </main>
  );
}

function ScanFindingsPanel({
  findings,
  selectedIds,
  allSelected,
  removeEnabled,
  isScanOnly,
  busy,
  onToggle,
  onToggleAll,
  onRemove,
}: {
  findings: Finding[];
  selectedIds: string[];
  allSelected: boolean;
  removeEnabled: boolean;
  isScanOnly: boolean;
  busy: boolean;
  onToggle: (id: string) => void;
  onToggleAll: () => void;
  onRemove: () => void;
}) {
  const removableFindings = findings.filter(
    (finding) => finding.removable !== false,
  );
  return (
    <div className="card p-5 animate-soft-pop">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <span className="badge badge-blue">Scan result</span>
          <h2 className="mt-3 text-xl font-bold text-ink">
            {isScanOnly ? "Detected metadata" : "Detected data before removal"}
          </h2>
          <p className="mt-2 text-sm leading-6 text-subtle">
            {isScanOnly
              ? "Review detected metadata and technical indicators. This tool does not modify the file."
              : "Review the top detected metadata categories. Select all or choose specific data before starting removal."}
          </p>
        </div>
        {!isScanOnly && removableFindings.length > 0 && (
          <button
            type="button"
            className="btn btn-secondary sm:w-auto"
            onClick={onToggleAll}
            disabled={busy}
          >
            {allSelected ? "Clear all" : "Select all"}
          </button>
        )}
      </div>

      <div className="mt-5 space-y-3">
        {findings.length > 0 ? (
          findings.map((finding) => (
            <label
              key={finding.id}
              className="flex cursor-pointer items-start gap-3 rounded-2xl border border-line bg-slate-50 p-4 transition hover:border-brand/30 hover:bg-blue-50/40"
            >
              {!isScanOnly && finding.removable !== false && (
                <input
                  type="checkbox"
                  className="mt-1 h-4 w-4 rounded border-line text-brand focus:ring-brand"
                  checked={selectedIds.includes(finding.id)}
                  onChange={() => onToggle(finding.id)}
                />
              )}
              <span className="min-w-0 flex-1">
                <span
                  className="block text-sm font-bold text-ink"
                  title={finding.label}
                >
                  {finding.label}
                </span>
                <span className="mt-1 block break-words text-xs leading-5 text-subtle">
                  {finding.detail}
                </span>
              </span>
            </label>
          ))
        ) : (
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-sm leading-6 text-emerald-900">
            No removable private metadata categories were found by the current
            scanner.
          </div>
        )}
      </div>

      <div className="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-xs leading-5 text-soft">
          Showing up to 10 detected metadata items for quick review.
        </p>
        {removeEnabled ? (
          <button
            className="btn btn-primary sm:w-auto"
            type="button"
            onClick={onRemove}
            disabled={
              busy || removableFindings.length === 0 || selectedIds.length === 0
            }
          >
            {busy ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Trash2 className="h-4 w-4" />
            )}
            {removableFindings.length > 0
              ? "Remove selected data"
              : "Nothing to remove"}
          </button>
        ) : (
          <span className="badge badge-green">Scan-only report ready</span>
        )}
      </div>
    </div>
  );
}
