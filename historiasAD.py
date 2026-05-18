from conexion import obtenerconexion


class Historia:
    def __init__(self, id_proyecto, id_sprint, id_asignado,
                 codigo, titulo, tipo, prioridad, estado, story_points):
        self.id_proyecto  = id_proyecto
        self.id_sprint    = id_sprint if id_sprint else None
        self.id_asignado  = id_asignado if id_asignado else None
        self.codigo       = codigo
        self.titulo       = titulo
        self.tipo         = tipo
        self.prioridad    = prioridad
        self.estado       = estado
        self.story_points = story_points if story_points else 0


def listarHistorias(id_proyecto=None):
    """Lista historias con nombre de proyecto, sprint y asignado."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            sql = """
                SELECT h.id_historia, h.codigo, h.titulo,
                       h.tipo, h.prioridad, h.estado, h.story_points,
                       p.nombre  AS nombre_proyecto,
                       s.nombre  AS nombre_sprint,
                       u.nombre_completo AS nombre_asignado
                FROM historias h
                JOIN proyectos p ON h.id_proyecto = p.id_proyecto
                LEFT JOIN sprints  s ON h.id_sprint   = s.id_sprint
                LEFT JOIN usuarios u ON h.id_asignado = u.id_usuario
            """
            if id_proyecto:
                sql += " WHERE h.id_proyecto = %s ORDER BY h.created_at DESC"
                cursor.execute(sql, (id_proyecto,))
            else:
                sql += " ORDER BY h.created_at DESC"
                cursor.execute(sql)
            return cursor.fetchall()


def insertarHistoria(obj):
    """Inserta una nueva historia."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO historias
                    (id_proyecto, id_sprint, id_asignado,
                     codigo, titulo, tipo, prioridad, estado, story_points)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                obj.id_proyecto, obj.id_sprint, obj.id_asignado,
                obj.codigo, obj.titulo, obj.tipo,
                obj.prioridad, obj.estado, obj.story_points
            ))
        conn.commit()


def actualizarEstadoHistoria(id_historia, nuevo_estado):
    """Cambia el estado de una historia."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE historias SET estado = %s WHERE id_historia = %s",
                (nuevo_estado, id_historia)
            )
        conn.commit()


def listarTodosSprints():
    """Devuelve todos los sprints con su proyecto."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT s.id_sprint, s.nombre, s.estado,
                       p.nombre AS nombre_proyecto, s.id_proyecto
                FROM sprints s
                JOIN proyectos p ON s.id_proyecto = p.id_proyecto
                ORDER BY s.id_proyecto, s.fecha_inicio
            """)
            return cursor.fetchall()


def resumenHistoriasPorProyecto():
    """KPI: total de historias agrupadas por proyecto y estado."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT p.nombre AS proyecto,
                       COUNT(h.id_historia)                          AS total,
                       SUM(h.estado = 'completada')                  AS completadas,
                       SUM(h.estado = 'en_progreso')                 AS en_progreso,
                       SUM(h.estado IN ('backlog','por_hacer'))      AS pendientes,
                       COALESCE(SUM(h.story_points),0)               AS puntos_totales
                FROM proyectos p
                LEFT JOIN historias h ON p.id_proyecto = h.id_proyecto
                GROUP BY p.id_proyecto, p.nombre
                ORDER BY p.created_at DESC
            """)
            return cursor.fetchall()