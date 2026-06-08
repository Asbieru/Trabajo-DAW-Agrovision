from conexion import obtenerconexion

class Proyecto:
    def __init__(self, nombre, ids_responsables, estado,
                 fecha_inicio, fecha_fin_plan, descripcion,
                 problematica=None, justificacion=None, beneficios=None):
        self.nombre           = nombre
        if isinstance(ids_responsables, list):
            self.ids_responsables = ids_responsables
            self.id_Stakeholder   = ids_responsables[0] if ids_responsables else None
        else:
            self.ids_responsables = [ids_responsables]
            self.id_Stakeholder   = ids_responsables
        self.estado          = estado
        self.fecha_inicio    = fecha_inicio
        self.fecha_fin_plan  = fecha_fin_plan
        self.descripcion     = descripcion
        self.problematica    = problematica
        self.justificacion   = justificacion
        self.beneficios      = beneficios


def _calcularEstado(estado_bd, total_acts, completadas, en_progreso, bloqueadas):
    """
    Calcula el estado real de un proyecto basandose en sus actividades.
    Si no hay actividades, respeta el estado guardado en la BD.
    """
    # Estados que no se sobreescriben con logica de actividades
    if estado_bd in ('en_revision', 'rechazado', 'eliminado', 'pausado'):
        return estado_bd
    if total_acts == 0:
        return estado_bd
    if completadas == total_acts:
        return 'completado'
    if bloqueadas > 0:
        return 'en_desarrollo'
    if en_progreso > 0 or completadas > 0:
        return 'en_desarrollo'
    return estado_bd


def listarProyectos():
    """Retorna proyectos aprobados (no en revision, rechazados ni eliminados) con estado calculado y Stakeholders agrupados."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT p.id_proyecto, p.nombre, p.estado AS estado_bd,
                       p.fecha_inicio, p.fecha_fin_plan, p.id_Stakeholder,
                       COUNT(a.id_actividad)                                          AS total_acts,
                       SUM(a.estado = 'completada')                                   AS completadas,
                       SUM(a.estado = 'en_progreso')                                  AS en_progreso,
                       SUM(a.estado = 'bloqueado')                                    AS bloqueadas
                FROM proyectos p
                LEFT JOIN actividades a
                       ON p.id_proyecto = a.id_proyecto
                      AND a.estado NOT IN ('cancelada', 'eliminado')
                WHERE p.estado NOT IN ('eliminado', 'en_revision', 'rechazado')
                GROUP BY p.id_proyecto, p.nombre, p.estado,
                         p.fecha_inicio, p.fecha_fin_plan, p.id_Stakeholder
                ORDER BY p.created_at DESC
            """)
            proyectos = cursor.fetchall()

            if not proyectos:
                return []

            cursor.execute("""
                SELECT a.id_proyecto, u.nombre_completo
                FROM asignado a
                JOIN usuarios u ON a.id_usuario = u.id_usuario
                ORDER BY a.id_proyecto, u.nombre_completo
            """)
            filas_resp = cursor.fetchall()

    resp_por_proyecto = {}
    for fila in filas_resp:
        pid = fila['id_proyecto']
        if pid not in resp_por_proyecto:
            resp_por_proyecto[pid] = []
        resp_por_proyecto[pid].append(fila['nombre_completo'])

    result = []
    for p in proyectos:
        pid   = p['id_proyecto']
        fila  = dict(p)

        fila['estado'] = _calcularEstado(
            estado_bd   = p['estado_bd'],
            total_acts  = int(p['total_acts']   or 0),
            completadas = int(p['completadas']  or 0),
            en_progreso = int(p['en_progreso']  or 0),
            bloqueadas  = int(p['bloqueadas']   or 0),
        )

        nombres = resp_por_proyecto.get(pid, [])
        fila['stakeholders']       = nombres
        fila['nombre_responsable'] = ', '.join(nombres) if nombres else '—'
        result.append(fila)

    return result


def listarProyectosEnRevision():
    """Retorna todos los proyectos en estado en_revision para aprobacion del gerente."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT p.id_proyecto, p.nombre, p.estado,
                       p.fecha_inicio, p.fecha_fin_plan,
                       p.problematica, p.justificacion, p.beneficios,
                       p.descripcion, p.created_at,
                       u.nombre_completo AS nombre_stakeholder
                FROM proyectos p
                JOIN usuarios u ON p.id_Stakeholder = u.id_usuario
                WHERE p.estado = 'en_revision'
                ORDER BY p.created_at DESC
            """)
            return cursor.fetchall()


def aprobarProyecto(id_proyecto):
    """Cambia el estado de en_revision a planificado."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE proyectos SET estado = 'planificado'
                WHERE id_proyecto = %s AND estado = 'en_revision'
            """, (id_proyecto,))
        conn.commit()
    return True


def rechazarProyecto(id_proyecto):
    """Cambia el estado de en_revision a rechazado."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE proyectos SET estado = 'rechazado'
                WHERE id_proyecto = %s AND estado = 'en_revision'
            """, (id_proyecto,))
        conn.commit()
    return True


