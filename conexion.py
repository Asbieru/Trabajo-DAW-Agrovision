"""
conexion.py  –  Conexión a la base de datos y funciones de consulta compartidas.
"""

import pymysql.cursors


# ──────────────────────────────────────────────────────────────
#  CONEXIÓN
# ──────────────────────────────────────────────────────────────

def obtenerconexion():
    """Devuelve una conexión a bd_proyectofinal. Lanza excepción si falla."""
    connection = pymysql.connect(
        host='localhost',
        user='root',
        password='',         
        database='bd_proyectofinal',
        cursorclass=pymysql.cursors.DictCursor
    )
    return connection