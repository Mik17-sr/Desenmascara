# Contrato Compartido entre Agentes y Módulos

**Proyecto:** Desenmascara · Versión 7.0 (Telegram Nativo)  
**Stack de Interoperabilidad:** FastAPI (Python 3.12) · Pydantic v2 · Supabase (PostgreSQL 15 + pgvector) · Telegram Bot API

---

## 1. Objetivo
Garantizar la interoperabilidad absoluta entre el Bot de Telegram (`@DesenmascaraBot`), el Dashboard Next.js, el Servidor FastAPI, el Motor de Detección de 6 detectives y la Persistencia en Supabase.

---

## 2. Entrada Normalizada al Motor de Análisis (`IncomingPayload`)

Cualquier evento de entrada desde Telegram o el Dashboard se normaliza a este esquema:

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal

class IncomingPayload(BaseModel):
    channel: Literal["telegram", "dashboard_box", "api"] = Field(..., description="Canal de origen")
    content_type: Literal["text", "photo", "voice", "phone_number", "payment_key", "purchase_offer"] = Field(...)
    raw_text: Optional[str] = Field(None, description="Texto del mensaje, transcripción o enlace")
    telegram_file_id: Optional[str] = Field(None, description="file_id de Telegram para descargar imagen o audio")
    telegram_chat_id: int = Field(..., description="ID del chat de Telegram para responder")
    user_identifier_hash: str = Field(..., description="HMAC-SHA256 del ID de usuario de Telegram o teléfono verificado")
    user_phone_verified: Optional[str] = Field(None, description="Teléfono validado si el usuario compartió contacto")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos auxiliares de transporte")
