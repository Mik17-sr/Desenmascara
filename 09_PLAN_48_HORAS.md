# Plan de Ejecución de 48 Horas — Colombia 5.0 Hackathon

**Inicio:** Viernes 16 de octubre de 2026 · 18:00 COT  
**Entrega:** Domingo 18 de octubre de 2026 · 15:00 COT (con 3 horas de margen antes del cierre)  
**Demo Day:** 19 y 20 de octubre de 2026

---

## Cronograma Maestro Bloque por Bloque

```
[VIE NOCHE] Kickoff ──► Esqueleto API ──► Tablas Supabase ──► Menú WhatsApp ──► Prompt Psicólogo
                              │
[SÁB MAÑANA] ──────────► LLAMADA VERIFICADA FUNCIONAL (Hito de Oro a Mediodía)
                              │
[SÁB TARDE]  ──────────► Círculo de Confianza ──► Banco de Números ──► Whisper ──► Dashboard en Vivo
                              │
[SÁB NOCHE]  ──────────► Antes de Pagar ──► Rayos X ──► pgvector Campañas ──► 13 Defensas
                              │
[DOM MAÑANA] ──────────► Pruebas Dataset (140 casos) ──► Red Team ──► Ensayo Demo 4 en Escena
                              │
[DOM TARDE]  ──────────► Congelamiento de Código ──► Video Backup ──► Entrega Final (15:00 COT)
```

---

## Asignación de Tareas por Integrante y Franja Horaria

### Bloque 1: Viernes 16 · Kickoff y Esqueleto Base (18:00 – 24:00)
- **Los 4 Integrantes:** Lectura del reto oficial de Colombia 5.0, ajuste de alcance en las primeras 2 horas y distribución final de accesos.
- **Miguel (Backend):** Inicializar repo en GitHub, configurar FastAPI, conectar Webhook de Twilio WhatsApp Sandbox y ejecutar migración inicial en Supabase (12 tablas). *Meta: bot responde "Hola" con el menú.*
- **Luis (IA):** Configurar cliente de LLM, diseñar el prompt de sistema del Psicólogo con tipado Pydantic y validar que un SMS sospechoso devuelva JSON estructurado.
- **Gerhard (Bot & Dashboard):** Redactar los textos de las 6 opciones del menú conversacional de WhatsApp; inicializar proyecto Next.js en Vercel con Tailwind y shadcn/ui.
- **IngBocadillo (Calidad):** Consolidar los 4 casos reales del equipo y estructurar la hoja del dataset con los primeros 50 casos etiquetados.

---

### Bloque 2: Sábado 17 · Mañana — Hito de Oro: Llamada Verificada (08:00 – 13:00)
- **Miguel:** Desarrollar endpoints `/api/v1/llamadas/registrar` y `/api/v1/llamadas/consultar` con generación de código aleatorio de 4 dígitos y caducidad a 15 min.
- **Gerhard:** Construir la Vista 4 del Dashboard (Panel de la Entidad para BancoAndino) e integrar el flujo de consulta en el bot de WhatsApp.
- **Luis:** Construir Revisión 2 (Extractor de Pistas regex) y Revisión 3 (Lista blanca de dominios bancarios, consulta Safe Browsing y cálculo de antigüedad RDAP).
- **IngBocadillo:** Probar con celulares reales el flujo de Llamada Verificada (caso llamada falsa y caso llamada legítima) registrando tiempos de respuesta.
- **HITO CRÍTICO (13:00 COT):** *Flujo de Llamada Verificada funcionando de punta a punta entre el Panel de BancoAndino y WhatsApp.*

---

### Bloque 3: Sábado 17 · Tarde — Círculo de Confianza y Banco de Números (14:00 – 19:00)
- **Miguel:** Endpoints del Círculo de Confianza (invitación, confirmación y difusión de alerta en cadena) y APIs del Banco de Números con hashing HMAC.
- **Luis:** Integración de Whisper para transcripción de notas de voz en llamadas (vishing) y detección de patrones de "falso familiar".
- **Gerhard:** Construir Vista 1 del Dashboard (Radar en vivo con Supabase Realtime) y programar flujos conversacionales de "Antes de Pagar".
- **IngBocadillo:** Grabar las notas de voz de prueba para la demo y completar los 140 casos del dataset.

---

### Bloque 4: Sábado 17 · Noche — Memoria, Juez y Rayos X (20:00 – 01:00)
- **Luis:** Implementar Revisión 5 (Embeddings en `pgvector` para campañas masivas) y afinar el algoritmo del Juez con la tabla de pesos y reglas duras.
- **Gerhard:** Construir Vista 2 del Dashboard (Verificar un Mensaje con visualización interactiva de Rayos X) y Vista 3 (Banco de Números).
- **Miguel:** Implementar validación de firmas de Twilio, rate limiting y reglas RLS en Supabase.
- **IngBocadillo:** Ejecutar pruebas de regresión automáticas con `pytest` y redactar borrador del README.md.

---

### Bloque 5: Domingo 18 · Mañana — QA, Red Teaming y Demo (08:00 – 13:00)
- **IngBocadillo & Luis:** Evaluar el dataset completo de 140 casos; calcular matriz de confusión, precisión y sensibilidad final para las diapositivas del pitch.
- **Miguel:** Configurar bot espejo de Telegram (Plan B) y realizar escaneo de seguridad con `gitleaks` y `pip-audit`.
- **Gerhard:** Activar modo presentación en pantalla completa en el Dashboard y generar código QR para el jurado.
- **Los 4 Integrantes:** Ensayos cronometrados del guion de 5 minutos de la demo en vivo (las 3 escenas con 4 celulares simultáneos). Grabación del video de contingencia de 3 minutos.

---

### Bloque 6: Domingo 18 · Tarde — Entrega Final (13:00 – 15:00)
- Congelamiento definitivo de código (*Code Freeze*).
- Despliegue de producción verificado en Render y Vercel.
- Carga del proyecto en la plataforma oficial del evento con 3 horas de margen de seguridad antes del cierre de las 18:00 COT.
