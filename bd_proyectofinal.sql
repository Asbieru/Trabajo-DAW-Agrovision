-- ============================================================
-- BASE DE DATOS: bd_proyectofinal
-- ============================================================

CREATE DATABASE IF NOT EXISTS bd_proyectofinal
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE bd_proyectofinal;

-- ============================================================
-- TABLA USUARIOS
-- ============================================================

CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario INT AUTO_INCREMENT PRIMARY KEY,
    nombre_completo VARCHAR(120) NOT NULL,
    apellido VARCHAR(120),
    edad INT,
    dni VARCHAR(15),
    direccion VARCHAR(255),
    correo VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255),
    rol ENUM('admin','soporte','programador','agente') NOT NULL DEFAULT 'soporte',
    foto_url VARCHAR(500),
    activo TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

INSERT INTO usuarios
(nombre_completo, apellido, edad, dni, direccion, correo, password_hash, rol, foto_url)
VALUES
('Renzo Carranza', 'Carranza López', 29, '74123456', 'Av. La Molina 342, Lima', 'renzo@agrovision.pe', '1', 'admin', NULL),
('Carlos Mendoza', 'Mendoza Quispe', 34, '72345678', 'Jr. Huallaga 198, Cercado de Lima', 'carlos@agrovision.pe', '123456', 'soporte', NULL),
('Juan Pérez', 'Pérez Salas', 26, '71234567', 'Calle Los Cedros 55, San Borja', 'juan@agrovision.pe', '123456', 'programador', NULL),
('Ana Torres', 'Torres Vásquez', 31, '73456789', 'Av. Arequipa 1250, Miraflores', 'ana@agrovision.pe', '123456', 'programador', NULL),
('Luis Flores', 'Flores Huanca', 28, '70987654', 'Psje. Los Pinos 12, Surco', 'luis@agrovision.pe', '123456', 'soporte', NULL);

-- ============================================================
-- TABLA APLICACIONES
-- ============================================================

CREATE TABLE IF NOT EXISTS aplicaciones (
    id_aplicacion INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    peso INT NOT NULL DEFAULT 1,
    descripcion TEXT NULL,
    participantes_promedio INT NOT NULL DEFAULT 1
) ENGINE=InnoDB;

INSERT INTO aplicaciones (nombre, peso, descripcion, participantes_promedio) VALUES
('Sistema Empaque',    5, 'Sistema de control de empaque y etiquetado', 8),
('App Móvil Campo',    4, 'Aplicación móvil para trabajadores de campo', 12),
('API Ventas',         4, 'API de integración de ventas', 6),
('Portal RRHH',        3, 'Portal de recursos humanos', 5),
('Dashboard BI',       3, 'Dashboard de inteligencia de negocio', 4),
('Reportes',           2, 'Sistema de reportes personalizados', 3),
('Panel',              4, 'Panel de administración general', 7),
('Usuarios',           3, 'Gestión de usuarios y permisos', 4),
('Mesa Ayuda',         5, 'Mesa de ayuda y soporte técnico', 10),
('Autenticación',      5, 'Sistema de autenticación y SSO', 6);

-- ============================================================
-- TABLA TICKETS
-- ============================================================

CREATE TABLE IF NOT EXISTS tickets (
    id_ticket INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    tipo ENUM('incidencia','peticion','consulta') NOT NULL,
    prioridad ENUM('critica','alta','media','baja') NOT NULL DEFAULT 'media',
    intensidad ENUM('critica','alta','media','baja') NOT NULL DEFAULT 'media',
    id_solicitante INT NOT NULL,
    id_aplicacion INT NOT NULL,
    sla_horas SMALLINT NOT NULL DEFAULT 24,
    estado ENUM('solicitado','en_progreso','resuelto','cerrado','cancelado') NOT NULL DEFAULT 'solicitado',
    f_registro DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    f_cierre DATETIME NULL,
    CONSTRAINT fk_ticket_solic FOREIGN KEY (id_solicitante) REFERENCES usuarios(id_usuario),
    CONSTRAINT fk_ticket_aplic FOREIGN KEY (id_aplicacion) REFERENCES aplicaciones(id_aplicacion)
) ENGINE=InnoDB;

-- ============================================================
-- TABLA DETALLE_TICKET
-- ============================================================

