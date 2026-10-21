# Validación Final e Integración del Sistema

**Proyecto:** Desenmascara v7.0 · Colombia 5.0 Hackathon  
**Responsable de Aceptación:** IngBocadillo & Miguel (Coordinador)  
**Fecha Límite:** Domingo 18 de octubre de 2026 · 14:00 COT

---

## Checklist de Certificación de Entrega

Este checklist debe ser firmado con evidencia comprobable antes de dar por terminado el proyecto.

### A. Bot de WhatsApp y Canales
- [ ] El webhook de Twilio responde en menos de 8 segundos a consultas entrantes.
- [ ] El menú de bienvenida (6 opciones) se despliega al escribir "Hola".
- [ ] El bot reconoce entradas directas (reenvío de texto, fotos, audios o números) sin requerir navegar el menú.
- [ ] El semáforo siempre aparece en la primera línea con color y palabra: `● ALTO RIESGO`, `● SOSPECHOSO` o `● BAJO RIESGO`.
- [ ] Respuestas concisas (máximo 8 a 10 líneas) sin tecnicismos complejos.
- [ ] Bot de Telegram (Plan B) configurado y funcional con el mismo backend.

### B. Llamada Verificada (Factor Diferencial 1)
- [ ] El Panel de la Entidad permite a "BancoAndino" registrar una llamada saliente (teléfono cliente, motivo, asesor).
- [ ] El sistema genera un código de 4 dígitos de un solo uso con caducidad estricta de 15 minutos.
- [ ] Si un cliente consulta por una entidad sin llamada registrada, el bot responde: **● NO ES TU BANCO: Cuelga ya**.
- [ ] Si existe registro activo, el bot responde **● SÍ, ES REAL**, especifica el motivo y revela el código de seguridad.

### C. Círculo de Confianza (Factor Diferencial 2)
- [ ] Flujo de invitación con doble consentimiento: el familiar debe responder SÍ para quedar registrado.
- [ ] Ante un mensaje que afirma ser un familiar ("Cambié de número"), el Cerebro identifica el patrón y consulta al familiar real en su número registrado.
- [ ] Si el familiar responde NO, el bot alerta a la persona protegida y genera una alerta en cadena al resto del círculo.
- [ ] El sistema advierte sobre clonación de voz con IA y recuerda solicitar la palabra clave acordada en persona.

### D. Banco de Números y Antes de Pagar (Factor Diferencial 3)
- [ ] Consulta de teléfonos, llaves Bre-B y cuentas bancarias devuelve nivel de riesgo calculado de 0 a 100.
- [ ] El algoritmo respeta la regla de que cada persona única suma una sola vez en ventana de 30 días.
- [ ] Lista blanca oficial configurada para entidades financieras y tiendas verificadas.
- [ ] Módulo "Antes de Pagar" analiza oferta, detecta precio anormalmente bajo, exigencia de anticipo y cruza la llave con reportes previos.

### E. Dashboard en Tiempo Real (Next.js)
- [ ] Vista 1 (Radar): Métricas del día (verificaciones, % alto riesgo, llamadas), gráfico de reportes por hora y alertas rojas de campañas masivas en vivo con Supabase Realtime.
- [ ] Vista 2 (Verificar un Mensaje): Caja de prueba interactiva para que el jurado verifique sin unirse al sandbox de Twilio, con desglose de los "Rayos X del puntaje".
- [ ] Vista 3 (Banco de Números): Listado de los indicadores más reportados de la semana, solicitudes de revisión y lista blanca verificada.
- [ ] Vista 4 (Panel de la Entidad): Interfaz privada de BancoAndino para registro de llamadas con API Key.
- [ ] Diseño adaptable a pantallas de computador, tablet y celulares; modo claro y oscuro funcional.

### F. Seguridad y Privacidad
- [ ] Firma de Twilio (`X-Twilio-Signature`) validada obligatoriamente en producción.
- [ ] Las notas de voz se eliminan de memoria inmediatamente después de la transcripción de Whisper.
- [ ] Supabase tiene Row Level Security (RLS) habilitado: el Dashboard no tiene acceso de lectura a datos personales ni llamadas privadas.
- [ ] Cero llaves de API o contraseñas en el repositorio público de GitHub (`gitleaks` en verde).
- [ ] El sistema resiste pruebas de Prompt Injection marcando el caso como alto riesgo (+20 pts).

### G. Entregables del Hackathon
- [ ] Repositorio público en GitHub con código limpio y estructurado.
- [ ] README.md completo con arquitectura, diagramas del sistema y guía de instalación.
- [ ] Video demostrativo de contingencia (2 a 3 minutos) grabado y cargado.
- [ ] Diapositivas del pitch listas con los 4 integrantes ensayados.
