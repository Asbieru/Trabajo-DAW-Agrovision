"""
ad.py  –  Utils para la conexión y funciones extras del proyecto.
"""

import pymysql.cursors


# ──────────────────────────────────────────────────────────────
#  CONEXIÓN
# ──────────────────────────────────────────────────────────────

def obtenerconexion():
    """Devuelve una conexión a bd_proyectofinal o None si falla."""
    try:
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='',          # Ajusta si tu MySQL tiene contraseña
            database='bd_proyectofinal',
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        print(f"[ERROR conexión] {e}")
        return None


# ──────────────────────────────────────────────────────────────
#  CLASES DTO
# ──────────────────────────────────────────────────────────────

class EvaluacionCampo:
    def __init__(self, id_lote, id_plaga, id_inspector,
                 fecha_evaluacion, hora_evaluacion,
                 plantas_evaluadas, plantas_afectadas,
                 nivel_incidencia, foto_url, observaciones):
        self.id_lote           = id_lote
        self.id_plaga          = id_plaga
        self.id_inspector      = id_inspector
        self.fecha_evaluacion  = fecha_evaluacion
        self.hora_evaluacion   = hora_evaluacion
        self.plantas_evaluadas = plantas_evaluadas
        self.plantas_afectadas = plantas_afectadas
        self.nivel_incidencia  = nivel_incidencia
        self.foto_url          = foto_url
        self.observaciones     = observaciones


# ──────────────────────────────────────────────────────────────
#  FUNCIONES DE CONSULTA (para poblar selects)
# ──────────────────────────────────────────────────────────────

def obtenerLotes():
    """Retorna lista de dicts con id_lote, codigo_lote, nombre_fundo."""
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT id_lote, codigo_lote, nombre_fundo "
                        "FROM lotes WHERE activo=1 ORDER BY codigo_lote"
                    )
                    return cursor.fetchall()
    except Exception as e:
        print(f"[ERROR obtenerLotes] {e}")
    return []


def obtenerPlagas():
    """Retorna lista de dicts con id_plaga, nombre, nivel_riesgo."""
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT id_plaga, nombre, nivel_riesgo "
                        "FROM plagas ORDER BY nombre"
                    )
                    return cursor.fetchall()
    except Exception as e:
        print(f"[ERROR obtenerPlagas] {e}")
    return []


def obtenerUsuarios(rol=None):
    """Retorna usuarios activos. Si se pasa rol, filtra por él."""
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    if rol:
                        cursor.execute(
                            "SELECT id_usuario, nombre_completo, rol "
                            "FROM usuarios WHERE activo=1 AND rol=%s ORDER BY nombre_completo",
                            (rol,)
                        )
                    else:
                        cursor.execute(
                            "SELECT id_usuario, nombre_completo, rol "
                            "FROM usuarios WHERE activo=1 ORDER BY nombre_completo"
                        )
                    return cursor.fetchall()
    except Exception as e:
        print(f"[ERROR obtenerUsuarios] {e}")
    return []


# ──────────────────────────────────────────────────────────────
#  FUNCIONES DE LISTADO
# ──────────────────────────────────────────────────────────────

def listarEvaluaciones():
    """Retorna evaluaciones con datos de lote, plaga e inspector."""
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql = """
                        SELECT e.id_evaluacion, e.fecha_evaluacion, e.nivel_incidencia,
                               e.plantas_evaluadas, e.plantas_afectadas,
                               l.codigo_lote, l.nombre_fundo,
                               p.nombre AS nombre_plaga,
                               u.nombre_completo AS nombre_inspector,
                               e.observaciones
                        FROM evaluaciones_campo e
                        JOIN lotes    l ON e.id_lote      = l.id_lote
                        JOIN plagas   p ON e.id_plaga     = p.id_plaga
                        JOIN usuarios u ON e.id_inspector = u.id_usuario
                        ORDER BY e.fecha_evaluacion DESC, e.id_evaluacion DESC
                    """
                    cursor.execute(sql)
                    return cursor.fetchall()
    except Exception as e:
        print(f"[ERROR listarEvaluaciones] {e}")
    return []

