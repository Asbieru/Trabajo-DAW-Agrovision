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
                       SUM(t.estado = 'solicitado') AS abiertos,
                       SUM(t.estado = 'en_progreso') AS en_progreso,
                       SUM(t.estado = 'resuelto') AS resueltos,
                       SUM(t.estado IN ('cerrado', 'cancelado')) AS cerrados,
                       SUM(dt.f_asignacion_agente IS NOT NULL AND dt.f_solucion IS NOT NULL AND
                           TIMESTAMPDIFF(HOUR, dt.f_asignacion_agente, dt.f_solucion) <= dt.sla_horas) AS sla_ok,
                       SUM(dt.f_asignacion_agente IS NOT NULL AND dt.f_solucion IS NOT NULL) AS total_con_fecha,
                       ROUND(AVG(CASE WHEN dt.f_asignacion_agente IS NOT NULL AND dt.f_solucion IS NOT NULL
                           THEN TIMESTAMPDIFF(HOUR, dt.f_asignacion_agente, dt.f_solucion) END), 1)
                           AS promedio_horas_resolucion
                FROM tickets t
                LEFT JOIN detalle_ticket dt ON dt.id_ticket = t.id_ticket
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
                SELECT a.nombre AS aplicacion, COUNT(*) AS total
                FROM tickets t
                JOIN aplicaciones a ON a.id_aplicacion = t.id_aplicacion
                GROUP BY t.id_aplicacion, a.nombre
                ORDER BY total DESC
                LIMIT 10
            """)
            return [dict(r) for r in cursor.fetchall()]


def kpiPorPrioridad():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT dt.prioridad, COUNT(*) AS total
                FROM tickets t
                JOIN detalle_ticket dt ON dt.id_ticket = t.id_ticket
                GROUP BY dt.prioridad
                ORDER BY FIELD(dt.prioridad, 'critica', 'alta', 'media', 'baja')
            """)
            return [dict(r) for r in cursor.fetchall()]


def kpiPorAgente():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.nombre_completo AS agente,
                       COUNT(*) AS total_atendidos,
                       SUM(t.estado IN ('resuelto', 'cerrado')) AS resueltos,
                       ROUND(AVG(CASE WHEN dt.f_asignacion_agente IS NOT NULL AND dt.f_solucion IS NOT NULL
                           THEN TIMESTAMPDIFF(HOUR, dt.f_asignacion_agente, dt.f_solucion)
                           END), 1) AS promedio_horas
                FROM tickets t
                JOIN detalle_ticket dt ON dt.id_ticket = t.id_ticket
                JOIN usuarios u ON dt.id_agente = u.id_usuario
                WHERE dt.id_agente IS NOT NULL
                GROUP BY dt.id_agente
                ORDER BY total_atendidos DESC
            """)
            return [dict(r) for r in cursor.fetchall()]


def kpiPorMes():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            # Intentar últimos 12 meses primero
            cursor.execute("""
                SELECT DATE_FORMAT(t.f_registro, '%Y-%m') AS mes,
                       MONTH(t.f_registro) AS num_mes,
                       YEAR(t.f_registro) AS anio,
                       COUNT(*) AS total,
                       SUM(t.estado IN ('resuelto', 'cerrado')) AS resueltos
                FROM tickets t
                WHERE t.f_registro >= DATE_SUB(NOW(), INTERVAL 12 MONTH)
                GROUP BY mes, num_mes, anio
                ORDER BY mes ASC
            """)
            rows = cursor.fetchall()

            # Si no hay datos en el rango, mostrar todos los disponibles
            if not rows:
                cursor.execute("""
                    SELECT DATE_FORMAT(t.f_registro, '%Y-%m') AS mes,
                           MONTH(t.f_registro) AS num_mes,
                           YEAR(t.f_registro) AS anio,
                           COUNT(*) AS total,
                           SUM(t.estado IN ('resuelto', 'cerrado')) AS resueltos
                    FROM tickets t
                    GROUP BY mes, num_mes, anio
                    ORDER BY mes ASC
                """)
                rows = cursor.fetchall()

            resultado = []
            for f in rows:
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
                       COALESCE(SUM(CASE WHEN a.estado = 'completada'
                           THEN a.story_points ELSE 0 END), 0) AS pts_completados,
                       COALESCE(SUM(CASE WHEN a.estado = 'en_progreso'
                           THEN a.story_points ELSE 0 END), 0) AS pts_en_progreso,
                       DATEDIFF(s.fecha_fin, CURDATE()) AS dias_restantes
                FROM sprints s
                JOIN proyectos p ON s.id_proyecto = p.id_proyecto
                LEFT JOIN actividades a ON a.id_sprint = s.id_sprint
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
                WHERE t.estado IN ('resuelto', 'cerrado')
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
                LEFT JOIN detalle_ticket dt ON dt.id_ticket = t.id_ticket
                LEFT JOIN usuarios a ON a.id_usuario = dt.id_agente
                ORDER BY c.fecha_calificacion DESC, c.id_calificacion DESC
                LIMIT %s
            """, (limit,))
            return [dict(r) for r in cursor.fetchall()]


