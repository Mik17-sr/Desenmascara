"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { Activity, Megaphone, Search } from "@/components/icons";
import { Button, Card, Empty, Notice, Skeleton } from "@/components/ui";
import { ApiError, api, postJSON, type CampanasEquipo, type CasoTraza } from "@/lib/api";
import { ago, plural } from "@/lib/format";

const field = "w-full rounded-xl border border-line bg-surface px-3 py-2 text-sm outline-none focus:border-brand focus:ring-4 focus:ring-brand/15";

type Props = { teamKey: string; onMessage: (message: string) => void; onUnauthorized: () => void };
type SaveBody = { regla: boolean; descripcion: string; nombre?: string; estado?: string };

/** The team identifies campaigns: describes them for the bot to quote, and turns them into rules. */
export function CampanasDelEquipo({ teamKey, onMessage, onUnauthorized }: Props) {
  const [data, setData] = useState<CampanasEquipo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  // The page passes a new function on every refresh: read it through a ref so the list is not fetched again each time.
  const unauthorized = useRef(onUnauthorized);
  useEffect(() => { unauthorized.current = onUnauthorized; }, [onUnauthorized]);
  const fail = useCallback((e: unknown) => {
    if (e instanceof ApiError && e.status === 401) unauthorized.current();
    setError(e instanceof Error ? e.message : "Error");
  }, []);

  const load = useCallback(() => {
    api<CampanasEquipo>("/equipo/campanas", { headers: { "X-Admin-Key": teamKey } }).then(setData).catch(fail);
  }, [teamKey, fail]);
  useEffect(load, [load]);

  async function save(id: string, body: SaveBody) {
    setError(null);
    try {
      await postJSON(`/equipo/campanas/${id}`, { ...body, revisada_por: "equipo" }, { "X-Admin-Key": teamKey });
      setEditing(null);
      onMessage(body.estado === "descartada" ? "Campaña descartada: el bot deja de mencionarla."
        : body.regla ? "Campaña identificada: ahora es una regla y el bot cita su descripción." : "Campaña guardada.");
      load();
    } catch (e) { fail(e); }
  }

  const campaigns = data?.campanas ?? [];
  return (
    <Card title="Campañas · identificación del equipo" icon={Megaphone} padded={false}
          action={data && <span className="text-xs text-muted">{plural(campaigns.length, "campaña", "campañas")} · regla automática desde {data.regla_automatica} reportes</span>}>
      <p className="border-b border-line px-5 py-3 text-xs text-muted">
        Una campaña identificada se vuelve <strong className="text-ink">regla</strong>: el bot la reconoce sin límite de días, sube el
        riesgo y responde «Campaña identificada por Desenmascara» con tu descripción.
      </p>
      {error && <div className="p-4"><Notice>{error}</Notice></div>}
      {!data ? <div className="space-y-2 p-5">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-14" />)}</div> : campaigns.length ? (
        <ul className="divide-y divide-line">
          {campaigns.map((c) => (
            <li key={c.id} className="px-5 py-4 text-sm">
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <div className="font-semibold">{c.nombre}</div>
                  <div className="mt-0.5 text-xs text-muted">
                    {(c.modalidad && data.modalidades[c.modalidad]) || "Sin modalidad"} · {plural(c.reportes, "reporte", "reportes")} · {ago(c.ultimo)}
                  </div>
                </div>
                <div className="flex shrink-0 flex-wrap items-center gap-1.5">
                  {c.estado === "descartada" ? <Badge tone="muted">Descartada</Badge>
                    : c.regla ? <Badge tone="brand">Regla del equipo</Badge>
                    : c.regla_automatica ? <Badge tone="amber">Regla automática</Badge> : <Badge tone="muted">Detectada</Badge>}
                  <Button variant="ghost" className="px-3 py-1.5 text-xs" onClick={() => setEditing(editing === c.id ? null : c.id)}>
                    {c.regla ? "Editar" : "Identificar"}
                  </Button>
                </div>
              </div>
              {c.descripcion && <p className="mt-2 rounded-lg bg-brand-soft px-3 py-2 text-xs text-brand-ink">{c.descripcion}</p>}
              {c.ejemplo && <p className="mt-2 line-clamp-2 text-xs italic text-muted">«{c.ejemplo}»</p>}
              {editing === c.id && <EditCampaign campaign={c} onSave={(body) => save(c.id, body)} onCancel={() => setEditing(null)} />}
            </li>
          ))}
        </ul>
      ) : <Empty icon={Megaphone}>Todavía no hay campañas detectadas.</Empty>}
      <div className="border-t border-line p-5">
        {creating
          ? <NewCampaign teamKey={teamKey} modalidades={data?.modalidades ?? {}} onDone={(m) => { setCreating(false); onMessage(m); load(); }}
                         onError={fail} onCancel={() => setCreating(false)} />
          : <Button variant="ghost" className="w-full" onClick={() => setCreating(true)}>+ Nueva campaña desde un mensaje de ejemplo</Button>}
      </div>
    </Card>
  );
}

