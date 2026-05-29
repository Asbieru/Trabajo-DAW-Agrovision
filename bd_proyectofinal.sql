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
    rol ENUM('admin','soporte','programador') NOT NULL DEFAULT 'soporte',
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
-- TABLA TICKETS
-- ============================================================

CREATE TABLE IF NOT EXISTS tickets (
    id_ticket INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    tipo ENUM('incidencia','peticion','consulta') NOT NULL,
    prioridad ENUM('critica','alta','media','baja') NOT NULL DEFAULT 'media',
    aplicacion VARCHAR(100) NOT NULL,
    id_solicitante INT NOT NULL,
    sla_horas SMALLINT NOT NULL DEFAULT 24,
    descripcion TEXT NOT NULL,
    estado ENUM('abierto','en_progreso','resuelto','cerrado','base_proyecto') NOT NULL DEFAULT 'abierto',
    fecha_apertura DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_resolucion DATETIME,
    id_agente INT NULL,
    notas_resolucion TEXT NULL,
    CONSTRAINT fk_ticket_solic FOREIGN KEY (id_solicitante) REFERENCES usuarios(id_usuario),
    CONSTRAINT fk_ticket_agente FOREIGN KEY (id_agente) REFERENCES usuarios(id_usuario)
) ENGINE=InnoDB;

INSERT INTO tickets
(titulo, tipo, prioridad, aplicacion, estado, sla_horas, descripcion, id_solicitante, id_agente)
VALUES
('Error al exportar PDF','incidencia','alta','Reportes','resuelto',8,'No exporta PDF',1,2),
('Acceso denegado','incidencia','critica','Panel','cerrado',4,'No puede ingresar',1,5),
('Nuevo usuario','peticion','media','Usuarios','cerrado',24,'Crear usuario',1,2),
('Lentitud tickets','incidencia','alta','Mesa Ayuda','resuelto',8,'Carga lenta',1,5),
('Error login','incidencia','critica','Autenticación','cerrado',2,'Error 500 login',1,2);

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

INSERT INTO calificaciones_ticket
(id_ticket, estrellas, observacion)
VALUES
(1, 4, 'Atencion buena, se resolvio con seguimiento.'),
(4, 5, 'Excelente atencion, solucion rapida y clara.');

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
(nombre, descripcion, estado, id_responsable, fecha_inicio, fecha_fin_plan, estado2)
VALUES
('Sistema AgroVision v2','Sistema de soporte','en_desarrollo',1,'2025-01-01','2025-12-31',1),
('App Movil Tecnicos','Aplicacion movil','planificado',1,'2025-02-01','2025-09-30',1),
('Portal Reportes','Dashboard gerencial','planificado',1,'2025-03-01','2025-10-31',1);

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
    estado ENUM('backlog','por_hacer','en_progreso','completada','cancelada')
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
(id_proyecto, id_sprint, id_asignado, codigo, titulo, prioridad, estado, story_points, estado2)
VALUES
(1,1,3,'ACT-001','Panel KPIs','alta','completada',8,1),
(1,1,2,'ACT-002','Exportar PDF','media','en_progreso',5,1),
(2,2,3,'ACT-003','Login movil','critica','completada',8,1);

-- ============================================================
-- FIN
-- ============================================================
