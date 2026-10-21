# Agente 4 — Base de Datos, Persistencia y Tiempo Real

**Responsable:** Luis Guillermo Nieto Patiño & Miguel  
**Motor:** PostgreSQL 15 en Supabase · Extensión `pgvector` · Supabase Realtime · Row Level Security (RLS)  
**Misión:** Administrar el modelo de datos relacional y vectorial de 12 tablas, asegurar el aislamiento de datos por RLS, gestionar la búsqueda semántica de campañas y emitir eventos en vivo para el Dashboard.

---

## 1. El Modelo de Datos: 12 Tablas en 4 Dominios

```
[DOMINIO 1: PERSONAS Y CÍRCULO]
  usuarios ──────< miembros_circulo >────── circulos
     │                     │
     └─────────────────────┴───────────────< avisos_circulo

[DOMINIO 2: VERIFICACIONES Y CAMPAÑAS]
  usuarios ──────< verificaciones >────── campanas (pgvector)
                          │
[DOMINIO 3: BANCO DE NÚMEROS]
  usuarios ──────< reportes >────── indicadores ──────< solicitudes_revision
                                         │
                                   numeros_oficiales (lista blanca)

[DOMINIO 4: ENTIDADES Y LLAMADA VERIFICADA]
  entidades ──────< llamadas_registradas (TTL 15 min)
```

---

## 2. Esquema DDL SQL Detallado (`migrations/001_initial_schema.sql`)

### Grupo 1: Personas y Círculo de Confianza
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

CREATE TABLE usuarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    telefono_hash TEXT UNIQUE NOT NULL,      -- HMAC-SHA256(phone, SECRET)
    telefono_cifrado BYTEA,                  -- AES-256-GCM para escribir al usuario
    nombre_corto TEXT,
    consentimiento_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE circulos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre TEXT NOT NULL,                   -- "Familia Pérez", "Empresa XYZ"
    tipo TEXT NOT NULL DEFAULT 'familia',    -- familia | empresa | barrio
    creado_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE miembros_circulo (
    circulo_id UUID REFERENCES circulos(id) ON DELETE CASCADE,
    usuario_id UUID REFERENCES usuarios(id) ON DELETE CASCADE,
    rol TEXT NOT NULL,                      -- protegido | familiar_verificador
    relacion TEXT,                          -- mama, hijo, jefe, etc.
    acepto_at TIMESTAMPTZ,
    PRIMARY KEY (circulo_id, usuario_id)
);

