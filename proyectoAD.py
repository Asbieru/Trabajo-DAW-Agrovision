from conexion import obtenerconexion

class Proyecto:
    def __init__(self, nombre, ids_responsables, estado,
                 fecha_inicio, fecha_fin_plan, descripcion):
        self.nombre           = nombre
        # ids_responsables puede ser lista (nuevo) o un solo valor (edicion existente)
        if isinstance(ids_responsables, list):
            self.ids_responsables = ids_responsables
            self.id_responsable   = ids_responsables[0] if ids_responsables else None
        else:
            self.ids_responsables = [ids_responsables]
            self.id_responsable   = ids_responsables
        self.estado          = estado
        self.fecha_inicio    = fecha_inicio
        self.fecha_fin_plan  = fecha_fin_plan
        self.descripcion     = descripcion


def listarProyectos():
    """Retorna proyectos con todos sus responsables agrupados."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            # Traer proyectos base
            cursor.execute("""
                SELECT p.id_proyecto, p.nombre, p.estado,
                       p.fecha_inicio, p.fecha_fin_plan, p.id_responsable
                FROM proyectos p
                ORDER BY p.created_at DESC
            """)
            proyectos = cursor.fetchall()

            if not proyectos:
                return []

            # Traer todos los responsables de la tabla asignado
            cursor.execute("""
                SELECT a.id_proyecto, u.nombre_completo
                FROM asignado a
                JOIN usuarios u ON a.id_usuario = u.id_usuario
                ORDER BY a.id_proyecto, u.nombre_completo
            """)
            filas_resp = cursor.fetchall()

    # Agrupar responsables por id_proyecto
    resp_por_proyecto = {}
    for fila in filas_resp:
        pid = fila['id_proyecto']
        if pid not in resp_por_proyecto:
            resp_por_proyecto[pid] = []
        resp_por_proyecto[pid].append(fila['nombre_completo'])

    # Inyectar la lista de nombres en cada proyecto como 'responsables'
    result = []
    for p in proyectos:
        pid = p['id_proyecto']
        nombres = resp_por_proyecto.get(pid, [])
        # Convertir a dict mutable para agregar el campo
        fila = dict(p)
        fila['responsables'] = nombres
        # Compatibilidad: nombre_responsable con todos los nombres juntos
        fila['nombre_responsable'] = ', '.join(nombres) if nombres else '—'
        result.append(fila)

    return result


def insertarProyecto(obj):
    """Inserta un proyecto de software y sus asignados en la tabla intermedia."""
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
            nuevo_id = cursor.lastrowid

            # Insertar todos los responsables en la tabla asignado
            for id_resp in obj.ids_responsables:
                cursor.execute("""
                    INSERT IGNORE INTO asignado (id_proyecto, id_usuario)
                    VALUES (%s, %s)
                """, (nuevo_id, int(id_resp)))
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
    """Actualiza nombre, responsable, estado y descripcion de un proyecto."""
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


def listarAvances(id_proyecto):
    """Retorna el historial de avances de un proyecto especifico."""
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
    """Guarda un nuevo reporte de avance en la bitacora."""
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
    """Elimina un reporte de avance especifico por su ID."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM avances_proyecto WHERE id_avance = %s", (id_avance,))
        conn.commit()