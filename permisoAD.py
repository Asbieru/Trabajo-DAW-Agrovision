from conexion import obtenerconexion

def listarPermisos(id_rol=None):
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            if id_rol:
                cursor.execute("""
                    SELECT rp.id_rol_permiso, rp.nombre, rp.nivel, rp.id_rol,
                           r.nombre AS rol_nombre
                    FROM rol_permiso rp
                    JOIN rol r ON r.id_rol = rp.id_rol
                    WHERE rp.id_rol = %s
                    ORDER BY rp.nombre
                """, (id_rol,))
            else:
                cursor.execute("""
                    SELECT rp.id_rol_permiso, rp.nombre, rp.nivel, rp.id_rol,
                           r.nombre AS rol_nombre
                    FROM rol_permiso rp
                    JOIN rol r ON r.id_rol = rp.id_rol
                    ORDER BY r.id_rol DESC, rp.nombre
                """)
            return cursor.fetchall()

def obtenerPermiso(id_rol_permiso):
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT rp.id_rol_permiso, rp.nombre, rp.nivel, rp.id_rol,
                       r.nombre AS rol_nombre
                FROM rol_permiso rp
                JOIN rol r ON r.id_rol = rp.id_rol
                WHERE rp.id_rol_permiso = %s
            """, (id_rol_permiso,))
            return cursor.fetchone()

def insertarPermiso(nombre, nivel, id_rol):
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO rol_permiso (nombre, nivel, id_rol) VALUES (%s, %s, %s)", (nombre, nivel, id_rol))
            conn.commit()
            return cursor.lastrowid

def actualizarPermiso(id_rol_permiso, nombre, nivel, id_rol):
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE rol_permiso SET nombre=%s, nivel=%s, id_rol=%s WHERE id_rol_permiso=%s", (nombre, nivel, id_rol, id_rol_permiso))
            conn.commit()

def eliminarPermiso(id_rol_permiso):
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM rol_permiso WHERE id_rol_permiso = %s", (id_rol_permiso,))
            conn.commit()

def obtenerPermisosPorRol(id_rol):
    conn = obtenerconexion()
    with conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT nombre FROM rol_permiso WHERE id_rol = %s", (id_rol,))
            return [r['nombre'] for r in cursor.fetchall()]
