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
      (False, 'mensaje', None)          si son incorrectas o hay error
    """
    try:
        conn = obtenerconexion()
        if conn:
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

    except Exception as e:
        print(f"[ERROR autenticarUsuario] {e}")
        return False, f'Error al autenticar: {e}', None

    return False, 'No se pudo conectar a la base de datos.', None


# ──────────────────────────────────────────────────────────────
#  OBTENER USUARIO POR CORREO  (para "Olvidé mi contraseña")
# ──────────────────────────────────────────────────────────────

def buscarUsuarioPorCorreo(correo):
    """
    Verifica si existe un usuario activo con ese correo.
    Retorna True si existe, False si no.
    (En un sistema real aquí se enviaría un correo de recuperación.)
    """
    try:
        conn = obtenerconexion()
        if conn:
            with conn:
                with conn.cursor() as cursor:
                    sql = """
                        SELECT id_usuario
                        FROM usuarios
                        WHERE correo = %s AND activo = 1
                    """
                    cursor.execute(sql, (correo.lower(),))
                    return cursor.fetchone() is not None
    except Exception as e:
        print(f"[ERROR buscarUsuarioPorCorreo] {e}")
    return False