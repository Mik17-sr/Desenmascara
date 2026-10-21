# Agente 3 — Interfaz Conversacional: Bot de WhatsApp (P0) y Telegram (Plan B)

**Responsable Líder:** Gerhard Arce  
**Canal Principal:** WhatsApp (Twilio Messaging API / Sandbox)  
**Canal de Respaldo:** Telegram Bot API (Plan B de contingencia para el jurado)  
**Filosofía:** *En un bot, la conversación es el diseño. La interfaz no son pantallas; son las palabras, el orden y la empatía del chat.*

---

## 1. Misión del Agente Conversacional
Diseñar, programar y afinar toda la interacción textual y multimedia del bot de WhatsApp. Garantizar que personas de cualquier edad (incluyendo adultos mayores) comprendan instantáneamente el riesgo, reciban instrucciones operativas claras y puedan acceder a las funciones avanzadas (Llamada Verificada, Círculo de Confianza, Banco de Números y Antes de Pagar).

---

## 2. El Menú Principal de WhatsApp (Las 6 Opciones)

Cuando un usuario escribe "Hola", "Buenas" o inicia conversación, el bot responde con calidez y presenta el menú central:

```text
Hola, soy Desenmascara.
Solo leo lo que tú me envíes.

¿Qué quieres revisar?
1. Un mensaje o una captura
2. ¿Me están llamando de verdad?
3. Un número o una llamada
4. Mi Círculo de Confianza
5. Antes de pagar una compra
6. Ya caí o quiero denunciar
```

### Enrutamiento Inteligente sin Menú (Zero-Click Routing)
Si el usuario no escribe un número del menú sino que reenvía directamente un SMS, pega un enlace, envía una captura de pantalla, una nota de voz o un número telefónico, el bot **detecta automáticamente el tipo de contenido** e inicia el análisis sin obligarlo a pasar por el menú.

---

## 3. Guía de Estilo y Reglas Conversacionales (Sección 8)
1. **El Semáforo en la Primera Línea:** La primera línea del mensaje debe comunicar inequívocamente el estado:
   - `● ALTO RIESGO · 96/100 · Suplantación bancaria (smishing)`
   - `● SOSPECHOSO · 55/100 · Posible oferta engañosa`
   - `● BAJO RIESGO · 12/100 · No encontramos señales de estafa`
2. **Brevedad Estricta (8 a 10 Líneas):** En pantallas pequeñas de celular, mensajes largos abruman y no se leen. Las explicaciones técnicas complejas se resumen en bullets concisos.
3. **Cero Tecnicismos:** No decir "phishing", "dominio malicioso" ni "ataque punycode". Escribir: *"El enlace imita la página del banco y fue creado hace solo 2 días"*.
4. **Instrucción de Acción Inmediata:** Nunca limitarse a diagnosticar; indicar siempre qué hacer:
   - *"Qué hacer: no abras el enlace. Si ya ingresaste datos, llama ahora mismo a tu banco al reverso de tu tarjeta."*
5. **Lenguaje Prudente y No Absoluto:** No decir *"Es 100% estafa"*, sino *"Es muy probable que sea una estafa"* o *"Detectamos señales claras de engaño"*.
6. **Ejemplo Moral:** El bot **jamás** solicita contraseñas, números de cédula ni códigos OTP para verificar.

---

## 4. Flujos Conversacionales Especiales

### Flujo 1 · Llamada Verificada (Opción 2)
1. Usuario escribe "2" o pregunta *"¿BancoAndino me está llamando?"*.
2. El bot consulta a la API de Llamada Verificada con el número de WhatsApp del usuario como llave.
3. **Caso SÍ (Llamada Real):**
   ```text
   ● SÍ, ES REAL
   BancoAndino te está llamando.
   Motivo: confirmar una compra.
   Pídele a la asesora que te diga este código:
   
   4 8 2 1
   
   Si no lo sabe, cuelga.
   ```
4. **Caso NO (Llamada Falsa):**
   ```text
   ● NO ES TU BANCO
   BancoAndino no tiene ninguna llamada registrada hacia tu número en este momento.
   
   Qué hacer: cuelga ya. Si necesitas hablar con tu banco, llama tú a la línea de tu tarjeta.
   ¿Quieres reportar el número? Envíamelo.
   ```

### Flujo 2 · Círculo de Confianza (Opción 4)
- **Vinculación:** *"Mi Círculo de Confianza. Envíame el nombre y el número de tu familiar."* -> Envía mensaje de confirmación al familiar -> Familiar responde SÍ -> Círculo activado.
- **Interrogación:** Ante mensaje de suplantación (*"Mamá cambié de número..."*):
  - Bot responde a la mamá: *"● SOSPECHOSO. Dice ser Juan, que está en tu Círculo. Le estoy preguntando a Juan en su número de siempre. Mientras tanto, no transfieras."*
  - Bot escribe a Juan: *"Juan: tu mamá recibió un mensaje de un número nuevo diciendo ser tú y pidiendo $800.000. ¿Fuiste tú? Responde SÍ o NO."*
  - Juan responde NO -> Bot avisa a mamá: *"● ES UNA ESTAFA. Juan confirmó que NO fue él. No transfieras y bloquea el número."*
  - Alerta en cadena: Difusión a toda la familia con el número del estafador bloqueado preventivamente.

### Flujo 3 · Antes de Pagar (Opción 5)
- Usuario envía captura de publicación en redes, teléfono del vendedor y llave Bre-B/cuenta.
- Bot desglosa:
  ```text
  ● ALTO RIESGO · 91/100
  Posible estafa en compra
  
  Por qué:
  • La llave 315 000 0000 tiene 12 reportes de 11 personas en el Banco de números.
  • Pide anticipo y te apura diciendo que hay otros interesados.
  • El precio está muy por debajo del valor comercial.
  
  Qué hacer: no pagues ningún anticipo. Exige pago contraentrega en lugar público.
  ```

### Flujo 4 · Flujo de Emergencia "Ya Caí" (Opción 6)
- Guía de primeros auxilios financieros:
  1. Llamar a la línea de bloqueos del banco (número oficial proporcionado).
  2. Modificar contraseña y código de acceso desde la app oficial.
  3. No compartir ningún código SMS que llegue.
  4. Generación del Kit de Denuncia con la evidencia lista para radicar en el CAI Virtual de la Policía Nacional.

---

## 5. Implementación del Bot de Telegram (Plan B)
- Mantiene paridad total de comandos: `/start`, `/verificar`, `/banco`, `/llamada`.
- Mismo backend, mismas 6 revisiones del Cerebro.
- Útil como respaldo si la red local del hackathon o el sandbox de Twilio experimentan congestión durante la evaluación del jurado.
