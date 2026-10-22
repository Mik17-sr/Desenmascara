# Desenmascara · Guía Técnica del Proyecto

**Evento:** Colombia 5.0 Hackathon (16 al 18 de octubre de 2026)  
**Versión:** 7.0 · Edición Telegram Nativo  
**Canal Ciudadano:** Telegram Bot API (`@DesenmascaraBot`)  
**Equipo:** Luis Guillermo Nieto Patiño · Miguel · Gerhard Arce · IngBocadillo  
**Lema:** *Reenvía el mensaje. Desenmascara la estafa. Las demás herramientas adivinan; Desenmascara confirma con la fuente.*

---

## Así funciona

Un verificador de estafas por Telegram: la persona reenvía el mensaje, la captura, el número que la llamó o una nota de voz, y en segundos recibe un semáforo, el porqué y qué hacer. Cuando puede, no adivina: **confirma con la fuente** (Llamada Verificada y Círculo de Confianza).

![Animación del flujo: lo que te llegó pasa por el bot de Telegram y la API, luego por las seis revisiones del Cerebro, y vuelve como un semáforo con sus razones](docs/img/flujo-mensaje.svg)

| Paso | Qué pasa |
| :--- | :--- |
| 1 · Lo que te llegó | Reenvías el mensaje, una captura, una nota de voz o el número que te llamó. |
| 2 · Bot de Telegram | Reconoce qué le enviaste. La primera vez pide tu consentimiento (Ley 1581). |
| 3 · API FastAPI | Comprueba el secreto del bot, limita las consultas y quita nombres y números antes de guardar. |
| 4 · El Cerebro | Seis revisiones en orden: Traductor (capturas y voz), Pistas, Enlaces, Psicólogo (IA local), Archivista (campañas de hoy) y Juez. |
| 5 · Semáforo y Rayos X | El juez suma los puntos: 0–39 bajo riesgo, 40–69 sospechoso, 70 o más alto riesgo. Cada punto trae su razón. |
| 6 · Respuesta | Vuelve por Telegram con el semáforo, el porqué y qué hacer (la meta es menos de 8 s). El Radar del Dashboard recibe solo un aviso anónimo con el nivel de riesgo. |

El ejemplo es una respuesta real de la API local: **80/100, alto riesgo**. En esa corrida la IA no respondió a tiempo, así que los puntos vienen de las demás revisiones; el sistema responde igual.

### Confirmar con la fuente

Cuando la estafa se hace pasar por alguien real, Desenmascara no adivina: le pregunta a ese alguien.

![Animación de Llamada Verificada: el banco registra la llamada y recibe un código; cuando el asesor te llama, el bot te confirma que es real y te da el código para comprobarlo](docs/img/flujo-llamada-verificada.svg)

![Animación del Círculo de Confianza: el bot marca sospechoso el mensaje del falso familiar, le pregunta a tu familiar si fue él y, si dice que no, te avisa que es una estafa](docs/img/flujo-circulo.svg)

Las animaciones se generan con `scripts/diagramas.py` (SVG con animación CSS, sin JavaScript). Con «reducir movimiento» activado en el sistema se ven quietas y completas.

---

## 1. El Problema que Resolvemos
En Colombia se reclaman más de **$252 millones de pesos al día** por fraudes cometidos mediante SMS y llamadas telefónicas (CRC, 2026). Las reclamaciones por vishing y smishing crecieron 3 veces en solo dos años (de $30.622 millones a $92.235 millones de pesos). 

Hoy, los ciberdelincuentes utilizan Inteligencia Artificial para clonar voces familiares y generar mensajes idénticos a los de entidades bancarias. Las herramientas tradicionales fallan porque intentan adivinar mediante probabilidades. Desenmascara cambia el paradigma: **confirma directamente con la fuente legítima**.

---

## 2. Los Tres Pilares de Protección
Desenmascara protege al ciudadano a través de tres capas coordinadas:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. CONFIRMAR CON LA FUENTE (Certeza Absoluta)                               │
│    • Llamada Verificada: La entidad bancaria confirma si te está llamando.  │
│    • Círculo de Confianza: Tu familiar confirma en su Telegram si es él.   │
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

## 3. ¿Por qué Telegram Bot API?
Para el hackathon, Telegram representa una ventaja estratégica decisiva:
- **Cero Fricción para el Jurado:** No requiere unirse a sandboxes con códigos manuales ni esperar aprobaciones. Cualquier jurado abre la cámara de su celular, escanea el código QR y prueba `@DesenmascaraBot` al instante.
- **Soporte Multimodal Nativo:** Recepción directa de capturas de pantalla, notas de voz OGG/Opus y compartición criptográfica de contacto telefónico (`request_contact=True`).
- **Botones Interactivos:** Teclados nativos que guían paso a paso al usuario sin riesgo de errores de digitación.

