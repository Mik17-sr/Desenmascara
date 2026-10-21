# Plan Clínico de Desarrollo: Backend, Integración y Persistencia (Supabase)

**Responsable:** Miguel Sierra  
**Ámbito:** Backend, Arquitectura de Integración, APIs de Llamada Verificada y Supabase  
**Estado:** En Ejecución  

---

## Misión
Garantizar una infraestructura de backend robusta, desacoplada y de alta resiliencia que coordine la recepción de peticiones, la orquestación del motor de detección de fraude, la consulta de servicios externos y la persistencia segura en Supabase, respetando rigurosamente el contrato compartido del proyecto.

---

## Fase 1: Arquitectura de Integración y Contratos de Datos

### 1.1. Congelación del Contrato Compartido (DTOs)
* **Objetivo:** Definir la fuente única de verdad para el intercambio de información entre la API, el motor de IA, la persistencia y los adaptadores de entrada (Telegram/Frontend).
* **Acción:**
  - Implementar en `app/schemas/contract.py` los modelos Pydantic validados: `AnalysisInput` y `AnalysisResult`.
  - Asegurar la inclusión estricta de enumeraciones reusables: `RiskLevel` (`low`, `medium`, `high`, `inconclusive`), `SignalSource`, `ConfidenceLevel` y `LinkStatus`.
  - Garantizar la calibración del campo `risk_score` como una escala heurística de 0 a 100.

### 1.2. Delimitación de Responsabilidades y Fronteras de Dominio
* **Objetivo:** Prevenir el acoplamiento de lógica de negocio o reglas antifraude dentro de las rutas de la API o la capa de datos.
* **Fronteras:**
  - **API Router:** Valida HTTP, límites de payload y orquesta llamadas.
  - **Motor (Engine):** Analiza contenido y produce señales. No conoce HTTP ni la base de datos.
  - **Repositorio (DB):** Persiste y consulta. No clasifica ni modifica la semántica de riesgo.

---

## Fase 2: Backend y Capa de API REST (FastAPI)

### 2.1. Configuración de Entorno y Core Asíncrono
* **Acción:**
  - Configurar `app/core/config.py` con `pydantic-settings` para la validación estricta de variables de entorno (`SUPABASE_URL`, `SUPABASE_KEY`, timeouts, etc.).
  - Configurar middlewares globales en `app/main.py`: CORS restringido, manejo de excepciones no controladas y trazabilidad mediante identificadores de petición (*Request-ID*).

### 2.2. Implementación de Endpoints Principales
* **Endpoint de Análisis (`POST /api/v1/analyze`):**
  - Recibir y validar `AnalysisInput`.
  - Aplicar rate-limiting y restricciones de longitud de texto (máximo 4000 caracteres) e insumos de enlaces.
  - Invocar el servicio de orquestación (`AnalysisService`) de forma asíncrona.
* **Endpoint de Feedback (`POST /api/v1/feedback`):**
  - Permitir el registro de utilidad o reporte de falsos positivos asociado a un id de análisis existente.
* **Endpoint de Salud (`GET /health`):**
  - Retornar estado del servicio y verificación de conectividad con Supabase y dependencias críticas sin exponer secretos.

### 2.3. Gestión de Excepciones y Seguridad en Errores
* **Acción:**
  - Garantizar que fallas internas, tiempos de espera o errores de la base de datos se traduzcan en estados `inconclusive` o respuestas HTTP estandarizadas.
  - Ocultar explícitamente *stack traces*, credenciales, cadenas de conexión y prompts internos en las respuestas al cliente.

---

## Fase 3: APIs de Llamada Verificada y Servicios Externos

### 3.1. Diseño de Adaptadores Desacoplados
* **Acción:**
  - Crear una interfaz estándar para verificaciones de reputación en `app/engine/adapters/` (por ejemplo, reputación de dominios/URLs con servicios tipo Google Safe Browsing o VirusTotal).
  - Asegurar que la API no visite ni descargue contenido arbitrario desde las URLs provistas por los usuarios.

### 3.2. Control de Timeouts y Resiliencia HTTP
* **Acción:**
  - Configurar un timeout estricto de cliente HTTP asíncrono (`httpx`) para todas las dependencias externas (máximo 3.0 a 5.0 segundos por llamada).
  - Implementar el patrón de degradación grácil (*Graceful Degradation*): si un servicio externo cae o agota el tiempo de espera, la respuesta debe marcar el estado correspondiente en la lista de `limitations` del resultado sin detener la ejecución del backend.

---

## Fase 4: Persistencia y Base de Datos (Supabase)

### 4.1. Diseños de Esquemas Relacionales en PostgreSQL (Supabase)
* **Tabla `analysis`:**
  - `id` (UUID, Primary Key)
  - `created_at` (TIMESTAMPTZ, Default NOW())
  - `source` (VARCHAR)
  - `user_ref` (VARCHAR, seudonimizado o NULL)
  - `risk_level` (VARCHAR)
  - `risk_score` (INT)
  - `summary` (TEXT)
  - `signals` (JSONB)
  - `recommendations` (JSONB)
  - `links` (JSONB)
  - `limitations` (JSONB)
  - `analysis_version` (VARCHAR)
  - `processing_ms` (INT)
* **Tabla `feedback`:**
  - `id` (UUID, Primary Key)
  - `analysis_id` (UUID, FK -> `analysis.id`)
  - `feedback_type` (VARCHAR: `useful`, `false_positive`, `incorrect`, `other`)
  - `comment` (VARCHAR, opcional, max 500 caracteres)
  - `created_at` (TIMESTAMPTZ)

### 4.2. Capa de Repositorio Asíncrono
* **Acción:**
  - Construir `app/db/repositories/analysis_repo.py` implementando la comunicación asíncrona con el cliente de Supabase / cliente PostgreSQL.
  - Asegurar la captura de errores de persistencia para evitar que un fallo al guardar devuelva una falsa notificación de éxito al cliente.

### 4.3. Minimización y Política de Privacidad de Datos
* **Acción:**
  - No almacenar credenciales, tokens, OTPs ni el mensaje original completo del usuario sin previa seudonimización y justificación.
  - Aplicar políticas de índices por fecha (`created_at`) y nivel de riesgo (`risk_level`) para optimizar lecturas e informes agregados.

---

##Matriz de Verificación del Plan

| Hito | Criterio de Aceptación | Estado |
| :--- | :--- | :---: |
| **Contrato Compartido** | DTOs de Pydantic validados y testeados |  Completado |
| **Ruta /health** | Respuesta 200 OK en `GET /health` |  Completado |
| **Ruta /api/v1/analyze** | Recibe payload, ejecuta stub/engine y retorna resultado estructurado | ⏳ Pendiente |
| **Conexión Supabase** | Inserción exitosa del modelo `AnalysisResult` en la DB | ⏳ Pendiente |
| **Resiliencia de APIs** | Expiración de timeout mapeada a `limitations` sin error 500 | ⏳ Pendiente |