import csv
import io
from conexion import obtenerconexion

def obtenerAplicaciones():
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql = "SELECT DISTINCT aplicacion FROM tickets ORDER BY aplicacion"
                    cursor.execute(sql)
                    return [row['aplicacion'] for row in cursor.fetchall()]
        return []
    except Exception as e:
        print(f"[ERROR obtenerAplicaciones] {e}")
        return []

def reporteResumen():
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  "SELECT COUNT(*) AS total_tickets,"
                    sql += " SUM(estado IN ('abierto','en_progreso')) AS tickets_pendientes,"
                    sql += " SUM(estado IN ('resuelto','cerrado')) AS tickets_resueltos,"
                    sql += " (SELECT COUNT(*) FROM proyectos) AS total_proyectos,"
                    sql += " (SELECT COUNT(*) FROM sprints WHERE estado='activo') AS sprints_activos,"
                    sql += " (SELECT COUNT(*) FROM usuarios WHERE rol='soporte') AS total_programadores"
                    sql += " FROM tickets"
                    cursor.execute(sql)
                    return cursor.fetchone()
        return {}
    except Exception as e:
        print(f"[ERROR reporteResumen] {e}")
        return {}

def reporteTicketsPorApp():
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  "SELECT aplicacion, COUNT(*) AS total,"
                    sql += " SUM(estado IN ('abierto','en_progreso')) AS pendientes,"
                    sql += " SUM(estado IN ('resuelto','cerrado')) AS cerrados"
                    sql += " FROM tickets"
                    sql += " GROUP BY aplicacion"
                    sql += " ORDER BY total DESC"
                    cursor.execute(sql)
                    return cursor.fetchall()
        return []
    except Exception as e:
        print(f"[ERROR reporteTicketsPorApp] {e}")
        return []

def reporteTicketsPorTipo():
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  "SELECT tipo, COUNT(*) AS total"
                    sql += " FROM tickets"
                    sql += " GROUP BY tipo"
                    cursor.execute(sql)
                    return cursor.fetchall()
        return []
    except Exception as e:
        print(f"[ERROR reporteTicketsPorTipo] {e}")
        return []

def reporteStoryPointsPorProgramador():
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  "SELECT u.nombre_completo AS programador,"
                    sql += " COALESCE(SUM(CASE WHEN h.estado='completada'"
                    sql += " THEN h.story_points ELSE 0 END), 0) AS pts_completados,"
                    sql += " COALESCE(SUM(h.story_points), 0) AS pts_asignados"
                    sql += " FROM historias h"
                    sql += " JOIN usuarios u ON h.id_asignado = u.id_usuario"
                    sql += " GROUP BY h.id_asignado, u.nombre_completo"
                    sql += " ORDER BY pts_completados DESC"
                    cursor.execute(sql)
                    return cursor.fetchall()
        return []
    except Exception as e:
        print(f"[ERROR reporteStoryPointsPorProgramador] {e}")
        return []

def reporteCarryoverPorProgramador():
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  "SELECT u.nombre_completo AS programador,"
                    sql += " COUNT(DISTINCT h.id_sprint) AS sprints_con_carryover,"
                    sql += " COALESCE(SUM(h.story_points), 0) AS pts_carryover"
                    sql += " FROM historias h"
                    sql += " JOIN sprints s ON h.id_sprint = s.id_sprint"
                    sql += " JOIN usuarios u ON h.id_asignado = u.id_usuario"
                    sql += " WHERE s.estado = 'completado'"
                    sql += " AND h.estado != 'completada'"
                    sql += " GROUP BY h.id_asignado, u.nombre_completo"
                    sql += " ORDER BY pts_carryover DESC"
                    cursor.execute(sql)
                    return cursor.fetchall()
        return []
    except Exception as e:
        print(f"[ERROR reporteCarryoverPorProgramador] {e}")
        return []

def reporteTicketsFiltrados(fecha_inicio=None, fecha_fin=None,
                             aplicacion=None, estado=None, prioridad=None):
    try:
        conn = obtenerconexion()
        if not conn:
            return []
        with conn:
            with conn.cursor() as cursor:

                fi = fecha_inicio.strip() if fecha_inicio and fecha_inicio.strip() else None
                ff = fecha_fin.strip()    if fecha_fin    and fecha_fin.strip()    else None
                ap = aplicacion.strip()   if aplicacion   and aplicacion.strip()   else None
                es = estado.strip()       if estado       and estado.strip()       else None
                pr = prioridad.strip()    if prioridad    and prioridad.strip()    else None

                sql =  "SELECT t.id_ticket, t.titulo, t.aplicacion,"
                sql += " t.tipo, t.prioridad, t.estado,"
                sql += " DATE_FORMAT(t.fecha_apertura, '%%d/%%m/%%Y') AS fecha_apertura,"
                sql += " u.nombre_completo AS solicitante"
                sql += " FROM tickets t"
                sql += " JOIN usuarios u ON t.id_solicitante = u.id_usuario"

                condiciones = []
                params      = []

                if fi:
                    condiciones.append("DATE(t.fecha_apertura) >= %s")
                    params.append(fi)
                if ff:
                    condiciones.append("DATE(t.fecha_apertura) <= %s")
                    params.append(ff)
                if ap:
                    condiciones.append("t.aplicacion = %s")
                    params.append(ap)
                if es:
                    condiciones.append("t.estado = %s")
                    params.append(es)
                if pr:
                    condiciones.append("t.prioridad = %s")
                    params.append(pr)

                if condiciones:
                    sql += " WHERE " + " AND ".join(condiciones)

                sql += " ORDER BY t.fecha_apertura DESC"

                cursor.execute(sql, tuple(params) if params else None)
                return cursor.fetchall()
    except Exception as e:
        print(f"[ERROR reporteTicketsFiltrados] {e}")
        return []

def generarCSV(tickets):
    try:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['#', 'Titulo', 'Aplicacion', 'Tipo',
                         'Prioridad', 'Estado', 'Solicitante', 'Fecha'])
        for t in tickets:
            writer.writerow([
                t['id_ticket'], t['titulo'], t['aplicacion'],
                t['tipo'], t['prioridad'], t['estado'],
                t['solicitante'], t['fecha_apertura']
            ])
        return output.getvalue()
    except Exception as e:
        print(f"[ERROR generarCSV] {e}")
        return ''