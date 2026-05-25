from conexion import obtenerconexion
from ticketAD import asegurarTablaCalificacionesTicket

MESES_CORTO = {
    1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr',
    5: 'May', 6: 'Jun', 7: 'Jul', 8: 'Ago',
    9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
}

def resumenKPI():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) AS total,
                       SUM(estado='abierto') AS abiertos,
                       SUM(estado='en_progreso') AS en_progreso,
                       SUM(estado='resuelto') AS resueltos,
                       SUM(estado='cerrado') AS cerrados,
                       SUM(fecha_resolucion IS NOT NULL AND
                           TIMESTAMPDIFF(HOUR, fecha_apertura, fecha_resolucion) <= sla_horas) AS sla_ok,
                       SUM(fecha_resolucion IS NOT NULL) AS total_con_fecha,
                       ROUND(AVG(CASE WHEN fecha_resolucion IS NOT NULL
                           THEN TIMESTAMPDIFF(HOUR, fecha_apertura, fecha_resolucion) END), 1)
                           AS promedio_horas_resolucion
                FROM tickets
            """)
            row = dict(cursor.fetchone())
            if row.get('total_con_fecha'):
                row['pct_sla'] = round(row['sla_ok'] / row['total_con_fecha'] * 100, 1)
            else:
                row['pct_sla'] = 0
            return row


def kpiPorAplicacion():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT aplicacion, COUNT(*) AS total
                FROM tickets
                GROUP BY aplicacion
                ORDER BY total DESC
                LIMIT 10
            """)
            return [dict(r) for r in cursor.fetchall()]


def kpiPorPrioridad():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT prioridad, COUNT(*) AS total
                FROM tickets
                GROUP BY prioridad
                ORDER BY FIELD(prioridad,'critica','alta','media','baja')
            """)
            return [dict(r) for r in cursor.fetchall()]


def kpiPorAgente():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.nombre_completo AS agente,
                       COUNT(*) AS total_atendidos,
                       SUM(t.estado IN ('resuelto','cerrado')) AS resueltos,
                       ROUND(AVG(CASE WHEN t.fecha_resolucion IS NOT NULL
                           THEN TIMESTAMPDIFF(HOUR, t.fecha_apertura, t.fecha_resolucion)
                           END), 1) AS promedio_horas
                FROM tickets t
                JOIN usuarios u ON t.id_agente = u.id_usuario
                WHERE t.id_agente IS NOT NULL
                GROUP BY t.id_agente
                ORDER BY total_atendidos DESC
            """)
            return [dict(r) for r in cursor.fetchall()]


def kpiPorMes():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT DATE_FORMAT(fecha_apertura, '%Y-%m') AS mes,
                       MONTH(fecha_apertura) AS num_mes,
                       YEAR(fecha_apertura) AS anio,
                       COUNT(*) AS total,
                       SUM(estado IN ('resuelto','cerrado')) AS resueltos
                FROM tickets
                WHERE fecha_apertura >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
                GROUP BY mes, num_mes, anio
                ORDER BY mes ASC
            """)
            resultado = []
            for f in cursor.fetchall():
                f = dict(f)
                f['mes_label'] = MESES_CORTO.get(f['num_mes'], '?') + ' ' + str(f['anio'])
                resultado.append(f)
            return resultado


def kpiSprintsActivos():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT s.nombre AS sprint, p.nombre AS proyecto,
                       s.capacidad_pts,
                       COALESCE(SUM(CASE WHEN h.estado='completada'
                           THEN h.story_points ELSE 0 END),0) AS pts_completados,
                       COALESCE(SUM(CASE WHEN h.estado='en_progreso'
                           THEN h.story_points ELSE 0 END),0) AS pts_en_progreso,
                       DATEDIFF(s.fecha_fin, CURDATE()) AS dias_restantes
                FROM sprints s
                JOIN proyectos p ON s.id_proyecto = p.id_proyecto
                LEFT JOIN actividades h ON h.id_sprint = s.id_sprint
                WHERE s.estado = 'activo'
                GROUP BY s.id_sprint
            """)
            return [dict(r) for r in cursor.fetchall()]


def kpiSatisfaccion():
    asegurarTablaCalificacionesTicket()
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) AS total_atendidos,
                       SUM(c.id_calificacion IS NOT NULL) AS total_calificados,
                       ROUND(AVG(c.estrellas), 1) AS promedio_estrellas,
                       SUM(c.estrellas >= 4) AS valoraciones_positivas
                FROM tickets t
                LEFT JOIN calificaciones_ticket c ON c.id_ticket = t.id_ticket
                WHERE t.estado IN ('resuelto', 'cerrado', 'base_proyecto')
            """)
            row = dict(cursor.fetchone())
            total_calificados = row.get('total_calificados') or 0
            if total_calificados:
                row['pct_positivas'] = round((row.get('valoraciones_positivas') or 0) / total_calificados * 100, 1)
            else:
                row['pct_positivas'] = 0
            return row


def comentariosCalificacionesRecientes(limit=6):
    asegurarTablaCalificacionesTicket()
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT c.estrellas, c.observacion, c.fecha_calificacion,
                       t.id_ticket, t.titulo,
                       u.nombre_completo AS solicitante,
                       a.nombre_completo AS agente
                FROM calificaciones_ticket c
                JOIN tickets t ON t.id_ticket = c.id_ticket
                JOIN usuarios u ON u.id_usuario = t.id_solicitante
                LEFT JOIN usuarios a ON a.id_usuario = t.id_agente
                ORDER BY c.fecha_calificacion DESC, c.id_calificacion DESC
                LIMIT %s
            """, (limit,))
            return [dict(r) for r in cursor.fetchall()]
        

