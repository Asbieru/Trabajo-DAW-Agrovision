"""
ad.py  –  Capa de Acceso a Datos  (AgroVisión · bd_proyectofinal)
Patrón igual al CRUD de películas: clases DTO + función obtenerconexion()
+ funciones de inserción para cada entidad.
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


class Ticket:
    def __init__(self, titulo, tipo, prioridad, aplicacion,
                 id_solicitante, sla_horas, descripcion):
        self.titulo          = titulo
        self.tipo            = tipo
        self.prioridad       = prioridad
        self.aplicacion      = aplicacion
        self.id_solicitante  = id_solicitante
        self.sla_horas       = sla_horas
        self.descripcion     = descripcion


class Proyecto:
    def __init__(self, nombre, id_responsable, estado,
                 fecha_inicio, fecha_fin_plan, descripcion):
        self.nombre          = nombre
        self.id_responsable  = id_responsable
        self.estado          = estado
        self.fecha_inicio    = fecha_inicio
        self.fecha_fin_plan  = fecha_fin_plan
        self.descripcion     = descripcion


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


def listarTickets():
    """Retorna tickets con nombre del solicitante."""
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql = """
                        SELECT t.id_ticket, t.titulo, t.tipo, t.prioridad,
                               t.aplicacion, t.estado, t.fecha_apertura, t.sla_horas,
                               u.nombre_completo AS nombre_solicitante
                        FROM tickets t
                        JOIN usuarios u ON t.id_solicitante = u.id_usuario
                        ORDER BY
                            FIELD(t.prioridad,'critica','alta','media','baja'),
                            t.fecha_apertura DESC
                    """
                    cursor.execute(sql)
                    return cursor.fetchall()
    except Exception as e:
        print(f"[ERROR listarTickets] {e}")
    return []


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


def insertarTicket(obj: Ticket) -> bool:
    """Inserta un ticket de soporte. Retorna True si tuvo éxito."""
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql = """
                        INSERT INTO tickets
                            (titulo, tipo, prioridad, aplicacion,
                             id_solicitante, sla_horas, descripcion)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(sql, (
                        obj.titulo, obj.tipo, obj.prioridad,
                        obj.aplicacion, obj.id_solicitante,
                        obj.sla_horas, obj.descripcion
                    ))
                conn.commit()
            return True
    except Exception as e:
        print(f"[ERROR insertarTicket] {e}")
    return False


def insertarProyecto(obj: Proyecto) -> bool:
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
