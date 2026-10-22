"use client";

import { useCallback, useEffect, useState } from "react";

import { Building, CheckCircle, Copy, Key, Logout, Phone, ShieldCheck } from "@/components/icons";
import { Button, Card, Empty, Notice, PageHeader } from "@/components/ui";
import { ApiError, api, postJSON, type Llamada } from "@/lib/api";
import { ago } from "@/lib/format";
import { useDemo } from "@/lib/useDemo";
import { useLive } from "@/lib/useLive";

const KEY = "desenmascara.entidad";
const TTL_MS = 15 * 60 * 1000;
const ESTADOS: Record<string, { label: string; className: string }> = {
  registrada: { label: "Esperando al cliente", className: "bg-risk-mid-bg text-risk-mid-ink" },
  confirmada: { label: "Verificada por el cliente", className: "bg-risk-low-bg text-risk-low" },
  vencida: { label: "Vencida (no preguntó)", className: "bg-surface-2 text-muted" },
};

type Registro = { codigo_verificacion: string; vence_at: string };

// "Recordar en este equipo" keeps the key in localStorage until "Cerrar sesión"; otherwise it lasts
// only while the tab is open. Storage can be blocked: then the key is simply asked again.
function savedKey(): string {
  try { return localStorage.getItem(KEY) ?? sessionStorage.getItem(KEY) ?? ""; } catch { return ""; }
}
function forgetKey() {
  try { localStorage.removeItem(KEY); sessionStorage.removeItem(KEY); } catch { /* storage blocked */ }
}
function keepKey(value: string, remember: boolean) {
  forgetKey();
  try { (remember ? localStorage : sessionStorage).setItem(KEY, value); } catch { /* storage blocked */ }
}

export default function EntidadPage() {
  const [key, setKey] = useState("");
  const [remember, setRemember] = useState(true);
  const [entity, setEntity] = useState<{ nombre: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [checking, setChecking] = useState(true);
  const demo = useDemo();

  const login = useCallback(async (candidate: string, keep: boolean) => {
    setError(null);
    try {
      const me = await api<{ nombre: string }>("/entidad/yo", { headers: { "X-Entity-API-Key": candidate } });
      setEntity(me);
      setKey(candidate);
      keepKey(candidate, keep);
    } catch (e) {
      setEntity(null);
      if (e instanceof ApiError && e.status === 401) forgetKey();
      setError(e instanceof ApiError && e.status === 401 ? "Esa llave de acceso no es válida." : e instanceof Error ? e.message : "Error");
    }
  }, []);

  useEffect(() => {
    // seed_demo.py prints /entidad#llave=…: sign in from the link and take the key out of the address bar.
    const fromLink = new URLSearchParams(window.location.hash.slice(1)).get("llave");
    if (fromLink) history.replaceState(null, "", window.location.pathname);
    let remembered = !!fromLink;
    if (!fromLink) try { remembered = localStorage.getItem(KEY) !== null; } catch { /* storage blocked */ }
    const candidate = fromLink ?? savedKey();
    if (candidate) login(candidate, remembered).finally(() => setChecking(false));
    else setChecking(false);
  }, [login]);

  if (checking) return <div className="mx-auto max-w-md py-24"><div className="skeleton h-40" /></div>;
  if (!entity) {
    return (
      <div className="mx-auto grid max-w-5xl items-center gap-10 py-6 lg:grid-cols-2 lg:py-12">
        <div className="rise">
          <span className="inline-flex items-center gap-2 rounded-full bg-brand-soft px-3 py-1 text-xs font-semibold text-brand-ink"><ShieldCheck width={14} height={14} /> Llamada Verificada</span>
          <h1 className="mt-4 text-3xl font-bold tracking-tight sm:text-4xl">Que tus clientes sepan que de verdad eres tú.</h1>
          <p className="mt-4 text-muted">Registra la llamada antes de marcar. Si el cliente le pregunta al bot de Telegram, verá «SÍ, ES REAL» y un código de un solo uso que tu asesor le dirá. Sin registro, el bot le dice que cuelgue.</p>
          <ul className="mt-6 space-y-3 text-sm">
            {["Le gana a la falsificación del número en pantalla.", "El código sirve una vez y se borra a los 15 minutos.", "Nadie más puede saber a quién estás llamando."].map((t) => (
              <li key={t} className="flex gap-3"><CheckCircle className="shrink-0 text-brand-ink" />{t}</li>
            ))}
          </ul>
        </div>
        <Card className="rise">
          <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); login(key, remember); }}>
            <div className="flex items-center gap-3">
              <span className="grid h-11 w-11 place-items-center rounded-2xl bg-brand-soft text-brand-ink"><Building /></span>
              <div><div className="font-semibold">Acceso para entidades</div><div className="text-xs text-muted">Bancos, operadores y tiendas</div></div>
            </div>
            <label className="block text-sm font-medium">
              Llave de acceso (API key)
              <div className="relative mt-1.5">
                <Key className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted" width={16} height={16} />
                <input type="password" value={key} onChange={(e) => setKey(e.target.value)} autoComplete="off" placeholder="sec_live_…"
                       className="w-full rounded-xl border border-line bg-surface py-2.5 pl-9 pr-3 text-sm outline-none focus:border-brand focus:ring-4 focus:ring-brand/15" />
              </div>
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} className="h-4 w-4 accent-brand" />
              Recordar la llave en este equipo
            </label>
            <Button disabled={!key} className="w-full py-2.5">Entrar al panel</Button>
            {error && <Notice>{error}</Notice>}
            <p className="text-xs text-muted">{demo
              ? "Demostración: python scripts/seed_demo.py --nueva-llave muestra la llave de BancoAndino (entidad ficticia) y un enlace que entra sin escribirla."
              : "La llave te la entrega el equipo de Desenmascara cuando conecta tu entidad a Llamada Verificada."}</p>
          </form>
        </Card>
      </div>
    );
  }
  return <Panel entity={entity.nombre} apiKey={key} onLogout={() => { setEntity(null); setKey(""); forgetKey(); }} />;
}

