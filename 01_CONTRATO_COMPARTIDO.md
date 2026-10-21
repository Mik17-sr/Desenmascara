# Contrato Compartido entre Agentes y Módulos

**Proyecto:** Desenmascara · Versión 7.0  
**Stack de Interoperabilidad:** FastAPI (Python 3.12) · Pydantic v2 · Supabase (PostgreSQL 15 + pgvector) · Next.js 14

---

## 1. Objetivo
Definir los esquemas de datos canónicos, formatos de comunicación y protocolos de integración entre el Bot de WhatsApp (Twilio), el Dashboard Next.js, el Servidor FastAPI, el Motor de Detección (6 detectives) y la Persistencia en Supabase.

---

## 2. Entrada Normalizada al Motor de Análisis (`IncomingPayload`)

El servidor normaliza cualquier entrada (texto, imagen, audio o consulta directa) antes de invocar al motor de análisis:

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Literal

class IncomingPayload(BaseModel):
    channel: Literal["whatsapp", "telegram", "dashboard_box", "api"] = Field(..., description="Canal de origen")
    content_type: Literal["text", "image", "audio", "phone_number", "payment_key", "purchase_offer"] = Field(...)
    raw_text: Optional[str] = Field(None, description="Texto del mensaje, SMS o descripción")
    media_url: Optional[str] = Field(None, description="URL temporal del medio en Twilio para OCR o audio")
    phone_sender_hash: str = Field(..., description="HMAC-SHA256 del remitente para anonimización y rate limiting")
    user_registered_phone_enc: Optional[str] = Field(None, description="Teléfono cifrado con AES-256 solo si requiere repuesta directa")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadatos auxiliares de transporte")
```

*Regla de Privacidad:* Jamás incluir tokens de sesión, credenciales o nombres completos sin anonimizar en `metadata`.

---

## 3. Contrato de la Revisión 4: Salida Estructurada del Psicólogo (LLM)

El LLM que ejecuta la Revisión 4 está blindado contra manipulación y obligado a responder exclusivamente bajo el siguiente esquema JSON validado con Pydantic:

```json
{
  "canal": "sms | whatsapp | llamada | compra",
  "modalidad": "suplantacion_bancaria | falso_familiar | falso_asesor | falsa_compra_anticipo | paquete_retenido | falso_funcionario | otro",
  "entidad_suplantada": "Nombre de la entidad identificada o 'Ninguna'",
  "tacticas": ["urgencia", "amenaza", "pide_datos", "falso_premio", "secreto", "cambio_plataforma"],
  "pide": "Descripción precisa de qué exige el atacante (datos, transferencias, códigos OTP)",
  "instrucciones_ocultas": false,
  "explicacion": "Resumen claro y pedagógico en lenguaje humano del truco psicológico detectado"
}
```

*Regla de Seguridad:* Si `instrucciones_ocultas` es `true` (detección de prompt injection), el motor suma automáticamente +20 puntos de riesgo al Juez.

---

## 4. Resultado Normalizado del Análisis (`AnalysisResult`)

Este es el contrato que devuelve el Cerebro y consumen WhatsApp, Telegram y el Dashboard:

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
    "¿Deseas preparar tu kit de denuncia? Responde 1."
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

## 5. Contratos de Verificación con la Fuente

### A. Llamada Verificada (`/api/v1/llamadas`)
- **Registro previo de la Entidad (Saliente):**
  - `POST /api/v1/llamadas/registrar`
  - *Headers:* `X-Entity-API-Key: sec_live_...`
  - *Body:* `{"telefono_cliente": "+573100000000", "motivo": "Confirmar una compra", "asesor": "Laura M."}`
  - *Respuesta:* `{"success": true, "codigo_verificacion": "4821", "expires_in_seconds": 900, "registro_id": "uuid"}`
- **Consulta del Usuario (Entrante por WhatsApp):**
  - `POST /api/v1/llamadas/consultar`
  - *Body:* `{"telefono_cliente_hash": "hmac_...", "entidad_consultada": "BancoAndino"}`
  - *Respuesta:*
    - Si existe registro válido (<15 min): `{"is_verified": true, "entidad": "BancoAndino", "motivo": "Confirmar una compra", "codigo_esperado": "4821"}`
    - Si no existe registro: `{"is_verified": false, "entidad": "BancoAndino", "advertencia": "NO ES TU BANCO. Cuelga de inmediato.", "accion": "reportar_numero"}`

### B. Círculo de Confianza (`/api/v1/circulo`)
- **Doble Consentimiento (Vinculación):**
  - `POST /api/v1/circulo/invitar`: Protegido envía número de familiar -> Bot envía invitación -> Familiar responde "SÍ" -> Estado `activo`.
- **Interrogación al Familiar Real:**
  - `POST /api/v1/circulo/verificar-familiar`
  - *Disparador:* El Psicólogo detecta `modalidad: falso_familiar` y el número no coincide con el guardado.
  - *Mensaje al Familiar:* *"Tu mamá recibió un mensaje de un número nuevo diciendo ser tú y pidiendo $800.000. ¿Fuiste tú? Responde SÍ o NO."*
  - *Timeout:* 5 minutos. Si no responde: *"No pudimos confirmar con tu familiar. No transfieras."*
  - *Alerta en Cadena:* Si el familiar responde NO, se envía broadcast automático a todos los miembros del círculo bloqueando el número atacante.

---

## 6. Contrato del Banco de Números y Compras (`/api/v1/banco`)
- **Consulta de Nivel de Riesgo (0–100):**
  - `GET /api/v1/banco/consultar?tipo=telefono|llave_breb|cuenta&valor=...`
  - *Respuesta:*
    ```json
    {
      "valor_visible": "+57 601 000 ****00",
      "nivel_riesgo": 90,
      "semaforo": "ALTO RIESGO",
      "personas_distintas_30d": 29,
      "total_reportes": 37,
      "modalidad_predominante": "Falso asesor del banco",
      "en_campana_activa": true,
      "is_oficial": false,
      "estado": "activo | en_revision | lista_blanca"
    }
    ```
- **Antes de Pagar (Confirmador de Compras):**
  - `POST /api/v1/compras/verificar-oferta`
  - *Body:* `{"vendedor_telefono": "...", "llave_pago": "...", "oferta_captura_url": "...", "precio_declarado": 900000}`
  - *Respuesta:* Semáforo cruzado (reputación de llave en Banco de Números + análisis de urgencia/anticipo en la oferta por la IA).

---

## 7. Semántica Obligatoria del Semáforo
- **● BAJO RIESGO (0 a 39 puntos · Verde):** No se observan indicadores maliciosos. Recordatorio permanente: *"Ninguna entidad oficial te pedirá contraseñas ni códigos OTP por mensaje o llamada"*.
- **● SOSPECHOSO (40 a 69 puntos · Amarillo):** Señales atípicas o ambigüedad en el remitente/oferta. Acción requerida: comprobar por canal alterno oficial antes de operar.
- **● ALTO RIESGO (70 a 100 puntos · Rojo):** Evidencia concreta de fraude, phishing, vishing o suplantación. Instrucción imperativa de bloqueo, no apertura y preservación de evidencia.
