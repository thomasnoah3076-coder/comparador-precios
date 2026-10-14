import sqlite3 # 1ro se importa la librería sqlite3 para poder trabajar con bases de datos SQLite.
from datetime import date
from pathlib import Path
import sys

# Arranque de ruta para permitir la EJECUCIÓN DIRECTA del archivo (python database/schema.py).
# Al ejecutar un archivo, Python pone SU directorio (database/) en sys.path, no la raíz del
# proyecto, y "from config.settings import ..." fallaría con ModuleNotFoundError.
# El guard (__package__ vacío) garantiza que esto solo ocurra al ejecutar el archivo directamente:
# al importarlo como paquete (import database.schema) o correrlo con -m (python -m database.schema),
# __package__ vale "database" y la raíz ya está en sys.path (sin efectos secundarios).
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import DB_PATH_TRACKER

def init_sqlite_db():
    conexion = sqlite3.connect(DB_PATH_TRACKER) # 2do se conecta al módulo que previamente creamos (en este caso le pasamos la ruta donde se encuentra la base de datos).
    cursor = conexion.cursor() # 3ro se crea un cursor. Que es un objeto que utilizaremos, para ejecutar las sentencias SQL y obtener resultados de la base de datos. 

    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS Productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL,
            url TEXT NOT NULL,
            vendedor TEXT NOT NULL,
            categoria TEXT NOT NULL,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS Historial_Precios(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL,
            precio_local REAL NOT NULL,
            moneda_local TEXT NOT NULL,
            precio_usd REAL NOT NULL,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (producto_id) REFERENCES Productos(id)
        );

        CREATE TABLE IF NOT EXISTS Metricas_Vendedor (
            id integer PRIMARY KEY AUTOINCREMENT,
            producto_id integer NOT NULL,
            nombre_vendedor TEXT NOT NULL,
            total_ventas INTEGER NOT NULL,
            calificacion_promedio REAL NOT NULL,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (producto_id) REFERENCES Productos(id)
        );
    ''') # 4to ejecutamos un script SQL que crea las tablas necesarias para nuestra base de datos.
    # IF NOT EXISTS: la inicialización es segura de repetir (CONSTITUTION §3). Si las tablas ya
    # existen no se tocan (ni se vacían ni se recrean); si faltan alguna u otras, solo se crean esas.
    conexion.commit() # 5to guardamos definitivamente los cambios realizados.
    conexion.close() # 6to cerramos la conexión con la base de datos.

def ya_se_consulto_hoy(conn, product_id: int) -> bool:
    cursor = conn.execute(
        "SELECT fecha FROM Historial_Precios WHERE producto_id = ? ORDER BY fecha DESC LIMIT 1",
        (product_id,)
    )
    row = cursor.fetchone()
    if row is None or row[0] is None:
        return False
    ultima_fecha = row[0]
    # El formato guardado es un TIMESTAMP completo ("2026-10-14 12:15:20"),
    # por lo que solo se compara la parte de fecha ("2026-10-14") con hoy.
    return ultima_fecha.startswith(date.today().isoformat())


def obtener_ultimo_registro(conn, product_id: int) -> dict:
    query = """
        SELECT 
            p.nombre,
            (SELECT precio_local FROM Historial_Precios WHERE producto_id = p.id ORDER BY fecha DESC LIMIT 1) AS precio,
            (SELECT moneda_local FROM Historial_Precios WHERE producto_id = p.id ORDER BY fecha DESC LIMIT 1) AS moneda,
            p.url,
            p.vendedor,
            (SELECT total_ventas FROM Metricas_Vendedor WHERE producto_id = p.id ORDER BY fecha_registro DESC LIMIT 1) AS ventas,
            (SELECT calificacion_promedio FROM Metricas_Vendedor WHERE producto_id = p.id ORDER BY fecha_registro DESC LIMIT 1) AS rating
        FROM Productos p
        WHERE p.id = ?
    """

    cursor = conn.execute(query, (product_id,))
    row = cursor.fetchone()

    # Si no se encuentra el producto en la tabla principal
    if row is None:
        return {
            "titulo": None,
            "precio": None,
            "moneda": None,
            "url": None,
            "vendedor": None,
            "ventas": None,
            "calificacion_promedio": None
        }

    # Si se encuentra, mapeamos los resultados al contrato de datos (MEMORY.md §4)
    return {
        "titulo": row[0],
        "precio": row[1],
        "moneda": row[2],
        "url": row[3],
        "vendedor": row[4],
        "ventas": row[5],
        "calificacion_promedio": row[6]
    }

if __name__ == "__main__":
    init_sqlite_db() # 7mo llamamos a la función init_sqlite_db() para inicializar la base de datos.
