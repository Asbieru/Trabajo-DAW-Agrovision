from conexion import obtenerconexion


def obtenerAplicaciones():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT DISTINCT aplicacion FROM tickets ORDER BY aplicacion")
            return [row['aplicacion'] for row in cursor.fetchall()]


def reporteResumen():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) AS total_tickets,
                       SUM(estado IN ('abierto','en_progreso')) AS tickets_pendientes,
                       SUM(estado IN ('resuelto','cerrado')) AS tickets_resueltos,
                       (SELECT COUNT(*) FROM proyectos) AS total_proyectos,
                       (SELECT COUNT(*) FROM sprints WHERE estado='activo') AS sprints_activos,
                       (SELECT COUNT(*) FROM usuarios WHERE rol='soporte') AS total_programadores
                FROM tickets
            """)
            return cursor.fetchone()


def reporteTicketsPorApp():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT aplicacion, COUNT(*) AS total,
                       SUM(estado IN ('abierto','en_progreso')) AS pendientes,
                       SUM(estado IN ('resuelto','cerrado')) AS cerrados
                FROM tickets
                GROUP BY aplicacion
                ORDER BY total DESC
            """)
            return cursor.fetchall()


def reporteTicketsPorTipo():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT tipo, COUNT(*) AS total FROM tickets GROUP BY tipo")
            return cursor.fetchall()


def reporteStoryPointsPorProgramador():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.nombre_completo AS programador,
                       COALESCE(SUM(CASE WHEN h.estado='completada'
                           THEN h.story_points ELSE 0 END), 0) AS pts_completados,
                       COALESCE(SUM(h.story_points), 0) AS pts_asignados
                FROM actividades h
                JOIN usuarios u ON h.id_asignado = u.id_usuario
                GROUP BY h.id_asignado, u.nombre_completo
                ORDER BY pts_completados DESC
            """)
            return cursor.fetchall()


def reporteCarryoverPorProgramador():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.nombre_completo AS programador,
                       COUNT(DISTINCT h.id_sprint) AS sprints_con_carryover,
                       COALESCE(SUM(h.story_points), 0) AS pts_carryover
                FROM actividades h
                JOIN sprints s ON h.id_sprint = s.id_sprint
                JOIN usuarios u ON h.id_asignado = u.id_usuario
                WHERE s.estado = 'completado' AND h.estado != 'completada'
                GROUP BY h.id_asignado, u.nombre_completo
                ORDER BY pts_carryover DESC
            """)
            return cursor.fetchall()


def reporteTicketsFiltrados(fecha_inicio=None, fecha_fin=None,
                             aplicacion=None, estado=None, prioridad=None):
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            fi = fecha_inicio.strip() if fecha_inicio and fecha_inicio.strip() else None
            ff = fecha_fin.strip()    if fecha_fin    and fecha_fin.strip()    else None
            ap = aplicacion.strip()   if aplicacion   and aplicacion.strip()   else None
            es = estado.strip()       if estado       and estado.strip()       else None
            pr = prioridad.strip()    if prioridad    and prioridad.strip()    else None

            sql = """
                SELECT t.id_ticket, t.titulo, t.aplicacion,
                       t.tipo, t.prioridad, t.estado,
                       DATE_FORMAT(t.fecha_apertura, '%d/%m/%Y') AS fecha_apertura,
                       u.nombre_completo AS solicitante
                FROM tickets t
                JOIN usuarios u ON t.id_solicitante = u.id_usuario
            """
            condiciones = []
            params      = []

            if fi and ff:
                condiciones.append("DATE(t.fecha_apertura) BETWEEN %s AND %s")
                params += [fi, ff]
            elif fi:
                condiciones.append("DATE(t.fecha_apertura) = %s")
                params.append(fi)
            elif ff:
                condiciones.append("DATE(t.fecha_apertura) = %s")
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