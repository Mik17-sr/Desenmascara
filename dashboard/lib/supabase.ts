"use client";

import { createClient, type SupabaseClient } from "@supabase/supabase-js";
import { useSyncExternalStore } from "react";

// Only the public key: with RLS it can read the anonymous event table and views, nothing else.
// New Supabase projects call it "publishable" (sb_publishable_...); older ones, "anon".
const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
const anonKey = process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ?? process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

export const supabase: SupabaseClient | null = url && anonKey ? createClient(url, anonKey) : null;

export type RealtimeStatus = "off" | "connecting" | "live" | "error";

let status: RealtimeStatus = supabase ? "connecting" : "off";
const listeners = new Set<() => void>();

export function setRealtimeStatus(next: RealtimeStatus) {
  if (next === status) return;
  status = next;
  listeners.forEach((listener) => listener());
}

export function useRealtimeStatus(): RealtimeStatus {
  return useSyncExternalStore(
    (listener) => { listeners.add(listener); return () => listeners.delete(listener); },
    () => status,
    () => (supabase ? "connecting" : "off"),
  );
}
