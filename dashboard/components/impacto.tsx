"use client";

import { useCallback } from "react";

import { AlertTriangle, Building, ShieldCheck } from "@/components/icons";
import { Card, Empty, Kpi, Skeleton } from "@/components/ui";
import { api, type Impacto, type Marca } from "@/lib/api";
import { ago, n, plural } from "@/lib/format";
import { useLive } from "@/lib/useLive";

const DATE = new Intl.DateTimeFormat("es-CO", { day: "numeric", month: "long", year: "numeric", timeZone: "America/Bogota" });

/** What Desenmascara did since it started and which entities scams impersonate: real checks, nothing estimated. */
export function ImpactoYMarcas() {
  const loadImpact = useCallback(() => api<Impacto>("/dashboard/impacto"), []);
  const loadBrands = useCallback(() => api<Marca[]>("/dashboard/marcas"), []);
  const { data: impact } = useLive(loadImpact, 15000);
  const { data: brands } = useLive(loadBrands, 15000);

  return (
    <div className="grid items-start gap-4 lg:grid-cols-3">
      <Card title="Impacto desde el inicio" icon={ShieldCheck} className="lg:col-span-2"
            action={impact?.desde && <span className="text-xs text-muted">desde el {DATE.format(new Date(impact.desde))}</span>}>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <Kpi label="Estafas detectadas" value={impact?.estafas_detectadas ?? 0} tone="high" loading={!impact}
               note={impact ? `${n(impact.alto_riesgo)} de alto riesgo` : undefined} />
          <Kpi label="Dinero que pedían" value={impact?.dinero_pedido ?? 0} prefix="$" loading={!impact} note="en estafas de alto riesgo" />
          <Kpi label="Alertas al Círculo" value={impact?.alertas_circulo ?? 0} tone="brand" loading={!impact} note="familiares avisados a tiempo" />
          <Kpi label="Reportes al Banco" value={impact?.reportes ?? 0} loading={!impact}
               note={impact ? `${plural(impact.campanas, "campaña detectada", "campañas detectadas")}` : undefined} />
        </div>
        {impact && (
          <p className="mt-3 text-xs text-muted">
            {plural(impact.revisiones, "revisión", "revisiones")} de {plural(impact.personas, "persona", "personas")} ·{" "}
            {plural(impact.llamadas_verificadas, "llamada verificada", "llamadas verificadas")} con la entidad. Datos reales, sin estimaciones.
          </p>
        )}
      </Card>

      <Card title="Marcas suplantadas · 30 días" icon={AlertTriangle} padded={false}
            action={brands && <span className="text-xs text-muted">{brands.length}</span>}>
        {!brands ? <div className="p-5"><Skeleton className="h-24" /></div> : brands.length ? (
          <ul className="divide-y divide-line">
            {brands.slice(0, 6).map((b) => (
              <li key={b.marca} className="flex items-center gap-3 px-5 py-3">
                <span className="grid h-9 w-9 shrink-0 place-items-center rounded-xl bg-risk-high-bg text-risk-high"><Building width={16} height={16} /></span>
                <div className="min-w-0 flex-1">
                  <div className="truncate text-sm font-semibold">{b.marca}</div>
                  <div className="truncate text-xs text-muted">{b.modalidad ?? "Suplantación"} · {ago(b.ultimo)}</div>
                </div>
                <div className="text-right">
                  <div className="tabular text-sm font-bold">{n(b.mensajes)}</div>
                  {b.hoy > 0 && <div className="text-[11px] font-semibold text-risk-high">+{n(b.hoy)} hoy</div>}
                </div>
              </li>
            ))}
          </ul>
        ) : <Empty icon={Building}>Ninguna marca suplantada en los últimos 30 días.</Empty>}
        <p className="border-t border-line px-5 py-3 text-xs text-muted">
          Cada entidad conectada ve en su Panel qué mensajes usan su nombre, con los enlaces falsos: alerta temprana para avisar a sus clientes.
        </p>
      </Card>
    </div>
  );
}
