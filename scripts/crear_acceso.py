"""Give one more person their own sign-in to an entity's panel, and print the password once.

    python scripts/crear_acceso.py "Desenmascara" --correo companero@correo.com
    python scripts/crear_acceso.py "Desenmascara" --correo companero@correo.com --quitar
    python scripts/crear_acceso.py "Desenmascara" --lista

Each person of the entity's team enters with their own e-mail: nobody shares a password, and one access can be
removed without touching the others. Only the password's hash is stored, so it is shown here once: send it to the
person by a private channel. It runs against the DATABASE_URL in .env (Supabase, the same one Render uses).
"""

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import delete, select  # noqa: E402

from app.db.database import SessionLocal, init_db  # noqa: E402
from app.db.models import AccesoEntidad  # noqa: E402
from app.services import entidades  # noqa: E402

PANEL = "https://desenmascara.onrender.com/entidad/"


async def main(args: argparse.Namespace) -> None:
    await init_db()
    async with SessionLocal() as db:
        entidad = await entidades.by_name(db, args.nombre)
        if entidad is None:
            raise SystemExit(f"No existe la entidad «{args.nombre}». Créala con scripts/crear_entidad.py.")
        if args.lista:
            correos = await db.scalars(select(AccesoEntidad.correo).where(AccesoEntidad.entidad_id == entidad.id).order_by(AccesoEntidad.correo))
            print(f"Accesos de {entidad.nombre}:", ", ".join(correos) or "ninguno")
            return
        if not args.correo:
            raise SystemExit("Falta --correo.")
        correo = args.correo.strip().lower()
        existing = await db.scalar(select(AccesoEntidad).where(AccesoEntidad.correo == correo))
        if args.quitar:
            if existing is None or existing.entidad_id != entidad.id:
                raise SystemExit(f"{correo} no tiene acceso a {entidad.nombre}.")
            await db.execute(delete(AccesoEntidad).where(AccesoEntidad.id == existing.id))
            await db.commit()
            print(f"Listo: {correo} ya no entra al panel de {entidad.nombre}.")
            return
        if existing is not None:
            raise SystemExit(f"{correo} ya tiene acceso. Para una contraseña nueva, quítalo con --quitar y créalo otra vez.")
        password = await entidades.add_access(db, entidad, correo)
        await db.commit()
    print(f"Acceso creado para {correo} en {entidad.nombre}.")
    print(f"Panel: {PANEL}  ·  correo {correo}  ·  contraseña {password}")
    print("La contraseña no se vuelve a mostrar: envíasela a esa persona por un canal privado.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Da a una persona su propio acceso al Panel de una entidad.")
    parser.add_argument("nombre", help="la entidad, por ejemplo Desenmascara")
    parser.add_argument("--correo", help="con el que esa persona entra al Panel")
    parser.add_argument("--quitar", action="store_true", help="retira el acceso de ese correo")
    parser.add_argument("--lista", action="store_true", help="muestra los correos que entran al Panel de la entidad")
    asyncio.run(main(parser.parse_args()))
