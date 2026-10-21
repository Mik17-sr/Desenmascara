"use client";

import type { ComponentType, ReactNode, SVGProps } from "react";

import { TrendDown, TrendUp } from "@/components/icons";
import type { Signal } from "@/lib/api";
import { DETECTIVES, LEVELS, n, type Level } from "@/lib/format";
import { useCountUp } from "@/lib/useCountUp";

type IconType = ComponentType<SVGProps<SVGSVGElement>>;

export function Logo({ size = 30 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" aria-hidden="true">
      <path d="M10 8h40a8 8 0 0 1 8 8v24a8 8 0 0 1-8 8H26l-12 10v-10h-4a8 8 0 0 1-8-8V16a8 8 0 0 1 8-8z" fill="#0e9f8e" />
      <path d="M12 28c4-6 12-6 16-1-2 5-12 7-16 1zM50 28c-4-6-12-6-16-1 2 5 12 7 16 1z" fill="#fff" />
      <circle cx="54" cy="10" r="9" fill="#e8951c" />
      <rect x="52.6" y="4.5" width="2.8" height="7" rx="1.2" fill="#fff" />
      <circle cx="54" cy="14.6" r="1.6" fill="#fff" />
    </svg>
  );
}

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: string; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
      <div className="flex min-w-0 flex-wrap items-baseline gap-x-3 gap-y-1">
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">{title}</h1>
        {subtitle && <p className="text-sm text-muted">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

export function Card({ title, icon: Icon, action, children, className = "", padded = true }: {
  title?: string; icon?: IconType; action?: ReactNode; children: ReactNode; className?: string; padded?: boolean;
}) {
  return (
    <section className={`rise flex min-w-0 flex-col rounded-2xl border border-line bg-surface shadow-card ${className}`}>
      {title && (
        <header className="flex items-center justify-between gap-3 border-b border-line px-5 py-3.5">
          <h2 className="flex items-center gap-2 text-sm font-semibold">
            {Icon && <Icon className="text-brand-ink" />}
            {title}
          </h2>
          {action}
        </header>
      )}
      <div className={`flex-1 ${padded ? "p-5" : ""}`}>{children}</div>
    </section>
  );
}

function Sparkline({ values }: { values: number[] }) {
  if (values.length < 2 || Math.max(...values) === 0) return null;
  const max = Math.max(...values);
  const points = values.map((v, i) => `${(i / (values.length - 1)) * 100},${28 - (v / max) * 26}`).join(" ");
  return (
    <svg viewBox="0 0 100 30" preserveAspectRatio="none" className="h-8 w-full" aria-hidden="true">
      <polyline points={`0,30 ${points} 100,30`} fill="var(--brand)" fillOpacity="0.12" stroke="none" />
      <polyline points={points} fill="none" stroke="var(--brand)" strokeWidth="1.6" vectorEffect="non-scaling-stroke" />
    </svg>
  );
}

/** A compact figure tile, as in the guide's mock-up. tone="brand" fills the tile with the brand's tint. */
export function Kpi({ label, value, suffix = "", decimals = 0, note, delta, tone, spark, loading }: {
  label: string; value: number; suffix?: string; decimals?: number; note?: string;
  delta?: number | null; tone?: "high" | "brand"; spark?: number[]; loading?: boolean;
}) {
  const shown = useCountUp(value);
  const color = tone === "high" ? "text-risk-high" : tone === "brand" ? "text-brand-ink" : "";
  const tile = tone === "brand" ? "border-brand/30 bg-brand-soft" : "border-line bg-surface-2";
  return (
    <div className={`rise flex min-w-0 flex-col rounded-xl border p-4 transition hover:-translate-y-0.5 hover:shadow-card ${tile}`}>
      <span className="text-xs font-medium text-muted">{label}</span>
      {loading ? <div className="skeleton mt-2 h-8 w-20" /> : (
        <div className={`tabular mt-1 text-2xl font-bold tracking-tight sm:text-[28px] ${color}`}>
          {shown.toLocaleString("es-CO", { maximumFractionDigits: decimals, minimumFractionDigits: decimals })}{suffix}
        </div>
      )}
      <div className="mt-1 flex items-center gap-2 text-xs text-muted">
        {delta !== undefined && delta !== null && (
          <span className={`inline-flex items-center gap-1 rounded-full px-1.5 py-0.5 font-semibold ${delta >= 0 ? "bg-brand-soft text-brand-ink" : "bg-risk-high-bg text-risk-high"}`}>
            {delta >= 0 ? <TrendUp width={12} height={12} /> : <TrendDown width={12} height={12} />}
            {delta >= 0 ? "+" : ""}{delta} %
          </span>
        )}
        {note}
      </div>
      {spark && <div className="mt-auto pt-3"><Sparkline values={spark} /></div>}
    </div>
  );
}

export function LiveDot({ tone = "brand" }: { tone?: "brand" | "high" | "muted" }) {
  const color = tone === "high" ? "text-risk-high" : tone === "muted" ? "text-muted" : "text-brand";
  return <span className={`live-dot relative inline-block h-2 w-2 rounded-full bg-current ${color}`} />;
}

/** The semáforo never goes alone: dot + word, so it reads without color too. */
export function LevelPill({ level, score, word }: { level: Level; score?: number; word?: string }) {
  const style = LEVELS[level];
  return (
    <span className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-semibold ${style.bg} ${style.text}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${style.dot}`} />
      {score !== undefined && <span className="tabular">{score} ·</span>}
      {word ?? style.word}
    </span>
  );
}

const ARC = Math.PI * 80;

/** Semicircular gauge with the semáforo bands (0-39, 40-69, 70-100) and an animated value arc. */
export function ScoreGauge({ score, level }: { score: number; level: Level }) {
  const shown = useCountUp(score, 900);
  const style = LEVELS[level];
  const stroke = level === "high" ? "var(--risk-high)" : level === "medium" ? "var(--risk-mid)" : level === "low" ? "var(--risk-low)" : "var(--muted)";
  const path = "M20 100 A80 80 0 0 1 180 100";
  return (
    <div className="relative mx-auto w-full max-w-[260px]">
      <svg viewBox="0 0 200 112" className="w-full" role="img" aria-label={`Puntaje ${score} de 100, ${style.word}`}>
        <path d={path} fill="none" stroke="var(--risk-low)" strokeOpacity="0.18" strokeWidth="16" strokeDasharray={`${ARC * 0.4} ${ARC}`} />
        <path d={path} fill="none" stroke="var(--risk-mid)" strokeOpacity="0.18" strokeWidth="16" strokeDasharray={`0 ${ARC * 0.4} ${ARC * 0.3} ${ARC}`} />
        <path d={path} fill="none" stroke="var(--risk-high)" strokeOpacity="0.18" strokeWidth="16" strokeDasharray={`0 ${ARC * 0.7} ${ARC * 0.3} ${ARC}`} />
        <path d={path} fill="none" stroke={stroke} strokeWidth="16" strokeLinecap="round"
              strokeDasharray={`${(ARC * Math.max(0.5, shown)) / 100} ${ARC}`} />
      </svg>
      <div className="absolute inset-x-0 bottom-0 text-center">
        <div className={`tabular text-5xl font-bold leading-none ${style.text}`}>{Math.round(shown)}</div>
        <div className="mt-1 text-xs text-muted">de 100</div>
      </div>
    </div>
  );
}

/** Rayos X: how many points each review added. The AI stops being a black box. */
export function RayosX({ signals }: { signals: Signal[] }) {
  const max = Math.max(30, ...signals.map((s) => Math.abs(s.points)));
  if (!signals.length) return <p className="text-sm text-muted">Ninguna revisión sumó puntos.</p>;
  return (
    <ul className="space-y-4">
      {signals.map((s, i) => (
        <li key={s.code + s.label} className="slide-in" style={{ animationDelay: `${i * 70}ms` }}>
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <div className="text-sm font-medium">{s.label}</div>
              <div className="text-[11px] uppercase tracking-wide text-muted">{DETECTIVES[s.source] ?? s.source}</div>
            </div>
            <div className={`tabular shrink-0 text-sm font-bold ${s.points < 0 ? "text-risk-low" : ""}`}>{s.points > 0 ? `+${s.points}` : s.points}</div>
          </div>
          <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-surface-2">
            <GrowBar percent={(Math.abs(s.points) / max) * 100} className={s.points < 0 ? "bg-risk-low" : "bg-brand"} />
          </div>
        </li>
      ))}
    </ul>
  );
}

export function GrowBar({ percent, className }: { percent: number; className: string }) {
  const width = useCountUp(percent, 800);
  return <div className={`h-full rounded-full ${className}`} style={{ width: `${width}%` }} />;
}

export function Chip({ children }: { children: ReactNode }) {
  return <span className="rounded-lg border border-line bg-surface-2 px-2.5 py-1 text-xs font-medium">{children}</span>;
}

export function Notice({ children }: { children: ReactNode }) {
  return <p className="rise rounded-xl border border-risk-high/30 bg-risk-high-bg px-4 py-3 text-sm text-risk-high">{children}</p>;
}

export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`skeleton ${className}`} />;
}

export function Empty({ icon: Icon, children }: { icon?: IconType; children: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-2 py-8 text-center text-sm text-muted">
      {Icon && <span className="grid h-10 w-10 place-items-center rounded-full bg-surface-2"><Icon /></span>}
      {children}
    </div>
  );
}

export function Button({ children, variant = "primary", className = "", ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "ghost" }) {
  const styles = variant === "primary"
    ? "bg-brand text-white shadow-sm hover:brightness-110 disabled:opacity-50"
    : "border border-line bg-surface hover:bg-surface-2 disabled:opacity-50";
  return (
    <button className={`inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition active:scale-[0.98] ${styles} ${className}`} {...props}>
      {children}
    </button>
  );
}

export { n };
