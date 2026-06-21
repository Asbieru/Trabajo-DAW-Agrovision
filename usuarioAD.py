from werkzeug.security import check_password_hash, generate_password_hash
from conexion import obtenerconexion

class Usuario:
    def __init__(self, id_usuario, nombre_completo, correo, nivel=1, id_rol=None, rol_nombre=None):
        self.id_usuario      = id_usuario
        self.nombre_completo = nombre_completo
        self.correo          = correo
        self.nivel           = nivel
        self.id_rol          = id_rol
        self.rol_nombre      = rol_nombre

def _obtenerPermisosUsuario(id_rol):
    if not id_rol:
        return []
    from permisoAD import obtenerPermisosPorRol
    return obtenerPermisosPorRol(id_rol)

# ──────────────────────────────────────────────────────────────
# AUTENTICAR
# ──────────────────────────────────────────────────────────────
def autenticarUsuario(correo, password):
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.id_usuario, u.nombre_completo, u.correo,
                       u.password_hash, u.activo, u.id_rol, u.nivel,
                       r.nombre AS rol_nombre
                FROM usuarios u
                LEFT JOIN rol r ON r.id_rol = u.id_rol
                WHERE u.correo = %s
            """, (correo.lower(),))
            usuario = cursor.fetchone()

    if not usuario:
        return False, 'Correo o contraseña incorrectos.', None
    if not usuario['activo']:
        return False, 'Tu cuenta está desactivada. Contacta al administrador.', None

    hash_bd = usuario['password_hash']
    if hash_bd and hash_bd.startswith(('pbkdf2:', 'scrypt:', 'argon2')):
        ok = check_password_hash(hash_bd, password)
    else:
        ok = (hash_bd == password)

    if not ok:
        return False, 'Correo o contraseña incorrectos.', None

    permisos = _obtenerPermisosUsuario(usuario['id_rol'])

    return True, '', {
        'id_usuario'     : usuario['id_usuario'],
        'nombre_completo': usuario['nombre_completo'],
        'correo'         : usuario['correo'],
        'rol_nombre'     : usuario['rol_nombre'] or '',
        'rol_id'         : usuario['id_rol'],
        'nivel'          : usuario['nivel'] or 1,
        'permisos'       : permisos,
    }

# ──────────────────────────────────────────────────────────────
# BUSCAR POR CORREO
# ──────────────────────────────────────────────────────────────
def buscarUsuarioPorCorreo(correo):
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id_usuario FROM usuarios
                WHERE correo = %s AND activo = 1
            """, (correo.lower(),))
            return cursor.fetchone() is not None

# ──────────────────────────────────────────────────────────────
# OBTENER USUARIOS (dropdowns)
# ──────────────────────────────────────────────────────────────
def obtenerUsuarios(rol=None):
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            if rol:
                cursor.execute("""
                    SELECT u.id_usuario, u.nombre_completo, r.nombre AS rol_nombre
                    FROM usuarios u
                    JOIN rol r ON r.id_rol = u.id_rol
                    WHERE u.activo=1 AND r.nombre=%s
                    ORDER BY u.nombre_completo
                """, (rol,))
            else:
                cursor.execute("""
                    SELECT u.id_usuario, u.nombre_completo, r.nombre AS rol_nombre
                    FROM usuarios u
                    LEFT JOIN rol r ON r.id_rol = u.id_rol
                    WHERE u.activo=1
                    ORDER BY u.nombre_completo
                """)
            return cursor.fetchall()

# ──────────────────────────────────────────────────────────────
# LISTAR USUARIOS COMPLETO
# ──────────────────────────────────────────────────────────────
def listarUsuariosCompleto():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.id_usuario, u.nombre_completo, u.apellido,
                       u.correo, u.nivel, u.foto_url, u.created_at,
                       u.id_rol, r.nombre AS rol_nombre
                FROM usuarios u
                LEFT JOIN rol r ON r.id_rol = u.id_rol
                WHERE u.activo = 1
                ORDER BY u.nombre_completo
            """)
            return cursor.fetchall()

# ──────────────────────────────────────────────────────────────
# INSERTAR USUARIO
# ──────────────────────────────────────────────────────────────
def insertarUsuario(nombre_completo, correo, password, id_rol, nivel=1, apellido=None, edad=None, dni=None, direccion=None, foto_url=None):
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            password_hash = generate_password_hash(password)
            cursor.execute("""
                INSERT INTO usuarios
                (nombre_completo, apellido, edad, dni, direccion, correo, password_hash, nivel, id_rol, foto_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                nombre_completo, apellido, edad, dni, direccion,
                correo.lower(), password_hash, nivel, id_rol, foto_url
            ))
            conn.commit()
            return True, cursor.lastrowid