---

## 4. Arquitectura del Sistema

```
                      [CANALES DE ENTRADA]
  Telegram Bot (@DesenmascaraBot) ─── Capturas / Audios ─── Dashboard Web
                                │
                                ▼
                   [SERVIDOR FASTAPI (Python 3.12)]
      Secret Token · Rate Limiting · Anonimización · APIs de Fuentes
                                │
                                ▼
                   [EL CEREBRO · 6 REVISIONES]
  ┌──────────────────────────────────────────────────────────────────────────┐
  │ 1. Traductor: OCR Visión (capturas) + Whisper (audios OGG de Telegram)  │
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

## 5. Las 6 Piezas del Prototipo
1. **Bot de Telegram (`@DesenmascaraBot`):** La interfaz ciudadana. Menú de 6 botones interactivos y enrutamiento inteligente sin menú.
2. **El Cerebro:** Motor analítico de 6 detectives con diagnóstico explicable en menos de 8 segundos.
3. **Módulo de Llamadas (Vishing):** Consulta de números reportados y análisis de notas de voz transcribiendo el audio con Whisper.
4. **Dashboard en Tiempo Real:** Aplicación web en Next.js con 4 vistas: Radar de campañas, Verificador con Rayos X, Banco de números y Panel de la entidad.
5. **Verificación con la Fuente:** Módulo de Llamada Verificada (código de 4 dígitos, TTL 15 min) y Círculo de Confianza en Telegram (confirmación cruzada y alertas en cadena).
6. **Banco de Números y Compras:** Registro comunitario con scoring 0–100 para teléfonos y llaves Bre-B, más el flujo "Antes de Pagar".

---

## 6. Modelo de Datos (12 Tablas en Supabase)
- **Personas y Círculo:** `usuarios`, `circulos`, `miembros_circulo`, `avisos_circulo`.
- **Verificaciones y Campañas:** `verificaciones`, `campanas` (con índices vectoriales HNSW).
- **Banco de Números:** `indicadores`, `reportes`, `solicitudes_revision`, `numeros_oficiales`.
- **Entidades y Llamadas:** `entidades`, `llamadas_registradas`.
- **Vistas Públicas:** `vista_radar_por_hora`, `vista_tipos_de_estafa`, `vista_campanas_activas`, `vista_llamadas_verificadas`, `vista_banco_mas_reportados`.

---

## 7. Las 13 Defensas de Ciberseguridad
Construido bajo estándares internacionales **OWASP Top 10 for LLM** y **OWASP API Security**:
1. Validación de cabecera `X-Telegram-Bot-Api-Secret-Token`.
2. Aislamiento de prompts contra inyección de instrucciones (OWASP LLM01) con penalización de +20 pts.
3. Protección contra SSRF y resolución segura de URLs sin navegación arbitraria.
4. Rate limiting por Telegram ID e IP.
5. Gestión segura de secretos (zero-secrets en Git con `gitleaks`).
6. Control de acceso granular con Row Level Security (RLS) en Supabase.
7. Cifrado TLS 1.3 en tránsito y AES-256 en reposo.
8. Anonimización estricta bajo Ley 1581 de 2012 y eliminación inmediata de notas de voz tras Whisper.
9. Resistencia contra envenenamiento de reportes en el Banco de Números.
10. Doble consentimiento explícito y revocable para Círculos de Confianza.
11. Protección de privacidad en Llamada Verificada mediante números efímeros.
12. Validación segura de archivos multimedia en memoria.
13. Escaneos continuos de vulnerabilidades en dependencias (`pip-audit`, CodeQL).

---

## 8. Estructura del Kit de Agentes

| Archivo | Contenido y Propósito |
| :--- | :--- |
| `00_COORDINADOR.md` | Guía de integración, roles del equipo, 10 etapas y estrategia con Telegram. |
| `01_CONTRATO_COMPARTIDO.md` | Esquemas canónicos de datos Pydantic, JSON y contratos de APIs. |
| `02_AGENTE_BACKEND.md` | Servidor FastAPI, webhook seguro de Telegram y orquestación. |
| `03_AGENTE_DETECCION_IA.md` | El Cerebro de 6 detectives, prompts, pgvector y scoring determinista. |
| `04_AGENTE_TELEGRAM.md` | Interfaz conversacional nativa en Telegram (`@DesenmascaraBot`). |
| `05_AGENTE_DATOS.md` | DDL de Supabase, 12 tablas, 5 vistas, pgvector y políticas RLS. |
| `06_AGENTE_SEGURIDAD.md` | Implementación y auditoría de las 13 defensas de ciberseguridad. |
| `07_AGENTE_QA.md` | Dataset de 140 casos, tests automatizados y guion del Demo Day. |
| `08_VALIDACION_FINAL.md` | Checklist exhaustivo de certificación previa a la entrega. |
| `09_PLAN_48_HORAS.md` | Cronograma bloque a bloque de 48 horas y roles de los 4 integrantes. |
| `README.md` | Visión general técnica del proyecto. |

---

## 9. Guía de Puesta en Marcha Rápida (Desarrollo Local)

> **En esta versión** el código está en la raíz del repositorio (no hay carpetas `backend/` ni `frontend/`), el Dashboard está en `dashboard/` y la IA corre local con Ollama, sin `OPENAI_API_KEY`. Los pasos al día están en la sección 13.

### 1. Configurar el Bot en Telegram
1. Abre Telegram y escribe a `@BotFather`.
2. Envía `/newbot`, asigna nombre y usuario (ej. `DesenmascaraDemoBot`).
3. Copia el token de acceso (`TELEGRAM_BOT_TOKEN`).

### 2. Instalación del Backend
```bash
git clone https://github.com/tu-organizacion/desenmascara.git
cd desenmascara/backend

