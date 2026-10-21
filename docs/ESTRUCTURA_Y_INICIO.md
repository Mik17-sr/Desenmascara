# Guía de Inicio y Estructura Profesional del Proyecto

Este documento define **por dónde empezar** la construcción del proyecto **Desenmascara** y proporciona una **estructura de archivos y carpetas profesional**, modular e ideal para el trabajo con múltiples agentes o desarrolladores.

---

## 1. ¿Por dónde se empieza? (Paso a Paso)

Para garantizar un desarrollo ágil y sin bloqueos entre agentes, sigue esta secuencia de ejecución:

### Paso 1: Configuración del Entorno y Repositorio Base
1. Crear el repositorio Git e ignorar secretos (`.gitignore`).
2. Configurar el gestor de dependencias (por ejemplo, `uv`, `poetry` o `pip` con `requirements.txt`).
3. Definir las variables de entorno ficticias en `.env.example`.

### Paso 2: Implementación del Contrato de Datos Compartido (Single Source of Truth)
* **Archivo:** `app/schemas/analysis.py`
* **Acción:** Definir los modelos de Pydantic (`AnalysisInput`, `AnalysisResult`, `Signal`, `LinkStatus`, etc.) basados rigurosamente en `01_CONTRATO_COMPARTIDO.md`.

### Paso 3: Motor de Análisis Local / Heurístico (Core Domain)
* **Archivo:** `app/engine/`
* **Acción:** Construir las reglas de detección simples (urgencia, pedido de OTP, links sospechosos) y el parsing estructurado para el LLM. Probar este módulo aisladamente con `pytest` sin requerir servidor HTTP ni Telegram.

### Paso 4: Capa de Persistencia y Repositorio de Datos
* **Archivo:** `app/db/`
* **Acción:** Crear los modelos de tabla/colección y las funciones de lectura/escritura (`CRUD`) para registrar los análisis y el feedback.

### Paso 5: API REST / Backend
* **Archivo:** `app/api/` y `app/services/`
* **Acción:** Exponer el endpoint `POST /api/v1/analyze`, conectando la validación del esquema, la invocación del motor y el guardado en base de datos.

### Paso 6: Bot de Telegram (Adaptador de Entrada)
* **Archivo:** `app/bot/`
* **Acción:** Implementar comandos (`/start`, `/help`) y el handler de mensajes que reenvía el texto a la API o al servicio del motor, formateando la salida para el usuario final.

### Paso 7: Pruebas End-to-End, Seguridad y Validación
* **Acción:** Ejecutar la suite de pruebas de QA (`tests/`), auditorías de seguridad y validar contra `08_VALIDACION_FINAL.md`.

---

## 2. Estructura Profesional de Carpetas

A continuación se presenta la arquitectura de carpetas siguiendo el patrón **Domain-Driven Layout / Modular Clean Architecture** recomendado para proyectos modernos en Python con FastAPI y Pydantic:

