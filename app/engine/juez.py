"""Revisión 6 · El juez: adds the points of every review and decides the semáforo (guide section 12).

No AI here: the same evidence always gives the same score, and every point has a reason that
the bot and the Rayos X can show. Two additions to the guide's table, needed so scams without
a link are not scored as low risk: a recognized modality adds +25, and asking for a code adds
+35 in messages too, as in the call table (section 9).
"""

from dataclasses import dataclass, field

from app.engine.analyzer import Psicologia
from app.engine.enlaces import DomainAge, LinkCheck
from app.engine.pistas import Pistas, plural
from app.schemas.contract import (
    AnalysisResult,
    CampaignMatch,
    LinkAnalysis,
    LinkStatus,
    RiskLevel,
    SignalItem,
    SignalSource,
)

P_IMITA = 30
P_DOMINIO_NUEVO = 15
P_LISTA_NEGRA = 25
P_OFICIAL = -40
P_MODALIDAD = 25
P_PRESION = 10
P_ENTIDAD = 5
P_NO_PIDE = -15
P_INYECCION = 20
P_CAMPANA_MAX = 20
P_BANCO_MAX = 25
P_AVISO_CODIGO = -40
P_DISFRAZADO = 20
P_ACORTADO = 10
P_AMENAZA = 20
P_PAGO_REFERENCIA = 10
P_COBRO = 15
COBRO_DUDOSO = ("amenaza_cobro", "cobro_de_deuda")
VERIFICA_LA_DEUDA = ("Antes de pagar, verifica la deuda con la empresa original por los canales de su página oficial, "
                     "no por los números ni los enlaces del mensaje.")
# Deterministic patterns from Pistas (real cases in datasets/casos_reales.csv) -> modalidad. The ones in
# PATRON_ALTO are specific enough to be high risk on their own; the false relative stays "sospechoso".
PATRON_MODALIDAD = {"falso_familiar": "falso_familiar", "robo_de_cuenta": "robo_de_cuenta", "falsa_multa": "falso_funcionario",
                    "falso_empleo": "falso_empleo", "phishing": "suplantacion_bancaria", "cobro_falso": "cobro_falso",
                    "falsa_compra": "falsa_compra", "falso_premio": "falso_premio", "paquete_retenido": "paquete_retenido",
                    "cuenta_bloqueada": "suplantacion_bancaria"}
PATRON_ALTO = {"robo_de_cuenta", "falsa_multa", "falso_empleo", "phishing", "cobro_falso", "falsa_compra", "falso_premio",
               "paquete_retenido"}
P_PIDE ={"codigo_o_clave": 35, "instalar_app": 30, "mover_dinero": 30, "dinero": 20, "datos_personales": 20, "abrir_enlace": 10}
# The false relative stays "sospechoso" (the guide's case 2): the Círculo confirms it with the real person.
STRONG_MODALIDADES = {"suplantacion_bancaria", "falso_asesor", "falsa_compra", "paquete_retenido", "falso_funcionario",
                      "falso_premio", "falso_empleo"}
HARMFUL_REQUESTS = {"codigo_o_clave", "instalar_app", "mover_dinero", "dinero", "datos_personales"}

