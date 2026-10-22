"""Fixed texts of the conversation (guide section 8), already in MarkdownV2."""

from app.bot.formatters import b, esc, join

MENU_OPTIONS = [
    ("1", "Un mensaje o una captura"),
    ("2", "¿Me están llamando de verdad?"),
    ("3", "Un número o una llamada"),
    ("4", "Mi Círculo de Confianza"),
    ("5", "Antes de pagar una compra"),
    ("6", "Ya caí o quiero denunciar"),
]

BIENVENIDA = join(
    f"{esc('Hola, soy')} {b('Desenmascara')}{esc('.')}",
    esc("Solo leo lo que tú me envíes."),
    "",
    b("¿Qué quieres revisar?"),
    esc("Elige una opción o envíame directo el mensaje, la captura, el número o una nota de voz: yo reconozco qué es."),
)

CONSENTIMIENTO = join(
    f"{esc('Hola, soy')} {b('Desenmascara')}{esc(': te ayudo a saber si un mensaje, una llamada o una compra es una estafa.')}",
    "",
    esc("Para ayudarte guardo una copia de lo que revisas, sin nombres, cédulas ni números, y la uso para alertar "
        "a otras personas sobre campañas de estafa (Ley 1581 de 2012). No leo tus chats: solo lo que me envíes."),
    esc("Puedes borrar tus datos cuando quieras con /borrar."),
    "",
    b("¿Aceptas?"),
)

PEDIR_MENSAJE = esc("Reenvíame el mensaje, pégalo aquí o envíame una captura de pantalla.")
PEDIR_ENTIDAD = join(
    b("¿Me están llamando de verdad?"),
    esc("Toca la entidad que dice llamarte, o escribe su nombre. No cuelgues todavía."),
)
PEDIR_TELEFONO = join(
    esc("Para preguntarle a la entidad necesito saber a qué número te están llamando."),
    f"{esc('Toca')} {b('Compartir mi número')}{esc('. Solo lo uso para esta verificación y lo guardo protegido.')}",
)
PEDIR_NUMERO = join(
    b("Revisar un número o una llamada"),
    esc("Pega el número que te llamó o te escribió, o envíame una nota de voz contando lo que te dijeron."),
)
PEDIR_FAMILIAR = join(
    b("Agregar a tu Círculo"),
    esc("Envíame el nombre de tu familiar, como lo llamas tú (por ejemplo: Juan)."),
)
ANTES_DE_PAGAR = join(
    b("Antes de pagar"),
    esc("Envíame la captura de la oferta o pega el texto, junto con el número del vendedor y la llave o cuenta a la que te piden pagar."),
)
COMPRA_SEGURA = join(
    b("Para comprar seguro:"),
    f"{esc('1. Paga')} {b('contraentrega')} {esc('o en persona, en un lugar público.')}",
    f"{esc('2. Usa plataformas con')} {b('protección al comprador')}{esc('.')}",
    f"{esc('3.')} {b('Nunca')} {esc('pagues anticipos a desconocidos.')}",
    esc("4. Desconfía si te piden seguir la conversación por otra app."),
    esc("¿Reportamos al vendedor y la llave? Toca «Reportar»."),
)
YA_CAI = join(
    b("Calma, vamos paso a paso."),
    esc("¿Qué entregaste o qué quieres hacer?"),
)
YA_CAI_TITULOS = {
    "codigo": "Si entregaste una clave o un código",
    "tarjeta": "Si entregaste los datos de tu tarjeta",
    "dinero": "Si enviaste dinero",
    "datos": "Si entregaste datos personales",
}
YA_CAI_PASOS = {
    "codigo": [
        "Llama ya a la línea de tu banco (está al respaldo de tu tarjeta) y pide bloquear.",
        "Cambia tu clave y el código de la app del banco.",
        "No compartas ningún código que te llegue, aunque te insistan.",
        "Revisa los movimientos de hoy y pide reversar los que no reconozcas.",
    ],
    "tarjeta": [
        "Llama ya a tu banco y pide bloquear la tarjeta.",
        "Pide reversar las compras que no reconozcas.",
        "Pide una tarjeta nueva y cambia la clave.",
    ],
    "dinero": [
        "Llama ya a tu banco y pide congelar la transferencia: entre más rápido, mejor.",
        "Guarda capturas del chat, el número y el comprobante.",
        "Denuncia en A Denunciar (adenunciar.policia.gov.co) o en el CAI Virtual (caivirtual.policia.gov.co).",
        "Reporta aquí el número o la llave para proteger a otros.",
    ],
    "datos": [
        "Cambia las claves de tus cuentas y del correo.",
        "Activa la verificación en dos pasos en Telegram y WhatsApp.",
        "Si diste tu cédula o datos de la cuenta, avísale a tu banco.",
        "Desconfía de quien te llame usando esos datos para parecer legítimo.",
    ],
}
LINEAS_DENUNCIA = [
    "La línea de fraudes de tu banco, al respaldo de tu tarjeta, si diste datos o dinero.",
    "A Denunciar, de la Policía Nacional: adenunciar.policia.gov.co",
    "CAI Virtual de la Policía: caivirtual.policia.gov.co",
]
AYUDA = join(
    b("Cómo usarme"),
    esc("• Reenvíame un mensaje, una captura o pega un texto."),
    esc("• Pega un número que te llamó o envíame una nota de voz contando la llamada."),
    esc("• Escribe «¿BancoAndino me está llamando?» para confirmar con la entidad."),
    esc("• /circulo: tu Círculo de Confianza · /kit: kit de denuncia · /revision: si tu número aparece reportado por error · /borrar: borrar tus datos."),
    esc("No abras enlaces por precaución y quita del mensaje los datos personales que no hagan falta."),
)
NO_SOPORTADO = esc("Por ahora reviso mensajes, capturas, números y notas de voz.")
SIN_RESPUESTA_API = esc("No pude conectarme con Desenmascara en este momento. Inténtalo de nuevo en un minuto.")
DEMASIADO_RAPIDO = esc("Vas muy rápido: espera un minuto y vuelve a intentarlo.")