CREATE TABLE avisos_circulo (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    circulo_id UUID REFERENCES circulos(id),
    destinatario_id UUID REFERENCES usuarios(id),
    verificacion_id UUID,
    tipo TEXT NOT NULL,                     -- pregunta_confirmacion | alerta_cadena
    pregunta TEXT NOT NULL,
    respuesta TEXT DEFAULT 'pendiente',     -- si | no | sin_respuesta
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Grupo 2: Verificaciones y Campañas
```sql
CREATE TABLE campanas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre TEXT NOT NULL,                   -- "Falso BancoAndino - valide sus datos"
    modalidad TEXT NOT NULL,
    total_reportes INT DEFAULT 1,
    estado TEXT DEFAULT 'activa',           -- activa | mitigada
    centroide vector(1536),                 -- Embedding representativo de la campaña
    primer_reporte_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE verificaciones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    usuario_id UUID REFERENCES usuarios(id),
    campana_id UUID REFERENCES campanas(id),
    llamada_id UUID,
    canal TEXT NOT NULL,                    -- whatsapp | sms | llamada | compra
    tipo TEXT NOT NULL,                     -- mensaje | captura | voz | numero
    texto_anonimizado TEXT NOT NULL,
    puntaje INT NOT NULL CHECK (puntaje BETWEEN 0 AND 100),
    nivel TEXT NOT NULL,                    -- bajo | sospechoso | alto
    modalidad TEXT,
    senales JSONB NOT NULL DEFAULT '[]'::jsonb,
    rayos_x JSONB NOT NULL DEFAULT '{}'::jsonb,
    huella vector(1536),                    -- Embedding del mensaje para pgvector
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_verificaciones_huella_hnsw ON verificaciones USING hnsw (huella vector_cosine_ops);
```

### Grupo 3: Banco de Números e Indicadores
```sql
CREATE TABLE indicadores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campana_id UUID REFERENCES campanas(id),
    tipo TEXT NOT NULL,                     -- telefono | llave_breb | cuenta | url
    valor_hash TEXT UNIQUE NOT NULL,        -- HMAC-SHA256
    valor_visible TEXT NOT NULL,            -- "+57 601 000 ****00"
    personas_distintas INT DEFAULT 1,
    consultas_rojo INT DEFAULT 0,
    nivel_riesgo INT DEFAULT 0 CHECK (nivel_riesgo BETWEEN 0 AND 100),
    estado TEXT DEFAULT 'activo',           -- activo | en_revision | oficial
    ultimo_visto_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE reportes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    indicador_id UUID REFERENCES indicadores(id) ON DELETE CASCADE,
    usuario_id UUID REFERENCES usuarios(id),
    verificacion_id UUID REFERENCES verificaciones(id),
    modalidad TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_reporte_usuario_indicador UNIQUE (indicador_id, usuario_id) -- 1 voto por persona
);

CREATE TABLE solicitudes_revision (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    indicador_id UUID REFERENCES indicadores(id),
    motivo TEXT NOT NULL,
    estado TEXT DEFAULT 'pendiente',        -- pendiente | aceptada | rechazada
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resuelto_at TIMESTAMPTZ
);

CREATE TABLE numeros_oficiales (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entidad_id UUID,
    nombre TEXT NOT NULL,                   -- "BancoAndino WhatsApp Oficial"
    valor_hash TEXT UNIQUE NOT NULL,
    canal TEXT NOT NULL,                    -- whatsapp | llamada | sms
    fuente TEXT NOT NULL,                   -- registro_directo | pagina_web_verificada
    verificado_por TEXT NOT NULL,
    verificado_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### Grupo 4: Entidades y Llamada Verificada
```sql
CREATE TABLE entidades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre TEXT NOT NULL,                   -- "BancoAndino"
    tipo TEXT NOT NULL,                     -- banco | operador | tienda
    api_key_hash TEXT UNIQUE NOT NULL,
    dominio_oficial TEXT NOT NULL,
    lineas_oficiales TEXT[],
    activa BOOLEAN DEFAULT TRUE
);

CREATE TABLE llamadas_registradas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entidad_id UUID REFERENCES entidades(id),
    telefono_hash TEXT NOT NULL,            -- Teléfono del cliente a quien llaman
    motivo TEXT NOT NULL,
    asesor TEXT NOT NULL,
    codigo_cifrado TEXT NOT NULL,           -- Código de 4 dígitos
    estado TEXT DEFAULT 'esperando',        -- esperando | confirmada | vencida
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    vence_at TIMESTAMPTZ NOT NULL           -- NOW() + interval '15 minutes'
);

CREATE INDEX idx_llamadas_hash_vence ON llamadas_registradas (telefono_hash, vence_at);
```

---

## 3. Las 5 Vistas de Solo Lectura para el Dashboard
El Dashboard Next.js **nunca** lee las tablas base; utiliza vistas anónimas precalculadas:
1. `vista_radar_por_hora`: Conteo de verificaciones y estafas en bloques de 1 hora (últimas 24h).
2. `vista_tipos_de_estafa`: Agrupación por modalidad (suplantación bancaria, falso asesor, paquete retenido, etc.).
3. `vista_campanas_activas`: Lista de campañas con estado activo, volumen de reportes y alerta roja.
4. `vista_llamadas_verificadas`: Registro de llamadas recientes marcadas como "Real - código ok" o "Falsa - colgó".
5. `vista_banco_mas_reportados`: Top de números y llaves Bre-B con mayor nivel de riesgo en los últimos 7 días.

---

## 4. Políticas de Seguridad RLS (Row Level Security)
- Habilitar RLS en las 12 tablas: `ALTER TABLE ... ENABLE ROW LEVEL SECURITY;`
- **Rol Servidor (`service_role`):** Lectura y escritura irrestricta.
- **Rol Público Dashboard (`anon`):** Acceso concedido únicamente a las 5 vistas públicas de agregación. Prohibido el acceso `SELECT` a las tablas `usuarios`, `llamadas_registradas` y `reportes`.