```

---

## 3. Contrato de la Revisión 4: Salida Estructurada del Psicólogo (LLM)

El LLM que ejecuta la Revisión 4 está encapsulado contra *Prompt Injection* y responde exclusivamente bajo este esquema JSON validado con Pydantic:

```json
{
  "canal": "sms | telegram | llamada | compra",
  "modalidad": "suplantacion_bancaria | falso_familiar | falso_asesor | falsa_compra_anticipo | paquete_retenido | falso_funcionario | otro",
  "entidad_suplantada": "Nombre de la entidad identificada o 'Ninguna'",
  "tacticas": ["urgencia", "amenaza", "pide_datos", "falso_premio", "secreto", "cambio_plataforma"],
  "pide": "Descripción precisa de qué exige el atacante (datos, transferencias, códigos OTP)",
  "instrucciones_ocultas": false,
  "explicacion": "Resumen claro y pedagógico en lenguaje humano del truco psicológico detectado"
}
```

*Regla de Seguridad:* Si `instrucciones_ocultas` es `true`, el motor suma automáticamente +20 puntos de riesgo al Juez.

---

## 4. Resultado Normalizado del Análisis (`AnalysisResult`)

Este es el contrato que devuelve el Cerebro y consume el Bot de Telegram y el Dashboard:

```json
{
  "risk_level": "low | suspicious | high",
  "risk_score": 96,
  "category": "Suplantación bancaria (smishing)",
  "summary": "El enlace no es el sitio oficial del banco y se creó hace 2 días. Usa urgencia y amenaza.",
  "rayos_x": {
    "enlace_imita_oficial": 30,
    "pide_claves_o_datos": 20,
    "parecido_campana_activa": 16,
    "dominio_nuevo_menor_30d": 15,
    "urgencia_amenaza": 10,
    "entidad_conocida": 5,
    "lista_negra_ioc": 0,
    "descuento_sitio_oficial": 0,
    "descuento_sin_peticion_datos": 0
  },
  "signals": [
    {
      "code": "DOMAIN_IMPERSONATION",
      "label": "El enlace imita el sitio oficial",
      "evidence": "bancoandino-seguro.co imita a bancoandino.com",
      "source": "enlaces",
      "points": 30
    },
    {
      "code": "CREDENTIAL_HARVESTING",
      "label": "Pide datos o claves",
      "evidence": "Texto exige 'valide sus datos'",
      "source": "psicologo",
      "points": 20
    }
  ],
  "recommendations": [
    "No abras el enlace ni ingreses datos.",
    "Si ya entregaste información, llama de inmediato al reverso de tu tarjeta.",
    "¿Deseas preparar tu kit de denuncia? Responde 1 o pulsa el botón correspondiente."
  ],
  "campaign_match": {
    "matched": true,
    "campaign_id": "c7a8b9-...",
    "campaign_name": "Falso BancoAndino - valide sus datos",
    "similarity_pct": 93,
    "total_reports_today": 312
  },
  "analysis_version": "v7.0"
}
```

---

## 5. Contratos de Verificación con la Fuente (Llamada Verificada y Círculo)

### A. Llamada Verificada (`/api/v1/llamadas`)
- **Registro previo de la Entidad (Saliente):**
  - `POST /api/v1/llamadas/registrar`
  - *Headers:* `X-Entity-API-Key: sec_live_...`
  - *Body:* `{"telefono_cliente": "+573100000000", "motivo": "Confirmar una compra", "asesor": "Laura M."}`
  - *Respuesta:* `{"success": true, "codigo_verificacion": "4821", "expires_in_seconds": 900, "registro_id": "uuid"}`
- **Consulta del Usuario desde Telegram:**
  - `POST /api/v1/llamadas/consultar`
  - *Body:* `{"telefono_cliente_hash": "hmac_...", "entidad_consultada": "BancoAndino", "telegram_chat_id": 12345678}`
  - *Respuesta:*
    - Si existe registro válido (<15 min): `{"is_verified": true, "entidad": "BancoAndino", "motivo": "Confirmar una compra", "codigo_esperado": "4821"}`
    - Si no existe registro: `{"is_verified": false, "entidad": "BancoAndino", "advertencia": "NO ES TU BANCO. Cuelga de inmediato.", "accion": "reportar_numero"}`

### B. Círculo de Confianza (`/api/v1/circulo`)
- **Doble Consentimiento en Telegram:**
  - El familiar recibe una notificación en su Telegram: *"Tu familiar te ha agregado a su Círculo de Confianza en Desenmascara. ¿Aceptas protegerlo? [SÍ] [NO]"*.
- **Interrogación ante Falso Familiar:**
  - Cuando el Psicólogo detecta `modalidad: falso_familiar` pidiendo dinero, el bot dispara un mensaje al Telegram del familiar real:
    - *"Tu mamá recibió un mensaje de un número nuevo diciendo ser tú y pidiendo $800.000. ¿Fuiste tú? [SÍ] [NO]"*.
  - Si responde NO: Se envía respuesta inmediata a la mamá (`● ES UNA ESTAFA`) y se dispara **alerta en cadena** a todo el grupo familiar bloqueando el número del atacante.

---

## 6. Contrato del Banco de Números y Antes de Pagar (`/api/v1/banco`)
- **Consulta de Nivel de Riesgo (0–100):**
  - `GET /api/v1/banco/consultar?tipo=telefono|llave_breb|cuenta&valor=...`
  - Retorna `nivel_riesgo`, `personas_distintas_30d`, `total_reportes`, `is_oficial` y `estado`.
- **Antes de Pagar (Confirmador de Compras):**
  - `POST /api/v1/compras/verificar-oferta`
  - Cruza el análisis de la captura de la oferta (precio sospechoso, anticipo) con el historial de reportes de la llave Bre-B en el Banco de Números.

---

## 7. Semántica Obligatoria del Semáforo
- **● BAJO RIESGO (0 a 39 puntos · Verde):** Sin indicios maliciosos. Recordatorio: ningún banco pide contraseñas por Telegram ni llamada.
- **● SOSPECHOSO (40 a 69 puntos · Amarillo):** Señales dudosas o falta de verificación. Requiere comprobar por canal oficial.
- **● ALTO RIESGO (70 a 100 puntos · Rojo):** Evidencia concreta de fraude. Bloquear, no transferir y preservar evidencia.
