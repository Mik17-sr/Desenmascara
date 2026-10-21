# Agente 4 — Persistencia y datos

## Objetivo
Proveer persistencia mínima y auditable para resultados de análisis y feedback, usando la tecnología ya elegida en el repositorio.

## Límites
- No cambiar rutas de API ni lógica del motor.
- No agregar un sistema de base de datos nuevo si ya existe uno operativo.
- No almacenar contenido personal completo por defecto.
- Coordinar modelos y métodos del repositorio con Backend antes de cerrar el contrato.

## Modelo mínimo orientativo
### `analysis`
- `id`
- `created_at`
- `source` (por ejemplo, telegram)
- `user_ref` seudonimizado o nulo
- `content_type` (text/link)
- `risk_level`
- `risk_score`
- `summary` o resumen limitado
- `signals` estructuradas
- `analysis_version`
- `limitations`
- `processing_ms` si puede medirse

### `feedback`
- `id`
- `analysis_id`
- `feedback_type` (useful / false_positive / incorrect / other)
- `created_at`
- comentario opcional con longitud limitada y sin pedir datos sensibles

Adaptar nombres y tipos al estilo del proyecto. No persistir secretos, tokens, contraseñas, OTP ni el mensaje completo sin una justificación clara y política de retención.

## Tareas P0
- Modelo/tabla para resultados.
- Migración o mecanismo de inicialización coherente con el proyecto.
- Repositorio con operaciones para crear y consultar el resultado.
- Manejo explícito de errores de persistencia.
- Índices mínimos por fecha y nivel de riesgo si la DB lo requiere.

## Tareas P1
- Guardar feedback.
- Consultas agregadas para métricas sin exponer mensajes individuales.
- Política de retención configurable o documentada.

## Validación
- Crear y recuperar análisis.
- Guardar arrays/JSON correctamente.
- Rechazar o tratar correctamente referencias inválidas.
- Verificar migración en una base limpia o documentar si solo se probó en una DB existente.
- No declarar éxito si la DB no estaba disponible.

## Entrega
Documentar cambios de esquema, migraciones, comandos de ejecución, política de retención y limitaciones. No modificar datos reales ni ejecutar migraciones destructivas.
