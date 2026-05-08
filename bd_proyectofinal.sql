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
    id_agente          INT         NULL,
    notas_resolucion   TEXT        NULL,
    CONSTRAINT fk_ticket_solic  FOREIGN KEY (id_solicitante) REFERENCES usuarios(id_usuario),
    CONSTRAINT fk_ticket_agente FOREIGN KEY (id_agente)      REFERENCES usuarios(id_usuario)
) ENGINE=InnoDB;

-- Si la tabla ya existe en tu BD, ejecuta esto en lugar del CREATE:
-- ALTER TABLE tickets ADD COLUMN id_agente INT NULL, ADD COLUMN notas_resolucion TEXT NULL;
-- ALTER TABLE tickets ADD CONSTRAINT fk_ticket_agente FOREIGN KEY (id_agente) REFERENCES usuarios(id_usuario);

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

INSERT INTO tickets (titulo, tipo, prioridad, aplicacion, estado, sla_horas, descripcion, id_solicitante, id_agente, fecha_apertura, fecha_resolucion) VALUES

-- Tickets resueltos (generan datos en tendencia y SLA)
('Error al exportar PDF de evaluaciones',       'incidencia', 'alta',   'Módulo Campo',     'resuelto', 8,  'El botón exportar no responde al hacer clic.',        1, 2, NOW() - INTERVAL 25 DAY, NOW() - INTERVAL 24 DAY),
('Acceso denegado en panel de control',         'incidencia', 'critica','Panel Control',    'cerrado',  4,  'Usuario no puede ingresar al sistema.',               1, 5, NOW() - INTERVAL 22 DAY, NOW() - INTERVAL 22 DAY),
('Solicitud de nuevo usuario inspector',        'peticion',   'media',  'Gestión Usuarios', 'cerrado',  24, 'Agregar nuevo inspector al sistema.',                 1, 2, NOW() - INTERVAL 20 DAY, NOW() - INTERVAL 19 DAY),
('Lentitud al cargar lista de evaluaciones',    'incidencia', 'alta',   'Módulo Campo',     'resuelto', 8,  'La página tarda más de 30 segundos en cargar.',      1, 5, NOW() - INTERVAL 18 DAY, NOW() - INTERVAL 17 DAY),
('Error 500 en login ocasional',                'incidencia', 'critica','Autenticación',    'cerrado',  2,  'Fallo intermitente al iniciar sesión.',               1, 2, NOW() - INTERVAL 15 DAY, NOW() - INTERVAL 15 DAY),
('Cambio de contraseña no funciona',            'incidencia', 'alta',   'Autenticación',    'cerrado',  8,  'Formulario no guarda los cambios.',                   1, 5, NOW() - INTERVAL 12 DAY, NOW() - INTERVAL 11 DAY),
('Reporte mensual de plagas no genera',         'incidencia', 'media',  'Módulo Campo',     'resuelto', 24, 'El reporte queda en blanco al generarlo.',            1, 2, NOW() - INTERVAL 10 DAY, NOW() - INTERVAL 9 DAY),
('Correo de notificación no llega',             'incidencia', 'media',  'Notificaciones',   'cerrado',  24, 'Los correos de alerta no se envían.',                 1, 5, NOW() - INTERVAL 8 DAY,  NOW() - INTERVAL 7 DAY),
('Dashboard no carga gráficos',                 'incidencia', 'alta',   'Panel Control',    'resuelto', 8,  'Las estadísticas del panel quedan en blanco.',        1, 2, NOW() - INTERVAL 6 DAY,  NOW() - INTERVAL 5 DAY),
('Duplicado de lotes en sistema',               'incidencia', 'media',  'Módulo Campo',     'cerrado',  24, 'Algunos lotes aparecen duplicados en la lista.',      1, 5, NOW() - INTERVAL 5 DAY,  NOW() - INTERVAL 4 DAY),
('Exportar Excel de tickets falla',             'peticion',   'baja',   'Mesa de Ayuda',    'cerrado',  48, 'El archivo Excel exportado está corrupto.',           1, 2, NOW() - INTERVAL 3 DAY,  NOW() - INTERVAL 2 DAY),

-- Tickets en progreso
('No se guardan observaciones en ticket',       'incidencia', 'media',  'Mesa de Ayuda',    'en_progreso', 24, 'Las observaciones no persisten al guardar.',       1, 5, NOW() - INTERVAL 3 DAY,  NULL),
('Filtro de fechas no funciona',                'incidencia', 'alta',   'Módulo Campo',     'en_progreso', 8,  'El filtro por fecha devuelve resultados vacíos.',   1, 2, NOW() - INTERVAL 2 DAY,  NULL),