function Badge({ tone, children }: { tone: "brand" | "amber" | "muted"; children: React.ReactNode }) {
  const cls = tone === "brand" ? "bg-brand-soft text-brand-ink" : tone === "amber" ? "bg-risk-mid-bg text-risk-mid-ink" : "bg-surface-2 text-muted";
  return <span className={`rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${cls}`}>{children}</span>;
}

function EditCampaign({ campaign, onSave, onCancel }: {
  campaign: CampanasEquipo["campanas"][number]; onSave: (body: SaveBody) => void; onCancel: () => void;
}) {
  const [nombre, setNombre] = useState(campaign.nombre);
  const [descripcion, setDescripcion] = useState(campaign.descripcion ?? "");
  const [regla, setRegla] = useState(true);
  return (
    <form className="mt-3 space-y-2 rounded-xl border border-line bg-surface-2 p-3" onSubmit={(e) => { e.preventDefault(); onSave({ regla, descripcion, nombre }); }}>
      <label className="block text-xs font-semibold text-muted">
        Nombre que verá la persona
        <input value={nombre} onChange={(e) => setNombre(e.target.value)} maxLength={120} className={`${field} mt-1 font-normal text-ink`}
               placeholder="Falso Credivalores · descuento de deuda" />
      </label>
      <label className="block text-xs font-semibold text-muted">
        Cómo funciona, en palabras simples (el bot lo cita)
        <textarea value={descripcion} onChange={(e) => setDescripcion(e.target.value)} rows={3} maxLength={400} className={`${field} mt-1 font-normal text-ink`}
                  placeholder="Ofrecen un descuento para quedar a paz y salvo y piden pagar por WhatsApp. La empresa no cobra así." />
      </label>
      <label className="flex items-center gap-2 text-sm">
        <input type="checkbox" checked={regla} onChange={(e) => setRegla(e.target.checked)} className="h-4 w-4 accent-brand" />
        Usar como regla: reconocerla sin límite de días
      </label>
      <div className="flex flex-wrap justify-end gap-2">
        <Button type="button" variant="ghost" className="px-3 py-1.5 text-xs" onClick={() => onSave({ regla: false, descripcion, estado: "descartada" })}>No es una estafa: descartar</Button>
        <Button type="button" variant="ghost" className="px-3 py-1.5 text-xs" onClick={onCancel}>Cancelar</Button>
        <Button className="px-3 py-1.5 text-xs" disabled={regla && descripcion.trim().length < 10}>Guardar</Button>
      </div>
    </form>
  );
}

