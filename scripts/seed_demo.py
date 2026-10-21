"""Demo data from the guide, all fictional: BancoAndino, Tienda Ejemplo and some reported numbers.

    python scripts/seed_demo.py            # creates what is missing and prints BancoAndino's key once
    python scripts/seed_demo.py --nueva-llave   # rotates BancoAndino's key

Reported numbers come from demo users named "Demo N", so the Banco de números and the
Dashboard are not empty during the demo. Tell the jury these are test data.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.core.security import encrypt, hash_api_key, new_api_key  # noqa: E402
from app.db.database import SessionLocal, init_db  # noqa: E402
from app.db.models import Usuario  # noqa: E402
from app.services import banco, entidades  # noqa: E402
from app.services.usuarios import value_fingerprint  # noqa: E402

ENTIDADES = [
    ("BancoAndino", "banco", "bancoandino.com", ["+57 601 000 0002"], "576010000002"),
    ("Tienda Ejemplo", "tienda", "tiendaejemplo.com", ["+57 601 000 0001"], "576010000001"),
]
# (tipo, valor, modalidad, distinct people, red results) — the first one is the guide's example
REPORTADOS = [
    ("telefono", "576010000000", "falso_asesor", 29, 31),
    ("llave", "3150000000", "falsa_compra", 11, 12),
    ("telefono", "573000000000", "falso_familiar", 9, 4),
    ("cuenta", "00004417", "falso_empleo", 7, 0),
    ("telefono", "573200000000", "falsa_compra", 3, 0),
]


async def main(rotate: bool) -> None:
    await init_db()
    async with SessionLocal() as db:
        demo_users = []
        for i in range(1, 31):
            telegram_hash = value_fingerprint("telegram", f"demo-{i}")
            user = await db.scalar(select(Usuario).where(Usuario.telegram_hash == telegram_hash))
            if user is None:
                user = Usuario(telegram_hash=telegram_hash, chat_cifrado=encrypt("0"), nombre_corto=f"Demo {i}")
                db.add(user)
                await db.flush()
            demo_users.append(user)

        for nombre, tipo, dominio, lineas, oficial in ENTIDADES:
            entidad = await entidades.by_name(db, nombre)
            if entidad is None:
                entidad, key = await entidades.create(db, nombre, tipo, dominio, lineas)
                print(f"Entidad creada: {nombre} · llave de acceso: {key}")
            elif rotate and nombre == "BancoAndino":
                key = new_api_key()
                entidad.api_key_hash = hash_api_key(key)
                print(f"Nueva llave de {nombre}: {key}")
            else:
                print(f"{nombre} ya existía (su llave no se vuelve a mostrar; usa --nueva-llave).")
            await banco.add_official(db, entidad, "telefono", oficial, "telegram", "registro", nombre)

        for tipo, valor, modalidad, people, red in REPORTADOS:
            for user in demo_users[:people]:
                indicador, _ = await banco.report(db, user, tipo, valor, modalidad)
            indicador.consultas_rojo = max(indicador.consultas_rojo, red)
            await banco.recompute(db, indicador)
        await db.commit()
    print("Datos de prueba listos. Son ficticios: díselo así al jurado.")


if __name__ == "__main__":
    asyncio.run(main("--nueva-llave" in sys.argv))
