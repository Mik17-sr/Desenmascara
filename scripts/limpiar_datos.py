"""Remove the demo data before showing the system to a company, or start from zero.

    python scripts/limpiar_datos.py          # BancoAndino, Tienda Ejemplo and the "Demo N" users with their reports
    python scripts/limpiar_datos.py --todo   # also every check, campaign, report and call (asks first; --si skips it)

Users, their Círculos and the real entities stay. The real entities' websites live in
datasets/dominios_oficiales.csv and are not touched.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db.database import SessionLocal, init_db  # noqa: E402
from app.services import demo  # noqa: E402


async def main(everything: bool) -> None:
    await init_db()
    async with SessionLocal() as db:
        removed = await demo.remove(db)
        print(f"Datos de demostración quitados: {removed['entidades']} entidades ficticias, "
              f"{removed['usuarios']} usuarios «Demo» y {removed['numeros']} números que solo ellos reportaron.")
        if everything:
            counts = await demo.remove_activity(db)
            print("Actividad borrada: " + ", ".join(f"{n} {name}" for name, n in counts.items()) + ".")
        await db.commit()


if __name__ == "__main__":
    everything = "--todo" in sys.argv
    if everything and "--si" not in sys.argv:
        answer = input("Esto borra TODAS las verificaciones, campañas, reportes y llamadas. Escribe BORRAR para seguir: ")
        if answer.strip() != "BORRAR":
            raise SystemExit("No se borró nada.")
    asyncio.run(main(everything))
