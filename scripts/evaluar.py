"""Measure the whole system with the dataset (guide section 21), through the running API.

    python scripts/evaluar.py                       # datasets/casos_prueba.csv
    python scripts/evaluar.py otra_hoja.csv

A scam counts as detected when the result is SOSPECHOSO or ALTO RIESGO; a legitimate message
counts as a false positive when it is not BAJO RIESGO. Rows marked "dudoso" (real collections that
may be genuine) should be at least SOSPECHOSO and are reported apart. Goals in docs/07: sensitivity >= 95 %,
false positives <= 5 %, P90 < 8 s. The checks are saved like any other, so they feed the Dashboard.
"""

import csv
import statistics
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings  # noqa: E402

DATASET = Path(__file__).resolve().parent.parent / "datasets" / "casos_prueba.csv"
TIMEOUT = 8.0  # the bot's budget


def main(path: Path) -> None:
    url = settings.API_BASE_URL.rstrip("/") + settings.API_V1_STR + "/analyze"
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    times, outcomes = [], []
    with httpx.Client(timeout=TIMEOUT) as client:
        for row in rows:
            tipo = {"compra": "compra", "llamada": "llamada"}.get(row["canal"], "mensaje")
            started = time.perf_counter()
            try:
                body = client.post(url, json={"text": row["texto"], "source": "api", "tipo": tipo}).json()
                level = body["risk_level"]
            except (httpx.HTTPError, KeyError, ValueError):
                level = "sin respuesta"
            elapsed = time.perf_counter() - started
            times.append(elapsed)
            label = row["es_estafa"].strip().lower()
            kind = "estafa" if label in ("si", "sí", "1", "true") else "dudoso" if label == "dudoso" else "legítimo"
            outcomes.append((kind, level))
            print(f"{row['id']:>3} {kind:8} {level:13} {elapsed:4.1f}s  {row['texto'][:60]}")
            time.sleep(3.2)  # the public endpoint allows 20 requests per minute

    scams = [lvl for kind, lvl in outcomes if kind == "estafa"]
    legit = [lvl for kind, lvl in outcomes if kind == "legítimo"]
    doubtful = [lvl for kind, lvl in outcomes if kind == "dudoso"]
    detected = sum(lvl in ("high", "medium") for lvl in scams)
    false_pos = sum(lvl in ("high", "medium") for lvl in legit)
    flagged = detected + false_pos
    p90 = sorted(times)[max(0, round(0.9 * len(times)) - 1)]
    print()
    print(f"Sensibilidad (estafas detectadas): {detected}/{len(scams)} = {100 * detected / max(1, len(scams)):.0f} %  (meta >= 95 %)")
    print(f"Falsos positivos: {false_pos}/{len(legit)} = {100 * false_pos / max(1, len(legit)):.0f} %  (meta <= 5 %)")
    print(f"Precisión (de lo marcado, cuánto era estafa): {100 * detected / max(1, flagged):.0f} %")
    if doubtful:  # real collections that may be genuine: the right answer is "verify first", so at least sospechoso
        print(f"Cobros dudosos marcados para verificar: {sum(lvl in ('high', 'medium') for lvl in doubtful)}/{len(doubtful)}")
    print(f"Sin respuesta o no concluyente: {sum(lvl in ('sin respuesta', 'inconclusive') for _, lvl in outcomes)}")
    print(f"Tiempo: mediana {statistics.median(times):.1f} s · P90 {p90:.1f} s  (meta P90 < 8 s)")


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else DATASET)
