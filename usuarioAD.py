"""
usuarioAD.py  –  Acceso a datos de la tabla 'usuarios' (AgroVision)
Estructura basada en la guía del profesor (clase DTO + obtenerconexion + funciones AD)
"""
from werkzeug.security import check_password_hash
from conexion import obtenerconexion


# ──────────────────────────────────────────────────────────────
#  CLASE DTO
# ──────────────────────────────────────────────────────────────

class Usuario:
    def __init__(self, id_usuario, nombre_completo, correo, rol):
        self.id_usuario       = id_usuario
        self.nombre_completo  = nombre_completo
        self.correo           = correo
        self.rol              = rol


# ──────────────────────────────────────────────────────────────
#  AUTENTICAR USUARIO  (SELECT a la BD)
# ──────────────────────────────────────────────────────────────

def autenticarUsuario(correo, password):
    """
    Busca al usuario por correo y verifica la contraseña.
    Retorna:
      (True,  '',        dict_sesion)   si las credenciales son correctas
      (False, 'mensaje', None)          si son incorrectas
    Lanza excepción si hay error de conexión o de BD.
    """
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            sql = """
                SELECT id_usuario, nombre_completo, correo,
                       rol, password_hash, activo
                FROM usuarios
                WHERE correo = %s
            """
            cursor.execute(sql, (correo.lower(),))
            usuario = cursor.fetchone()

    if not usuario:
        return False, 'Correo o contraseña incorrectos.', None

    if not usuario['activo']:
        return False, 'Tu cuenta está desactivada. Contacta al administrador.', None

    # Verificar contraseña (hash werkzeug o texto plano para pruebas)
    hash_bd = usuario['password_hash']
    if hash_bd.startswith(('pbkdf2:', 'scrypt:', 'argon2')):
        ok = check_password_hash(hash_bd, password)
    else:
        ok = (hash_bd == password)

    if not ok:
        return False, 'Correo o contraseña incorrectos.', None

    datos_sesion = {
        'id_usuario':      usuario['id_usuario'],
        'nombre_completo': usuario['nombre_completo'],
        'correo':          usuario['correo'],
        'rol':             usuario['rol'],
    }
    return True, '', datos_sesion


# ──────────────────────────────────────────────────────────────
#  OBTENER USUARIO POR CORREO  (para "Olvidé mi contraseña")
# ──────────────────────────────────────────────────────────────

def buscarUsuarioPorCorreo(correo):
    """
    Verifica si existe un usuario activo con ese correo.
    Retorna True si existe, False si no.
    Lanza excepción si hay error de conexión.
    """
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            sql = """
                SELECT id_usuario
                FROM usuarios
                WHERE correo = %s AND activo = 1
            """
            cursor.execute(sql, (correo.lower(),))
            return cursor.fetchone() is not None


def obtenerUsuarios(rol=None):
    """Retorna usuarios activos. Si se pasa rol, filtra por él."""
    conn = obtenerconexion()
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
# ── NUEVAS FUNCIONES ───────────────────────────────────────────

def listarUsuariosCompleto():
    """Todos los usuarios activos con datos de perfil extendido."""
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id_usuario, nombre_completo, apellido,
                       correo, rol, foto_url, created_at
                FROM usuarios
                WHERE activo = 1
                ORDER BY nombre_completo
            """)
            return cursor.fetchall()


def obtenerPerfilUsuario(id_usuario):
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id_usuario, nombre_completo, apellido,
                       edad, dni, direccion, correo, rol,
                       foto_url, activo, created_at
                FROM usuarios WHERE id_usuario = %s
            """, (id_usuario,))
            return cursor.fetchone()