-- Tickets abiertos
('Solicitud acceso módulo reportes',            'peticion',   'baja',   'Gestión Usuarios', 'abierto',  48, 'Usuario necesita acceso al módulo de reportes.',      1, NULL, NOW() - INTERVAL 1 DAY,  NULL),
('Error al imprimir evaluación de campo',       'incidencia', 'media',  'Módulo Campo',     'abierto',  24, 'La impresión sale con formato incorrecto.',           1, NULL, NOW(),                   NULL),
('Consulta sobre proceso de cierre de sprint',  'consulta',   'baja',   'Mesa de Ayuda',    'abierto',  48, '¿Cómo se realiza el cierre formal de un sprint?',    1, NULL, NOW(),                   NULL);

INSERT INTO proyectos (nombre, descripcion, estado, id_responsable, fecha_inicio, fecha_fin_plan) VALUES
('Sistema AgroVisión v2',     'Módulo de gestión de campo y soporte técnico',   'activo', 1, '2025-01-01', '2025-12-31'),
('App Móvil Inspectores',     'Aplicación móvil para registro de evaluaciones', 'activo', 1, '2025-02-01', '2025-09-30'),
('Portal de Reportes Gerencia','Dashboard ejecutivo con KPIs de producción',    'activo', 1, '2025-03-01', '2025-10-31');
 
-- Sprints activos
INSERT INTO sprints (id_proyecto, nombre, objetivo, estado, capacidad_pts, fecha_inicio, fecha_fin) VALUES
(1, 'Sprint 4 – Dashboard KPIs',      'Implementar panel de indicadores para Jefe TI',         'activo', 60, CURDATE() - INTERVAL 10 DAY, CURDATE() + INTERVAL 4 DAY),
(2, 'Sprint 2 – Registro Offline',    'Permitir registro de evaluaciones sin conexión a internet','activo', 40, CURDATE() - INTERVAL 5 DAY,  CURDATE() + INTERVAL 9 DAY),
(3, 'Sprint 1 – Módulo Producción',   'Conectar datos de campo con reportes de gerencia',       'activo', 50, CURDATE() - INTERVAL 2 DAY,  CURDATE() + INTERVAL 12 DAY);
 
-- Historias para Sprint 1 (id_sprint=1)
INSERT INTO historias (id_proyecto, id_sprint, id_asignado, codigo, titulo, tipo, prioridad, estado, story_points) VALUES
(1, 1, 2, 'HU-001', 'Ver KPIs de tickets en tiempo real',       'funcional', 'alta',   'completada',  8),
(1, 1, 2, 'HU-002', 'Gráfico tendencia mensual de tickets',     'funcional', 'alta',   'completada',  5),
(1, 1, 5, 'HU-003', 'Filtro de indicadores por fecha',          'funcional', 'media',  'completada',  3),
(1, 1, 5, 'HU-004', 'KPI SLA cumplido en tiempo real',          'funcional', 'alta',   'en_progreso', 8),
(1, 1, 2, 'HU-005', 'Carga de trabajo por programador',         'funcional', 'media',  'en_progreso', 5),
(1, 1, 5, 'HU-006', 'Exportar reporte PDF de indicadores',      'funcional', 'baja',   'por_hacer',   5),
(1, 1, 2, 'HU-007', 'Alertas automáticas tickets críticos',     'funcional', 'alta',   'backlog',     8);
 
-- Historias para Sprint 2 (id_sprint=2)
INSERT INTO historias (id_proyecto, id_sprint, id_asignado, codigo, titulo, tipo, prioridad, estado, story_points) VALUES
(2, 2, 2, 'HU-008', 'Registro evaluación sin internet',         'funcional', 'critica', 'completada',  8),
(2, 2, 5, 'HU-009', 'Sincronización automática al reconectar',  'tecnica',   'alta',    'en_progreso', 8),
(2, 2, 2, 'HU-010', 'Caché local de lotes y plagas',            'tecnica',   'media',   'en_progreso', 5),
(2, 2, 5, 'HU-011', 'Notificación de sync exitoso',             'funcional', 'baja',    'por_hacer',   3),
(2, 2, 2, 'HU-012', 'Manejo de conflictos de datos offline',    'tecnica',   'alta',    'backlog',     8);
 
-- Historias para Sprint 3 (id_sprint=3)
INSERT INTO historias (id_proyecto, id_sprint, id_asignado, codigo, titulo, tipo, prioridad, estado, story_points) VALUES
(3, 3, 5, 'HU-013', 'Dashboard ejecutivo con KPIs producción',  'funcional', 'alta',   'en_progreso', 8),
(3, 3, 2, 'HU-014', 'Gráfico de hectáreas monitoreadas',        'funcional', 'media',  'por_hacer',   5),
(3, 3, 5, 'HU-015', 'Reporte semanal automático por correo',    'funcional', 'media',  'backlog',     5),
(3, 3, 2, 'HU-016', 'Comparativo producción vs año anterior',   'funcional', 'alta',   'backlog',     8);

-- ============================================================
--  FIN DEL SCRIPT
-- ============================================================
