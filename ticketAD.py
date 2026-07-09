from conexion import obtenerconexion


def asegurarTablaCalificacionesTicket():
    """Crea la tabla de calificaciones si aún no existe."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS calificaciones_ticket (
                    id_calificacion INT AUTO_INCREMENT PRIMARY KEY,
                    id_detalle INT NOT NULL UNIQUE,
                    estrellas TINYINT NOT NULL,
                    observacion TEXT NULL,
                    fecha_calificacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_calif_detalle
                        FOREIGN KEY (id_detalle) REFERENCES detalle_ticket(id_detalle)
                        ON DELETE CASCADE
                ) ENGINE=InnoDB
            """)
        conn.commit()


def asegurarTablas():
    """Asegura que existan las tablas necesarias del nuevo esquema."""
    asegurarTablaCalificacionesTicket()
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
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
                ) ENGINE=InnoDB
            """)
            # Migración: remover UNIQUE de id_ticket si existe
            cursor.execute("""
                SELECT INDEX_NAME FROM information_schema.STATISTICS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'detalle_ticket'
                  AND COLUMN_NAME = 'id_ticket'
                  AND NON_UNIQUE = 0
                  AND INDEX_NAME != 'PRIMARY'
                LIMIT 1
            """)
            row = cursor.fetchone()
            if row:
                # Antes de dropear el UNIQUE, crear un index regular para la FK
                cursor.execute("""
                    SELECT COUNT(*) AS cnt FROM information_schema.STATISTICS
                    WHERE TABLE_SCHEMA = DATABASE()
                      AND TABLE_NAME = 'detalle_ticket'
                      AND COLUMN_NAME = 'id_ticket'
                      AND NON_UNIQUE = 1
                """)
                has_non_unique = cursor.fetchone()['cnt'] > 0
                if not has_non_unique:
                    cursor.execute("ALTER TABLE detalle_ticket ADD INDEX idx_detalle_ticket_id_ticket (id_ticket)")
                cursor.execute(f"ALTER TABLE detalle_ticket DROP INDEX `{row['INDEX_NAME']}`")
            # Migración: agregar columna activo si no existe
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME = 'detalle_ticket'
                  AND COLUMN_NAME = 'activo'
            """)
            if cursor.fetchone()['COUNT(*)'] == 0:
                cursor.execute("ALTER TABLE detalle_ticket ADD COLUMN activo TINYINT(1) NOT NULL DEFAULT 1")
            # Migración: si existen columnas nuevas faltantes
            for col in ('prioridad', 'intensidad', 'sla_horas'):
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = DATABASE()
                      AND TABLE_NAME = 'detalle_ticket'
                      AND COLUMN_NAME = %s
                """, (col,))
                if cursor.fetchone()['COUNT(*)'] == 0:
                    tipo = "ENUM('critica','alta','media','baja') DEFAULT 'media'" if col != 'sla_horas' else "SMALLINT DEFAULT 24"
                    cursor.execute(f"ALTER TABLE detalle_ticket ADD COLUMN {col} {tipo}")
        conn.commit()


class Ticket:
    def __init__(self, titulo, tipo, id_solicitante, id_aplicacion, descripcion, link_img_descripcion=None):
        self.titulo                = titulo
        self.tipo                  = tipo
        self.id_solicitante        = id_solicitante
        self.id_aplicacion         = id_aplicacion
        self.descripcion           = descripcion
        self.link_img_descripcion  = link_img_descripcion


def obtenerTicket(id_ticket):
    """Retorna un ticket por su ID con datos relacionados."""
    asegurarTablas()
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT t.id_ticket, t.titulo, t.tipo, t.estado,
                       t.f_registro, t.f_cierre,
                       t.id_solicitante, t.id_aplicacion,
                       IFNULL(d.prioridad, 'media') AS prioridad,
                       IFNULL(d.intensidad, 'media') AS intensidad,
                       IFNULL(d.sla_horas, 24) AS sla_horas,
                       d.id_detalle, d.f_asignacion_agente, d.id_agente,
                       d.f_solucion, d.f_revision,
                       d.link_img_descripcion, d.descripcion,
                       d.notas_resolucion, d.link_img_resolucion,
                       u.nombre_completo AS nombre_solicitante,
                       ag.nombre_completo AS nombre_agente,
                       a.id_aplicacion, a.nombre AS nombre_aplicacion
                  FROM tickets t
                 JOIN usuarios u ON t.id_solicitante = u.id_usuario
                 JOIN aplicaciones a ON t.id_aplicacion = a.id_aplicacion
                  LEFT JOIN detalle_ticket d ON d.id_ticket = t.id_ticket AND d.activo = 1
                 LEFT JOIN usuarios ag ON d.id_agente = ag.id_usuario
                 WHERE t.id_ticket = %s
            """, (id_ticket,))
            return cursor.fetchone()


