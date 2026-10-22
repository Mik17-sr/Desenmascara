package co.desenmascara.llamadas

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context

/** The notice over the incoming call: a high-importance notification, so it shows on top while it rings. */
object Avisos {
    private const val CANAL = "llamadas"

    fun mostrar(contexto: Context, numero: String?, veredicto: Veredicto) {
        val avisos = contexto.getSystemService(NotificationManager::class.java)
        avisos.createNotificationChannel(
            NotificationChannel(CANAL, "Llamadas que entran", NotificationManager.IMPORTANCE_HIGH).apply {
                description = "Te dice si conviene contestar"
            }
        )
        val color = when (veredicto.nivel) {
            Nivel.NO_CONTESTES -> 0xFFD92D20.toInt()
            Nivel.CUIDADO -> 0xFFDC8A00.toInt()
            Nivel.CONTESTA -> 0xFF0E9F8E.toInt()
            Nivel.DESCONOCIDO -> 0xFF667085.toInt()
        }
        val aviso = Notification.Builder(contexto, CANAL)
            .setSmallIcon(R.drawable.ic_notificacion)
            .setColor(color)
            .setContentTitle(veredicto.titulo)
            .setContentText(veredicto.detalle)
            .setStyle(Notification.BigTextStyle().bigText(listOfNotNull(numero, veredicto.detalle).joinToString("\n")))
            .setCategory(Notification.CATEGORY_STATUS)
            .setAutoCancel(true)
            .build()
        avisos.notify((numero ?: "oculto").hashCode(), aviso)
    }
}
