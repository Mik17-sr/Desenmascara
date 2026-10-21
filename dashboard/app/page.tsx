"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import {
  Activity, AlertTriangle, Close, ImageIcon, Megaphone, Message, Mic, Phone, ShieldCheck,
} from "@/components/icons";
import { Card, Empty, GrowBar, Kpi, LevelPill, LiveDot, Notice, PageHeader, Skeleton } from "@/components/ui";
import { api, type Radar } from "@/lib/api";
import { ago, LEVELS, n, plural } from "@/lib/format";
import { useLive } from "@/lib/useLive";
import { useNow } from "@/lib/useNow";

type Toast = { id: string; title: string; text: string };
const TIPO_ICON = { mensaje: Message, captura: ImageIcon, voz: Mic, numero: Phone, llamada: Phone, compra: ShieldCheck } as const;
const CANAL: Record<string, string> = { telegram: "Telegram", dashboard: "Dashboard", api: "API" };
const TIPO: Record<string, string> = { mensaje: "Mensaje", captura: "Captura", voz: "Nota de voz", numero: "Número", llamada: "Llamada Verificada", compra: "Antes de pagar" };

export default function RadarPage() {
  const load = useCallback(() => api<Radar>("/dashboard/radar"), []);
  const { data, error, updatedAt } = useLive(load);
  const now = useNow(5000);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const seen = useRef<Set<string> | null>(null);

  useEffect(() => {
    if (!data) return;
    if (seen.current === null) {
      seen.current = new Set(data.actividad.map((a) => a.id)); // no toasts for what was already there
      return;
    }
    const fresh = data.actividad.filter((a) => !seen.current!.has(a.id));
    fresh.forEach((a) => seen.current!.add(a.id));
    const alerts = fresh.filter((a) => a.nivel === "high").map((a) => ({
      id: a.id, title: `ALTO RIESGO · ${a.puntaje}/100`, text: `${a.modalidad ?? "Posible estafa"} · ${TIPO[a.tipo] ?? a.tipo} por ${CANAL[a.canal] ?? a.canal}`,
    }));
    if (alerts.length) setToasts((t) => [...alerts, ...t].slice(0, 3));
  }, [data]);

  useEffect(() => {
    if (!toasts.length) return;
    const timer = setTimeout(() => setToasts((t) => t.slice(0, -1)), 6000);
    return () => clearTimeout(timer);
  }, [toasts]);

  const change = data && data.verificaciones_ayer
    ? Math.round(((data.verificaciones_hoy - data.verificaciones_ayer) / data.verificaciones_ayer) * 100) : null;
  const maxTipo = Math.max(1, ...(data?.tipos_de_estafa.map((t) => t.total) ?? [1]));
  const peak = data?.reportes_por_hora.reduce((best, h) => (h.total > best.total ? h : best), { hora: 0, total: 0 });
  const seconds = updatedAt ? Math.max(0, Math.round((now - updatedAt) / 1000)) : null;

  return (
    <div>
      <PageHeader
        title="Radar de campañas"
        subtitle="Colombia · hoy, en vivo"
        actions={<>
          <span className="text-xs text-muted">{seconds === null ? "Cargando…" : seconds < 5 ? "Actualizado ahora" : `Actualizado hace ${seconds} s`}</span>
          <Link href="/verificar" className="inline-flex items-center gap-1.5 rounded-lg bg-brand px-3.5 py-2 text-sm font-semibold text-white shadow-sm transition hover:brightness-110">
            + Verificar un mensaje
          </Link>
        </>}
      />

      <div className="space-y-4">
        {error && <Notice>{error}</Notice>}
        {data?.alerta && (
          <div className="pulse-alert rise flex flex-wrap items-center gap-x-2 gap-y-1 rounded-xl border border-risk-high/40 bg-risk-high-bg px-4 py-2.5 text-sm text-risk-high">
            <AlertTriangle width={16} height={16} className="shrink-0" />
            <span className="font-bold">Campaña en aumento:</span>
            <span className="min-w-0 truncate">{data.alerta.campana}</span>
            <span className="tabular">· {n(data.alerta.reportes_hoy)} reportes · {n(data.alerta.ultima_hora)} en la última hora · alerta emitida</span>
          </div>
        )}

        <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
          <Kpi label="Verificaciones hoy" value={data?.verificaciones_hoy ?? 0} loading={!data}
               delta={change} note={change === null ? "sin datos de ayer" : "vs. ayer"} />
          <Kpi label="Alto riesgo" value={data?.alto_riesgo_pct ?? 0} suffix=" %" tone="high" loading={!data}
               note={data ? plural(data.alto_riesgo_total, "mensaje", "mensajes") : undefined} />
          <Kpi label="Llamadas reportadas" value={data?.llamadas_reportadas ?? 0} loading={!data} note="por número o nota de voz" />
          <Kpi label="Llamadas verificadas" value={data?.llamadas_verificadas ?? 0} tone="brand" loading={!data} note="confirmadas con la entidad" />
          <Kpi label="Campañas activas" value={data?.campanas_activas ?? 0} loading={!data} note="últimas 24 horas" />
          <Kpi label="Tiempo de respuesta" value={data?.tiempo_respuesta_s ?? 0} decimals={1} suffix=" s" loading={!data} note="promedio · meta < 8 s" />
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          <Card title="Tipos de estafa reportados hoy" icon={AlertTriangle}>
            {!data ? <Skeleton className="h-48" /> : data.tipos_de_estafa.length ? (
              <ul className="space-y-3.5">
                {data.tipos_de_estafa.slice(0, 6).map((t) => (
                  <li key={t.tipo} className="grid grid-cols-[minmax(0,11.5rem)_1fr_2.5rem] items-center gap-3 text-sm">
                    <span className="truncate" title={t.tipo}>{t.tipo}</span>
                    <div className="h-2.5 overflow-hidden rounded-full bg-surface-2"><GrowBar percent={(t.total / maxTipo) * 100} className="bg-brand" /></div>
                    <span className="tabular text-right font-semibold">{n(t.total)}</span>
                  </li>
                ))}
              </ul>
            ) : <Empty icon={ShieldCheck}>Todavía no hay estafas reportadas hoy.</Empty>}
          </Card>

          <Card title="Reportes por hora" icon={Activity}
                action={peak && peak.total > 0 && <span className="text-xs text-muted">pico: {peak.hora}:00</span>}>
            <div className="h-full min-h-52">
              {data ? (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={data.reportes_por_hora} margin={{ top: 8, right: 8, left: -18, bottom: 0 }}>
                    <defs>
                      <linearGradient id="fillBrand" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="var(--brand)" stopOpacity={0.35} />
                        <stop offset="100%" stopColor="var(--brand)" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="var(--line)" strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="hora" tick={{ fontSize: 11, fill: "var(--muted)" }} interval={2} tickFormatter={(h) => `${h}h`} axisLine={false} tickLine={false} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: "var(--muted)" }} axisLine={false} tickLine={false} />
                    <Tooltip formatter={(v) => [`${v} verificaciones`, ""]} labelFormatter={(h) => `${h}:00 – ${h}:59`}
                             contentStyle={{ background: "var(--surface)", border: "1px solid var(--line)", borderRadius: 12, color: "var(--ink)" }} />
                    <Area type="monotone" dataKey="total" stroke="var(--brand)" strokeWidth={2.5} fill="url(#fillBrand)" animationDuration={900} />
                  </AreaChart>
                </ResponsiveContainer>
              ) : <Skeleton className="h-full w-full" />}
            </div>
          </Card>

          <Card title="Campañas activas" icon={Megaphone} action={data && <span className="text-xs text-muted">{data.campanas.length}</span>}>
            {!data ? <Skeleton className="h-48" /> : data.campanas.length ? (
              <ul className="space-y-2.5">
                {data.campanas.slice(0, 3).map((c, i) => {
                  const hot = i === 0 && !!data.alerta;
                  return (
                    <li key={c.id} className={`rounded-xl border px-3.5 py-2.5 transition hover:shadow-card ${hot ? "border-risk-high/40 bg-risk-high-bg" : "border-line bg-surface-2"}`}>
                      <div className="line-clamp-2 text-sm font-semibold" title={c.nombre}>{c.nombre}</div>
                      <div className={`mt-0.5 flex items-center gap-1.5 text-xs ${hot ? "text-risk-high" : "text-muted"}`}>
                        {hot && <LiveDot tone="high" />}{plural(c.reportes, "reporte", "reportes")} · último {ago(c.ultimo)}
                      </div>
                    </li>
                  );
                })}
              </ul>
            ) : <Empty icon={Megaphone}>Ninguna campaña activa en las últimas 24 horas.</Empty>}
          </Card>
        </div>

        <div className="grid items-start gap-4 lg:grid-cols-3">
          <Card title="Llamada Verificada · últimas consultas" icon={Phone} padded={false}>
            {!data ? <div className="p-5"><Skeleton className="h-24" /></div> : data.llamadas_ultimas.length ? (
              <ul className="divide-y divide-line">
                {data.llamadas_ultimas.map((c) => (
                  <li key={c.cuando + c.entidad} className="flex items-center justify-between gap-3 px-5 py-3 text-sm">
                    <div className="min-w-0">
                      <div className="truncate font-semibold">{c.entidad}</div>
                      <div className="text-xs text-muted">{ago(c.cuando)}</div>
                    </div>
                    <span className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-semibold ${c.real ? "bg-risk-low-bg text-risk-low" : "bg-risk-high-bg text-risk-high"}`}>
                      {c.real ? "● Real · registrada" : "● Falsa · sin registro"}
                    </span>
                  </li>
                ))}
              </ul>
            ) : <Empty icon={Phone}>Nadie ha preguntado todavía por una llamada.</Empty>}
          </Card>

          <Card title="Actividad en vivo" icon={Activity} padded={false} action={<LiveDot />} className="lg:col-span-2">
            {!data ? <div className="space-y-3 p-5">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-12" />)}</div> : data.actividad.length ? (
              <ul className="divide-y divide-line">
                {data.actividad.slice(0, 6).map((a) => {
                  const Icon = TIPO_ICON[a.tipo as keyof typeof TIPO_ICON] ?? Message;
                  return (
                    <li key={a.id} className="slide-in flex gap-3 px-5 py-3">
                      <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-xl ${LEVELS[a.nivel].bg} ${LEVELS[a.nivel].text}`}><Icon width={16} height={16} /></span>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-baseline justify-between gap-2">
                          <span className="truncate text-sm font-medium">{a.modalidad ?? (a.nivel === "low" ? "Sin señales de estafa" : TIPO[a.tipo] ?? a.tipo)}</span>
                          {a.nivel !== "inconclusive" && <span className={`tabular shrink-0 text-sm font-bold ${LEVELS[a.nivel].text}`}>{a.puntaje}</span>}
                        </div>
                        <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-muted">
                          <LevelPill level={a.nivel} />
                          <span>{TIPO[a.tipo] ?? a.tipo} · {CANAL[a.canal] ?? a.canal} · {ago(a.cuando)}</span>
                        </div>
                      </div>
                    </li>
                  );
                })}
              </ul>
            ) : <Empty icon={Activity}>Aún no hay verificaciones.</Empty>}
          </Card>
        </div>
      </div>

      <div className="pointer-events-none fixed bottom-4 right-4 z-50 flex w-[min(92vw,360px)] flex-col gap-2" aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} className="toast-in pointer-events-auto flex items-start gap-3 rounded-2xl border border-risk-high/40 bg-surface p-4 shadow-xl">
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-risk-high text-white"><AlertTriangle width={16} height={16} /></span>
            <div className="min-w-0 flex-1">
              <div className="text-sm font-bold text-risk-high">{t.title}</div>
              <div className="text-xs text-muted">{t.text}</div>
            </div>
            <button onClick={() => setToasts((all) => all.filter((x) => x.id !== t.id))} className="text-muted hover:text-ink" aria-label="Cerrar aviso"><Close width={16} height={16} /></button>
          </div>
        ))}
      </div>
    </div>
  );
}