def insertarTicket(obj):
    """Inserta un ticket y su detalle."""
    asegurarTablas()
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tickets
                    (titulo, tipo, id_solicitante, id_aplicacion)
                VALUES (%s, %s, %s, %s)
            """, (
                obj.titulo, obj.tipo,
                obj.id_solicitante, obj.id_aplicacion
            ))
            id_ticket = cursor.lastrowid
            cursor.execute("""
                INSERT INTO detalle_ticket
                    (id_ticket, descripcion, link_img_descripcion, activo)
                VALUES (%s, %s, %s, 1)
            """, (id_ticket, obj.descripcion, obj.link_img_descripcion))
        conn.commit()
    return id_ticket


def editarTicket(id_ticket, titulo, tipo, id_aplicacion, descripcion, link_img_descripcion=None):
    """Actualiza los campos editables de un ticket (sin prioridad/intensidad/SLA)."""
    asegurarTablas()
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE tickets
                   SET titulo         = %s,
                       tipo           = %s,
                       id_aplicacion  = %s
                  WHERE id_ticket = %s
                    AND estado = 'solicitado'
             """, (titulo, tipo, id_aplicacion, id_ticket))
            cursor.execute("""
                UPDATE detalle_ticket
                   SET descripcion          = %s,
                       link_img_descripcion = %s
                 WHERE id_ticket = %s AND activo = 1
            """, (descripcion, link_img_descripcion, id_ticket))
            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO detalle_ticket
                        (id_ticket, descripcion, link_img_descripcion, activo)
                    VALUES (%s, %s, %s, 1)
                """, (id_ticket, descripcion, link_img_descripcion))
        conn.commit()


def resolverTicket(id_ticket, id_agente, estado, notas, link_img_resolucion=None, f_solucion=None, f_revision=None):
    """Actualiza el estado y registra la resolución en detalle_ticket."""
    from datetime import datetime
    ahora = datetime.now()

    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            f_cierre = ahora if estado == 'cerrado' else None

            cursor.execute("""
                UPDATE tickets
                   SET estado    = %s,
                       f_cierre  = %s
                 WHERE id_ticket = %s
            """, (estado, f_cierre, id_ticket))

            # Si notas = 'reasignado', buscamos el detalle activo para marcarlo
            if notas == 'reasignado':
                cursor.execute("""
                    UPDATE detalle_ticket
                       SET notas_resolucion = 'reasignado',
                           activo = 0
                     WHERE id_ticket = %s AND activo = 1
                """, (id_ticket,))
            else:
                cursor.execute("""
                    UPDATE detalle_ticket
                       SET id_agente           = %s,
                           f_asignacion_agente = COALESCE(%s, f_asignacion_agente),
                           f_solucion          = %s,
                           f_revision          = %s,
                           notas_resolucion    = %s,
                           link_img_resolucion = %s
                     WHERE id_ticket = %s AND activo = 1
                """, (id_agente, ahora,
                      f_solucion or ahora, f_revision,
                      notas, link_img_resolucion, id_ticket))
                if cursor.rowcount == 0:
                    cursor.execute("""
                        INSERT INTO detalle_ticket
                            (id_ticket, id_agente, f_asignacion_agente,
                             f_solucion, f_revision,
                             notas_resolucion, link_img_resolucion, descripcion, activo)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, '', 1)
                    """, (id_ticket, id_agente, ahora,
                          f_solucion or ahora, f_revision,
                          notas, link_img_resolucion))
        conn.commit()


def cancelarTicket(id_ticket):
    """Cancela un ticket (solicitado o en_progreso)."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE tickets
                   SET estado = 'cancelado',
                       f_cierre = NOW()
                 WHERE id_ticket = %s
                   AND estado IN ('solicitado','en_progreso')
            """, (id_ticket,))
        conn.commit()


def guardarCalificacionTicket(id_detalle, estrellas, observacion):
    """Guarda la calificación del solicitante para un detalle específico."""
    asegurarTablaCalificacionesTicket()
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO calificaciones_ticket (id_detalle, estrellas, observacion)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    estrellas = VALUES(estrellas),
                    observacion = VALUES(observacion),
                    fecha_calificacion = CURRENT_TIMESTAMP
            """, (id_detalle, estrellas, observacion))
        conn.commit()


