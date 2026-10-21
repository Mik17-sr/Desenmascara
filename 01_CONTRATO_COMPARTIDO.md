# Contrato compartido entre agentes

## Objetivo
Evitar que los agentes construyan módulos incompatibles. Antes de programar, inspeccionar el repositorio y adaptar estos contratos a su estilo existente sin cambiar su semántica sin avisar al coordinador.

## Entrada normalizada
El motor debe recibir una estructura equivalente a:

```python
{
    "text": "contenido del mensaje",
    "source": "telegram",
    "user_ref": "identificador interno seudonimizado o None",
    "links": ["https://example.com"],
    "metadata": {}
}
```

No guardar el token del bot, credenciales ni datos innecesarios en `metadata`. El identificador del usuario debe minimizarse/seudonimizarse cuando sea posible. El motor no debe depender de Telegram.

## Resultado normalizado
Usar una estructura equivalente a:

```json
{
  "risk_level": "low | medium | high | inconclusive",
  "risk_score": 0,
  "summary": "Explicación breve y prudente",
  "signals": [
    {
      "code": "URGENT_LANGUAGE",
      "label": "Lenguaje de urgencia",
      "evidence": "Fragmento o descripción concreta",
      "source": "rule | reputation | model",
      "confidence": "low | medium | high"
    }
  ],
  "recommendations": [
    "No compartas códigos de verificación",
    "Verifica por un canal oficial independiente"
  ],
  "links": [
    {
      "url": "https://example.com",
      "status": "unchecked | suspicious | flagged | no_known_threat",
      "reason": "Motivo o limitación"
    }
  ],
  "limitations": [],
  "analysis_version": "v1"
}
```

El esquema puede representarse mediante Pydantic. `risk_score` debe ser un entero de 0 a 100. No presentar el puntaje como probabilidad estadística si no está calibrado con datos.

## Semántica obligatoria
- `low`: se detectaron pocas señales; no significa “seguro”.
- `medium`: hay señales que justifican precaución o falta información importante.
- `high`: hay múltiples señales fuertes o una amenaza respaldada por evidencia confiable.
- `inconclusive`: no se pudo evaluar de manera responsable, falló una dependencia o el contenido es insuficiente.

Un dominio sin alertas conocidas no se debe describir como seguro. Una heurística o una respuesta del LLM no constituye confirmación de delito.

## Errores
- Errores de proveedor de IA o reputación deben degradar el resultado de forma explícita.
- No devolver excepciones, stack traces, secretos ni prompts internos al usuario.
- Distinguir entre contenido inválido, límite excedido, dependencia temporalmente no disponible y error interno.
- No ocultar una falla de reputación diciendo que el enlace se verificó.

## Responsabilidades
- Telegram normaliza la entrada y presenta la salida; no calcula el riesgo.
- API valida, coordina motor y persistencia; no contiene prompts grandes ni reglas de negocio extensas.
- Motor analiza y produce el resultado; no llama a Telegram ni escribe directamente en tablas.
- Repositorio de datos guarda/consulta resultados; no clasifica contenido.
- QA verifica el contrato y los casos límite.

## Compatibilidad
Si el proyecto ya tiene un contrato equivalente, reutilizarlo y documentar el mapeo. No crear una segunda versión del mismo DTO. Todo cambio de contrato debe comunicarse al coordinador y reflejarse en pruebas.
