"use client";

import { useEffect, useState } from "react";

import { health } from "@/lib/api";

let asked: Promise<boolean> | null = null;

/** True while scripts/seed_demo.py's fictional data is loaded; the API is asked once per page load. */
export function useDemo(): boolean {
  const [demo, setDemo] = useState(false);
  useEffect(() => {
    asked ??= health().then((h) => !!h.demo).catch(() => false);
    asked.then(setDemo);
  }, []);
  return demo;
}
