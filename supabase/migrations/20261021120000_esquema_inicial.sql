-- Desenmascara · esquema inicial para Supabase (guía, sección 16).
-- Las 12 tablas, adaptadas a Telegram, con RLS en todas: solo el servidor (rol postgres,
-- dueño de las tablas) las lee y escribe. El público solo ve 5 vistas agregadas y anónimas,
-- y una tabla de eventos sin datos personales que alimenta Supabase Realtime.
-- Las fechas se guardan en UTC sin zona horaria, igual que en SQLite. «Hoy» es el día de Colombia
-- (UTC-5, sin horario de verano), calculado con un desfase fijo para no depender de tzdata.

-- gen_random_uuid() es nativo desde PostgreSQL 13 (Supabase usa la 15): no hace falta pgcrypto.

-- En Supabase estos roles ya existen; se crean solo para probar en un PostgreSQL normal.
do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'anon') then create role anon nologin; end if;
  if not exists (select 1 from pg_roles where rolname = 'authenticated') then create role authenticated nologin; end if;
end $$;

create table if not exists usuarios (
  id uuid primary key default gen_random_uuid(),
  telegram_hash varchar(64) not null unique,
  chat_cifrado text not null,
  telefono_hash varchar(64) unique,
  nombre_corto varchar(60),
  consentimiento_at timestamp,
  creado_at timestamp not null default (now() at time zone 'utc')
);

create table if not exists circulos (
  id uuid primary key default gen_random_uuid(),
  nombre varchar(80) not null,
  tipo varchar(20) not null default 'familia',
  creado_at timestamp not null default (now() at time zone 'utc')
);

create table if not exists miembros_circulo (
  id uuid primary key default gen_random_uuid(),
  circulo_id uuid not null references circulos(id) on delete cascade,
  usuario_id uuid references usuarios(id) on delete cascade,
  rol varchar(20) not null,
  nombre varchar(60) not null,
  relacion varchar(40),
  invitacion_hash varchar(64) unique,
  acepto_at timestamp,
  creado_at timestamp not null default (now() at time zone 'utc')
);

create table if not exists campanas (
  id uuid primary key default gen_random_uuid(),
  nombre varchar(120) not null,
  modalidad varchar(40),
  total_reportes integer not null default 0,
  estado varchar(20) not null default 'activa',
  centroide jsonb not null,
  primer_reporte_at timestamp not null default (now() at time zone 'utc'),
  ultimo_reporte_at timestamp not null default (now() at time zone 'utc')
);

create table if not exists entidades (
  id uuid primary key default gen_random_uuid(),
  nombre varchar(80) not null unique,
  tipo varchar(20) not null,
  api_key_hash varchar(64) not null unique,
  dominio_oficial varchar(120),
  lineas_oficiales jsonb not null default '[]',
  activa boolean not null default true
);

create table if not exists llamadas_registradas (
  id uuid primary key default gen_random_uuid(),
  entidad_id uuid not null references entidades(id) on delete cascade,
  telefono_hash varchar(64),
  telefono_visible varchar(30) not null,
  motivo varchar(120) not null,
  asesor varchar(60) not null,
  codigo_cifrado text,
  estado varchar(20) not null default 'registrada',
  creado_at timestamp not null default (now() at time zone 'utc'),
  vence_at timestamp not null,
  confirmada_at timestamp
);

create table if not exists verificaciones (
  id uuid primary key default gen_random_uuid(),
  usuario_id uuid references usuarios(id) on delete set null,
  campana_id uuid references campanas(id) on delete set null,
  llamada_id uuid references llamadas_registradas(id) on delete set null,
  canal varchar(20) not null,
  tipo varchar(20) not null,
  texto_anonimizado text not null default '',
  puntaje integer not null,
  nivel varchar(20) not null,
  modalidad varchar(40),
  senales jsonb not null default '[]',
  huella jsonb,
  processing_ms integer not null default 0,
  creado_at timestamp not null default (now() at time zone 'utc')
);

