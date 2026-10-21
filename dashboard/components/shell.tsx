"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";

import { Activity, Building, Close, Cpu, Database, Menu, Radio, Server, ShieldCheck } from "@/components/icons";
import { LiveDot, Logo } from "@/components/ui";
import { health, type Health } from "@/lib/api";
import { supabase, useRealtimeStatus } from "@/lib/supabase";

const NAV = [
  { section: "Monitoreo", items: [{ href: "/", label: "Radar", icon: Activity }, { href: "/verificar", label: "Verificar un mensaje", icon: ShieldCheck }] },
  { section: "Comunidad", items: [{ href: "/banco", label: "Banco de números", icon: Database }] },
  { section: "Entidades", items: [{ href: "/entidad", label: "Panel de la entidad", icon: Building }] },
];
const CLOCK = new Intl.DateTimeFormat("es-CO", { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", second: "2-digit", timeZone: "America/Bogota" });

function isActive(path: string, href: string) {
  return href === "/" ? path === "/" : path.startsWith(href);
}

export function Shell({ children }: { children: ReactNode }) {
  const path = usePathname();
  const [open, setOpen] = useState(false);
  useEffect(() => setOpen(false), [path]);
  const current = NAV.flatMap((s) => s.items).find((i) => isActive(path, i.href));

  return (
    <div className="min-h-screen lg:pl-64">
      <div className={`fixed inset-0 z-40 bg-black/50 transition-opacity lg:hidden ${open ? "opacity-100" : "pointer-events-none opacity-0"}`}
           onClick={() => setOpen(false)} aria-hidden="true" />
      <aside className={`fixed inset-y-0 left-0 z-50 flex w-64 flex-col bg-sidebar text-sidebar-ink transition-transform duration-300 lg:translate-x-0 ${open ? "translate-x-0" : "-translate-x-full"}`}>
        <div className="flex items-center gap-3 px-5 py-5">
          <Logo />
          <div className="min-w-0">
            <div className="text-[17px] font-bold leading-tight">Desen<span className="text-[#2bb5a3]">mascara</span></div>
            <div className="text-[11px] text-sidebar-muted">Plataforma antifraude</div>
          </div>
          <button className="ml-auto rounded-lg p-1.5 text-sidebar-muted hover:bg-white/5 lg:hidden" onClick={() => setOpen(false)} aria-label="Cerrar menú">
            <Close />
          </button>
        </div>
        <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-2">
          {NAV.map((section) => (
            <div key={section.section}>
              <div className="px-3 pb-2 text-[11px] font-semibold uppercase tracking-wider text-sidebar-muted">{section.section}</div>
              <ul className="space-y-1">
                {section.items.map(({ href, label, icon: Icon }) => {
                  const active = isActive(path, href);
                  return (
                    <li key={href}>
                      <Link href={href} aria-current={active ? "page" : undefined}
                            className={`group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-medium transition ${active ? "bg-[#2bb5a3]/15 text-white" : "text-sidebar-muted hover:bg-white/5 hover:text-white"}`}>
                        <Icon className={active ? "text-[#2bb5a3]" : ""} />
                        {label}
                        {active && <span className="ml-auto h-5 w-1 rounded-full bg-[#2bb5a3]" />}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}
        </nav>
        <SystemStatus />
      </aside>

      <header className="sticky top-0 z-30 border-b border-line bg-surface/85 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-[1400px] items-center gap-3 px-4 sm:px-6 lg:px-8">
          <button className="rounded-lg p-2 hover:bg-surface-2 lg:hidden" onClick={() => setOpen(true)} aria-label="Abrir menú">
            <Menu />
          </button>
          <div className="flex min-w-0 items-center gap-2 text-sm">
            <span className="hidden text-muted sm:inline">Desenmascara</span>
            <span className="hidden text-muted sm:inline">/</span>
            <span className="truncate font-semibold">{current?.label ?? "Dashboard"}</span>
          </div>
          <div className="ml-auto flex items-center gap-3">
            <Clock />
            <LiveMode />
            {path !== "/verificar" && (
              <Link href="/verificar" className="hidden rounded-xl bg-brand px-3.5 py-2 text-sm font-semibold text-white shadow-sm transition hover:brightness-110 md:inline-flex">
                Verificar mensaje
              </Link>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1400px] px-4 py-6 sm:px-6 lg:px-8 lg:py-8">{children}</main>
    </div>
  );
}

function Clock() {
  const [now, setNow] = useState<Date | null>(null);
  useEffect(() => {
    setNow(new Date());
    const timer = setInterval(() => setNow(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);
  return <span className="tabular hidden text-xs text-muted xl:inline">{now ? `${CLOCK.format(now)} · Colombia` : ""}</span>;
}

function LiveMode() {
  const realtime = useRealtimeStatus();
  const label = !supabase ? "En vivo · cada 3 s" : realtime === "live" ? "En vivo · Realtime" : realtime === "error" ? "Realtime sin conexión" : "Conectando…";
  return (
    <span className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${realtime === "error" ? "bg-risk-high-bg text-risk-high" : "bg-brand-soft text-brand-ink"}`}>
      <LiveDot tone={realtime === "error" ? "high" : "brand"} />
      <span className="hidden sm:inline">{label}</span>
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
    { icon: Server, label: "API", ok: !!up, text: up ? "En línea" : state === "down" ? "Sin conexión" : "…" },
    { icon: Database, label: "Base de datos", ok: up && state.base_de_datos === "ok", text: up ? (state.base_de_datos === "ok" ? (supabase ? "Supabase" : "Lista") : "Falla") : "—" },
    { icon: Cpu, label: "IA local", ok: up && state.ia === "ok", text: up ? (state.ia === "ok" ? "Lista" : "No disponible") : "—" },
    { icon: Radio, label: "Tiempo real", ok: !supabase || realtime === "live", text: !supabase ? "Cada 3 s" : realtime === "live" ? "Realtime" : realtime === "error" ? "Sin conexión" : "Conectando" },
  ];
  return (
    <div className="border-t border-sidebar-line px-5 py-4">
      <div className="mb-3 text-[11px] font-semibold uppercase tracking-wider text-sidebar-muted">Estado del sistema</div>
      <ul className="space-y-2.5 text-xs">
        {rows.map(({ icon: Icon, label, ok, text }) => (
          <li key={label} className="flex items-center gap-2.5">
            <Icon width={15} height={15} className="text-sidebar-muted" />
            <span className="text-sidebar-ink/90">{label}</span>
            <span className={`ml-auto inline-flex items-center gap-1.5 ${ok ? "text-[#2bb5a3]" : "text-[#ef7b70]"}`}>
              <span className="h-1.5 w-1.5 rounded-full bg-current" />{text}
            </span>
          </li>
        ))}
      </ul>
      <div className="mt-4 text-[10px] text-sidebar-muted">v{up ? state.version : "—"} · datos de prueba ficticios</div>
    </div>
  );
}