PIDE_LABEL = {
    "codigo_o_clave": "Pide un código o una clave: ningún banco los pide por mensaje ni por llamada.",
    "instalar_app": "Pide instalar una aplicación o compartir la pantalla: así toman el control del celular.",
    "mover_dinero": "Pide mover el dinero a una «cuenta segura»: esas cuentas no existen.",
    "dinero": "Pide dinero o un anticipo.",
    "datos_personales": "Pide datos personales o de tu cuenta.",
    "abrir_enlace": "Pide entrar a un enlace.",
}
PIDE_CHIP = {
    "codigo_o_clave": "un código o una clave", "instalar_app": "instalar una app", "mover_dinero": "mover el dinero",
    "dinero": "dinero", "datos_personales": "datos", "abrir_enlace": "abrir un enlace",
}
# modalidad -> (name shown to the person, why it matters, what to do)
MODALIDADES = {
    "suplantacion_bancaria": ("Suplantación de entidad", "Se hace pasar por una entidad para que entregues tus datos.",
                              "No abras el enlace ni compartas claves. Si ya pusiste tus datos, llama a tu banco al número del respaldo de tu tarjeta."),
    "falso_familiar": ("Posible falso familiar", "Dice ser un familiar con número nuevo o en apuros: es el patrón del falso familiar.",
                       "No transfieras. Llama a tu familiar a su número de siempre o hazle una pregunta que solo esa persona sepa responder."),
    "falso_asesor": ("Falso asesor del banco", "Dice ser un asesor o el área de seguridad: los bancos no piden códigos ni claves.",
                     "Cuelga y no dictes ningún código. Llama tú a la línea oficial que está en tu tarjeta."),
    "falsa_compra": ("Posible estafa en compra", "Tiene el patrón de las compras falsas: precio irreal, anticipo o pasar a otra app.",
                     "No pagues anticipos. Paga contraentrega o por una plataforma con protección al comprador."),
    "paquete_retenido": ("Paquete retenido", "Dice que un envío está retenido y que hay que pagar para liberarlo.",
                         "No pagues ni abras el enlace. Revisa el envío solo en la página o la app oficial de la transportadora."),
    "falso_funcionario": ("Falso funcionario", "Dice ser una autoridad y amenaza con multas o procesos.",
                          "No pagues por enlaces ni por teléfono. Las multas y procesos se consultan en los canales oficiales."),
    "falso_premio": ("Falso premio o subsidio", "Ofrece un premio o un subsidio a cambio de datos o pagos.",
                     "No envíes datos ni pagues para reclamar nada: los premios reales no piden pagos ni códigos."),
    "falso_empleo": ("Falso empleo", "Ofrece un trabajo fácil a cambio de pagos o documentos.",
                     "No pagues por un empleo ni envíes documentos a desconocidos."),
    "cobro_falso": ("Posible cobranza falsa",
                    "Cobra una deuda con descuento o amenazas y pide pagar o escribir por un canal que vino en el mismo mensaje.",
                    "No pagues ni escribas por los enlaces, números o referencias del mensaje. Si crees que tienes una deuda, "
                    "búscala tú en la página oficial de la empresa."),
    "robo_de_cuenta": ("Robo de cuenta", "Se hace pasar por el soporte de WhatsApp u otra app para quedarse con tu cuenta.",
                       "No respondas ni compartas códigos: WhatsApp nunca te escribe desde un número común. Activa la verificación en dos pasos."),
    "otra": ("Posible estafa", "Tiene señales típicas de una estafa.", ""),
}
QUE_HACER = {
    RiskLevel.HIGH: "Es muy probable que sea una estafa: no abras, no respondas, no pagues.",
    RiskLevel.MEDIUM: "Verifica por otro canal antes de hacer cualquier cosa. ¿Te pidieron dinero o datos? Cuéntame.",
    RiskLevel.LOW: "Aun así, nunca compartas claves ni códigos, aunque el mensaje sea real.",
}
SUMMARY = {
    RiskLevel.HIGH: "Es muy probable que sea una estafa.",
    RiskLevel.MEDIUM: "Hay señales sospechosas.",
    RiskLevel.LOW: "No encontramos señales de estafa.",
    RiskLevel.INCONCLUSIVE: "No pudimos completar el análisis.",
}
REGLA_DE_ORO_LLAMADAS = "Cuelga y llama tú a la línea oficial que está en tu tarjeta."
QUE_HACER_LLAMADA = "Cuelga y no dictes ningún código ni clave. Si ya lo diste, elige «Ya caí» y llama de inmediato a tu banco."
BASE_LIMITATIONS = [
    "Análisis automático; puede equivocarse.",
    "Los enlaces no se abrieron: solo se revisó su nombre y su registro.",
]


@dataclass
class BancoHit:
    tipo: str  # telefono | llave | cuenta | enlace
    visible: str
    nivel: int
    personas: int
    reportes: int
    modalidad: str | None = None
    estado: str = "normal"
    oficial_de: str | None = None
    sitio: str | None = None  # where a published official line comes from


@dataclass
class CampaignHit:
    id: str
    nombre: str
    similitud: float
    reportes_hoy: int


@dataclass
class Evidencia:
    tipo: str  # mensaje | compra | llamada
    pistas: Pistas
    links: list[LinkCheck] = field(default_factory=list)
    ages: dict[str, DomainAge] = field(default_factory=dict)
    flagged_urls: set[str] = field(default_factory=set)
    psicologia: Psicologia | None = None
    ia_consultada: bool = True
    inyeccion: bool = False
    campana: CampaignHit | None = None
    banco: list[BancoHit] = field(default_factory=list)


