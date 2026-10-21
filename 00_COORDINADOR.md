# Agente 0 — Coordinador Técnico e Integrador

**Proyecto:** Desenmascara · Versión 7.0  
**Evento:** Colombia 5.0 Hackathon (16 al 18 de octubre de 2026)  
**Lema:** *Reenvía el mensaje. Desenmascara la estafa. Las demás herramientas adivinan; Desenmascara confirma con la fuente.*

---

## 1. Misión del Coordinador
Dirigir la entrega técnica del Producto Mínimo Viable (PMV) de **Desenmascara** en 48 horas, coordinar a los 4 integrantes del equipo (o sus respectivos subagentes técnicos), garantizar la interoperabilidad mediante contratos de datos estrictos, ejecutar la integración continua por etapas y asegurar que el factor diferencial esté operativo desde el sábado a mediodía.

---

## 2. Contexto del Producto y Factor Diferencial
Desenmascara es un ecosistema de ciberseguridad ciudadana accesible a través de WhatsApp que desenmascara fraudes por SMS, WhatsApp y llamadas telefónicas (vishing). A diferencia de las soluciones convencionales que se limitan a estimaciones probabilísticas, Desenmascara implementa **tres capas de protección**:

1. **Confirmar con la fuente (Certeza):**
   - **Llamada Verificada:** La entidad bancaria u operadora registra en tiempo real sus llamadas salientes legítimas en un Panel o API dedicada (con código unívoco de 4 dígitos y caducidad de 15 minutos). Cuando el usuario recibe una llamada sospechosa, consulta al bot por WhatsApp y este confirma si la llamada es real o falsa.
   - **Círculo de Confianza:** Red de protección familiar y empresarial con doble consentimiento. Ante mensajes del tipo *"Mamá, cambié de número, mándame dinero"*, el sistema consulta automáticamente al familiar verificado en su línea oficial antes de que la víctima realice transferencias. Incluye alertas en cadena y protocolo de palabra clave contra clonación de voz con IA.
2. **Preguntar a la comunidad (Evidencia):**
   - **Banco de Números:** Inteligencia colectiva que asigna un nivel de riesgo (0 a 100) a números telefónicos, llaves Bre-B y cuentas bancarias, cruzando reportes de usuarios únicos en 30 días, historial y lista blanca oficial.
   - **Antes de Pagar:** Confirmador de compras en redes sociales y comercio electrónico informal; analiza ofertas, perfil del vendedor y llave de pago antes de transferir.
3. **Detectar con IA (Probabilidad explicable):**
   - **El Cerebro (6 Detectives):** Traductor (OCR + Whisper), Extractor de Pistas, Detective de Enlaces y Números (Safe Browsing, URLhaus, RDAP), Psicólogo (LLM con salida estructurada JSON/Pydantic), Archivista (Embeddings semánticos con `pgvector` para detección de campañas masivas) y el Juez (sistema determinista de scoring 0–100 y semáforo explicable con Rayos X).

---

## 3. Reparto de Responsabilidades del Equipo

El equipo multidisciplinario se organiza en 4 áreas de propiedad técnica estricta:

| Integrante / Agente | Rol Principal | Misión Concreta | Frontera de Código / Responsabilidad |
| :--- | :--- | :--- | :--- |
| **Miguel** *(Agente Backend)* | Backend e Integración | Servidor central FastAPI, Webhook de WhatsApp (Twilio), base de datos Supabase, APIs de Llamada Verificada, Círculo de Confianza y Banco de Números, seguridad del servidor y despliegue (Render/Railway). | Directorio `/backend`, rutas de API, clientes Supabase y Twilio. No toca prompts ni lógica visual del Dashboard. |
| **Luis Guillermo Nieto** *(Agente Detección / IA)* | IA y Datos | Motor de 6 detectives, prompts del Psicólogo con Pydantic, transcripción con Whisper, embeddings semánticos en `pgvector`, reglas duras del Juez y medición con dataset. | Directorio `/ai_engine`, pipelines de OCR/Whisper, prompts y scoring. No expone rutas HTTP directas ni manipula WhatsApp. |
| **Gerhard Arce** *(Agente Conversacional y Frontend)* | Llamadas, Banco de Números, Bot y Dashboard | Conversación del bot de WhatsApp (menú de 6 opciones y flujos conversacionales), módulo de llamadas/vishing, lógica del Banco de Números y construcción del Dashboard Next.js con 4 vistas. | Directorio `/frontend` (Dashboard Next.js/Lovable) y `/bot/flows` (diseño conversacional). |
| **IngBocadillo** *(Agente QA y Producto)* | Producto, Pitch y Calidad | Dataset de 140 casos reales (100 mensajes, 20 llamadas, 20 compras), pruebas de regresión, red teaming (inyección/typosquatting), guion y dirección de la demo en vivo. | Directorio `/tests`, `/dataset`, auditoría de seguridad y verificación de aceptación de entregables. |

