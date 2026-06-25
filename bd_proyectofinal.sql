-- ============================================================
-- BASE DE DATOS: bd_proyectofinal
-- ============================================================

CREATE DATABASE IF NOT EXISTS bd_proyectofinal
CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE bd_proyectofinal;

-- ============================================================
-- TABLA ROL
-- ============================================================

CREATE TABLE IF NOT EXISTS rol (
    id_rol INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ============================================================
-- TABLA ROL_PERMISO
-- ============================================================

CREATE TABLE IF NOT EXISTS rol_permiso (
    id_rol_permiso INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    nivel INT NOT NULL DEFAULT 1,
    id_rol INT NOT NULL,
    FOREIGN KEY (id_rol) REFERENCES rol(id_rol) ON DELETE CASCADE
) ENGINE=InnoDB;

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
    nivel INT NOT NULL DEFAULT 1,
    foto_url VARCHAR(500),
    activo TINYINT(1) NOT NULL DEFAULT 1,
    id_rol INT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (id_rol) REFERENCES rol(id_rol)
) ENGINE=InnoDB;

-- ============================================================
-- TABLA APLICACIONES
-- ============================================================

CREATE TABLE IF NOT EXISTS aplicaciones (
    id_aplicacion INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    peso INT NOT NULL DEFAULT 1,
    descripcion TEXT NULL,
    participantes_promedio INT NOT NULL DEFAULT 1,
    estado ENUM('activo','cerrado') NOT NULL DEFAULT 'activo'
) ENGINE=InnoDB;

-- ============================================================
-- TABLA TICKETS
-- ============================================================

CREATE TABLE IF NOT EXISTS tickets (
    id_ticket INT AUTO_INCREMENT PRIMARY KEY,
    titulo VARCHAR(200) NOT NULL,
    tipo ENUM('incidencia','peticion','consulta') NOT NULL,
    id_solicitante INT NOT NULL,
    id_aplicacion INT NOT NULL,
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
    id_ticket INT NOT NULL,
    f_asignacion_agente DATETIME NULL,
    id_agente INT NULL,
    f_solucion DATETIME NULL,
    f_revision DATETIME NULL,
    link_img_descripcion TEXT NULL,
    descripcion TEXT NOT NULL,
    notas_resolucion TEXT NULL,
    link_img_resolucion TEXT NULL,
    prioridad ENUM('critica','alta','media','baja') DEFAULT 'media',
    intensidad ENUM('critica','alta','media','baja') DEFAULT 'media',
    sla_horas SMALLINT DEFAULT 24,
    activo TINYINT(1) NOT NULL DEFAULT 1,
    CONSTRAINT fk_detalle_ticket FOREIGN KEY (id_ticket)
        REFERENCES tickets(id_ticket) ON DELETE CASCADE,
    CONSTRAINT fk_detalle_agente FOREIGN KEY (id_agente)
        REFERENCES usuarios(id_usuario)
) ENGINE=InnoDB;

-- ============================================================
-- CALIFICACIONES (1 por detalle_ticket)
-- ============================================================

