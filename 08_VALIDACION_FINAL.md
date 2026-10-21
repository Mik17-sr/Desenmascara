# Validación Final e Integración del Sistema

**Proyecto:** Desenmascara v7.0 · Colombia 5.0 Hackathon  
**Canal Certificado:** Telegram Bot API (`@DesenmascaraBot`)  
**Responsable de Aceptación:** IngBocadillo & Miguel (Coordinador)  
**Fecha Límite:** Domingo 18 de octubre de 2026 · 14:00 COT

---

## Checklist de Certificación de Entrega

### A. Bot de Telegram
- [ ] El webhook de Telegram responde en menos de 8 segundos a consultas entrantes.
- [ ] El comando `/start` despliega el teclado con las 6 opciones interactivas.
- [ ] El bot reconoce entradas directas (reenvío de mensajes, fotos, notas de voz o números) sin obligar a navegar el menú.
- [ ] El semáforo siempre aparece en la primera línea con color y palabra: `● ALTO RIESGO`, `● SOSPECHOSO` o `● BAJO RIESGO`.
- [ ] Respuestas concisas (máximo 8 a 10 líneas) sin tecnicismos complejos.
- [ ] Procesamiento de fotos (OCR visión) y notas de voz (Whisper) verificado en Telegram.

### B. Llamada Verificada (Factor Diferencial 1)
- [ ] El Panel de la Entidad permite a "BancoAndino" registrar una llamada saliente (teléfono cliente, motivo, asesor).
- [ ] El sistema genera un código de 4 dígitos con caducidad estricta de 15 minutos.
- [ ] Si un cliente consulta por una entidad sin llamada registrada, el bot responde: **● NO ES TU BANCO: Cuelga ya**.
- [ ] Si existe registro activo, el bot responde **● SÍ, ES REAL**, especifica el motivo y revela el código de seguridad.

### C. Círculo de Confianza (Factor Diferencial 2)
- [ ] Doble consentimiento en Telegram: el familiar debe aceptar la vinculación.
- [ ] Detección del patrón "falso familiar" en mensajes y consulta interactiva con botones al familiar real.
- [ ] Si el familiar responde NO, se alerta a la persona protegida y se emite alerta en cadena al grupo familiar.
- [ ] Recordatorio sobre clonación de voz y palabra clave familiar.

### D. Banco de Números y Antes de Pagar (Factor Diferencial 3)
- [ ] Consulta de teléfonos, llaves Bre-B y cuentas bancarias devuelve nivel de riesgo calculado de 0 a 100.
- [ ] Deduplicación estricta de reportes (1 voto por persona en 30 días).
- [ ] Lista blanca oficial configurada para entidades financieras y tiendas verificadas.
- [ ] Módulo "Antes de Pagar" analiza oferta, detecta precio irreal, exigencia de anticipo y cruza la llave con reportes previos.

### E. Dashboard en Tiempo Real (Next.js)
- [ ] Vista 1 (Radar): Métricas del día, gráfico por hora y alertas rojas de campañas masivas en vivo con Supabase Realtime.
- [ ] Vista 2 (Verificar un Mensaje): Caja interactiva para que el jurado pruebe en la web con desglose de Rayos X.
- [ ] Vista 3 (Banco de Números): Listado de indicadores más reportados, solicitudes de revisión y lista blanca oficial.
- [ ] Vista 4 (Panel de la Entidad): Interfaz de BancoAndino para registro de llamadas con API Key.
- [ ] Código QR generado en el Dashboard para abrir directamente `@DesenmascaraBot` en Telegram.

### F. Seguridad y Privacidad
- [ ] Cabecera `X-Telegram-Bot-Api-Secret-Token` validada obligatoriamente en el webhook.
- [ ] Las notas de voz se eliminan de memoria inmediatamente tras la transcripción de Whisper.
- [ ] Supabase tiene Row Level Security (RLS) habilitado: el Dashboard no tiene acceso a datos personales.
- [ ] Cero secretos en GitHub (`gitleaks` en verde).
- [ ] Resistente a Prompt Injection marcando el caso como alto riesgo (+20 pts).
