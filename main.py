
import asyncio
import sqlite3

from config.settings import DB_PATH_TRACKER
from scrapers.AmazonScraper import AmazonScraper

PRODUCT_ID = "B09XLK9GVS"
URL_PRODUCTO = "https://www.amazon.com/BellaVita-Luxury-Womens-Cologne-Set/dp/B09XLK9GVS/?_encoding=UTF8&pd_rd_w=29OPu&content-id=amzn1.sym.aa180eba-14de-4cee-a59e-364a439570fb&pf_rd_p=aa180eba-14de-4cee-a59e-364a439570fb&pf_rd_r=AJD52JA4QBA1H07N78K3&pd_rd_wg=JSUMx&pd_rd_r=37e78470-1879-4649-8e63-a71f31a6c726&ref_=pd_hp_d_r_btf_sspa_dk_gateway&ie=UTF8&psc=1&sp_csd=d2lkZ2V0TmFtZT1zcF9ob21lcGFnZQ=="


async def obtener_datos_producto() -> dict:
    conn = sqlite3.connect(DB_PATH_TRACKER)
    try:
        scraper = AmazonScraper(conn)
        return await scraper.obtener_datos(PRODUCT_ID, URL_PRODUCTO)
    finally:
        conn.close()


def main() -> None:
    try:
        datos = asyncio.run(obtener_datos_producto())
    except (ValueError, TypeError) as e:
        print(f"Error de validación de la URL: {e}")
        return
    except Exception as e:
        print(f"Error durante la extracción: {type(e).__name__}: {e}")
        return

    print("\n=== Resultado de la consulta ===")
    for campo, valor in datos.items():
        print(f"{campo}: {valor}")


if __name__ == "__main__":
    main()
