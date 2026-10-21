# Agente 6 — QA, Pruebas, Dataset y Evaluación de Calidad

**Responsable Líder:** IngBocadillo  
**Misión:** Validar el sistema de punta a punta en Telegram (`@DesenmascaraBot`), coordinar el dataset oficial de prueba (140 casos), medir métricas científicas de rendimiento y dirigir los ensayos del Demo Day.

---

## 1. El Dataset Oficial de Evaluación (140 Casos Reales)

| Categoría | Volumen | Propósito Evaluativo |
| :--- | :--- | :--- |
| **Mensajes Fraudulentos (Estafas)** | 50 casos | Smishing bancario, paquetes retenidos, falsos premios. Mide la **Sensibilidad (Recall)**. |
| **Mensajes Legítimos** | 50 casos | Notificaciones bancarias reales, compras verificadas. Mide los **Falsos Positivos**. |
| **Llamadas Fraudulentas (Vishing)** | 20 casos | Transcripciones y notas de voz de falsos asesores bancarios y compras no reconocidas. |
| **Ofertas de Compraventa Inseguras** | 20 casos | Publicaciones fraudulentas en redes con llaves Bre-B reportadas y solicitud de anticipos. |

---

## 2. Métricas de Rendimiento Exigidas
- **Sensibilidad (Recall) en Fraudes:** $\ge 95\%$
- **Tasa de Falsos Positivos:** $\le 5\%$
- **Latencia de Respuesta en Telegram:** $< 8$ segundos en el P90.
- **Acceso Inmediato en Demo Day:** Código QR que abre directamente `@DesenmascaraBot` en Telegram sin pasos previos.

---

## 3. Ensayo de las 3 Escenas del Demo Day en Telegram (Guion de 5 Minutos)

1. **Escena 1 · Llamada Verificada (Minuto 1:10 a 2:10):**
   - Gerhard llama a IngBocadillo simulando ser asesor de BancoAndino.
   - IngBocadillo abre `@DesenmascaraBot` en Telegram y pulsa *"¿Me están llamando de verdad?"*.
   - El bot responde: **● NO ES TU BANCO: Cuelga ya**. Ella cuelga en vivo frente al jurado.
   - Miguel (como BancoAndino) registra una llamada legítima en el Panel de la Entidad en pantalla gigante.
   - Gerhard vuelve a llamar. IngBocadillo consulta en el bot. El bot responde: **● SÍ, ES REAL**, motivo "Confirmar compra", código `4821`. Gerhard confirma el código `4821`. Validación exitosa.
2. **Escena 2 · Círculo de Confianza (Minuto 2:10 a 2:50):**
   - IngBocadillo (como mamá) recibe mensaje en Telegram: *"Mamá, se dañó mi celular, mándame $800.000 urgente"*.
   - Lo reenvía a `@DesenmascaraBot`. El bot detecta que dice ser Juan y consulta al Juan real (Luis) en su chat de Telegram.
   - Luis recibe el mensaje interactivo y pulsa el botón: **[NO]**.
   - IngBocadillo recibe en segundos: **● ES UNA ESTAFA. Juan confirmó que no fue él.**
3. **Escena 3 · Antes de Pagar (Minuto 2:50 a 3:30):**
   - IngBocadillo reenvía una oferta de compraventa con solicitud de anticipo a una llave Bre-B.
   - El bot responde **● ALTO RIESGO · 91/100**: la llave tiene 12 reportes en el Banco de Números.
   - En el proyector, el Dashboard de Gerhard se actualiza en tiempo real mostrando los Rayos X del puntaje.
