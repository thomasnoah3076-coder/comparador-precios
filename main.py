
import asyncio
import sqlite3

from config.settings import DB_PATH_TRACKER
from database.schema import init_sqlite_db
from scrapers.AmazonScraper import AmazonScraper

# Constantes editables del módulo (Subtarea 6.1.5).
PRODUCT_ID = "B09XLK9GVS"
URL_PRODUCTO = "https://www.amazon.com/BellaVita-Luxury-Womens-Cologne-Set/dp/B09XLK9GVS/?_encoding=UTF8&pd_rd_w=29OPu&content-id=amzn1.sym.aa180eba-14de-4cee-a59e-364a439570fb&pf_rd_p=aa180eba-14de-4cee-a59e-364a439570fb&pf_rd_r=AJD52JA4QBA1H07N78K3&pd_rd_wg=JSUMx&pd_rd_r=37e78470-1879-4649-8e63-a71f31a6c726&ref_=pd_hp_d_r_btf_sspa_dk_gateway&ie=UTF8&psc=1&sp_csd=d2lkZ2V0TmFtZT1zcF9ob21lcGFnZQ=="


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
