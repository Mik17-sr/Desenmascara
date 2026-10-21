# Desenmascara — Kit de agentes para el PMV

Este paquete coordina el desarrollo acelerado del PMV de **Desenmascara** durante hoy y mañana. El producto inicial es un bot de Telegram que analiza mensajes y enlaces sospechosos, explica señales observables y recomienda acciones seguras.

## Cómo usar estos archivos

1. Entrega `00_COORDINADOR.md` al agente que coordina el trabajo.
2. Entrega cada archivo especializado al agente responsable correspondiente.
3. Todos los agentes deben leer `01_CONTRATO_COMPARTIDO.md` antes de modificar código.
4. Los agentes deben trabajar únicamente dentro de su ámbito asignado y reportar archivos modificados, comandos ejecutados, resultados y bloqueos.
5. El coordinador integra cambios, resuelve conflictos y ejecuta `08_VALIDACION_FINAL.md`.

## Archivos

- `00_COORDINADOR.md`: reparto de trabajo, dependencias, integración y control de cambios.
- `01_CONTRATO_COMPARTIDO.md`: contratos comunes de entrada/salida y límites entre módulos.
- `02_AGENTE_BACKEND.md`: API FastAPI y orquestación del análisis.
- `03_AGENTE_DETECCION_IA.md`: reglas, IA, clasificación y explicación.
- `04_AGENTE_TELEGRAM.md`: bot y adaptación de mensajes al contrato común.
- `05_AGENTE_DATOS.md`: persistencia e historial.
- `06_AGENTE_SEGURIDAD.md`: revisión de riesgos, privacidad y seguridad.
- `07_AGENTE_QA.md`: pruebas, casos de evaluación y regresión.
- `08_VALIDACION_FINAL.md`: checklist de integración, aceptación y demo.
- `09_PLAN_48_HORAS.md`: orden de ejecución por bloques de tiempo.

## Reglas del equipo

- No inventar funcionalidades ya implementadas; inspeccionar primero el repositorio.
- No reemplazar ni reestructurar todo el proyecto si no es necesario.
- No cambiar contratos compartidos sin avisar al coordinador.
- No almacenar secretos en el código ni en archivos versionados.
- No afirmar que un mensaje o una persona es fraudulenta sin pruebas verificables.
- Si una integración externa no puede terminarse a tiempo, encapsularla detrás de una interfaz y devolver un estado explícito de “no disponible/no verificado”.
- Cada agente debe dejar una nota breve de entrega en su respuesta final.
