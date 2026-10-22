"""Revisión 2 · El que subraya pistas: links, phones, Bre-B keys, accounts, amounts and codes. No AI."""

import re
import unicodedata
from dataclasses import dataclass, field
from urllib.parse import urlsplit, urlunsplit

from app.core.security import normalize_phone

_TLDS = r"(?:com\.co|gov\.co|org\.co|net\.co|edu\.co|com|co|net|org|info|xyz|site|online|top|app|link|shop|store|club|live|me|io|ly|lat|vip)"
URL_PATTERN = re.compile(
    r"(?i)(?:https?://|\bwww\.)[^\s<>\"']+"  # no \b before "http": OCR glues it to the word before ("WhatsApphttps://")
    rf"|(?<![@\w.-])(?:[a-z0-9](?:[a-z0-9-]{{0,61}}[a-z0-9])?\.)+{_TLDS}\b(?:/[^\s<>\"']*)?"
)
# OCR drops a screenshot's spaces and line breaks: "Info: 601 756 0385 wa.me/" with "+57 304 472 2062" on the next line
# comes out as "Info6017560385wa.me/" and "+573044722062".
GLUED_CHAT_LINK = re.compile(r"(?i)(?<=\d)(?=(?:wa|t)\.me/)")
BROKEN_CHAT_LINK = re.compile(r"(?i)\b((?:wa|t)\.me/)\s+(?=\+?\d)")
PHONE_PATTERN = re.compile(r"(?<![\d$])(?:\+?57[\s.-]?)?(?:3\d{2}|60\d)[\s.-]?\d{3}[\s.-]?\d{4}(?!\d)")
LLAVE_PATTERN = re.compile(
    r"(?i)llave(?:\s*bre-?b)?\s*[:\-]?\s*(@[\w.\-]{3,30}|[\w.+-]+@[\w-]+\.[\w.]+|\d[\d\s]{6,14}\d)"
)
CUENTA_PATTERN = re.compile(
    r"(?i)cuenta(?:\s+(?:de\s+)?(?:ahorros|corriente|nequi|daviplata))?\s*(?:n(?:o|ro|úmero)?\.?\s*|#\s*)?(\d[\d\s-]{7,18}\d)"
)
AMOUNT_PATTERN = re.compile(r"\$\s?\d{1,3}(?:[.,]\d{3})+(?:[.,]\d{2})?|\$\s?\d+")
# 4-8 digits that are not part of an amount such as 45.200 (a final period is fine).
CODE_PATTERN = re.compile(r"(?<![\d$])(?<!\d[.,])\b\d{4,8}\b(?!\d|[.,]\d)")

# Detection only: whether a message claims to come from one of these. Official websites come from
# datasets/dominios_oficiales.csv and the entidades table; official numbers only from the entidades table.
KNOWN_NAMES = [
    "Bancolombia", "Davivienda", "BBVA", "Banco de Bogotá", "Banco Popular", "Banco de Occidente",
    "Banco Caja Social", "Scotiabank Colpatria", "Davibank", "Banco Agrario", "AV Villas", "Itaú", "Nequi",
    "Daviplata", "Banco Falabella", "Lulo Bank", "DIAN", "Policía", "Fiscalía", "Registraduría",
    "Secretaría de Movilidad", "SIMIT", "Servientrega", "Interrapidisimo", "Coordinadora", "Mercado Libre",
]
# "Tu código es 482913. No lo compartas": a notice that hands over a code, which small models
# read as a request for it. Only counts when the message asks for nothing back.
CODE_WARNING = re.compile(r"no\s+(?:lo|la)\s+compartas|no\s+compartas|nunca\s+te\s+(?:lo|la)\s+pedir|si\s+no\s+(?:lo|la)\s+(?:solicitaste|pediste)|si\s+no\s+fuiste\s+tu")
# "489370 es tu código de verificación para U Distrital App": it hands over a code without warning.
CODE_DELIVERY = re.compile(r"\b(?:es\s+tu|es\s+su|tu|su)\s+codigo\b|\bcodigo\s+de\s+(?:verificacion|seguridad|acceso|confirmacion)\b")
ASKS_BACK = re.compile(r"envi|reenvi|dime|digame|dicta|dictame|compart(?:e|eme|ir)\b|respond|escribe|escribeme|manda|llama\s+al|ingresa|entra\s+a")
URGENCY_WORDS = [
    "urgente", "inmediat", "hoy mismo", "solo hoy", "solo por hoy", "ultimo aviso", "bloque", "suspend", "24 horas",
    "48 horas", "embargo", "multa", "decomiso", "cobro juridico", "no le digas", "no le diga", "antes de que",
    "ultima oportunidad", "se eliminara", "pronta respuesta",
]

