# Agente 0 — Coordinador Técnico e Integrador

**Proyecto:** Desenmascara · Versión 7.0 (Edición Telegram Nativo)  
**Evento:** Colombia 5.0 Hackathon (16 al 18 de octubre de 2026)  
**Canal Operativo:** Telegram Bot API (`@DesenmascaraBot`)  
**Lema:** *Reenvía el mensaje. Desenmascara la estafa. Las demás herramientas adivinan; Desenmascara confirma con la fuente.*

---

## 1. Misión del Coordinador
Dirigir la entrega técnica del Producto Mínimo Viable (PMV) de **Desenmascara** en 48 horas, coordinar a los 4 integrantes del equipo, garantizar la interoperabilidad técnica mediante contratos de datos estrictos, ejecutar la integración continua por etapas y asegurar que el factor diferencial esté operativo desde el sábado a mediodía utilizando **Telegram Bot API como canal principal y nativo**.

---

## 2. Decisión Estratégica de Canal: Telegram Bot API
Al no disponer de acceso inmediato a la API comercial de WhatsApp Business y para evitar las limitaciones críticas del Sandbox de Twilio (que exige códigos manuales `join...`, caduca a los 3 días e introduce fricción letal ante el jurado), **Telegram es el canal oficial de Desenmascara en el hackathon**:
- **Cero fricción de onboarding:** El jurado y los usuarios acceden en un segundo escaneando un código QR o abriendo `@DesenmascaraBot`, sin códigos de invitación ni aprobaciones previas.
- **Capacidades interactivas superiores:** Menús con botones nativos (`ReplyKeyboardMarkup` e `InlineKeyboardMarkup`), compartición segura de contacto criptográficamente firmado (`request_contact=True`) para validar la identidad telefónica en Llamada Verificada, y soporte nativo de notas de voz en formato OGG/Opus e imágenes de alta definición.
- **Misma arquitectura central:** El motor de 6 detectives, las APIs de verificación y la base de datos Supabase son 100% independientes del canal y operan idénticamente.

---

## 3. Contexto del Producto y Factor Diferencial
Desenmascara implementa **tres capas de protección**:

1. **Confirmar con la fuente (Certeza):**
   - **Llamada Verificada:** La entidad bancaria u operadora registra en tiempo real sus llamadas salientes legítimas en un Panel o API dedicada (con código unívoco de 4 dígitos y caducidad de 15 minutos). Cuando el usuario recibe una llamada sospechosa, consulta a `@DesenmascaraBot` en Telegram y este confirma si la llamada es real o falsa.
   - **Círculo de Confianza:** Red de protección familiar y empresarial con doble consentimiento en Telegram. Ante mensajes de *"Mamá, cambié de número, mándame dinero"*, el sistema consulta automáticamente al familiar verificado en su chat antes de que la víctima transfiera. Incluye alertas en cadena y protocolo de palabra clave contra clonación de voz con IA.
2. **Preguntar a la comunidad (Evidencia):**
   - **Banco de Números:** Inteligencia colectiva que asigna un nivel de riesgo (0 a 100) a números telefónicos, llaves Bre-B y cuentas bancarias, cruzando reportes de usuarios únicos en 30 días, historial y lista blanca oficial.
   - **Antes de Pagar:** Confirmador de compras en redes sociales y comercio electrónico informal; analiza ofertas, perfil del vendedor y llave de pago antes de transferir.
3. **Detectar con IA (Probabilidad explicable):**
   - **El Cerebro (6 Detectives):** Traductor (OCR con visión + Whisper para notas de voz de Telegram), Extractor de Pistas regex, Detective de Enlaces y Números (Safe Browsing, URLhaus, RDAP), Psicólogo (LLM con salida estructurada JSON/Pydantic), Archivista (Embeddings semánticos con `pgvector` para detección de campañas masivas) y el Juez (sistema determinista de scoring 0–100 y semáforo explicable con Rayos X).

---

## 4. Reparto de Responsabilidades del Equipo

