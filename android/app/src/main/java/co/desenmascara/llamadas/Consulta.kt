package co.desenmascara.llamadas

import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.net.URLEncoder

enum class Nivel { CONTESTA, CUIDADO, NO_CONTESTES, DESCONOCIDO }

/** What to do with a number, as the bot says it: the title decides, the detail says why. */
data class Veredicto(val nivel: Nivel, val titulo: String, val detalle: String)

/** Asks Desenmascara's Banco de números about a number. Only the number travels: never who asks. */
object Consulta {
    private const val SIN_CONEXION =
        "No me pude conectar con Desenmascara. Si dice ser tu banco, cuelga y llama tú a la línea de tu tarjeta."

    fun revisar(numero: String?): Veredicto {
        if (numero.isNullOrBlank()) {
            return Veredicto(Nivel.CUIDADO, "🟡 Número oculto",
                "No sé quién llama. Si dice ser tu banco, cuelga y llama tú a la línea de tu tarjeta.")
        }
        return try {
            veredicto(buscar(numero))
        } catch (e: Exception) {
            Veredicto(Nivel.DESCONOCIDO, "⚪ No pude revisar el número", SIN_CONEXION)
        }
    }

    private fun buscar(numero: String): JSONObject {
        val valor = URLEncoder.encode(numero, "UTF-8")
        val conexion = URL("${BuildConfig.API_URL}/banco/consultar?tipo=telefono&valor=$valor").openConnection() as HttpURLConnection
        conexion.connectTimeout = 20_000
        conexion.readTimeout = 60_000 // the free server may be waking up: up to a minute
        try {
            if (conexion.responseCode != 200) throw IllegalStateException("HTTP ${conexion.responseCode}")
            return JSONObject(conexion.inputStream.bufferedReader().use { it.readText() })
        } finally {
            conexion.disconnect()
        }
    }

    fun veredicto(datos: JSONObject): Veredicto {
        val valor = datos.texto("valor") ?: "Este número"
        val oficial = datos.texto("oficial_de")
        val personas = datos.optInt("personas", 0)
        val reportes = datos.optInt("reportes", 0)
        val modalidad = datos.texto("modalidad")?.let { " como «${it.lowercase()}»" } ?: ""
        val cuantos = "${veces(reportes, "reporte", "reportes")} de ${veces(personas, "persona", "personas")}$modalidad."
        return when {
            oficial != null && datos.texto("sitio") != null -> Veredicto(Nivel.CONTESTA, "🟢 Línea oficial de $oficial",
                "Puedes contestar. Ojo: el número en pantalla se puede falsificar; nunca des claves ni códigos.")
            oficial != null -> Veredicto(Nivel.CONTESTA, "🟢 Número oficial de $oficial",
                "Puedes contestar. Nunca des claves ni códigos por teléfono.")
            datos.texto("estado") == "en_revision" -> Veredicto(Nivel.CUIDADO, "🟡 Contesta con cuidado · en revisión",
                "Tiene reportes, pero su dueño pidió revisión.")
            !datos.optBoolean("encontrado", false) || personas == 0 -> Veredicto(Nivel.CUIDADO, "🟡 Contesta con cuidado",
                "Nadie ha reportado este número. Si dice ser tu banco, cuelga y llama tú a la línea de tu tarjeta.")
            datos.optInt("nivel", 0) >= 70 -> Veredicto(Nivel.NO_CONTESTES, "🔴 NO CONTESTES · $valor",
                "$cuantos Si ya contestaste, cuelga: no des claves, códigos ni datos.")
            else -> Veredicto(Nivel.CUIDADO, "🟡 Cuidado · $valor",
                "$cuantos Si contestas, no des claves ni códigos, y no pagues nada por teléfono.")
        }
    }

    private fun JSONObject.texto(clave: String): String? = if (isNull(clave)) null else optString(clave).ifEmpty { null }

    private fun veces(n: Int, uno: String, varios: String) = "$n ${if (n == 1) uno else varios}"
}
