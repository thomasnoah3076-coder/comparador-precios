
from abc import ABC, abstractmethod
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from database.schema import ya_se_consulto_hoy, obtener_ultimo_registro

# Constructor de la clase
class ScraperBase(ABC):
    def __init__(self, conn):
        self.conn = conn

    async def obtener_datos(self, product_id: str, url: str) -> dict:
        if ya_se_consulto_hoy(self.conn, product_id):
            registro = obtener_ultimo_registro(self.conn, product_id)
            registro["origen"] = "base_de_datos"
            return registro

        dom_html = await self._obtener_dom(url)
        datos = self.extraer_datos(dom_html)
        datos["origen"] = "scraping"
        return datos

    async def _obtener_dom(self, url: str) -> str:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={"width": 1366, "height": 768},
                locale="es-CO",
            )
            page = await context.new_page()

            stealth = Stealth()
            await stealth.apply_stealth_async(page)

            await page.goto(url, timeout=30000, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)

            html = await page.content()
            await browser.close()
            return html

    @abstractmethod
    def extraer_datos(self, dom_html: str) -> dict:
        raise NotImplementedError