function NewCampaign({ teamKey, modalidades, onDone, onError, onCancel }: {
  teamKey: string; modalidades: Record<string, string>; onDone: (message: string) => void; onError: (e: unknown) => void; onCancel: () => void;
}) {
  const [nombre, setNombre] = useState("");
  const [modalidad, setModalidad] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [ejemplo, setEjemplo] = useState("");

  async function create() {
    try {
      await postJSON("/equipo/campanas", { nombre, modalidad: modalidad || null, descripcion, ejemplo, revisada_por: "equipo" }, { "X-Admin-Key": teamKey });
      onDone(`Campaña «${nombre}» creada como regla: el bot ya la reconoce.`);
    } catch (e) { onError(e); }
  }

  return (
    <form className="space-y-2" onSubmit={(e) => { e.preventDefault(); create(); }}>
      <div className="text-xs font-semibold uppercase tracking-wide text-muted">Nueva campaña</div>
      <div className="grid gap-2 sm:grid-cols-2">
        <input value={nombre} onChange={(e) => setNombre(e.target.value)} aria-label="Nombre" placeholder="Falso Ingreso Solidario 2026" className={field} />
        <select value={modalidad} onChange={(e) => setModalidad(e.target.value)} aria-label="Modalidad" className={field}>
          <option value="">Modalidad…</option>
          {Object.entries(modalidades).filter(([k]) => k !== "otra").map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
      </div>
      <textarea value={descripcion} onChange={(e) => setDescripcion(e.target.value)} rows={2} maxLength={400} aria-label="Descripción" className={field}
                placeholder="Cómo funciona: dicen que un subsidio está aprobado y piden la cédula y la cuenta." />
      <textarea value={ejemplo} onChange={(e) => setEjemplo(e.target.value)} rows={3} maxLength={4000} aria-label="Mensaje de ejemplo" className={field}
                placeholder="Pega un mensaje real de la campaña, sin nombres ni números de personas." />
      <div className="flex justify-end gap-2">
        <Button type="button" variant="ghost" onClick={onCancel}>Cancelar</Button>
        <Button disabled={nombre.length < 4 || descripcion.length < 10 || ejemplo.length < 20}>Crear regla</Button>
      </div>
    </form>
  );
}

/** Registro trazable: the team follows any case by its reference DSM-XXXXXXXX, without relatives' names. */
export function CasoDelEquipo({ teamKey, onUnauthorized }: { teamKey: string; onUnauthorized: () => void }) {
  const [ref, setRef] = useState("");
  const [caso, setCaso] = useState<CasoTraza | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function find() {
    setError(null);
    setCaso(null);
    try {
      setCaso(await api<CasoTraza>(`/equipo/casos/${encodeURIComponent(ref.trim())}`, { headers: { "X-Admin-Key": teamKey } }));
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) onUnauthorized();
      setError(e instanceof Error ? e.message : "Error");
    }
  }

  return (
    <Card title="Seguimiento de un caso" icon={Activity}>
      <form className="flex gap-2" onSubmit={(e) => { e.preventDefault(); find(); }}>
        <input value={ref} onChange={(e) => setRef(e.target.value)} aria-label="Referencia del caso" placeholder="DSM-1A2B3C4D" className={`${field} tabular uppercase`} />
        <Button disabled={ref.trim().length < 8}><Search width={16} height={16} /> Buscar</Button>
      </form>
      {error && <p className="mt-3 text-xs text-risk-high">{error}</p>}
      {caso && (
        <div className="mt-4 space-y-3 text-sm">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="tabular font-bold">{caso.referencia}</span>
            <span className="rounded-full bg-surface-2 px-2.5 py-0.5 text-xs font-semibold">{caso.estado}</span>
          </div>
          <ol className="space-y-2 border-l-2 border-line pl-4">
            {caso.eventos.map((e, i) => (
              <li key={i}>
                <div className="text-xs text-muted">{e.cuando}</div>
                <div className="font-semibold">{e.paso}</div>
                <div className="text-muted">{e.detalle}</div>
              </li>
            ))}
          </ol>
          {caso.texto && <p className="line-clamp-3 rounded-lg bg-surface-2 px-3 py-2 text-xs italic text-muted">«{caso.texto}»</p>}
        </div>
      )}
      <p className="mt-3 text-xs text-muted">La persona ve el mismo registro con /caso en el bot. Aquí los familiares aparecen como «un familiar».</p>
    </Card>
  );
}
