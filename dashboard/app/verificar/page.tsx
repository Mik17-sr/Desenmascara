"use client";

import { useState } from "react";

import { Activity, AlertTriangle, CheckCircle, Database, ImageIcon, Link2, Message, Phone, ShieldCheck } from "@/components/icons";
import { Button, Card, Chip, Empty, LevelPill, Notice, PageHeader, RayosX, ScoreGauge, Skeleton } from "@/components/ui";
import { ApiError, api, postJSON, type AnalysisResult, type Lookup } from "@/lib/api";
import { LEVELS, levelOf, n, plural } from "@/lib/format";

type Tab = "texto" | "captura" | "numero";
const TABS: { id: Tab; label: string; icon: typeof Message }[] = [
  { id: "texto", label: "Texto", icon: Message },
  { id: "captura", label: "Captura", icon: ImageIcon },
  { id: "numero", label: "Número o llave", icon: Phone },
];
const EXAMPLES = [
  { label: "SMS de falso banco", text: "BancoAndino: su cuenta sera suspendida hoy por actividad inusual. Valide sus datos en bancoandino-seguro.co/validar para evitar el bloqueo." },
  { label: "Falso familiar", text: "Hola ma, cambié de número, guarda este. Necesito que me hagas una transferencia urgente, después te explico." },
  { label: "Compra con anticipo", text: "Vendo celular nuevo y sellado a $900.000, precio de locura solo hoy. Si me envías $450.000 a la llave Bre-B 315 000 0000 te lo aparto." },
  { label: "Mensaje legítimo", text: "Tu pedido #48213 llegará mañana entre 8:00 a. m. y 12:00 m. Sigue el envío en la app oficial." },
];

