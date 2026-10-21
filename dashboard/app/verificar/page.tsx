"use client";

import { useState } from "react";

import { Card, Chip, LevelPill, Notice, RayosX, ScoreBar } from "@/components/ui";
import { API_URL, ApiError, api, postJSON, type AnalysisResult, type Lookup } from "@/lib/api";
import { LEVELS, levelOf, n } from "@/lib/format";

type Tab = "texto" | "captura" | "numero";

const EXAMPLE = "BancoAndino: su cuenta sera suspendida hoy por actividad inusual. Valide sus datos en bancoandino-seguro.co/validar para evitar el bloqueo.";

export default function VerificarPage() {
  const [tab, setTab] = useState<Tab>("texto");
  const [text, setText] = useState(EXAMPLE);
  const [file, setFile] = useState<File | null>(null);
  const [value, setValue] = useState("");
  const [kind, setKind] = useState("telefono");
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [lookup, setLookup] = useState<Lookup | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function analyze() {
    setBusy(true);
    setError(null);
    setResult(null);
    setLookup(null);
    try {
      if (tab === "texto") {
        setResult(await postJSON<AnalysisResult>("/analyze", { text, source: "dashboard" }));
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
    <div className="space-y-5">
      <div className="flex flex-wrap items-baseline gap-3">
        <h1 className="text-3xl font-bold">Verificar un mensaje</h1>
        <span className="text-sm text-muted">usa el mismo cerebro que el bot de Telegram</span>
      </div>

      <div className="grid gap-4 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)]">
        <Card>
          <div role="tablist" className="mb-3 inline-flex rounded-lg bg-surface-2 p-1 text-sm">
            {(["texto", "captura", "numero"] as Tab[]).map((t) => (
              <button key={t} role="tab" aria-selected={tab === t} onClick={() => setTab(t)}
                      className={`rounded-md px-3 py-1.5 ${tab === t ? "bg-surface font-semibold shadow-sm" : "text-muted"}`}>
                {t === "texto" ? "Texto" : t === "captura" ? "Captura" : "Número o llave"}
              </button>
            ))}
          </div>

          {tab === "texto" && (
            <textarea value={text} onChange={(e) => setText(e.target.value)} maxLength={4000} rows={7} aria-label="Mensaje a verificar"
                      className="w-full rounded-lg border border-line bg-surface p-3 text-sm outline-none focus:border-brand" />
          )}
          {tab === "captura" && (
            <label className="flex min-h-36 cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-line p-4 text-center text-sm text-muted">
              <input type="file" accept="image/png,image/jpeg,image/webp" className="sr-only" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
              {file ? <span className="font-semibold text-ink">{file.name}</span> : "Sube una captura del mensaje (JPG, PNG o WEBP, hasta 5 MB)"}
            </label>
          )}
          {tab === "numero" && (
            <div className="flex gap-2">
              <select value={kind} onChange={(e) => setKind(e.target.value)} aria-label="Tipo"
                      className="rounded-lg border border-line bg-surface px-2 text-sm">
                <option value="telefono">Teléfono</option>
                <option value="llave">Llave Bre-B</option>
                <option value="cuenta">Cuenta</option>
              </select>
              <input value={value} onChange={(e) => setValue(e.target.value)} placeholder="+57 601 000 0000" aria-label="Número o llave"
                     className="min-w-0 flex-1 rounded-lg border border-line bg-surface px-3 py-2 text-sm outline-none focus:border-brand" />
            </div>
          )}

          <div className="mt-3 flex items-center justify-between gap-3">
            <span className="text-xs text-muted">No guardamos nombres, cédulas ni cuentas.</span>
            <button onClick={analyze} disabled={!ready || busy}
                    className="rounded-lg bg-brand px-5 py-2 text-sm font-semibold text-white disabled:opacity-50">
              {busy ? "Analizando…" : "Analizar"}
            </button>
          </div>

          {result && (
            <div className="mt-5 space-y-4">
              {result.extracted_text && (
                <div>
                  <h3 className="mb-1 text-sm font-semibold">Texto leído de la captura</h3>
                  <p className="whitespace-pre-line rounded-lg bg-surface-2 p-3 text-xs">{result.extracted_text}</p>
                </div>
              )}
              {result.recognized.length > 0 && (
                <div>
                  <h3 className="mb-2 text-sm font-semibold">Lo que reconoció</h3>
                  <div className="flex flex-wrap gap-2">{result.recognized.map((r) => <Chip key={r}>{r}</Chip>)}</div>
                </div>
              )}
              {result.campaign && (
                <div>
                  <h3 className="mb-2 text-sm font-semibold">Parecido a</h3>
                  <div className="rounded-lg border border-risk-high/30 bg-risk-high-bg px-3 py-2 text-sm">
                    <div className="font-semibold">{result.campaign.name}</div>
                    <div className="text-xs text-risk-high">
                      ▲ {n(result.campaign.total_reports_today)} reportes hoy · parecido {result.campaign.similarity_pct} %
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </Card>

        <div className="space-y-4">
          {error && <Notice>{error}</Notice>}
          {!result && !lookup && !error && (
            <Card><p className="py-16 text-center text-sm text-muted">Pega un mensaje o sube una captura y toca «Analizar».</p></Card>
          )}
          {result && <ResultCard result={result} />}
          {lookup && <LookupCard lookup={lookup} />}
        </div>
      </div>
      <p className="text-xs text-muted">API: {API_URL} · entidad y dominio de los ejemplos ficticios</p>
    </div>
  );
}

function ResultCard({ result }: { result: AnalysisResult }) {
  const style = LEVELS[result.risk_level];
  return (
    <Card>
      <div className={`flex flex-wrap items-center gap-4 rounded-lg px-4 py-3 ${style.bg}`}>
        {result.risk_level !== "inconclusive" && (
          <div className={`tabular text-5xl font-bold ${style.text}`}>
            {result.risk_score}<span className="text-base font-semibold">/100</span>
          </div>
        )}
        <div>
          <div className={`font-bold ${style.text}`}>● {style.word}</div>
          <div className="text-sm">{result.category ?? result.summary}</div>
        </div>
        <span className="ml-auto text-xs text-muted">{(result.processing_ms / 1000).toLocaleString("es-CO", { maximumFractionDigits: 1 })} s</span>
      </div>
      {result.risk_level !== "inconclusive" && <div className="mt-5"><ScoreBar score={result.risk_score} /></div>}
      <h3 className="mb-3 mt-6 text-base font-semibold">
        Rayos X del puntaje <span className="text-xs font-normal text-muted">· cuántos puntos sumó cada revisión</span>
      </h3>
      <RayosX signals={result.signals} />
      {result.recommendations.length > 0 && (
        <p className="mt-5 rounded-lg bg-mint px-4 py-3 text-sm">
          <strong className="text-brand-ink">Qué hacer:</strong> {result.recommendations.join(" ")}
        </p>
      )}
      {result.limitations.length > 0 && <p className="mt-3 text-xs text-muted">{result.limitations.join(" ")}</p>}
    </Card>
  );
}

function LookupCard({ lookup }: { lookup: Lookup }) {
  const level = lookup.oficial_de ? "low" : lookup.estado === "en_revision" ? "medium" : levelOf(lookup.nivel);
  return (
    <Card>
      <div className="flex flex-wrap items-center gap-3">
        <div className="tabular text-5xl font-bold">{lookup.nivel}<span className="text-base text-muted">/100</span></div>
        <LevelPill level={level} word={lookup.palabra} />
      </div>
      <div className="mt-5"><ScoreBar score={lookup.nivel} /></div>
      <dl className="mt-6 grid grid-cols-2 gap-3 text-sm">
        <div><dt className="text-muted">Personas distintas que lo reportaron</dt><dd className="tabular text-2xl font-bold">{n(lookup.personas)}</dd></div>
        <div><dt className="text-muted">Reportes</dt><dd className="tabular text-2xl font-bold">{n(lookup.reportes)}</dd></div>
        {lookup.modalidad && <div><dt className="text-muted">Modalidad</dt><dd>{lookup.modalidad}</dd></div>}
        {lookup.oficial_de && <div><dt className="text-muted">Número oficial de</dt><dd className="font-semibold">{lookup.oficial_de}</dd></div>}
      </dl>
      <p className="mt-5 text-xs text-muted">
        Nunca decimos «estafador»: mostramos cuántas personas distintas lo reportaron. En llamadas, un número se puede falsificar.
      </p>
    </Card>
  );
}
