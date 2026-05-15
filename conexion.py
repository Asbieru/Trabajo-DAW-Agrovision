"""
conexion.py  –  Conexión a la base de datos y funciones de consulta compartidas.
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
