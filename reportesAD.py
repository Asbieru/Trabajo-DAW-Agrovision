from conexion import obtenerconexion


def obtenerAplicaciones():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id_aplicacion, nombre FROM aplicaciones ORDER BY nombre")
            return [dict(r) for r in cursor.fetchall()]


def reporteResumen():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) AS total_tickets,
                       SUM(estado IN ('solicitado', 'en_progreso')) AS tickets_pendientes,
                       SUM(estado IN ('resuelto', 'cerrado'))       AS tickets_resueltos,
                       (SELECT COUNT(*) FROM proyectos)             AS total_proyectos,
                       (SELECT COUNT(*) FROM sprints s
                        JOIN proyectos p ON s.id_proyecto = p.id_proyecto
                        WHERE s.estado = 'activo')                  AS sprints_activos,
                         (SELECT COUNT(*) FROM usuarios u JOIN rol r ON r.id_rol = u.id_rol WHERE r.nombre = 'Programador') AS total_soporte
                FROM tickets
            """)
            return cursor.fetchone()


def reporteTicketsPorApp():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT a.nombre AS aplicacion,
                       COUNT(*) AS total,
                       SUM(t.estado IN ('solicitado', 'en_progreso')) AS pendientes,
                       SUM(t.estado IN ('resuelto', 'cerrado'))       AS cerrados
                FROM tickets t
                JOIN aplicaciones a ON a.id_aplicacion = t.id_aplicacion
                GROUP BY t.id_aplicacion, a.nombre
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
                       COALESCE(SUM(CASE WHEN a.estado = 'completada'
                           THEN a.story_points ELSE 0 END), 0) AS pts_completados,
                       COALESCE(SUM(a.story_points), 0) AS pts_asignados
                FROM actividades a
                JOIN usuarios u ON a.id_asignado = u.id_usuario
                GROUP BY a.id_asignado, u.nombre_completo
                ORDER BY pts_completados DESC
            """)
            return cursor.fetchall()


