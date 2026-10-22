-- Desenmascara · validación del familiar en el Círculo de Confianza.
-- Quien acepta una invitación debe compartir con Telegram el mismo número que dio el protegido, y el protegido
-- confirma que es su familiar. Se guarda la huella del número, nunca el número.
-- Aplícala después de 20261022120000_accesos_entidad.sql. La tabla ya tiene RLS.

alter table miembros_circulo add column if not exists telefono_hash varchar(64);
