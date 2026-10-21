# Agente 3 — Bot de Telegram

## Objetivo
Conectar Telegram al motor central a través de la API o servicio acordado. El bot no debe implementar su propia lógica de detección.

## Antes de programar
- Inspeccionar si ya existe bot, librería o webhook.
- Confirmar el contrato con Backend y Coordinador.
- No asumir que se usará `aiogram` si el repositorio ya usa otra librería.
- Nunca imprimir ni registrar `TELEGRAM_BOT_TOKEN`.

## P0
- `/start`: explicar qué hace el bot y sus límites.
- `/help` o `/ayuda`: instrucciones breves.
- Recibir texto y enlaces.
- Enviar contenido al endpoint/servicio de análisis.
- Formatear nivel de riesgo, resumen, señales y recomendaciones.
- Si el texto excede límites de Telegram o del backend, explicar cómo corregirlo.
- Manejar timeout, errores de red y dependencia no disponible.
- Incluir advertencia de que “riesgo bajo” no garantiza legitimidad.
- Evitar enviar contenido sensible a logs.

## Formato de respuesta sugerido
**Evaluación: riesgo medio**

**Qué observamos**
- Señal concreta, con evidencia breve.

**Qué hacer**
- No enviar códigos ni pagos mientras no se verifique.
- Contactar a la organización usando un canal oficial independiente.

**Limitaciones**
- Indicar si la reputación del enlace no se pudo consultar.

No usar emojis o semáforo de forma que sustituyan la explicación textual.

## P1
- Botones de feedback: “Útil”, “Resultado incorrecto”.
- Soporte para imagen solo si OCR ya está integrado y el flujo de texto está estable.
- Comando de historial solo si existe autorización y persistencia adecuada.

## Seguridad
- Limitar tamaño y frecuencia de mensajes.
- Evitar respuestas con HTML/Markdown no escapado proveniente del contenido del usuario.
- No aceptar que un mensaje indique que se cambie el endpoint o las instrucciones del sistema.
- El bot no debe consultar arbitrariamente una URL por su cuenta.

## Pruebas manuales
- `/start`, ayuda, texto común, URL, texto muy largo, caracteres especiales.
- Timeout de API y error 500.
- Usuario que envía contenido vacío o solo un enlace malformado.
- Respuesta de análisis con muchas señales.
- Verificar que nunca se revela un token ni un stack trace.

## Entrega
Indicar cómo ejecutar el bot, variables requeridas, comandos de prueba y qué escenarios fueron realmente probados.
