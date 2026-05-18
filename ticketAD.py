from conexion import obtenerconexion

class Ticket:
    def __init__(self, titulo, tipo, prioridad, aplicacion, id_solicitante, sla_horas, descripcion):
        self.titulo          = titulo
        self.tipo            = tipo
        self.prioridad       = prioridad
        self.aplicacion      = aplicacion
        self.id_solicitante  = id_solicitante
        self.sla_horas       = sla_horas
        self.descripcion     = descripcion


def obtenerTicket(id_ticket):
    """Retorna un ticket por su ID con datos del solicitante."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT t.*, u.nombre_completo AS nombre_solicitante
                FROM tickets t
                JOIN usuarios u ON t.id_solicitante = u.id_usuario
                WHERE t.id_ticket = %s
            """, (id_ticket,))
            return cursor.fetchone()


def resolverTicket(id_ticket, id_agente, estado, notas):
    """Actualiza el estado de un ticket y registra la resolución."""
    from datetime import datetime
    fecha_res = datetime.now() if estado in ('resuelto', 'cerrado') else None

    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE tickets
                   SET estado            = %s,
                       id_agente         = %s,
                       notas_resolucion  = %s,
                       fecha_resolucion  = %s
                 WHERE id_ticket = %s
            """, (estado, id_agente, notas, fecha_res, id_ticket))
        conn.commit()


def insertarTicket(obj):
    """Inserta un ticket de soporte."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO tickets
                    (titulo, tipo, prioridad, aplicacion,
                     id_solicitante, sla_horas, descripcion)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                obj.titulo, obj.tipo, obj.prioridad,
                obj.aplicacion, obj.id_solicitante,
                obj.sla_horas, obj.descripcion
            ))
        conn.commit()


def listarTickets():
    """Retorna tickets con nombre del solicitante y agente asignado."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT t.id_ticket, t.titulo, t.tipo, t.prioridad,
                       t.aplicacion, t.estado, t.fecha_apertura, t.sla_horas,
                       t.notas_resolucion, t.fecha_resolucion,
                       u.nombre_completo AS nombre_solicitante,
                       a.nombre_completo AS nombre_agente
                FROM tickets t
                JOIN usuarios u ON t.id_solicitante = u.id_usuario
                LEFT JOIN usuarios a ON t.id_agente = a.id_usuario
                ORDER BY
                    FIELD(t.prioridad,'critica','alta','media','baja'),
                    t.fecha_apertura DESC
            """)
            return cursor.fetchall()