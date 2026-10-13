
from abc import ABC, abstractmethod
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from database.schema import ya_se_consulto_hoy, obtener_ultimo_registro
from urllib.parse import urlparse
class BaseScraper(ABC):

    ZIP_MIAMI = "33122"
    URL_HOME = "https://www.amazon.com/"
    COOKIES_USD = [
        {"name": "i18n-prefs", "value": "USD", "domain": ".amazon.com", "path": "/"},
    ]


    def __init__(self, conn):
        self.conn = conn


    async def obtener_datos(self, product_id: str, url: str) -> dict:
        if ya_se_consulto_hoy(self.conn, product_id):
            registro = obtener_ultimo_registro(self.conn, product_id)
            registro["origen"] = "base_de_datos"
            return registro
        datos = await self.extraer_datos(url)
        datos["origen"] = "scraping"
        return datos


    async def obtener_dom(self, url: str) -> str:
        await self.verficar_url_valido(url)
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                context = await browser.new_context(
                    viewport={"width": 1366, "height": 768},
                    locale="en-US",
                )
                await context.add_cookies(self.COOKIES_USD)

                page = await context.new_page()

                stealth = Stealth()
                await stealth.apply_stealth_async(page)

                await self._fijar_ubicacion_miami(page)

                response = await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                await page.wait_for_timeout(2000)

                html = await page.content()
                await self.verificacion_de_estado_html(html, response)
                return html
            finally:
                await browser.close()

    async def _fijar_ubicacion_miami(self, page) -> None:
        """
        Fija la ubicación de entrega en Miami mediante el widget
        "Enviar a" de la cabecera. Best-effort: si el widget cambia o falla, se
        imprime un aviso y se continúa con la ubicación por defecto.
        """
        try:
            # Navega a la página principal de Amazon.

            await page.goto(self.URL_HOME, timeout=30000, wait_until="domcontentloaded")

            # Simula el tiempo humano.
            await page.wait_for_timeout(1500)

            # Hace clic en el botón superior izquierdo "Enviar a".
            await page.click("#nav-global-location-popover-link", timeout=8000)

            # Detiene el flujo del código hasta verificar que la ventana emergente y
            # el campo de texto del código postal existan físicamente en el DOM.
            await page.wait_for_selector("#GLUXZipUpdateInput", timeout=8000)

            # Escribe el código postal correspondiente a Miami en el campo.
            await page.fill("#GLUXZipUpdateInput", self.ZIP_MIAMI)

            # Breve pausa para asegurar que los eventos de teclado de React/JavaScript de Amazon lo registren.
            await page.wait_for_timeout(400)

            # Presiona el botón "Aplicar".
            # Utiliza múltiples selectores separados por coma como estrategia de respaldo por si el diseño web varía.
            await page.click(
                "#GLUXZipUpdate input[type='submit'], #GLUXZipUpdate span.a-button-input",
                timeout=4000,
            )

            # Otorga tiempo para que la petición asíncrona de Amazon
            # viaje a sus servidores y devuelva la nueva sesión con la ubicación actualizada.
            await page.wait_for_timeout(2500)

            # Amazon a veces muestra un botón de "Continuar"
            # y otras veces cierra el cuadro de diálogo de inmediato.
            try:
                # Localiza el botón de confirmación sin lanzar un error automático si no existe.
                confirm = page.locator("#GLUXConfirmClose")

                # Verifica si el botón existe en el código (count > 0) y si el
                # usuario realmente puede verlo en la pantalla (is_visible).
                if await confirm.count() > 0 and await confirm.first.is_visible():
                    await confirm.first.click(timeout=3000)
            except Exception:
                # Si el botón no existe o hubo un error al clickearlo, absorbe el error silenciosamente
                # ya que es un paso opcional.
                pass

            await page.wait_for_timeout(500)

        except Exception as e:
            # Si todo el bloque colapsa (por un CAPTCHA, lentitud de red o cambio crítico de diseño web),
            # se intercepta la excepción para evitar que el programa principal se caiga.
            print(
                f"Aviso: no se pudo fijar la ubicación Miami ({type(e).__name__}: {e}). "
                "Se continúa con la ubicación por defecto."
            )


    @staticmethod
    async def verificacion_de_estado_html(dom_html: str, response) -> bool:
        error_indicators = ['Robot Check', 'Captcha', 'form action="/errors/validateCaptcha"',
                            'Amazon.com Something Went Wrong']
        if response.status != 200:
            raise Exception(f"Error HTTP {response.status} al acceder a la página.")
        if dom_html is None or any(indicator in dom_html for indicator in error_indicators):
            raise Exception("Error: HTML contiene indicadores de bloqueo o está vacío.")
        return True

    @staticmethod
    async def validar_url_amazon(url) -> bool:
        # Troceando la URL usando urlparse
        parsed_url = urlparse(url)
        # Validando que tenga un protocolo seguro (https)
        if parsed_url.scheme != 'https':
            return False
        # Obtener el host (ej: "://amazon.com", "amazon.co.uk", "smile.amazon.es")
        host = parsed_url.hostname
        if not host:
            return False
        # Convertir a minúsculas para evitar evasiones de mayúsculas
        host = host.lower()
        # Validar que termine exactamente en un dominio oficial de Amazon
        dominios_validos = ('.amazon.com', '.amazon.es', '.amazon.co.uk', '.amazon.ca', '.amazon.com.mx')
        # También contemplamos si entran directamente a "amazon.com" sin subdominio
        if host.endswith(dominios_validos):
            return True
        return False

    async def verficar_url_valido(self, url: str):
        # Orden importa: primero el tipo (si no, url.strip() lanza AttributeError).
        if not isinstance(url, str):
            raise TypeError("El argumento debe ser un string.")
        if not url.strip():
            raise ValueError("No se proporcionó una URL sino un argumento vacio.")
        if not await self.validar_url_amazon(url):
            raise ValueError("La URL no es una URL de Amazon.")


    @abstractmethod
    def extraer_datos(self, url: str) -> dict:
        raise NotImplementedError
