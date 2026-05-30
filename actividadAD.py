from conexion import obtenerconexion


class Actividad:
    def __init__(self, id_proyecto, id_sprint, id_asignado,
                 titulo, prioridad, estado, story_points):
        self.id_proyecto  = id_proyecto
        self.id_sprint    = id_sprint if id_sprint else None
        self.id_asignado  = id_asignado if id_asignado else None
        self.titulo       = titulo
        self.prioridad    = prioridad
        self.estado       = estado
        self.story_points = story_points if story_points else 0


def _generarCodigo():
    """Genera automáticamente el siguiente código ACT-XXX."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT codigo FROM actividades
                WHERE codigo LIKE 'ACT-%'
                ORDER BY id_actividad DESC
                LIMIT 1
            """)
            fila = cursor.fetchone()
    if fila:
        try:
            num = int(fila['codigo'].split('-')[1]) + 1
        except (IndexError, ValueError):
            num = 1
    else:
        num = 1
    return f'ACT-{num:03d}'


def listarActividades(id_proyecto=None):
    """Lista actividades no eliminadas con nombre de proyecto, sprint y asignado."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            sql = """
                SELECT a.id_actividad, a.codigo, a.titulo,
                       a.prioridad, a.estado, a.story_points,
                       p.nombre  AS nombre_proyecto,
                       s.nombre  AS nombre_sprint,
                       u.nombre_completo AS nombre_asignado
                FROM actividades a
                JOIN proyectos p ON a.id_proyecto = p.id_proyecto
                LEFT JOIN sprints  s ON a.id_sprint   = s.id_sprint
                LEFT JOIN usuarios u ON a.id_asignado = u.id_usuario
                WHERE a.estado != 'eliminado'
            """
            if id_proyecto:
                sql += " AND a.id_proyecto = %s ORDER BY a.created_at DESC"
                cursor.execute(sql, (id_proyecto,))
            else:
                sql += " ORDER BY a.created_at DESC"
                cursor.execute(sql)
            return cursor.fetchall()


def insertarActividad(obj):
    """Inserta una nueva actividad con código auto-generado."""
    codigo = _generarCodigo()
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO actividades
                    (id_proyecto, id_sprint, id_asignado,
                     codigo, titulo, prioridad, estado, story_points)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                obj.id_proyecto, obj.id_sprint, obj.id_asignado,
                codigo, obj.titulo,
                obj.prioridad, obj.estado, obj.story_points
            ))
        conn.commit()


def actualizarEstadoActividad(id_actividad, nuevo_estado):
    """Cambia el estado de una actividad."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE actividades SET estado = %s WHERE id_actividad = %s",
                (nuevo_estado, id_actividad)
            )
        conn.commit()


def eliminarActividad(id_actividad):
    """Elimina lógicamente una actividad (estado = 'eliminado'). Solo si está en estado 'cancelada'."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            # Verificar que esté cancelada antes de eliminar
            cursor.execute(
                "SELECT estado FROM actividades WHERE id_actividad = %s",
                (id_actividad,)
            )
            row = cursor.fetchone()
            if not row or row['estado'] != 'cancelada':
                return False
            cursor.execute(
                "UPDATE actividades SET estado = 'eliminado' WHERE id_actividad = %s",
                (id_actividad,)
            )
        conn.commit()
    return True


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


def listarAsignadosPorProyecto(id_proyecto):
    """Devuelve los usuarios asignados como responsables de un proyecto."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.id_usuario, u.nombre_completo
                FROM asignado a
                JOIN usuarios u ON a.id_usuario = u.id_usuario
                WHERE a.id_proyecto = %s
                ORDER BY u.nombre_completo
            """, (id_proyecto,))
            return cursor.fetchall()


def resumenActividadesPorProyecto():
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql = """
                        SELECT p.id_proyecto,
                               p.nombre AS nombre_proyecto,
                               COUNT(a.id_actividad) AS total,
                               SUM(CASE
                                   WHEN a.estado = 'completada' THEN 100
                                   WHEN a.estado = 'en_progreso' THEN 50
                                   WHEN a.estado = 'por_hacer' THEN 10
                                   ELSE 0
                               END) / NULLIF(COUNT(a.id_actividad), 0) AS porcentaje_avance_real
                        FROM proyectos p
                        LEFT JOIN actividades a ON p.id_proyecto = a.id_proyecto
                            AND a.estado != 'cancelada'
                            AND a.estado != 'eliminado'
                        GROUP BY p.id_proyecto, p.nombre
                    """
                    cursor.execute(sql)
                    return cursor.fetchall()
    except Exception as e:
        print(f"[ERROR resumenActividadesPorProyecto] {e}")
    return []

def obtenerActividad(id_actividad):
    """Retorna el detalle de una actividad por su ID."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT a.id_actividad, a.codigo, a.titulo,
                       a.prioridad, a.estado, a.story_points,
                       a.id_proyecto, a.id_sprint, a.id_asignado,
                       p.nombre AS nombre_proyecto,
                       s.nombre AS nombre_sprint,
                       u.nombre_completo AS nombre_asignado
                FROM actividades a
                JOIN proyectos p ON a.id_proyecto = p.id_proyecto
                LEFT JOIN sprints  s ON a.id_sprint   = s.id_sprint
                LEFT JOIN usuarios u ON a.id_asignado = u.id_usuario
                WHERE a.id_actividad = %s AND a.estado != 'eliminado'
            """, (id_actividad,))
            return cursor.fetchone()


def actualizarActividad(id_actividad, id_proyecto, id_sprint, id_asignado,
                        titulo, prioridad, estado, story_points):
    """Actualiza los datos editables de una actividad."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE actividades
                SET id_proyecto  = %s,
                    id_sprint    = %s,
                    id_asignado  = %s,
                    titulo       = %s,
                    prioridad    = %s,
                    estado       = %s,
                    story_points = %s
                WHERE id_actividad = %s
            """, (id_proyecto, id_sprint, id_asignado,
                  titulo, prioridad, estado, story_points,
                  id_actividad))
        conn.commit()
    return True


def proximoCodigo():
    """Devuelve el próximo código que se generaría (para mostrar en formulario)."""
    return _generarCodigo()