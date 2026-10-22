"""Official websites and phone lines of real Colombian entities, from the datasets folder.

With the websites (dominios_oficiales.csv) a real Bancolombia link counts as official and
bancolombia-seguro.co as an imitation. The lines (lineas_oficiales.csv) are only numbers each
entity publishes on its own website, with that page as the source; a caller can still fake
them on screen, so they confirm messages and tell people where to call, never a call.
Entities connected to Llamada Verificada add their own from the entidades table.
"""

import csv
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from urllib.parse import urlsplit

from app.core.security import normalize_phone

DATASETS = Path(__file__).resolve().parents[2] / "datasets"
CSV = DATASETS / "dominios_oficiales.csv"
LINES_CSV = DATASETS / "lineas_oficiales.csv"


@dataclass(frozen=True)
class OfficialLine:
    entidad: str
    linea: str   # as the entity publishes it, e.g. "01 8000 9 12345"
    donde: str   # "Bogotá", "Resto del país"...
    sitio: str   # the website it was taken from


@cache
def official_lines() -> dict[str, OfficialLine]:
    """Normalized number -> the published line."""
    if not LINES_CSV.exists():
        return {}
    lines = {}
    with LINES_CSV.open(encoding="utf-8", newline="") as rows:
        for row in csv.DictReader(rows):
            number = normalize_phone(row["linea"])
            if number:
                site = (urlsplit(row["fuente"]).hostname or "").removeprefix("www.")
                lines[number] = OfficialLine(row["entidad"].strip(), row["linea"].strip(), row["donde"].strip(), site)
    return lines


def line_to_call(entidad: str) -> OfficialLine | None:
    """The line to suggest for an entity: its national toll-free one if it has it."""
    own = [line for line in official_lines().values() if line.entidad == entidad]
    return next((line for line in own if line.linea.startswith("01")), own[0] if own else None)


@cache
def official_websites() -> dict[str, tuple[str, ...]]:
    if not CSV.exists():
        return {}
    sites: dict[str, list[str]] = {}
    with CSV.open(encoding="utf-8", newline="") as rows:
        for row in csv.DictReader(rows):
            sites.setdefault(row["entidad"].strip(), []).append(row["dominio"].strip().lower())
    return {name: tuple(dict.fromkeys(domains)) for name, domains in sites.items()}
