# Agente 6 — QA, Pruebas, Dataset y Evaluación de Calidad

**Responsable Líder:** IngBocadillo  
**Misión:** Validar el sistema de punta a punta, coordinar el dataset oficial de prueba (140 casos), medir métricas científicas de rendimiento (precisión, sensibilidad y latencia) y dirigir los ensayos del Demo Day.

---

## 1. El Dataset Oficial de Evaluación (140 Casos Reales)

El dataset está estructurado en una hoja de control con casos obtenidos de alertas bancarias reales, reportes de Policía Nacional y experiencias del equipo:

| Categoría | Volumen | Propósito Evaluativo |
| :--- | :--- | :--- |
| **Mensajes Fraudulentos (Estafas)** | 50 casos | Smishing bancario, paquetes retenidos, falsos premios, falsas alertas de seguridad. Mide la **Sensibilidad (Recall)**. |
| **Mensajes Legítimos** | 50 casos | Notificaciones bancarias reales, confirmaciones de encomiendas, OTPs solicitados por el usuario. Mide los **Falsos Positivos**. |
| **Llamadas Fraudulentas (Vishing)** | 20 casos | Transcripciones y audios de falsos asesores bancarios, compras no reconocidas, llamadas de falsos funcionarios. |
| **Ofertas de Compraventa Inseguras** | 20 casos | Publicaciones fraudulentas en redes sociales con solicitud de anticipos y llaves Bre-B reportadas. |

---

## 2. Métricas de Rendimiento Exigidas para el Pitch
- **Sensibilidad (Recall) en Fraudes:** $\ge 95\%$ (detectar prácticamente todas las estafas).
- **Tasa de Falsos Positivos:** $\le 5\%$ (no alarmar indebidamente ante mensajes de bancos legítimos).
- **Latencia de Respuesta:** $< 8$ segundos en el 90% de las consultas (P90).
- **Disponibilidad de la Demo:** 100% de éxito en los 3 flujos clave durante el Demo Day.

---

## 3. Plan de Pruebas Automatizadas (`pytest`)

```
tests/
  ├── test_api_webhook.py          # Validación de firma Twilio y formato de entrada
  ├── test_cerebro_detectives.py    # Pruebas unitarias para cada uno de los 6 detectives
  ├── test_hard_rules.py            # Verificación de que las Reglas Duras del Juez se cumplan
  ├── test_llamada_verificada.py   # Flujo completo registrar -> consultar (SÍ y NO)
  ├── test_circulo_confianza.py     # Flujo familiar: consulta, respuesta y alerta en cadena
  ├── test_banco_numeros.py         # Algoritmo de scoring 0-100 y deduplicación de reportes
  ├── test_seguridad_inyeccion.py   # Ataques de inyección de prompts y URLs maliciosas
  └── test_dataset_evaluation.py    # Evaluación batch del dataset de 140 casos
```

---

## 4. Ensayo de las 3 Escenas del Demo Day (Guion de 5 Minutos)

IngBocadillo coordina la sincronización de los 4 integrantes en escena:

1. **Escena 1 · Llamada Verificada (Minuto 1:10 a 2:10):**
   - *Paso 1:* Gerhard llama a IngBocadillo simulando ser asesor de BancoAndino.
   - *Paso 2:* IngBocadillo consulta al bot por WhatsApp: *"¿BancoAndino me está llamando?"*.
   - *Paso 3:* El bot responde: **● NO ES TU BANCO: Cuelga ya**. Ella cuelga en vivo.
   - *Paso 4:* Miguel (como BancoAndino) registra una llamada legítima en el Panel de la Entidad en pantalla gigante.
   - *Paso 5:* Gerhard llama de nuevo. IngBocadillo consulta al bot. El bot responde: **● SÍ, ES REAL**, motivo "Confirmar compra", código `4821`. Gerhard dice `4821`. Validación confirmada.
2. **Escena 2 · Círculo de Confianza (Minuto 2:10 a 2:50):**
   - IngBocadillo (como mamá) recibe mensaje de número desconocido: *"Mamá, se dañó mi celular, mándame $800.000 urgente"*.
   - Lo reenvía al bot. El bot detecta que dice ser Juan y consulta al Juan real (Luis) a su número registrado.
   - Luis recibe el mensaje en su celular en vivo y responde: **NO**.
   - IngBocadillo recibe en segundos: **● ES UNA ESTAFA. Juan confirmó que no fue él.**
3. **Escena 3 · Antes de Pagar (Minuto 2:50 a 3:30):**
   - IngBocadillo muestra una oferta de un celular de alta gama a mitad de precio donde piden pagar un anticipo a una llave Bre-B.
   - Reenvía la oferta y la llave al bot. El bot responde **● ALTO RIESGO · 91/100**: la llave tiene 12 reportes en el Banco de Números.
   - En el proyector, el Dashboard de Gerhard se actualiza en tiempo real mostrando los Rayos X del puntaje.
