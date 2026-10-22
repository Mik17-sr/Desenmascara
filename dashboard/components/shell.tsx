"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { Building, Moon, Sun } from "@/components/icons";
import { LiveDot, Logo } from "@/components/ui";
import { health, type Health } from "@/lib/api";
import { supabase, useRealtimeStatus } from "@/lib/supabase";

// Top navigation as in the guide's mock-up: one white bar, the views as tabs, entities apart.
const TABS = [
  { href: "/", label: "Radar", short: "Radar" },
  { href: "/verificar", label: "Verificar un mensaje", short: "Verificar" },
  { href: "/banco", label: "Banco de números", short: "Banco de números" },
];
const ENTIDAD = { href: "/entidad", label: "Acceso para entidades", short: "Entidades" };

function isActive(path: string, href: string) {
  return href === "/" ? path === "/" : path.startsWith(href);
}

export function Shell({ children }: { children: ReactNode }) {
  const path = usePathname();
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-30 border-b border-line bg-surface/90 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-[1400px] items-center gap-6 px-4 sm:px-6 lg:px-8">
          <Link href="/" className="flex shrink-0 items-center gap-2.5" aria-label="Desenmascara · inicio">
            <Logo size={28} />
            <span className="leading-none">
              <span className="block text-[15px] font-bold">Desen<span className="text-brand-ink">mascara</span></span>
              <span className="hidden text-[10.5px] text-muted sm:block">bot antiestafas · plataforma</span>
            </span>
          </Link>
          <nav className="hidden h-full items-stretch gap-1 lg:flex" aria-label="Vistas">
            {TABS.map((tab) => <Tab key={tab.href} {...tab} active={isActive(path, tab.href)} />)}
          </nav>
          <div className="ml-auto flex items-center gap-2 sm:gap-3">
            <LiveMode />
            <ThemeToggle />
            <Link href={ENTIDAD.href} aria-current={isActive(path, ENTIDAD.href) ? "page" : undefined}
                  className={`hidden items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-medium transition lg:inline-flex ${isActive(path, ENTIDAD.href) ? "bg-brand-soft text-brand-ink" : "text-muted hover:bg-surface-2 hover:text-ink"}`}>
              <Building width={16} height={16} /> {ENTIDAD.label}
            </Link>
          </div>
        </div>
        <nav className="flex gap-1 overflow-x-auto px-2 sm:px-4 lg:hidden" aria-label="Vistas">
          {[...TABS, ENTIDAD].map((tab) => <Tab key={tab.href} {...tab} label={tab.short} active={isActive(path, tab.href)} />)}
        </nav>
      </header>

      <main className="mx-auto w-full max-w-[1400px] flex-1 px-4 py-6 sm:px-6 lg:px-8">{children}</main>
      <SystemStatus />
    </div>
  );
}

function Tab({ href, label, active }: { href: string; label: string; active: boolean }) {
  return (
    <Link href={href} aria-current={active ? "page" : undefined}
          className={`relative flex shrink-0 items-center whitespace-nowrap px-2.5 py-3 text-sm font-medium transition lg:px-3 lg:py-0 ${active ? "text-brand-ink" : "text-muted hover:text-ink"}`}>
      {label}
      <span className={`absolute inset-x-2 bottom-0 h-0.5 rounded-full bg-brand transition-opacity ${active ? "opacity-100" : "opacity-0"}`} />
    </Link>
  );
}

const THEME_KEY = "desenmascara.tema"; // read before the first paint in app/layout.tsx

function ThemeToggle() {
  const [dark, setDark] = useState(false);
  useEffect(() => setDark(document.documentElement.dataset.theme === "dark"), []);
  function toggle() {
    const next = dark ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    setDark(!dark);
    try { localStorage.setItem(THEME_KEY, next); } catch { /* storage blocked: back to light next visit */ }
  }
  const label = dark ? "Cambiar a modo claro" : "Cambiar a modo oscuro";
  return (
    <button type="button" onClick={toggle} aria-label={label} title={label}
            className="grid h-8 w-8 place-items-center rounded-lg text-muted transition hover:bg-surface-2 hover:text-ink">
      {dark ? <Sun width={17} height={17} /> : <Moon width={17} height={17} />}
    </button>
  );
}

function LiveMode() {
  const realtime = useRealtimeStatus();
  const error = !!supabase && realtime === "error";
  const label = error ? "SIN CONEXIÓN" : !supabase || realtime === "live" ? "EN VIVO" : "CONECTANDO";
  const title = !supabase ? "Se actualiza cada 3 s" : realtime === "live" ? "Supabase Realtime" : undefined;
  return (
    <span title={title} className={`inline-flex items-center gap-2 rounded-full px-2.5 py-1 text-[11px] font-bold tracking-wide ${error ? "bg-risk-high-bg text-risk-high" : "bg-brand-soft text-brand-ink"}`}>
      <LiveDot tone={error ? "high" : "brand"} /> {label}
    </span>
  );
}

function SystemStatus() {
  const [state, setState] = useState<Health | null | "down">(null);
  const realtime = useRealtimeStatus();
  useEffect(() => {
    const check = () => health().then(setState).catch(() => setState("down"));
    check();
    const timer = setInterval(check, 15000);
    return () => clearInterval(timer);
  }, []);
  const up = state && state !== "down";
  const rows = [
    { label: "API", ok: !!up, text: up ? "en línea" : state === "down" ? "sin conexión" : "…" },
    { label: "Base de datos", ok: up && state.base_de_datos === "ok", text: up ? (state.base_de_datos === "ok" ? (supabase ? "Supabase" : "lista") : "falla") : "—" },
    // On the server the AI is off on purpose ("apagada"): the rules answer, so it is a mode, not a failure.
    up && state.ia === "apagada"
      ? { label: "Análisis", ok: true, text: "reglas verificadas" }
      : { label: "IA local", ok: up && state.ia === "ok", text: up ? (state.ia === "ok" ? "lista" : "no disponible") : "—" },
    { label: "Tiempo real", ok: !supabase || realtime === "live", text: !supabase ? "cada 3 s" : realtime === "live" ? "Realtime" : realtime === "error" ? "sin conexión" : "conectando" },
  ];
  return (
    <footer className="border-t border-line bg-surface">
      <div className="mx-auto flex max-w-[1400px] flex-wrap items-center gap-x-5 gap-y-2 px-4 py-3 text-xs text-muted sm:px-6 lg:px-8">
        {rows.map(({ label, ok, text }) => (
          <span key={label} className="inline-flex items-center gap-1.5">
            <span className={`h-1.5 w-1.5 rounded-full ${ok ? "bg-brand" : "bg-risk-high"}`} />
            {label}: <span className={ok ? "text-ink" : "text-risk-high"}>{text}</span>
          </span>
        ))}
        <span className="ml-auto flex items-center gap-3">
          {up && state.demo && <span className="rounded-full bg-risk-mid-bg px-2 py-0.5 font-semibold text-risk-mid-ink">Datos de demostración</span>}
          Desenmascara v{up ? state.version : "—"}
        </span>
      </div>
    </footer>
  );
}
