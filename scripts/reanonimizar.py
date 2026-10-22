"""Pass the stored texts and campaign names through the current anonymizer again.

Campaigns the team has not reviewed also get the current automatic name («Posible cobranza falsa · Credivalores»)
from their latest check, instead of the first words of a screenshot.

When the anonymizer learns a new pattern (names glued by the OCR, a title before the name), the checks already
saved keep the old text. This only removes more, never adds. Without --aplicar it just counts.

    python scripts/reanonimizar.py            # how many would change
    python scripts/reanonimizar.py --aplicar  # save them
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select  # noqa: E402

from app.db.database import SessionLocal  # noqa: E402
from app.db.models import Campana, Verificacion  # noqa: E402
from app.services.verificaciones import anonymize, campaign_name  # noqa: E402


async def main(apply: bool) -> None:
    async with SessionLocal() as session:
        checks = [v for v in await session.scalars(select(Verificacion)) if anonymize(v.texto_anonimizado or "") != (v.texto_anonimizado or "")]
        names = {}
        for c in await session.scalars(select(Campana)):
            example = await session.scalar(select(Verificacion.texto_anonimizado).where(Verificacion.campana_id == c.id)
                                           .order_by(Verificacion.creado_at.desc()).limit(1))
            name = campaign_name(c.modalidad, example) if example and not c.revisada_por else anonymize(c.nombre)
            if name != c.nombre:
                names[c] = name[:120]
        campaigns = list(names)
        print(f"Textos que cambian: {len(checks)} · nombres de campaña: {len(campaigns)}")
        for c, name in names.items():
            print("  campaña:", name)
        if apply:
            for v in checks:
                v.texto_anonimizado = anonymize(v.texto_anonimizado)
            for c, name in names.items():
                c.nombre = name
            await session.commit()
            print("Guardado.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--aplicar", action="store_true", help="guardar los textos limpios")
    asyncio.run(main(parser.parse_args().aplicar))