def reporteCarryoverPorProgramador():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.nombre_completo AS programador,
                       COUNT(DISTINCT a.id_sprint) AS sprints_con_carryover,
                       COALESCE(SUM(a.story_points), 0) AS pts_carryover
                FROM actividades a
                JOIN sprints s ON a.id_sprint = s.id_sprint
                JOIN proyectos p ON s.id_proyecto = p.id_proyecto
                JOIN usuarios u ON a.id_asignado = u.id_usuario
                WHERE s.estado = 'completado'
                  AND a.estado != 'completada'
                GROUP BY a.id_asignado, u.nombre_completo
                ORDER BY pts_carryover DESC
            """)
            return cursor.fetchall()


def reporteTicketsFiltrados(fecha_inicio=None, fecha_fin=None,
                             id_aplicacion=None, estado=None, prioridad=None):
    """
    Devuelve tickets con información completa:
    agente, intensidad, horas de resolución, cumplimiento SLA, calificación.
    """
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            fi = fecha_inicio.strip() if fecha_inicio and fecha_inicio.strip() else None
            ff = fecha_fin.strip()    if fecha_fin    and fecha_fin.strip()    else None
            ap = int(id_aplicacion)   if id_aplicacion else None
            es = estado.strip()       if estado        and estado.strip()      else None
            pr = prioridad.strip()    if prioridad     and prioridad.strip()   else None

            sql = """
                SELECT
                    t.id_ticket,
                    t.titulo,
                    a.nombre                                            AS aplicacion,
                    t.tipo,
                    dt.prioridad,
                    dt.intensidad,
                    t.estado,
                    DATE_FORMAT(t.f_registro, '%d/%m/%Y %H:%i')        AS fecha_apertura,
                    DATE_FORMAT(t.f_cierre,   '%d/%m/%Y %H:%i')        AS fecha_cierre,
                    DATE_FORMAT(dt.f_asignacion_agente, '%d/%m/%Y %H:%i') AS fecha_asignacion,
                    DATE_FORMAT(dt.f_solucion, '%d/%m/%Y %H:%i')       AS fecha_solucion,
                    uSol.nombre_completo                                AS solicitante,
                    uAge.nombre_completo                                AS agente,
                    dt.sla_horas,
                    CASE
                        WHEN dt.f_asignacion_agente IS NOT NULL AND dt.f_solucion IS NOT NULL
                        THEN TIMESTAMPDIFF(MINUTE, dt.f_asignacion_agente, dt.f_solucion)
                        ELSE NULL
                    END                                                 AS minutos_resolucion,
                    CASE
                        WHEN dt.f_asignacion_agente IS NOT NULL AND dt.f_solucion IS NOT NULL
                             AND TIMESTAMPDIFF(HOUR, dt.f_asignacion_agente, dt.f_solucion) <= dt.sla_horas
                        THEN 'SI'
                        WHEN dt.f_asignacion_agente IS NOT NULL AND dt.f_solucion IS NOT NULL
                        THEN 'NO'
                        WHEN dt.f_asignacion_agente IS NULL
                        THEN 'Sin asignar'
                        ELSE '—'
                    END                                                 AS sla_cumplido,
                    c.estrellas                                         AS calificacion,
                    c.observacion                                       AS obs_calificacion
                FROM tickets t
                JOIN aplicaciones a   ON a.id_aplicacion = t.id_aplicacion
                JOIN usuarios uSol    ON uSol.id_usuario  = t.id_solicitante
                LEFT JOIN detalle_ticket dt ON dt.id_ticket = t.id_ticket AND dt.activo = 1
                LEFT JOIN usuarios uAge     ON uAge.id_usuario = dt.id_agente
                LEFT JOIN calificaciones_ticket c ON c.id_detalle = dt.id_detalle
            """
            condiciones, params = [], []

            if fi and ff:
                condiciones.append("DATE(t.f_registro) BETWEEN %s AND %s")
                params += [fi, ff]
            elif fi:
                condiciones.append("DATE(t.f_registro) = %s")
                params.append(fi)
            elif ff:
                condiciones.append("DATE(t.f_registro) = %s")
                params.append(ff)
            if ap:
                condiciones.append("t.id_aplicacion = %s")
                params.append(ap)
            if es:
                condiciones.append("t.estado = %s")
                params.append(es)
            if pr:
                condiciones.append("dt.prioridad = %s")
                params.append(pr)

            if condiciones:
                sql += " WHERE " + " AND ".join(condiciones)
            sql += " ORDER BY t.id_ticket DESC"
            cursor.execute(sql, tuple(params) if params else None)
            return [dict(r) for r in cursor.fetchall()]


def reporteProyectosPorEstado():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT estado, COUNT(*) AS total
                FROM proyectos
                GROUP BY estado
                ORDER BY FIELD(estado,'en_desarrollo','planificado','qa','pausado','completado')
            """)
            return cursor.fetchall()


def reporteProyectosEnRiesgo():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT p.id_proyecto, p.nombre, p.estado,
                       p.fecha_fin_plan,
                       u.nombre_completo                          AS responsable,
                       DATEDIFF(CURDATE(), p.fecha_fin_plan)      AS dias_vencido,
                       CASE WHEN p.estado = 'eliminado' THEN 0 ELSE 1 END AS estado2
                FROM proyectos p
                JOIN usuarios u ON p.id_Stakeholder = u.id_usuario
                WHERE p.fecha_fin_plan < CURDATE()
                  AND p.estado NOT IN ('completado','eliminado')
                ORDER BY dias_vencido DESC
            """)
            return cursor.fetchall()


def reporteRendimientoPorSprint():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT s.nombre AS sprint,
                       p.nombre AS proyecto,
                       s.capacidad_pts,
                       COALESCE(SUM(CASE WHEN a.estado = 'completada'
                           THEN a.story_points ELSE 0 END), 0) AS pts_completados,
                       COALESCE(SUM(CASE WHEN a.estado NOT IN ('completada','cancelada')
                           THEN a.story_points ELSE 0 END), 0) AS pts_pendientes,
                       s.estado AS estado_sprint,
                       CASE WHEN p.estado = 'eliminado' THEN 0 ELSE 1 END AS estado2
                FROM sprints s
                JOIN proyectos p ON s.id_proyecto = p.id_proyecto
                LEFT JOIN actividades a ON a.id_sprint = s.id_sprint
                GROUP BY s.id_sprint
                ORDER BY s.fecha_inicio DESC
            """)
            return cursor.fetchall()