function Panel({ entity, apiKey, onLogout }: { entity: string; apiKey: string; onLogout: () => void }) {
  const [telefono, setTelefono] = useState("+57 310 000 0000");
  const [motivo, setMotivo] = useState("Confirmar una compra");
  const [asesor, setAsesor] = useState("Laura M.");
  const [registro, setRegistro] = useState<Registro | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [now, setNow] = useState(Date.now());

  const load = useCallback(() => api<Llamada[]>("/llamadas/hoy", { headers: { "X-Entity-API-Key": apiKey } }), [apiKey]);
  const { data: calls, refresh } = useLive(load, 4000);

  useEffect(() => {
    const tick = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(tick);
  }, []);

  async function register() {
    setError(null);
    setCopied(false);
    try {
      setRegistro(await postJSON<Registro>("/llamadas/registrar", { telefono_cliente: telefono, motivo, asesor }, { "X-Entity-API-Key": apiKey }));
      refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo registrar.");
    }
  }

  async function copy() {
    if (!registro) return;
    try { await navigator.clipboard.writeText(registro.codigo_verificacion); setCopied(true); } catch { /* clipboard blocked */ }
  }

  const remaining = registro ? Math.max(0, new Date(registro.vence_at).getTime() - now) : 0;
  const mmss = `${Math.floor(remaining / 60000)}:${String(Math.floor((remaining % 60000) / 1000)).padStart(2, "0")}`;
  const counts = { total: calls?.length ?? 0, ok: calls?.filter((c) => c.estado === "confirmada").length ?? 0 };

  return (
    <div>
      <PageHeader
        title={`Panel de ${entity}`}
        subtitle="Registra una llamada antes de marcar. El cliente la confirma por Telegram con un código de un solo uso."
        actions={<Button variant="ghost" onClick={onLogout}><Logout width={16} height={16} /> Cerrar sesión</Button>}
      />
      {error && <div className="mb-6"><Notice>{error}</Notice></div>}

      <div className="grid gap-6 lg:grid-cols-2">
        <Card title="Datos de la llamada" icon={Phone}>
          <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); register(); }}>
            <Field label="Número del cliente" value={telefono} onChange={setTelefono} />
            <Field label="Motivo" value={motivo} onChange={setMotivo} />
            <Field label="Asesor o asesora" value={asesor} onChange={setAsesor} />
            <Button className="w-full py-2.5"><Phone width={16} height={16} /> Registrar y llamar</Button>
          </form>
        </Card>

        <Card title="Código para el cliente" icon={ShieldCheck}>
          {registro ? (
            <div className="rise">
              <div className="flex items-center gap-2 text-sm font-semibold text-risk-low"><CheckCircle width={16} height={16} /> Llamada registrada</div>
              <p className="mt-1 text-sm text-muted">Tu asesor o asesora le dirá este código al cliente:</p>
              <div className="mt-4 flex items-center gap-2 sm:gap-3">
                {registro.codigo_verificacion.split("").map((digit, i) => (
                  <span key={i} className="tabular grid h-16 w-14 place-items-center rounded-2xl border border-brand/30 bg-brand-soft text-4xl font-bold text-brand-ink sm:h-20 sm:w-16">{digit}</span>
                ))}
                <button onClick={copy} className="ml-auto rounded-xl border border-line p-3 text-muted transition hover:bg-surface-2 hover:text-ink" aria-label="Copiar código">
                  {copied ? <CheckCircle className="text-risk-low" /> : <Copy />}
                </button>
              </div>
              <div className="mt-5">
                <div className="flex justify-between text-xs text-muted">
                  <span>{remaining > 0 ? "Vence en" : "Venció: registra la llamada de nuevo."}</span>
                  {remaining > 0 && <span className="tabular font-semibold text-ink">{mmss}</span>}
                </div>
                <div className="mt-1.5 h-1.5 overflow-hidden rounded-full bg-surface-2">
                  <div className="h-full rounded-full bg-brand transition-[width] duration-1000 ease-linear" style={{ width: `${(remaining / TTL_MS) * 100}%` }} />
                </div>
              </div>
              <p className="mt-4 text-xs text-muted">Sirve una sola vez. Si el cliente le pregunta al bot, verá «SÍ, ES REAL» y este mismo código.</p>
            </div>
          ) : <Empty icon={ShieldCheck}>Registra la llamada y aquí aparecerá el código de un solo uso.</Empty>}
        </Card>
      </div>

      <div className="mt-6">
        <Card title="Llamadas de hoy" icon={Phone} padded={false}
              action={<span className="text-xs text-muted">{counts.ok} de {counts.total} verificadas por el cliente</span>}>
          {calls && calls.length ? (
            <div className="overflow-x-auto">
              <table className="w-full min-w-xl text-sm">
                <thead className="bg-surface-2 text-left text-[11px] uppercase tracking-wide text-muted">
                  <tr><th className="px-5 py-3 font-semibold">Cliente</th><th className="font-semibold">Motivo</th><th className="font-semibold">Asesor</th><th className="font-semibold">Estado</th><th className="pr-5 font-semibold">Registrada</th></tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {calls.map((c) => (
                    <tr key={c.id} className="transition hover:bg-surface-2">
                      <td className="tabular px-5 py-3 font-medium">{c.cliente}</td>
                      <td>{c.motivo}</td>
                      <td className="text-muted">{c.asesor}</td>
                      <td><span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold ${ESTADOS[c.estado]?.className ?? ""}`}>{ESTADOS[c.estado]?.label ?? c.estado}</span></td>
                      <td className="pr-5 text-muted">{ago(c.creado)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : <Empty icon={Phone}>Todavía no registraste llamadas hoy.</Empty>}
          <p className="border-t border-line px-5 py-3 text-xs text-muted">Los números se guardan protegidos y cada registro se borra a los 15 minutos; aquí solo queda el número enmascarado.</p>
        </Card>
      </div>
    </div>
  );
}

function Field({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <label className="block text-sm">
      <span className="font-medium">{label}</span>
      <input value={value} onChange={(e) => onChange(e.target.value)}
             className="mt-1.5 w-full rounded-xl border border-line bg-surface px-3.5 py-2.5 outline-none focus:border-brand focus:ring-4 focus:ring-brand/15" />
    </label>
  );
}