def kpiProyectosPorEstado():
    """Cuenta proyectos activos agrupados por estado."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT estado, COUNT(*) AS total
                FROM proyectos
                WHERE estado != 'eliminado'
                GROUP BY estado
                ORDER BY FIELD(estado, 'en_desarrollo', 'planificado', 'qa', 'pausado', 'completado')
            """)
            return [dict(r) for r in cursor.fetchall()]


def kpiVelocityPorSprint():
    """Velocity (pts completados vs capacidad) de los últimos 8 sprints."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT s.nombre AS sprint,
                       p.nombre AS proyecto,
                       s.capacidad_pts,
                       COALESCE(SUM(CASE WHEN a.estado = 'completada'
                           THEN a.story_points ELSE 0 END), 0) AS pts_completados
                FROM sprints s
                JOIN proyectos p ON s.id_proyecto = p.id_proyecto
                LEFT JOIN actividades a ON a.id_sprint = s.id_sprint
                WHERE s.estado IN ('activo', 'completado')
                GROUP BY s.id_sprint
                ORDER BY s.fecha_inicio ASC
                LIMIT 8
            """)
            return [dict(r) for r in cursor.fetchall()]


def kpiCargaPorProgramador():
    """Actividades activas y story points asignados por programador."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.nombre_completo AS programador,
                       COUNT(a.id_actividad) AS total_activas,
                       SUM(CASE WHEN a.estado = 'en_progreso' THEN 1 ELSE 0 END) AS en_progreso,
                       SUM(CASE WHEN a.estado = 'por_hacer'   THEN 1 ELSE 0 END) AS por_hacer,
                       COALESCE(SUM(a.story_points), 0) AS pts_asignados
                FROM usuarios u
                JOIN actividades a ON a.id_asignado = u.id_usuario
                WHERE a.estado IN ('en_progreso', 'por_hacer', 'backlog')
                  AND a.estado2 = 1
                GROUP BY u.id_usuario
                ORDER BY total_activas DESC
            """)
            return [dict(r) for r in cursor.fetchall()]


def kpiTiempoResolucionPorAplicacion():
    """Tiempo promedio de resolución (desde asignación hasta solución) por aplicación."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT a.nombre AS aplicacion,
                       COUNT(*) AS total_resueltos,
                       ROUND(AVG(
                           TIMESTAMPDIFF(HOUR, dt.f_asignacion_agente, dt.f_solucion)
                       ), 1) AS promedio_horas,
                       ROUND(MIN(
                           TIMESTAMPDIFF(HOUR, dt.f_asignacion_agente, dt.f_solucion)
                       ), 1) AS minimo_horas,
                       ROUND(MAX(
                           TIMESTAMPDIFF(HOUR, dt.f_asignacion_agente, dt.f_solucion)
                       ), 1) AS maximo_horas
                FROM tickets t
                JOIN detalle_ticket dt ON dt.id_ticket = t.id_ticket
                JOIN aplicaciones a ON a.id_aplicacion = t.id_aplicacion
                WHERE dt.f_asignacion_agente IS NOT NULL
                  AND dt.f_solucion IS NOT NULL
                GROUP BY t.id_aplicacion, a.nombre
                ORDER BY promedio_horas DESC
            """)
            return [dict(r) for r in cursor.fetchall()]


