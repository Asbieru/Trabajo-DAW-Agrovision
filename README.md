# Trabajo-DAW-Agrovision

# Instalar flesk y cambiar a la base de datos
    py -3 -m venv .venv
    .venv\Scripts\activate
        --NOTA: Si no te deja o te sale error, abre poerShell como administrador y escribe
            Set-ExecutionPolicy RemoteSigned
        Y acepta con S)
    pip install Flask
    flask --app main run --debug
# Crea la base de datos y las tablas o si no, no corre 
    pip install pymysql 

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