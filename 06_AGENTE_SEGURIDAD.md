# Agente 5 — Seguridad, privacidad y revisión de riesgos

## Objetivo
Revisar el PMV y reportar vulnerabilidades prácticas antes de la demostración. No ampliar el alcance; priorizar controles realizables en dos días.

## Riesgos P0
1. **Secretos:** tokens de Telegram y claves de IA solo en variables de entorno; `.env` ignorado por Git; `.env.example` con valores ficticios.
2. **URLs/SSRF:** no hacer fetch a enlaces proporcionados por usuarios en el servidor salvo integración de reputación controlada. Bloquear localhost, redes privadas, IPs literales sospechosas y redirecciones inseguras si hay resolución de URL; preferir proveedores de reputación que reciben el dominio sin visitar la página.
3. **Prompt injection:** el texto del usuario es dato no confiable. El modelo debe recibir instrucciones fijas y no obedecer contenido analizado como instrucciones.
4. **Privacidad:** no guardar mensajes completos ni identificadores directos innecesarios; documentar propósito, acceso y retención.
5. **Abuso:** límite de longitud, rate limiting, timeout y control de tamaño de imagen si existe OCR.
6. **Salida no confiable:** validar JSON del modelo y escapar texto mostrado en Telegram.
7. **Errores:** no exponer stack traces, prompts, variables de entorno ni información de infraestructura.
8. **Falsas acusaciones:** usar lenguaje probabilístico y basado en señales; no publicar números/personas como estafadores sin revisión y evidencia.

## Checklist
- [ ] `.env` ignorado por Git.
- [ ] No hay tokens/claves en el diff ni logs.
- [ ] Longitud de entrada y frecuencia limitadas.
- [ ] Timeout para IA y servicios externos.
- [ ] Excepciones controladas.
- [ ] Resultado del modelo validado por esquema.
- [ ] Enlaces no se abren arbitrariamente.
- [ ] Logs minimizados y sin contenido sensible.
- [ ] Riesgo bajo no se describe como garantía.
- [ ] Datos de prueba sintéticos, no credenciales o mensajes privados reales.

## Pruebas de abuso
- Entrada enorme.
- Prompt injection dentro del mensaje.
- URL hacia `localhost`, `127.0.0.1`, IP privada o metadata endpoint.
- Markdown/HTML malicioso en el texto.
- Proveedor de IA caído o salida malformada.
- Repetición rápida de solicitudes.

No intentes pruebas destructivas contra sistemas externos ni uses datos reales sin autorización.

## Entrega
Reportar hallazgos como P0/P1/P2, evidencia reproducible, archivo/línea cuando se conozca, corrección recomendada y si se reprobó/reprobó después de la corrección. No afirmar que el sistema es “seguro”; reportar el alcance de la revisión.
