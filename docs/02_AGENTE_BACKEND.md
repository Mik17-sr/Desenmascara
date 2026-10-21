# Agente 1 — Backend, APIs y Orquestación

**Responsable Líder:** Miguel  
**Tecnologías:** Python 3.12 · FastAPI · Pydantic v2 · HTTPX · Supabase-py · Telegram Bot API  
**Despliegue:** Render / Railway (Servicio Web 24/7 con SSL automático)

---

## 1. Misión del Agente Backend
Construir, asegurar y mantener el servidor central de Desenmascara. Es el motor que recibe los webhooks de Telegram (`@DesenmascaraBot`), descarga y procesa medios en memoria (fotos para OCR y notas de voz para Whisper), orquesta las 6 revisiones del Cerebro de IA, gestiona las APIs de Llamada Verificada, Círculo de Confianza y Banco de Números, y persiste los resultados anonimizados en Supabase.

---

## 2. Límites y Fronteras de Responsabilidad
- **Responsable de:** Rutas HTTP, validación de Webhook de Telegram con Secret Token, streaming de medios desde Telegram, orquestación asíncrona, clientes Supabase y control de concurrencia.
- **No es responsable de:**
  - Calibración heurística del Juez ni prompts del Psicólogo (responsabilidad de Luis).
  - Textos conversacionales ni componentes del Dashboard (responsabilidad de Gerhard).
  - Modificación de pruebas para enmascarar fallos (responsabilidad de IngBocadillo).

---

## 3. Arquitectura de Endpoints (FastAPI)

```
/api/v1
  ├── /webhook
  │     └── POST /telegram             # Webhook oficial de Telegram Bot API
  ├── /verify
  │     └── POST /                     # Verificación pública consumida por la caja del Dashboard
  ├── /llamadas
  │     ├── POST /registrar            # API privada para entidades (BancoAndino registra llamada)
  │     └── POST /consultar            # Consulta desde el bot con el teléfono o ID del cliente
  ├── /circulo
  │     ├── POST /invitar              # Genera solicitud de vinculación en Telegram
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

## 4. Implementación del Webhook Seguro de Telegram

```python
from fastapi import FastAPI, Request, HTTPException, Header
import os, httpx

app = FastAPI(title="Desenmascara API", version="7.0")
TELEGRAM_SECRET_TOKEN = os.getenv("TELEGRAM_SECRET_TOKEN")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

@app.post("/api/v1/webhook/telegram")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(None)
):
    # Validación criptográfica de origen Telegram
    if x_telegram_bot_api_secret_token != TELEGRAM_SECRET_TOKEN:
        raise HTTPException(status_code=403, detail="Secret token de Telegram inválido")
    
    update = await request.json()
    # Procesamiento asíncrono del update (mensaje, foto, nota de voz, contacto o callback query)
    await orchestrate_telegram_update(update)
    return {"ok": True}
```

### Descarga Segura de Medios desde Telegram
Cuando el usuario envía una foto o nota de voz:
1. Extraer `file_id` del payload de Telegram.
2. Invocar `https://api.telegram.org/bot<TOKEN>/getFile?file_id=<FILE_ID>`.
3. Descargar el archivo binario en memoria mediante streaming seguro (sin guardar en disco persistente).
4. Si es imagen (`photo`): pasar buffer al OCR con visión del LLM.
5. Si es audio (`voice` en formato `.ogg`): pasar buffer a Whisper para transcripción e inmediatamente purgar el buffer de memoria.

---

## 5. Tareas Prioritarias (P0 / P1)

### P0 — Imprescindibles para la Entrega
1. **Webhook de Telegram con Secret Token:** Enrutamiento confiable y respuesta en < 8 segundos.
2. **Orquestación del Cerebro:** Secuencia completa: Traductor -> Pistas -> Enlaces -> Psicólogo -> Archivista -> Juez.
3. **API de Llamada Verificada:** Generación de código de 4 dígitos con TTL de 15 minutos, persistencia en `llamadas_registradas` y consulta instantánea.
4. **Persistencia en Supabase:** Almacenamiento anonimizado en `verificaciones` y actualización de métricas para el Dashboard.

### P1 — Mejoras de Alto Impacto
- Manejo de botones interactivos (`InlineKeyboardMarkup`) para confirmaciones rápidas de "Útil", "Reportar" o "Ya caí".
- Endpoint `/api/v1/circulo/verificar-familiar` con temporizador de 5 minutos y broadcast de alerta en cadena.

---

## 6. Requisitos de Seguridad
- **Mitigación SSRF:** Descargas restringidas exclusivamente a `api.telegram.org` y APIs de reputación en lista blanca. Bloqueo de rangos privados (`127.0.0.1`, `10.0.0.0/8`, `169.254.169.254`).
- **Rate Limiting:** Máximo 20 peticiones por minuto por `telegram_chat_id` y por IP.
- **Anonimización:** Aplicar `HMAC-SHA256(user_id, SERVER_SECRET)` antes de registrar en Supabase.
