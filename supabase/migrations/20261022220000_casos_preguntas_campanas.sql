-- Desenmascara · pregunta de confidencialidad del Círculo y campañas identificadas por el equipo.
-- 1. Al invitar a un familiar, el protegido puede poner una pregunta que solo esa persona sabe responder: la pregunta
--    se guarda cifrada y la respuesta solo como huella. Tres respuestas equivocadas cancelan la invitación.
-- 2. El equipo describe una campaña y la vuelve regla: el bot la reconoce sin límite de días y cita la descripción.
-- Aplícala después de 20261022160000_validar_familiar.sql. Las tablas ya tienen RLS.

alter table miembros_circulo add column if not exists pregunta_cifrada text;
alter table miembros_circulo add column if not exists respuesta_hash varchar(64);
alter table miembros_circulo add column if not exists intentos integer default 0;

alter table campanas add column if not exists descripcion text;
alter table campanas add column if not exists regla boolean default false;
alter table campanas add column if not exists revisada_por varchar(60);
alter table campanas add column if not exists revisada_at timestamp;
