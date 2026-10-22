package co.desenmascara.llamadas

import android.telecom.Call
import android.telecom.CallScreeningService

/**
 * Android asks this service about each incoming call from a number outside the contacts. It never blocks or
 * silences the call: Android wants an answer within 5 seconds and a sleeping server takes longer, so the call
 * rings as always and the notice arrives as soon as Desenmascara answers.
 */
class ScreeningService : CallScreeningService() {
    override fun onScreenCall(callDetails: Call.Details) {
        respondToCall(callDetails, CallResponse.Builder().build())
        if (callDetails.callDirection != Call.Details.DIRECTION_INCOMING) return
        val numero = callDetails.handle?.schemeSpecificPart
        val contexto = applicationContext
        Thread { Avisos.mostrar(contexto, numero, Consulta.revisar(numero)) }.start()
    }
}
