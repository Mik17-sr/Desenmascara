"use client";

import Link from "next/link";
import { useCallback } from "react";
import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, Kpi, LiveBadge, Notice } from "@/components/ui";
import { api, type Radar } from "@/lib/api";
import { ago, n } from "@/lib/format";
import { usePolling } from "@/lib/usePolling";

export default function RadarPage() {
  const load = useCallback(() => api<Radar>("/dashboard/radar"), []);
  const { data, error } = usePolling(load);

  const change = data && data.verificaciones_ayer
    ? Math.round(((data.verificaciones_hoy - data.verificaciones_ayer) / data.verificaciones_ayer) * 100)
    : null;
  const maxTipo = Math.max(1, ...(data?.tipos_de_estafa.map((t) => t.total) ?? [1]));

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-3xl font-bold">Radar de campañas</h1>
        <span className="text-sm text-muted">Colombia · hoy</span>
        <LiveBadge error={error} />
        <Link href="/verificar" className="ml-auto rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white hover:opacity-90">
          + Verificar un mensaje
        </Link>
      </div>

      {error && <Notice>{error}</Notice>}
      {data?.alerta && (
        <div className="pulse-alert rounded-lg border border-risk-high/40 bg-risk-high-bg px-4 py-3 text-sm text-risk-high">
          <strong>▲ Campaña en aumento:</strong> {data.alerta.campana} · {n(data.alerta.reportes_hoy)} reportes ·{" "}
          {n(data.alerta.ultima_hora)} en la última hora · alerta emitida
        </div>
      )}

      <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
        <Kpi label="Verificaciones hoy" value={data ? n(data.verificaciones_hoy) : "—"}
             note={change === null ? "sin datos de ayer" : `${change >= 0 ? "+" : ""}${change} % vs. ayer`} />
        <Kpi label="Alto riesgo" value={data ? `${data.alto_riesgo_pct} %` : "—"} tone="high"
             note={data ? `${n(data.alto_riesgo_total)} mensajes` : undefined} />
        <Kpi label="Llamadas reportadas" value={data ? n(data.llamadas_reportadas) : "—"} note="por número o nota de voz" />
        <Kpi label="Llamadas verificadas" value={data ? n(data.llamadas_verificadas) : "—"} note="confirmadas con la entidad" highlight />
        <Kpi label="Campañas activas" value={data ? n(data.campanas_activas) : "—"} note="últimas 24 h" />
        <Kpi label="Tiempo de respuesta" value={data ? `${data.tiempo_respuesta_s.toLocaleString("es-CO")} s` : "—"} note="promedio" />
      </div>

      <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-4">
        <Card title="Tipos de estafa reportados hoy">
          {data?.tipos_de_estafa.length ? (
            <ul className="space-y-3">
              {data.tipos_de_estafa.slice(0, 6).map((t) => (
                <li key={t.tipo} className="text-sm">
                  <div className="flex justify-between gap-2"><span>{t.tipo}</span><span className="tabular font-semibold">{n(t.total)}</span></div>
                  <div className="mt-1 h-2 rounded bg-brand" style={{ width: `${(t.total / maxTipo) * 100}%` }} />
                </li>
              ))}
            </ul>
          ) : <Empty>Todavía no hay estafas reportadas hoy.</Empty>}
        </Card>

        <Card title="Reportes por hora">
          <div className="h-44">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data?.reportes_por_hora ?? []} margin={{ top: 4, right: 4, left: -24, bottom: 0 }}>
                <CartesianGrid stroke="var(--line)" vertical={false} />
                <XAxis dataKey="hora" tick={{ fontSize: 11, fill: "var(--muted)" }} interval={5} tickFormatter={(h) => `${h}h`} />
                <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: "var(--muted)" }} />
                <Tooltip formatter={(v) => [`${v} verificaciones`, ""]} labelFormatter={(h) => `${h}:00 – ${h}:59`}
                         contentStyle={{ background: "var(--surface)", border: "1px solid var(--line)", color: "var(--ink)" }} />
                <Area type="monotone" dataKey="total" stroke="var(--brand)" fill="var(--brand)" fillOpacity={0.15} strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card title="Campañas activas">
          {data?.campanas.length ? (
            <ul className="space-y-2">
              {data.campanas.map((c, i) => (
                <li key={c.id} className={`rounded-lg border px-3 py-2 text-sm ${i === 0 && data.alerta ? "border-risk-high/40 bg-risk-high-bg" : "border-line bg-surface-2"}`}>
                  <div className="font-semibold">{c.nombre}</div>
                  <div className={`text-xs ${i === 0 && data.alerta ? "text-risk-high" : "text-muted"}`}>
                    {i === 0 && data.alerta ? "▲ " : ""}{n(c.reportes)} reportes · último {ago(c.ultimo)}
                  </div>
                </li>
              ))}
            </ul>
          ) : <Empty>Ninguna campaña activa en las últimas 24 horas.</Empty>}
        </Card>

        <Card title="Llamada Verificada · últimas consultas">
          {data?.llamadas_ultimas.length ? (
            <ul className="divide-y divide-line">
              {data.llamadas_ultimas.map((c) => (
                <li key={c.cuando + c.entidad} className="flex items-center justify-between gap-2 py-2 text-sm">
                  <div>
                    <div className="font-semibold">{c.entidad}</div>
                    <div className="text-xs text-muted">{ago(c.cuando)}</div>
                  </div>
                  <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${c.real ? "bg-risk-low-bg text-risk-low" : "bg-risk-high-bg text-risk-high"}`}>
                    {c.real ? "● Real · registrada" : "● Falsa · sin registro"}
                  </span>
                </li>
              ))}
            </ul>
          ) : <Empty>Nadie ha preguntado todavía por una llamada.</Empty>}
        </Card>
      </div>

      <p className="text-right text-xs text-muted">
        {data ? `Actualizado ${ago(data.actualizado)}` : "Cargando…"} · Datos de esta instalación · entidades y números de prueba ficticios
      </p>
    </div>
  );
}

function Empty({ children }: { children: React.ReactNode }) {
  return <p className="py-6 text-center text-sm text-muted">{children}</p>;
}
