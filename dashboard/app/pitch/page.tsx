"use client";

import { useRef, useState } from "react";

import { Activity, Building, Download, Play, ShieldCheck, Users } from "@/components/icons";
import { Card, Kpi, PageHeader } from "@/components/ui";

const VIDEO = "/pitch/desenmascara-pitch.mp4";
const BOT = "https://t.me/Desenmascara_bot";
// Where each part starts in the video (seconds), so the jury can jump to it.
const CHAPTERS = [
  { at: 0, title: "Doña Rosa", note: "Miles de mensajes al día que no se sabe si creer." },
  { at: 6.5, title: "El falso familiar", note: "El bot le pregunta al hijo de verdad, en su Telegram." },
  { at: 53, title: "La llamada", note: "La app de Android avisa antes de contestar." },
  { at: 70.6, title: "Llamada Verificada", note: "Cuando sí es el banco, el código lo confirma." },
  { at: 103.7, title: "El cobro falso", note: "Reporte al Banco de números y kit de denuncia." },
  { at: 123.9, title: "La red y las entidades", note: "Campañas en el Radar y alerta temprana para la empresa." },
  { at: 144.6, title: "Impacto", note: "Datos reales y lo que ya funciona." },
];
const PILLARS = [
  { icon: ShieldCheck, title: "El problema", text: "El falso familiar, el falso asesor del banco y las cobranzas falsas llegan por mensaje y por llamada. Las herramientas que existen adivinan si algo es estafa." },
  { icon: Activity, title: "La solución", text: "Reenvías el mensaje o el número a @Desenmascara_bot y en segundos recibes un semáforo con el porqué. Cuando puede, confirma con la fuente: tu familiar o tu banco." },
  { icon: Building, title: "El modelo", text: "Las entidades pagan por Llamada Verificada y por las alertas tempranas de suplantación. Para las personas es gratis." },
];
const TEAM = ["Luis Guillermo Nieto Patiño", "Miguel", "Gerhard Arce", "IngBocadillo"];

const link = "inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-semibold transition active:scale-[0.98]";

function clock(seconds: number) {
  const s = Math.floor(seconds);
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

export default function PitchPage() {
  const video = useRef<HTMLVideoElement>(null);
  const [now, setNow] = useState(0);
  const current = CHAPTERS.reduce((found, c, i) => (now >= c.at ? i : found), 0);

  function jump(at: number) {
    const v = video.current;
    if (!v) return;
    v.currentTime = at;
    v.play().catch(() => { /* the browser asks for a tap first */ });
    v.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  return (
    <div>
      <PageHeader
        title="Pitch"
        subtitle="El día de Doña Rosa · 3 minutos · Colombia 5.0 Hackathon"
        actions={<>
          <a href={BOT} rel="noopener" className={`${link} bg-brand text-white shadow-sm hover:brightness-110`}>Probar @Desenmascara_bot</a>
          <a href={VIDEO} download="Desenmascara-pitch.mp4" className={`${link} border border-line bg-surface hover:bg-surface-2`}>
            <Download width={16} height={16} /> Descargar el video
          </a>
        </>}
      />

      <div className="space-y-6">
        <div className="grid items-start gap-4 lg:grid-cols-3">
          <Card className="overflow-hidden lg:col-span-2" padded={false}>
            <video ref={video} controls playsInline preload="metadata" poster="/pitch/portada.jpg"
                   onTimeUpdate={(e) => setNow(e.currentTarget.currentTime)} className="block aspect-video w-full bg-black">
              <source src={VIDEO} type="video/mp4" />
              Tu navegador no reproduce el video: <a href={VIDEO}>descárgalo aquí</a>.
            </video>
          </Card>

          <Card title="Capítulos" icon={Play} padded={false}>
            <ol className="divide-y divide-line">
              {CHAPTERS.map((c, i) => (
                <li key={c.at}>
                  <button type="button" onClick={() => jump(c.at)} aria-current={i === current && now > 0 ? "step" : undefined}
                          className={`flex w-full gap-3 px-5 py-3 text-left transition hover:bg-surface-2 ${i === current && now > 0 ? "bg-brand-soft" : ""}`}>
                    <span className="tabular w-10 shrink-0 pt-px text-xs font-semibold text-brand-ink">{clock(c.at)}</span>
                    <span className="min-w-0">
                      <span className="block text-sm font-semibold">{c.title}</span>
                      <span className="block text-xs text-muted">{c.note}</span>
                    </span>
                  </button>
                </li>
              ))}
            </ol>
          </Card>
        </div>

        <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          <Kpi label="Estafas reales detectadas" value={20} suffix="/20" tone="brand" note="prueba con mensajes reales de Colombia" />
          <Kpi label="Falsos positivos" value={0} note="en los mensajes legítimos de la prueba" />
          <Kpi label="Dinero que pedían" value={421600} prefix="$" note="19 estafas en sus primeras horas en línea" />
          <Kpi label="Alertas al Círculo" value={11} tone="brand" note="familias avisadas a tiempo" />
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          {PILLARS.map(({ icon, title, text }) => (
            <Card key={title} title={title} icon={icon}>
              <p className="text-sm leading-relaxed text-muted">{text}</p>
            </Card>
          ))}
        </div>

        <Card title="Equipo" icon={Users}>
          <ul className="flex flex-wrap gap-2">
            {TEAM.map((name) => <li key={name} className="rounded-full border border-line bg-surface-2 px-3 py-1 text-sm font-medium">{name}</li>)}
          </ul>
          <p className="mt-4 text-xs leading-relaxed text-muted">
            Dramatización con personas de bancos de imágenes de licencia libre (Pexels) y voces sintéticas en español. BancoAndino es una
            entidad de ejemplo. Las cifras salen de datasets/casos_reales.csv y del Radar en vivo del 22 de octubre de 2026.
          </p>
        </Card>
      </div>
    </div>
  );
}
