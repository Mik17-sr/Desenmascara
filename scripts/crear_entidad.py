"""Connect a real entity to Llamada Verificada and print its access key once.

    python scripts/crear_entidad.py "Nombre de la entidad" --tipo banco --dominio entidad.com --linea "+57 601 000 0000"

--linea can repeat: those numbers go to the official-number list, so the Banco de números says
they are the entity's. Use only numbers the entity itself confirmed.
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.security import normalize_phone  # noqa: E402
from app.db.database import SessionLocal, init_db  # noqa: E402
from app.services import banco, entidades  # noqa: E402


async def main(args: argparse.Namespace) -> None:
    await init_db()
    async with SessionLocal() as db:
        if await entidades.by_name(db, args.nombre):
            raise SystemExit(f"{args.nombre} ya existe. Para una llave nueva, entra al panel o pídela al equipo.")
        phones = [normalize_phone(line) for line in args.linea]
        if None in phones:
            raise SystemExit("Alguna línea no parece un número de teléfono válido.")
        entidad, key = await entidades.create(db, args.nombre, args.tipo, args.dominio, args.linea)
        for phone in phones:
            await banco.add_official(db, entidad, "telefono", phone, "llamada", "registro", args.nombre)
        await db.commit()
    print(f"{args.nombre} conectada a Llamada Verificada.")
    print(f"Llave de acceso (se muestra una sola vez): {key}")
    print(f"Abre el panel sin escribirla: {entidades.panel_link(key)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Conecta una entidad real a Llamada Verificada.")
    parser.add_argument("nombre")
    parser.add_argument("--tipo", default="banco", choices=["banco", "tienda", "operador", "publica"])
    parser.add_argument("--dominio", help="sitio oficial, por ejemplo entidad.com")
    parser.add_argument("--linea", action="append", default=[], help="línea oficial; se puede repetir")
    asyncio.run(main(parser.parse_args()))
