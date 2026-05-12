from conexion import (obtenerconexion)

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
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT t.*, u.nombre_completo AS nombre_solicitante
                        FROM tickets t
                        JOIN usuarios u ON t.id_solicitante = u.id_usuario
                        WHERE t.id_ticket = %s
                    """, (id_ticket,))
                    return cursor.fetchone()
    except Exception as e:
        print(f"[ERROR obtenerTicket] {e}")
    return None


def resolverTicket(id_ticket, id_agente, estado, notas):
    """
    Actualiza el estado de un ticket y registra la resolución.
    Retorna (True, '') si OK, o (False, 'mensaje') si falla.
    """
    try:
        conn = obtenerconexion()
        if not conn:
            return False, 'No se pudo conectar a la base de datos.'

        fecha_res = None
        if estado in ('resuelto', 'cerrado'):
            from datetime import datetime
            fecha_res = datetime.now()

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
        return True, 'Ticket actualizado correctamente.'
    except Exception as e:
        print(f"[ERROR resolverTicket] {e}")
        return False, f'Error al actualizar: {e}'

def insertarTicket(obj):
    """Inserta un ticket de soporte. Retorna True si tuvo éxito."""
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql = """
                        INSERT INTO tickets
                            (titulo, tipo, prioridad, aplicacion,
                             id_solicitante, sla_horas, descripcion)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (
                        obj.titulo, obj.tipo, obj.prioridad,
                        obj.aplicacion, obj.id_solicitante,
                        obj.sla_horas, obj.descripcion
                    ))
                    conn.commit()
            return True
    except Exception as e:
        print(f"[ERROR insertarTicket] {e}")
    return False

# ================= Listar tablas de tickets =======================

def listarTickets():
    """Retorna tickets con nombre del solicitante y agente asignado."""
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql = """
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
                    """
                    cursor.execute(sql)
                    return cursor.fetchall()
    except Exception as e:
        print(f"[ERROR listarTickets] {e}")
    return []

def resumenTickets():
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT
                            COUNT(*) AS total,
                            SUM(estado='abierto')     AS abiertos,
                            SUM(estado='en_progreso') AS en_progreso,
                            SUM(estado='resuelto')    AS resueltos,
                            SUM(estado='cerrado')     AS cerrados,
                            SUM(
                                fecha_resolucion IS NOT NULL AND
                                TIMESTAMPDIFF(HOUR, fecha_apertura, fecha_resolucion) <= sla_horas
                            ) AS sla_ok,
                            SUM(fecha_resolucion IS NOT NULL) AS total_resueltos_con_fecha,
                            ROUND(AVG(
                                CASE WHEN fecha_resolucion IS NOT NULL
                                THEN TIMESTAMPDIFF(HOUR, fecha_apertura, fecha_resolucion)
                                END
                            ), 1) AS promedio_horas_resolucion
                        FROM tickets
                    """)
                    row = cursor.fetchone()
                    if row and row['total_resueltos_con_fecha']:
                        row['pct_sla'] = round(row['sla_ok'] / row['total_resueltos_con_fecha'] * 100, 1)
                    else:
                        row['pct_sla'] = 0
                    return row
    except Exception as e:
        print(f"[ERROR resumenTickets] {e}")
    return {}

def ticketsPorAplicacion():
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT aplicacion,
                               COUNT(*) AS total,
                               SUM(estado IN ('abierto','en_progreso')) AS pendientes,
                               SUM(estado IN ('resuelto','cerrado'))    AS cerrados
                        FROM tickets
                        GROUP BY aplicacion
                        ORDER BY total DESC
                        LIMIT 10
                    """)
                    return cursor.fetchall()
    except Exception as e:
        print(f"[ERROR TicketsPorAplicacion] {e}")
    return []

def ticketsPorPrioridad():
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT prioridad, COUNT(*) AS total,
                               SUM(estado IN ('abierto','en_progreso')) AS pendientes
                        FROM tickets
                        GROUP BY prioridad
                        ORDER BY FIELD(prioridad,'critica','alta','media','baja')
                    """)
                    return cursor.fetchall()
    except Exception as e:
        print(f"[ERROR TicketsPorPrioridad] {e}")
    return []