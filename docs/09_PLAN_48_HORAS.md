# Plan de Ejecución de 48 Horas — Colombia 5.0 Hackathon

**Inicio:** Viernes 16 de octubre de 2026 · 18:00 COT  
**Entrega:** Domingo 18 de octubre de 2026 · 15:00 COT (con 3 horas de margen antes del cierre)  
**Demo Day:** 19 y 20 de octubre de 2026

---

## Cronograma Maestro Bloque por Bloque

```
[VIE NOCHE] Kickoff ──► Bot Telegram (BotFather) ──► Tablas Supabase ──► Menú Bot ──► Prompt Psicólogo
                              │
[SÁB MAÑANA] ──────────► LLAMADA VERIFICADA FUNCIONAL (Hito de Oro a Mediodía)
                              │
[SÁB TARDE]  ──────────► Círculo de Confianza ──► Banco de Números ──► Whisper ──► Dashboard en Vivo
                              │
[SÁB NOCHE]  ──────────► Antes de Pagar ──► Rayos X ──► pgvector Campañas ──► 13 Defensas
                              │
[DOM MAÑANA] ──────────► Pruebas Dataset (140 casos) ──► Red Team ──► Ensayo Demo con QR Telegram
                              │
[DOM TARDE]  ──────────► Congelamiento de Código ──► Video Backup ──► Entrega Final (15:00 COT)
```

---

## Asignación de Tareas por Integrante

### Bloque 1: Viernes 16 · Kickoff y Esqueleto Base (18:00 – 24:00)
- **Miguel (Backend):** Crear bot en Telegram con BotFather (`@DesenmascaraBot`), configurar Webhook de Telegram con Secret Token en FastAPI y migrar las 12 tablas a Supabase. *Meta: el bot responde /start con el teclado de 6 botones.*
- **Luis (IA):** Diseñar prompt de sistema del Psicólogo con Pydantic y probar extracción de texto y detección de tácticas.
- **Gerhard (Bot & Dashboard):** Configurar botones y textos conversacionales en Telegram; inicializar Dashboard Next.js en Vercel.
- **IngBocadillo (Calidad):** Consolidar los 4 casos reales y cargar los primeros 50 casos del dataset.

### Bloque 2: Sábado 17 · Mañana — Hito de Oro: Llamada Verificada (08:00 – 13:00)
- **Miguel:** Endpoints `/api/v1/llamadas/registrar` y `/api/v1/llamadas/consultar` con código de 4 dígitos y TTL 15 min.
- **Gerhard:** Vista 4 del Dashboard (Panel de BancoAndino) e integración de la consulta en Telegram.
- **Luis:** Extractor regex de pistas y reputación de dominios (Safe Browsing / RDAP).
- **IngBocadillo:** Probar en vivo el flujo de Llamada Verificada en Telegram.
- **HITO CRÍTICO (13:00 COT):** *Llamada Verificada funcionando de punta a punta entre el Panel de BancoAndino y Telegram.*

### Bloque 3: Sábado 17 · Tarde — Círculo de Confianza y Banco de Números (14:00 – 19:00)
- **Miguel:** Endpoints de Círculo de Confianza y Banco de Números con hashing HMAC.
- **Luis:** Transcripción de audios OGG de Telegram con Whisper y detección de patrones de "falso familiar".
- **Gerhard:** Vista 1 del Dashboard (Radar en vivo) y flujos conversacionales de "Antes de Pagar".
- **IngBocadillo:** Grabar notas de voz de prueba y completar los 140 casos del dataset.

### Bloque 4: Sábado 17 · Noche — Memoria, Juez y Rayos X (20:00 – 01:00)
- **Luis:** Memoria semántica de campañas en `pgvector` y reglas duras del Juez.
- **Gerhard:** Vista 2 del Dashboard (Verificar con Rayos X) y Vista 3 (Banco de Números).
- **Miguel:** Validación de Secret Token, rate limiting y reglas RLS en Supabase.
- **IngBocadillo:** Pruebas automatizadas con `pytest` y redacción del README.md.

### Bloque 5: Domingo 18 · Mañana — QA, Red Teaming y Demo (08:00 – 13:00)
- **IngBocadillo & Luis:** Evaluar el dataset completo de 140 casos (sensibilidad y falsos positivos para las diapositivas).
- **Gerhard:** Generar código QR de acceso instantáneo a `@DesenmascaraBot` en el Dashboard.
- **Los 4 Integrantes:** Ensayos cronometrados del guion de 5 minutos de la demo en vivo con Telegram.

### Bloque 6: Domingo 18 · Tarde — Entrega Final (13:00 – 15:00)
- Congelamiento de código (*Code Freeze*), video de respaldo y entrega en la plataforma con 3 horas de margen.
