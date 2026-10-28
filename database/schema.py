import sqlite3 # 1ro se importa la librería sqlite3 para poder trabajar con bases de datos SQLite.
from datetime import date
from pathlib import Path
import sys
from dataclasses import dataclass, fields
import typing
from services.currency import convertir_a_moneda_local

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import DB_PATH_TRACKER

def init_sqlite_db():
    conexion = sqlite3.connect(DB_PATH_TRACKER) # 2do se conecta al módulo que previamente creamos (en este caso le pasamos la ruta donde se encuentra la base de datos).
    cursor = conexion.cursor() # 3ro se crea un cursor. Que es un objeto que utilizaremos, para ejecutar las sentencias SQL y obtener resultados de la base de datos. 

    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS Productos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asin TEXT UNIQUE,
            titulo TEXT NOT NULL,
            url TEXT NOT NULL,
            vendedor TEXT NOT NULL,
            categoria TEXT,
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

def ya_se_consulto_hoy(conn: sqlite3.Connection, product_id: int | None) -> bool:
    cursor = conn.execute(
        "SELECT DATE(fecha, 'localtime') FROM Historial_Precios WHERE producto_id = ? ORDER BY fecha DESC LIMIT 1",
        (product_id,)
    )
    row = cursor.fetchone()
    if row is None or row[0] is None:
        return False
    ultima_fecha = row[0]
    # CURRENT_TIMESTAMP escribe en UTC; DATE(..., 'localtime') normaliza a la hora
    # local antes de comparar, para usar una sola base temporal (Subtarea 4.1.2).
    return str(ultima_fecha) == date.today().isoformat()


def obtener_ultimo_registro(conn :sqlite3.Connection, product_id: int | None) -> dict:
    cursor = conn.execute('''
        SELECT 
            p.titulo,
            (SELECT precio_usd FROM Historial_Precios WHERE producto_id = p.id ORDER BY fecha DESC LIMIT 1) AS precio,
            'USD' AS moneda,
            p.url,
            p.vendedor,
            (SELECT total_ventas FROM Metricas_Vendedor WHERE producto_id = p.id ORDER BY fecha_registro DESC LIMIT 1) AS ventas,
            (SELECT calificacion_promedio FROM Metricas_Vendedor WHERE producto_id = p.id ORDER BY fecha_registro DESC LIMIT 1) AS rating
        FROM Productos p
        WHERE p.id = ?
    ''', (product_id,))
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

@dataclass
class ContratoDatos:
    titulo: str
    precio: float
    moneda: str
    url: str
    vendedor: str
    ventas: int | None = None
    calificacion_promedio: float | None = None

    @classmethod
    def filtrar_diccionario(cls, datos: dict) -> "ContratoDatos":

        if not isinstance(datos, dict):
            raise TypeError("Datos inválidos: se esperaba un diccionario")

        claves_validas = {campo.name for campo in fields(cls)}

        datos_filtrados = {k: v for k, v in datos.items() if k in claves_validas}

        return cls(**datos_filtrados)

    def __post_init__(self):

        for nombre, valor in (
            ("titulo", self.titulo),
            ("moneda", self.moneda),
            ("url", self.url),
            ("vendedor", self.vendedor),
        ):
            if not isinstance(valor, str):
                raise TypeError(f"{nombre} debe ser texto")

        if isinstance(self.precio, bool) or not isinstance(self.precio, (int, float)):
            raise TypeError("El precio debe ser numérico")

        self.precio = float(self.precio)

        if not self.precio > 0:
            raise ValueError("El precio debe ser mayor que cero")

        if self.ventas is not None:
            if isinstance(self.ventas, bool) or not isinstance(self.ventas, int):
                raise TypeError("Las ventas deben ser un entero o None")
        if self.calificacion_promedio is not None:
            if isinstance(self.calificacion_promedio, bool) or not isinstance(
                self.calificacion_promedio, (int, float)
            ):
                raise TypeError("La calificación debe ser numérica o None")
            self.calificacion_promedio = float(self.calificacion_promedio)


