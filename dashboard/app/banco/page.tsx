"use client";

import { useCallback, useEffect, useState } from "react";
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { Card, Kpi, LevelPill, LiveBadge, Notice } from "@/components/ui";
import { ApiError, api, postJSON, type BancoView, type Lookup } from "@/lib/api";
import { ago, levelOf, n } from "@/lib/format";
import { usePolling } from "@/lib/usePolling";

const TEAM_KEY = "desenmascara.equipo";
const TIPOS: Record<string, string> = { telefono: "Teléfono", llave: "Llave Bre-B", cuenta: "Cuenta", enlace: "Enlace" };
const DAY = new Intl.DateTimeFormat("es-CO", { weekday: "short", day: "numeric", timeZone: "America/Bogota" });

export default function BancoPage() {
  const load = useCallback(() => api<BancoView>("/dashboard/banco"), []);
  const { data, error, refresh } = usePolling(load, 5000);
  const [teamKey, setTeamKey] = useState("");
  const [search, setSearch] = useState("");
  const [found, setFound] = useState<Lookup | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    try {
      setTeamKey(sessionStorage.getItem(TEAM_KEY) ?? "");
    } catch {
      /* storage blocked: the key is asked again */
    }
  }, []);

  function saveKey(value: string) {
    setTeamKey(value);
    try {
      sessionStorage.setItem(TEAM_KEY, value);
    } catch {
      /* storage blocked */
    }
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
    label: i === all.length - 1 ? "hoy" : DAY.format(new Date(d.dia)),
    total: d.total,
    today: i === all.length - 1,
  }));

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-3xl font-bold">Banco de números</h1>
        <span className="text-sm text-muted">lo que la comunidad ha reportado · últimos 30 días</span>
        <LiveBadge error={error} />
        <form className="ml-auto flex w-full gap-2 sm:w-auto" onSubmit={(e) => { e.preventDefault(); lookup(); }}>
          <input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Buscar un número, una llave o una cuenta"
                 aria-label="Buscar" className="min-w-0 flex-1 rounded-lg border border-line bg-surface px-3 py-2 text-sm sm:w-80" />
          <button className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white">Buscar</button>
        </form>
      </div>

      {error && <Notice>{error}</Notice>}
      {message && <p className="rounded-lg bg-mint px-4 py-3 text-sm">{message}</p>}
      {found && (
        <Card>
          <div className="flex flex-wrap items-center gap-3 text-sm">
            <span className="font-semibold">{found.valor ?? search}</span>
            <LevelPill level={found.oficial_de ? "low" : levelOf(found.nivel)} score={found.nivel} word={found.palabra} />
            <span className="text-muted">{n(found.personas)} personas · {n(found.reportes)} reportes{found.modalidad ? ` · ${found.modalidad}` : ""}</span>
            {found.oficial_de && <span className="text-brand-ink">Número oficial de {found.oficial_de}</span>}
          </div>
        </Card>
      )}

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Kpi label="Números, llaves y cuentas" value={data ? n(data.total) : "—"} />
        <Kpi label="En alto riesgo" value={data ? n(data.alto_riesgo) : "—"} note="nivel 70 o más" tone="high" />
        <Kpi label="Reportes esta semana" value={data ? n(data.reportes_semana) : "—"} note={data ? `de ${n(data.personas_semana)} personas distintas` : undefined} />
        <Kpi label="Números oficiales" value={data ? n(data.oficiales) : "—"} note="lista blanca verificada" highlight />
      </div>

      <div className="grid gap-4 xl:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
        <div className="space-y-4">
          <Card title="Más reportados" note="ordenados por nivel de riesgo">
            <div className="overflow-x-auto">
              <table className="w-full min-w-[36rem] text-sm">
                <thead className="text-left text-xs text-muted">
                  <tr><th className="py-2 font-medium">Número, llave o cuenta</th><th className="font-medium">Tipo</th><th className="font-medium">Personas</th><th className="font-medium">Nivel de riesgo</th><th className="font-medium">Modalidad</th><th className="font-medium">Último reporte</th></tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {data?.mas_reportados.map((r) => (
                    <tr key={r.valor + r.tipo}>
                      <td className="tabular py-2.5 font-semibold">{r.valor}</td>
                      <td>{TIPOS[r.tipo] ?? r.tipo}</td>
                      <td className="tabular">{n(r.personas)}</td>
                      <td>
                        {r.palabra === "En revisión"
                          ? <span className="rounded-full bg-surface-2 px-2.5 py-0.5 text-xs font-semibold text-muted">En revisión</span>
                          : <LevelPill level={levelOf(r.nivel)} score={r.nivel} word={r.palabra} />}
                      </td>
                      <td>{r.modalidad ?? "—"}</td>
                      <td className="text-muted">{ago(r.ultimo)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {data && !data.mas_reportados.length && <p className="py-6 text-center text-sm text-muted">Todavía no hay reportes.</p>}
            </div>
            <p className="mt-3 text-xs text-muted">
              Nunca dice «estafador»: muestra cuántas personas distintas lo reportaron y cuándo. Cada persona cuenta una sola vez.
            </p>
          </Card>

          <Card title="Reportes por día" note="últimos 7 días">
            <div className="h-48">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={days} margin={{ top: 16, right: 4, left: -24, bottom: 0 }}>
                  <XAxis dataKey="label" tick={{ fontSize: 11, fill: "var(--muted)" }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 11, fill: "var(--muted)" }} />
                  <Tooltip formatter={(v) => [`${v} reportes`, ""]} contentStyle={{ background: "var(--surface)", border: "1px solid var(--line)", color: "var(--ink)" }} />
                  <Bar dataKey="total" radius={[4, 4, 0, 0]} label={{ position: "top", fontSize: 11, fill: "var(--ink)" }}>
                    {days.map((d) => <Cell key={d.label} fill={d.today ? "var(--brand-ink)" : "var(--brand)"} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
        </div>

        <div className="space-y-4">
          <Card title="Solicitudes de revisión" note={data ? `${data.solicitudes.length} pendientes` : undefined}>
            <TeamKey value={teamKey} onChange={saveKey} />
            <ul className="mt-3 space-y-2">
              {data?.solicitudes.map((s) => (
                <li key={s.id} className="rounded-lg border border-line bg-surface-2 p-3 text-sm">
                  <div className="flex justify-between gap-2"><span className="tabular font-semibold">{s.valor}</span><span className="text-xs text-muted">{ago(s.creado)}</span></div>
                  <p className="mt-1 italic text-muted">«{s.motivo}»</p>
                  <div className="mt-2 flex items-center gap-2">
                    <button onClick={() => resolve(s.id, true)} disabled={!teamKey} className="rounded-md bg-brand px-3 py-1 text-xs font-semibold text-white disabled:opacity-50">Aceptar</button>
                    <button onClick={() => resolve(s.id, false)} disabled={!teamKey} className="rounded-md border border-line px-3 py-1 text-xs font-semibold disabled:opacity-50">Rechazar</button>
                    <span className="text-xs text-muted">escribió desde ese número</span>
                  </div>
                </li>
              ))}
              {data && !data.solicitudes.length && <li className="py-3 text-center text-sm text-muted">No hay solicitudes pendientes.</li>}
            </ul>
          </Card>

          <Card title="Lista blanca · números oficiales" note={data ? `${data.lista_blanca.length}` : undefined}>
            <ul className="space-y-2 text-sm">
              {data?.lista_blanca.map((o) => (
                <li key={o.entidad + o.valor} className="flex gap-2">
                  <span className="text-risk-low">✓</span>
                  <div>
                    <div><strong>{o.entidad}</strong> · {o.canal} <span className="tabular">{o.valor}</span></div>
                    <div className="text-xs text-muted">{o.fuente === "registro" ? "registrado por la entidad" : `página oficial · verificado por ${o.verificado_por}`}</div>
                  </div>
                </li>
              ))}
            </ul>
            <AddOfficial teamKey={teamKey} onDone={(m) => { setMessage(m); refresh(); }} />
          </Card>
        </div>
      </div>
      <p className="text-right text-xs text-muted">Datos de prueba ficticios marcados como «Demo» · números enmascarados</p>
    </div>
  );
}

function TeamKey({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  return (
    <label className="block text-xs text-muted">
      Llave del equipo (ADMIN_API_KEY del archivo .env)
      <input type="password" value={value} onChange={(e) => onChange(e.target.value)} autoComplete="off"
             className="mt-1 w-full rounded-md border border-line bg-surface px-2 py-1.5 text-sm text-ink" />
    </label>
  );
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
    <form className="mt-4 space-y-2 border-t border-line pt-3" onSubmit={(e) => { e.preventDefault(); add(); }}>
      <div className="text-xs font-semibold">+ Agregar número oficial</div>
      <div className="flex gap-2">
        <input value={entidad} onChange={(e) => setEntidad(e.target.value)} aria-label="Entidad" className="w-1/2 rounded-md border border-line bg-surface px-2 py-1.5 text-sm" />
        <input value={valor} onChange={(e) => setValor(e.target.value)} aria-label="Número" placeholder="+57 601 000 0003" className="w-1/2 rounded-md border border-line bg-surface px-2 py-1.5 text-sm" />
      </div>
      <button disabled={!teamKey || valor.length < 7} className="rounded-md bg-brand px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50">Agregar</button>
      <p className="text-xs text-muted">Solo con fuente oficial: una búsqueda en internet no basta.</p>
      {error && <p className="text-xs text-risk-high">{error}</p>}
    </form>
  );
}