def kpiTiempoRespuesta():
    """Tiempo promedio de primera respuesta (f_registro → f_asignacion_agente) por agente."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.nombre_completo AS agente,
                       COUNT(*) AS total_asignados,
                       ROUND(AVG(
                           TIMESTAMPDIFF(MINUTE, t.f_registro, dt.f_asignacion_agente)
                       ), 0) AS promedio_minutos_respuesta,
                       ROUND(MIN(
                           TIMESTAMPDIFF(MINUTE, t.f_registro, dt.f_asignacion_agente)
                       ), 0) AS minimo_minutos,
                       ROUND(MAX(
                           TIMESTAMPDIFF(MINUTE, t.f_registro, dt.f_asignacion_agente)
                       ), 0) AS maximo_minutos
                FROM tickets t
                JOIN detalle_ticket dt ON dt.id_ticket = t.id_ticket
                JOIN usuarios u ON dt.id_agente = u.id_usuario
                WHERE dt.f_asignacion_agente IS NOT NULL
                GROUP BY dt.id_agente
                ORDER BY promedio_minutos_respuesta ASC
            """)
            return [dict(r) for r in cursor.fetchall()]


def kpiPorIntensidad():
    """Distribución de tickets por intensidad."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT dt.intensidad, COUNT(*) AS total
                FROM tickets t
                JOIN detalle_ticket dt ON dt.id_ticket = t.id_ticket
                GROUP BY dt.intensidad
                ORDER BY FIELD(dt.intensidad, 'critica', 'alta', 'media', 'baja')
            """)
            return [dict(r) for r in cursor.fetchall()]


def kpiSLAPorAgente():
    """Cumplimiento de SLA por agente (desde asignación hasta solución)."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.nombre_completo AS agente,
                       COUNT(*) AS total_resueltos,
                       SUM(
                           TIMESTAMPDIFF(HOUR, dt.f_asignacion_agente, dt.f_solucion) <= dt.sla_horas
                       ) AS sla_cumplidos,
                       ROUND(
                           SUM(TIMESTAMPDIFF(HOUR, dt.f_asignacion_agente, dt.f_solucion) <= dt.sla_horas)
                           / COUNT(*) * 100, 1
                       ) AS pct_sla
                FROM tickets t
                JOIN detalle_ticket dt ON dt.id_ticket = t.id_ticket
                JOIN usuarios u ON dt.id_agente = u.id_usuario
                WHERE dt.f_asignacion_agente IS NOT NULL
                  AND dt.f_solucion IS NOT NULL
                GROUP BY dt.id_agente
                ORDER BY pct_sla DESC
            """)
            return [dict(r) for r in cursor.fetchall()]


def kpiProyectosPorSalud():
    """Proyectos activos clasificados por salud (a tiempo, en riesgo, retrasado)."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT
                    SUM(CASE WHEN ap.estado_salud = 'a_tiempo'  THEN 1 ELSE 0 END) AS a_tiempo,
                    SUM(CASE WHEN ap.estado_salud = 'en_riesgo' THEN 1 ELSE 0 END) AS en_riesgo,
                    SUM(CASE WHEN ap.estado_salud = 'retrasado' THEN 1 ELSE 0 END) AS retrasado,
                    COUNT(DISTINCT p.id_proyecto) AS total_con_avance
                FROM proyectos p
                JOIN (
                    SELECT id_proyecto, estado_salud,
                           ROW_NUMBER() OVER (PARTITION BY id_proyecto ORDER BY created_at DESC) AS rn
                    FROM avances_proyecto
                ) ap ON ap.id_proyecto = p.id_proyecto AND ap.rn = 1
                WHERE p.estado NOT IN ('eliminado', 'completado')
            """)
            return dict(cursor.fetchone())


def kpiAvancePromedioPorProyecto():
    """Último porcentaje de avance registrado por proyecto activo."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT p.nombre AS proyecto,
                       p.estado,
                       ap.porcentaje_avance,
                       ap.estado_salud,
                       ap.fecha_reporte
                FROM proyectos p
                JOIN (
                    SELECT id_proyecto, porcentaje_avance, estado_salud, fecha_reporte,
                           ROW_NUMBER() OVER (PARTITION BY id_proyecto ORDER BY created_at DESC) AS rn
                    FROM avances_proyecto
                ) ap ON ap.id_proyecto = p.id_proyecto AND ap.rn = 1
                WHERE p.estado NOT IN ('eliminado', 'completado')
                ORDER BY ap.porcentaje_avance DESC
            """)
            return [dict(r) for r in cursor.fetchall()]


def kpiCancelados():
    """Tickets cancelados y tasa de cancelación."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) AS total,
                       SUM(estado = 'cancelado') AS cancelados,
                       ROUND(SUM(estado = 'cancelado') / COUNT(*) * 100, 1) AS tasa_cancelacion
                FROM tickets
            """)
            return dict(cursor.fetchone())


