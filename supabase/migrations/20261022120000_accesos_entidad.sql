-- Desenmascara · inicio de sesión de las entidades con correo y contraseña.
-- La llave de acceso (API key) queda para integraciones; el Panel usa correo y contraseña.
-- Aplícala después de 20261021120000_esquema_inicial.sql.

create table if not exists accesos_entidad (
  id uuid primary key default gen_random_uuid(),
  entidad_id uuid not null references entidades(id) on delete cascade,
  correo varchar(120) not null unique,
  clave_hash varchar(200) not null,  -- scrypt: la contraseña nunca se guarda
  creado_at timestamptz not null default now()
);
create index if not exists accesos_entidad_entidad_idx on accesos_entidad (entidad_id);

-- Como las demás tablas: RLS sin políticas, nadie fuera del servidor la lee ni la escribe.
alter table accesos_entidad enable row level security;
revoke all on table accesos_entidad from anon, authenticated;