def insertarProyecto(obj):
    """Inserta un proyecto de software y sus Stakeholders en la tabla intermedia."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO proyectos
                    (nombre, id_Stakeholder, estado,
                     fecha_inicio, fecha_fin_plan,
                     problematica, justificacion, beneficios, descripcion)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                obj.nombre, obj.id_Stakeholder, obj.estado,
                obj.fecha_inicio, obj.fecha_fin_plan,
                obj.problematica, obj.justificacion, obj.beneficios,
                obj.descripcion
            ))
            nuevo_id = cursor.lastrowid

            for id_resp in obj.ids_responsables:
                cursor.execute("""
                    INSERT IGNORE INTO asignado (id_proyecto, id_usuario)
                    VALUES (%s, %s)
                """, (nuevo_id, int(id_resp)))
        conn.commit()


def obtenerProyecto(id_proyecto):
    """Retorna el detalle completo de un proyecto con estado calculado."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT p.id_proyecto, p.nombre, p.estado AS estado_bd,
                       p.fecha_inicio, p.fecha_fin_plan, p.descripcion,
                       p.problematica, p.justificacion, p.beneficios,
                       p.id_Stakeholder,
                       u.nombre_completo AS nombre_responsable,
                       COUNT(a.id_actividad)          AS total_acts,
                       SUM(a.estado = 'completada')   AS completadas,
                       SUM(a.estado = 'en_progreso')  AS en_progreso,
                       SUM(a.estado = 'bloqueado')    AS bloqueadas
                FROM proyectos p
                JOIN usuarios u ON p.id_Stakeholder = u.id_usuario
                LEFT JOIN actividades a
                       ON p.id_proyecto = a.id_proyecto
                      AND a.estado NOT IN ('cancelada', 'eliminado')
                WHERE p.id_proyecto = %s
                GROUP BY p.id_proyecto, p.nombre, p.estado,
                         p.fecha_inicio, p.fecha_fin_plan, p.descripcion,
                         p.problematica, p.justificacion, p.beneficios,
                         p.id_Stakeholder, u.nombre_completo
            """, (id_proyecto,))
            row = cursor.fetchone()

    if not row:
        return None

    fila = dict(row)
    fila['estado'] = _calcularEstado(
        estado_bd   = row['estado_bd'],
        total_acts  = int(row['total_acts']  or 0),
        completadas = int(row['completadas'] or 0),
        en_progreso = int(row['en_progreso'] or 0),
        bloqueadas  = int(row['bloqueadas']  or 0),
    )
    return fila


def actualizarProyecto(id_proyecto, nombre, id_Stakeholder, estado, descripcion):
    """Actualiza nombre, Stakeholder, estado y descripcion de un proyecto."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE proyectos
                SET nombre         = %s,
                    id_Stakeholder = %s,
                    estado         = %s,
                    descripcion    = %s
                WHERE id_proyecto = %s
            """, (nombre, id_Stakeholder, estado, descripcion, id_proyecto))
        conn.commit()
    return True


def obtenerResponsablesProyecto(id_proyecto):
    """Retorna lista de ids de usuarios asignados al proyecto."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id_usuario FROM asignado
                WHERE id_proyecto = %s
            """, (id_proyecto,))
            filas = cursor.fetchall()
    return [str(f['id_usuario']) for f in filas]


def actualizarProyectoCompleto(id_proyecto, nombre, ids_responsables, estado,
                                fecha_fin_plan, descripcion):
    """Actualiza todos los datos editables de un proyecto, incluyendo Stakeholders."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE proyectos
                SET nombre         = %s,
                    id_Stakeholder = %s,
                    estado         = %s,
                    fecha_fin_plan = %s,
                    descripcion    = %s
                WHERE id_proyecto = %s
            """, (nombre, int(ids_responsables[0]), estado,
                  fecha_fin_plan, descripcion, id_proyecto))

            cursor.execute("DELETE FROM asignado WHERE id_proyecto = %s", (id_proyecto,))
            for id_resp in ids_responsables:
                cursor.execute("""
                    INSERT IGNORE INTO asignado (id_proyecto, id_usuario)
                    VALUES (%s, %s)
                """, (id_proyecto, int(id_resp)))
        conn.commit()
    return True


def tieneActividadesPendientes(id_proyecto):
    """Retorna True si el proyecto tiene actividades no eliminadas."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) AS total
                FROM actividades
                WHERE id_proyecto = %s AND estado != 'eliminado'
            """, (id_proyecto,))
            row = cursor.fetchone()
    return int(row['total'] or 0) > 0


def eliminarProyecto(id_proyecto):
    """Elimina logicamente un proyecto (estado = 'eliminado'). Solo si no tiene actividades activas."""
    if tieneActividadesPendientes(id_proyecto):
        return False
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE proyectos SET estado = 'eliminado' WHERE id_proyecto = %s
            """, (id_proyecto,))
        conn.commit()
    return True


def listarAvances(id_proyecto):
    """Retorna el historial de avances de un proyecto con nombre del autor."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT ap.id_avance,
                       ap.fecha_reporte,
                       ap.porcentaje_avance,
                       ap.estado_salud,
                       ap.logros_periodo,
                       ap.pendientes_next,
                       u.nombre_completo AS autor
                FROM avances_proyecto ap
                JOIN usuarios u ON ap.id_autor = u.id_usuario
                WHERE ap.id_proyecto = %s
                ORDER BY ap.fecha_reporte DESC, ap.created_at DESC
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
            cursor.execute(
                "DELETE FROM avances_proyecto WHERE id_avance = %s",
                (id_avance,)
            )
        conn.commit()