create table if not exists avisos_circulo (
  id uuid primary key default gen_random_uuid(),
  circulo_id uuid not null references circulos(id) on delete cascade,
  destinatario_id uuid not null references miembros_circulo(id) on delete cascade,
  verificacion_id uuid references verificaciones(id) on delete set null,
  tipo varchar(20) not null,
  respuesta varchar(20),
  creado_at timestamp not null default (now() at time zone 'utc'),
  respondido_at timestamp
);

create table if not exists indicadores (
  id uuid primary key default gen_random_uuid(),
  campana_id uuid references campanas(id) on delete set null,
  tipo varchar(20) not null,
  valor_hash varchar(64) not null,
  valor_visible varchar(120) not null,
  personas_distintas integer not null default 0,
  consultas_rojo integer not null default 0,
  nivel_riesgo integer not null default 0,
  estado varchar(20) not null default 'normal',
  modalidad varchar(40),
  ultimo_visto_at timestamp not null default (now() at time zone 'utc'),
  creado_at timestamp not null default (now() at time zone 'utc'),
  unique (tipo, valor_hash)
);

create table if not exists reportes (
  id uuid primary key default gen_random_uuid(),
  indicador_id uuid not null references indicadores(id) on delete cascade,
  usuario_id uuid not null references usuarios(id) on delete cascade,
  verificacion_id uuid references verificaciones(id) on delete set null,
  modalidad varchar(40),
  creado_at timestamp not null default (now() at time zone 'utc'),
  -- Una persona cuenta una sola vez por número: nadie puede hundir un número solo.
  unique (indicador_id, usuario_id)
);

create table if not exists solicitudes_revision (
  id uuid primary key default gen_random_uuid(),
  indicador_id uuid not null references indicadores(id) on delete cascade,
  motivo varchar(300) not null,
  estado varchar(20) not null default 'pendiente',
  creado_at timestamp not null default (now() at time zone 'utc'),
  resuelto_at timestamp
);

create table if not exists numeros_oficiales (
  id uuid primary key default gen_random_uuid(),
  entidad_id uuid not null references entidades(id) on delete cascade,
  nombre varchar(80) not null,
  tipo varchar(20) not null default 'telefono',
  valor_hash varchar(64) not null,
  valor_visible varchar(40) not null,
  canal varchar(20) not null,
  fuente varchar(30) not null,
  verificado_por varchar(60) not null,
  verificado_at timestamp not null default (now() at time zone 'utc'),
  unique (tipo, valor_hash)
);

create index if not exists verificaciones_creado_idx on verificaciones (creado_at);
create index if not exists verificaciones_nivel_idx on verificaciones (nivel, creado_at);
create index if not exists verificaciones_campana_idx on verificaciones (campana_id);
create index if not exists indicadores_nivel_idx on indicadores (nivel_riesgo desc);
create index if not exists reportes_creado_idx on reportes (creado_at);
create index if not exists llamadas_telefono_idx on llamadas_registradas (telefono_hash);
create index if not exists llamadas_entidad_idx on llamadas_registradas (entidad_id, creado_at);

-- RLS en todas las tablas y sin políticas: anon y authenticated no leen ni escriben nada.
-- El servidor se conecta como postgres (dueño de las tablas), que no está sujeto a RLS.
do $$
declare t text;
begin
  foreach t in array array['usuarios','circulos','miembros_circulo','avisos_circulo','campanas','entidades',
                           'llamadas_registradas','verificaciones','indicadores','reportes','solicitudes_revision','numeros_oficiales']
  loop
    execute format('alter table %I enable row level security', t);
    execute format('revoke all on table %I from anon, authenticated', t);
  end loop;
end $$;

-- Las 5 vistas de solo lectura de la guía: agregadas y anónimas. Corren con los permisos de su
-- dueño, por eso pueden leer tablas con RLS sin exponer filas con datos personales.
create or replace view radar_por_hora as
select (v.creado_at - interval '5 hours')::date as dia,
       extract(hour from v.creado_at - interval '5 hours')::int as hora,
       count(*)::int as total,
       (count(*) filter (where v.nivel = 'high'))::int as alto_riesgo,
       (count(*) filter (where v.tipo in ('numero', 'voz')))::int as llamadas_reportadas,
       round(avg(v.processing_ms))::int as ms_promedio
