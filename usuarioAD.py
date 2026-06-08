"""
usuarioAD.py – Acceso a datos de la tabla 'usuarios' (AgroVision)
Adaptado siguiendo exactamente el patrón de ticketAD.py y proyectoAD.py
"""

from werkzeug.security import check_password_hash
from conexion import obtenerconexion

# ──────────────────────────────────────────────────────────────
# CLASE DTO
# ──────────────────────────────────────────────────────────────
class Usuario:
    def __init__(self, id_usuario, nombre_completo, correo, rol):
        self.id_usuario      = id_usuario
        self.nombre_completo = nombre_completo
        self.correo          = correo
        self.rol             = rol

# ──────────────────────────────────────────────────────────────
# AUTENTICAR USUARIO
# ──────────────────────────────────────────────────────────────
def autenticarUsuario(correo, password):
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id_usuario, nombre_completo, correo,
                       rol, password_hash, activo
                FROM usuarios
                WHERE correo = %s
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

    return True, '', {
        'id_usuario'     : usuario['id_usuario'],
        'nombre_completo': usuario['nombre_completo'],
        'correo'         : usuario['correo'],
        'rol'            : usuario['rol'],
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
# OBTENER USUARIOS (para dropdowns — igual que antes)
# ──────────────────────────────────────────────────────────────
def obtenerUsuarios(rol=None):
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

# ──────────────────────────────────────────────────────────────
# LISTAR USUARIOS COMPLETO
# ──────────────────────────────────────────────────────────────
def listarUsuariosCompleto():
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

# ──────────────────────────────────────────────────────────────
# PERFIL DE USUARIO
# ──────────────────────────────────────────────────────────────
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

# ──────────────────────────────────────────────────────────────
# ESTADÍSTICAS
# Patrón copiado de ticketAD.listarTickets() y proyectoAD.listarProyectos()
# ──────────────────────────────────────────────────────────────
def estadisticasUsuario(id_usuario):
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:

            # Tickets por tipo — igual JOIN que ticketAD.py
            cursor.execute("""
                SELECT t.tipo, COUNT(*) AS total
                FROM tickets t
                LEFT JOIN detalle_ticket d ON d.id_ticket = t.id_ticket
                WHERE t.id_solicitante = %s OR d.id_agente = %s
                GROUP BY t.tipo
                ORDER BY total DESC
            """, (id_usuario, id_usuario))
            tickets_por_tipo = cursor.fetchall()

            # Proyectos por estado — igual que proyectoAD.listarProyectos()
            # usa id_responsable y tabla asignado, filtra estado2=1
            cursor.execute("""
                SELECT p.estado, COUNT(*) AS total
                FROM proyectos p
                LEFT JOIN asignado a
                       ON a.id_proyecto = p.id_proyecto AND a.id_usuario = %s
                WHERE p.estado2 = 1
                  AND (p.id_responsable = %s OR a.id_usuario IS NOT NULL)
                GROUP BY p.estado
                ORDER BY total DESC
            """, (id_usuario, id_usuario))
            proyectos_por_estado = cursor.fetchall()

            # Calificación como agente — agente está en detalle_ticket
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
            # Columnas copiadas de ticketAD.listarTickets()
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

            # Proyectos donde participa
            # Patrón copiado de proyectoAD.listarProyectos():
            # usa p.id_responsable, LEFT JOIN asignado, WHERE estado2=1
            cursor.execute("""
                SELECT DISTINCT
                       p.id_proyecto,
                       p.nombre          AS titulo,
                       p.estado          AS estado_proyecto,
                       CASE WHEN p.id_responsable = %s
                            THEN 'responsable'
                            ELSE 'asignado' END AS rol_usuario,
                       p.nombre          AS nombre_proyecto,
                       p.created_at      AS fecha
                FROM proyectos p
                LEFT JOIN asignado asig
                       ON asig.id_proyecto = p.id_proyecto
                      AND asig.id_usuario  = %s
                LEFT JOIN actividades a
                       ON a.id_proyecto = p.id_proyecto
                      AND a.id_asignado = %s
                      AND a.estado2 = 1
                WHERE p.estado2 = 1
                  AND (p.id_responsable = %s
                       OR asig.id_usuario IS NOT NULL
                       OR a.id_asignado  IS NOT NULL)
            """, (id_usuario, id_usuario, id_usuario, id_usuario))
            proyectos_raw = cursor.fetchall()

            # Actividades propias — igual que actividadAD patrón
            cursor.execute("""
                SELECT a.id_proyecto, a.titulo, a.codigo, a.estado
                FROM actividades a
                WHERE a.id_asignado = %s AND a.estado2 = 1
            """, (id_usuario,))
            actividades_propias = cursor.fetchall()

            # Actividades de proyectos donde es responsable/asignado
            cursor.execute("""
                SELECT a.id_proyecto, a.titulo, a.codigo, a.estado
                FROM actividades a
                JOIN proyectos p ON a.id_proyecto = p.id_proyecto
                LEFT JOIN asignado asig
                       ON asig.id_proyecto = p.id_proyecto
                      AND asig.id_usuario  = %s
                WHERE p.estado2 = 1 AND a.estado2 = 1
                  AND (p.id_responsable = %s OR asig.id_usuario IS NOT NULL)
            """, (id_usuario, id_usuario))
            todas_actividades = cursor.fetchall()

    # ── Lógica Kanban ─────────────────────────────────────────
    jerarquia = ['backlog', 'por_hacer', 'en_progreso', 'completada', 'cancelada']

    mapa_proyecto = {
        'planificado'  : 'backlog',
        'en_revision'  : 'backlog',
        'en_desarrollo': 'en_progreso',
        'qa'           : 'en_progreso',
        'completado'   : 'completada',
        'pausado'      : 'cancelada',
        'rechazado'    : 'cancelada',
    }
    # Estados copiados del ENUM de tickets en ticketAD.py
    mapa_ticket = {
        'solicitado' : 'backlog',
        'en_progreso': 'en_progreso',
        'resuelto'   : 'completada',
        'cerrado'    : 'completada',
        'cancelado'  : 'cancelada',
    }

    def estado_mas_atrasado(acts):
        estados = [a['estado'] for a in acts]
        activos = [e for e in estados if e != 'cancelada']
        pool    = activos if activos else estados
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
        estados[i['estado']] = estados.get(i['estado'], 0) + 1
        if i['tipo_item'] == 'ticket':
            tickets_total += 1
        else:
            proyectos_total += 1

    return {
        'estados'        : estados,
        'tickets_total'  : tickets_total,
        'proyectos_total': proyectos_total,
        'total'          : len(items),
    }