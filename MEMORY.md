# 🧠 Memoria del Proyecto (Project Memory)

**Última actualización:** (Octubre 2026)
**Estado Global:** Fase de Desarrollo Inicial / Refactorización de Arquitectura de Scraping.

## 1. Visión General del Proyecto
Sistema programado en Python para comparar precios de productos en línea, registrar el historial en una base de datos local (SQLite), evaluar si el precio es una buena oferta, convertir divisas y enviar notificaciones vía Telegram.

## 2. Trayectoria y Decisiones Arquitectónicas (Historial)
* **Pivote de Plataformas (Mercado Libre -> eBay -> Amazon):** 
  * *Contexto:* Inicialmente se intentó scrapear Mercado Libre (usando requests/BS4 y luego APIs), pero se encontraron bloqueos 403 y contenido dinámico complejo. 
  * *Decisión:* Se decidió simplificar el alcance a **una sola tienda inicial** para validar todo el flujo de trabajo (End-to-End). Actualmente, el foco principal de desarrollo es **Amazon**.
* **Patrón de Diseño "Template Method" (Separación de Responsabilidades):**
  * *Problema:* Mezclar lógica de base de datos, control de navegador y selectores de tiendas en un solo archivo hace que el código sea frágil e inescalable.
  * *Solución:* 
    * **`BaseScraper` (Orquestador):** Se encarga exclusivamente de la infraestructura. Conecta con la BD, verifica si ya se consultó hoy, levanta `Playwright`, maneja las esperas y detecta bloqueos de seguridad (CAPTCHAs).
    * **`AmazonScraper` (Especialista):** No sabe nada de bases de datos ni de navegadores. Solo recibe un DOM (HTML) validado, aplica selectores CSS, limpia los datos (ej. quitar el símbolo "$" del precio) y retorna un diccionario estandarizado.
* **Manejo de Anti-Scraping (Amazon):**
  * *Decisión:* Antes de extraer cualquier dato, el `BaseScraper` debe validar el estado HTTP y buscar huellas de bloqueo en el DOM (ej. `<form action="/errors/validateCaptcha">` o `<title>Robot Check</title>`). Si hay bloqueo, se aborta la ejecución para no guardar datos nulos ni quemar el proxy/IP local.