# ──────────────────────────────────────────────────────────────
# PERFIL DE USUARIO
# ──────────────────────────────────────────────────────────────
def obtenerPerfilUsuario(id_usuario):
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT u.id_usuario, u.nombre_completo, u.apellido,
                       u.edad, u.dni, u.direccion, u.correo, u.nivel,
                       u.foto_url, u.activo, u.created_at,
                       u.id_rol, r.nombre AS rol_nombre
                FROM usuarios u
                LEFT JOIN rol r ON r.id_rol = u.id_rol
                WHERE u.id_usuario = %s
            """, (id_usuario,))
            return cursor.fetchone()

# ──────────────────────────────────────────────────────────────
# ESTADÍSTICAS
# ──────────────────────────────────────────────────────────────
def estadisticasUsuario(id_usuario):
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:

            # Tickets por tipo: solicitante en tickets, agente en detalle_ticket
            cursor.execute("""
                SELECT t.tipo, COUNT(*) AS total
                FROM tickets t
                LEFT JOIN detalle_ticket d ON d.id_ticket = t.id_ticket
                WHERE t.id_solicitante = %s OR d.id_agente = %s
                GROUP BY t.tipo
                ORDER BY total DESC
            """, (id_usuario, id_usuario))
            tickets_por_tipo = cursor.fetchall()

            # Proyectos por estado: id_Stakeholder (nombre exacto del SQL)
            # o en tabla asignado
            cursor.execute("""
                SELECT p.estado, COUNT(*) AS total
                FROM proyectos p
                LEFT JOIN asignado a
                       ON a.id_proyecto = p.id_proyecto
                      AND a.id_usuario  = %s
                WHERE p.estado2 = 1
                  AND (p.id_Stakeholder = %s OR a.id_usuario IS NOT NULL)
                GROUP BY p.estado
                ORDER BY total DESC
            """, (id_usuario, id_usuario))
            proyectos_por_estado = cursor.fetchall()

            # Calificación como agente
            cursor.execute("""
                SELECT COUNT(*) AS total_agente,
                       SUM(CASE WHEN t.estado IN ('resuelto','cerrado') THEN 1 ELSE 0 END) AS resueltos
                FROM detalle_ticket d
                JOIN tickets t ON t.id_ticket = d.id_ticket
                WHERE d.id_agente = %s
            """, (id_usuario,))
            fila         = cursor.fetchone()
            total_agente = int(fila['total_agente'] or 0)
            resueltos    = int(fila['resueltos']    or 0)
            calificacion = round((resueltos / total_agente) * 5, 1) if total_agente > 0 else None

    return {
        'tickets_por_tipo'    : tickets_por_tipo,
        'proyectos_por_estado': proyectos_por_estado,
        'calificacion'        : calificacion,
        'total_agente'        : total_agente,
    }

# ──────────────────────────────────────────────────────────────
# HISTORIAL DE PARTICIPACIÓN
# ──────────────────────────────────────────────────────────────
def historialParticipacionUsuario(id_usuario):
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:

            # Tickets como SOLICITANTE
            cursor.execute("""
                SELECT 'ticket'       AS tipo_item,
                       t.id_ticket    AS id_item,
                       t.titulo,
                       t.tipo         AS subtipo,
                       IFNULL(d.prioridad, 'media') AS prioridad,
                       t.estado,
                       'solicitante'  AS rol_usuario,
                       NULL           AS codigo,
                       NULL           AS nombre_proyecto,
                       t.f_registro   AS fecha
                FROM tickets t
                LEFT JOIN detalle_ticket d ON d.id_ticket = t.id_ticket
                WHERE t.id_solicitante = %s
            """, (id_usuario,))
            como_solicitante = cursor.fetchall()

            # Tickets como AGENTE (agente vive en detalle_ticket)
            cursor.execute("""
                SELECT 'ticket'       AS tipo_item,
                       t.id_ticket    AS id_item,
                       t.titulo,
                       t.tipo         AS subtipo,
                       IFNULL(d.prioridad, 'media') AS prioridad,
                       t.estado,
                       'agente'       AS rol_usuario,
                       NULL           AS codigo,
                       NULL           AS nombre_proyecto,
                       t.f_registro   AS fecha
                FROM detalle_ticket d
                JOIN tickets t ON t.id_ticket = d.id_ticket
                WHERE d.id_agente = %s
                  AND t.id_solicitante != %s
            """, (id_usuario, id_usuario))
            como_agente = cursor.fetchall()

            # Proyectos donde participa como Stakeholder o en asignado o con actividades
            # id_Stakeholder es el nombre exacto de la columna en proyectos
            cursor.execute("""
                SELECT DISTINCT
                       p.id_proyecto,
                       p.nombre         AS titulo,
                       p.estado         AS estado_proyecto,
                       CASE WHEN p.id_Stakeholder = %s
                            THEN 'responsable'
                            ELSE 'asignado' END AS rol_usuario,
                       p.nombre         AS nombre_proyecto,
                       p.created_at     AS fecha
                FROM proyectos p
                LEFT JOIN asignado asig
                       ON asig.id_proyecto = p.id_proyecto
                      AND asig.id_usuario  = %s
                LEFT JOIN actividades a
                       ON a.id_proyecto = p.id_proyecto
                      AND a.id_asignado = %s
                      AND a.estado2     = 1
                WHERE p.estado2 = 1
                  AND p.estado != 'eliminado'
                  AND (p.id_Stakeholder = %s
                       OR asig.id_usuario IS NOT NULL
                       OR a.id_asignado  IS NOT NULL)
            """, (id_usuario, id_usuario, id_usuario, id_usuario))
            proyectos_raw = cursor.fetchall()

            # Actividades propias
            cursor.execute("""
                SELECT a.id_proyecto, a.titulo, a.codigo, a.estado
                FROM actividades a
                WHERE a.id_asignado = %s AND a.estado2 = 1
            """, (id_usuario,))
            actividades_propias = cursor.fetchall()

            # Actividades de proyectos donde es Stakeholder o asignado
            cursor.execute("""
                SELECT a.id_proyecto, a.titulo, a.codigo, a.estado
                FROM actividades a
                JOIN proyectos p ON a.id_proyecto = p.id_proyecto
                LEFT JOIN asignado asig
                       ON asig.id_proyecto = p.id_proyecto
                      AND asig.id_usuario  = %s
                WHERE p.estado2 = 1
                  AND a.estado2 = 1
                  AND (p.id_Stakeholder = %s OR asig.id_usuario IS NOT NULL)
            """, (id_usuario, id_usuario))
            todas_actividades = cursor.fetchall()

    # ── Lógica Kanban ─────────────────────────────────────────
    # Estados de actividades según el ENUM del SQL:
    # backlog, por_hacer, en_progreso, completada, cancelada, bloqueado, eliminado
    jerarquia = ['backlog', 'por_hacer', 'en_progreso', 'completada', 'cancelada']

    # Estados de proyectos según el ENUM del SQL:
    # en_revision, rechazado, planificado, en_desarrollo, qa, pausado, completado, eliminado
    mapa_proyecto = {
        'en_revision'  : 'backlog',
        'rechazado'    : 'cancelada',
        'planificado'  : 'por_hacer',
        'en_desarrollo': 'en_progreso',
        'qa'           : 'en_progreso',
        'pausado'      : 'cancelada',
        'completado'   : 'completada',
        'eliminado'    : 'cancelada',
    }
    # Estados de tickets según el ENUM del SQL:
    # solicitado, en_progreso, resuelto, cerrado, cancelado
    mapa_ticket = {
        'solicitado' : 'backlog',
        'en_progreso': 'en_progreso',
        'resuelto'   : 'completada',
        'cerrado'    : 'completada',
        'cancelado'  : 'cancelada',
    }

    def estado_mas_atrasado(acts):
        estados = [a['estado'] for a in acts if a['estado'] != 'eliminado']
        activos = [e for e in estados if e not in ('cancelada', 'completada')]
        pool    = activos if activos else estados
        if not pool:
            return 'backlog'
        return min(pool, key=lambda e: jerarquia.index(e) if e in jerarquia else 99)

    propias_por_proyecto = {}
    for a in actividades_propias:
        propias_por_proyecto.setdefault(a['id_proyecto'], []).append(dict(a))

    todas_por_proyecto = {}
    for a in todas_actividades:
        todas_por_proyecto.setdefault(a['id_proyecto'], []).append(dict(a))

    resultado = []

    for t in list(como_solicitante) + list(como_agente):
        t = dict(t)
        t['estado'] = mapa_ticket.get(t['estado'], 'backlog')
        resultado.append(t)

    for p in proyectos_raw:
        p   = dict(p)
        pid = p['id_proyecto']
        propias = propias_por_proyecto.get(pid, [])
        todas   = todas_por_proyecto.get(pid, [])

        if propias:
            estado_kanban = estado_mas_atrasado(propias)
        elif todas:
            estado_kanban = estado_mas_atrasado(todas)
        else:
            estado_kanban = mapa_proyecto.get(p['estado_proyecto'], 'backlog')

        p['tipo_item']   = 'proyecto'
        p['estado']      = estado_kanban
        p['subtipo']     = p['estado_proyecto']
        p['prioridad']   = 'media'
        p['codigo']      = None
        p['actividades'] = propias
        resultado.append(p)

    return resultado

# ──────────────────────────────────────────────────────────────
# RESUMEN HISTORIAL
# ──────────────────────────────────────────────────────────────
def resumenHistorialUsuario(id_usuario):
    items = historialParticipacionUsuario(id_usuario)
    estados = {'backlog': 0, 'por_hacer': 0, 'en_progreso': 0, 'completada': 0, 'cancelada': 0}
    tickets_total = proyectos_total = 0

    for i in items:
        k = i['estado']
        if k in estados:
            estados[k] += 1
        tickets_total  += 1 if i['tipo_item'] == 'ticket'   else 0
        proyectos_total += 1 if i['tipo_item'] == 'proyecto' else 0

    return {
        'estados'        : estados,
        'tickets_total'  : tickets_total,
        'proyectos_total': proyectos_total,
        'total'          : len(items),
    }