def estadisticasUsuario(id_usuario):
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT tipo, COUNT(*) AS total
                FROM tickets
                WHERE id_solicitante = %s OR id_agente = %s
                GROUP BY tipo ORDER BY total DESC
            """, (id_usuario, id_usuario))
            tickets_por_tipo = cursor.fetchall()

            cursor.execute("""
                SELECT estado, COUNT(*) AS total
                FROM proyectos
                WHERE id_responsable = %s
                GROUP BY estado ORDER BY total DESC
            """, (id_usuario,))
            proyectos_por_estado = cursor.fetchall()

            cursor.execute("""
                SELECT COUNT(*) AS total_agente,
                       SUM(CASE WHEN estado IN ('resuelto','cerrado') THEN 1 ELSE 0 END) AS resueltos
                FROM tickets WHERE id_agente = %s
            """, (id_usuario,))
            fila = cursor.fetchone()
            total_agente = int(fila['total_agente'] or 0)
            resueltos    = int(fila['resueltos']    or 0)
            calificacion = round((resueltos / total_agente) * 5, 1) if total_agente > 0 else None

    return {
        'tickets_por_tipo':     tickets_por_tipo,
        'proyectos_por_estado': proyectos_por_estado,
        'calificacion':         calificacion,
        'total_agente':         total_agente,
    }


def historialParticipacionUsuario(id_usuario):
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT 'ticket' AS tipo_item, t.id_ticket AS id_item,
                       t.titulo, t.tipo AS subtipo, t.prioridad, t.estado,
                       'solicitante' AS rol_usuario,
                       NULL AS codigo, NULL AS nombre_proyecto,
                       t.fecha_apertura AS fecha
                FROM tickets t WHERE t.id_solicitante = %s
            """, (id_usuario,))
            como_solicitante = cursor.fetchall()

            cursor.execute("""
                SELECT 'ticket' AS tipo_item, t.id_ticket AS id_item,
                       t.titulo, t.tipo AS subtipo, t.prioridad, t.estado,
                       'agente' AS rol_usuario,
                       NULL AS codigo, NULL AS nombre_proyecto,
                       t.fecha_apertura AS fecha
                FROM tickets t
                WHERE t.id_agente = %s
                  AND (t.id_solicitante != %s OR t.id_solicitante IS NULL)
            """, (id_usuario, id_usuario))
            como_agente = cursor.fetchall()

            cursor.execute("""
                SELECT 'historia' AS tipo_item, h.id_historia AS id_item,
                       h.titulo, h.tipo AS subtipo, h.prioridad, h.estado,
                       'asignado' AS rol_usuario,
                       h.codigo, p.nombre AS nombre_proyecto,
                       h.created_at AS fecha
                FROM historias h
                JOIN proyectos p ON h.id_proyecto = p.id_proyecto
                WHERE h.id_asignado = %s
            """, (id_usuario,))
            como_asignado = cursor.fetchall()

            cursor.execute("""
                SELECT 'historia' AS tipo_item, p.id_proyecto AS id_item,
                       p.nombre AS titulo, p.estado AS subtipo,
                       'media' AS prioridad,
                       CASE p.estado
                           WHEN 'completado'    THEN 'completada'
                           WHEN 'pausado'       THEN 'cancelada'
                           WHEN 'en_desarrollo' THEN 'en_progreso'
                           WHEN 'qa'            THEN 'en_progreso'
                           ELSE 'backlog'
                       END AS estado,
                       'responsable' AS rol_usuario,
                       NULL AS codigo, p.nombre AS nombre_proyecto,
                       p.created_at AS fecha
                FROM proyectos p WHERE p.id_responsable = %s
            """, (id_usuario,))
            como_responsable = cursor.fetchall()

    mapa = {
        'abierto':       'backlog',
        'en_progreso':   'en_progreso',
        'resuelto':      'completada',
        'cerrado':       'completada',
        'base_proyecto': 'cancelada',
    }
    todos = []
    for t in list(como_solicitante) + list(como_agente):
        t = dict(t)
        t['estado'] = mapa.get(t['estado'], 'backlog')
        todos.append(t)
    for h in list(como_asignado) + list(como_responsable):
        todos.append(dict(h))
    return todos


def resumenHistorialUsuario(id_usuario):
    items = historialParticipacionUsuario(id_usuario)
    estados = {'backlog': 0, 'por_hacer': 0, 'en_progreso': 0, 'completada': 0, 'cancelada': 0}
    tickets_total = historias_total = 0
    for i in items:
        estados[i['estado']] = estados.get(i['estado'], 0) + 1
        if i['tipo_item'] == 'ticket':
            tickets_total += 1
        else:
            historias_total += 1
    return {
        'estados':         estados,
        'tickets_total':   tickets_total,
        'historias_total': historias_total,
        'total':           len(items),
    }