# ──────────────────────────────────────────────────────────────
#  FUNCIONES DE INSERCIÓN
# ──────────────────────────────────────────────────────────────

def insertarEvaluacion(obj: EvaluacionCampo) -> bool:
    """Inserta una evaluación de campo. Retorna True si tuvo éxito."""
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql = """
                        INSERT INTO evaluaciones_campo
                            (id_lote, id_plaga, id_inspector, fecha_evaluacion,
                             hora_evaluacion, plantas_evaluadas, plantas_afectadas,
                             nivel_incidencia, foto_url, observaciones)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (
                        obj.id_lote, obj.id_plaga, obj.id_inspector,
                        obj.fecha_evaluacion, obj.hora_evaluacion or None,
                        obj.plantas_evaluadas, obj.plantas_afectadas,
                        obj.nivel_incidencia,
                        obj.foto_url or None,
                        obj.observaciones or None
                    ))
                conn.commit()
            return True
    except Exception as e:
        print(f"[ERROR insertarEvaluacion] {e}")
    return False

# ══════════════════════════════════════════════════════════════
#  KPIs INDICADORES DE SOPORTE
# ══════════════════════════════════════════════════════════════

def kpiTicketsPorAgente():
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT u.nombre_completo AS agente,
                               COUNT(*) AS total_atendidos,
                               SUM(t.estado IN ('resuelto','cerrado')) AS resueltos,
                               ROUND(AVG(
                                   CASE WHEN t.fecha_resolucion IS NOT NULL
                                   THEN TIMESTAMPDIFF(HOUR, t.fecha_apertura, t.fecha_resolucion)
                                   END
                               ), 1) AS promedio_horas
                        FROM tickets t
                        JOIN usuarios u ON t.id_agente = u.id_usuario
                        WHERE t.id_agente IS NOT NULL
                        GROUP BY t.id_agente
                        ORDER BY total_atendidos DESC
                    """)
                    return cursor.fetchall()
    except Exception as e:
        print(f"[ERROR kpiTicketsPorAgente] {e}")
    return []


def kpiTicketsPorMes():
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT DATE_FORMAT(fecha_apertura, '%%Y-%%m') AS mes,
                               DATE_FORMAT(fecha_apertura, '%%b %%Y') AS mes_label,
                               COUNT(*) AS total,
                               SUM(estado IN ('resuelto','cerrado')) AS resueltos
                        FROM tickets
                        WHERE fecha_apertura >= DATE_SUB(NOW(), INTERVAL 6 MONTH)
                        GROUP BY mes, mes_label
                        ORDER BY mes ASC
                    """)
                    return cursor.fetchall()
    except Exception as e:
        print(f"[ERROR kpiTicketsPorMes] {e}")
    return []

def kpiAvanceSprintActual():
    """Story points del sprint activo de cada proyecto."""
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT s.nombre AS sprint,
                               p.nombre AS proyecto,
                               s.capacidad_pts,
                               COALESCE(SUM(h.story_points), 0) AS pts_asignados,
                               COALESCE(SUM(CASE WHEN h.estado = 'completada' THEN h.story_points ELSE 0 END), 0) AS pts_completados,
                               COALESCE(SUM(CASE WHEN h.estado = 'en_progreso' THEN h.story_points ELSE 0 END), 0) AS pts_en_progreso,
                               s.fecha_inicio,
                               s.fecha_fin,
                               DATEDIFF(s.fecha_fin, CURDATE()) AS dias_restantes
                        FROM sprints s
                        JOIN proyectos p ON s.id_proyecto = p.id_proyecto
                        LEFT JOIN historias h ON h.id_sprint = s.id_sprint
                        WHERE s.estado = 'activo'
                        GROUP BY s.id_sprint
                    """)
                    return cursor.fetchall()
    except Exception as e:
        print(f"[ERROR kpiAvanceSprintActual] {e}")
    return []