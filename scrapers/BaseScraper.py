from abc import ABC, abstractmethod
from playwright.sync_api import sync_playwright, playwright

class BaseScraper(ABC):
    @abstractmethod
    def extraer_datos(self, url) -> dict:
        pass

    """
    extraer_html: extrae el contenido HTML de la página web especificada por la URL utilizando Playwright.
    Parámetros:
    - url (str): La URL de la página web de la que se desea extraer el contenido HTML.
    Retorna:
    - str: El contenido HTML de la página web.
    Funcionamiento:
    1. Se inicia un contexto de Playwright utilizando sync_playwright() al cual llamamos 'p'.
    2. Se lanza un navegador Chromium en modo no oculto (headless=False).
    3. Se crea una nueva página en el navegador.
    4. Se navega a la URL especificada utilizando page.goto(url).
    5. Se obtiene el contenido HTML de la página utilizando page.content().
    6. Se cierra el navegador.
    7. Se retorna el contenido HTML obtenido.
    """
    
    def extraer_html(self, url):
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=False) # headless=True significa que el navegador se ejecutará en segundo plano sin mostrar la interfaz gráfica.
                page = browser.new_page()
                page.goto(url, timeout=30000) #  Busca la URL y espera hasta que la página se cargue completamente o hasta que se alcance el tiempo de espera máximo (30 segundos).
                page.wait_for_load_state('domcontentloaded', timeout=30000) # Espera hasta que el html basico esté cargado, lo que indica que la página se ha cargado completamente.
                html = page.content()
                browser.close()
                return html
        except playwright._impl._errors.TimeoutError as e:
            print(f"Error de tiempo de espera: {e}. Posiblemente la página no se cargó completamente o el estado nunca deja de solicitar peticiones a internet.")
            return None