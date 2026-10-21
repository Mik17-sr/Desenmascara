# Desenmascara

Un verificador de estafas por Telegram: la persona reenvía el mensaje, la captura, el número que la llamó o una nota de voz, y en segundos recibe un semáforo, el porqué y qué hacer. Cuando puede, no adivina: **confirma con la fuente** (Llamada Verificada y Círculo de Confianza).

Esta versión implementa la guía del proyecto (`docs/`, v7.0) con tres cambios:

| La guía dice | Aquí | Por qué |
|---|---|---|
| WhatsApp con Twilio | **Telegram** | Ya existía el bot; no hace falta sandbox ni cuenta de Twilio. Como un bot de Telegram no puede escribir primero, el Círculo usa enlaces de invitación. |
| Supabase (PostgreSQL + pgvector) | **SQLite local o Supabase**, con las mismas 12 tablas | En local funciona sin cuentas. Con Supabase hay RLS y Realtime (ver «Pasar a Supabase»). Las huellas de campañas son MinHash en JSON en lugar de pgvector. |
| LLM por API (Claude, GPT o Gemini) | **llama3.2 local con Ollama** | Sin claves ni costo. En CPU tarda 5-7 s por análisis, así que la IA solo clasifica y el juez arma la explicación. |

## Qué hay

- **Bot de Telegram** (`app/bot/`): menú de 6 opciones, detección automática (mensaje, captura, número, nota de voz, «¿X me está llamando?», «ya caí»), consentimiento (Ley 1581), Llamada Verificada, Círculo de Confianza, Antes de pagar, kit de denuncia, reportes y revisión por el dueño.
- **El cerebro** (`app/engine/`), con las seis revisiones de la sección 11:

  | Revisión | Archivo | Cómo |
  |---|---|---|
  | 1 · Traductor | `traductor.py` | OCR (RapidOCR) y notas de voz (faster-whisper), en memoria |
  | 2 · Pistas | `pistas.py` | Reglas: enlaces, teléfonos, llaves Bre-B, cuentas, montos, códigos |
  | 3 · Enlaces | `enlaces.py` | Sitio oficial, imitaciones (homoglifos, punycode, casi iguales), edad con RDAP, Safe Browsing opcional |
  | 4 · Psicólogo | `analyzer.py` | IA: modalidad, qué pide, si presiona. Respuesta con esquema JSON fijo |
  | 5 · Archivista | `archivista.py` | Huellas MinHash para reconocer campañas aunque cambien palabras |
  | 6 · Juez | `juez.py` | Puntos y reglas de la sección 12; cada punto tiene una razón (Rayos X) |
- **API** (`app/api/`): análisis público con límite por IP, endpoints del bot (`BOT_API_SECRET`), de las entidades (llave de acceso), del equipo (`ADMIN_API_KEY`) y vistas anónimas para el Dashboard.
- **Dashboard** (`dashboard/`, Next.js): Radar en vivo con actividad y avisos, Verificar un mensaje con Rayos X, Banco de números y Panel de la entidad. Con Supabase se actualiza por Realtime; sin Supabase consulta cada 3 s.

## Cómo arrancarlo (Windows, PowerShell)

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

## Pasar a Supabase (RLS y Realtime)

1. Crea un proyecto en [supabase.com](https://supabase.com).
2. En **SQL Editor**, pega y ejecuta `supabase/migrations/20261021120000_esquema_inicial.sql` (o `supabase db push` con la CLI). Crea las 12 tablas con RLS, las 5 vistas anónimas y la tabla `eventos_dashboard`, que ya queda publicada en Realtime.
3. En **Project Settings → Database → Connection string**, copia la de **Session pooler** (funciona con IPv4) y ponla en `.env`:
   `DATABASE_URL=postgresql://postgres.<proyecto>:<contraseña>@aws-0-<región>.pooler.supabase.com:5432/postgres`
4. Copia tus datos locales (opcional): `python scripts/migrar_a_supabase.py`. Usa los mismos `HMAC_SECRET` y `ENCRYPTION_KEY`.
5. En el Dashboard, copia `dashboard/.env.local.example` a `dashboard/.env.local` con la **Project URL** y la llave pública **anon** (Project Settings → API), y vuelve a ejecutar `npm run build` y `npm run start`. La barra lateral mostrará «Tiempo real · Realtime».

Cómo queda protegido: la API se conecta como `postgres` (dueño de las tablas); `anon` y `authenticated` no pueden leer ninguna tabla con datos, solo las vistas agregadas y `eventos_dashboard`, que guarda qué tabla cambió y el nivel de riesgo, sin texto, números ni usuarios. Nunca pongas la llave `service_role` en el Dashboard.

Para probar la migración sin Supabase: `TEST_DATABASE_URL=postgresql://... python -m pytest` corre las 67 pruebas sobre un PostgreSQL vacío con la migración aplicada.

## Pruebas y medición

```powershell
python -m pytest                     # 67 pruebas: motor, API de punta a punta y bot (sin red ni IA real)
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

## Seguridad (las 13 defensas de la sección 18)

| Defensa | Estado |
|---|---|
| Autenticidad del canal | El bot llama a la API con `BOT_API_SECRET`; usa polling, así que no hay webhook que firmar. |
| Inyección de instrucciones | Mensaje aislado entre comillas, esquema JSON fijo, regla que detecta órdenes (+20 y mínimo alto riesgo) y el juez decide. |
| Enlaces y SSRF | Los enlaces nunca se abren: solo se compara el nombre y se consulta RDAP en un host fijo, con tiempo límite. |
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

## Qué funciona y qué falta

Funciona: el bot con mensajes, capturas, números y notas de voz; Llamada Verificada con BancoAndino (ficticio); Círculo de Confianza con invitaciones; Banco de números con lista blanca y revisiones; Antes de pagar; el Dashboard con sus 4 vistas.

Falta o es visión: WhatsApp (Twilio); los 4 casos reales del equipo y el dataset real; despliegue (Render/Railway y Vercel) con TLS; escaneos de seguridad en CI; entidades reales conectadas.