def listarTickets():
    """Retorna tickets activos con datos relacionados."""
    asegurarTablas()
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT t.id_ticket, t.titulo, t.tipo, t.estado,
                       t.f_registro, t.f_cierre,
                       t.id_solicitante, t.id_aplicacion,
                       IFNULL(d.prioridad, 'media') AS prioridad,
                       IFNULL(d.intensidad, 'media') AS intensidad,
                       IFNULL(d.sla_horas, 24) AS sla_horas,
                       d.id_detalle, d.f_asignacion_agente, d.id_agente,
                       d.f_solucion, d.f_revision,
                       d.link_img_descripcion, d.descripcion,
                       d.notas_resolucion, d.link_img_resolucion,
                       a.nombre AS nombre_aplicacion,
                       u.nombre_completo AS nombre_solicitante,
                       ag.nombre_completo AS nombre_agente,
                        c.calificacion_promedio,
                        c.activo_calificado
                FROM tickets t
                JOIN usuarios u ON t.id_solicitante = u.id_usuario
                JOIN aplicaciones a ON t.id_aplicacion = a.id_aplicacion
                LEFT JOIN detalle_ticket d ON d.id_ticket = t.id_ticket AND d.activo = 1
                LEFT JOIN usuarios ag ON d.id_agente = ag.id_usuario
                LEFT JOIN (
                    SELECT d.id_ticket,
                           ROUND(AVG(c.estrellas), 1) AS calificacion_promedio,
                           MAX(d.activo = 1) AS activo_calificado
                    FROM calificaciones_ticket c
                    JOIN detalle_ticket d ON d.id_detalle = c.id_detalle
                    GROUP BY d.id_ticket
                ) c ON c.id_ticket = t.id_ticket
                WHERE t.estado NOT IN ('cancelado')
                ORDER BY t.id_ticket DESC
            """)
            return cursor.fetchall()


def listarAplicaciones():
    """Retorna todas las aplicaciones."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id_aplicacion, nombre, peso, descripcion, participantes_promedio, estado
                FROM aplicaciones
                ORDER BY nombre
            """)
            return cursor.fetchall()


def listarAplicacionesActivas():
    """Retorna solo aplicaciones activas."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id_aplicacion, nombre, peso, descripcion, participantes_promedio
                FROM aplicaciones
                WHERE estado = 'activo'
                ORDER BY nombre
            """)
            return cursor.fetchall()


def obtenerAplicacion(id_aplicacion):
    """Retorna una aplicación por ID."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id_aplicacion, nombre, peso, descripcion, participantes_promedio, estado
                FROM aplicaciones
                WHERE id_aplicacion = %s
            """, (id_aplicacion,))
            return cursor.fetchone()


def insertarAplicacion(nombre, peso, descripcion, participantes_promedio):
    """Inserta una nueva aplicación."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO aplicaciones (nombre, peso, descripcion, participantes_promedio, estado)
                VALUES (%s, %s, %s, %s, 'activo')
            """, (nombre, peso, descripcion, participantes_promedio))
        conn.commit()


def editarAplicacion(id_aplicacion, nombre, peso, descripcion, participantes_promedio):
    """Actualiza una aplicación existente."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE aplicaciones
                   SET nombre = %s, peso = %s, descripcion = %s, participantes_promedio = %s
                 WHERE id_aplicacion = %s
            """, (nombre, peso, descripcion, participantes_promedio, id_aplicacion))
        conn.commit()


def eliminarAplicacion(id_aplicacion):
    """Elimina una aplicación."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                DELETE FROM aplicaciones WHERE id_aplicacion = %s
            """, (id_aplicacion,))
        conn.commit()


def toggleEstadoAplicacion(id_aplicacion):
    """Cambia entre activo/cerrado."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE aplicaciones
                   SET estado = IF(estado = 'activo', 'cerrado', 'activo')
                 WHERE id_aplicacion = %s
            """, (id_aplicacion,))
        conn.commit()


def cerrarAplicacion(id_aplicacion):
    """Fuerza el estado de una aplicación a 'cerrado' (sin eliminarla)."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE aplicaciones SET estado = 'cerrado' WHERE id_aplicacion = %s
            """, (id_aplicacion,))
        conn.commit()


def calcularSLA(prioridad, intensidad, peso, participantes_promedio):
    """Calcula SLA en horas según prioridad, intensidad, peso y participantes."""
    base = {'critica': 4, 'alta': 8, 'media': 16, 'baja': 32}
    int_mult = {'critica': 1.8, 'alta': 1.4, 'media': 1.0, 'baja': 0.6}
    b = base.get(prioridad, 16)
    m = int_mult.get(intensidad, 1.0)
    sla = round(b * m + participantes_promedio - peso)
    return max(2, min(120, sla))


def listarPosiblesAgentes():
    """Retorna usuarios con rol soporte o programador (posibles agentes)."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.id_usuario, u.nombre_completo, r.nombre AS rol_nombre
                FROM usuarios u
                JOIN rol r ON r.id_rol = u.id_rol
                WHERE r.nombre IN ('Soporte','Programador')
                  AND u.activo = 1
                ORDER BY u.nombre_completo
            """)
            return cursor.fetchall()


def asignarTicket(id_ticket, id_agente, prioridad, intensidad, sla_horas):
    """Asigna un agente a un ticket en estado 'solicitado' y lo pasa a 'en_progreso'."""
    from datetime import datetime
    ahora = datetime.now()
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE tickets
                   SET estado = 'en_progreso'
                 WHERE id_ticket = %s
                   AND estado = 'solicitado'
            """, (id_ticket,))
            if cursor.rowcount == 0:
                raise ValueError("El ticket no está en estado 'solicitado' o no existe.")
            cursor.execute("""
                UPDATE detalle_ticket
                   SET id_agente = %s,
                       f_asignacion_agente = %s,
                       prioridad = %s,
                       intensidad = %s,
                       sla_horas = %s
                 WHERE id_ticket = %s AND activo = 1
            """, (id_agente, ahora, prioridad, intensidad, sla_horas, id_ticket))
            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO detalle_ticket
                        (id_ticket, id_agente, f_asignacion_agente,
                         prioridad, intensidad, sla_horas, descripcion, activo)
                    VALUES (%s, %s, %s, %s, %s, %s, '', 1)
                """, (id_ticket, id_agente, ahora, prioridad, intensidad, sla_horas))
        conn.commit()


def reasignarTicket(id_ticket, id_nuevo_agente, descripcion_reasignacion, link_img=None):
    """Reasigna un ticket a otro agente. Marca el detalle activo como 'reasignado' y crea uno nuevo."""
    from datetime import datetime
    ahora = datetime.now()
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            # 1. Obtener datos del detalle activo actual (prioridad, intensidad, sla)
            cursor.execute("""
                SELECT prioridad, intensidad, sla_horas, id_agente
                FROM detalle_ticket
                WHERE id_ticket = %s AND activo = 1
            """, (id_ticket,))
            actual = cursor.fetchone()

            # 2. Marcar el detalle activo como reasignado
            cursor.execute("""
                UPDATE detalle_ticket
                   SET notas_resolucion = 'reasignado',
                       activo = 0
                 WHERE id_ticket = %s AND activo = 1
            """, (id_ticket,))

            # 3. Insertar nuevo detalle con el nuevo agente
            prioridad = actual['prioridad'] if actual else 'media'
            intensidad = actual['intensidad'] if actual else 'media'
            sla_horas = actual['sla_horas'] if actual else 24

            cursor.execute("""
                INSERT INTO detalle_ticket
                    (id_ticket, id_agente, f_asignacion_agente,
                     prioridad, intensidad, sla_horas,
                     descripcion, link_img_descripcion, activo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1)
            """, (id_ticket, id_nuevo_agente, ahora,
                  prioridad, intensidad, sla_horas,
                  descripcion_reasignacion, link_img))
        conn.commit()


def reabrirTicket(id_ticket, descripcion, link_img=None):
    """Reabre un ticket marcándolo como 'en_progreso'. Crea un nuevo detalle con el mismo agente y SLA."""
    from datetime import datetime
    ahora = datetime.now()
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            # 1. Obtener datos del detalle activo actual
            cursor.execute("""
                SELECT prioridad, intensidad, sla_horas, id_agente
                FROM detalle_ticket
                WHERE id_ticket = %s AND activo = 1
            """, (id_ticket,))
            actual = cursor.fetchone()

            # 2. Marcar detalle activo como inactivo (sin sobrescribir notas_resolucion)
            cursor.execute("""
                UPDATE detalle_ticket
                   SET activo = 0
                 WHERE id_ticket = %s AND activo = 1
            """, (id_ticket,))

            # 3. Insertar nuevo detalle con el mismo agente y SLA
            prioridad = actual['prioridad'] if actual else 'media'
            intensidad = actual['intensidad'] if actual else 'media'
            sla_horas = actual['sla_horas'] if actual else 24
            id_agente = actual['id_agente'] if actual else None

            cursor.execute("""
                INSERT INTO detalle_ticket
                    (id_ticket, id_agente, f_asignacion_agente,
                     prioridad, intensidad, sla_horas,
                     descripcion, link_img_descripcion, activo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1)
            """, (id_ticket, id_agente, ahora,
                  prioridad, intensidad, sla_horas,
                  descripcion, link_img))

            # 4. Volver ticket a en_progreso, limpiar f_cierre
            cursor.execute("""
                UPDATE tickets
                   SET estado = 'en_progreso',
                       f_cierre = NULL
                 WHERE id_ticket = %s
            """, (id_ticket,))
        conn.commit()


def obtenerDetallesTicket(id_ticket):
    """Retorna todos los registros de detalle_ticket para un ticket, con su calificación si existe."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT d.*, u.nombre_completo AS nombre_agente,
                       c.id_calificacion, c.estrellas AS calificacion_estrellas,
                       c.observacion AS calificacion_observacion,
                       c.fecha_calificacion AS calificacion_fecha
                FROM detalle_ticket d
                LEFT JOIN usuarios u ON d.id_agente = u.id_usuario
                LEFT JOIN calificaciones_ticket c ON c.id_detalle = d.id_detalle
                WHERE d.id_ticket = %s
                ORDER BY d.f_asignacion_agente ASC, d.id_detalle ASC
            """, (id_ticket,))
            return cursor.fetchall()


def obtenerCalificacionTicket(id_detalle):
    """Retorna la calificación de un detalle si existe."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT c.*, d.id_ticket
                FROM calificaciones_ticket c
                JOIN detalle_ticket d ON d.id_detalle = c.id_detalle
                WHERE c.id_detalle = %s
                LIMIT 1
            """, (id_detalle,))
            return cursor.fetchone()


def listarUsuariosNivelMenor(nivel):
    """Retorna usuarios activos con nivel menor al dado."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.id_usuario, u.nombre_completo, r.nombre AS rol_nombre, u.nivel
                FROM usuarios u
                JOIN rol r ON r.id_rol = u.id_rol
                WHERE u.activo = 1 AND u.nivel < %s
                ORDER BY u.nombre_completo
            """, (nivel,))
            return cursor.fetchall()


def listarCalificaciones():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT c.*, d.id_ticket, d.descripcion
                FROM calificaciones_ticket c
                JOIN detalle_ticket d ON d.id_detalle = c.id_detalle
                ORDER BY c.fecha_calificacion DESC
            """)
            return cursor.fetchall()


def listarDetallesTicketAll(id_ticket=None):
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            if id_ticket:
                cursor.execute("""
                    SELECT d.*, u.nombre_completo AS nombre_agente
                    FROM detalle_ticket d
                    LEFT JOIN usuarios u ON u.id_usuario = d.id_agente
                    WHERE d.id_ticket = %s
                    ORDER BY d.id_detalle
                """, (id_ticket,))
            else:
                cursor.execute("""
                    SELECT d.*, u.nombre_completo AS nombre_agente
                    FROM detalle_ticket d
                    LEFT JOIN usuarios u ON u.id_usuario = d.id_agente
                    ORDER BY d.id_ticket, d.id_detalle
                """)
            return cursor.fetchall()


def obtenerDetalleTicket(id_detalle):
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT d.*, u.nombre_completo AS nombre_agente
                FROM detalle_ticket d
                LEFT JOIN usuarios u ON u.id_usuario = d.id_agente
                WHERE d.id_detalle = %s
            """, (id_detalle,))
            return cursor.fetchone()