import pymysql

try:
    conn = pymysql.connect(
        host='Cristhian18.mysql.pythonanywhere-services.com',
        user='Cristhian18',
        password='TU_PASSWORD',
        database='Cristhian18$agrovision'
    )
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tablas = cursor.fetchall()
    print("--- TABLAS ENCONTRADAS ---")
    for tabla in tablas:
        print(tabla[0])
    conn.close()
except Exception as e:
    print(f"ERROR: {e}")
