"""The 12 tables of the project guide (section 16), adapted to Telegram.

Changes from the guide: users are identified by an HMAC of their Telegram id and an
encrypted chat id (the bot needs it to write to Círculo members); their phone is only
fingerprinted, after they share it, for Llamada Verificada and review requests.
Message fingerprints are MinHash signatures stored as JSON instead of pgvector.
"""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    # Naive UTC everywhere: SQLite does not keep time zones.
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Base(DeclarativeBase):
    pass


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    telegram_hash: Mapped[str] = mapped_column(String(64), unique=True)
    chat_cifrado: Mapped[str] = mapped_column(Text)
    telefono_hash: Mapped[str | None] = mapped_column(String(64), unique=True)
    nombre_corto: Mapped[str | None] = mapped_column(String(60))
    consentimiento_at: Mapped[datetime | None] = mapped_column(DateTime)
    creado_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Circulo(Base):
    __tablename__ = "circulos"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    nombre: Mapped[str] = mapped_column(String(80))
    tipo: Mapped[str] = mapped_column(String(20), default="familia")
    creado_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class MiembroCirculo(Base):
    __tablename__ = "miembros_circulo"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    circulo_id: Mapped[UUID] = mapped_column(ForeignKey("circulos.id", ondelete="CASCADE"))
    # Empty until the invited relative opens the link: the bot cannot write first on Telegram.
    usuario_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    rol: Mapped[str] = mapped_column(String(20))  # protegido | familiar
    nombre: Mapped[str] = mapped_column(String(60))
    relacion: Mapped[str | None] = mapped_column(String(40))
    invitacion_hash: Mapped[str | None] = mapped_column(String(64), unique=True)
    acepto_at: Mapped[datetime | None] = mapped_column(DateTime)
    creado_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class AvisoCirculo(Base):
    __tablename__ = "avisos_circulo"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    circulo_id: Mapped[UUID] = mapped_column(ForeignKey("circulos.id", ondelete="CASCADE"))
    destinatario_id: Mapped[UUID] = mapped_column(ForeignKey("miembros_circulo.id", ondelete="CASCADE"))
    verificacion_id: Mapped[UUID | None] = mapped_column(ForeignKey("verificaciones.id", ondelete="SET NULL"))
    tipo: Mapped[str] = mapped_column(String(20))  # pregunta | alerta
    respuesta: Mapped[str | None] = mapped_column(String(20))  # si | no | sin_respuesta
    creado_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    respondido_at: Mapped[datetime | None] = mapped_column(DateTime)


class Campana(Base):
    __tablename__ = "campanas"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    nombre: Mapped[str] = mapped_column(String(120))
    modalidad: Mapped[str | None] = mapped_column(String(40))
    total_reportes: Mapped[int] = mapped_column(Integer, default=0)
    estado: Mapped[str] = mapped_column(String(20), default="activa")
    centroide: Mapped[list] = mapped_column(JSON)
    primer_reporte_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    ultimo_reporte_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Entidad(Base):
    __tablename__ = "entidades"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    nombre: Mapped[str] = mapped_column(String(80), unique=True)
    tipo: Mapped[str] = mapped_column(String(20))  # banco | tienda | operador | publica
    api_key_hash: Mapped[str] = mapped_column(String(64), unique=True)
    dominio_oficial: Mapped[str | None] = mapped_column(String(120))
    lineas_oficiales: Mapped[list] = mapped_column(JSON, default=list)
    activa: Mapped[bool] = mapped_column(Boolean, default=True)


class AccesoEntidad(Base):
    """E-mail and password for the entity panel. The API key stays for integrations."""
    __tablename__ = "accesos_entidad"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    entidad_id: Mapped[UUID] = mapped_column(ForeignKey("entidades.id", ondelete="CASCADE"), index=True)
    correo: Mapped[str] = mapped_column(String(120), unique=True)
    clave_hash: Mapped[str] = mapped_column(String(200))
    creado_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class LlamadaRegistrada(Base):
    __tablename__ = "llamadas_registradas"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    entidad_id: Mapped[UUID] = mapped_column(ForeignKey("entidades.id", ondelete="CASCADE"))
    # Phone fingerprint and code are wiped when the call expires; the masked row stays for the panel.
    telefono_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    telefono_visible: Mapped[str] = mapped_column(String(30))
    motivo: Mapped[str] = mapped_column(String(120))
    asesor: Mapped[str] = mapped_column(String(60))
    codigo_cifrado: Mapped[str | None] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(String(20), default="registrada")  # registrada | confirmada | vencida
    creado_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    vence_at: Mapped[datetime] = mapped_column(DateTime)
    confirmada_at: Mapped[datetime | None] = mapped_column(DateTime)


