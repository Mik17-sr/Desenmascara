"use client";

import { useCallback, useEffect, useState } from "react";

import { Card, Notice } from "@/components/ui";
import { ApiError, api, postJSON, type Llamada } from "@/lib/api";
import { ago } from "@/lib/format";

const KEY = "desenmascara.entidad";
const ESTADOS: Record<string, { label: string; className: string }> = {
  registrada: { label: "Esperando al cliente", className: "bg-risk-mid-bg text-risk-mid-ink" },
  confirmada: { label: "Verificada por el cliente", className: "bg-risk-low-bg text-risk-low" },
  vencida: { label: "Vencida (no preguntó)", className: "bg-surface-2 text-muted" },
};

type Registro = { codigo_verificacion: string; vence_at: string };

export default function EntidadPage() {
  const [key, setKey] = useState("");
  const [entity, setEntity] = useState<{ nombre: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const login = useCallback(async (candidate: string) => {
    setError(null);
    try {
      const me = await api<{ nombre: string }>("/entidad/yo", { headers: { "X-Entity-API-Key": candidate } });
      setEntity(me);
      setKey(candidate);
      try { sessionStorage.setItem(KEY, candidate); } catch { /* storage blocked */ }
    } catch (e) {
      setEntity(null);
      setError(e instanceof ApiError && e.status === 401 ? "Esa llave de acceso no es válida." : e instanceof Error ? e.message : "Error");
    }
  }, []);

  useEffect(() => {
    let saved = "";
    try { saved = sessionStorage.getItem(KEY) ?? ""; } catch { /* storage blocked */ }
    if (saved) login(saved);
  }, [login]);

  if (!entity) {
    return (
      <div className="mx-auto max-w-md space-y-4 py-10">
        <h1 className="text-3xl font-bold">Acceso para entidades</h1>
        <p className="text-sm text-muted">
          Bancos, operadores y tiendas registran aquí sus llamadas antes de marcar. Así sus clientes pueden confirmar por Telegram que de verdad son ustedes.
        </p>
        <Card>
          <form className="space-y-3" onSubmit={(e) => { e.preventDefault(); login(key); }}>
            <label className="block text-sm font-medium">
              Llave de acceso (API key)
              <input type="password" value={key} onChange={(e) => setKey(e.target.value)} autoComplete="off" placeholder="sec_live_…"
                     className="mt-1 w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm" />
            </label>
            <button disabled={!key} className="w-full rounded-lg bg-brand py-2 text-sm font-semibold text-white disabled:opacity-50">Entrar</button>
          </form>
        </Card>
        {error && <Notice>{error}</Notice>}
        <p className="text-xs text-muted">Para la demo: `python scripts/seed_demo.py --nueva-llave` muestra la llave de BancoAndino (entidad ficticia).</p>
      </div>
    );
  }
  return <Panel entity={entity.nombre} apiKey={key} onLogout={() => { setEntity(null); setKey(""); try { sessionStorage.removeItem(KEY); } catch { /* */ } }} />;
}

function Panel({ entity, apiKey, onLogout }: { entity: string; apiKey: string; onLogout: () => void }) {
  const headers = { "X-Entity-API-Key": apiKey };
  const [telefono, setTelefono] = useState("+57 310 000 0000");
  const [motivo, setMotivo] = useState("Confirmar una compra");
  const [asesor, setAsesor] = useState("Laura M.");
  const [registro, setRegistro] = useState<Registro | null>(null);
  const [calls, setCalls] = useState<Llamada[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [now, setNow] = useState(Date.now());

  const loadCalls = useCallback(async () => {
    try { setCalls(await api<Llamada[]>("/llamadas/hoy", { headers: { "X-Entity-API-Key": apiKey } })); } catch { /* shown on next action */ }
  }, [apiKey]);

  useEffect(() => {
    loadCalls();
    const poll = setInterval(loadCalls, 4000);
    const tick = setInterval(() => setNow(Date.now()), 1000);
    return () => { clearInterval(poll); clearInterval(tick); };
  }, [loadCalls]);

  async function register() {
    setError(null);
    try {
      setRegistro(await postJSON<Registro>("/llamadas/registrar", { telefono_cliente: telefono, motivo, asesor }, headers));
      loadCalls();
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo registrar.");
    }
  }

  const remaining = registro ? Math.max(0, new Date(registro.vence_at).getTime() - now) : 0;
  const mmss = `${Math.floor(remaining / 60000)}:${String(Math.floor((remaining % 60000) / 1000)).padStart(2, "0")}`;

  return (
    <div className="grid gap-4 lg:grid-cols-[14rem_minmax(0,1fr)]">
      <aside className="rounded-xl bg-[#1F2A44] p-4 text-white">
        <div className="text-lg font-bold">{entity}</div>
        <div className="text-xs text-white/60">Panel de la entidad</div>
        <nav className="mt-5 space-y-1 text-sm">
          <div className="rounded-md bg-white/10 px-3 py-2 font-semibold">Llamada Verificada</div>
          <div className="px-3 py-2 text-white/70">Llamadas de hoy</div>
        </nav>
        <div className="mt-6 rounded-lg border border-[#2BB5A3]/40 bg-[#2BB5A3]/15 p-3 text-xs">
          ● Conectado a Desenmascara. Tus clientes pueden confirmar tus llamadas por Telegram.
        </div>
        <button onClick={onLogout} className="mt-4 text-xs text-white/70 underline">Salir</button>
      </aside>

      <div className="space-y-4">
        <h1 className="text-2xl font-bold">Registrar una llamada antes de marcar</h1>
        {error && <Notice>{error}</Notice>}
        <div className="grid gap-4 md:grid-cols-2">
          <Card title="Datos de la llamada">
            <form className="space-y-3" onSubmit={(e) => { e.preventDefault(); register(); }}>
              <Field label="Número del cliente" value={telefono} onChange={setTelefono} />
              <Field label="Motivo" value={motivo} onChange={setMotivo} />
              <Field label="Asesor o asesora" value={asesor} onChange={setAsesor} />
              <button className="rounded-lg bg-brand px-4 py-2 text-sm font-semibold text-white">Registrar y llamar</button>
            </form>
          </Card>
          <Card>
            {registro ? (
              <div>
                <div className="font-semibold text-risk-low">✓ Llamada registrada</div>
                <div className="mt-1 text-sm text-muted">Código que tu asesor o asesora le dirá al cliente:</div>
                <div className="tabular mt-3 text-6xl font-bold tracking-[0.3em] text-brand-ink">{registro.codigo_verificacion}</div>
                <div className="mt-3 text-sm text-muted">
                  {remaining > 0 ? <>Vence en <span className="tabular font-semibold text-ink">{mmss}</span> · sirve una sola vez.</> : "Venció: registra la llamada de nuevo."}
                </div>
                <p className="mt-2 text-xs text-muted">Si el cliente le pregunta al bot, verá «SÍ, ES REAL» y este mismo código.</p>
              </div>
            ) : (
              <p className="py-10 text-center text-sm text-muted">Registra la llamada y aquí aparecerá el código de un solo uso.</p>
            )}
          </Card>
        </div>

        <Card title="Llamadas de hoy">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[32rem] text-sm">
              <thead className="text-left text-xs text-muted">
                <tr><th className="py-2 font-medium">Cliente</th><th className="font-medium">Motivo</th><th className="font-medium">Asesor</th><th className="font-medium">Estado</th><th className="font-medium">Registrada</th></tr>
              </thead>
              <tbody className="divide-y divide-line">
                {calls.map((c) => (
                  <tr key={c.id}>
                    <td className="tabular py-2.5">{c.cliente}</td>
                    <td>{c.motivo}</td>
                    <td>{c.asesor}</td>
                    <td><span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${ESTADOS[c.estado]?.className ?? ""}`}>{ESTADOS[c.estado]?.label ?? c.estado}</span></td>
                    <td className="text-muted">{ago(c.creado)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {!calls.length && <p className="py-6 text-center text-sm text-muted">Todavía no registraste llamadas hoy.</p>}
          </div>
          <p className="mt-3 text-xs text-muted">Los números se guardan protegidos y cada registro se borra a los 15 minutos; aquí solo queda el número enmascarado.</p>
        </Card>
      </div>
    </div>
  );
}

function Field({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <label className="block text-sm">
      <span className="text-muted">{label}</span>
      <input value={value} onChange={(e) => onChange(e.target.value)} className="mt-1 w-full rounded-lg border border-line bg-surface px-3 py-2" />
    </label>
  );
}