## 3. Estado Actual del Código
* **Completado:**
  * Entorno virtual (`.venv`) configurado correctamente con **Python 3.14.8 (gestionado con pyenv)**. `pytest` 9.1.1 instalado y declarado en `requirements.txt`.
  * Base de datos (`tracker.db`) y esquema inicial definidos en SQLite.
  * Carga de variables de entorno (`.env`, `config/settings.py`).
  * Servicio de conversión de divisas (`services/currency.py`) con caché en JSON.
  * Estructura base del `BaseScraper` (flujo de consulta a BD -> extracción de DOM).
  * `AmazonScraper` corregido: método `extraer_datos` asíncrono, contrato de datos alineado (`titulo`), lógica de extracción de ventas mejorada.
  * Dependencias actualizadas: requests 2.34.2, beautifulsoup4 4.15.0, playwright 1.63.0, playwright-stealth 2.0.3, python-dotenv 1.2.4, python-telegram-bot 22.8.
  * Playwright Chromium instalado correctamente.
  * **Validación de URL corregida (`BaseScraper.verficar_url_valido`):** se reordenó el chequeo (`isinstance` antes de `strip`, para no lanzar `AttributeError` con `None`/enteros) y se **negó** la condición del dominio (antes lanzaba error con URLs de Amazon válidas y dejaba pasar las ajenas).
  * **`extraer_precio` corregido:** limpia el texto con `.get_text(strip=True).replace(',', '')` sobre el **string**, no sobre el Tag (en bs4 4.15 `Tag.replace` resuelve a `None` → `TypeError`). Ahora tolera la ausencia de `price-fraction` (asume `.00`).
  * **`extraer_calificacion_promedio` corregido:** usa regex `re.match(r'\d+(?:[.,]\d+)?')` para tomar el primer grupo numérico completo (`"4.7 de 5"` → `4.7`) en vez de truncar con `[:2]`; devuelve `None` (no `0`) cuando no hay rating, por coherencia con el contrato.
  * **`main.py` implementado:** punto de entrada que respeta el Template Method (solo habla con el orquestador `obtener_datos`, nunca con `extraer_datos`). Constantes `PRODUCT_ID`/`URL_PRODUCTO` editables al inicio. Ejecutado contra Amazon real con éxito (título, `precio: 42.7`, `moneda: USD`, ventas, rating 4.7, `origen: scraping`).
  * **Rutas/paquetes normalizados:** `config/___init__.py` y `database/___init__.py` renombrados a `__init__.py` (se unen a `scrapers/` y `services/`). La cadena `main -> AmazonScraper -> BaseScraper -> database.schema -> config.settings` importa sin errores.
  * Batería de 33 pruebas (temporal, ya eliminada) en verde sobre `extraer_datos` con el `.venv` nuevo.
  * **Selector de precio, moneda USD y ubicación Miami (sesión Oct 2026):**
    * *Selector (simplificado, solo Miami):* el precio vive en el **buybox**. `AmazonScraper._tag_precio_principal` es ahora un bucle corto sobre **3 contenedores EXCLUSIVOS del precio principal**: `#corePrice_feature_div`, `#corePrice_desktop_div`, `#apex_desktop`. Se **eliminaron** `_es_precio_de_comparacion` y el set `_CONTENEDORES_COMPARACION`: eran redundantes porque los carruseles de comparación (sims/aplus/carousel) nunca están anidados dentro de esos contenedores, y los selectores genéricos que causaban la contaminación (`span.a-price[data-a-size='medium_plus']`, `.a-price[data-a-color='price']`) se descartaron. Solo se conserva el chequeo de 1 línea `.a-price-whole` (filtra placeholders/tachados).
    * *Moneda (simplificada a solo USD):* como solo se scrapeará Miami, la moneda es **siempre USD**. Se quitó la lógica de detectar COP; ahora se valida el símbolo `$` del tag del buybox. (Contexto: el `locale` NO fija la moneda — Amazon decide por IP; `BaseScraper` usa `locale="en-US"` + cookie `i18n-prefs=USD`.)
    * *Ubicación por defecto = Miami (ZIP 33101), vía WIDGET y NO cookie:* `BaseScraper._fijar_ubicacion_miami` navega a la home, abre `#nav-global-location-popover-link`, rellena `#GLUXZipUpdateInput` con `33101`, envía y cierra el diálogo `#GLUXConfirmClose`; luego se navega al producto (1 sola carga). **La cookie `sp-cdn` NO sirve: Amazon la borra por IP** (`L549:US-33101` → `L5Z9:CO`). Con Miami aparece `#corePrice_feature_div` con el precio buybox real; sin Miami este perfume no envía a Colombia y no hay precio principal (solo *"15 opciones desde US$42.00"*). Es *best-effort*: si el widget falla, se imprime aviso y se continúa.
    * Verificado end-to-end (`main.py`: `precio: 42.7`, `moneda: USD`) y con batería aislada de 14 pruebas (HTML simulado, sin red/BD) en verde y borrada.
    * *Verificación tras la simplificación:* batería aislada de 4 pruebas (HTML simulado del DOM de Miami, con y sin carrusel de comparación presente) en verde: el buybox (42.70) gana al carrusel (30.37) sin filtro, no hay caída al carrusel si falla el widget, fallback a `#apex_desktop` y precio entero → `.00`. Temporales borradas.
  * **`extraer_vendedor` pulido (ambos idiomas):** limpiaba solo el prefijo español `"Visita la tienda de "`, por lo que en la tienda US (Miami) devolvía *"Visit the Afnan Store"*. Ahora limpia también el inglés (`"Visit the "` + `removesuffix(" Store")`) y devuelve **"Afnan"** en ES y EN. Batería aislada de 3 pruebas (HTML simulado, sin red/BD) en verde y borrada.
  * **`.env` recreado (vacío) tras migrar de Windows a Linux:** se perdió el original. Se listaron las **7 variables** que consume `config/settings.py` y se creó `.env` con ellas vacías y comentadas: `TELEGRAM_BOT_TOKEN`, `EXCHANGE_RATE_API_KEY`, `TELEGRAM_CHAT_ID_GENERAL`, `TELEGRAM_CHAT_ID_PERFUMES`, `TELEGRAM_CHAT_ID_TECNOLOGIA`, `LOCAL_CURRENCY`, `EXCHANGE_RATE_API_URL`. Ignorado por git (`.gitignore:153`). Pendiente que el Director rellene los valores.
  * **`extraer_calificacion_promedio` probado y selector robustificado (3ª ronda):** `py_compile` OK; batería aislada de **13 pruebas** (HTML simulado, `conn` mockeado, sin red/BD) en verde (decimales punto/coma, enteros, inglés, `0 de 5`→`0.0`, ausente/no numérico→`None`, negativos→`None`, inválidos→`AttributeError`). El método devuelve `None` (no `0`) sin rating: contrato correcto. **Bug real detectado por el Director:** el selector original `span.a-size-small.a-color-base` **no existía en algunos productos** y el rating fallaba al cambiar de producto. Se verificó contra el DOM real (Playwright, 3 productos) y se reemplazó por el **`data-hook` oficial de Amazon `span[data-hook="rating-out-of-text"]`** (texto `"4.7 out of 5"`): 1 coincidencia siempre, funcionó incluso en el producto que rompía al selector viejo, y la regex existente lo parsea sin cambiar. Re-test aislado de 7 pruebas (ES/EN, escenario que fallaba, regresión que ignora el span genérico ruidoso) en verde. Sin añadir complejidad (swap de un selector). Temporales, `__pycache__` y `.pytest_cache` borrados. Detalles en `AGENTS.md` §6.3 (3ª ronda).