# Patterns of real Colombian scams (datasets/casos_reales.csv), matched on the text without spaces or
# accents because screenshots often lose the spaces in OCR ("esteesminumeronuevo"). A pattern needs one
# word of each of its groups.
PATRONES = {
    "falso_familiar": (("mama", "mami", "papa", "papi", "abuel", "hijo", "hija", "mamita"),
                       ("numeronuevo", "nuevonumero", "cambiedenumero", "esteesminumero", "otronumeroyano", "semehaestropeado",
                        "semedanoelcelular", "semerobaronelcelular")),
    "robo_de_cuenta": (("soportetecnicodewhatsapp", "soportedewhatsapp", "equipodewhatsapp", "whatsappsupport",
                        "soportedetelegram", "soportedefacebook", "soportedeinstagram"),),
    "falsa_multa": (("sancionvial", "comparendo", "fotomulta", "infractor", "multadetransito"),
                    ("descuento", "descto", "dto", "embargo", "decomiso", "cobrojuridico", "ingresa", "paga", "cancela")),
    # A sale that asks for an advance, or to go on in another app: the guide's fake purchase, without waiting for the AI.
    "falsa_compra": (("vendo", "venta", "remate", "anuncio", "articulo", "producto", "enviogratis"),
                     ("anticipo", "apartar", "apartalo", "apartala", "separar", "separalo", "separala", "abono", "poradelantado",
                      "pagoanticipado", "otraapp", "linkdepago", "pagaprimero")),
    "falso_empleo": (("generadinero", "ganadinero", "ganahasta", "ingresosextra", "trabajodesdecasa", "ganadiario"),),
    "phishing": (("verifyyouraccount", "verifyaccount", "confirmyouridentity", "logintoyouraccount", "updateyourpayment"),
                 ("suspiciousactivity", "beenlocked", "beensuspended", "unauthorized", "unusualactivity")),
    # Not a scam by itself: real collections use them too, so these only add points.
    "amenaza_cobro": (("cobrojuridico", "embargo", "decomiso", "procesojuridico", "instanciadecobro", "centralesderiesgo",
                       "reportenegativo", "reconex", "cortedelservicio", "suspensiondelservicio"),
                      ("descuento", "descto", "dto", "paga", "cancela", "cancele", "aproveche", "evita", "evite", "pagooportuno")),
    "cobro_de_deuda": (("deuda", "obligacion", "mora", "historialcrediticio", "imagencrediticia", "imagencomercial", "datacredito",
                        "saldopendiente", "efecty", "baloto"),
                       ("descuento", "descto", "desct", "dto", "pagasolo", "pazysalvo", "facilidades", "condonacion", "liberarte",
                        "pagooportuno", "rebaja")),
    "pago_referencia": (("efecty", "baloto", "superpagos", "pagatodo", "convenio", "conv1", "conv2", "conv3", "conv4", "conv5",
                         "conv6", "conv7", "conv8", "conv9"),),
}
# Family words: a "false relative" needs one. As whole words ("Hola ma") or inside OCR text without spaces.
FAMILY_WORDS = {"ma", "mami", "mama", "mamita", "pa", "papi", "papa", "papito", "abuela", "abuelo", "abue", "hijo", "hija",
                "tia", "tio", "hermano", "hermana", "primo", "prima", "suegra", "suegro"}
FAMILY_SQUASHED = ("mama", "mami", "papa", "papi", "abuel", "hermano", "hermana")
# Asking for money, as a false relative does once trust is won ("préstame", "mándame plata", "transfiéreme").
MONEY_ASK = ("transfier", "transferen", "consign", "prestame", "presteme", "mandame", "enviame", "necesitoplata",
             "necesitodinero", "plata", "nequi", "daviplata", "llavebreb", "girame", "pagame")
# Link shorteners hide where a link goes.
SHORTENERS = {"bit.ly", "bitly.com", "wa.link", "ma.sv", "tinyurl.com", "cutt.ly", "t.ly", "is.gd", "rebrand.ly",
              "shorturl.at", "acortar.link", "rb.gy", "tiny.cc", "ow.ly", "s.id"}
# Links that open a chat with whoever sent the message, and the words that ask to write or call them.
CHAT_LINKS = {"wa.me", "wa.link", "api.whatsapp.com", "t.me", "telegram.me"}
CONTACT_WORDS = ("whatsapp", "escribenos", "escribanos", "llamanosal", "llamenosal", "contactenos", "contactanos", "llamaya")
# ".col.cuctly.cc/": a domain written with a leading dot so that filters do not turn it into a link.
DISGUISED_LINK = re.compile(r"(?i)(?<![\w/.:@-])\.([a-z0-9-]+(?:\.[a-z0-9-]+)+)/?")


def plain(text: str) -> str:
    """Lowercase without accents, for matching names and words."""
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def plural(count: int, one: str, many: str) -> str:
    """The count with the right word: '1 vez', '3 veces'."""
    return f"{count} {one if count == 1 else many}"