def kpiProyectosPorEstado():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT estado, COUNT(*) AS total
                FROM proyectos
                GROUP BY estado
                ORDER BY FIELD(estado,'en_desarrollo','planificado','qa','pausado','completado')
            """)
            return [dict(r) for r in cursor.fetchall()]


def kpiVelocityPorSprint():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT s.nombre AS sprint,
                       p.nombre AS proyecto,
                       s.capacidad_pts,
                       COALESCE(SUM(CASE WHEN a.estado='completada'
                           THEN a.story_points ELSE 0 END), 0) AS pts_completados
                FROM sprints s
                JOIN proyectos p ON s.id_proyecto = p.id_proyecto
                LEFT JOIN actividades a ON a.id_sprint = s.id_sprint
                WHERE s.estado IN ('activo','completado')
                GROUP BY s.id_sprint
                ORDER BY s.fecha_inicio ASC
                LIMIT 8
            """)
            return [dict(r) for r in cursor.fetchall()]


def kpiCargaPorProgramador():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.nombre_completo AS programador,
                       COUNT(a.id_actividad) AS total_activas,
                       SUM(CASE WHEN a.estado='en_progreso' THEN 1 ELSE 0 END) AS en_progreso,
                       SUM(CASE WHEN a.estado='por_hacer'   THEN 1 ELSE 0 END) AS por_hacer,
                       COALESCE(SUM(a.story_points), 0) AS pts_asignados
                FROM usuarios u
                JOIN actividades a ON a.id_asignado = u.id_usuario
                WHERE a.estado IN ('en_progreso','por_hacer','backlog')
                GROUP BY u.id_usuario
                ORDER BY total_activas DESC
            """)
            return [dict(r) for r in cursor.fetchall()]

def kpiProyectosPorEstado():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT estado, COUNT(*) AS total
                FROM proyectos
                GROUP BY estado
                ORDER BY FIELD(estado,'en_desarrollo','planificado','qa','pausado','completado')
            """)
            return [dict(r) for r in cursor.fetchall()]


def kpiVelocityPorSprint():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT s.nombre AS sprint,
                       p.nombre AS proyecto,
                       s.capacidad_pts,
                       COALESCE(SUM(CASE WHEN a.estado='completada'
                           THEN a.story_points ELSE 0 END), 0) AS pts_completados
                FROM sprints s
                JOIN proyectos p ON s.id_proyecto = p.id_proyecto
                LEFT JOIN actividades a ON a.id_sprint = s.id_sprint
                WHERE s.estado IN ('activo','completado')
                GROUP BY s.id_sprint
                ORDER BY s.fecha_inicio ASC
                LIMIT 8
            """)
            return [dict(r) for r in cursor.fetchall()]


def kpiCargaPorProgramador():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.nombre_completo AS programador,
                       COUNT(a.id_actividad) AS total_activas,
                       SUM(CASE WHEN a.estado='en_progreso' THEN 1 ELSE 0 END) AS en_progreso,
                       SUM(CASE WHEN a.estado='por_hacer'   THEN 1 ELSE 0 END) AS por_hacer,
                       COALESCE(SUM(a.story_points), 0) AS pts_asignados
                FROM usuarios u
                JOIN actividades a ON a.id_asignado = u.id_usuario
                WHERE a.estado IN ('en_progreso','por_hacer','backlog')
                GROUP BY u.id_usuario
                ORDER BY total_activas DESC
            """)
            return [dict(r) for r in cursor.fetchall()]


def kpiProyectosFiltrados(estado=None, id_responsable=None):
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            sql = """
                SELECT p.id_proyecto, p.nombre, p.estado,
                       p.fecha_inicio, p.fecha_fin_plan,
                       u.nombre_completo AS responsable,
                       DATEDIFF(p.fecha_fin_plan, CURDATE()) AS dias_restantes,
                       COALESCE(
                           ROUND(
                               SUM(CASE WHEN a.estado='completada' THEN a.story_points ELSE 0 END)
                               / NULLIF(SUM(a.story_points), 0) * 100
                           ), 0
                       ) AS pct_avance,
                       CASE
                           WHEN p.estado = 'completado' THEN 'completado'
                           WHEN p.fecha_fin_plan < CURDATE() THEN 'vencido'
                           WHEN DATEDIFF(p.fecha_fin_plan, CURDATE()) <= 7 THEN 'por_vencer'
                           ELSE 'ok'
                       END AS salud
                FROM proyectos p
                JOIN usuarios u ON p.id_responsable = u.id_usuario
                LEFT JOIN actividades a ON a.id_proyecto = p.id_proyecto
                    AND a.estado != 'cancelada'
            """
            condiciones = []
            params = []
            if estado:
                condiciones.append("p.estado = %s")
                params.append(estado)
            if id_responsable:
                condiciones.append("p.id_responsable = %s")
                params.append(id_responsable)
            if condiciones:
                sql += " WHERE " + " AND ".join(condiciones)
            sql += " GROUP BY p.id_proyecto ORDER BY p.fecha_fin_plan ASC"
            cursor.execute(sql, tuple(params) if params else None)
            return [dict(r) for r in cursor.fetchall()]


def obtenerResponsablesProyecto():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT DISTINCT u.id_usuario, u.nombre_completo
                FROM proyectos p
                JOIN usuarios u ON p.id_responsable = u.id_usuario
                ORDER BY u.nombre_completo
            """)
            return [dict(r) for r in cursor.fetchall()]