# Agente 1 — Backend y API

## Objetivo
Implementar o completar la capa de API que coordina la entrada, motor de análisis y persistencia, respetando la arquitectura que ya exista.

## Límites
- Responsable de rutas, validación HTTP, configuración y orquestación.
- No implementar reglas antifraude dentro de los endpoints.
- No crear un segundo motor de análisis.
- No hacer llamadas directas a Telegram desde la API.
- No reescribir estructura existente sin justificación.

## Tareas P0
1. Inspeccionar el backend y reutilizar framework, convenciones y dependencias existentes.
2. Exponer un endpoint de análisis equivalente a `POST /api/v1/analyze` (adaptar prefijo a la aplicación actual).
3. Validar longitud máxima de texto, número de enlaces y tipos de entrada.
4. Validar entrada/salida con Pydantic o el mecanismo ya usado.
5. Invocar el motor a través de una interfaz clara.
6. Guardar resultado mediante un repositorio, si está disponible.
7. Manejar errores sin filtrar información interna.
8. Añadir health check sin revelar configuración sensible.

## Tareas P1
- Endpoint para recuperar el historial propio si hay autenticación y el tiempo lo permite.
- Endpoint de feedback para registrar utilidad/falso positivo.
- Métricas internas mínimas sin datos personales innecesarios.

## Requisitos técnicos
- Mantener separación entre router, servicio, DTO y repositorio según el proyecto.
- Configurar CORS solo para orígenes requeridos; no usar comodines con credenciales.
- Configurar timeout para dependencias externas.
- No bloquear el event loop con operaciones lentas; usar el patrón compatible con el stack actual.
- No confiar en `source`, usuario ni campos del cliente como datos autorizados.
- Nunca incluir claves de API en respuestas.

## Pruebas mínimas
- Entrada válida devuelve contrato normalizado.
- Texto vacío o demasiado largo se rechaza claramente.
- Falla del motor no genera un stack trace al cliente.
- Falla de persistencia no debe producir un falso mensaje de éxito.
- Dependencia externa caída se refleja en `limitations` o estado inconcluso.
- Health check responde sin revelar secretos.

## Entrega
Informar rutas, DTOs, servicios, variables de entorno, comandos de prueba y resultado real. No afirmar que el endpoint funciona si no se probó con una petición real o test automatizado.