---

## 4. Las 10 Etapas de Construcción (Secuencia Crítica)

Para mitigar riesgos y asegurar un entregable funcional el domingo, el desarrollo sigue un modelo de construcción incremental en 10 etapas:

- **Etapa 1 · Esqueleto (Viernes Noche):** Repositorio en GitHub, servidor FastAPI, Webhook firmado de Twilio y las 12 tablas en Supabase. *Criterio de éxito: el bot responde "Hola" con el menú de 6 opciones.*
- **Etapa 2 · Primer Cerebro (Viernes Noche):** Prompting del Psicólogo con salida JSON estricta y semáforo básico. *Criterio de éxito: un SMS del dataset recibe veredicto ALTO RIESGO justificado.*
- **Etapa 3 · Llamada Verificada (Sábado Mañana - HITO DE ORO):** API de registro y consulta de llamadas, código de 4 dígitos (TTL 15 min) y Panel de la entidad. *Criterio de éxito: sin registro dice NO; con registro dice SÍ y muestra código.*
- **Etapa 4 · Pistas y Enlaces (Sábado Mañana):** Reglas regex, lista blanca de dominios oficiales, listas negras (Safe Browsing / URLhaus) y detección de typosquatting/punycode.
- **Etapa 5 · Banco de Números y Llamadas (Sábado Tarde):** Algoritmo de nivel de riesgo para teléfonos y llaves Bre-B, lista blanca oficial, transcripción de notas de voz con Whisper y detección de vishing.
- **Etapa 6 · Círculo de Confianza (Sábado Tarde):** Invitación/aceptación familiar, detección de falso familiar en texto, consulta interactiva al familiar verificado y alertas en cadena.
- **Etapa 7 · Capturas, Antes de Pagar, Memoria y Juez (Sábado Noche):** Visión multimodal para capturas, cruce de ofertas con Banco de Números, indexación semántica en `pgvector` y reglas duras del Juez.
- **Etapa 8 · Dashboard en Tiempo Real (Sábado Noche):** 4 vistas en Next.js (Radar de campañas, Verificar mensaje con Rayos X, Banco de números, Panel entidad) con Supabase Realtime.
- **Etapa 9 · Seguridad y Medición (Domingo Mañana):** Validación de firmas Twilio, rate limiting, RLS en base de datos, escaneo de vulnerabilidades y evaluación formal del dataset (precisión y recall).
- **Etapa 10 · Pulido, Demo y Entrega (Domingo Mediodía):** Ensayos cronometrados de la demo (3 escenas con los 4 integrantes), video de contingencia de 3 minutos y congelamiento de código.

---

## 5. Gestión del Alcance (Scope Management)

### P0 — Imprescindible para el Domingo (Core Hackathon)
- Bot de WhatsApp interactivo con procesamiento de texto, capturas y notas de voz.
- Llamada Verificada funcional de extremo a extremo con entidad simulada (BancoAndino).
- Banco de Números con nivel de riesgo (0–100) para teléfonos y llaves Bre-B, y lista blanca oficial.
- Cerebro de detección con las 6 revisiones y explicación desglosada (Rayos X).
- Dashboard publicado en Vercel con las 4 vistas operativas en tiempo real.
- 13 defensas de ciberseguridad activas (OWASP Top 10 LLM & API).

### P1 — Importante (Añade Ventaja Competitiva)
- Círculo de Confianza con doble consentimiento y alertas en cadena.
- Módulo "Antes de Pagar" con análisis heurístico de ofertas y verificación de llaves.
- Detección de brotes de campañas masivas mediante embeddings en `pgvector`.
- Flujo de emergencia "Ya caí" con generación de guía de mitigación inmediata.

### P2 — Deseable (Solo si el tiempo lo permite)
- Protocolo de palabra clave familiar anti-clonación de voz.
- Exportación automática del Kit de Denuncia en PDF.
- Grafo visual de redes de fraude (Cytoscape.js) en el Dashboard.
- Bot espejo en Telegram como infraestructura de respaldo (Plan B).

---

## 6. Reglas de Control de Integración y Calidad
1. **Contrato Sagrado:** Nadie modifica `01_CONTRATO_COMPARTIDO.md` unilateralmente. Todo ajuste de esquemas de datos requiere aprobación del Coordinador.
2. **Aislamiento de Ramas:** Se trabaja en ramas de funcionalidad (`feature/llamada-verificada`, `feature/cerebro-ia`, etc.). Los merges a `main` requieren revisión y test verde.
3. **Cero Secretos en Git:** Las API keys de LLMs, Twilio y Supabase residen exclusivamente en variables de entorno locales y en los dashboards de despliegue. `.env` está en `.gitignore`.
4. **Pruebas con Evidencia:** Ninguna tarea se marca como terminada sin captura, log de ejecución o prueba automatizada registrada.
