
from bs4 import BeautifulSoup
from scrapers import BaseScraper

class AmazonScraper(BaseScraper):

    def extraer_datos(self, url : str) -> dict:
        html = self.obtener_dom(url)
        if html is None:
            print("Error: No se pudo obtener el HTML de la página. El sitio puede estar bloqueando las solicitudes.")
            return {
                "nombre": None,
                "precio": None,
                "moneda": None,
                "url": url,
                "vendedor": None,
                "ventas": None,
                "rating": None,
            }
        soup = BeautifulSoup(html, "html.parser")
        datos = {
            "nombre": self.extraer_titulo(soup),
            "precio": self.extraer_precio(soup),
            "moneda": self.extraer_moneda(soup),
            "url": url,
            "vendedor": self.extraer_vendedor(soup),
            "ventas": self.extraer_ventas_y_rating(soup)[0],
            "rating": self.extraer_ventas_y_rating(soup)[1],
        }
        return datos
    

    def extraer_titulo(self, soup) -> str:
        titulo_tag = soup.select_one("span.a-size-large.product-title-word-break")
        if titulo_tag:
            return titulo_tag.get_text(strip=True)
        else:
            print("Advertencia: no se encontró el título del producto.")
            return ""

    def extraer_precio(self, soup) -> float:
        precio_tag_entero = soup.select_one("a.price-whole")
        precio_tag_decimal = soup.select_one("a.price-fraction")

        if precio_tag_entero and precio_tag_decimal:
            precio = f"{precio_tag_entero.get_text(strip=True)}.{precio_tag_decimal.get_text(strip=True)}"
            try:
                return float(precio)
            except ValueError as e:
                print(f"Advertencia: no se pudo convertir el precio a número. Texto obtenido: '{precio}'. Error: {e}")
                return None
        else:
            print("Advertencia: no se encontró el precio del producto.")
            return 0

    def extraer_moneda(self, soup) -> str:
        moneda_tag = soup.select_one("span.aria-hidden")
        if moneda_tag:
            moneda = moneda_tag.get_text(strip=True)
            formato_dolares = ['US', '$', 'USD']
            formato_cop = ['COP', 'pesos colombianos', 'peso colombiano']
            if any(formato_dolares) in moneda:
                return "USD"
            if any(formato_cop) in moneda.lower():
                return "COP"
            print(f"Advertencia: moneda no reconocida en el texto '{moneda}'.")
            return ""

    def extraer_vendedor(self, soup) -> str:
        vendedor_tag = soup.select_one("div.a-section.a-spacing-none")
        if vendedor_tag:
            return vendedor_tag.get_text(strip=True)
        print("Advertencia: no se encontró el nombre del vendedor.")
        return ""

    def extraer_rating(self, soup) -> float:
        rating_tag = soup.select_one("span.a-size-small.a-color-base")
        if rating_tag:
            rating_text = rating_tag.get_text(strip=True)
            rating_float = float(rating_text.strip())
            return rating_float
        else:
            print("Advertencia: no se encontró el rating del articulo.")
            return 0
        
    def extraer_ventas(self, soup) -> float:
        ventas_tag = soup.select_one("a")
        if ventas_tag:
            rating_text = ventas_tag.get_text(strip=True)
            rating_float = float(rating_text.strip())
            return rating_float
        else:
            print("Advertencia: no se encontró el rating del articulo.")
            return 0

if __name__ == "__main__":
    url = ""
    scraper = AmazonScraper()
    print (scraper.extraer_datos(url))