// The Dashboard only reads anonymous, aggregated views of the API (guide section 16).
export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000/api/v1";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, { cache: "no-store", ...init });
  } catch {
    throw new ApiError(0, "No hay conexión con la API. ¿Está corriendo en el puerto 8000?");
  }
  if (!response.ok) {
    let detail = "";
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : "";
    } catch {
      /* the body was not JSON */
    }
    throw new ApiError(response.status, detail || `La API respondió ${response.status}.`);
  }
  return response.json() as Promise<T>;
}

export function postJSON<T>(path: string, body: unknown, headers: Record<string, string> = {}): Promise<T> {
  return api<T>(path, { method: "POST", headers: { "Content-Type": "application/json", ...headers }, body: JSON.stringify(body) });
}

export type Signal = { code: string; label: string; evidence: string; source: string; points: number };

export type AnalysisResult = {
  risk_level: "low" | "medium" | "high" | "inconclusive";
  risk_score: number;
  summary: string;
  category: string | null;
  signals: Signal[];
  recommendations: string[];
  recognized: string[];
  campaign: { campaign_id: string; name: string; similarity_pct: number; total_reports_today: number } | null;
  extracted_text: string | null;
  limitations: string[];
  processing_ms: number;
};

export type Lookup = {
  encontrado: boolean;
  valor?: string;
  nivel: number;
  palabra: string;
  personas: number;
  reportes: number;
  modalidad?: string | null;
  estado?: string;
  oficial_de?: string | null;
};

export type Radar = {
  actualizado: string;
  verificaciones_hoy: number;
  verificaciones_ayer: number;
  alto_riesgo_pct: number;
  alto_riesgo_total: number;
  llamadas_reportadas: number;
  llamadas_verificadas: number;
  campanas_activas: number;
  tiempo_respuesta_s: number;
  tipos_de_estafa: { tipo: string; total: number }[];
  reportes_por_hora: { hora: number; total: number }[];
  campanas: { id: string; nombre: string; reportes: number; ultimo: string }[];
  alerta: { campana: string; reportes_hoy: number; ultima_hora: number } | null;
  actividad: { id: string; nivel: "low" | "medium" | "high" | "inconclusive"; puntaje: number; tipo: string; canal: string; modalidad: string | null; cuando: string }[];
  llamadas_ultimas: { entidad: string; real: boolean; cuando: string }[];
};

export type Health = { status: string; version: string; base_de_datos: string; ia: string };

export function health(): Promise<Health> {
  return fetch(API_URL.replace(/\/api\/v1\/?$/, "") + "/health", { cache: "no-store" }).then((r) => r.json());
}

export type BancoView = {
  total: number;
  alto_riesgo: number;
  reportes_semana: number;
  personas_semana: number;
  oficiales: number;
  mas_reportados: { valor: string; tipo: string; personas: number; nivel: number; palabra: string; modalidad: string | null; ultimo: string }[];
  solicitudes: { id: string; valor: string; motivo: string; creado: string }[];
  lista_blanca: { entidad: string; valor: string; canal: string; fuente: string; verificado_por: string }[];
  reportes_por_dia: { dia: string; total: number }[];
};

export type Llamada = { id: string; cliente: string; motivo: string; asesor: string; estado: string; creado: string; vence: string };