from verificaciones v
where v.creado_at >= (now() at time zone 'utc') - interval '2 days'
group by 1, 2;

create or replace view tipos_de_estafa as
select v.modalidad, count(*)::int as total
from verificaciones v
where v.modalidad is not null and v.nivel in ('high', 'medium')
  and (v.creado_at - interval '5 hours')::date = ((now() at time zone 'utc') - interval '5 hours')::date
group by v.modalidad;

create or replace view campanas_activas as
select c.id, c.nombre, c.modalidad, c.total_reportes, c.ultimo_reporte_at,
       (select count(*) from verificaciones v
         where v.campana_id = c.id and v.creado_at >= (now() at time zone 'utc') - interval '1 hour')::int as ultima_hora
from campanas c
where c.ultimo_reporte_at >= (now() at time zone 'utc') - interval '24 hours';

create or replace view llamadas_verificadas as
select v.senales -> 0 ->> 'evidence' as entidad, (v.nivel = 'low') as real, v.creado_at
from verificaciones v
where v.tipo = 'llamada'
order by v.creado_at desc
limit 50;

create or replace view banco_mas_reportados as
select i.valor_visible, i.tipo, i.personas_distintas, i.nivel_riesgo, i.estado, i.modalidad, i.ultimo_visto_at
from indicadores i
where i.personas_distintas > 0 or i.estado = 'en_revision'
order by i.nivel_riesgo desc, i.ultimo_visto_at desc
limit 50;

grant select on radar_por_hora, tipos_de_estafa, campanas_activas, llamadas_verificadas, banco_mas_reportados to anon, authenticated;

-- Realtime: el Dashboard se suscribe a esta tabla y vuelve a pedir los agregados cuando cambia algo.
-- Solo guarda qué tabla cambió y el nivel de riesgo; nunca texto, números ni usuarios.
create table if not exists eventos_dashboard (
  id bigint generated always as identity primary key,
  tabla text not null,
  nivel text,
  modalidad text,
  creado_at timestamp not null default (now() at time zone 'utc')
);
alter table eventos_dashboard enable row level security;
drop policy if exists "Eventos anónimos visibles para el Dashboard" on eventos_dashboard;
create policy "Eventos anónimos visibles para el Dashboard" on eventos_dashboard for select to anon, authenticated using (true);
grant select on eventos_dashboard to anon, authenticated;

create or replace function avisar_dashboard() returns trigger
language plpgsql security definer set search_path = public as $$
declare fila jsonb := to_jsonb(new);
begin
  insert into eventos_dashboard (tabla, nivel, modalidad)
  values (tg_table_name,
          case when tg_table_name = 'verificaciones' then fila ->> 'nivel' end,
          case when tg_table_name = 'verificaciones' then fila ->> 'modalidad' end);
  delete from eventos_dashboard where creado_at < (now() at time zone 'utc') - interval '1 day';
  return null;
end $$;

drop trigger if exists avisar_dashboard on verificaciones;
create trigger avisar_dashboard after insert on verificaciones for each row execute function avisar_dashboard();
drop trigger if exists avisar_dashboard on reportes;
create trigger avisar_dashboard after insert on reportes for each row execute function avisar_dashboard();
drop trigger if exists avisar_dashboard on llamadas_registradas;
create trigger avisar_dashboard after insert or update of estado on llamadas_registradas for each row execute function avisar_dashboard();
drop trigger if exists avisar_dashboard on solicitudes_revision;
create trigger avisar_dashboard after insert or update of estado on solicitudes_revision for each row execute function avisar_dashboard();

do $$
begin
  if exists (select 1 from pg_publication where pubname = 'supabase_realtime')
     and not exists (select 1 from pg_publication_tables where pubname = 'supabase_realtime' and tablename = 'eventos_dashboard') then
    alter publication supabase_realtime add table eventos_dashboard;
  end if;
end $$;
