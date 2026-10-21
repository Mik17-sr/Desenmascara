"use client";

import { useCallback, useEffect, useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Activity, AlertTriangle, CheckCircle, Database, Key, Search, Users } from "@/components/icons";
import { Button, Card, Empty, Kpi, LevelPill, Notice, PageHeader, Skeleton } from "@/components/ui";
import { ApiError, api, postJSON, type BancoView, type Lookup } from "@/lib/api";
import { ago, levelOf, n, plural } from "@/lib/format";
import { useLive } from "@/lib/useLive";

const TEAM_KEY = "desenmascara.equipo";
const TIPOS: Record<string, string> = { telefono: "Teléfono", llave: "Llave Bre-B", cuenta: "Cuenta", enlace: "Enlace" };
const DAY = new Intl.DateTimeFormat("es-CO", { weekday: "short", day: "numeric", timeZone: "America/Bogota" });

export default function BancoPage() {
  const load = useCallback(() => api<BancoView>("/dashboard/banco"), []);
  const { data, error, refresh } = useLive(load, 5000);
  const [teamKey, setTeamKey] = useState("");
  const [search, setSearch] = useState("");
  const [found, setFound] = useState<Lookup | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  // The team key stays in this browser until it is erased from the field.
  useEffect(() => {
    try { setTeamKey(localStorage.getItem(TEAM_KEY) ?? ""); } catch { /* storage blocked: the key is asked again */ }
  }, []);

  function saveKey(value: string) {
    setTeamKey(value);
    try {
      if (value) localStorage.setItem(TEAM_KEY, value);
      else localStorage.removeItem(TEAM_KEY);
    } catch { /* storage blocked */ }
  }

  async function lookup() {
    setMessage(null);
    const digits = search.replace(/[\s+().-]/g, "");
    const tipo = /^\d{10,12}$/.test(digits) ? "telefono" : /^\d+$/.test(digits) ? "cuenta" : "llave";
    try {
      setFound(await api<Lookup>(`/banco/consultar?tipo=${tipo}&valor=${encodeURIComponent(search)}`));
    } catch (e) {
      setMessage(e instanceof ApiError ? e.message : "No se pudo consultar.");
    }
  }

  async function resolve(id: string, aceptar: boolean) {
    setMessage(null);
    try {
      await postJSON(`/banco/revisiones/${id}`, { aceptar }, { "X-Admin-Key": teamKey });
      setMessage(aceptar ? "Revisión aceptada: el número volvió a «sin reportes»." : "Revisión rechazada: los reportes se mantienen.");
      refresh();
    } catch (e) {
      setMessage(e instanceof ApiError && e.status === 401 ? "Esa llave del equipo no es válida." : e instanceof Error ? e.message : "Error");
    }
  }

  const days = (data?.reportes_por_dia ?? []).map((d, i, all) => ({
    label: i === all.length - 1 ? "hoy" : DAY.format(new Date(d.dia)), total: d.total, today: i === all.length - 1,
  }));

  return (
    <div>
      <PageHeader
        title="Banco de números"
        subtitle="La memoria de la comunidad: números, llaves Bre-B y cuentas reportados en los últimos 30 días."
        actions={
          <form className="flex w-full gap-2 sm:w-auto" onSubmit={(e) => { e.preventDefault(); lookup(); }}>
            <div className="relative flex-1 sm:w-80">
              <Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted" width={16} height={16} />
              <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Buscar número, llave o cuenta" aria-label="Buscar"
                     className="w-full rounded-xl border border-line bg-surface py-2.5 pl-9 pr-3 text-sm outline-none focus:border-brand focus:ring-4 focus:ring-brand/15" />
            </div>
            <Button>Buscar</Button>
          </form>
        }
      />

      <div className="space-y-6">
        {error && <Notice>{error}</Notice>}
        {message && <p className="rise rounded-xl border border-brand/30 bg-brand-soft px-4 py-3 text-sm">{message}</p>}
        {found && (
          <Card>
            <div className="flex flex-wrap items-center gap-3 text-sm">
              <span className="tabular text-lg font-bold">{found.valor ?? search}</span>
              <LevelPill level={found.oficial_de ? "low" : levelOf(found.nivel)} score={found.nivel} word={found.palabra} />
              <span className="text-muted">{plural(found.personas, "persona", "personas")} · {plural(found.reportes, "reporte", "reportes")}{found.modalidad ? ` · ${found.modalidad}` : ""}</span>
              {found.oficial_de && <span className="font-medium text-brand-ink">Número oficial de {found.oficial_de}</span>}
            </div>
          </Card>
        )}

        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <Kpi label="Números, llaves y cuentas" value={data?.total ?? 0} loading={!data} note="en el Banco" />
          <Kpi label="En alto riesgo" value={data?.alto_riesgo ?? 0} tone="high" loading={!data} note="nivel 70 o más" />
          <Kpi label="Reportes esta semana" value={data?.reportes_semana ?? 0} loading={!data} note={data ? `de ${plural(data.personas_semana, "persona", "personas distintas")}` : undefined} />
          <Kpi label="Números oficiales" value={data?.oficiales ?? 0} tone="brand" loading={!data} note="lista blanca verificada" />
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          <div className="min-w-0 space-y-4 lg:col-span-2">
            <Card title="Más reportados" icon={Users} padded={false} action={<span className="hidden text-xs text-muted sm:inline">ordenados por nivel de riesgo</span>}>
              {!data ? <div className="space-y-2 p-5">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-10" />)}</div> : data.mas_reportados.length ? (<>
                <ul className="divide-y divide-line md:hidden">
                  {data.mas_reportados.map((r) => (
                    <li key={r.valor + r.tipo} className="px-5 py-3 text-sm">
                      <div className="flex items-center justify-between gap-3">
                        <span className="tabular font-semibold">{r.valor}</span>
                        <RiskCell row={r} />
                      </div>
                      <div className="mt-1 text-xs text-muted">{TIPOS[r.tipo] ?? r.tipo} · {plural(r.personas, "persona", "personas")} · {ago(r.ultimo)}</div>
                      {r.modalidad && <div className="mt-0.5 text-xs">{r.modalidad}</div>}
                    </li>
                  ))}
                </ul>
                <div className="hidden overflow-x-auto md:block">
                  <table className="w-full text-sm">
                    <thead className="bg-surface-2 text-left text-[11px] uppercase tracking-wide text-muted">
                      <tr>
                        <th className="py-3 pl-5 pr-2.5 font-semibold xl:whitespace-nowrap">Número, llave o cuenta</th>
                        <th className="hidden whitespace-nowrap px-3 font-semibold xl:table-cell">Tipo</th>
                        <th className="whitespace-nowrap px-2.5 text-right font-semibold">Personas</th>
                        <th className="whitespace-nowrap px-2.5 font-semibold">Nivel de riesgo</th>
                        <th className="px-2.5 font-semibold">Modalidad</th>
                        <th className="whitespace-nowrap pl-2.5 pr-4 font-semibold">Último</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-line">
                      {data.mas_reportados.map((r) => (
                        <tr key={r.valor + r.tipo} className="transition hover:bg-surface-2">
                          <td className="tabular whitespace-nowrap py-3 pl-5 pr-2.5 font-semibold">
                            {r.valor}
                            <div className="text-xs font-normal text-muted xl:hidden">{TIPOS[r.tipo] ?? r.tipo}</div>
                          </td>
                          <td className="hidden px-3 leading-snug text-muted xl:table-cell">{TIPOS[r.tipo] ?? r.tipo}</td>
                          <td className="tabular px-2.5 text-right">{n(r.personas)}</td>
                          <td className="px-2.5"><RiskCell row={r} /></td>
                          <td className="min-w-28 px-2.5 py-3 leading-snug">{r.modalidad ?? "—"}</td>
                          <td className="whitespace-nowrap pl-2.5 pr-4 text-muted">{ago(r.ultimo)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>) : <Empty icon={Database}>Todavía no hay reportes.</Empty>}
              <p className="border-t border-line px-5 py-3 text-xs text-muted">
                Nunca dice «estafador»: muestra cuántas personas distintas lo reportaron y cuándo. Cada persona cuenta una sola vez.
              </p>
            </Card>

            <Card title="Reportes por día" icon={Activity}
                  action={<span className="text-xs text-muted">últimos 7 días{days.length ? ` · ${n(days.reduce((sum, d) => sum + d.total, 0))} en total` : ""}</span>}>
              <div className="h-56">
                {data ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={days} margin={{ top: 18, right: 4, left: -22, bottom: 0 }}>
                      <CartesianGrid stroke="var(--line)" strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="label" tick={{ fontSize: 11, fill: "var(--muted)" }} axisLine={false} tickLine={false} />
                      <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: "var(--muted)" }} axisLine={false} tickLine={false} />
                      <Tooltip cursor={{ fill: "var(--surface-2)" }} formatter={(v) => [plural(Number(v), "reporte", "reportes"), ""]}
                               contentStyle={{ background: "var(--surface)", border: "1px solid var(--line)", borderRadius: 12, color: "var(--ink)" }} />
                      <Bar dataKey="total" radius={[6, 6, 0, 0]} label={{ position: "top", fontSize: 11, fill: "var(--ink)" }} animationDuration={800}>
                        {days.map((d) => <Cell key={d.label} fill={d.today ? "var(--brand-ink)" : "var(--brand)"} fillOpacity={d.today ? 1 : 0.7} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                ) : <Skeleton className="h-full" />}
              </div>
            </Card>
          </div>

          <div className="min-w-0 space-y-4">
            <Card title="Solicitudes de revisión" icon={AlertTriangle} action={data && <span className="rounded-full bg-surface-2 px-2 py-0.5 text-xs font-semibold">{data.solicitudes.length}</span>}>
              {!data ? <Skeleton className="h-20" /> : data.solicitudes.length ? (
                <ul className="space-y-3">
                  {data.solicitudes.map((s) => (
                    <li key={s.id} className="rounded-xl border border-line bg-surface-2 p-3.5 text-sm">
                      <div className="flex justify-between gap-2"><span className="tabular font-semibold">{s.valor}</span><span className="text-xs text-muted">{ago(s.creado)}</span></div>
                      <p className="mt-1 text-muted">«{s.motivo}»</p>
                      <div className="mt-3 flex items-center gap-2">
                        <Button onClick={() => resolve(s.id, true)} disabled={!teamKey} className="px-3 py-1.5 text-xs">Aceptar</Button>
                        <Button variant="ghost" onClick={() => resolve(s.id, false)} disabled={!teamKey} className="px-3 py-1.5 text-xs">Rechazar</Button>
                        <span className="text-[11px] text-muted">escribió desde ese número</span>
                      </div>
                    </li>
                  ))}
                </ul>
              ) : <Empty icon={CheckCircle}>No hay solicitudes pendientes.</Empty>}
            </Card>

            <Card title="Lista blanca · números oficiales" icon={CheckCircle}>
              <ul className="space-y-3 text-sm">
                {data?.lista_blanca.map((o) => (
                  <li key={o.entidad + o.valor} className="flex gap-3">
                    <span className="grid h-8 w-8 shrink-0 place-items-center rounded-lg bg-risk-low-bg text-risk-low"><CheckCircle width={15} height={15} /></span>
                    <div className="min-w-0">
                      <div><strong>{o.entidad}</strong> <span className="text-muted">· {o.canal}</span></div>
                      <div className="tabular">{o.valor}</div>
                      <div className="text-xs text-muted">{o.fuente === "registro" ? "registrado por la entidad" : `página oficial · verificado por ${o.verificado_por}`}</div>
                    </div>
                  </li>
                ))}
              </ul>
              <AddOfficial teamKey={teamKey} onDone={(m) => { setMessage(m); refresh(); }} />
            </Card>

            <Card title="Llave del equipo" icon={Key}>
              <label className="block text-xs text-muted">
                Para aceptar revisiones y agregar números oficiales (ADMIN_API_KEY del archivo .env). Queda guardada en este equipo; bórrala del campo para olvidarla.
                <input type="password" value={teamKey} onChange={(e) => saveKey(e.target.value)} autoComplete="off" placeholder="adm_…"
                       className="mt-2 w-full rounded-xl border border-line bg-surface px-3 py-2 text-sm text-ink outline-none focus:border-brand focus:ring-4 focus:ring-brand/15" />
              </label>
            </Card>
          </div>
        </div>
        <p className="text-right text-xs text-muted">Datos de prueba ficticios marcados como «Demo» · números enmascarados</p>
      </div>
    </div>
  );
}

function RiskCell({ row }: { row: BancoView["mas_reportados"][number] }) {
  return row.palabra === "En revisión"
    ? <span className="whitespace-nowrap rounded-full bg-surface-2 px-2.5 py-0.5 text-xs font-semibold text-muted">En revisión</span>
    : <LevelPill level={levelOf(row.nivel)} score={row.nivel} word={row.palabra} />;
}

function AddOfficial({ teamKey, onDone }: { teamKey: string; onDone: (message: string) => void }) {
  const [entidad, setEntidad] = useState("BancoAndino");
  const [valor, setValor] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function add() {
    setError(null);
    try {
      await postJSON("/banco/lista-blanca", { entidad, valor, canal: "telegram", verificado_por: "equipo" }, { "X-Admin-Key": teamKey });
      setValor("");
      onDone(`Número agregado a la lista blanca de ${entidad}.`);
    } catch (e) {
      setError(e instanceof ApiError && e.status === 401 ? "Esa llave del equipo no es válida." : e instanceof Error ? e.message : "Error");
    }
  }

  return (
    <form className="mt-5 space-y-2 border-t border-line pt-4" onSubmit={(e) => { e.preventDefault(); add(); }}>
      <div className="text-xs font-semibold uppercase tracking-wide text-muted">Agregar número oficial</div>
      <div className="grid grid-cols-2 gap-2">
        <input value={entidad} onChange={(e) => setEntidad(e.target.value)} aria-label="Entidad" className="rounded-xl border border-line bg-surface px-3 py-2 text-sm" />
        <input value={valor} onChange={(e) => setValor(e.target.value)} aria-label="Número" placeholder="+57 601 000 0003" className="rounded-xl border border-line bg-surface px-3 py-2 text-sm" />
      </div>
      <Button disabled={!teamKey || valor.length < 7} className="w-full">Agregar a la lista blanca</Button>
      <p className="text-[11px] text-muted">Solo con fuente oficial: una búsqueda en internet no basta.</p>
      {error && <p className="text-xs text-risk-high">{error}</p>}
    </form>
  );
}