def risk_level(score: int) -> RiskLevel:
    if score >= 70:
        return RiskLevel.HIGH
    if score >= 40:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


TIPO_LABEL = {"telefono": "El número", "llave": "La llave", "cuenta": "La cuenta", "enlace": "El enlace"}


def judge(e: Evidencia) -> AnalysisResult:
    signals: list[SignalItem] = []
    recognized: list[str] = []
    links: list[LinkAnalysis] = []
    limitations = list(BASE_LIMITATIONS)

    def add(code: str, label: str, evidence: str, source: SignalSource, points: int) -> None:
        signals.append(SignalItem(code=code, label=label, evidence=evidence, source=source, points=points))

    if e.inyeccion:
        add("INSTRUCCIONES_OCULTAS", "El mensaje intenta darle órdenes al sistema de análisis: es un intento de manipulación.",
            "Frases como «ignora tus instrucciones»", SignalSource.JUEZ, P_INYECCION)

    patron = next((name for name in e.pistas.patrones if name in PATRON_MODALIDAD), None)
    cobro = any(name in e.pistas.patrones for name in COBRO_DUDOSO)
    if patron is None and cobro and e.pistas.canal_del_mensaje:
        patron = "cobro_falso"  # the team's call on real cases: a collection that asks to pay or write through its own link
    imita = None
    for check in e.links:
        recognized.append(f"Enlace: {check.dominio}")
        age = e.ages.get(check.dominio)
        if check.oficial_de:
            if patron:  # scams paste a real link to look trustworthy: it does not clear the rest of the message
                add("ENLACE_OFICIAL", f"El enlace es de {check.oficial_de}, pero el mensaje tiene el patrón de una estafa.",
                    check.dominio, SignalSource.ENLACES, 0)
            else:
                add("ENLACE_OFICIAL", f"El enlace es de la página oficial de {check.oficial_de}.", check.dominio, SignalSource.ENLACES, P_OFICIAL)
            links.append(LinkAnalysis(url=check.url, status=LinkStatus.OFFICIAL, reason=f"Página oficial de {check.oficial_de}"))
            continue
        status, reason = LinkStatus.UNCHECKED, "Sin reportes conocidos"
        if check.imita_a or check.punycode:
            imita = check.imita_a or "una entidad"
            label = (f"El enlace no es la página oficial de {imita}." if not check.punycode
                     else "El enlace usa letras de otros alfabetos para parecerse a otro sitio.")
            add("ENLACE_IMITA_OFICIAL", label, check.dominio, SignalSource.ENLACES, P_IMITA)
            status, reason = LinkStatus.SUSPICIOUS, label
        if age and age.registrado is False:
            add("DOMINIO_NO_REGISTRADO", "El enlace lleva a una página que no aparece registrada.", check.dominio, SignalSource.ENLACES, P_DOMINIO_NUEVO)
            recognized.append("Página sin registro")
            status = LinkStatus.SUSPICIOUS
        elif age and age.dias is not None and age.dias < 30:
            dias = "hoy" if age.dias == 0 else f"hace {age.dias} día{'s' if age.dias != 1 else ''}"
            add("DOMINIO_NUEVO", f"La página del enlace se creó {dias}.", check.dominio, SignalSource.ENLACES, P_DOMINIO_NUEVO)
            recognized.append(f"Página creada {dias}")
            status = LinkStatus.SUSPICIOUS
        if check.url in e.flagged_urls:
            add("ENLACE_LISTA_NEGRA", "El enlace ya está reportado como peligroso.", check.dominio, SignalSource.ENLACES, P_LISTA_NEGRA)
            status, reason = LinkStatus.FLAGGED, "Reportado como peligroso"
        links.append(LinkAnalysis(url=check.url, status=status, reason=reason))
    if e.pistas.enlace_disfrazado:
        add("ENLACE_DISFRAZADO", "El enlace está escrito a propósito para que los filtros no lo detecten.", "", SignalSource.ENLACES, P_DISFRAZADO)
    if e.pistas.acortados:
        add("ENLACE_ACORTADO", "Usa un enlace acortado que esconde a dónde lleva.", e.pistas.acortados[0], SignalSource.ENLACES, P_ACORTADO)

    for name in e.pistas.entidades[:1]:
        add("ENTIDAD_CONOCIDA", f"Dice ser {name}.", name, SignalSource.PISTAS, P_ENTIDAD)
        recognized.append(f"Dice ser: {name}")

    p = e.psicologia
    aviso_de_codigo = e.pistas.aviso_de_codigo
    if aviso_de_codigo:
        add("AVISO_DE_CODIGO", "Es un aviso que te entrega un código y te pide no compartirlo: no te lo está pidiendo.",
            "", SignalSource.PISTAS, P_AVISO_CODIGO)
    # A deterministic pattern names the scam before the AI does: small models mislabel real cases.
    patron_modalidad = PATRON_MODALIDAD.get(patron) if patron else None
    ai_modalidad = p.modalidad if p and p.modalidad in MODALIDADES else None
    if ai_modalidad == "falso_familiar" and not e.pistas.menciona_familia:
        ai_modalidad = None  # small models call any debt or plea a false relative; it needs a relative
    modalidad = patron_modalidad or ai_modalidad
    if modalidad:
        add("MODALIDAD", MODALIDADES[modalidad][1], modalidad, SignalSource.PISTAS if patron_modalidad else SignalSource.PSICOLOGO, P_MODALIDAD)
    # What it asks for: the AI's reading, or the words themselves when there is no AI.
    asked, asked_by = (p.pide, SignalSource.PSICOLOGO) if p else (e.pistas.pide, SignalSource.PISTAS)
    if asked in P_PIDE and not (aviso_de_codigo and asked == "codigo_o_clave"):
        add("PIDE_" + asked.upper(), PIDE_LABEL[asked], asked, asked_by, P_PIDE[asked])
        recognized.append(f"Pide: {PIDE_CHIP[asked]}")
    presion = (p.presion if p else bool(e.pistas.urgencia)) or (bool(e.pistas.urgencia) and bool(e.pistas.patrones))
    if presion:
        add("PRESION", "Usa urgencia, amenazas o premios para que actúes sin pensar.",
            ", ".join(e.pistas.urgencia[:3]) or "urgencia", SignalSource.PSICOLOGO if p else SignalSource.PISTAS, P_PRESION)
        recognized.append("Tácticas: urgencia o presión")
    if "amenaza_cobro" in e.pistas.patrones:
        add("AMENAZA_DE_COBRO", "Amenaza con cobro jurídico, embargo o corte y ofrece descuento por pagar ya: así presionan "
            "las estafas y también los cobros dudosos. Verifica la deuda con la empresa por sus canales oficiales.",
            "", SignalSource.PISTAS, P_AMENAZA)
    if "cobro_de_deuda" in e.pistas.patrones:
        add("COBRO_DE_DEUDA", "Es un cobro de deuda con descuento que llegó sin que lo pidieras: puede ser real o una cobranza falsa.",
            "", SignalSource.PISTAS, P_COBRO)
    if "pago_referencia" in e.pistas.patrones:
        add("PAGO_POR_REFERENCIA", "Pide pagar en un punto de pago con una referencia que llegó por mensaje.", "", SignalSource.PISTAS, P_PAGO_REFERENCIA)
    evidence_of_request = e.pistas.urls or e.pistas.montos or e.pistas.patrones or e.pistas.enlace_disfrazado
    if p and p.pide == "nada" and not evidence_of_request:  # the AI's "asks nothing" never beats a link, an amount or a pattern
        add("NO_PIDE_NADA", "No pide datos, dinero ni clics.", "", SignalSource.PSICOLOGO, P_NO_PIDE)

    if e.campana and e.campana.similitud >= 0.6:
        points = round(P_CAMPANA_MAX * min(1.0, (e.campana.similitud - 0.6) / 0.4))
        pct = round(e.campana.similitud * 100)
        add("CAMPANA_ACTIVA", f"Es muy parecido ({pct} %) a una campaña reportada {plural(e.campana.reportes_hoy, 'vez', 'veces')} hoy.",
            e.campana.nombre, SignalSource.ARCHIVISTA, points)

    banco_alto = False
    for hit in e.banco:
        name = TIPO_LABEL.get(hit.tipo, "El dato")
        recognized.append(f"{name.split()[1].capitalize()}: {hit.visible}")
        if hit.oficial_de:
            add("NUMERO_OFICIAL", f"{name} {hit.visible} es oficial de {hit.oficial_de}.", hit.visible, SignalSource.BANCO, 0)
        elif hit.estado == "en_revision":
            recognized.append(f"{hit.visible}: en revisión")
        elif hit.nivel >= 40:
            points = min(P_BANCO_MAX, round(hit.nivel / 4))
            add("BANCO_REPORTADO", f"{name} {hit.visible} tiene {plural(hit.reportes, 'reporte', 'reportes')} de {plural(hit.personas, 'persona', 'personas')}.",
                hit.modalidad or "", SignalSource.BANCO, points)
            banco_alto = banco_alto or hit.nivel >= 70

    score = max(0, min(100, sum(s.points for s in signals)))
    pide = p.pide if p else e.pistas.pide
    if aviso_de_codigo and pide == "codigo_o_clave":
        pide = "nada"
    if imita and pide in ("datos_personales", "codigo_o_clave", "dinero"):
        score = max(score, 85)  # rule: the link impersonates an entity and the message asks for data
    if e.tipo == "llamada" and pide in ("codigo_o_clave", "instalar_app"):
        score = max(score, 85)  # rule: in a call they asked for a code or to install an app
    if modalidad in STRONG_MODALIDADES and pide in HARMFUL_REQUESTS:
        score = max(score, 75)  # rule: a known scam pattern that asks for money, a code or data
    if e.inyeccion or banco_alto:
        score = max(score, 70)  # rule: hidden orders for the AI, or a number the community marked red
    if e.pistas.pide == "codigo_o_clave" and not aviso_de_codigo:
        score = max(score, 75)  # rule: it asks in words to hand over a code or a password; no entity ever does
    if patron in PATRON_ALTO:
        score = max(score, 75)  # rule: a pattern of real scams: account theft, fake fine, easy-money job, phishing, fake sale
    if patron == "falso_familiar" or modalidad == "falso_familiar":
        # The team's rule: "sospechoso" while it only says "new number" (the Círculo can confirm it), high risk as soon
        # as it asks for money, a transfer or a code.
        asks_money = e.pistas.pide_dinero or (p is not None and p.pide in ("dinero", "mover_dinero", "codigo_o_clave"))
        score = max(score, 75 if asks_money else 45)
    if cobro:
        score = max(score, 40)  # rule: an unrequested collection with threats or discounts is verified before paying
    if aviso_de_codigo and not banco_alto and not e.inyeccion:
        score = min(score, 30)  # rule: a code notice that asks for nothing back is not a scam by itself

    if p is None and e.ia_consultada:
        limitations.append("La revisión con IA no respondió a tiempo; el resultado usa solo las demás revisiones.")
    if p is None and e.ia_consultada and score < 40:
        # Without the AI, weak clues alone (a bank's name, an urgent word) are not enough to say "bajo riesgo".
        level = RiskLevel.INCONCLUSIVE
        score = 0
    else:
        level = risk_level(score)

    category = MODALIDADES[modalidad][0] if modalidad else ("Posible suplantación" if imita else "Cobro por verificar" if cobro else None)
    if category and e.tipo == "llamada":
        category = f"Llamada: {category.lower()}"

    recommendations = []
    if e.tipo == "llamada" and level in (RiskLevel.HIGH, RiskLevel.MEDIUM):
        recommendations.append(QUE_HACER_LLAMADA)  # the guide's case 3; the link advice makes no sense in a call
    elif level in (RiskLevel.HIGH, RiskLevel.MEDIUM) and modalidad and MODALIDADES[modalidad][2]:
        recommendations.append(MODALIDADES[modalidad][2])
    elif level in (RiskLevel.HIGH, RiskLevel.MEDIUM) and cobro:
        recommendations.append(VERIFICA_LA_DEUDA)
    if level in QUE_HACER and not (level == RiskLevel.HIGH and recommendations):
        recommendations.append(QUE_HACER[level])
    if e.tipo == "llamada":
        recommendations.append(REGLA_DE_ORO_LLAMADAS)

    signals.sort(key=lambda s: s.points, reverse=True)
    campaign = None
    if e.campana and e.campana.similitud >= 0.6:
        campaign = CampaignMatch(campaign_id=e.campana.id, name=e.campana.nombre,
                                 similarity_pct=round(e.campana.similitud * 100), total_reports_today=e.campana.reportes_hoy)
    return AnalysisResult(
        risk_level=level,
        risk_score=score,
        summary=SUMMARY[level],
        category=category if level != RiskLevel.LOW else None,
        modalidad=modalidad,
        signals=signals,
        recommendations=recommendations,
        links=links,
        recognized=list(dict.fromkeys(recognized)),
        campaign=campaign,
        limitations=limitations,
    )