* **En Progreso:**
  * Integración de `AmazonScraper` con `BaseScraper` para flujo completo end-to-end.
  * Implementación de detección de bloqueos (CAPTCHAs) en `BaseScraper`.

## 4. Contrato de Datos (Data Contract)
Cualquier scraper específico (ej. `AmazonScraper`) DEBE retornar al `BaseScraper` un diccionario con la siguiente estructura estandarizada:
* `titulo` (str): Nombre del producto.
* `precio` (float): Precio numérico limpio (sin símbolos ni comas).
* `moneda` (str): Moneda original (ej. "USD", "COP").
* `url` (str): Enlace directo al producto.
* `vendedor` (str): Nombre del vendedor.
* `ventas` (int): Cantidad de productos vendidos.
* `calificacion_promedio` (float): Promedios de calificaciones de los compradores.

## 5. Próximos Pasos (Roadmap Inmediato)
Los agentes deben ejecutar estas tareas en orden, proponiendo y esperando aprobación para cada una:

1. **Implementar Detección de Bloqueos en `BaseScraper`:** Añadir la lógica que verifique si el DOM devuelto por Playwright es un CAPTCHA de Amazon antes de intentar extraer datos.
2. **Crear `AmazonScraper` (El Especialista):** Desarrollar la clase que reciba el DOM limpio, aplique los selectores para extraer título, precio, etc., y devuelva el formato establecido en el Contrato de Datos.
3. **Conectar Retorno con SQLite:** Asegurar que el `BaseScraper` tome los datos extraídos y haga el `INSERT` o `UPDATE` correspondiente en la base de datos para guardar el historial.
4. **Desarrollar Analizador de Ofertas:** Crear el script que compare el precio actual guardado en la BD con el historial para detectar caídas de precio.
5. **Integrar Notificaciones:** Conectar los resultados del analizador con el bot de Telegram.