```text
desenmascara-core/
│
├── .github/                     # Workflows de CI/CD, linter y tests automáticos
│   └── workflows/
│       └── ci.yml
│
├── docs/                        # Especificaciones de los Agentes y Documentación
│   ├── 00_COORDINADOR.md
│   ├── 01_CONTRATO_COMPARTIDO.md
│   ├── 02_AGENTE_BACKEND.md
│   ├── 03_AGENTE_DETECCION_IA.md
│   ├── 04_AGENTE_TELEGRAM.md
│   ├── 05_AGENTE_DATOS.md
│   ├── 06_AGENTE_SEGURIDAD.md
│   ├── 07_AGENTE_QA.md
│   ├── 08_VALIDACION_FINAL.md
│   └── 09_PLAN_48_HORAS.md
│
├── app/                         # Código fuente principal de la aplicación
│   ├── __init__.py
│   ├── main.py                  # Punto de entrada de la aplicación FastAPI
│   ├── config.py                # Gestión de variables de entorno (Pydantic Settings)
│   │
│   ├── api/                     # Capa de presentación HTTP / Routers
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── router.py        # Agregador de rutas de la v1
│   │   │   ├── endpoints/
│   │   │   │   ├── analyze.py   # Route POST /api/v1/analyze
│   │   │   │   ├── feedback.py  # Route POST /api/v1/feedback
│   │   │   │   └── health.py    # Route GET /health
│   │   └── middlewares/        # Rate limiting, CORS, error handlers
│   │
│   ├── schemas/                 # DTOs y Contratos de Datos (Pydantic Models)
│   │   ├── __init__.py
│   │   ├── analysis.py          # Definición exacta de 01_CONTRATO_COMPARTIDO
│   │   ├── feedback.py
│   │   └── common.py
│   │
│   ├── engine/                  # Motor de Análisis de Fraude e IA (Aislado)
│   │   ├── __init__.py
│   │   ├── analyzer.py          # Coordinador del motor híbrido
│   │   ├── rules/               # Reglas deterministas / heurísticas
│   │   │   ├── __init__.py
│   │   │   ├── urgency.py
│   │   │   ├── credentials.py
│   │   │   └── links.py
│   │   ├── adapters/            # Adaptadores de proveedores externos
│   │   │   ├── __init__.py
│   │   │   ├── llm_provider.py  # Integración con OpenAI/Gemini/Anthropic
│   │   │   └── url_reputation.py# Integración con Safe Browsing/VirusTotal
│   │   └── prompts.py           # Prompts del sistema e instrucciones del modelo
│   │
│   ├── services/                # Capa de orquestación de negocio
│   │   ├── __init__.py
│   │   └── analysis_service.py  # Conecta API/Bot con Engine y DB
│   │
│   ├── db/                      # Capa de datos y persistencia
│   │   ├── __init__.py
│   │   ├── session.py           # Conexión a Base de Datos
│   │   ├── models/              # ORM Models (SQLAlchemy / SQLModel)
│   │   │   ├── __init__.py
│   │   │   ├── analysis.py
│   │   │   └── feedback.py
│   │   └── repositories/        # Patrón Repository para acceso a datos
│   │       ├── __init__.py
│   │       ├── analysis_repo.py
│   │       └── feedback_repo.py
│   │
│   └── bot/                     # Adaptador para el Bot de Telegram
│       ├── __init__.py
│       ├── main.py              # Invocación/polling del bot
│       ├── handlers.py          # Manejadores de /start, /help y mensajes
│       ├── formatters.py        # Formateador de AnalysisResult a Markdown/Telegram
│       └── client.py            # Cliente para invocar a la API o al servicio
│
├── tests/                       # Suite de pruebas automatizadas
│   ├── conftest.py              # Fixtures de pytest (DB temporal, clientes simulados)
│   ├── unit/                    # Pruebas unitarias
│   │   ├── test_engine_rules.py
│   │   ├── test_schemas.py
│   │   └── test_formatters.py
│   ├── integration/             # Pruebas de integración
│   │   ├── test_api_endpoints.py
│   │   └── test_db_repository.py
│   └── security/                # Pruebas de abuso e inyección
│       ├── test_prompt_injection.py
│       └── test_input_limits.py
│
├── scripts/                     # Scripts auxiliares de mantenimiento o migraciones
│   └── seed_test_data.py
│
├── .env.example                 # Plantilla de variables de entorno (SIN SECRETOS)
├── .gitignore                   # Exclusión de entornos virtuales, .env, caches
├── pyproject.toml               # Configuración del proyecto, dependencias y herramientas
├── README.md                    # Visión general e instrucciones del proyecto
└── Dockerfile                   # Configuración para despliegue en contenedores
```

---

## 3. Matriz de Asignación por Agente

Cada agente debe concentrar sus cambios exclusivamente en su módulo correspondiente para evitar conflictos de integración:

| Agente | Subcarpeta Principal asignada |
| :--- | :--- |
| **01 Contrato Compartido** | `app/schemas/` |
| **02 Agente Backend** | `app/api/`, `app/services/`, `app/config.py`, `app/main.py` |
| **03 Agente Detección / IA**| `app/engine/` |
| **04 Agente Telegram** | `app/bot/` |
| **05 Agente Datos** | `app/db/` |
| **06 Agente Seguridad** | `.env.example`, `app/api/middlewares/`, `tests/security/` |
| **07 Agente QA** | `tests/` |