def kpiRankingAppsProblemáticas():
    """Aplicaciones con más incidencias críticas o alta intensidad."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT a.nombre AS aplicacion,
                       COUNT(*) AS total_incidencias,
                       SUM(dt.prioridad IN ('critica','alta')) AS alta_prioridad,
                       SUM(dt.intensidad IN ('critica','alta')) AS alta_intensidad,
                       ROUND(SUM(dt.prioridad IN ('critica','alta')) / COUNT(*) * 100, 1) AS pct_criticas
                FROM tickets t
                JOIN aplicaciones a ON a.id_aplicacion = t.id_aplicacion
                JOIN detalle_ticket dt ON dt.id_ticket = t.id_ticket
                WHERE t.tipo = 'incidencia'
                GROUP BY t.id_aplicacion, a.nombre
                ORDER BY alta_prioridad DESC, total_incidencias DESC
                LIMIT 8
            """)
            return [dict(r) for r in cursor.fetchall()]


def kpiPorTipo():
    """Distribución de tickets por tipo con totales y porcentaje."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT tipo,
                       COUNT(*) AS total,
                       ROUND(COUNT(*) / (SELECT COUNT(*) FROM tickets) * 100, 1) AS pct
                FROM tickets
                GROUP BY tipo
                ORDER BY total DESC
            """)
            return [dict(r) for r in cursor.fetchall()]


def kpiTop5MasLentos():
    """Top 5 tickets con mayor tiempo de resolución (desde asignación)."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT t.id_ticket,
                       t.titulo,
                       a.nombre AS aplicacion,
                       dt.prioridad,
                       u.nombre_completo AS agente,
                       ROUND(TIMESTAMPDIFF(MINUTE, dt.f_asignacion_agente, dt.f_solucion) / 60.0, 1) AS horas_resolucion,
                       dt.sla_horas,
                       CASE WHEN TIMESTAMPDIFF(HOUR, dt.f_asignacion_agente, dt.f_solucion) <= dt.sla_horas
                            THEN 'SI' ELSE 'NO' END AS sla_cumplido
                FROM tickets t
                JOIN detalle_ticket dt ON dt.id_ticket = t.id_ticket
                JOIN aplicaciones a ON a.id_aplicacion = t.id_aplicacion
                LEFT JOIN usuarios u ON u.id_usuario = dt.id_agente
                WHERE dt.f_asignacion_agente IS NOT NULL AND dt.f_solucion IS NOT NULL
                ORDER BY horas_resolucion DESC
                LIMIT 5
            """)
            return [dict(r) for r in cursor.fetchall()]


def kpiActividadesPorEstado():
    """Total de actividades agrupadas por estado en todos los proyectos activos."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT a.estado,
                       COUNT(*) AS total,
                       COALESCE(SUM(a.story_points), 0) AS pts
                FROM actividades a
                JOIN proyectos p ON a.id_proyecto = p.id_proyecto
                WHERE p.estado NOT IN ('eliminado')
                  AND a.estado NOT IN ('eliminado')
                GROUP BY a.estado
                ORDER BY FIELD(a.estado,'en_progreso','por_hacer','backlog','completada','cancelada','bloqueado')
            """)
            return [dict(r) for r in cursor.fetchall()]


def kpiProgramadoresSinCarga():
    """Programadores sin actividades activas asignadas."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.nombre_completo AS programador
                FROM usuarios u
                WHERE u.rol = 'programador'
                  AND u.activo = 1
                  AND u.id_usuario NOT IN (
                      SELECT DISTINCT id_asignado FROM actividades
                      WHERE estado IN ('en_progreso','por_hacer','backlog')
                        AND estado2 = 1
                        AND id_asignado IS NOT NULL
                  )
                ORDER BY u.nombre_completo
            """)
            return [dict(r) for r in cursor.fetchall()]


def kpiProyectosVencidos():
    """Proyectos con fecha fin vencida que aún no están completados."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT p.nombre,
                       p.estado,
                       u.nombre_completo AS responsable,
                       DATEDIFF(CURDATE(), p.fecha_fin_plan) AS dias_vencido,
                       p.fecha_fin_plan
                FROM proyectos p
                JOIN usuarios u ON p.id_Stakeholder = u.id_usuario
                WHERE p.fecha_fin_plan < CURDATE()
                  AND p.estado NOT IN ('completado','eliminado')
                ORDER BY dias_vencido DESC
            """)
            return [dict(r) for r in cursor.fetchall()]