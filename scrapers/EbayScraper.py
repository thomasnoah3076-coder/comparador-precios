import html

from bs4 import BeautifulSoup
import playwright
from playwright.sync_api import sync_playwright
from scrapers.BaseScraper import BaseScraper
import re

class EbayScraper(BaseScraper):
    def extraer_datos(self, url):
        html = self.extraer_html(url)
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

    def extraer_titulo(self, soup):
        titulo_tag = soup.select_one("h1.x-item-title__mainTitle")
        if titulo_tag:
            return titulo_tag.get_text(strip=True)
        else:
            print("Advertencia: no se encontró el título del producto.")
            return None

    def extraer_precio(self, soup):
        precio_tag = soup.select_one("span.x-price-primary__price")
        if precio_tag:
            precio = precio_tag.get_text(strip=True)
            # Escapamos el $ usando \$ para que lo detecte literalmente
            patron_de_formateo = r"U|S|\$| |c|a|d|n|u"
            
            precio_formateado = re.sub(patron_de_formateo, "", precio)
            return float(precio_formateado)

    def extraer_moneda(self, soup):
        moneda_tag = soup.select_one("span.x-price-primary__price")
        if moneda_tag:
            moneda = moneda_tag.get_text(strip=True)
            if "US" in moneda:
                return "USD"
            if "COP" in moneda:
                return "COP"
        else:
            print("Advertencia: no se encontró la moneda del producto.")
            return None

    def extraer_vendedor(self, soup):
        vendedor_tag = soup.select_one("div.x-sellercard-atf__about-seller-item.x-sellercard-atf__about-seller-item--seller-name")
        if vendedor_tag:
            return vendedor_tag.get_text(strip=True)
        else:
            print("Advertencia: no se encontró el nombre del vendedor.")
            return None

    def extraer_ventas_y_rating(self, soup):
        ventas_rating_tag = soup.select_one("p.x-store-information__highlights")
        if ventas_rating_tag:
            texto = ventas_rating_tag.get_text(strip=True)
            rating = texto[:texto.find("•")]
            ventas = texto[texto.find("•") + 1:]
            return ventas.strip(), rating.strip()
        else:
            print("Advertencia: no se encontró la cantidad de ventas.")
            return None, None

if __name__ == "__main__":
    url = "https://www.ebay.com/itm/137503131228?_skw=9pm+elixir+afnan&itmmeta=01M1ZBH155MJ06K6RN3G9ET8Y8&hash=item2003d3465c:g:OSIAAeSwDDdqUXqi&itmprp=enc%3AAQALAAAA8GfYFPkwiKCW4ZNSs2u11xB5ISQ7l9M2zmDkQLB4ExCDxQSrmY5h4%2FmcMT1lDdu8b7ArWf5doLLiJxSkknqHRxrQK8dWiL7nyKtTeDQ7xPuLQGPm7yuyoDr3uMvp0HScueocPNHwGZ3JZqY7tNI9eRMmx0RooT9OgqQrcdH1hU%2Fh%2B%2F09BCKstv5tavp5Vi51I6Ws2MR4O9oijXWaQV7Za0MDuBk5kCq%2Fpg5Wf6zcemzTfZ5eNW%2FpoXfKJOOJuBEqOBVrgxKa4rwGTDJgYaFgHrg1%2FLDfhtjY8KsztRrpfDtLkLmG1CgzHH4wqtEBF5KU%2FQ%3D%3D%7Ctkp%3ABk9SR8yTxOuPaA"
    scraper = EbayScraper()
    print (scraper.extraer_datos(url))