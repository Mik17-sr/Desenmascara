export type Level = "low" | "medium" | "high" | "inconclusive";

export const LEVELS: Record<Level, { word: string; text: string; bg: string; dot: string }> = {
  high: { word: "ALTO RIESGO", text: "text-risk-high", bg: "bg-risk-high-bg", dot: "bg-risk-high" },
  medium: { word: "SOSPECHOSO", text: "text-risk-mid-ink", bg: "bg-risk-mid-bg", dot: "bg-risk-mid" },
  low: { word: "BAJO RIESGO", text: "text-risk-low", bg: "bg-risk-low-bg", dot: "bg-risk-low" },
  inconclusive: { word: "NO CONCLUYENTE", text: "text-muted", bg: "bg-surface-2", dot: "bg-muted" },
};

export function levelOf(score: number): Level {
  return score >= 70 ? "high" : score >= 40 ? "medium" : "low";
}

const number = new Intl.NumberFormat("es-CO");

export function n(value: number): string {
  return number.format(value);
}

export function ago(iso: string | null | undefined): string {
  if (!iso) return "";
  const seconds = Math.max(0, (Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return "hace un momento";
  if (seconds < 3600) return `hace ${Math.round(seconds / 60)} min`;
  if (seconds < 86400) return `hace ${Math.round(seconds / 3600)} h`;
  const days = Math.round(seconds / 86400);
  return days === 1 ? "ayer" : `hace ${days} días`;
}

export const DETECTIVES: Record<string, string> = {
  traductor: "El traductor",
  pistas: "El que subraya pistas",
  enlaces: "Detective de enlaces",
  psicologo: "Psicólogo (IA)",
  archivista: "Archivista",
  juez: "El juez",
  banco: "Banco de números",
};
