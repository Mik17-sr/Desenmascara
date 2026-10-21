"use client";

import { useEffect, useState } from "react";

/** Re-renders every few seconds so "hace 2 min" labels keep moving. */
export function useNow(everyMs = 10_000): number {
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), everyMs);
    return () => clearInterval(timer);
  }, [everyMs]);
  return now;
}
