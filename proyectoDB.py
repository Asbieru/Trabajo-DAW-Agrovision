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