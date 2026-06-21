from conexion import obtenerconexion

def listarRoles():
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id_rol, nombre, descripcion FROM rol ORDER BY nombre")
            return cursor.fetchall()

def obtenerRol(id_rol):
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id_rol, nombre, descripcion FROM rol WHERE id_rol = %s", (id_rol,))
            return cursor.fetchone()

def insertarRol(nombre, descripcion):
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO rol (nombre, descripcion) VALUES (%s, %s)", (nombre, descripcion))
            conn.commit()
            return cursor.lastrowid

def actualizarRol(id_rol, nombre, descripcion):
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE rol SET nombre=%s, descripcion=%s WHERE id_rol=%s", (nombre, descripcion, id_rol))
            conn.commit()

def eliminarRol(id_rol):
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as cnt FROM usuarios WHERE id_rol = %s", (id_rol,))
            if cursor.fetchone()['cnt'] > 0:
                return False
            cursor.execute("DELETE FROM rol_permiso WHERE id_rol = %s", (id_rol,))
            cursor.execute("DELETE FROM rol WHERE id_rol = %s", (id_rol,))
            conn.commit()
            return True
