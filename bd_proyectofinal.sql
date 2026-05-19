-- ============================================================
--  BASE DE DATOS: bd_proyectofinal  (AgroVisión)
--  Ejecutar en MySQL / MariaDB (XAMPP)
-- ============================================================

CREATE DATABASE IF NOT EXISTS bd_proyectofinal
    CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE bd_proyectofinal;

-- ── 1. USUARIOS ─────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario      INT AUTO_INCREMENT PRIMARY KEY,
    nombre_completo VARCHAR(120) NOT NULL,
    correo          VARCHAR(120) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NULL,
    rol             ENUM('admin','soporte','programador') NOT NULL DEFAULT 'soporte',
    activo          TINYINT(1) NOT NULL DEFAULT 1,
    created_at      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

INSERT INTO usuarios (nombre_completo, correo, password_hash, rol) VALUES
    ('Renzo Carranza',  'renzo@agrovision.pe',  '1',      'admin'),
    ('Carlos Mendoza',  'carlos@agrovision.pe', '123456', 'soporte'),
    ('Juan Pérez',      'juan@agrovision.pe',   '123456', 'programador'),
    ('Ana Torres',      'ana@agrovision.pe',    '123456', 'programador'),
    ('Luis Flores',     'luis@agrovision.pe',   '123456', 'soporte');

