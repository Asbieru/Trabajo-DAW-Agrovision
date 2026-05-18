from conexion import obtenerconexion

class Proyecto:
    def __init__(self, nombre, id_responsable, estado,
                 fecha_inicio, fecha_fin_plan, descripcion):
        self.nombre          = nombre
        self.id_responsable  = id_responsable
        self.estado          = estado
        self.fecha_inicio    = fecha_inicio
        self.fecha_fin_plan  = fecha_fin_plan
        self.descripcion     = descripcion


def listarProyectos():
    """Retorna proyectos con nombre del responsable."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT p.id_proyecto, p.nombre, p.estado,
                       p.fecha_inicio, p.fecha_fin_plan,
                       u.nombre_completo AS nombre_responsable
                FROM proyectos p
                JOIN usuarios u ON p.id_responsable = u.id_usuario
                ORDER BY p.created_at DESC
            """)
            return cursor.fetchall()


def insertarProyecto(obj):
    """Inserta un proyecto de software."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO proyectos
                    (nombre, id_responsable, estado,
                     fecha_inicio, fecha_fin_plan, descripcion)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                obj.nombre, obj.id_responsable, obj.estado,
                obj.fecha_inicio, obj.fecha_fin_plan, obj.descripcion
            ))
        conn.commit()


def obtenerProyecto(id_proyecto):
    """Retorna el detalle completo de un proyecto por su ID."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT p.id_proyecto, p.nombre, p.estado,
                       p.fecha_inicio, p.fecha_fin_plan, p.descripcion,
                       p.id_responsable,
                       u.nombre_completo AS nombre_responsable
                FROM proyectos p
                JOIN usuarios u ON p.id_responsable = u.id_usuario
                WHERE p.id_proyecto = %s
            """, (id_proyecto,))
            return cursor.fetchone()


def actualizarProyecto(id_proyecto, nombre, id_responsable, estado, descripcion):
    """Actualiza nombre, responsable, estado y descripción de un proyecto."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE proyectos
                SET nombre         = %s,
                    id_responsable = %s,
                    estado         = %s,
                    descripcion    = %s
                WHERE id_proyecto = %s
            """, (nombre, id_responsable, estado, descripcion, id_proyecto))
        conn.commit()
    return True


def resumenHistoriasPorProyecto():
    """Devuelve para cada proyecto: total de historias y cuántas están completadas."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT p.id_proyecto,
                       p.nombre AS nombre_proyecto,
                       COUNT(h.id_historia)         AS total,
                       SUM(h.estado = 'completada') AS completadas
                FROM proyectos p
                LEFT JOIN historias h ON p.id_proyecto = h.id_proyecto
                GROUP BY p.id_proyecto, p.nombre
                ORDER BY p.created_at DESC
            """)
            return cursor.fetchall()


def listarAvances(id_proyecto):
    """Retorna el historial de avances de un proyecto específico."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT a.id_avance, a.fecha_reporte, a.porcentaje_avance,
                       a.estado_salud, a.logros_periodo, a.pendientes_next
                FROM avances_proyecto a
                WHERE a.id_proyecto = %s
                ORDER BY a.fecha_reporte DESC, a.created_at DESC
            """, (id_proyecto,))
            return cursor.fetchall()


def insertarAvance(id_proyecto, id_autor, fecha_reporte, porcentaje_avance,
                   estado_salud, logros_periodo, pendientes_next):
    """Guarda un nuevo reporte de avance en la bitácora."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO avances_proyecto
                    (id_proyecto, id_autor, fecha_reporte, porcentaje_avance,
                     estado_salud, logros_periodo, pendientes_next)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (id_proyecto, id_autor, fecha_reporte, porcentaje_avance,
                  estado_salud, logros_periodo, pendientes_next))
        conn.commit()


def eliminarAvance(id_avance):
    """Elimina un reporte de avance específico por su ID."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM avances_proyecto WHERE id_avance = %s", (id_avance,))
        conn.commit()