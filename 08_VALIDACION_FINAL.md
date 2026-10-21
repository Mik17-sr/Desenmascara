# Validación final e integración — Desenmascara

Este checklist lo ejecuta el coordinador después de integrar a los agentes. No marcar una casilla sin evidencia.

## A. Flujo funcional
- [ ] Bot responde a `/start` y `/help`.
- [ ] Usuario envía texto desde Telegram.
- [ ] El bot llama a la API/servicio acordado.
- [ ] El motor combina reglas y, si está configurada, IA.
- [ ] La respuesta contiene nivel de riesgo, explicación, señales y recomendaciones.
- [ ] El resultado se guarda cuando la persistencia está disponible.
- [ ] La respuesta informa limitaciones si un proveedor no está disponible.
- [ ] El flujo no requiere una interfaz web completa.

## B. Contrato
- [ ] Entrada normalizada coherente en bot y API.
- [ ] Resultado coincide con `01_CONTRATO_COMPARTIDO.md`.
- [ ] Niveles admitidos: `low`, `medium`, `high`, `inconclusive`.
- [ ] Puntaje en rango 0–100 y etiquetado como heurístico.
- [ ] Salida del modelo validada.
- [ ] No existen dos DTOs incompatibles para el mismo resultado.

## C. Calidad
- [ ] Casos legítimos, sospechosos, fraudulentos y ambiguos probados.
- [ ] Se documentaron falsos positivos y falsos negativos observados.
- [ ] Las reglas tienen evidencia asociada.
- [ ] No se afirma “seguro” por ausencia de alertas.
- [ ] No se presenta una sospecha como acusación confirmada.
- [ ] Latencia y coste se midieron o se marcaron como pendientes.

## D. Seguridad
- [ ] Secretos fuera del código y del repositorio.
- [ ] `.env.example` no contiene secretos reales.
- [ ] Entrada y frecuencia limitadas.
- [ ] Timeouts configurados.
- [ ] No se abren enlaces arbitrarios.
- [ ] No se filtran excepciones internas.
- [ ] Datos guardados minimizados y política de retención documentada.
- [ ] Se escaparon caracteres especiales en la respuesta de Telegram.

## E. Operación
- [ ] Instalación reproducible con instrucciones escritas.
- [ ] Variables de entorno documentadas.
- [ ] Backend y bot pueden iniciarse según el README.
- [ ] Health check probado si existe.
- [ ] Dependencias externas opcionales pueden fallar sin derribar el sistema.
- [ ] Git diff revisado y no hay archivos de entorno, dumps o logs privados.

## F. Demo
- [ ] Caso legítimo.
- [ ] Caso con señales de fraude.
- [ ] Caso ambiguo.
- [ ] Caso con enlace no verificado.
- [ ] Mostrar explicación y recomendaciones, no solo el semáforo.
- [ ] Explicar honestamente las limitaciones.
- [ ] Existe plan alternativo si falla la API de IA o la reputación externa.

## Decisión de salida
- **Apto para demo:** flujo principal funciona y no hay fallos críticos conocidos.
- **Apto con limitaciones:** se conocen fallos no críticos, están documentados y no se ocultan al usuario.
- **No apto:** no funciona el flujo completo, se exponen secretos/datos, o se generan afirmaciones de fraude sin respaldo.

## Informe final
| Área | Estado | Evidencia | Riesgo pendiente |
|---|---|---|---|
| Bot Telegram | Pendiente | | |
| API | Pendiente | | |
| Motor de análisis | Pendiente | | |
| Persistencia | Pendiente | | |
| Seguridad | Pendiente | | |
| Pruebas | Pendiente | | |
