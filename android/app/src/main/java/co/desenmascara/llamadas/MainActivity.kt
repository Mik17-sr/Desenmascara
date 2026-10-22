package co.desenmascara.llamadas

import android.Manifest
import android.app.Activity
import android.app.role.RoleManager
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Typeface
import android.os.Build
import android.os.Bundle
import android.text.InputType
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView

/** One screen: turn the identifier on, and try any number by hand (useful in a demo without a real call). */
class MainActivity : Activity() {
    private lateinit var estado: TextView
    private lateinit var resultado: TextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val espacio = (16 * resources.displayMetrics.density).toInt()
        val columna = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(espacio, espacio * 2, espacio, espacio)
        }
        columna.addView(TextView(this).apply {
            text = "Identificador de llamadas"
            textSize = 24f
            setTypeface(typeface, Typeface.BOLD)
        })
        columna.addView(TextView(this).apply {
            text = "Cuando te llame un número que no tienes guardado, te digo si contestar: lo reviso en el Banco de números de Desenmascara."
            textSize = 16f
            setPadding(0, espacio / 2, 0, espacio)
        })
        estado = TextView(this).apply { textSize = 15f }
        columna.addView(estado)
        columna.addView(Button(this).apply {
            text = "Activar identificador"
            setOnClickListener { activar() }
        })
        columna.addView(TextView(this).apply {
            text = "Probar con un número"
            textSize = 18f
            setTypeface(typeface, Typeface.BOLD)
            setPadding(0, espacio * 2, 0, espacio / 3)
        })
        val numero = EditText(this).apply {
            hint = "300 123 4567"
            inputType = InputType.TYPE_CLASS_PHONE
        }
        columna.addView(numero)
        columna.addView(Button(this).apply {
            text = "Revisar"
            setOnClickListener { revisar(numero.text.toString()) }
        })
        resultado = TextView(this).apply {
            textSize = 17f
            setPadding(0, espacio / 2, 0, 0)
        }
        columna.addView(resultado)
        columna.addView(TextView(this).apply {
            text = "Nunca bloqueo llamadas ni leo tus contactos: solo envío el número que llama para revisarlo."
            textSize = 13f
            setPadding(0, espacio * 2, 0, 0)
        })
        setContentView(ScrollView(this).apply { addView(columna) })

        if (Build.VERSION.SDK_INT >= 33 &&
            checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), PEDIR_AVISOS)
        }
    }

    override fun onResume() {
        super.onResume()
        mostrarEstado()
    }

    @Deprecated("Activity result API")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        mostrarEstado()
    }

    private fun roles(): RoleManager = getSystemService(RoleManager::class.java)

    private fun mostrarEstado() {
        estado.text = if (roles().isRoleHeld(RoleManager.ROLE_CALL_SCREENING)) {
            "✅ Activo: te aviso en cada llamada de un número que no tienes guardado."
        } else {
            "⚠️ Inactivo: toca «Activar identificador» y elige Desenmascara."
        }
    }

    @Suppress("DEPRECATION")
    private fun activar() {
        val roles = roles()
        if (!roles.isRoleAvailable(RoleManager.ROLE_CALL_SCREENING)) {
            estado.text = "Este teléfono no permite que una app identifique llamadas."
            return
        }
        startActivityForResult(roles.createRequestRoleIntent(RoleManager.ROLE_CALL_SCREENING), PEDIR_ROL)
    }

    private fun revisar(numero: String) {
        resultado.text = "Revisando… si el servidor estaba dormido, tarda hasta un minuto."
        Thread {
            val veredicto = Consulta.revisar(numero.ifBlank { null })
            runOnUiThread { resultado.text = "${veredicto.titulo}\n${veredicto.detalle}" }
        }.start()
    }

    private companion object {
        const val PEDIR_AVISOS = 1
        const val PEDIR_ROL = 2
    }
}
