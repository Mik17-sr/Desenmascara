"""Demo data from the guide, all fictional: BancoAndino, Tienda Ejemplo and some reported numbers.

    python scripts/seed_demo.py            # creates what is missing and prints BancoAndino's key once
    python scripts/seed_demo.py --nueva-llave   # rotates BancoAndino's key

Reported numbers come from demo users named "Demo N", so the Banco de números and the
Dashboard are not empty during the demo. Tell the jury these are test data, and remove them
with scripts/limpiar_datos.py before showing the system to a company.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select  # noqa: E402

from app.core.security import encrypt, hash_api_key, new_api_key  # noqa: E402
from app.db.database import SessionLocal, init_db  # noqa: E402
from app.db.models import AccesoEntidad, Usuario  # noqa: E402
from app.services import banco, demo, entidades  # noqa: E402
from app.services.entidades import panel_link  # noqa: E402

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
        for i, telegram_hash in enumerate(demo.user_fingerprints(), 1):
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
                print(f"  Abre el panel sin escribirla: {panel_link(key)}")
            elif rotate and nombre == "BancoAndino":
                key = new_api_key()
                entidad.api_key_hash = hash_api_key(key)
                print(f"Nueva llave de {nombre}: {key}")
                print(f"  Abre el panel sin escribirla: {panel_link(key)}")
            else:
                print(f"{nombre} ya existía (su llave no se vuelve a mostrar; usa --nueva-llave).")
            await banco.add_official(db, entidad, "telefono", oficial, "telegram", "registro", nombre)
            correo = f"panel@{nombre.lower().replace(' ', '')}.test"  # .test is reserved: never a real company's mail
            if not await db.scalar(select(AccesoEntidad).where(AccesoEntidad.entidad_id == entidad.id)):
                print(f"  Panel de {nombre}: correo {correo} · contraseña {await entidades.add_access(db, entidad, correo)}")

        for tipo, valor, modalidad, people, red in REPORTADOS:
            for user in demo_users[:people]:
                indicador, _ = await banco.report(db, user, tipo, valor, modalidad)
            indicador.consultas_rojo = max(indicador.consultas_rojo, red)
            await banco.recompute(db, indicador)
        await db.commit()
    print("Datos de prueba listos. Son ficticios: díselo así al jurado.")
    print("Antes de mostrarlo a una empresa: python scripts/limpiar_datos.py")


if __name__ == "__main__":
    asyncio.run(main("--nueva-llave" in sys.argv))
