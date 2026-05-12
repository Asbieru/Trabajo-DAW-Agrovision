from conexion import obtenerconexion

def resumenKPI():
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  "SELECT COUNT(*) AS total,"
                    sql += " SUM(estado='abierto') AS abiertos,"
                    sql += " SUM(estado='en_progreso') AS en_progreso,"
                    sql += " SUM(estado='resuelto') AS resueltos,"
                    sql += " SUM(estado='cerrado') AS cerrados,"
                    sql += " SUM(fecha_resolucion IS NOT NULL AND"
                    sql += " TIMESTAMPDIFF(HOUR, fecha_apertura, fecha_resolucion) <= sla_horas) AS sla_ok,"
                    sql += " SUM(fecha_resolucion IS NOT NULL) AS total_con_fecha,"
                    sql += " ROUND(AVG(CASE WHEN fecha_resolucion IS NOT NULL"
                    sql += " THEN TIMESTAMPDIFF(HOUR, fecha_apertura, fecha_resolucion) END), 1)"
                    sql += " AS promedio_horas_resolucion"
                    sql += " FROM tickets"
                    cursor.execute(sql)
                    row = cursor.fetchone()
                    if row and row['total_con_fecha']:
                        row['pct_sla'] = round(row['sla_ok'] / row['total_con_fecha'] * 100, 1)
                    else:
                        row['pct_sla'] = 0
                    return row
        return {}
    except:
        return {}

def kpiPorAplicacion():
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  "SELECT aplicacion, COUNT(*) AS total"
                    sql += " FROM tickets"
                    sql += " GROUP BY aplicacion"
                    sql += " ORDER BY total DESC"
                    sql += " LIMIT 10"
                    cursor.execute(sql)
                    return cursor.fetchall()
        return []
    except:
        return []

def kpiPorPrioridad():
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  "SELECT prioridad, COUNT(*) AS total"
                    sql += " FROM tickets"
                    sql += " GROUP BY prioridad"
                    sql += " ORDER BY FIELD(prioridad,'critica','alta','media','baja')"
                    cursor.execute(sql)
                    return cursor.fetchall()
        return []
    except:
        return []

def kpiPorAgente():
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  "SELECT u.nombre_completo AS agente,"
                    sql += " COUNT(*) AS total_atendidos,"
                    sql += " SUM(t.estado IN ('resuelto','cerrado')) AS resueltos,"
                    sql += " ROUND(AVG(CASE WHEN t.fecha_resolucion IS NOT NULL"
                    sql += " THEN TIMESTAMPDIFF(HOUR, t.fecha_apertura, t.fecha_resolucion)"
                    sql += " END), 1) AS promedio_horas"
                    sql += " FROM tickets t"
                    sql += " JOIN usuarios u ON t.id_agente = u.id_usuario"
                    sql += " WHERE t.id_agente IS NOT NULL"
                    sql += " GROUP BY t.id_agente"
                    sql += " ORDER BY total_atendidos DESC"
                    cursor.execute(sql)
                    return cursor.fetchall()
        return []
    except:
        return []

def kpiPorMes():
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  "SELECT DATE_FORMAT(fecha_apertura, '%%Y-%%m') AS mes,"
                    sql += " DATE_FORMAT(fecha_apertura, '%%b %%Y') AS mes_label,"
                    sql += " COUNT(*) AS total,"
                    sql += " SUM(estado IN ('resuelto','cerrado')) AS resueltos"
                    sql += " FROM tickets"
                    sql += " WHERE fecha_apertura >= DATE_SUB(NOW(), INTERVAL 6 MONTH)"
                    sql += " GROUP BY mes, mes_label"
                    sql += " ORDER BY mes ASC"
                    cursor.execute(sql)
                    return cursor.fetchall()
        return []
    except:
        return []

def kpiSprintsActivos():
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql =  "SELECT s.nombre AS sprint, p.nombre AS proyecto,"
                    sql += " s.capacidad_pts,"
                    sql += " COALESCE(SUM(CASE WHEN h.estado='completada'"
                    sql += " THEN h.story_points ELSE 0 END),0) AS pts_completados,"
                    sql += " COALESCE(SUM(CASE WHEN h.estado='en_progreso'"
                    sql += " THEN h.story_points ELSE 0 END),0) AS pts_en_progreso,"
                    sql += " DATEDIFF(s.fecha_fin, CURDATE()) AS dias_restantes"
                    sql += " FROM sprints s"
                    sql += " JOIN proyectos p ON s.id_proyecto = p.id_proyecto"
                    sql += " LEFT JOIN historias h ON h.id_sprint = s.id_sprint"
                    sql += " WHERE s.estado = 'activo'"
                    sql += " GROUP BY s.id_sprint"
                    cursor.execute(sql)
                    return cursor.fetchall()
        return []
    except:
        return []