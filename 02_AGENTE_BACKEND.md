# Agente 1 — Backend, APIs y Orquestación

**Responsable Líder:** Miguel  
**Tecnologías:** Python 3.12 · FastAPI · Pydantic v2 · HTTPX · Supabase-py · Twilio SDK  
**Despliegue:** Render / Railway (Servicio Web 24/7 con SSL automático)

---

## 1. Misión del Agente Backend
Construir, asegurar y mantener el servidor central de Desenmascara. Es el corazón operativo que recibe los webhooks de WhatsApp (Twilio), descarga y valida los medios en memoria, orquesta las 6 revisiones del Cerebro de IA, gestiona las APIs de Llamada Verificada, Círculo de Confianza y Banco de Números, y persiste los resultados anonimizados en Supabase.

---

## 2. Límites y Fronteras de Responsabilidad
- **Responsable de:** Enrutamiento HTTP, validación de esquemas, middlewares de seguridad, orquestación asíncrona, integración con Twilio/Telegram, llamadas a base de datos y control de concurrencia.
- **No es responsable de:**
  - Rediseñar prompts internos o calibrar los pesos heurísticos del Juez (responsabilidad de Luis).
  - Diseñar la redacción de los mensajes del bot o maquetar componentes web (responsabilidad de Gerhard).
  - Modificar las pruebas de aceptación para forzar resultados positivos (responsabilidad de IngBocadillo).

---

## 3. Arquitectura de Endpoints (FastAPI)

```
/api/v1
  ├── /webhook
  │     ├── POST /whatsapp             # Webhook oficial de Twilio para mensajes entrantes
  │     └── POST /telegram             # Webhook alternativo (Plan B)
  ├── /verify
  │     └── POST /                     # Verificación pública usada por la caja del Dashboard
  ├── /llamadas
  │     ├── POST /registrar            # API privada para entidades (BancoAndino registra llamada)
  │     └── POST /consultar            # Consulta rápida desde el bot con el teléfono del cliente
  ├── /circulo
  │     ├── POST /invitar              # Genera código de vinculación familiar
  │     ├── POST /responder            # Procesa la respuesta SÍ/NO del familiar verificado
  │     └── POST /alerta-cadena        # Difunde broadcast de alerta ante fraude confirmado
  ├── /banco
  │     ├── GET  /consultar            # Consulta nivel de riesgo de teléfono, llave Bre-B o cuenta
  │     ├── POST /reportar             # Añade reporte comunitario (1 por persona única)
  │     └── POST /solicitar-revision   # Impugnación por parte del dueño de una línea
  ├── /compras
  │     └── POST /verificar-oferta     # Orquestación de "Antes de pagar"
  └── /health
        └── GET  /                     # Health check con diagnóstico sin fuga de secretos
```

---

## 4. Tareas Prioritarias (P0 / P1)

### P0 — Imprescindibles para la Entrega
1. **Webhook de Twilio WhatsApp:**
   - Validar la firma criptográfica `X-Twilio-Signature` en cada request entrante.
   - Soportar payloads multimodales: extraer texto, descargar imágenes (capturas) y audios (notas de voz) mediante streaming autenticado a Twilio Media Storage.
   - Responder en menos de 8 segundos respetando los timeouts de webhook de mensajería (usar background tasks de FastAPI si el pipeline de IA supera 5 segundos).
2. **Orquestación del Cerebro:**
   - Invocar secuencialmente al pipeline del motor: Traductor (OCR/Whisper) -> Extractor de Pistas -> Detective de Enlaces -> Psicólogo LLM -> Archivista pgvector -> Juez determinista.
3. **API de Llamada Verificada:**
   - Endpoint de registro con validación de API Key (`entidades.api_key_hash`).
   - Generación de código aleatorio de 4 dígitos criptográficamente seguro (`secrets.randbelow(10000)`).
   - Inserción en `llamadas_registradas` con TTL de 15 minutos (`vence_at = now() + interval '15 minutes'`).
   - Endpoint de consulta que busca registros activos coincidentes con el número del remitente de WhatsApp (usado como llave natural).
4. **Persistencia en Supabase:**
   - Guardar cada evento en la tabla `verificaciones` con texto anonimizado (eliminando nombres, cédulas y cuentas con regex).
   - Actualizar contadores en la tabla `indicadores` del Banco de Números.

### P1 — Mejoras de Alto Impacto
- Endpoint `/api/v1/circulo/verificar-familiar` con cola de espera y temporizador de 5 minutos.
- Endpoint de exportación de indicadores maliciosos (IOCs) en formato JSON para entidades bancarias.
- Integración del Bot de Telegram como respaldo automático si Twilio reporta tasa de error > 10%.

---

## 5. Requisitos de Seguridad y Rendimiento

```python
# Ejemplo de validación obligatoria de Webhook Twilio
from twilio.request_validator import RequestValidator
from fastapi import Request, HTTPException, Header
import os

validator = RequestValidator(os.getenv("TWILIO_AUTH_TOKEN"))

async def verify_twilio_signature(request: Request, x_twilio_signature: str = Header(None)):
    url = str(request.url)
    form_data = await request.form()
    params = dict(form_data)
    if not validator.validate(url, params, x_twilio_signature):
        raise HTTPException(status_code=403, detail="Firma de Twilio inválida")
```

- **Mitigación SSRF:** Al descargar medios de Twilio o consultar reputación de URLs, validar que las peticiones se realicen únicamente hacia dominios en lista blanca (`api.twilio.com`, APIs oficiales de seguridad) y bloquear estrictamente cualquier redirección a IPs privadas (`10.0.0.0/8`, `192.168.0.0/16`, `127.0.0.1`, AWS/GCP metadata endpoints).
- **Rate Limiting:** Implementar limitación por hash de número telefónico (máximo 15 consultas por minuto y 60 por día) y por IP de origen.
- **Anonimización In-Flight:** Ningún payload entrante se escribe en base de datos con números de teléfono en texto plano; aplicar inmediatamente `HMAC-SHA256(phone, SERVER_SECRET)`.

---

## 6. Entregables Verificables
- Servidor FastAPI desplegado en URL pública HTTPS.
- Suite de tests unitarios de rutas con `pytest` y `httpx.AsyncClient`.
- Archivo `.env.example` completo y documentado.
- Logs limpios estructurados en JSON (sin stack traces ni números telefónicos legibles).