| Integrante / Agente | Rol Principal | Misión Concreta | Frontera de Código / Responsabilidad |
| :--- | :--- | :--- | :--- |
| **Miguel** *(Agente Backend)* | Backend e Integración | Servidor central FastAPI, Webhook seguro de Telegram (`X-Telegram-Bot-Api-Secret-Token`), integración con Supabase, APIs de Llamada Verificada, Círculo de Confianza y Banco de Números, y despliegue continuo (Render/Railway). | Directorio `/backend`, rutas de API, clientes Supabase y Telegram Bot API. |
| **Luis Guillermo Nieto** *(Agente Detección / IA)* | IA y Datos | Motor de 6 detectives, prompts del Psicólogo con Pydantic, transcripción con Whisper de audios OGG de Telegram, embeddings semánticos en `pgvector`, reglas duras del Juez y calibración con dataset. | Directorio `/ai_engine`, pipelines de OCR/Whisper, prompts y scoring. |
| **Gerhard Arce** *(Agente Conversacional y Frontend)* | Bot de Telegram, Banco de Números y Dashboard | Experiencia conversacional en Telegram (menú de 6 botones interactivos, flujos guiados), lógica del Banco de Números y construcción del Dashboard Next.js con 4 vistas y Supabase Realtime. | Directorio `/frontend` (Dashboard Next.js/Lovable) y `/bot/handlers` (Telegram). |
| **IngBocadillo** *(Agente QA y Producto)* | Producto, Pitch y Calidad | Dataset de 140 casos reales, pruebas automáticas, red teaming (inyección/typosquatting), generación del código QR del bot para el jurado y dirección de la demo en vivo. | Directorio `/tests`, `/dataset`, auditoría de seguridad y verificación final. |

---

## 5. Las 10 Etapas de Construcción

- **Etapa 1 · Esqueleto (Viernes Noche):** Bot creado con BotFather (`@DesenmascaraBot`), servidor FastAPI, Webhook de Telegram con Secret Token y las 12 tablas en Supabase. *Criterio de éxito: el bot responde /start con el teclado de 6 opciones.*
- **Etapa 2 · Primer Cerebro (Viernes Noche):** Prompting del Psicólogo con salida JSON estricta y semáforo básico en Telegram.
- **Etapa 3 · Llamada Verificada (Sábado Mañana - HITO DE ORO):** API de registro y consulta de llamadas, código de 4 dígitos (TTL 15 min), validación de teléfono y Panel de la entidad. *Criterio de éxito: sin registro dice NO; con registro dice SÍ y muestra código.*
- **Etapa 4 · Pistas y Enlaces (Sábado Mañana):** Reglas regex, lista blanca de dominios oficiales, listas negras (Safe Browsing / URLhaus) y detección de typosquatting/punycode.
- **Etapa 5 · Banco de Números y Llamadas (Sábado Tarde):** Algoritmo de nivel de riesgo para teléfonos y llaves Bre-B, lista blanca oficial, transcripción de notas de voz de Telegram con Whisper y detección de vishing.
- **Etapa 6 · Círculo de Confianza (Sábado Tarde):** Vinculación de contactos en Telegram, detección de falso familiar, consulta interactiva al familiar verificado y alertas en cadena.
- **Etapa 7 · Capturas, Antes de Pagar, Memoria y Juez (Sábado Noche):** Visión multimodal para fotos enviadas a Telegram, cruce de ofertas con Banco de Números, indexación en `pgvector` y reglas duras del Juez.
- **Etapa 8 · Dashboard en Tiempo Real (Sábado Noche):** 4 vistas en Next.js (Radar de campañas, Verificar mensaje con Rayos X, Banco de números, Panel entidad) con Supabase Realtime.
- **Etapa 9 · Seguridad y Medición (Domingo Mañana):** Validación de Secret Token, rate limiting, RLS en base de datos, escaneo de vulnerabilidades y evaluación formal del dataset (precisión y recall).
- **Etapa 10 · Pulido, Demo y Entrega (Domingo Mediodía):** Ensayos cronometrados de la demo (3 escenas con los 4 integrantes usando Telegram), video de contingencia de 3 minutos y entrega con QR directo.

---

## 6. Control de Integración
1. **Contrato Único:** Todos los agentes respetan `01_CONTRATO_COMPARTIDO.md`.
2. **Cero Secretos:** `TELEGRAM_BOT_TOKEN`, llaves de Supabase y de LLM solo en `.env` y variables de entorno de producción.
3. **Pruebas de Integración:** Todo commit a `main` debe superar las pruebas de webhook y respuesta en menos de 8 segundos.
