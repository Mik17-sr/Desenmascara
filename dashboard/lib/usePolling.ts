"use client";

import { useCallback, useEffect, useState } from "react";

/** Live without reloading: asks the API again every few seconds (SQLite has no Realtime like Supabase). */
export function usePolling<T>(load: () => Promise<T>, everyMs = 3000) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setData(await load());
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo cargar.");
    }
  }, [load]);

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, everyMs);
    return () => clearInterval(timer);
  }, [refresh, everyMs]);

  return { data, error, refresh };
}
