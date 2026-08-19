import sqlite3 # 1ro se importa la librería sqlite3 para poder trabajar con bases de datos SQLite.
from config.config import DB_PATH

def init_sqlite_db():
    conexion = sqlite3.connect(DB_PATH) # 2do se conecta al módulo que previamente creamos (en este caso le pasamos la ruta donde se encuentra la base de datos).
    cursor = conexion.cursor() # 3ro se crea un cursor. Que es un objeto que utilizaremos, para ejecutar las sentencias SQL y obtener resultados de la base de datos. 

    cursor.executescript('''
        CREATE TABLE Productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            url TEXT NOT NULL,
            tienda TEXT NOT NULL,
            categoria TEXT NOT NULL,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE Historial_Precios(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL,
            precio_local REAL NOT NULL,
            moneda_local TEXT NOT NULL,
            precio_usd REAL NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (producto_id) REFERENCES Productos(id)
        );

        CREATE TABLE Metricas_Vendedor (
            id integer PRIMARY KEY AUTOINCREMENT,
            producto_id integer NOT NULL,
            nombre_vendedor TEXT NOT NULL,
            total_ventas INTEGER NOT NULL,
            calificacion_promedio REAL NOT NULL,
            porcentaje_reputacion REAL NOT NULL,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (producto_id) REFERENCES Productos(id)
        );
    ''') # 4to ejecutamos un script SQL que crea las tablas necesarias para nuestra base de datos.
    conexion.commit() # 5to guardamos definitivamente los cambios realizados.
    conexion.close() # 6to cerramos la conexión con la base de datos.

if __name__ == "__main__":
    init_sqlite_db() # 7mo llamamos a la función init_sqlite_db() para inicializar la base de datos.