def obtenerResponsables():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT u.id_usuario, u.nombre_completo
                FROM proyectos p
                JOIN usuarios u ON p.id_Stakeholder = u.id_usuario
                ORDER BY u.nombre_completo
            """)
            return cursor.fetchall()


def reporteProyectosFiltrados(estado=None, id_responsable=None):
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            sql = """
                SELECT p.id_proyecto, p.nombre, p.estado,
                       p.fecha_inicio, p.fecha_fin_plan,
                       u.nombre_completo AS responsable,
                       DATEDIFF(p.fecha_fin_plan, CURDATE()) AS dias_restantes,
                       CASE WHEN p.estado = 'eliminado' THEN 0 ELSE 1 END AS estado2,
                       CASE
                           WHEN p.estado = 'completado'             THEN 'completado'
                           WHEN p.fecha_fin_plan < CURDATE()        THEN 'vencido'
                           WHEN DATEDIFF(p.fecha_fin_plan, CURDATE()) <= 7 THEN 'por_vencer'
                           ELSE 'ok'
                       END AS salud,
                       COALESCE(ROUND(
                           SUM(CASE WHEN a.estado = 'completada' THEN a.story_points ELSE 0 END)
                           / NULLIF(SUM(a.story_points), 0) * 100, 0
                       ), 0) AS pct_avance
                FROM proyectos p
                JOIN usuarios u ON p.id_Stakeholder = u.id_usuario
                LEFT JOIN actividades a  ON a.id_proyecto = p.id_proyecto AND a.estado2 = 1
            """
            condiciones, params = [], []
            if estado:
                condiciones.append("p.estado = %s")
                params.append(estado)
            if id_responsable:
                condiciones.append("p.id_Stakeholder = %s")
                params.append(id_responsable)
            if condiciones:
                sql += " WHERE " + " AND ".join(condiciones)
            sql += " GROUP BY p.id_proyecto ORDER BY p.id_proyecto DESC"
            cursor.execute(sql, tuple(params) if params else None)
            return cursor.fetchall()

def reporteActividadesPorProyecto(id_proyecto):
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT a.id_actividad,
                       a.codigo,
                       a.titulo,
                       a.prioridad,
                       a.estado,
                       a.story_points,
                       CASE WHEN a.estado = 'eliminado' THEN 0 ELSE 1 END AS estado2,
                       COALESCE(s.nombre, '—') AS sprint,
                       COALESCE(u.nombre_completo, '—') AS asignado
                FROM actividades a
                LEFT JOIN sprints  s ON a.id_sprint   = s.id_sprint
                LEFT JOIN usuarios u ON a.id_asignado = u.id_usuario
                WHERE a.id_proyecto = %s
                ORDER BY (a.estado != 'eliminado') DESC, a.created_at DESC
            """, (id_proyecto,))
            return [dict(r) for r in cursor.fetchall()]