-- ── 2. TICKETS DE SOPORTE ───────────────────────────────────
CREATE TABLE IF NOT EXISTS tickets (
    id_ticket          INT AUTO_INCREMENT PRIMARY KEY,
    titulo             VARCHAR(200) NOT NULL,
    tipo               ENUM('incidencia','peticion','consulta') NOT NULL,
    prioridad          ENUM('critica','alta','media','baja')    NOT NULL DEFAULT 'media',
    aplicacion         VARCHAR(100) NOT NULL,
    id_solicitante     INT         NOT NULL,
    sla_horas          SMALLINT    NOT NULL DEFAULT 24,
    descripcion        TEXT        NOT NULL,
    estado             ENUM('abierto','en_progreso','resuelto','cerrado','base_proyecto') NOT NULL DEFAULT 'abierto',
    fecha_apertura     DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_resolucion   DATETIME,
    id_agente          INT         NULL,
    notas_resolucion   TEXT        NULL,
    CONSTRAINT fk_ticket_solic  FOREIGN KEY (id_solicitante) REFERENCES usuarios(id_usuario),
    CONSTRAINT fk_ticket_agente FOREIGN KEY (id_agente)      REFERENCES usuarios(id_usuario)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS calificaciones_ticket (
    id_calificacion     INT AUTO_INCREMENT PRIMARY KEY,
    id_ticket           INT NOT NULL UNIQUE,
    estrellas           TINYINT NOT NULL,
    observacion         TEXT NULL,
    fecha_calificacion  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_calif_ticket FOREIGN KEY (id_ticket)
        REFERENCES tickets(id_ticket) ON DELETE CASCADE
) ENGINE=InnoDB;

INSERT INTO tickets (titulo, tipo, prioridad, aplicacion, estado, sla_horas, descripcion, id_solicitante, id_agente, fecha_apertura, fecha_resolucion) VALUES
('Error al exportar PDF de reportes',           'incidencia', 'alta',   'Módulo Reportes',  'resuelto',    8,  'El botón exportar no responde al hacer clic.',        1, 2, NOW() - INTERVAL 25 DAY, NOW() - INTERVAL 24 DAY),
('Acceso denegado en panel de control',         'incidencia', 'critica','Panel Control',    'cerrado',     4,  'Usuario no puede ingresar al sistema.',               1, 5, NOW() - INTERVAL 22 DAY, NOW() - INTERVAL 22 DAY),
('Solicitud de nuevo usuario',                  'peticion',   'media',  'Gestión Usuarios', 'cerrado',     24, 'Agregar nuevo usuario al sistema.',                   1, 2, NOW() - INTERVAL 20 DAY, NOW() - INTERVAL 19 DAY),
('Lentitud al cargar lista de tickets',         'incidencia', 'alta',   'Mesa de Ayuda',    'resuelto',    8,  'La página tarda más de 30 segundos en cargar.',       1, 5, NOW() - INTERVAL 18 DAY, NOW() - INTERVAL 17 DAY),
('Error 500 en login ocasional',                'incidencia', 'critica','Autenticación',    'cerrado',     2,  'Fallo intermitente al iniciar sesión.',                1, 2, NOW() - INTERVAL 15 DAY, NOW() - INTERVAL 15 DAY),
('Cambio de contraseña no funciona',            'incidencia', 'alta',   'Autenticación',    'cerrado',     8,  'Formulario no guarda los cambios.',                   1, 5, NOW() - INTERVAL 12 DAY, NOW() - INTERVAL 11 DAY),
('Reporte mensual no genera correctamente',     'incidencia', 'media',  'Módulo Reportes',  'resuelto',    24, 'El reporte queda en blanco al generarlo.',             1, 2, NOW() - INTERVAL 10 DAY, NOW() - INTERVAL 9 DAY),
('Correo de notificación no llega',             'incidencia', 'media',  'Notificaciones',   'cerrado',     24, 'Los correos de alerta no se envían.',                  1, 5, NOW() - INTERVAL 8 DAY,  NOW() - INTERVAL 7 DAY),
('Dashboard no carga gráficos',                 'incidencia', 'alta',   'Panel Control',    'resuelto',    8,  'Las estadísticas del panel quedan en blanco.',         1, 2, NOW() - INTERVAL 6 DAY,  NOW() - INTERVAL 5 DAY),
('Exportar Excel de tickets falla',             'peticion',   'baja',   'Mesa de Ayuda',    'cerrado',     48, 'El archivo Excel exportado está corrupto.',            1, 5, NOW() - INTERVAL 5 DAY,  NOW() - INTERVAL 4 DAY),
('Duplicado de registros en sistema',           'incidencia', 'media',  'Módulo Proyectos', 'cerrado',     24, 'Algunos proyectos aparecen duplicados en la lista.',   1, 2, NOW() - INTERVAL 3 DAY,  NOW() - INTERVAL 2 DAY),
-- Tickets en progreso
('No se guardan observaciones en ticket',       'incidencia', 'media',  'Mesa de Ayuda',    'en_progreso', 24, 'Las observaciones no persisten al guardar.',           1, 5, NOW() - INTERVAL 3 DAY,  NULL),
('Filtro de fechas no funciona en reportes',    'incidencia', 'alta',   'Módulo Reportes',  'en_progreso', 8,  'El filtro por fecha devuelve resultados vacíos.',      1, 2, NOW() - INTERVAL 2 DAY,  NULL),
-- Tickets abiertos
('Solicitud acceso módulo reportes',            'peticion',   'baja',   'Gestión Usuarios', 'abierto',     48, 'Usuario necesita acceso al módulo de reportes.',       1, NULL, NOW() - INTERVAL 1 DAY, NULL),
('App móvil no sincroniza con servidor',        'incidencia', 'alta',   'App Móvil',        'abierto',     8,  'Los datos no se sincronizan tras reconectar wifi.',    1, NULL, NOW(),                  NULL),
('Consulta sobre proceso de cierre de sprint',  'consulta',   'baja',   'Mesa de Ayuda',    'abierto',     48, '¿Cómo se realiza el cierre formal de un sprint?',     1, NULL, NOW(),                  NULL);


-- ── 3. PROYECTOS DE SOFTWARE ─────────────────────────────────
CREATE TABLE IF NOT EXISTS proyectos (
    id_proyecto        INT AUTO_INCREMENT PRIMARY KEY,
    nombre             VARCHAR(200) NOT NULL,
    id_responsable     INT         NOT NULL,
    estado             ENUM('planificado','en_desarrollo','qa','completado','pausado') NOT NULL DEFAULT 'planificado',
    fecha_inicio       DATE        NOT NULL,
    fecha_fin_plan     DATE        NOT NULL,
    descripcion        TEXT        NOT NULL,
    created_at         DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_proy_resp FOREIGN KEY (id_responsable) REFERENCES usuarios(id_usuario)
) ENGINE=InnoDB;

INSERT INTO proyectos (nombre, descripcion, estado, id_responsable, fecha_inicio, fecha_fin_plan) VALUES
('Sistema AgroVisión v2',      'Módulo de gestión de soporte técnico y proyectos ágiles',   'en_desarrollo', 1, '2025-01-01', '2025-12-31'),
('App Móvil Técnicos',         'Aplicación móvil para gestión de tickets en campo',          'planificado',   1, '2025-02-01', '2025-09-30'),
('Portal de Reportes Gerencia','Dashboard ejecutivo con KPIs de soporte y producción',       'planificado',   1, '2025-03-01', '2025-10-31');

-- ── 4. SPRINTS ────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sprints (
    id_sprint     INT AUTO_INCREMENT PRIMARY KEY,
    id_proyecto   INT NOT NULL,
    nombre        VARCHAR(150) NOT NULL,
    objetivo      TEXT,
    estado        ENUM('planificado','activo','completado','cancelado') NOT NULL DEFAULT 'planificado',
    capacidad_pts INT DEFAULT 0,
    fecha_inicio  DATE NOT NULL,
    fecha_fin     DATE NOT NULL,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sprint_proy FOREIGN KEY (id_proyecto) REFERENCES proyectos(id_proyecto)
) ENGINE=InnoDB;

INSERT INTO sprints (id_proyecto, nombre, objetivo, estado, capacidad_pts, fecha_inicio, fecha_fin) VALUES
(1, 'Sprint 4 – Dashboard KPIs',      'Implementar panel de indicadores para Jefe TI',          'activo', 60, CURDATE() - INTERVAL 10 DAY, CURDATE() + INTERVAL 4 DAY),
(2, 'Sprint 1 – Core Móvil',          'Funcionalidades base de la app móvil para técnicos',      'activo', 40, CURDATE() - INTERVAL 5 DAY,  CURDATE() + INTERVAL 9 DAY),
(3, 'Sprint 1 – Módulo Producción',   'Conectar datos de soporte con reportes de gerencia',      'activo', 50, CURDATE() - INTERVAL 2 DAY,  CURDATE() + INTERVAL 12 DAY);

-- ── 5. HISTORIAS DE USUARIO ───────────────────────────────────
CREATE TABLE IF NOT EXISTS historias (
    id_historia   INT AUTO_INCREMENT PRIMARY KEY,
    id_proyecto   INT NOT NULL,
    id_sprint     INT NULL,
    id_asignado   INT NULL,
    codigo        VARCHAR(30) NOT NULL UNIQUE,
    titulo        VARCHAR(200) NOT NULL,
    tipo          ENUM('funcional','tecnica','bug') NOT NULL DEFAULT 'funcional',
    prioridad     ENUM('critica','alta','media','baja') NOT NULL DEFAULT 'media',
    estado        ENUM('backlog','por_hacer','en_progreso','completada','cancelada') NOT NULL DEFAULT 'backlog',
    story_points  SMALLINT DEFAULT 0,
    created_at    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_historia_proy   FOREIGN KEY (id_proyecto) REFERENCES proyectos(id_proyecto),
    CONSTRAINT fk_historia_sprint FOREIGN KEY (id_sprint)   REFERENCES sprints(id_sprint),
    CONSTRAINT fk_historia_asig   FOREIGN KEY (id_asignado) REFERENCES usuarios(id_usuario)
) ENGINE=InnoDB;

-- ── 6. AVANCES DE PROYECTO (Bitácora de revisiones) ──────────
CREATE TABLE IF NOT EXISTS avances_proyecto (
    id_avance         INT AUTO_INCREMENT PRIMARY KEY,
    id_proyecto       INT NOT NULL,
    id_autor          INT NOT NULL, -- Quién registra el avance (Jefe TI)
    fecha_reporte     DATE NOT NULL, -- Fecha de la revisión
    porcentaje_avance DECIMAL(5,2) NOT NULL DEFAULT 0.00, -- Ej: 45.50%
    estado_salud      ENUM('a_tiempo', 'en_riesgo', 'retrasado') NOT NULL DEFAULT 'a_tiempo',
    logros_periodo    TEXT NOT NULL, -- ¿Qué se avanzó?
    pendientes_next   TEXT,          -- ¿Qué sigue?
    created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_avance_proy  FOREIGN KEY (id_proyecto) REFERENCES proyectos(id_proyecto) ON DELETE CASCADE,
    CONSTRAINT fk_avance_autor FOREIGN KEY (id_autor)    REFERENCES usuarios(id_usuario)
) ENGINE=InnoDB;


-- Registro de prueba para visualizarlo luego
INSERT INTO avances_proyecto (id_proyecto, id_autor, fecha_reporte, porcentaje_avance, estado_salud, logros_periodo) 
VALUES (1, 1, CURDATE(), 43.00, 'a_tiempo', 'Finalización del módulo de reportes base y conexión con la base de datos.');

INSERT INTO historias (id_proyecto, id_sprint, id_asignado, codigo, titulo, tipo, prioridad, estado, story_points) VALUES
-- Sprint 1 – Dashboard KPIs (proyecto 1)
(1, 1, 3, 'HU-001', 'Ver KPIs de tickets en tiempo real',       'funcional', 'alta',   'completada',  8),
(1, 1, 3, 'HU-002', 'Gráfico tendencia mensual de tickets',     'funcional', 'alta',   'completada',  5),
(1, 1, 2, 'HU-003', 'Filtro de indicadores por fecha',          'funcional', 'media',  'completada',  3),
(1, 1, 2, 'HU-004', 'KPI SLA cumplido en tiempo real',          'funcional', 'alta',   'en_progreso', 8),
(1, 1, 3, 'HU-005', 'Carga de trabajo por programador',         'funcional', 'media',  'en_progreso', 5),
(1, 1, 2, 'HU-006', 'Exportar reporte PDF de indicadores',      'funcional', 'baja',   'por_hacer',   5),
(1, 1, 3, 'HU-007', 'Alertas automáticas tickets críticos',     'funcional', 'alta',   'backlog',     8),
-- Sprint 2 – Core Móvil (proyecto 2)
(2, 2, 3, 'HU-008', 'Login móvil con cuenta corporativa',       'funcional', 'critica','completada',  8),
(2, 2, 2, 'HU-009', 'Ver tickets asignados desde móvil',        'funcional', 'alta',   'en_progreso', 8),
(2, 2, 3, 'HU-010', 'Actualizar estado de ticket desde móvil',  'funcional', 'alta',   'en_progreso', 5),
(2, 2, 2, 'HU-011', 'Notificaciones push para tickets nuevos',  'funcional', 'media',  'por_hacer',   5),
(2, 2, 3, 'HU-012', 'Modo offline para lectura de tickets',     'tecnica',   'media',  'backlog',     8),
-- Sprint 3 – Módulo Producción (proyecto 3)
(3, 3, 2, 'HU-013', 'Dashboard ejecutivo con KPIs soporte',     'funcional', 'alta',   'en_progreso', 8),
(3, 3, 3, 'HU-014', 'Gráfico de tickets resueltos por mes',     'funcional', 'media',  'por_hacer',   5),
(3, 3, 2, 'HU-015', 'Reporte semanal automático por correo',    'funcional', 'media',  'backlog',     5),
(3, 3, 3, 'HU-016', 'Comparativo SLA vs año anterior',          'funcional', 'alta',   'backlog',     8);


-- ── TABLA INTERMEDIA: ASIGNADOS A PROYECTO (muchos a muchos) ─
CREATE TABLE IF NOT EXISTS asignado (
    id_proyecto INT NOT NULL,
    id_usuario  INT NOT NULL,
    PRIMARY KEY (id_proyecto, id_usuario),
    CONSTRAINT fk_asig_proyecto FOREIGN KEY (id_proyecto) REFERENCES proyectos(id_proyecto) ON DELETE CASCADE,
    CONSTRAINT fk_asig_usuario  FOREIGN KEY (id_usuario)  REFERENCES usuarios(id_usuario)   ON DELETE CASCADE
) ENGINE=InnoDB;

-- Poblar la tabla con los responsables ya existentes en proyectos
INSERT IGNORE INTO asignado (id_proyecto, id_usuario)
SELECT id_proyecto, id_responsable FROM proyectos;

-- ============================================================
--  FIN DEL SCRIPT
-- ============================================================