"use client";

import { useCallback, useEffect, useState } from "react";

import { setRealtimeStatus, supabase } from "@/lib/supabase";

const SAFETY_POLL_MS = 60_000;

/**
 * Live data without reloading. With Supabase, the database announces every change through
 * Realtime (table eventos_dashboard) and the view asks the API again; without Supabase
 * (local SQLite) it asks every few seconds.
 */
export function useLive<T>(load: () => Promise<T>, pollMs = 3000) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [updatedAt, setUpdatedAt] = useState<number | null>(null);

  const refresh = useCallback(async () => {
    try {
      setData(await load());
      setError(null);
      setUpdatedAt(Date.now());
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo cargar.");
    }
  }, [load]);

  useEffect(() => {
    refresh();
    if (!supabase) {
      const timer = setInterval(refresh, pollMs);
      return () => clearInterval(timer);
    }
    const client = supabase;
    let debounce: ReturnType<typeof setTimeout> | undefined;
    const channel = client
      .channel(`dashboard-${Math.random().toString(36).slice(2)}`)
      .on("postgres_changes", { event: "INSERT", schema: "public", table: "eventos_dashboard" }, () => {
        clearTimeout(debounce);
        debounce = setTimeout(refresh, 400); // a burst of inserts becomes one request
      })
      .subscribe((state) => {
        setRealtimeStatus(state === "SUBSCRIBED" ? "live" : state === "CHANNEL_ERROR" || state === "TIMED_OUT" ? "error" : "connecting");
      });
    const safety = setInterval(refresh, SAFETY_POLL_MS);
    return () => {
      clearTimeout(debounce);
      clearInterval(safety);
      client.removeChannel(channel);
    };
  }, [refresh, pollMs]);

  return { data, error, refresh, updatedAt };
}