def resumenActividadesReporte(id_proyecto):
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    COUNT(*) AS total,
                    COALESCE(SUM(estado = 'completada'),  0) AS completadas,
                    COALESCE(SUM(estado = 'en_progreso'), 0) AS en_progreso,
                    COALESCE(SUM(estado IN ('backlog','por_hacer')), 0) AS pendientes,
                    COALESCE(SUM(estado = 'cancelada'),   0) AS canceladas,
                    COALESCE(SUM(story_points), 0) AS total_pts,
                    COALESCE(SUM(CASE WHEN estado = 'completada' THEN story_points ELSE 0 END), 0) AS pts_completados
                FROM actividades
                WHERE id_proyecto = %s
            """, (id_proyecto,))
            return dict(cursor.fetchone())


def reporteSLAPorAplicacion():
    """Cumplimiento de SLA por aplicación (desde asignación hasta solución)."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT a.nombre AS aplicacion,
                       COUNT(*) AS total_resueltos,
                       SUM(TIMESTAMPDIFF(HOUR, dt.f_asignacion_agente, dt.f_solucion) <= dt.sla_horas) AS sla_ok,
                       SUM(TIMESTAMPDIFF(HOUR, dt.f_asignacion_agente, dt.f_solucion) > dt.sla_horas)  AS sla_ko,
                       ROUND(SUM(TIMESTAMPDIFF(HOUR, dt.f_asignacion_agente, dt.f_solucion) <= dt.sla_horas)
                             / COUNT(*) * 100, 1) AS pct_cumplido
                FROM tickets t
                JOIN aplicaciones a ON a.id_aplicacion = t.id_aplicacion
                JOIN detalle_ticket dt ON dt.id_ticket = t.id_ticket
                WHERE dt.f_asignacion_agente IS NOT NULL AND dt.f_solucion IS NOT NULL
                GROUP BY t.id_aplicacion, a.nombre
                ORDER BY pct_cumplido ASC
            """)
            return [dict(r) for r in cursor.fetchall()]


def reporteTicketsPorEstado():
    """Tickets agrupados por estado."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT estado, COUNT(*) AS total
                FROM tickets
                GROUP BY estado
                ORDER BY FIELD(estado,'solicitado','en_progreso','resuelto','cerrado','cancelado')
            """)
            return [dict(r) for r in cursor.fetchall()]


def reporteAgentesMetricas():
    """Tabla completa de agentes: atendidos, resueltos, SLA, promedio resolución, satisfacción."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.nombre_completo AS agente,
                       COUNT(*) AS total_atendidos,
                       SUM(t.estado IN ('resuelto','cerrado')) AS resueltos,
                       SUM(dt.f_solucion IS NOT NULL AND
                           TIMESTAMPDIFF(HOUR, dt.f_asignacion_agente, dt.f_solucion) <= dt.sla_horas) AS sla_ok,
                       ROUND(SUM(dt.f_solucion IS NOT NULL AND
                           TIMESTAMPDIFF(HOUR, dt.f_asignacion_agente, dt.f_solucion) <= dt.sla_horas)
                           / NULLIF(SUM(dt.f_solucion IS NOT NULL), 0) * 100, 1) AS pct_sla,
                       ROUND(AVG(CASE WHEN dt.f_solucion IS NOT NULL
                           THEN TIMESTAMPDIFF(HOUR, dt.f_asignacion_agente, dt.f_solucion) END), 1) AS promedio_horas,
                       ROUND(AVG(c.estrellas), 1) AS satisfaccion
                FROM tickets t
                JOIN detalle_ticket dt ON dt.id_ticket = t.id_ticket AND dt.activo = 1
                JOIN usuarios u ON dt.id_agente = u.id_usuario
                LEFT JOIN calificaciones_ticket c ON c.id_detalle = dt.id_detalle
                WHERE dt.id_agente IS NOT NULL
                GROUP BY dt.id_agente, u.nombre_completo
                ORDER BY total_atendidos DESC
            """)
            return [dict(r) for r in cursor.fetchall()]


def reporteTendenciaPorMes():
    """Tickets por mes — todos los datos disponibles."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT DATE_FORMAT(f_registro, '%Y-%m') AS mes,
                       DATE_FORMAT(f_registro, '%b %Y') AS mes_label,
                       COUNT(*) AS total,
                       SUM(estado IN ('resuelto','cerrado')) AS resueltos,
                       SUM(estado = 'cancelado') AS cancelados
                FROM tickets
                GROUP BY mes, mes_label
                ORDER BY mes ASC
            """)
            return [dict(r) for r in cursor.fetchall()]