def buscar_id_producto (conn: sqlite3.Connection, asin: str ) -> int | None:
    """ Busca él id de un producto en la base de datos, con base en su codigo asin (str).
    Ejecuta una consulta a la base de datos, verifica si él id existe y lo retorna; de lo contrario retorna None."""
    cursor = conn.cursor()
    cursor.execute("SELECT Productos.id FROM Productos WHERE asin = ?", (asin,))
    producto_id = cursor.fetchone()
    if not producto_id:
        return None
    return producto_id[0]


def obtener_o_crear_producto(conn: sqlite3.Connection, asin: str, titulo: str, url: str, vendedor: str, categoria: str | None = None) -> int:
    cursor = conn.cursor()
    consulta_sql = '''
            INSERT OR IGNORE INTO Productos (asin, titulo, url, vendedor, categoria)
            VALUES (?, ?, ?, ?, ?)
        '''
    cursor.execute(consulta_sql, (asin, titulo, url, vendedor, categoria))

    cursor.execute("SELECT id FROM Productos WHERE asin = ?", (asin,))
    return cursor.fetchone()[0]

def insertar_historial_precio(conn: sqlite3.Connection, producto_id: int, precio_local: float, moneda_local: str, precio_usd: float) -> None:
    cursor = conn.cursor()
    consulta_sql = '''
                INSERT INTO Historial_Precios (producto_id, precio_local, moneda_local, precio_usd)
                VALUES (?, ?, ?, ?)
            '''
    cursor.execute(consulta_sql, (producto_id, precio_local, moneda_local, precio_usd))

def insertar_metricas_vendedor(conn: sqlite3.Connection, producto_id: int, nombre_vendedor: str | None, total_ventas: int | None, calificacion_promedio: float | None) -> bool:
    if total_ventas is None or calificacion_promedio is None:
        return False
    cursor = conn.cursor()
    consulta_sql = '''
                INSERT INTO Metricas_Vendedor (producto_id, nombre_vendedor, total_ventas, calificacion_promedio)
                VALUES(?, ?, ?, ?)
    '''
    cursor.execute(consulta_sql, (producto_id, nombre_vendedor, total_ventas, calificacion_promedio))
    return True

def guardar_datos_producto(conn: sqlite3.Connection, asin: str, datos: dict, categoria: str | None = None) -> bool:
    if not isinstance(asin, str) or not asin.strip():
        print("No se pudo guardar: el ASIN debe ser texto no vacío.")
        return False
    if conn is None:
        print("No se pudo guardar: conexión inválida.")
        return False

    try:
        verificador_datos = ContratoDatos.filtrar_diccionario(datos)

        precio_local, moneda_local = convertir_a_moneda_local(verificador_datos.precio, verificador_datos.moneda)

        producto_id = obtener_o_crear_producto(conn, asin, verificador_datos.titulo, verificador_datos.url, verificador_datos.vendedor,  categoria)

        insertar_historial_precio(conn, producto_id, precio_local, moneda_local, verificador_datos.precio)

        insertar_metricas_vendedor(conn, producto_id, verificador_datos.vendedor, verificador_datos.ventas,verificador_datos.calificacion_promedio)

        conn.commit()

        return True
    except Exception as e:
        try:
            if conn is not None:
                conn.rollback()
        except Exception:
            pass
        print(f"No se pudo guardar: {e}.")
        return False

COLUMNAS_HISTORIAL = ("fecha", "precio_usd", "titulo")

def obtener_historial_precios(conn: sqlite3.Connection, producto_id: int) -> list[dict]:
    """Devuelve el historial de precios de un producto, del más antiguo al más reciente.

    Retorna una lista de diccionarios con las claves `fecha`, `precio_usd` y `titulo`;
    `[]` si el producto no tiene registros, nunca `None`. Es de solo lectura: no
    confirma, no revierte ni cierra la conexión recibida, y no modifica `row_factory`.
    """
    cursor = conn.execute(
        "SELECT h.fecha, h.precio_usd, p.titulo "
        "FROM Historial_Precios h JOIN Productos p ON p.id = h.producto_id "
        "WHERE h.producto_id = ? "
        "ORDER BY h.fecha ASC, h.id ASC",
        (producto_id,),
    )

    filas = cursor.fetchall()

    if filas and len(filas[0]) != len(COLUMNAS_HISTORIAL):
        raise ValueError("El SELECT y COLUMNAS_HISTORIAL no coinciden")

    return [dict(zip(COLUMNAS_HISTORIAL, fila)) for fila in filas]