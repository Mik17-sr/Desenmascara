# Agente 2 — Motor de Detección, Reglas e IA (El Cerebro)

**Responsable Líder:** Luis Guillermo Nieto Patiño  
**Tecnologías:** Python 3.12 · LLMs Multimodales (Claude / GPT-4o / Gemini) · OpenAI Whisper · pgvector · Pydantic v2  
**Misión:** Construir el Cerebro de 6 revisiones que analiza mensajes reenviados, capturas, notas de voz y números desde Telegram en menos de 8 segundos, combinando inteligencia artificial con reglas deterministas inmutables.

---

## 1. Los 6 Detectives del Cerebro

```
[Mensaje / Captura / Audio desde Telegram]
                    │
                    ▼
[1. El Traductor] ────► OCR Visión (capturas) + Whisper (audios OGG de Telegram)
                    │
                    ▼
[2. El de las Pistas] ──► Extractor Regex: URLs, teléfonos, llaves Bre-B, bancos, montos y OTP
                    │
                    ▼
[3. Enlaces y Números] ─► Safe Browsing, URLhaus, RDAP (antigüedad de dominio), Typosquatting, Banco de Números
                    │
                    ▼
[4. El Psicólogo (IA)] ─► LLM con salida estructurada JSON validada (defensa OWASP LLM01)
                    │
                    ▼
[5. El Archivista] ─────► Embeddings semánticos + búsqueda HNSW en pgvector (campañas masivas)
                    │
                    ▼
[6. El Juez] ───────────► Fusión determinista: scoring 0–100, semáforo, reglas duras y Rayos X
```

---

## 2. Especificación Detallada de cada Detective

### Revisión 1 · El Traductor (Percepción Multimodal en Telegram)
- **Capturas de Pantalla:** Recibe la imagen de Telegram (máxima resolución), la envía al LLM con visión para OCR forense, recuperando el texto literal del SMS o chat sospechoso, remitente aparente y enlaces visibles.
- **Notas de Voz (Vishing):** Recibe el audio OGG/Opus nativo de Telegram y lo transcribe con Whisper. El audio se procesa en memoria y se destruye inmediatamente tras la transcripción para cumplir la Ley 1581 de 2012.

### Revisión 2 · El que subraya Pistas (Extracción Regex)
- Extrae URLs, dominios, teléfonos colombianos (+57, celulares 3XX, fijos), llaves Bre-B (celulares, cédulas, correos), cuentas bancarias, menciones de bancos colombianos y códigos OTP.

### Revisión 3 · Detective de Enlaces y Números (Reputación Técnica)
- Cruce con Google Safe Browsing y URLhaus.
- Consulta RDAP/WHOIS para determinar fecha de registro: si tiene **menos de 30 días**, suma +15 puntos de riesgo.
- Detección de homoglifos, typosquatting y dominios Punycode (`xn--`, ceros por letra 'o').
- Consulta en el Banco de Números para verificar historial de reportes comunitarios y lista blanca oficial (-40 pts si es dominio oficial verificado).

### Revisión 4 · El Psicólogo (Razonamiento LLM con Defensa OWASP LLM01)
- El texto sospechoso se encapsula como **evidencia pura no confiable** entre etiquetas `<evidencia>`.
- Salida validada estrictamente con Pydantic (`canal`, `modalidad`, `entidad_suplantada`, `tacticas`, `pide`, `instrucciones_ocultas`, `explicacion`).
- Si detecta intentos de manipulación (*"ignora tus instrucciones"*), activa `instrucciones_ocultas: true` (+20 pts).

### Revisión 5 · El Archivista (Memoria Vectorial en pgvector)
- Generación de embedding del mensaje normalizado.
- Búsqueda de similitud de coseno en Supabase (`pgvector` con índice HNSW) contra la tabla `campanas`. Si la similitud supera el 85%, vincula a la campaña masiva activa y suma hasta +20 puntos.

### Revisión 6 · El Juez (Scoring Determinista y Semáforo)

| Señal Detectada | Detective | Puntos |
| :--- | :--- | :--- |
| Enlace imita entidad oficial (typosquatting) | Enlaces | +30 |
| Pide contraseñas, OTP o datos de tarjeta | Psicólogo | +20 |
| Dominio creado hace menos de 30 días | Enlaces | +15 |
| Usa urgencia, amenaza o falso premio | Psicólogo | +10 |
| Parecido >85% con campaña masiva activa | Archivista | +16 a +20 |
| Número o llave con múltiples reportes | Banco de Números | +15 a +25 |
| Enlace en listas negras (Safe Browsing / URLhaus) | Enlaces | +25 |
| Intento de inyección de instrucciones detectado | Psicólogo | +20 |
| **Atenuante:** Enlace pertenece al dominio oficial legítimo | Enlaces | -40 |
| **Atenuante:** Mensaje informativo sin enlaces ni pedidos | Psicólogo | -15 |

#### Reglas Duras Inmutables del Juez
1. **Suplantación + Datos:** Si imita a un banco y pide datos o claves, el puntaje es **mínimo 85 (ALTO RIESGO)**.
2. **Vishing Crítico:** Si en una llamada piden el código SMS recibido o instalar una app remota, el puntaje es **mínimo 85**.
3. **Llamada Verificada Falsa:** Si consulta por una entidad registrada y no hay llamada activa, el veredicto es **ALTO RIESGO (100)**: *"NO ES TU BANCO: Cuelga ya"*.
4. **Remitente Oficial:** Si está verificado en lista blanca y no contiene URLs externas, el puntaje es **máximo 39 (Verde)**.

---

## 3. Módulo de Llamadas y Compras
- **Vishing:** Pondera solicitud de código SMS (+35), claves (+30), apps remotas (+30) y regla de oro: *"Cuelga y llama tú a la línea oficial en tu tarjeta"*.
- **Antes de Pagar:** Pondera precio irrealmente bajo, solicitud de anticipo, apuro ("hay 3 interesados") y cruce de la llave Bre-B con el Banco de Números.