python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Configurar SUPABASE_URL, SUPABASE_KEY, TELEGRAM_BOT_TOKEN, TELEGRAM_SECRET_TOKEN, OPENAI_API_KEY

uvicorn app.main:app --reload --port 8000
```

### 3. Instalación del Dashboard (Frontend)
```bash
cd ../frontend
npm install
cp .env.example .env.local
# Configurar NEXT_PUBLIC_SUPABASE_URL y NEXT_PUBLIC_SUPABASE_ANON_KEY

npm run dev
```

---

## 10. Equipo de Trabajo (Colombia 5.0)
- **Luis Guillermo Nieto Patiño:** IA, Datos, Cerebro de 6 revisiones y Detección de Falso Familiar.
- **Miguel Sierra:** Backend, Arquitectura de Integración, APIs de Llamada Verificada y Supabase.
- **Gerhard Arce:** Módulo de Llamadas, Banco de Números, Bot de Telegram y Dashboard.
- **Tomas Lancheros:** Dirección de Producto, Dataset, Ciberseguridad, QA y Pitch.

---

## 11. Lo que cambia en esta versión

Esta versión implementa la guía del proyecto (`docs/`, v7.0) con tres cambios:

| La guía dice | Aquí | Por qué |
|---|---|---|
| WhatsApp con Twilio | **Telegram** | Ya existía el bot; no hace falta sandbox ni cuenta de Twilio. Como un bot de Telegram no puede escribir primero, el Círculo usa enlaces de invitación. |
| Supabase (PostgreSQL + pgvector) | **SQLite local o Supabase**, con las mismas 12 tablas | En local funciona sin cuentas. Con Supabase hay RLS y Realtime (ver sección 14). Las huellas de campañas son MinHash en JSON en lugar de pgvector. |
| LLM por API (Claude, GPT o Gemini) | **llama3.2 local con Ollama** | Sin claves ni costo. En CPU tarda 5-7 s por análisis, así que la IA solo clasifica y el juez arma la explicación. |

---

## 12. Qué hay en el código

- **Bot de Telegram** (`app/bot/`): menú de 6 opciones, detección automática (mensaje, captura, número, nota de voz, «¿X me está llamando?», «ya caí»), consentimiento (Ley 1581), Llamada Verificada, Círculo de Confianza, Antes de pagar, kit de denuncia, reportes y revisión por el dueño.
- **El cerebro** (`app/engine/`), con las seis revisiones de la sección 11:

  | Revisión | Archivo | Cómo |
  |---|---|---|
  | 1 · Traductor | `traductor.py` | OCR (RapidOCR) y notas de voz (faster-whisper), en memoria |
  | 2 · Pistas | `pistas.py` | Reglas: enlaces, teléfonos, llaves Bre-B, cuentas, montos, códigos |
  | 3 · Enlaces | `enlaces.py` | Sitio oficial, imitaciones (homoglifos, punycode, casi iguales), edad con RDAP; Safe Browsing y URLhaus si hay llave |
  | 4 · Psicólogo | `analyzer.py` | IA: modalidad, qué pide, si presiona. Respuesta con esquema JSON fijo |
  | 5 · Archivista | `archivista.py` | Huellas MinHash para reconocer campañas aunque cambien palabras |
  | 6 · Juez | `juez.py` | Puntos y reglas de la sección 12; cada punto tiene una razón (Rayos X) |
- **API** (`app/api/`): análisis público con límite por IP, endpoints del bot (`BOT_API_SECRET`), de las entidades (llave de acceso), del equipo (`ADMIN_API_KEY`) y vistas anónimas para el Dashboard.
- **Dashboard** (`dashboard/`, Next.js): Radar en vivo con actividad y avisos, Verificar un mensaje con Rayos X, Banco de números y Panel de la entidad. Con Supabase se actualiza por Realtime; sin Supabase consulta cada 3 s.

---

## 13. Cómo arrancarlo (Windows, PowerShell)

Requisitos: Python 3.12, Node.js 20+, [Ollama](https://ollama.com) con `ollama pull llama3.2`.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python scripts/setup_local.py        # crea .env con secretos generados
python scripts/seed_demo.py          # BancoAndino, Tienda Ejemplo y números reportados (ficticios); muestra la llave de BancoAndino

uvicorn app.main:app --port 8000     # espera "Application startup complete" (~20 s: carga los modelos)
```