@dataclass
class Pistas:
    urls: list[str] = field(default_factory=list)
    telefonos: list[str] = field(default_factory=list)
    llaves: list[str] = field(default_factory=list)
    cuentas: list[str] = field(default_factory=list)
    montos: list[str] = field(default_factory=list)
    codigos: list[str] = field(default_factory=list)
    entidades: list[str] = field(default_factory=list)
    urgencia: list[str] = field(default_factory=list)
    aviso_de_codigo: bool = False
    patrones: list[str] = field(default_factory=list)
    acortados: list[str] = field(default_factory=list)
    enlace_disfrazado: bool = False
    menciona_familia: bool = False
    pide_dinero: bool = False
    # A way to pay or talk that came inside the message: a shortened or disguised link, a chat link or a payment reference.
    canal_del_mensaje: bool = False


def squash(text: str) -> str:
    """Lowercase, no accents, only letters and digits: 'Número nuevo' and 'numeronuevo' read the same."""
    return re.sub(r"[^a-z0-9]", "", plain(text))


def find_patterns(squashed: str) -> list[str]:
    return [name for name, groups in PATRONES.items() if all(any(word in squashed for word in group) for group in groups)]


def extract_urls(text: str) -> list[str]:
    """URL-shaped strings, also bare domains such as 'banco-seguro.co/validar'. They are never opened."""
    urls = []
    text = BROKEN_CHAT_LINK.sub(r"\1", GLUED_CHAT_LINK.sub(" ", text))
    for match in URL_PATTERN.finditer(text):
        url = match.group(0).rstrip(".,!?;:")
        while url.endswith(")") and url.count(")") > url.count("("):
            url = url[:-1]
        if not re.match(r"(?i)https?://", url):
            url = f"https://{url}"
        try:
            parsed = urlsplit(url)
        except ValueError:
            continue
        if parsed.hostname in CHAT_LINKS and not parsed.path.strip("/"):
            continue  # "wa.me/" alone, its number lost: it leads nowhere
        if parsed.scheme in {"http", "https"} and parsed.hostname and "." in parsed.hostname:
            urls.append(urlunsplit(parsed._replace(scheme=parsed.scheme.lower(), netloc=parsed.netloc.lower())))
    return list(dict.fromkeys(urls))


def _find_names(text: str, names: list[str]) -> list[str]:
    squashed = plain(text).replace(" ", "")
    words = set(re.findall(r"\w+", plain(text)))
    found = []
    for name in names:
        key = plain(name).replace(" ", "")
        if (len(key) >= 5 and key in squashed) or key in words:
            found.append(name)
    return list(dict.fromkeys(found))


def extract(text: str, entity_names: list[str] | None = None) -> Pistas:
    phones = [p for p in (normalize_phone(m.group(0)) for m in PHONE_PATTERN.finditer(text)) if p]
    without_phones = PHONE_PATTERN.sub(" ", text)
    llaves = []
    for match in LLAVE_PATTERN.finditer(text):
        value = match.group(1).strip()
        llaves.append(re.sub(r"\s", "", value) if value[0].isdigit() else value.lower())
    cuentas = [re.sub(r"\D", "", m.group(1)) for m in CUENTA_PATTERN.finditer(text)]
    lowered = plain(text).replace("sin embargo", "sin_embargo")  # "however", not a seizure
    squashed = squash(text).replace("sinembargo", "")
    disguised = [f"https://{m.group(1).lower()}" for m in DISGUISED_LINK.finditer(text)]
    urls = list(dict.fromkeys(extract_urls(text) + disguised))
    codigos = CODE_PATTERN.findall(AMOUNT_PATTERN.sub(" ", without_phones))
    # The warning itself contains "compartas", so it is removed before looking for requests.
    asks_back = ASKS_BACK.search(CODE_WARNING.sub(" ", lowered))
    hosts = [(urlsplit(u).hostname or "").removeprefix("www.") for u in urls]
    patrones = find_patterns(squashed)
    return Pistas(
        urls=urls,
        telefonos=list(dict.fromkeys(phones)),
        llaves=list(dict.fromkeys(llaves)),
        cuentas=list(dict.fromkeys(cuentas)),
        montos=AMOUNT_PATTERN.findall(text),
        codigos=codigos,
        entidades=_find_names(text, (entity_names or []) + KNOWN_NAMES),
        urgencia=[w for w in URGENCY_WORDS if w in lowered or w.replace(" ", "") in squashed],
        aviso_de_codigo=(bool(codigos) and bool(CODE_WARNING.search(lowered) or CODE_DELIVERY.search(lowered))
                         and not asks_back and not urls),
        patrones=patrones,
        acortados=[h for h in hosts if h in SHORTENERS],
        enlace_disfrazado=bool(disguised),
        menciona_familia=bool(FAMILY_WORDS & set(re.findall(r"\w+", lowered))) or any(w in squashed for w in FAMILY_SQUASHED),
        pide_dinero=bool(llaves or cuentas) or any(w in squashed for w in MONEY_ASK),
        canal_del_mensaje=(bool(disguised) or "pago_referencia" in patrones or bool(phones) or any(h in SHORTENERS | CHAT_LINKS for h in hosts)
                           or any(w in squashed for w in CONTACT_WORDS)),
    )
