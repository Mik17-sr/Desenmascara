# Desenmascara · Guía Técnica del Proyecto

**Evento:** Colombia 5.0 Hackathon (16 al 18 de octubre de 2026)  
**Versión:** 7.0 · Oficial  
**Equipo:** Luis Guillermo Nieto Patiño · Miguel · Gerhard Arce · IngBocadillo  
**Lema:** *Reenvía el mensaje. Desenmascara la estafa. Las demás herramientas adivinan; Desenmascara confirma con la fuente.*

---

## 1. El Problema que Resolvemos
En Colombia se reclaman más de **$252 millones de pesos al día** por fraudes cometidos mediante SMS y llamadas telefónicas (CRC, 2026). Las reclamaciones por vishing y smishing crecieron 3 veces en solo dos años (de $30.622 millones a $92.235 millones de pesos). 

Hoy, los ciberdelincuentes utilizan Inteligencia Artificial para eliminar errores ortográficos, clonar voces de familiares y generar millones de mensajes fraudulentos. Las soluciones actuales (filtros de operadoras o antivirus) fallan porque **intentan adivinar mediante probabilidades**. Desenmascara cambia el paradigma: **confirma directamente con la fuente legítima**.

---

## 2. Los Tres Pilares de Protección
Desenmascara protege al ciudadano a través de tres capas coordinadas:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. CONFIRMAR CON LA FUENTE (Certeza Absoluta)                               │
│    • Llamada Verificada: La entidad bancaria confirma si te está llamando.  │
│    • Círculo de Confianza: Tu familiar confirma en su WhatsApp si es él.    │
├─────────────────────────────────────────────────────────────────────────────┤
│ 2. PREGUNTAR A LA COMUNIDAD (Evidencia Colectiva)                           │
│    • Banco de Números: Nivel de riesgo 0–100 de teléfonos y llaves Bre-B.  │
│    • Antes de Pagar: Verificador de compras y vendedores en redes sociales. │
├─────────────────────────────────────────────────────────────────────────────┤
│ 3. DETECTAR CON IA (Probabilidad Explicable en <8s)                         │
│    • El Cerebro: 6 detectives (Traductor, Pistas, Enlaces, Psicólogo,       │
│      Archivista pgvector y Juez determinista con Rayos X del puntaje).      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Arquitectura del Sistema

```
                      [CANALES DE ENTRADA]
  WhatsApp (Twilio) ─── SMS Reenviado ─── Notas de Voz ─── Dashboard Web
                                │
                                ▼
                   [SERVIDOR FASTAPI (Python 3.12)]
      Firma X-Twilio · Rate Limiting · Anonimización · APIs de Fuentes
                                │
                                ▼
                   [EL CEREBRO · 6 REVISIONES]
  ┌──────────────────────────────────────────────────────────────────────────┐
  │ 1. Traductor: OCR Visión (capturas) + Whisper (audios de llamadas)      │
  │ 2. Pistas: Regex de URLs, teléfonos colombianos, llaves Bre-B y marcas    │
  │ 3. Enlaces y Números: Safe Browsing, URLhaus, RDAP edad y Banco Números  │
  │ 4. Psicólogo (IA): LLM con JSON validado (tácticas, urgencia, entidad)   │
  │ 5. Archivista: Búsqueda vectorial HNSW en pgvector (campañas activas)   │
  │ 6. El Juez: Puntuación determinista 0-100, semáforo y Rayos X           │
  └──────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                     [SUPABASE (PostgreSQL 15)]
   12 Tablas · pgvector · Supabase Realtime · Row Level Security (RLS)
                                │
        ┌───────────────────────┴───────────────────────┐
        ▼                                               ▼
[RESPUESTA AL USUARIO]                       [DASHBOARD NEXT.JS]
Semáforo · Razones · Qué hacer               Radar · Rayos X · Banco · Entidad
```

---

## 4. Las 6 Piezas del Prototipo
1. **Bot de WhatsApp:** La interfaz central ciudadana. Sin apps que instalar; menú intuitivo de 6 opciones y enrutamiento inteligente sin menú.
2. **El Cerebro:** Motor analítico de 6 detectives que produce un diagnóstico explicable en menos de 8 segundos.
3. **Módulo de Llamadas (Vishing):** Consulta de números reportados y análisis de notas de voz transcribiendo el audio con Whisper.
4. **Dashboard en Tiempo Real:** Aplicación web en Next.js con 4 vistas: Radar de campañas, Verificador con Rayos X del puntaje, Banco de números y Panel de la entidad.
5. **Verificación con la Fuente:** Módulo de Llamada Verificada (código de 4 dígitos, TTL de 15 min) y Círculo de Confianza (doble consentimiento, preguntas cruzadas y alertas en cadena).
6. **Banco de Números y Compras:** Registro comunitario con scoring 0–100 para teléfonos y llaves de pago Bre-B, complementado por el flujo "Antes de Pagar".

