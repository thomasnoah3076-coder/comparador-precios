
from bs4 import BeautifulSoup
from scrapers.BaseScraper import BaseScraper
import re

class AmazonScraper(BaseScraper):

    async def extraer_datos(self, url : str) -> dict:
        try:
            html = await self.obtener_dom(url)
            if html is None:
                print("Error: No se pudo obtener el HTML de la página. El sitio puede estar bloqueando las solicitudes.")
                return {
                    "titulo": None,
                    "precio": None,
                    "moneda": None,
                    "url": url,
                    "vendedor": None,
                    "ventas": None,
                    "calificacion_promedio": None,
                }
            soup = BeautifulSoup(html, "html.parser")
            datos = {
                "titulo": self.extraer_titulo(soup),
                "precio": self.extraer_precio(soup),
                "moneda": self.extraer_moneda(soup),
                "url": url,
                "vendedor": self.extraer_vendedor(soup),
                "ventas": self.extraer_ventas(soup),
                "calificacion_promedio": self.extraer_calificacion_promedio(soup),
            }
            return datos
        except TypeError as e:
            print(f"Error:{e}.")
            raise

    def extraer_titulo(self, soup) -> str:
        titulo_tag = soup.select_one("#productTitle")
        if titulo_tag:
            return titulo_tag.get_text(strip=True)
        else:
            print("Advertencia: no se encontró el título del producto.")
            return ""

    def _tag_precio_principal(self, soup):

        # Estos son los contenedores que suelen variar dinamicamente
        # Amazon dependiendo del tipo de usuario que este veinod un
        # producto.
        for selector in (
            "#corePrice_feature_div .a-price",
            "#corePrice_desktop_div .a-price",
            "#apex_desktop .a-price",
        ):
        # Verfica si alguno de estos contenedores esta en el html
        # parseado en la variable soup.
            tag = soup.select_one(selector)
            if tag and tag.select_one(".a-price-whole"):
                # Si adicionalmente a existir alguno de estos selectores
                # estos contiene el selector del precio entero del
                # producto lo retorna corectamente.
                return tag
        return None

    def extraer_precio(self, soup) -> float:
        precio_tag = self._tag_precio_principal(soup)
        if precio_tag is None:
            print("Advertencia: no se encontró el precio del producto.")
            return None

        entero_tag = precio_tag.select_one(".a-price-whole")
        decimal_tag = precio_tag.select_one(".a-price-fraction")
        # Busca cualquier caracter que no(^) sea un numero(\d) o un signo menos y lo elmina.
        parte_entera = re.sub(r"[^\d-]", "", entero_tag.get_text(strip=True))
        # Busca cualquier caracter que no sea un numero(\D) y lo elmina si no hay ningun selector, devuelve la parte decimal como vacio.
        parte_decimal = (re.sub(r"\D", "", decimal_tag.get_text(strip=True)) if decimal_tag else "")

        if not parte_decimal:
            parte_decimal = "00"

        if not parte_entera:
            print("Advertencia: No hay parte entera del precio del producto.")
            return None

        precio = f"{parte_entera}.{parte_decimal}"
        try:
            return float(precio)
        except ValueError as e:
            print(f"Advertencia: no se pudo convertir el precio a número decimal. Texto obtenido: '{precio}'. Error: {e}")
            return None

    def extraer_moneda(self, soup) -> str:
        precio_tag = self._tag_precio_principal(soup)
        if precio_tag is None:
            print("Advertencia: no se encontró moneda (sin precio principal).")
            return ""
        moneda_tag = precio_tag.select_one(".a-price-symbol")
        if moneda_tag and "$" in moneda_tag.get_text(strip=True):
            return "USD"
        print("Advertencia: no se detectó el símbolo '$' de la tienda US en el precio principal.")
        return ""

    def extraer_vendedor(self, soup) -> str:
        vendedor_tag = soup.select_one("#bylineInfo")
        if not vendedor_tag:
            print("Advertencia: no se encontró el nombre del vendedor.")
            return ""

        vendedor = vendedor_tag.get_text(strip=True)

        vendedor = vendedor.replace("Visita la tienda de ", "")
        vendedor = vendedor.replace("Visit the ", "")
        vendedor = vendedor.removesuffix(" Store")

        return vendedor.strip()

    def extraer_calificacion_promedio(self, soup) -> float:
        rating_tag = soup.select_one('span[data-hook="rating-out-of-text"]')
        if rating_tag:
            rating_text = rating_tag.get_text(strip=True)
            # Primer grupo numérico completo ("4.7 out of 5" -> 4.7), sin truncar.
            match = re.match(r'\d+(?:[.,]\d+)?', rating_text)
            if match:
                return float(match.group(0).replace(',', '.'))
            print(f"Advertencia: no se pudo interpretar el rating '{rating_text}'.")
            return None
        print("Advertencia: no se encontró el rating del articulo.")
        return None
        
    def extraer_ventas(self, soup) -> int:
        ventas_tag = soup.select_one("#acrCustomerReviewText")
        if ventas_tag:
            ventas_text = ventas_tag.get_text(strip=True)
            match = re.search(r'([\d,]+)', ventas_text.replace(',', ''))
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    print(f"Advertencia: no se pudo convertir ventas a número. Texto: '{ventas_text}'")
                    return None
        print("Advertencia: no se encontró el número de ventas del articulo.")
        return None