En otra terminal, el bot (pon antes tu token de @BotFather en `TELEGRAM_BOT_TOKEN` dentro de `.env`):

```powershell
.venv\Scripts\Activate.ps1
python -m app.bot.client
```

Al arrancar, el bot se pone el perfil del manual: nombre «Desenmascara», descripción «bot antiestafas», menú de comandos y el logo (`app/bot/assets/avatar.png`) si todavía no tiene foto. Solo envía a Telegram lo que cambió.

Y el Dashboard:

```powershell
cd dashboard
npm install
npm run build
npm run start                        # http://localhost:3000
```

- La llave de la entidad para el Panel la muestra `seed_demo.py` (o `--nueva-llave` para generar otra).
- La llave del equipo (revisiones y lista blanca) es `ADMIN_API_KEY` de `.env`.
- Documentación de la API: http://127.0.0.1:8000/docs

### Entrega con datos reales

Para mostrarlo a una empresa sin nada ficticio:

```powershell
python scripts/limpiar_datos.py --todo   # quita BancoAndino, Tienda Ejemplo, los usuarios «Demo» y la actividad de prueba
python scripts/crear_entidad.py "Nombre de la entidad" --dominio entidad.com --linea "+57 601 000 0000"   # la conecta a Llamada Verificada
```

- `datasets/dominios_oficiales.csv`: páginas oficiales de 27 entidades reales (bancos, DIAN, Policía, mensajerías). Con ellas, un enlace a `bancolombia.com` es oficial y `bancolombia-seguro.co` es una imitación.
- `datasets/lineas_oficiales.csv`: 22 líneas de atención que cada entidad publica en su propia página, con la página de origen. El bot las da como «llama tú a este número», nunca como prueba de que una llamada es real: el número en pantalla se puede falsificar.
- Revisen y amplíen las dos listas con fuentes oficiales antes de producción. Nunca agreguen números de estafadores a mano: el Banco de números se llena con los reportes de las personas, y un número inventado puede ser el de alguien real.

---

## 14. Pasar a Supabase (RLS y Realtime)