---

## 5. Modelo de Datos (12 Tablas en Supabase)
- **Personas y Círculo:** `usuarios`, `circulos`, `miembros_circulo`, `avisos_circulo`.
- **Verificaciones y Campañas:** `verificaciones`, `campanas` (con índices vectoriales HNSW).
- **Banco de Números:** `indicadores`, `reportes`, `solicitudes_revision`, `numeros_oficiales`.
- **Entidades y Llamadas:** `entidades`, `llamadas_registradas`.
- **Vistas Públicas:** `vista_radar_por_hora`, `vista_tipos_de_estafa`, `vista_campanas_activas`, `vista_llamadas_verificadas`, `vista_banco_mas_reportados`.

---

## 6. Las 13 Defensas de Ciberseguridad
Construido bajo estándares internacionales **OWASP Top 10 for LLM** y **OWASP API Security**:
1. Validación de firma digital en Webhooks (`X-Twilio-Signature`).
2. Aislamiento estricto de prompts contra inyección de instrucciones (OWASP LLM01) con penalización de +20 pts.
3. Protección contra SSRF y resolución segura de URLs sin navegación real.
4. Rate limiting por teléfono e IP.
5. Gestión segura de secretos (zero-secrets en Git con `gitleaks`).
6. Control de acceso granular con Row Level Security (RLS) en Supabase.
7. Cifrado TLS 1.3 en tránsito y AES-256 en reposo.
8. Anonimización estricta bajo Ley 1581 de 2012 y eliminación inmediata de notas de voz.
9. Resistencia contra envenenamiento de reportes en el Banco de Números.
10. Doble consentimiento explícito y revocable para Círculos de Confianza.
11. Protección de privacidad en Llamada Verificada mediante números de teléfono como llave temporal.
12. Validación segura de tipos de archivo multimedia en memoria.
13. Escaneos continuos de vulnerabilidades en dependencias (`pip-audit`, CodeQL).

---

## 7. Estructura del Kit de Agentes en este Repositorio

| Archivo | Contenido y Propósito |
| :--- | :--- |
| `00_COORDINADOR.md` | Guía de integración, reparto de tareas, 10 etapas y control de alcance. |
| `01_CONTRATO_COMPARTIDO.md` | Esquemas canónicos de datos Pydantic, JSON y contratos de APIs. |
| `02_AGENTE_BACKEND.md` | Servidor FastAPI, endpoints, webhook de Twilio y orquestación. |
| `03_AGENTE_DETECCION_IA.md` | El Cerebro de 6 detectives, prompts, pgvector y scoring determinista. |
| `04_AGENTE_TELEGRAM.md` | Interfaz conversacional: Bot de WhatsApp (P0) y Telegram (Plan B). |
| `05_AGENTE_DATOS.md` | DDL de Supabase, 12 tablas, 5 vistas, pgvector y políticas RLS. |
| `06_AGENTE_SEGURIDAD.md` | Implementación y auditoría de las 13 defensas de ciberseguridad. |
| `07_AGENTE_QA.md` | Dataset de 140 casos, tests automatizados y guion del Demo Day. |
| `08_VALIDACION_FINAL.md` | Checklist exhaustivo de certificación previa a la entrega. |
| `09_PLAN_48_HORAS.md` | Cronograma bloque a bloque de 48 horas y roles de los 4 integrantes. |
| `README.md` | Este documento de visión general técnica del proyecto. |

---

## 8. Guía de Puesta en Marcha Rápida (Desarrollo Local)

### Requisitos Previos
- Python 3.12+
- Node.js 20 LTS
- Cuenta de Supabase (PostgreSQL con extensión `vector`)
- Cuenta de Twilio (Sandbox de WhatsApp activado)

### Instalación del Backend
```bash
git clone https://github.com/tu-organizacion/desenmascara.git
cd desenmascara/backend

python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Configurar SUPABASE_URL, SUPABASE_KEY, TWILIO_AUTH_TOKEN, OPENAI_API_KEY / ANTHROPIC_API_KEY

uvicorn app.main:app --reload --port 8000
```

### Instalación del Dashboard (Frontend)
```bash
cd ../frontend
npm install
cp .env.example .env.local
# Configurar NEXT_PUBLIC_SUPABASE_URL y NEXT_PUBLIC_SUPABASE_ANON_KEY

npm run dev
```

---

## 9. Equipo de Trabajo (Colombia 5.0)
- **Luis Guillermo Nieto Patiño:** IA, Datos, Cerebro de 6 revisiones y Detección de Falso Familiar.
- **Miguel:** Backend, Arquitectura de Integración, APIs de Llamada Verificada y Supabase.
- **Gerhard Arce:** Módulo de Llamadas, Banco de Números, Diseño Conversacional y Dashboard.
- **IngBocadillo:** Dirección de Producto, Dataset, Ciberseguridad, QA y Pitch.
