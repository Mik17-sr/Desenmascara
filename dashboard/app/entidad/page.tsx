"use client";

import { useCallback, useEffect, useState } from "react";

import { Building, CheckCircle, Copy, Key, Logout, Phone, ShieldCheck } from "@/components/icons";
import { Button, Card, Empty, Notice, PageHeader } from "@/components/ui";
import { ApiError, api, postJSON, type Llamada } from "@/lib/api";
import { ago } from "@/lib/format";
import { useDemo } from "@/lib/useDemo";
import { useLive } from "@/lib/useLive";

const KEY = "desenmascara.entidad"; // the panel session, never the API key
const TTL_MS = 15 * 60 * 1000;
const ESTADOS: Record<string, { label: string; className: string }> = {
  registrada: { label: "Esperando al cliente", className: "bg-risk-mid-bg text-risk-mid-ink" },
  confirmada: { label: "Verificada por el cliente", className: "bg-risk-low-bg text-risk-low" },
  vencida: { label: "Vencida (no preguntó)", className: "bg-surface-2 text-muted" },
};
const INPUT = "mt-1.5 w-full rounded-xl border border-line bg-surface py-2.5 pr-3 text-sm outline-none focus:border-brand focus:ring-4 focus:ring-brand/15";

type Registro = { codigo_verificacion: string; vence_at: string };
type Sesion = { token: string; nombre: string };

// "Recordar en este equipo" keeps the session in localStorage (30 days) until "Cerrar sesión"; otherwise it
// lasts while the tab is open (12 hours at most). Storage can be blocked: then the entity signs in again.
function savedSession(): { value: string; remembered: boolean } {
  try {
    const kept = localStorage.getItem(KEY);
    return kept ? { value: kept, remembered: true } : { value: sessionStorage.getItem(KEY) ?? "", remembered: false };
  } catch {
    return { value: "", remembered: false };
  }
}
function forgetSession() {
  try { localStorage.removeItem(KEY); sessionStorage.removeItem(KEY); } catch { /* storage blocked */ }
}
function keepSession(token: string, remember: boolean) {
  forgetSession();
  try { (remember ? localStorage : sessionStorage).setItem(KEY, token); } catch { /* storage blocked */ }
}
const bearer = (token: string) => ({ Authorization: `Bearer ${token}` });

export default function EntidadPage() {
  const [correo, setCorreo] = useState("");
  const [clave, setClave] = useState("");
  const [remember, setRemember] = useState(true);
  const [session, setSession] = useState<Sesion | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [checking, setChecking] = useState(true);
  const [busy, setBusy] = useState(false);
  const demo = useDemo();

  const start = useCallback((s: Sesion, keep: boolean) => {
    keepSession(s.token, keep);
    setSession(s);
  }, []);

  async function signIn() {
    setError(null);
    setBusy(true);
    try {
      start(await postJSON<Sesion>("/entidad/ingresar", { correo, clave, recordar: remember }), remember);
      setClave("");
    } catch (e) {
      setError(e instanceof ApiError && e.status === 401 ? "Correo o contraseña incorrectos."
        : e instanceof ApiError && e.status === 429 ? "Demasiados intentos. Espera un minuto e inténtalo de nuevo."
        : e instanceof Error ? e.message : "Error");
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    // A sign-in link (/entidad#llave=…, printed by crear_entidad.py or seed_demo.py) carries the API key: it is
    // swapped for a session and taken out of the address bar. A key remembered by an older version is swapped too.
    const fromLink = new URLSearchParams(window.location.hash.slice(1)).get("llave");
    if (fromLink) history.replaceState(null, "", window.location.pathname);
    const saved = savedSession();
    const restore = async () => {
      const key = fromLink ?? (saved.value.startsWith("sec_live_") ? saved.value : null);
      if (key) {
        start(await postJSON<Sesion>("/entidad/sesion", { recordar: true }, { "X-Entity-API-Key": key }), fromLink ? true : saved.remembered);
      } else if (saved.value) {
        const me = await api<{ nombre: string }>("/entidad/yo", { headers: bearer(saved.value) });
        setSession({ token: saved.value, nombre: me.nombre });
      }
    };
    restore()
      .catch((e) => { if (e instanceof ApiError && e.status === 401) forgetSession(); })
      .finally(() => setChecking(false));
  }, [start]);

  if (checking) return <div className="mx-auto max-w-md py-24"><div className="skeleton h-40" /></div>;
  if (!session) {
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
          <form className="space-y-4" onSubmit={(e) => { e.preventDefault(); signIn(); }}>
            <div className="flex items-center gap-3">
              <span className="grid h-11 w-11 place-items-center rounded-2xl bg-brand-soft text-brand-ink"><Building /></span>
              <div><div className="font-semibold">Acceso para entidades</div><div className="text-xs text-muted">Bancos, operadores y tiendas</div></div>
            </div>
            <label className="block text-sm font-medium">
              Correo
              <input type="email" value={correo} onChange={(e) => setCorreo(e.target.value)} autoComplete="username" placeholder="panel@tuentidad.com"
                     className={`${INPUT} pl-3`} />
            </label>
            <label className="block text-sm font-medium">
              Contraseña
              <div className="relative">
                <Key className="pointer-events-none absolute left-3 top-[60%] -translate-y-1/2 text-muted" width={16} height={16} />
                <input type="password" value={clave} onChange={(e) => setClave(e.target.value)} autoComplete="current-password" className={`${INPUT} pl-9`} />
              </div>
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} className="h-4 w-4 accent-brand" />
              Recordar en este equipo
            </label>
            <Button disabled={!correo || !clave || busy} className="w-full py-2.5">{busy ? "Entrando…" : "Entrar al panel"}</Button>
            {error && <Notice>{error}</Notice>}
            <p className="text-xs text-muted">{demo
              ? "Demostración: python scripts/seed_demo.py muestra el correo y la contraseña de BancoAndino (entidad ficticia)."
              : "El correo y la contraseña te los entrega el equipo de Desenmascara cuando conecta tu entidad a Llamada Verificada."}</p>
          </form>
        </Card>
      </div>
    );
  }
  return <Panel entity={session.nombre} token={session.token} onLogout={() => { setSession(null); forgetSession(); }} />;
}

function Panel({ entity, token, onLogout }: { entity: string; token: string; onLogout: () => void }) {
  const [telefono, setTelefono] = useState("+57 310 000 0000");
  const [motivo, setMotivo] = useState("Confirmar una compra");
  const [asesor, setAsesor] = useState("Laura M.");
  const [registro, setRegistro] = useState<Registro | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [now, setNow] = useState(Date.now());

  const load = useCallback(() => api<Llamada[]>("/llamadas/hoy", { headers: bearer(token) }), [token]);
  const { data: calls, refresh } = useLive(load, 4000);

  useEffect(() => {
    const tick = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(tick);
  }, []);

  async function register() {
    setError(null);
    setCopied(false);
    try {
      setRegistro(await postJSON<Registro>("/llamadas/registrar", { telefono_cliente: telefono, motivo, asesor }, bearer(token)));
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