export default function VerificarPage() {
  const [tab, setTab] = useState<Tab>("texto");
  const [text, setText] = useState(EXAMPLES[0].text);
  const [file, setFile] = useState<File | null>(null);
  const [value, setValue] = useState("");
  const [kind, setKind] = useState("telefono");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [lookup, setLookup] = useState<Lookup | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function analyze(override?: string) {
    setBusy(true);
    setError(null);
    setResult(null);
    setLookup(null);
    try {
      if (tab === "texto" || override) {
        setResult(await postJSON<AnalysisResult>("/analyze", { text: override ?? text, source: "dashboard" }));
      } else if (tab === "captura" && file) {
        const form = new FormData();
        form.append("file", file);
        form.append("source", "dashboard");
        setResult(await api<AnalysisResult>("/analyze/imagen", { method: "POST", body: form }));
      } else if (tab === "numero") {
        setLookup(await api<Lookup>(`/banco/consultar?tipo=${kind}&valor=${encodeURIComponent(value)}`));
      }
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "No se pudo analizar.");
    } finally {
      setBusy(false);
    }
  }

  const ready = tab === "texto" ? text.trim().length > 0 : tab === "captura" ? !!file : value.trim().length >= 3;

  return (
    <div>
      <PageHeader title="Verificar un mensaje" subtitle="El mismo cerebro de seis revisiones que usa el bot de Telegram, con los Rayos X del puntaje." />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
        <div className="space-y-6">
          <Card>
            <div role="tablist" className="grid grid-cols-3 gap-1 rounded-xl bg-surface-2 p-1 text-sm">
              {TABS.map(({ id, label, icon: Icon }) => (
                <button key={id} role="tab" aria-selected={tab === id} onClick={() => setTab(id)}
                        className={`flex items-center justify-center gap-2 rounded-lg px-2 py-2 font-medium transition ${tab === id ? "bg-surface text-ink shadow-card" : "text-muted hover:text-ink"}`}>
                  <Icon width={16} height={16} /><span className="truncate">{label}</span>
                </button>
              ))}
            </div>

            <div className="mt-4">
              {tab === "texto" && (
                <>
                  <textarea value={text} onChange={(e) => setText(e.target.value)} maxLength={4000} rows={7} aria-label="Mensaje a verificar"
                            className="w-full resize-y rounded-xl border border-line bg-surface p-3.5 text-sm leading-relaxed outline-none transition focus:border-brand focus:ring-4 focus:ring-brand/15" />
                  <div className="mt-1 text-right text-[11px] text-muted tabular">{text.length} / 4000</div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {EXAMPLES.map((ex) => (
                      <button key={ex.label} onClick={() => { setText(ex.text); analyze(ex.text); }} disabled={busy}
                              className="rounded-full border border-line px-3 py-1 text-xs font-medium text-muted transition hover:border-brand hover:text-brand-ink disabled:opacity-50">
                        {ex.label}
                      </button>
                    ))}
                  </div>
                </>
              )}
              {tab === "captura" && (
                <label className="flex min-h-44 cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed border-line p-6 text-center text-sm text-muted transition hover:border-brand hover:bg-brand-soft/40">
                  <input type="file" accept="image/png,image/jpeg,image/webp" className="sr-only" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
                  <span className="grid h-12 w-12 place-items-center rounded-2xl bg-brand-soft text-brand-ink"><ImageIcon /></span>
                  {file ? <span className="font-semibold text-ink">{file.name}</span> : <span>Arrastra o elige una captura del mensaje<br /><span className="text-xs">JPG, PNG o WEBP · hasta 5 MB</span></span>}
                </label>
              )}
              {tab === "numero" && (
                <div className="flex flex-col gap-2 sm:flex-row">
                  <select value={kind} onChange={(e) => setKind(e.target.value)} aria-label="Tipo"
                          className="rounded-xl border border-line bg-surface px-3 py-2.5 text-sm">
                    <option value="telefono">Teléfono</option>
                    <option value="llave">Llave Bre-B</option>
                    <option value="cuenta">Cuenta</option>
                  </select>
                  <input value={value} onChange={(e) => setValue(e.target.value)} placeholder="+57 601 000 0000" aria-label="Número o llave"
                         className="min-w-0 flex-1 rounded-xl border border-line bg-surface px-3.5 py-2.5 text-sm outline-none focus:border-brand focus:ring-4 focus:ring-brand/15" />
                </div>
              )}
            </div>

            <div className="mt-4 flex flex-wrap items-center justify-between gap-3 border-t border-line pt-4">
              <span className="text-xs text-muted">No guardamos nombres, cédulas ni cuentas.</span>
              <Button onClick={() => analyze()} disabled={!ready || busy}>
                {busy ? <><span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" /> Analizando…</> : <><ShieldCheck width={16} height={16} /> Analizar</>}
              </Button>
            </div>
          </Card>

          {result && (result.recognized.length > 0 || result.campaign || result.extracted_text) && (
            <Card title="Lo que reconoció" icon={Activity}>
              <div className="space-y-4">
                {result.extracted_text && (
                  <div>
                    <div className="mb-1 text-xs font-semibold uppercase tracking-wide text-muted">Texto leído de la captura</div>
                    <p className="whitespace-pre-line rounded-xl bg-surface-2 p-3 text-xs">{result.extracted_text}</p>
                  </div>
                )}
                {result.recognized.length > 0 && <div className="flex flex-wrap gap-2">{result.recognized.map((r) => <Chip key={r}>{r}</Chip>)}</div>}
                {result.campaign && (
                  <div className="rounded-xl border border-risk-high/30 bg-risk-high-bg px-4 py-3 text-sm">
                    <div className="text-xs font-semibold uppercase tracking-wide text-risk-high">Parecido a una campaña</div>
                    <div className="mt-0.5 font-semibold">{result.campaign.name}</div>
                    <div className="text-xs text-risk-high">{plural(result.campaign.total_reports_today, "reporte", "reportes")} hoy · parecido {result.campaign.similarity_pct} %</div>
                  </div>
                )}
              </div>
            </Card>
          )}
        </div>

        <div className="space-y-6">
          {error && <Notice>{error}</Notice>}
          {busy && <Card><div className="space-y-4"><Skeleton className="mx-auto h-32 w-64" /><Skeleton className="h-4" /><Skeleton className="h-4 w-4/5" /><Skeleton className="h-4 w-3/5" /></div></Card>}
          {!busy && !result && !lookup && !error && (
            <Card><Empty icon={ShieldCheck}>Pega un mensaje, sube una captura o prueba uno de los ejemplos.<br />Verás el semáforo y cuántos puntos sumó cada revisión.</Empty></Card>
          )}
          {result && <ResultCard result={result} />}
          {lookup && <LookupCard lookup={lookup} />}
        </div>
      </div>
    </div>
  );
}

