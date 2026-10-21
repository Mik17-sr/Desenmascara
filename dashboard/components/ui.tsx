import type { ReactNode } from "react";

import { DETECTIVES, LEVELS, type Level } from "@/lib/format";
import type { Signal } from "@/lib/api";

export function Logo({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true">
      <path d="M10 8h40a8 8 0 0 1 8 8v24a8 8 0 0 1-8 8H26l-12 10v-10h-4a8 8 0 0 1-8-8V16a8 8 0 0 1 8-8z" fill="var(--brand)" />
      <path d="M12 28c4-6 12-6 16-1-2 5-12 7-16 1zM50 28c-4-6-12-6-16-1 2 5 12 7 16 1z" fill="#fff" />
      <circle cx="54" cy="10" r="9" fill="var(--alert)" />
      <rect x="52.6" y="4.5" width="2.8" height="7" rx="1.2" fill="#fff" />
      <circle cx="54" cy="14.6" r="1.6" fill="#fff" />
    </svg>
  );
}

export function Card({ title, note, children, className = "" }: { title?: string; note?: string; children: ReactNode; className?: string }) {
  return (
    <section className={`rounded-xl border border-line bg-surface p-4 sm:p-5 ${className}`}>
      {title && (
        <header className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
          <h2 className="text-lg font-semibold">{title}</h2>
          {note && <span className="text-xs text-muted">{note}</span>}
        </header>
      )}
      {children}
    </section>
  );
}

export function Kpi({ label, value, note, highlight = false, tone }: { label: string; value: string; note?: string; highlight?: boolean; tone?: "high" }) {
  return (
    <div className={`rounded-xl border p-4 ${highlight ? "border-brand/40 bg-mint" : "border-line bg-surface"}`}>
      <div className="text-xs text-muted">{label}</div>
      <div className={`tabular mt-1 text-4xl font-bold ${tone === "high" ? "text-risk-high" : highlight ? "text-brand-ink" : ""}`}>{value}</div>
      {note && <div className="mt-1 text-xs text-muted">{note}</div>}
    </div>
  );
}

export function LiveBadge({ error }: { error?: string | null }) {
  return error ? (
    <span className="rounded-full bg-risk-high-bg px-3 py-1 text-xs font-semibold text-risk-high" title={error}>● SIN CONEXIÓN</span>
  ) : (
    <span className="rounded-full bg-mint px-3 py-1 text-xs font-semibold text-brand-ink">● EN VIVO</span>
  );
}

/** The semáforo never goes alone: dot + word, so it reads without color too. */
export function LevelPill({ level, score, word }: { level: Level; score?: number; word?: string }) {
  const style = LEVELS[level];
  return (
    <span className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-semibold ${style.bg} ${style.text}`}>
      <span className={`h-2 w-2 rounded-full ${style.dot}`} />
      {score !== undefined && <span className="tabular">{score} ·</span>}
      {word ?? style.word}
    </span>
  );
}

export function ScoreBar({ score }: { score: number }) {
  return (
    <div>
      <div className="relative flex h-2.5 overflow-hidden rounded-full">
        <div className="bg-risk-low" style={{ width: "40%" }} />
        <div className="bg-risk-mid" style={{ width: "30%" }} />
        <div className="bg-risk-high" style={{ width: "30%" }} />
      </div>
      <div className="relative h-0">
        <div className="absolute -top-4 h-5 w-1 -translate-x-1/2 rounded bg-ink" style={{ left: `${Math.min(99, Math.max(1, score))}%` }} />
      </div>
      <div className="mt-1.5 flex justify-between text-[11px] text-muted">
        <span>0 · bajo riesgo</span>
        <span>40 · sospechoso</span>
        <span>70 · alto riesgo · 100</span>
      </div>
    </div>
  );
}

/** Rayos X: how many points each review added. The AI stops being a black box. */
export function RayosX({ signals }: { signals: Signal[] }) {
  const max = Math.max(30, ...signals.map((s) => Math.abs(s.points)));
  if (!signals.length) return <p className="text-sm text-muted">Ninguna revisión sumó puntos.</p>;
  return (
    <ul className="space-y-3">
      {signals.map((s) => (
        <li key={s.code + s.label} className="grid grid-cols-[1fr_auto] items-center gap-x-4 gap-y-1 sm:grid-cols-[minmax(0,1fr)_40%_3rem]">
          <div className="min-w-0">
            <div className="text-sm">{s.label}</div>
            <div className="text-[11px] text-muted">{DETECTIVES[s.source] ?? s.source}</div>
          </div>
          <div className="col-span-2 h-2 rounded-full bg-surface-2 sm:col-span-1">
            <div className={`h-2 rounded-full ${s.points < 0 ? "bg-muted" : "bg-brand"}`} style={{ width: `${(Math.abs(s.points) / max) * 100}%` }} />
          </div>
          <div className="tabular row-start-1 text-right text-sm font-semibold sm:row-auto">{s.points > 0 ? `+${s.points}` : s.points}</div>
        </li>
      ))}
    </ul>
  );
}

export function Chip({ children }: { children: ReactNode }) {
  return <span className="rounded-md border border-line bg-surface-2 px-2 py-1 text-xs">{children}</span>;
}

export function Notice({ children }: { children: ReactNode }) {
  return <p className="rounded-lg bg-risk-high-bg px-4 py-3 text-sm text-risk-high">{children}</p>;
}
