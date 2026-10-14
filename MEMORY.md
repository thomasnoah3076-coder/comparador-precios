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
    * *Ubicación por defecto = Miami (ZIP 33122), vía WIDGET y NO cookie:* `BaseScraper._fijar_ubicacion_miami` navega a la home, abre `#nav-global-location-popover-link`, rellena `#GLUXZipUpdateInput` con `33122`, envía y cierra el diálogo `#GLUXConfirmClose`; luego se navega al producto (1 sola carga). **La cookie `sp-cdn` NO sirve: Amazon la borra por IP** (el `sp-cdn` geolocaliza por IP, no sirve para forzar Miami). Con Miami aparece `#corePrice_feature_div` con el precio buybox real; sin Miami este perfume no envía a Colombia y no hay precio principal (solo *"15 opciones desde US$42.00"*). Es *best-effort*: si el widget falla, se imprime aviso y se continúa.
    * Verificado end-to-end (`main.py`: `precio: 42.7`, `moneda: USD`) y con batería aislada de 14 pruebas (HTML simulado, sin red/BD) en verde y borrada.
    * *Verificación tras la simplificación:* batería aislada de 4 pruebas (HTML simulado del DOM de Miami, con y sin carrusel de comparación presente) en verde: el buybox (42.70) gana al carrusel (30.37) sin filtro, no hay caída al carrusel si falla el widget, fallback a `#apex_desktop` y precio entero → `.00`. Temporales borradas.
  * **`extraer_vendedor` pulido (ambos idiomas):** limpiaba solo el prefijo español `"Visita la tienda de "`, por lo que en la tienda US (Miami) devolvía *"Visit the Afnan Store"*. Ahora limpia también el inglés (`"Visit the "` + `removesuffix(" Store")`) y devuelve **"Afnan"** en ES y EN. Batería aislada de 3 pruebas (HTML simulado, sin red/BD) en verde y borrada.
  * **`.env` recreado (vacío) tras migrar de Windows a Linux:** se perdió el original. Se listaron las **7 variables** que consume `config/settings.py` y se creó `.env` con ellas vacías y comentadas: `TELEGRAM_BOT_TOKEN`, `EXCHANGE_RATE_API_KEY`, `TELEGRAM_CHAT_ID_GENERAL`, `TELEGRAM_CHAT_ID_PERFUMES`, `TELEGRAM_CHAT_ID_TECNOLOGIA`, `LOCAL_CURRENCY`, `EXCHANGE_RATE_API_URL`. Ignorado por git (`.gitignore:153`). Pendiente que el Director rellene los valores.
  * **`extraer_calificacion_promedio` probado y selector robustificado (3ª ronda):** `py_compile` OK; batería aislada de **13 pruebas** (HTML simulado, `conn` mockeado, sin red/BD) en verde (decimales punto/coma, enteros, inglés, `0 de 5`→`0.0`, ausente/no numérico→`None`, negativos→`None`, inválidos→`AttributeError`). El método devuelve `None` (no `0`) sin rating: contrato correcto. **Bug real detectado por el Director:** el selector original `span.a-size-small.a-color-base` **no existía en algunos productos** y el rating fallaba al cambiar de producto. Se verificó contra el DOM real (Playwright, 3 productos) y se reemplazó por el **`data-hook` oficial de Amazon `span[data-hook="rating-out-of-text"]`** (texto `"4.7 out of 5"`): 1 coincidencia siempre, funcionó incluso en el producto que rompía al selector viejo, y la regex existente lo parsea sin cambiar. Re-test aislado de 7 pruebas (ES/EN, escenario que fallaba, regresión que ignora el span genérico ruidoso) en verde. Sin añadir complejidad (swap de un selector). Temporales, `__pycache__` y `.pytest_cache` borrados. Detalles en `AGENTS.md` §6.3 (3ª ronda).
  * **Auditoría código vs documentación + correcciones (4ª ronda, Oct 2026):** revisión archivo por archivo (`README.md`, `AGENTS.md`, `MEMORY.md`, `docs/constitution.md` y todo el código) con aprobación del Director. **Bugs corregidos** (batería aislada de **13 pruebas** en verde y borrada): (1) `ya_se_consulto_hoy` comparaba el `TIMESTAMP` completo (`'2026-10-14 12:15:20'`) con `date.today().isoformat()` → **nunca devolvía `True`**; ahora usa `.startswith(hoy)`. (2) `obtener_ultimo_registro` devolvía `nombre`/`rating` en vez de `titulo`/`calificacion_promedio` → los dos caminos de `obtener_datos()` devolvían claves distintas; alineado al Contrato (§4). (3) `currency_converter` no hacía `return` (devolvía `None`); añadidos los `return` de todas las ramas. (4) `extraer_datos` abstracto era sync con hija async → ahora `async def`. (5) Eliminado `scrapers/retorno.txt` (residual con claves viejas). **Descubrimiento nuevo:** `python database/schema.py` no funciona (`ModuleNotFoundError`, hay que usar `python -m database.schema`) y `init_sqlite_db()` no es idempotente (`CREATE TABLE` sin `IF NOT EXISTS` → `OperationalError` si ya existe) — documentado como pendiente en README. **Documentación actualizada:** README (falsos sobre EbayScraper/main.py vacío/stealth/pytest/síncrono/headful/umbral 0.3/Windows/comandos; roadmap y fases 6-8; pendientes resueltos), AGENTS (§1/§5/§6.3 con contrato en español y nueva "4ª ronda"), MEMORY (ZIP **33122** — el código es el correcto, no 33101), `probar-metodo.md` (pytest vía `.venv/bin/python -m pytest`).
* **En Progreso:**
  * Integración completa del flujo: conectar scraping → conversión → persistencia (el scraping end-to-end con `main.py` ya funciona).

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

1. ~~**Implementar Detección de Bloqueos en `BaseScraper`**~~ — **COMPLETADO** (`verificacion_de_estado_html` detecta CAPTCHA/HTTP ≠ 200 antes de extraer).
2. ~~**Crear `AmazonScraper` (El Especialista)**~~ — **COMPLETADO** (devuelve el Contrato de Datos de la §4; verificado end-to-end).
3. **Conectar Retorno con SQLite:** Asegurar que el `BaseScraper` tome los datos extraídos y haga el `INSERT` o `UPDATE` correspondiente en la base de datos para guardar el historial. *(Siguiente pendiente inmediato: sin esto, `ya_se_consulto_hoy` no tiene filas que cachear y `obtener_ultimo_registro` siempre devuelve `None`.)*
4. **Desarrollar Analizador de Ofertas:** Crear el script que compare el precio actual guardado en la BD con el historial para detectar caídas de precio (umbral `PRICE_DROP_THRESHOLD = 0.15`).
5. **Integrar Notificaciones:** Conectar los resultados del analizador con el bot de Telegram.

*Pendiente técnico conocido (detectado en la auditoría de Oct 2026): `init_sqlite_db()` necesita `CREATE TABLE IF NOT EXISTS` para ser idempotente (regla CONSTITUTION §3). **Todavía sin corregir** — requiere aprobación del Director. Ver "Pendientes de documentar" en README.*