function ResultCard({ result }: { result: AnalysisResult }) {
  const style = LEVELS[result.risk_level];
  return (
    <Card padded={false}>
      <div className={`grid gap-6 rounded-t-2xl p-6 sm:grid-cols-[minmax(0,260px)_1fr] sm:items-center ${style.bg}`}>
        {result.risk_level === "inconclusive"
          ? <div className="grid place-items-center py-6 text-muted"><AlertTriangle width={40} height={40} /></div>
          : <ScoreGauge score={result.risk_score} level={result.risk_level} />}
        <div>
          <div className={`text-xl font-bold ${style.text}`}>● {style.word}</div>
          <div className="mt-1 text-lg font-semibold">{result.category ?? result.summary}</div>
          <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted">
            <span className="rounded-full bg-surface/70 px-2.5 py-1">{result.signals.length} señales</span>
            <span className="rounded-full bg-surface/70 px-2.5 py-1 tabular">{(result.processing_ms / 1000).toLocaleString("es-CO", { maximumFractionDigits: 1 })} s</span>
          </div>
        </div>
      </div>
      <div className="space-y-6 p-6">
        <div>
          <h3 className="mb-4 text-sm font-semibold">Rayos X del puntaje <span className="font-normal text-muted">· cuántos puntos sumó cada revisión</span></h3>
          <RayosX signals={result.signals} />
        </div>
        {result.recommendations.length > 0 && (
          <div className="flex gap-3 rounded-xl border border-brand/30 bg-brand-soft p-4 text-sm">
            <CheckCircle className="mt-0.5 shrink-0 text-brand-ink" />
            <p><strong className="text-brand-ink">Qué hacer:</strong> {result.recommendations.join(" ")}</p>
          </div>
        )}
        {result.limitations.length > 0 && <p className="text-xs text-muted">{result.limitations.join(" ")}</p>}
      </div>
    </Card>
  );
}

function LookupCard({ lookup }: { lookup: Lookup }) {
  const level = lookup.oficial_de ? "low" : lookup.estado === "en_revision" ? "medium" : levelOf(lookup.nivel);
  return (
    <Card padded={false}>
      <div className={`grid gap-6 rounded-t-2xl p-6 sm:grid-cols-[minmax(0,260px)_1fr] sm:items-center ${LEVELS[level].bg}`}>
        <ScoreGauge score={lookup.nivel} level={level} />
        <div>
          <LevelPill level={level} word={lookup.palabra} />
          <div className="mt-2 text-lg font-semibold tabular">{lookup.valor ?? "Sin reportes"}</div>
          {lookup.oficial_de && <div className="mt-1 text-sm text-brand-ink">Número oficial de {lookup.oficial_de}</div>}
        </div>
      </div>
      <div className="grid gap-4 p-6 sm:grid-cols-3">
        <Stat icon={Database} label="Personas distintas" value={n(lookup.personas)} />
        <Stat icon={Activity} label="Reportes" value={n(lookup.reportes)} />
        <Stat icon={Link2} label="Modalidad" value={lookup.modalidad ?? "—"} />
        <p className="text-xs text-muted sm:col-span-3">Nunca decimos «estafador»: mostramos cuántas personas distintas lo reportaron. En llamadas, un número se puede falsificar.</p>
      </div>
    </Card>
  );
}

function Stat({ icon: Icon, label, value }: { icon: typeof Activity; label: string; value: string }) {
  return (
    <div className="rounded-xl bg-surface-2 p-4">
      <div className="flex items-center gap-2 text-xs text-muted"><Icon width={14} height={14} />{label}</div>
      <div className="mt-1 text-xl font-bold tabular">{value}</div>
    </div>
  );
}