CREATE TABLE IF NOT EXISTS detalle_ticket (
    id_detalle INT AUTO_INCREMENT PRIMARY KEY,
    id_ticket INT NOT NULL UNIQUE,
    f_asignacion_agente DATETIME NULL,
    id_agente INT NULL,
    f_solucion DATETIME NULL,
    f_revision DATETIME NULL,
    link_img_descripcion TEXT NULL,
    descripcion TEXT NOT NULL,
    notas_resolucion TEXT NULL,
    link_img_resolucion TEXT NULL,
    CONSTRAINT fk_detalle_ticket FOREIGN KEY (id_ticket)
        REFERENCES tickets(id_ticket) ON DELETE CASCADE,
    CONSTRAINT fk_detalle_agente FOREIGN KEY (id_agente)
        REFERENCES usuarios(id_usuario)
) ENGINE=InnoDB;

-- ============================================================
-- CALIFICACIONES
-- ============================================================

CREATE TABLE IF NOT EXISTS calificaciones_ticket (
    id_calificacion INT AUTO_INCREMENT PRIMARY KEY,
    id_ticket INT NOT NULL UNIQUE,
    estrellas TINYINT NOT NULL,
    observacion TEXT,
    fecha_calificacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_calif_ticket FOREIGN KEY (id_ticket)
    REFERENCES tickets(id_ticket) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- TABLA PROYECTOS
-- ============================================================

CREATE TABLE IF NOT EXISTS proyectos (
    id_proyecto INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    id_responsable INT NOT NULL,
    estado ENUM('planificado','en_desarrollo','qa','completado','pausado', 'eliminado')
    NOT NULL DEFAULT 'planificado',
    fecha_inicio DATE NOT NULL,
    fecha_fin_plan DATE NOT NULL,
    descripcion TEXT NOT NULL,
    estado2 TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_proy_resp FOREIGN KEY (id_responsable)
    REFERENCES usuarios(id_usuario)
) ENGINE=InnoDB;

INSERT INTO proyectos
(nombre, descripcion, estado, id_responsable, fecha_inicio, fecha_fin_plan)
VALUES
('Sistema AgroVision v2','Sistema de soporte','en_desarrollo',1,'2025-01-01','2025-12-31'),
('App Movil Tecnicos','Aplicacion movil','planificado',1,'2025-02-01','2025-09-30'),
('Portal Reportes','Dashboard gerencial','planificado',1,'2025-03-01','2025-10-31');

-- ============================================================
-- TABLA SPRINTS
-- ============================================================

CREATE TABLE IF NOT EXISTS sprints (
    id_sprint INT AUTO_INCREMENT PRIMARY KEY,
    id_proyecto INT NOT NULL,
    nombre VARCHAR(150) NOT NULL,
    objetivo TEXT,
    estado ENUM('planificado','activo','completado','cancelado')
    NOT NULL DEFAULT 'planificado',
    capacidad_pts INT DEFAULT 0,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sprint_proy FOREIGN KEY (id_proyecto)
    REFERENCES proyectos(id_proyecto)
) ENGINE=InnoDB;

INSERT INTO sprints
(id_proyecto, nombre, objetivo, estado, capacidad_pts, fecha_inicio, fecha_fin)
VALUES
(1,'Sprint KPIs','Dashboard KPIs','activo',60,CURDATE(),CURDATE()+INTERVAL 10 DAY),
(2,'Sprint Movil','Core App','activo',40,CURDATE(),CURDATE()+INTERVAL 10 DAY);


-- ============================================================
-- TABLA AVANCES
-- ============================================================

CREATE TABLE IF NOT EXISTS avances_proyecto (
    id_avance INT AUTO_INCREMENT PRIMARY KEY,
    id_proyecto INT NOT NULL,
    id_autor INT NOT NULL,
    fecha_reporte DATE NOT NULL,
    porcentaje_avance DECIMAL(5,2) NOT NULL DEFAULT 0.00,
    estado_salud ENUM('a_tiempo','en_riesgo','retrasado')
    NOT NULL DEFAULT 'a_tiempo',
    logros_periodo TEXT NOT NULL,
    pendientes_next TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_avance_proy FOREIGN KEY (id_proyecto)
    REFERENCES proyectos(id_proyecto) ON DELETE CASCADE,
    CONSTRAINT fk_avance_autor FOREIGN KEY (id_autor)
    REFERENCES usuarios(id_usuario)
) ENGINE=InnoDB;

INSERT INTO avances_proyecto
(id_proyecto, id_autor, fecha_reporte, porcentaje_avance, estado_salud, logros_periodo)
VALUES
(1,1,CURDATE(),43.00,'a_tiempo','Modulo reportes finalizado');

-- ============================================================
-- TABLA ASIGNADO
-- ============================================================

CREATE TABLE IF NOT EXISTS asignado (
    id_proyecto INT NOT NULL,
    id_usuario INT NOT NULL,
    PRIMARY KEY (id_proyecto, id_usuario),
    CONSTRAINT fk_asig_proyecto FOREIGN KEY (id_proyecto)
    REFERENCES proyectos(id_proyecto) ON DELETE CASCADE,
    CONSTRAINT fk_asig_usuario FOREIGN KEY (id_usuario)
    REFERENCES usuarios(id_usuario) ON DELETE CASCADE
) ENGINE=InnoDB;

INSERT IGNORE INTO asignado (id_proyecto, id_usuario)
SELECT id_proyecto, id_responsable FROM proyectos;

-- ============================================================
-- TABLA ACTIVIDADES
-- ============================================================

CREATE TABLE IF NOT EXISTS actividades (
    id_actividad INT AUTO_INCREMENT PRIMARY KEY,
    id_proyecto INT NOT NULL,
    id_sprint INT NULL,
    id_asignado INT NULL,
    codigo VARCHAR(30) NOT NULL UNIQUE,
    titulo VARCHAR(200) NOT NULL,
    prioridad ENUM('critica','alta','media','baja') NOT NULL DEFAULT 'media',
    estado ENUM('backlog','por_hacer','en_progreso','completada','cancelada','eliminado')
    NOT NULL DEFAULT 'backlog',
    story_points SMALLINT DEFAULT 0,
    estado2 TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_act_proy FOREIGN KEY (id_proyecto)
    REFERENCES proyectos(id_proyecto),
    CONSTRAINT fk_act_sprint FOREIGN KEY (id_sprint)
    REFERENCES sprints(id_sprint),
    CONSTRAINT fk_act_asig FOREIGN KEY (id_asignado)
    REFERENCES usuarios(id_usuario)
) ENGINE=InnoDB;

INSERT INTO actividades
(id_proyecto, id_sprint, id_asignado, codigo, titulo, prioridad, estado, story_points)
VALUES
(1,1,3,'ACT-001','Panel KPIs','alta','completada',8),
(1,1,2,'ACT-002','Exportar PDF','media','en_progreso',5),
(2,2,3,'ACT-003','Login movil','critica','completada',8);

-- ============================================================
-- DATOS DE EJEMPLO: TICKETS + DETALLES
-- ============================================================

INSERT INTO tickets (id_ticket, titulo, tipo, prioridad, intensidad, id_solicitante, id_aplicacion, sla_horas, estado, f_registro, f_cierre)
VALUES
(1, 'Error al exportar PDF',  'incidencia', 'alta',   'alta',   1, 6, 8,  'cerrado',   '2025-05-01 10:00:00', '2025-05-03 15:00:00'),
(2, 'Acceso denegado',        'incidencia', 'critica','critica',1, 8, 4,  'cerrado',   '2025-05-02 09:00:00', '2025-05-02 18:00:00'),
(3, 'Nuevo usuario',          'peticion',   'media',  'baja',   1,10,24, 'cerrado',   '2025-05-03 08:00:00', '2025-05-05 12:00:00'),
(4, 'Lentitud tickets',       'incidencia', 'alta',   'alta',   1, 9, 8,  'resuelto',  '2025-05-04 14:00:00', NULL),
(5, 'Error login',            'incidencia', 'critica','critica',1,10, 2,  'cerrado',   '2025-05-05 07:00:00', '2025-05-05 16:00:00');

INSERT INTO detalle_ticket (id_ticket, f_asignacion_agente, id_agente, f_solucion, f_revision, descripcion, notas_resolucion)
VALUES
(1, '2025-05-01 11:00:00', 2, '2025-05-03 14:00:00', '2025-05-03 15:00:00', 'No exporta PDF', 'Se corrigió la librería de exportación'),
(2, '2025-05-02 10:00:00', 5, '2025-05-02 17:00:00', '2025-05-02 18:00:00', 'No puede ingresar', 'Se restauró acceso desde el panel'),
(3, '2025-05-03 09:00:00', 2, '2025-05-05 11:00:00', '2025-05-05 12:00:00', 'Crear usuario', 'Usuario creado exitosamente'),
(4, '2025-05-04 15:00:00', 5, '2025-05-06 10:00:00', NULL, 'Carga lenta', 'Se optimizaron consultas, pendiente revisión'),
(5, '2025-05-05 08:00:00', 2, '2025-05-05 15:00:00', '2025-05-05 16:00:00', 'Error 500 login', 'Corregido error en microservicio de autenticación');

INSERT INTO calificaciones_ticket (id_ticket, estrellas, observacion) VALUES
(1, 4, 'Atencion buena, se resolvio con seguimiento.'),
(4, 5, 'Excelente atencion, solucion rapida y clara.');

-- ============================================================
-- FIN
-- ============================================================
