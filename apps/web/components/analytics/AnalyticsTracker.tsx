"use client";

import { useEffect, useMemo, useRef } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import { analyticsEvent } from "@/lib/api/client";

function getSessionId() {
  if (typeof window === "undefined") return "";
  const key = "pt_session_id";
  let value = window.sessionStorage.getItem(key);
  if (!value) {
    value = `sess_${Math.random().toString(36).slice(2)}_${Date.now()}`;
    window.sessionStorage.setItem(key, value);
  }
  return value;
}

export function AnalyticsTracker() {
  const pathname = usePathname();
  const params = useSearchParams();
  const startedAt = useRef(Date.now());
  const sessionId = useMemo(getSessionId, []);

  useEffect(() => {
    if (!pathname) return;
    const toolMatch = pathname.match(/^\/tools\/([^/]+)/);
    analyticsEvent({
      event: toolMatch ? "tool_view" : "page_view",
      path: pathname,
      tool_slug: toolMatch?.[1] || "",
      session_id: sessionId,
      referrer: typeof document !== "undefined" ? document.referrer : "",
      utm_source: params.get("utm_source") || "",
      utm_campaign: params.get("utm_campaign") || "",
    });
  }, [pathname, params, sessionId]);

  useEffect(() => {
    const sendEnd = () => {
      const duration = Math.max(1, Math.round((Date.now() - startedAt.current) / 1000));
      analyticsEvent({ event: "session_duration", path: pathname || "", session_id: sessionId, duration_seconds: duration });
    };
    window.addEventListener("pagehide", sendEnd);
    const timer = window.setInterval(sendEnd, 30000);
    return () => {
      window.removeEventListener("pagehide", sendEnd);
      window.clearInterval(timer);
    };
  }, [pathname, sessionId]);

  return null;
}
