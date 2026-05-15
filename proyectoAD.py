from conexion import (obtenerconexion)

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
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql = """
                        SELECT p.id_proyecto, p.nombre, p.estado,
                               p.fecha_inicio, p.fecha_fin_plan,
                               u.nombre_completo AS nombre_responsable
                        FROM proyectos p
                        JOIN usuarios u ON p.id_responsable = u.id_usuario
                        ORDER BY p.created_at DESC
                    """
                    cursor.execute(sql)
                    return cursor.fetchall()
    except Exception as e:
        print(f"[ERROR listarProyectos] {e}")
    return []


def insertarProyecto(obj):
    """Inserta un proyecto de software. Retorna True si tuvo éxito."""
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql = """
                        INSERT INTO proyectos
                            (nombre, id_responsable, estado,
                             fecha_inicio, fecha_fin_plan, descripcion)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (
                        obj.nombre, obj.id_responsable, obj.estado,
                        obj.fecha_inicio, obj.fecha_fin_plan, obj.descripcion
                    ))
                conn.commit()
            return True
    except Exception as e:
        print(f"[ERROR insertarProyecto] {e}")
    return False


def obtenerProyecto(id_proyecto):
    """Retorna el detalle completo de un proyecto por su ID."""
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql = """
                        SELECT p.id_proyecto, p.nombre, p.estado,
                               p.fecha_inicio, p.fecha_fin_plan, p.descripcion,
                               p.id_responsable,
                               u.nombre_completo AS nombre_responsable
                        FROM proyectos p
                        JOIN usuarios u ON p.id_responsable = u.id_usuario
                        WHERE p.id_proyecto = %s
                    """
                    cursor.execute(sql, (id_proyecto,))
                    return cursor.fetchone()
    except Exception as e:
        print(f"[ERROR obtenerProyecto] {e}")
    return None


def actualizarProyecto(id_proyecto, nombre, id_responsable, estado, descripcion):
    """Actualiza nombre, responsable, estado y descripción de un proyecto."""
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql = """
                        UPDATE proyectos
                        SET nombre         = %s,
                            id_responsable = %s,
                            estado         = %s,
                            descripcion    = %s
                        WHERE id_proyecto = %s
                    """
                    cursor.execute(sql, (
                        nombre, id_responsable, estado,
                        descripcion, id_proyecto
                    ))
                conn.commit()
            return True
    except Exception as e:
        print(f"[ERROR actualizarProyecto] {e}")
    return False


def resumenHistoriasPorProyecto():
    """
    Devuelve para cada proyecto: total de historias y cuántas
    están completadas. Se usa en gestión de proyecto para la
    barra de progreso y el gráfico de barras comparativo.
    """
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql = """
                        SELECT p.id_proyecto,
                               p.nombre AS nombre_proyecto,
                               COUNT(h.id_historia)         AS total,
                               SUM(h.estado = 'completada') AS completadas
                        FROM proyectos p
                        LEFT JOIN historias h ON p.id_proyecto = h.id_proyecto
                        GROUP BY p.id_proyecto, p.nombre
                        ORDER BY p.created_at DESC
                    """
                    cursor.execute(sql)
                    return cursor.fetchall()
    except Exception as e:
        print(f"[ERROR resumenHistoriasPorProyecto] {e}")
    return []

def listarAvances(id_proyecto):
    """Retorna el historial de avances de un proyecto específico."""
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql = """
                        SELECT a.id_avance, a.fecha_reporte, a.porcentaje_avance, 
                               a.estado_salud, a.logros_periodo, a.pendientes_next,
                               u.nombre_completo AS autor
                        FROM avances_proyecto a
                        JOIN usuarios u ON a.id_autor = u.id_usuario
                        WHERE a.id_proyecto = %s
                        ORDER BY a.fecha_reporte DESC, a.created_at DESC
                    """
                    cursor.execute(sql, (id_proyecto,))
                    return cursor.fetchall()
    except Exception as e:
        print(f"[ERROR listarAvances] {e}")
    return []


def insertarAvance(id_proyecto, id_autor, fecha_reporte, porcentaje_avance, estado_salud, logros_periodo, pendientes_next):
    """Guarda un nuevo reporte de avance en la bitácora."""
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql = """
                        INSERT INTO avances_proyecto 
                            (id_proyecto, id_autor, fecha_reporte, porcentaje_avance, estado_salud, logros_periodo, pendientes_next)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (id_proyecto, id_autor, fecha_reporte, porcentaje_avance, estado_salud, logros_periodo, pendientes_next))
                conn.commit()
            return True
    except Exception as e:
        print(f"[ERROR insertarAvance] {e}")
    return False

def eliminarAvance(id_avance):
    """Elimina un reporte de avance específico por su ID."""
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql = "DELETE FROM avances_proyecto WHERE id_avance = %s"
                    cursor.execute(sql, (id_avance,))
                conn.commit()
            return True
    except Exception as e:
        print(f"[ERROR eliminarAvance] {e}")
    return False