"""Revisión 2 · El que subraya pistas: links, phones, Bre-B keys, accounts, amounts and codes. No AI."""

import re
import unicodedata
from dataclasses import dataclass, field
from urllib.parse import urlsplit

from app.core.security import normalize_phone

_TLDS = r"(?:com\.co|gov\.co|org\.co|net\.co|edu\.co|com|co|net|org|info|xyz|site|online|top|app|link|shop|store|club|live|me|io|ly|lat|vip)"
URL_PATTERN = re.compile(
    r"(?i)\b(?:https?://|www\.)[^\s<>\"']+"
    rf"|(?<![@\w.-])(?:[a-z0-9](?:[a-z0-9-]{{0,61}}[a-z0-9])?\.)+{_TLDS}\b(?:/[^\s<>\"']*)?"
)
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

# Detection only: whether a message claims to come from one of these. Official domains and
# numbers come from the entidades table, never from this list.
KNOWN_NAMES = [
    "Bancolombia", "Davivienda", "BBVA", "Banco de Bogotá", "Banco Popular", "Banco de Occidente",
    "Banco Caja Social", "Scotiabank Colpatria", "Banco Agrario", "AV Villas", "Itaú", "Nequi",
    "Daviplata", "Banco Falabella", "Lulo Bank", "DIAN", "Policía", "Fiscalía", "Secretaría de Movilidad",
    "SIMIT", "Servientrega", "Interrapidisimo", "Coordinadora", "Envia",
]
# "Tu código es 482913. No lo compartas": a notice that hands over a code, which small models
# read as a request for it. Only counts when the message asks for nothing back.
CODE_WARNING = re.compile(r"no\s+(?:lo|la)\s+compartas|no\s+compartas|nunca\s+te\s+(?:lo|la)\s+pedir|si\s+no\s+(?:lo|la)\s+(?:solicitaste|pediste)|si\s+no\s+fuiste\s+tu")
ASKS_BACK = re.compile(r"envi|reenvi|dime|digame|dicta|dictame|compart(?:e|eme|ir)\b|respond|escribe|escribeme|manda|llama\s+al|ingresa|entra\s+a")
URGENCY_WORDS = [
    "urgente", "inmediat", "hoy mismo", "solo hoy", "ultimo aviso", "bloque", "suspend", "24 horas",
    "48 horas", "embargo", "multa", "no le digas", "no le diga", "antes de que", "ultima oportunidad",
]


def plain(text: str) -> str:
    """Lowercase without accents, for matching names and words."""
    decomposed = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


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


def extract_urls(text: str) -> list[str]:
    """URL-shaped strings, also bare domains such as 'banco-seguro.co/validar'. They are never opened."""
    urls = []
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
        if parsed.scheme in {"http", "https"} and parsed.hostname and "." in parsed.hostname:
            urls.append(url)
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
    lowered = plain(text)
    urls = extract_urls(text)
    codigos = CODE_PATTERN.findall(AMOUNT_PATTERN.sub(" ", without_phones))
    # The warning itself contains "compartas", so it is removed before looking for requests.
    asks_back = ASKS_BACK.search(CODE_WARNING.sub(" ", lowered))
    return Pistas(
        urls=urls,
        telefonos=list(dict.fromkeys(phones)),
        llaves=list(dict.fromkeys(llaves)),
        cuentas=list(dict.fromkeys(cuentas)),
        montos=AMOUNT_PATTERN.findall(text),
        codigos=codigos,
        entidades=_find_names(text, (entity_names or []) + KNOWN_NAMES),
        urgencia=[w for w in URGENCY_WORDS if w in lowered],
        aviso_de_codigo=bool(codigos) and bool(CODE_WARNING.search(lowered)) and not asks_back and not urls,
    )
