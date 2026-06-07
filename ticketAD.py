from conexion import obtenerconexion


def asegurarTablaCalificacionesTicket():
    """Crea la tabla de calificaciones si aún no existe."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS calificaciones_ticket (
                    id_calificacion INT AUTO_INCREMENT PRIMARY KEY,
                    id_ticket INT NOT NULL UNIQUE,
                    estrellas TINYINT NOT NULL,
                    observacion TEXT NULL,
                    fecha_calificacion DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_calif_ticket
                        FOREIGN KEY (id_ticket) REFERENCES tickets(id_ticket)
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
                ) ENGINE=InnoDB
            """)
        conn.commit()


class Ticket:
    def __init__(self, titulo, tipo, prioridad, intensidad, id_solicitante, id_aplicacion, sla_horas, descripcion, link_img_descripcion=None):
        self.titulo                = titulo
        self.tipo                  = tipo
        self.prioridad             = prioridad
        self.intensidad            = intensidad
        self.id_solicitante        = id_solicitante
        self.id_aplicacion         = id_aplicacion
        self.sla_horas             = sla_horas
        self.descripcion           = descripcion
        self.link_img_descripcion  = link_img_descripcion


def obtenerTicket(id_ticket):
    """Retorna un ticket por su ID con datos relacionados."""
    asegurarTablas()
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT t.*,
                       d.id_detalle, d.f_asignacion_agente, d.id_agente,
                       d.f_solucion, d.f_revision,
                       d.link_img_descripcion, d.descripcion,
                       d.notas_resolucion, d.link_img_resolucion,
                       u.nombre_completo AS nombre_solicitante,
                       ag.nombre_completo AS nombre_agente,
                       a.id_aplicacion, a.nombre AS nombre_aplicacion,
                       c.estrellas AS calificacion_estrellas,
                       c.observacion AS calificacion_observacion,
                       c.fecha_calificacion
                FROM tickets t
                JOIN usuarios u ON t.id_solicitante = u.id_usuario
                JOIN aplicaciones a ON t.id_aplicacion = a.id_aplicacion
                LEFT JOIN detalle_ticket d ON d.id_ticket = t.id_ticket
                LEFT JOIN usuarios ag ON d.id_agente = ag.id_usuario
                LEFT JOIN calificaciones_ticket c ON c.id_ticket = t.id_ticket
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
                    (titulo, tipo, prioridad, intensidad,
                     id_solicitante, id_aplicacion, sla_horas)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                obj.titulo, obj.tipo, obj.prioridad, obj.intensidad,
                obj.id_solicitante, obj.id_aplicacion, obj.sla_horas
            ))
            id_ticket = cursor.lastrowid
            cursor.execute("""
                INSERT INTO detalle_ticket
                    (id_ticket, descripcion, link_img_descripcion)
                VALUES (%s, %s, %s)
            """, (id_ticket, obj.descripcion, obj.link_img_descripcion))
        conn.commit()
    return id_ticket


def editarTicket(id_ticket, titulo, tipo, prioridad, intensidad, id_aplicacion, sla_horas, descripcion, link_img_descripcion=None):
    """Actualiza los campos editables de un ticket."""
    asegurarTablas()
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE tickets
                   SET titulo         = %s,
                       tipo           = %s,
                       prioridad      = %s,
                       intensidad     = %s,
                       id_aplicacion  = %s,
                       sla_horas      = %s
                  WHERE id_ticket = %s
                    AND estado = 'solicitado'
             """, (titulo, tipo, prioridad, intensidad, id_aplicacion, sla_horas, id_ticket))
            cursor.execute("""
                INSERT INTO detalle_ticket (id_ticket, descripcion, link_img_descripcion)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    descripcion          = VALUES(descripcion),
                    link_img_descripcion = VALUES(link_img_descripcion)
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

            cursor.execute("""
                INSERT INTO detalle_ticket (id_ticket, id_agente, f_asignacion_agente,
                                            f_solucion, f_revision,
                                            notas_resolucion, link_img_resolucion)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    id_agente           = VALUES(id_agente),
                    f_asignacion_agente = COALESCE(VALUES(f_asignacion_agente), f_asignacion_agente),
                    f_solucion          = VALUES(f_solucion),
                    f_revision          = VALUES(f_revision),
                    notas_resolucion    = VALUES(notas_resolucion),
                    link_img_resolucion = VALUES(link_img_resolucion)
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


def guardarCalificacionTicket(id_ticket, estrellas, observacion):
    """Guarda o actualiza la calificación del solicitante."""
    asegurarTablaCalificacionesTicket()
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO calificaciones_ticket (id_ticket, estrellas, observacion)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    estrellas = VALUES(estrellas),
                    observacion = VALUES(observacion),
                    fecha_calificacion = CURRENT_TIMESTAMP
            """, (id_ticket, estrellas, observacion))
        conn.commit()


def listarTickets():
    """Retorna tickets activos con datos relacionados."""
    asegurarTablas()
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT t.id_ticket, t.titulo, t.tipo, t.prioridad, t.intensidad,
                       t.estado, t.f_registro, t.sla_horas, t.f_cierre,
                       t.id_solicitante, t.id_aplicacion,
                       d.id_detalle, d.f_asignacion_agente, d.id_agente,
                       d.f_solucion, d.f_revision,
                       d.link_img_descripcion, d.descripcion,
                       d.notas_resolucion, d.link_img_resolucion,
                       a.nombre AS nombre_aplicacion,
                       u.nombre_completo AS nombre_solicitante,
                       ag.nombre_completo AS nombre_agente,
                       c.estrellas AS calificacion_estrellas,
                       c.observacion AS calificacion_observacion,
                       c.fecha_calificacion
                FROM tickets t
                JOIN usuarios u ON t.id_solicitante = u.id_usuario
                JOIN aplicaciones a ON t.id_aplicacion = a.id_aplicacion
                LEFT JOIN detalle_ticket d ON d.id_ticket = t.id_ticket
                LEFT JOIN usuarios ag ON d.id_agente = ag.id_usuario
                LEFT JOIN calificaciones_ticket c ON c.id_ticket = t.id_ticket
                WHERE t.estado NOT IN ('cancelado')
                ORDER BY
                    FIELD(t.prioridad,'critica','alta','media','baja'),
                    t.f_registro DESC
            """)
            return cursor.fetchall()


def listarAplicaciones():
    """Retorna todas las aplicaciones."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id_aplicacion, nombre, peso, descripcion, participantes_promedio
                FROM aplicaciones
                ORDER BY nombre
            """)
            return cursor.fetchall()


def obtenerAplicacion(id_aplicacion):
    """Retorna una aplicación por ID."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id_aplicacion, nombre, peso, descripcion, participantes_promedio
                FROM aplicaciones
                WHERE id_aplicacion = %s
            """, (id_aplicacion,))
            return cursor.fetchone()


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
                SELECT id_usuario, nombre_completo, rol
                FROM usuarios
                WHERE rol IN ('soporte','programador')
                  AND activo = 1
                ORDER BY nombre_completo
            """)
            return cursor.fetchall()


def asignarTicket(id_ticket, id_agente):
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
                INSERT INTO detalle_ticket (id_ticket, id_agente, f_asignacion_agente)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    id_agente           = VALUES(id_agente),
                    f_asignacion_agente = VALUES(f_asignacion_agente)
            """, (id_ticket, id_agente, ahora))
        conn.commit()
