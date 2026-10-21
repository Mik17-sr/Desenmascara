# Agente 3 — Interfaz Conversacional: Bot de Telegram

**Responsable Líder:** Gerhard Arce  
**Canal Oficial:** Telegram Bot API (`@DesenmascaraBot`)  
**Filosofía:** *En un bot, la conversación es el diseño. La interfaz no son pantallas; son las palabras, el orden, los botones y la empatía del chat.*

---

## 1. Misión del Agente Conversacional
Diseñar e implementar la experiencia de usuario completa en Telegram. Garantizar que cualquier ciudadano, adulto mayor o jurado del evento pueda interactuar en segundos, recibir veredictos pedagógicos y acceder sin fricción a las tres capas de protección (Llamada Verificada, Círculo de Confianza, Banco de Números y Antes de Pagar).

---

## 2. El Menú Principal en Telegram (6 Opciones Interactivas)

Al pulsar `/start` o escribir cualquier saludo, el bot responde con un teclado interactivo (`ReplyKeyboardMarkup` o `InlineKeyboardMarkup`):

```text
Hola, soy Desenmascara.
Solo leo lo que tú decidas enviarme.

¿Qué quieres revisar hoy?
1. 🔍 Un mensaje o una captura
2. 📞 ¿Me están llamando de verdad?
3. 📱 Un número o una llamada
4. 🛡️ Mi Círculo de Confianza
5. 🛒 Antes de pagar una compra
6. 🚨 Ya caí o quiero denunciar
```

### Enrutamiento Inteligente sin Menú (Zero-Click Routing)
Si el usuario no toca el menú sino que simplemente:
- Reenvía un mensaje sospechoso desde cualquier chat o canal.
- Pega un enlace sospechoso.
- Envía una foto o captura de pantalla.
- Envía una nota de voz relatando una llamada recibida.
- Pega un número telefónico o llave Bre-B.
El bot **detecta el tipo de contenido automáticamente** e inicia el análisis en segundos.

---

## 3. Reglas de Redacción Conversacional
1. **El Semáforo en la Primera Línea:** Inicia con icono y veredicto visible:
   - `● ALTO RIESGO · 96/100 · Suplantación bancaria (smishing)`
   - `● SOSPECHOSO · 55/100 · Posible falso familiar`
   - `● BAJO RIESGO · 12/100 · No encontramos señales de estafa`
2. **Concisión (8 a 10 Líneas):** En pantallas móviles, los párrafos densos no se leen. Las razones se entregan en viñetas cortas.
3. **Cero Jerga Técnica:** En lugar de "spoofing" o "phishing", explicar: *"El enlace imita al banco y el dominio fue creado hace 2 días"*.
4. **Instrucción de Acción Siempre:** Terminar con qué hacer: *"Qué hacer: no abras el enlace. Si ya ingresaste datos, llama ya al reverso de tu tarjeta."*
5. **Jamás Solicitar Datos Privados:** El bot nunca pide contraseñas, cédulas ni códigos OTP.

---

## 4. Flujos Conversacionales Clave

### Flujo 1 · Llamada Verificada (Opción 2)
1. Usuario pulsa "📞 ¿Me están llamando de verdad?" o pregunta *"¿BancoAndino me está llamando?"*.
2. Telegram permite compartir el contacto de forma autenticada con un botón: `[📱 Compartir mi número para verificar]`.
3. **Caso SÍ (Llamada Real Registrada):**
   ```text
   ● SÍ, ES REAL
   BancoAndino te está llamando.
   Motivo: confirmar una compra.
   Pídele a la asesora que te diga este código:
   
   4 8 2 1
   
   Si no lo sabe, cuelga de inmediato.
   ```
4. **Caso NO (Llamada Falsa / No Registrada):**
   ```text
   ● NO ES TU BANCO
   BancoAndino no tiene ninguna llamada registrada hacia tu número en este momento.
   
   Qué hacer: cuelga ya. Si necesitas comunicarte con tu banco, llama tú a la línea oficial de tu tarjeta.
   ¿Quieres reportar el número que te llamó? Pégalo aquí.
   ```

### Flujo 2 · Círculo de Confianza (Opción 4)
- **Vinculación:** Usuario agrega a su familiar mediante su usuario de Telegram o contacto. El familiar recibe un mensaje: *"Tu mamá te ha agregado a su Círculo de Confianza. ¿Aceptas protegerla? [Aceptar]"*.
- **Interrogación:** Ante *"Mamá, cambié de número, mándame plata"*:
  - Bot responde a la mamá: *"● SOSPECHOSO. Dice ser Juan. Le estoy preguntando a Juan en su Telegram. Mientras tanto, NO transfieras."*
  - Bot envía botón interactivo a Juan: *"Juan: tu mamá recibió un mensaje diciendo ser tú y pidiendo $800.000. ¿Fuiste tú? [SÍ] [NO]"*.
  - Si Juan pulsa NO: Se confirma la estafa a la mamá y se emite alerta en cadena a toda la familia.
  - El bot recuerda: *"Con IA se puede clonar la voz de un familiar. Acuerden en persona una palabra secreta familiar"*.

### Flujo 3 · Antes de Pagar (Opción 5)
- Usuario envía captura de una oferta en redes, número del vendedor y llave Bre-B.
- Bot responde con evaluación combinada: reputación de la llave en el Banco de Números + análisis de urgencia y precio anormal por la IA.

### Flujo 4 · "Ya Caí" y Kit de Denuncia (Opción 6)
- Despliega pasos de emergencia paso a paso (bloquear tarjetas, cambiar contraseñas desde la app oficial, no dictar códigos).
- Genera un resumen estructurado listo para reenviar a la entidad y al CAI Virtual de la Policía.