"""Official websites of real Colombian entities (datasets/dominios_oficiales.csv).

With them a real Bancolombia link counts as official and bancolombia-seguro.co as an imitation.
Entities connected to Llamada Verificada add their own from the entidades table. Only websites:
official phone numbers come from the entities themselves, never from this list.
"""

import csv
from functools import cache
from pathlib import Path

CSV = Path(__file__).resolve().parents[2] / "datasets" / "dominios_oficiales.csv"


@cache
def official_websites() -> dict[str, tuple[str, ...]]:
    if not CSV.exists():
        return {}
    sites: dict[str, list[str]] = {}
    with CSV.open(encoding="utf-8", newline="") as rows:
        for row in csv.DictReader(rows):
            sites.setdefault(row["entidad"].strip(), []).append(row["dominio"].strip().lower())
    return {name: tuple(dict.fromkeys(domains)) for name, domains in sites.items()}
