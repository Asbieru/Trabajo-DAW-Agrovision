-- ============================================================
--  BASE DE DATOS: bd_proyectofinal  (AgroVisión)
--  Ejecutar en MySQL / MariaDB
-- ============================================================

CREATE DATABASE IF NOT EXISTS bd_proyectofinal
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE bd_proyectofinal;

-- ── 1. USUARIOS ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario      INT AUTO_INCREMENT PRIMARY KEY,
    nombre_completo VARCHAR(120) NOT NULL,
    correo          VARCHAR(120) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NULL,                          -- ← AGREGADO
    rol             ENUM('inspector','analista','admin','soporte') NOT NULL DEFAULT 'inspector',
    activo          TINYINT(1) NOT NULL DEFAULT 1,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Datos de ejemplo
INSERT INTO usuarios (nombre_completo, correo, password_hash, rol) VALUES
    ('Renzo Carranza',   'renzo@agrovision.pe', '1',   'admin'),
    ('María Quispe',     'maria@agrovision.pe', '123456',  'inspector'),
    ('Luis Flores',      'luis@agrovision.pe', '123456',    'inspector'),
    ('Ana Torres',       'ana@agrovision.pe', '123456',    'analista'),
    ('Carlos Mendoza',   'carlos@agrovision.pe','123456',   'soporte');

-- ── 2. LOTES ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS lotes (
    id_lote        INT AUTO_INCREMENT PRIMARY KEY,
    codigo_lote    VARCHAR(20)  NOT NULL UNIQUE,
    nombre_fundo   VARCHAR(100) NOT NULL,
    hectareas      DECIMAL(8,2),
    cultivo        VARCHAR(80),
    activo         TINYINT(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB;

INSERT INTO lotes (codigo_lote, nombre_fundo, hectareas, cultivo) VALUES
    ('L-001', 'Fundo El Milagro',   45.50, 'Espárrago'),
    ('L-002', 'Fundo San Martín',   30.00, 'Palta'),
    ('L-003', 'Fundo La Esperanza', 60.25, 'Arándano'),
    ('L-004', 'Fundo El Verde',     22.00, 'Espárrago');

-- ── 3. PLAGAS ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS plagas (
    id_plaga       INT AUTO_INCREMENT PRIMARY KEY,
    nombre         VARCHAR(120) NOT NULL,
    nombre_cientifico VARCHAR(150),
    nivel_riesgo   ENUM('bajo','medio','alto','critico') NOT NULL DEFAULT 'medio',
    descripcion    TEXT
) ENGINE=InnoDB;

INSERT INTO plagas (nombre, nombre_cientifico, nivel_riesgo) VALUES
    ('Mosca blanca',     'Bemisia tabaci',        'alto'),
    ('Pulgón verde',     'Acyrthosiphon pisum',   'medio'),
    ('Trips',            'Frankliniella occidentalis', 'alto'),
    ('Arañita roja',     'Tetranychus urticae',   'medio'),
    ('Nematodo del suelo','Meloidogyne incognita', 'critico');

-- ── 4. EVALUACIONES DE CAMPO ────────────────────────────────
CREATE TABLE IF NOT EXISTS evaluaciones_campo (
    id_evaluacion      INT AUTO_INCREMENT PRIMARY KEY,
    id_lote            INT NOT NULL,
    id_plaga           INT NOT NULL,
    id_inspector       INT NOT NULL,
    fecha_evaluacion   DATE        NOT NULL,
    hora_evaluacion    TIME,
    plantas_evaluadas  SMALLINT    NOT NULL CHECK (plantas_evaluadas > 0),
    plantas_afectadas  SMALLINT    NOT NULL DEFAULT 0,
    nivel_incidencia   ENUM('bajo','medio','alto') NOT NULL,
    foto_url           VARCHAR(500),
    observaciones      TEXT,
    created_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_eval_lote     FOREIGN KEY (id_lote)      REFERENCES lotes(id_lote),
    CONSTRAINT fk_eval_plaga    FOREIGN KEY (id_plaga)     REFERENCES plagas(id_plaga),
    CONSTRAINT fk_eval_insp     FOREIGN KEY (id_inspector) REFERENCES usuarios(id_usuario)
) ENGINE=InnoDB;

-- ── 5. TICKETS DE SOPORTE ───────────────────────────────────
CREATE TABLE IF NOT EXISTS tickets (
    id_ticket          INT AUTO_INCREMENT PRIMARY KEY,
    titulo             VARCHAR(200) NOT NULL,
    tipo               ENUM('incidencia','peticion','consulta') NOT NULL,
    prioridad          ENUM('critica','alta','media','baja')    NOT NULL DEFAULT 'media',
    aplicacion         VARCHAR(100) NOT NULL,
    id_solicitante     INT         NOT NULL,
    sla_horas          SMALLINT    NOT NULL DEFAULT 24,
    descripcion        TEXT        NOT NULL,
    estado             ENUM('abierto','en_progreso','resuelto','cerrado') NOT NULL DEFAULT 'abierto',
    fecha_apertura     DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_resolucion   DATETIME,
    CONSTRAINT fk_ticket_solic  FOREIGN KEY (id_solicitante) REFERENCES usuarios(id_usuario)
) ENGINE=InnoDB;

-- ── 6. PROYECTOS DE SOFTWARE ─────────────────────────────────
CREATE TABLE IF NOT EXISTS proyectos (
    id_proyecto        INT AUTO_INCREMENT PRIMARY KEY,
    nombre             VARCHAR(200) NOT NULL,
    id_responsable     INT         NOT NULL,
    estado             ENUM('planificado','en_desarrollo','qa','completado','pausado') NOT NULL DEFAULT 'planificado',
    fecha_inicio       DATE        NOT NULL,
    fecha_fin_plan     DATE        NOT NULL,
    descripcion        TEXT        NOT NULL,
    created_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_proy_resp     FOREIGN KEY (id_responsable) REFERENCES usuarios(id_usuario)
) ENGINE=InnoDB;

-- ============================================================
--  FIN DEL SCRIPT
-- ============================================================
