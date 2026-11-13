
import asyncio
import sqlite3

from config.settings import DB_PATH_TRACKER
from database.esquema import init_sqlite_db
from scrapers.AmazonScraper import AmazonScraper

# Constantes editables del módulo (Subtarea 6.1.5).
PRODUCT_ID = "B07WC5V4QN"
URL_PRODUCTO = "https://www.amazon.com/-/es/Afnan-Supremacy-Edición-Coleccionista-líquidas/dp/B07WC5V4QN/ref=sr_1_1?crid=37MWVAZYGDRSM&dib=eyJ2IjoiMSJ9.K1bCrvxaVLtsIJxYGCG45UJzC_0qWPdxIe-33bZnx8pTrSwdmNQDqAADKo9SNdvSYN509EL4PC8kPSYI0SXnEGvJd7EzwNGxYHuqPv1pHj9qiKQ9CMmOQgPabF64wIBtTaGsoHA5Ha_sedLk0ZG9Ht5l5-cuzHVKz-Yi8G1kEix485dHqlp33Qp1h3GjV-ta3j5MJDsnstcW2GGmwEaLroQ_KxdUTPK-U1A4LVyextloAmB0tVqhHDDSELw8aD2Um2rvfq7nPxwdyKQa4929Nppi1Nmmb0rVfXA1j-b_cpw.01vhab4RlgygVMvU84aOIE-9wc6HXNRvqevfv5oA86I&dib_tag=se&keywords=afnan+supremacy+collector%27s+edition&qid=1793037142&s=beauty&sprefix=afna%2Cbeauty%2C195&sr=1-1"
def main() -> None:
    conn = sqlite3.connect(DB_PATH_TRACKER)
    # Subtarea 6.1.3: el esquema se garantiza (idempotente) ANTES de leer o escribir.
    init_sqlite_db()
    try:
        # Subtareas 6.1.6/6.1.7: la misma conexión es de lectura y escritura;
        # solo se habla con el orquetador `obtener_datos`, nunca con `extraer_datos`.
        datos = asyncio.run(AmazonScraper(conn).obtener_datos(PRODUCT_ID, URL_PRODUCTO))
    finally:
        conn.close()

    # Imprime el diccionario devuelto: las siete claves del Contrato + `origen`.
    print("\n=== Resultado de la consulta ===")
    for campo, valor in datos.items():
        print(f"{campo}: {valor}")


if __name__ == "__main__":
    main()