class Verificacion(Base):
    __tablename__ = "verificaciones"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    usuario_id: Mapped[UUID | None] = mapped_column(ForeignKey("usuarios.id", ondelete="SET NULL"))
    campana_id: Mapped[UUID | None] = mapped_column(ForeignKey("campanas.id", ondelete="SET NULL"))
    llamada_id: Mapped[UUID | None] = mapped_column(ForeignKey("llamadas_registradas.id", ondelete="SET NULL"))
    canal: Mapped[str] = mapped_column(String(20))  # telegram | dashboard | api
    tipo: Mapped[str] = mapped_column(String(20))  # mensaje | captura | voz | numero | compra | llamada
    texto_anonimizado: Mapped[str] = mapped_column(Text, default="")
    puntaje: Mapped[int] = mapped_column(Integer)
    nivel: Mapped[str] = mapped_column(String(20))
    modalidad: Mapped[str | None] = mapped_column(String(40))
    senales: Mapped[list] = mapped_column(JSON, default=list)
    huella: Mapped[list | None] = mapped_column(JSON)
    processing_ms: Mapped[int] = mapped_column(Integer, default=0)
    creado_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class Indicador(Base):
    """The Banco de números: phones, Bre-B keys, accounts and links with their risk level."""

    __tablename__ = "indicadores"
    __table_args__ = (UniqueConstraint("tipo", "valor_hash"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    campana_id: Mapped[UUID | None] = mapped_column(ForeignKey("campanas.id", ondelete="SET NULL"))
    tipo: Mapped[str] = mapped_column(String(20))  # telefono | llave | cuenta | enlace
    valor_hash: Mapped[str] = mapped_column(String(64))
    valor_visible: Mapped[str] = mapped_column(String(120))
    personas_distintas: Mapped[int] = mapped_column(Integer, default=0)
    consultas_rojo: Mapped[int] = mapped_column(Integer, default=0)
    nivel_riesgo: Mapped[int] = mapped_column(Integer, default=0)
    estado: Mapped[str] = mapped_column(String(20), default="normal")  # normal | en_revision
    modalidad: Mapped[str | None] = mapped_column(String(40))
    ultimo_visto_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    creado_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Reporte(Base):
    __tablename__ = "reportes"
    # One vote per person and number: a single person cannot sink a number.
    __table_args__ = (UniqueConstraint("indicador_id", "usuario_id"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    indicador_id: Mapped[UUID] = mapped_column(ForeignKey("indicadores.id", ondelete="CASCADE"))
    usuario_id: Mapped[UUID] = mapped_column(ForeignKey("usuarios.id", ondelete="CASCADE"))
    verificacion_id: Mapped[UUID | None] = mapped_column(ForeignKey("verificaciones.id", ondelete="SET NULL"))
    modalidad: Mapped[str | None] = mapped_column(String(40))
    creado_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class SolicitudRevision(Base):
    __tablename__ = "solicitudes_revision"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    indicador_id: Mapped[UUID] = mapped_column(ForeignKey("indicadores.id", ondelete="CASCADE"))
    motivo: Mapped[str] = mapped_column(String(300))
    estado: Mapped[str] = mapped_column(String(20), default="pendiente")  # pendiente | aceptada | rechazada
    creado_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    resuelto_at: Mapped[datetime | None] = mapped_column(DateTime)


class NumeroOficial(Base):
    """The whitelist: only numbers with an official source."""

    __tablename__ = "numeros_oficiales"
    __table_args__ = (UniqueConstraint("tipo", "valor_hash"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    entidad_id: Mapped[UUID] = mapped_column(ForeignKey("entidades.id", ondelete="CASCADE"))
    nombre: Mapped[str] = mapped_column(String(80))
    tipo: Mapped[str] = mapped_column(String(20), default="telefono")
    valor_hash: Mapped[str] = mapped_column(String(64))
    valor_visible: Mapped[str] = mapped_column(String(40))
    canal: Mapped[str] = mapped_column(String(20))  # telegram | whatsapp | llamada | sms
    fuente: Mapped[str] = mapped_column(String(30))  # registro | pagina_oficial
    verificado_por: Mapped[str] = mapped_column(String(60))
    verificado_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
