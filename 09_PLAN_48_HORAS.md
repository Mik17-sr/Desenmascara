# Plan de ejecución de 48 horas

## Objetivo
Entregar un PMV demostrable con un flujo completo: Telegram → análisis → respuesta explicada → persistencia mínima.

## Bloque 0 — Primeros 30–45 minutos
- Coordinador inspecciona repositorio, stack y estado de Git.
- Identifica módulos ya existentes.
- Todo el equipo lee el contrato compartido.
- Acuerdan nombres de funciones, DTOs, rutas y dependencias.
- Cada agente confirma qué archivos tocará.

## Día 1 — Flujo vertical
### Bloque 1
- Detección/IA implementa el esquema de resultado y motor básico.
- Backend define la interfaz de invocación y endpoint.
- Datos define persistencia mínima en paralelo, sin tocar rutas.
- Telegram prepara comandos y cliente de API usando el contrato.

### Bloque 2
- Integrar motor y API.
- Ejecutar pruebas unitarias.
- Verificar respuesta real de ejemplo.
- Resolver primero incompatibilidades del contrato.

### Bloque 3
- Conectar Telegram a API.
- Probar `/start`, texto, URL, entrada inválida y errores.
- Guardar al menos un resultado real de prueba.

**Hito del día 1:** un mensaje enviado a Telegram produce una evaluación explicada y el resultado queda persistido, o se registra claramente el bloqueo que impide lograrlo.

## Día 2 — Calidad, seguridad y demo
### Bloque 4
- QA ejecuta casos legítimos, ambiguos y fraudulentos.
- Seguridad revisa secretos, límites, enlaces, logs y prompt injection.
- Corregir únicamente fallos que afectan la demo, seguridad o interpretación del riesgo.

### Bloque 5
- Añadir reputación externa de enlaces si el flujo principal es estable.
- Añadir feedback y métricas básicas si queda tiempo.
- OCR solo si todo lo anterior está completo y probado.

### Bloque 6
- Ensayar los casos de demo.
- Ejecutar pruebas de regresión.
- Revisar `git diff`, README y variables de entorno.
- Completar `08_VALIDACION_FINAL.md`.

## Regla de priorización
P0: Telegram + texto + motor + resultado explicado + persistencia mínima + pruebas + seguridad básica.
P1: reputación externa + feedback + métricas.
P2: OCR de imágenes.
Fuera del alcance de 48 horas: notas de voz, verificación bancaria, WhatsApp en producción, círculos de confianza y dashboard avanzado.

## Reuniones cortas
- Inicio: contratos y propietarios de archivos.
- Mitad del día 1: verificar integración del motor/API.
- Final del día 1: decidir qué se recorta.
- Mitad del día 2: congelar funcionalidades y corregir defectos.
- Cierre: validación final y ensayo de demo.

## Regla de no bloqueo
Los agentes pueden crear stubs o interfaces temporales únicamente si los documentan y no los presentan como implementación final. Si una dependencia externa no se configura, el sistema debe indicar que esa verificación no está disponible.
