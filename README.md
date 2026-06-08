# Trabajo-DAW-Agrovision

# Instalar flesk y cambiar a la base de datos
    py -3 -m venv .venv
    .venv\Scripts\activate

--NOTA: Si no te deja o te sale error, abre poerShell como administrador y escribe
    Set-ExecutionPolicy RemoteSigned
    Y acepta con (S)
    
    pip install Flask
    flask --app main run --debug

Se usa esto

    py main.py
    
# Crea la base de datos y las tablas o si no, no corre 
    pip install pymysql 

    pip install openpyxl

--------------------------------------------------------------------------------------------------

# Qué hacer si hago cambios en versiones desactualizadas.
--NOTA: Revisar si cambiaron los nombres del archivo, eso se hace manualmante antes de estos pasos.
1. Guarda temporalmente tus cambios
    git stash -u
2. Trae los cambios del repositorio
    git pull origin main
3. Recupera tus cambios
    git stash pop
4. Si no deja subir cambios
    git add .
    git commit -m "" <- pon tu mensaje

--------------------------------------------------------------------------------------------------

# Como actualizar el público
1. Entrar carpeta
    cd ~/Trabajo-DAW-Agrovision
2. Ver si se modificó conexión (no cambien conexión)
    git status
3. Traer cambios
    git pull
--------------------------------------------------------------------------------------------------

# Conexion a BD pública
    def obtenerconexion():
        connection = pymysql.connect(
            host='Cristhian18.mysql.pythonanywhere-services.com',
            user='Cristhian18',
            password='agrovision',
            database='Cristhian18$agrovision',
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection

--NOTA: si se desactiva y se cambia la coneccion poner en la terminal:

    git update-index --skip-worktree conexion.py

Cuando se coloque push y pull no se movera conexion.py