CREATE TABLE IF NOT EXISTS calificaciones_ticket (
    id_calificacion INT AUTO_INCREMENT PRIMARY KEY,
    id_detalle INT NOT NULL UNIQUE,
    estrellas TINYINT NOT NULL,
    observacion TEXT,
    fecha_calificacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_calif_detalle FOREIGN KEY (id_detalle)
    REFERENCES detalle_ticket(id_detalle) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ============================================================
-- TABLA PROYECTOS
-- ============================================================

CREATE TABLE IF NOT EXISTS proyectos (
    id_proyecto INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(200) NOT NULL,
    id_Stakeholder INT NOT NULL,
    estado ENUM('en_revision','rechazado','planificado','en_desarrollo','qa','pausado','completado','eliminado')
    NOT NULL DEFAULT 'en_revision',
    fecha_inicio DATE NOT NULL,
    fecha_fin_plan DATE NOT NULL,
    problematica TEXT NULL,
    justificacion TEXT NULL,
    beneficios TEXT NULL,
    descripcion TEXT NOT NULL,
    estado2 TINYINT(1) NOT NULL DEFAULT 1,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_proy_resp FOREIGN KEY (id_Stakeholder)
    REFERENCES usuarios(id_usuario)
) ENGINE=InnoDB;

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
    estado ENUM('backlog','por_hacer','en_progreso','completada','cancelada','bloqueado','eliminado')
    NOT NULL DEFAULT 'backlog',
    estado_anterior VARCHAR(30) NULL,
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

-- ============================================================
-- DATOS INICIALES
-- ============================================================

INSERT INTO rol (nombre, descripcion) VALUES
('Admin', 'Acceso total al sistema'),
('Soporte', 'Mesa de ayuda y atención de tickets'),
('Programador', 'Desarrollo y gestión de proyectos'),
('Agente', 'Agente de soporte con acceso limitado'),
('Usuario Final', 'Usuario final del sistema');

INSERT INTO rol_permiso (nombre, nivel, id_rol) VALUES
-- Admin (id=1)
('dashboard', 5, 1), ('nuevo_ticket', 5, 1), ('ver_tickets', 5, 1), ('resolver_tickets', 5, 1), 
('nuevo_proyecto', 5, 1), ('ver_proyectos', 5, 1), ('aprobacion_proyectos', 5, 1),
('nueva_actividad', 5, 1), ('indicadores', 5, 1), ('lista_usuarios', 5, 1), ('reportes', 5, 1),
('configuracion', 5, 1),
-- Soporte (id=2)
('dashboard', 4, 2), ('nuevo_ticket', 4, 2), ('ver_tickets', 4, 2), ('resolver_tickets', 4, 2),
-- Programador (id=3)
('dashboard', 3, 3), ('nuevo_ticket', 3, 3), ('ver_tickets', 3, 3), ('resolver_tickets', 3, 3),
('ver_proyectos', 3, 3), ('nueva_actividad', 3, 3),
-- Agente (id=4)
('dashboard', 2, 4), ('nuevo_ticket', 2, 4), ('ver_tickets', 2, 4),
-- Usuario Final (id=5)
('dashboard', 1, 5), ('nuevo_ticket', 1, 5);

INSERT INTO usuarios
(nombre_completo, apellido, edad, dni, direccion, correo, password_hash, nivel, id_rol)
VALUES
('Renzo Carranza', 'Carranza López', 29, '74123456', 'Av. La Molina 342, Lima',  'renzo@agrovision.pe', 'scrypt:32768:8:1$iaR7uleTvmvuGwBx$ae3840efdbbfd2129ef1d251c77a712d3155caf470af7e4d89e07bed76eed39be686d6aa834873e960ecf94e88a69bf799fb22af9c0ebefc60a364de4dd0ca2b', 5, 1),
('Carlos Mendoza', 'Mendoza Quispe', 34, '72345678', 'Jr. Huallaga 198, Cercado de Lima', 'carlos@agrovision.pe', 'scrypt:32768:8:1$geg5CNy9PksRAdKG$0b112cd044c79592293deeab08836a24e2a91a0981f27fb7b38848bb2532e8e60867f2112a23641945cb94cf101ab888c73bdb172b4c7c14b0dc00e4efe97f76', 4, 2),
('Juan Pérez',     'Pérez Salas',    26, '71234567', 'Calle Los Cedros 55, San Borja', 'juan@agrovision.pe', 'scrypt:32768:8:1$geg5CNy9PksRAdKG$0b112cd044c79592293deeab08836a24e2a91a0981f27fb7b38848bb2532e8e60867f2112a23641945cb94cf101ab888c73bdb172b4c7c14b0dc00e4efe97f76', 3, 3),
('Ana Torres',     'Torres Vásquez', 31, '73456789', 'Av. Arequipa 1250, Miraflores',  'ana@agrovision.pe', 'scrypt:32768:8:1$geg5CNy9PksRAdKG$0b112cd044c79592293deeab08836a24e2a91a0981f27fb7b38848bb2532e8e60867f2112a23641945cb94cf101ab888c73bdb172b4c7c14b0dc00e4efe97f76', 3, 3),
('Luis Flores',    'Flores Huanca',  28, '70987654', 'Psje. Los Pinos 12, Surco', 'luis@agrovision.pe', 'scrypt:32768:8:1$geg5CNy9PksRAdKG$0b112cd044c79592293deeab08836a24e2a91a0981f27fb7b38848bb2532e8e60867f2112a23641945cb94cf101ab888c73bdb172b4c7c14b0dc00e4efe97f76', 4, 2);

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
-- FIN
-- ============================================================