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

class Ticket:
    def __init__(self, titulo, tipo, prioridad, aplicacion, id_solicitante, sla_horas, descripcion, link_img_descripcion=None):
        self.titulo                = titulo
        self.tipo                  = tipo
        self.prioridad             = prioridad
        self.aplicacion            = aplicacion
        self.id_solicitante        = id_solicitante
        self.sla_horas             = sla_horas
        self.descripcion           = descripcion
        self.link_img_descripcion  = link_img_descripcion


def obtenerTicket(id_ticket):
    """Retorna un ticket por su ID con datos del solicitante."""
    asegurarTablaCalificacionesTicket()
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT t.*, u.nombre_completo AS nombre_solicitante,
                       c.estrellas AS calificacion_estrellas,
                       c.observacion AS calificacion_observacion,
                       c.fecha_calificacion
                FROM tickets t
                JOIN usuarios u ON t.id_solicitante = u.id_usuario
                LEFT JOIN calificaciones_ticket c ON c.id_ticket = t.id_ticket
                WHERE t.id_ticket = %s
            """, (id_ticket,))
            return cursor.fetchone()


def resolverTicket(id_ticket, id_agente, estado, notas, link_img_resolucion=None):
    """Actualiza el estado de un ticket y registra la resolución."""
    from datetime import datetime
    fecha_res = datetime.now() if estado in ('resuelto', 'cerrado') else None

    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE tickets
                   SET estado              = %s,
                       id_agente           = %s,
                       notas_resolucion    = %s,
                       fecha_resolucion    = %s,
                       link_img_resolucion = %s
                 WHERE id_ticket = %s
            """, (estado, id_agente, notas, fecha_res, link_img_resolucion, id_ticket))
        conn.commit()


def guardarCalificacionTicket(id_ticket, estrellas, observacion):
    """Guarda o actualiza la calificación del solicitante para un ticket atendido."""
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


def insertarTicket(obj):
    """Inserta un ticket de soporte."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tickets
                    (titulo, tipo, prioridad, aplicacion,
                     id_solicitante, sla_horas, descripcion,
                     link_img_descripcion)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                obj.titulo, obj.tipo, obj.prioridad,
                obj.aplicacion, obj.id_solicitante,
                obj.sla_horas, obj.descripcion,
                obj.link_img_descripcion
            ))
        conn.commit()


def editarTicket(id_ticket, titulo, tipo, prioridad, aplicacion, sla_horas, descripcion, link_img_descripcion=None):
    """Actualiza los campos editables de un ticket que está en_progreso."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE tickets
                   SET titulo                = %s,
                       tipo                  = %s,
                       prioridad             = %s,
                       aplicacion            = %s,
                       sla_horas             = %s,
                       descripcion           = %s,
                       link_img_descripcion  = %s
                 WHERE id_ticket = %s
                   AND estado    = 'en_progreso'
            """, (titulo, tipo, prioridad, aplicacion, sla_horas, descripcion, link_img_descripcion, id_ticket))
        conn.commit()


def eliminarTicket(id_ticket):
    """Elimina permanentemente un ticket que está en estado cerrado."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE tickets
                   SET estado    = 'eliminado'
                 WHERE id_ticket = %s
                   AND estado    = 'cerrado'
            """, (id_ticket,))
        conn.commit()


def listarTickets():
    """Retorna tickets con nombre del solicitante y agente asignado."""
    asegurarTablaCalificacionesTicket()
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT t.id_ticket, t.titulo, t.tipo, t.prioridad,
                       t.aplicacion, t.estado, t.fecha_apertura, t.sla_horas,
                       t.notas_resolucion, t.fecha_resolucion,
                       t.link_img_descripcion, t.link_img_resolucion,
                       t.id_solicitante,
                       u.nombre_completo AS nombre_solicitante,
                       a.nombre_completo AS nombre_agente,
                       c.estrellas AS calificacion_estrellas,
                       c.observacion AS calificacion_observacion,
                       c.fecha_calificacion
                FROM tickets t
                JOIN usuarios u ON t.id_solicitante = u.id_usuario
                LEFT JOIN usuarios a ON t.id_agente = a.id_usuario
                LEFT JOIN calificaciones_ticket c ON c.id_ticket = t.id_ticket
                WHERE t.estado != 'eliminado'
                ORDER BY
                    FIELD(t.prioridad,'critica','alta','media','baja'),
                    t.fecha_apertura DESC
            """)
            return cursor.fetchall()