1. Crea un proyecto en [supabase.com](https://supabase.com).
2. En **SQL Editor**, pega y ejecuta `supabase/migrations/20261021120000_esquema_inicial.sql` (o `supabase db push` con la CLI). Crea las 12 tablas con RLS, las 5 vistas anónimas y la tabla `eventos_dashboard`, que ya queda publicada en Realtime.
3. En **Project Settings → Database → Connection string**, copia la de **Session pooler** (funciona con IPv4) y ponla en `.env`:
   `DATABASE_URL=postgresql://postgres.<proyecto>:<contraseña>@aws-0-<región>.pooler.supabase.com:5432/postgres`
4. Copia tus datos locales (opcional): `python scripts/migrar_a_supabase.py`. Usa los mismos `HMAC_SECRET` y `ENCRYPTION_KEY`.
5. En el Dashboard, copia `dashboard/.env.local.example` a `dashboard/.env.local` con la **Project URL** y la llave pública **anon** (Project Settings → API), y vuelve a ejecutar `npm run build` y `npm run start`. La barra lateral mostrará «Tiempo real · Realtime».

Cómo queda protegido: la API se conecta como `postgres` (dueño de las tablas); `anon` y `authenticated` no pueden leer ninguna tabla con datos, solo las vistas agregadas y `eventos_dashboard`, que guarda qué tabla cambió y el nivel de riesgo, sin texto, números ni usuarios. Nunca pongas la llave `service_role` en el Dashboard.

Para probar la migración sin Supabase: `TEST_DATABASE_URL=postgresql://... python -m pytest` corre las 70 pruebas sobre un PostgreSQL vacío con la migración aplicada.

---

## 15. Pruebas y medición

```powershell
python -m pytest                     # 70 pruebas: motor, API de punta a punta y bot (sin red ni IA real)
python scripts/evaluar.py            # mide sensibilidad, falsos positivos y P90 contra la API en marcha
```

`datasets/casos_prueba.csv` trae 26 casos **sintéticos** para empezar. La guía pide 100 mensajes reales (50 estafas y 50 legítimos), 20 llamadas y 20 compras con las mismas columnas.

Última medición en un portátil sin GPU (i5-1035G1), 30 mensajes por la misma llamada que hace el bot:

| | Resultado |
|---|---|
| Estafas marcadas como alto riesgo | 11 de 16 (3 más como sospechoso) |
| Mensajes legítimos en bajo riesgo | 11 de 12, sin falsos positivos |
| Tiempo | mediana 6,4 s; 27 de 30 dentro de los 8 s |

Con otras aplicaciones abiertas la CPU se satura y algunas respuestas pasan de 8 s. Para tener margen hace falta GPU o un LLM en la nube; el modelo se cambia con `OLLAMA_MODEL`.

Comparación de modelos con los 26 casos del CSV (misma máquina con la CPU libre, mismo juez y sin memoria de campañas):

| | `llama3.2` (3B) | `llama3.2:1b` |
|---|---|---|
| La IA responde a tiempo (< 7 s) | 26 de 26 | 26 de 26 |
| Tiempo de la IA | mediana 4,7 s · P90 5,2 s | mediana 3,0 s · P90 3,3 s |
| Modalidad correcta | 19 de 26 | 15 de 26 |
| Estafas detectadas | 13 de 14 | 5 de 14 |
| Falsos positivos | 0 de 12 | 0 de 12 |

El modelo de 1B es más rápido, pero deja pasar 9 de las 14 estafas: nos quedamos con `llama3.2`.

---

## 16. Estado de las 13 defensas (sección 18 de la guía)

| Defensa | Estado |
|---|---|
| Autenticidad del canal | El bot llama a la API con `BOT_API_SECRET`; usa polling, así que no hay webhook que firmar. |
| Inyección de instrucciones | Mensaje aislado entre comillas, esquema JSON fijo, regla que detecta órdenes (+20 y mínimo alto riesgo) y el juez decide. |
| Enlaces y SSRF | Los enlaces nunca se abren: solo se compara el nombre y se consulta RDAP en un host fijo, con tiempo límite. Con llave (`GOOGLE_SAFE_BROWSING_KEY`, `URLHAUS_AUTH_KEY`), el texto del enlace se busca en Safe Browsing y URLhaus, también en hosts fijos. |
| Rate limiting | 20 consultas por minuto por IP en lo público y 12 por persona en el bot. |
| Secretos | En `.env` (ignorado por git), generados por `setup_local.py`. Falta gitleaks en CI. |
| Acceso a datos | RLS en las 13 tablas de Supabase y permisos revocados a `anon`/`authenticated`; el Dashboard solo lee agregados anónimos; entidades con llave (guardada como hash). |
| Cifrado | Teléfonos, llaves e ids de Telegram como HMAC-SHA256; códigos y chats cifrados (Fernet). Falta TLS al desplegar. |
| Datos personales | Se borran nombres, números y cuentas antes de guardar; audios en memoria; `/borrar` elimina a la persona. |
| Envenenamiento | Un voto por persona y valor, reportes viejos a la mitad, revisión por el dueño. |
| Círculo | Doble consentimiento y salida con un mensaje. |
| Llamada Verificada | Solo responde a la persona llamada (su propio contacto de Telegram); código de un uso que se borra a los 15 minutos. |
| Archivos | Tipo real por sus bytes, límites de tamaño y proceso en memoria. |
| Dependencias | Pendiente: pip-audit, npm audit y Dependabot en CI. |

---

## 17. Qué funciona y qué falta

Funciona: el bot con mensajes, capturas, números y notas de voz; Llamada Verificada con BancoAndino (ficticio); Círculo de Confianza con invitaciones; Banco de números con lista blanca y revisiones; Antes de pagar; el Dashboard con sus 4 vistas.

Falta o es visión: WhatsApp (Twilio); los 4 casos reales del equipo y el dataset real; despliegue (Render/Railway y Vercel) con TLS; escaneos de seguridad en CI; entidades reales conectadas.
