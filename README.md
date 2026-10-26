# comparador-precios

Sistema en Python para el seguimiento y comparación de precios de productos en marketplaces en línea, con persistencia de historial en SQLite y (planificado) notificaciones automáticas por Telegram cuando un producto alcanza un precio considerado buena oferta.

Repositorio: [`thomasnoah3076-coder/comparador-precios`](https://github.com/thomasnoah3076-coder/comparador-precios)

---

## Tabla de contenidos

- [Problema que resuelve y público objetivo](#problema-que-resuelve-y-público-objetivo)
- [Características principales](#características-principales)
- [Estado actual y nivel de madurez](#estado-actual-y-nivel-de-madurez)
- [Stack tecnológico](#stack-tecnológico)
- [Arquitectura del sistema](#arquitectura-del-sistema)
- [Estructura de directorios](#estructura-de-directorios)
- [Requisitos previos](#requisitos-previos)
- [Instalación paso a paso](#instalación-paso-a-paso)
- [Configuración](#configuración)
- [Uso básico y ejemplos](#uso-básico-y-ejemplos)
- [Scripts disponibles](#scripts-disponibles)
- [Pruebas, calidad de código y cobertura](#pruebas-calidad-de-código-y-cobertura)
- [Despliegue y entornos](#despliegue-y-entornos)
- [Seguridad, privacidad y manejo de datos](#seguridad-privacidad-y-manejo-de-datos)
- [Solución de problemas frecuentes](#solución-de-problemas-frecuentes)
- [Guía de contribución](#guía-de-contribución)
- [Convenciones de desarrollo](#convenciones-de-desarrollo)
- [Roadmap](#roadmap)
- [Fases de desarrollo](#fases-de-desarrollo)
- [Decisiones técnicas y evolución del proyecto](#decisiones-técnicas-y-evolución-del-proyecto)
- [Licencia y créditos](#licencia-y-créditos)
- [Pendientes de documentar](#pendientes-de-documentar)
- [Resumen de cambios propuestos](#resumen-de-cambios-propuestos)

---

## Problema que resuelve y público objetivo

El proyecto automatiza una tarea que de otro modo sería manual y repetitiva: revisar periódicamente el precio de productos específicos en marketplaces en línea, guardar ese precio en un historial y —cuando el flujo esté completo— avisar por Telegram si el precio actual representa una caída significativa respecto al histórico.

Es un **proyecto personal de un solo desarrollador**, sin intención declarada de escalar a múltiples usuarios ni a un volumen alto de productos. El público objetivo es el propio autor, como herramienta de ahorro y aprendizaje técnico (scraping, bases de datos, consumo de APIs, automatización).

## Características principales

**Implementado y verificado en el código actual del repositorio:**

- Esquema de base de datos SQLite con tres tablas: `Productos`, `Historial_Precios`, `Metricas_Vendedor` (`database/schema.py`).
- Conversión de montos entre COP y USD con caché diario de tasas en un objeto único (`services/currency.py::convertir_moneda`, `database/tasas_cambio.json`): si el registro del JSON es de hoy se usa sin red; si no, se consulta la API (con `timeout`) y se sobreescribe el archivo.
- Contrato común de scraper (`BaseScraper`) con extracción de HTML renderizado vía Playwright **asíncrono** (`scrapers/BaseScraper.py`).
- Implementación concreta de scraper para **Amazon** (`scrapers/AmazonScraper.py`) que extrae `titulo`, `precio`, `moneda`, `url`, `vendedor`, `ventas` y `calificacion_promedio`, con detección de bloqueos (CAPTCHAs) y fijación de ubicación de entrega (Miami) en el orquestador.
- Punto de entrada funcional (`main.py`) que consulta un producto de Amazon de extremo a extremo (`asyncio` + `obtener_datos()`), garantiza el esquema con `init_sqlite_db()` y **persiste cada consulta en SQLite**.
- **Persistencia del ciclo completo en SQLite:** `BaseScraper.obtener_datos()` guarda los datos scrapeados vía la fachada transaccional `guardar_datos_producto()` (`INSERT OR IGNORE` en `Productos`, historial append-only en `Historial_Precios`, métricas omitidas si faltan en `Metricas_Vendedor`), con conversión previa a COP si `LOCAL_CURRENCY` está configurada y fallback honesto en USD; caché diaria activa (segunda consulta del mismo día se sirve de la BD sin navegar).
- Función para verificar si un producto ya fue consultado en el día actual, como base para controlar el volumen de peticiones (`database/schema.py::ya_se_consulto_hoy`).
- Carga de variables de entorno sensibles desde `.env`, excluido de control de versiones (`config/settings.py`).
- `playwright-stealth` integrado en el orquestador (`Stealth().apply_stealth_async(page)`).

**Planificado, mencionado en diseño o en documentación de contexto, pero AÚN NO presente en el código del repositorio** (ver [Roadmap](#roadmap)):

- Analizador de ofertas que compare el precio actual contra el historial (`PRICE_DROP_THRESHOLD` aún sin consumir).
- Módulo de notificaciones por Telegram (`python-telegram-bot` está en `requirements.txt` pero no se usa en ningún módulo todavía).
- Rotación de proxies residenciales, delays aleatorios y rotación de User-Agents para scraping en segundo plano sostenido.

## Estado actual y nivel de madurez

**Prototipo en desarrollo activo, no apto para producción ni para ejecución desatendida (segundo plano) todavía.**

Evidencia concreta del estado:

- `main.py` está implementado: punto de entrada que conecta el scraper de Amazon (`asyncio` + `obtener_datos()`), inicializa `init_sqlite_db()` antes de leer/escribir, imprime el resultado y **persiste la consulta en SQLite**. AÚN no conecta analizador de ofertas ni notificaciones.
- El scraper (`AmazonScraper` + `BaseScraper`) se ejecuta con Playwright en modo **headless** (`headless=True`) y con `playwright-stealth`, es decir, apto para segundo plano gráfico; sigue sin tratarse como un proceso desatendido probado a volumen.
- No existen pruebas automatizadas versionadas (las baterías se crean y borran como temporales según `AGENTS.md` §6.4), ni configuración de integración continua.
- No hay módulo de notificaciones ni analizador de ofertas implementados; la persistencia scrape→SQLite **ya está implementada** (esquema con `asin`, fachada transaccional única, caché diaria verificada con baterías aisladas de 25 pruebas).

## Stack tecnológico

| Tecnología | Uso en el proyecto | Justificación |
|---|---|---|
| **Python** | Lenguaje principal de todo el proyecto | Ecosistema maduro para scraping, manejo de datos y APIs |
| **SQLite** (`sqlite3`, stdlib) | Persistencia de productos, historial de precios y métricas de vendedor | Cero configuración, base de datos como archivo único, adecuada para un proyecto de un solo usuario |
| **Playwright** (`playwright.async_api`) | Renderizado de páginas con contenido dinámico (JavaScript) antes de extraer el DOM | `requests` + `BeautifulSoup` resultó insuficiente contra Mercado Libre y eBay por carga dinámica de contenido |
| **BeautifulSoup4** | Parseo del HTML ya renderizado por Playwright, búsqueda por selectores CSS | Estándar de facto en Python para extracción de datos de HTML |
| **requests** | Consumo de la API de tasas de cambio en `services/currency.py` | Cliente HTTP simple para APIs que no requieren renderizado |
| **python-dotenv** | Carga de variables sensibles desde `.env` | Evita hardcodear tokens y claves en el código fuente |
| **python-telegram-bot** | Declarado en `requirements.txt` para el futuro módulo de notificaciones | Aún sin uso en el código; ver [Roadmap](#roadmap) |

> `playwright-stealth` **sí está** en `requirements.txt` y se usa en `scrapers/BaseScraper.py` (`Stealth().apply_stealth_async(page)`) para mitigar la detección de automatización.

## Arquitectura del sistema

El proyecto sigue un patrón **Template Method**: un orquestador común (`BaseScraper`) posee la infraestructura (Playwright, base de datos, control de flujo, detección de bloqueos) y los especialistas de tienda solo extraen datos del DOM. La escritura scrape→SQLite está conectada mediante la fachada transaccional (`guardar_datos_producto`, que convierte a COP antes de la transacción con fallback honesto); aún no existe analizador de ofertas ni notificaciones que consuman ese historial.

```
┌──────────────────────────────┐
│      BaseScraper (ABC)        │  scrapers/BaseScraper.py
│  - obtener_datos(id, url)     │  (consulta BD o delega extracción)
│  - obtener_dom(url)           │  (Playwright async, headless + stealth,
│  - verificacion_de_estado_html│   ubicación Miami, anti-CAPTCHA)
│  - extraer_datos(url)         │  (abstracto, async)
└──────────┬───────────────────┘
           │ hereda
┌──────────▼───────────────────┐
│      AmazonScraper            │  scrapers/AmazonScraper.py
│  extraer_datos(url) async     │  → dict: titulo, precio, moneda,
│                               │    url, vendedor, ventas,
│                               │    calificacion_promedio
└───────────────────────────────┘

┌───────────────────────┐        ┌──────────────────────────┐
│ services/currency.py   │        │  database/schema.py       │
│ convertir_moneda()     │        │  init_sqlite_db()          │
│ obtener_tasas()        │        │  ya_se_consulto_hoy()      │
│ (caché JSON del día)   │        │  obtener_ultimo_registro() │
└───────────────────────┘        │  obtener_ultimo_registro() │
                                 └──────────────────────────┘

┌───────────────────────┐
│   config/settings.py   │  Carga .env, rutas, umbral de oferta,
│                        │  IDs de chat de Telegram por categoría
└───────────────────────┘

     main.py  ← Punto de entrada real: consulta un producto de Amazon,
                  garantiza el esquema (init_sqlite_db) y persiste la
                  consulta en tracker.db.
```

**Flujo de datos** (implementado hasta el paso 4; el resto sigue el [Roadmap](#roadmap)):

1. Se define un `PRODUCT_ID` (ASIN) y una URL de producto de Amazon en `main.py`.
2. `BaseScraper.obtener_datos()` consulta primero la BD: si el producto ya se consultó hoy, devuelve el registro guardado; si no, `AmazonScraper.extraer_datos()` renderiza la página con Playwright y extrae los datos con BeautifulSoup.
3. **(Implementado)** `services/currency.py::convertir_a_moneda_local()` convierte el precio a la moneda local **dentro de la fachada `guardar_datos_producto()`, antes de la transacción**; si `LOCAL_CURRENCY` no está configurada, guarda el par de origen (USD). Los valores convertidos quedan como histórico: `precio_local`/`moneda_local` en `Historial_Precios`.
4. **(Implementado)** Los datos se insertan en `database/tracker.db` (tablas `Productos`, `Historial_Precios`, `Metricas_Vendedor`) en una sola transacción con `commit`/`rollback` en la fachada.
5. *(No implementado)* Un analizador compararía el precio actual contra el historial para decidir si es una oferta.
6. *(No implementado)* Un módulo de notificaciones enviaría un mensaje a Telegram, al chat correspondiente según `CHATS_ID` en `config/settings.py`.

**Esquema vigente** (`init_sqlite_db()`, idempotente — `CREATE TABLE IF NOT EXISTS`; `Productos` con `asin` único, `titulo` y `categoria` nullable):

```sql
CREATE TABLE IF NOT EXISTS Productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asin TEXT UNIQUE,
    titulo TEXT NOT NULL,
    url TEXT NOT NULL,
    vendedor TEXT NOT NULL,
    categoria TEXT,                    -- nullable
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Historial_Precios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL,
    precio_local REAL NOT NULL,        -- COP si hubo conversión; USD si no
    moneda_local TEXT NOT NULL,        -- "COP" o "USD"
    precio_usd REAL NOT NULL,          -- precio original del scraper (siempre USD)
    fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES Productos(id)
);

CREATE TABLE IF NOT EXISTS Metricas_Vendedor (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL,
    nombre_vendedor TEXT NOT NULL,
    total_ventas INTEGER NOT NULL,
    calificacion_promedio REAL NOT NULL,
    fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES Productos(id)
);
```

## Estructura de directorios

```
comparador-precios/
├── config/
│   ├── __init__.py
│   └── settings.py          # Rutas, variables de entorno, umbral de oferta
├── database/
│   ├── __init__.py
│   ├── schema.py            # init_sqlite_db(), ContratoDatos, fachada guardar_datos_producto(), ya_se_consulto_hoy(), obtener_ultimo_registro()
│   ├── tracker.db           # Base de datos SQLite real (versionada en git, ver Seguridad)
│   └── tasas_cambio.json    # Caché del día: objeto único {"fecha", "COP", "USD"} (se sobreescribe)
├── docs/
│   └── constitution.md      # Leyes inmutables de desarrollo del proyecto
├── scrapers/
│   ├── __init__.py
│   ├── BaseScraper.py       # Orquestador abstracto (Playwright async, BD, anti-CAPTCHA)
│   └── AmazonScraper.py     # Especialista de Amazon (solo extracción del DOM)
├── services/
│   ├── __init__.py
│   └── currency.py          # Conversión COP↔USD con caché JSON
├── .opencode/commands/      # Comandos del agente (/probar-metodo, /crear_spec)
├── .agents/skills/          # Roles del agente (@analista-nodos, @auditor-arquitectura)
├── main.py                  # Punto de entrada: consulta un producto de Amazon
├── MEMORY.md                # Memoria del proyecto (estado y decisiones)
├── AGENTS.md                # Directrices para agentes de IA
├── requirements.txt
├── .gitignore
└── README.md
```

## Requisitos previos

- **Python 3.14.8** (gestionado con pyenv en el entorno actual del proyecto; el repositorio no fija versión con `pyproject.toml` ni `.python-version` — `TODO:` versionar la versión objetivo).
- `pip` para instalar dependencias.
- Los navegadores de Playwright instalados localmente (`playwright install`), ya que `scrapers/BaseScraper.py` depende de un binario de Chromium.
- Un bot de Telegram creado (token y chat IDs) si se desea usar en el futuro el módulo de notificaciones — actualmente `config/settings.py` ya espera estas variables aunque ningún módulo las consuma todavía.
- Una API key de un servicio de tasas de cambio que devuelva la forma `{"conversion_rates": {"COP": ...}}` en su respuesta (formato inferido del código en `services/currency.py`; `TODO:` confirmar el proveedor exacto).

## Instalación paso a paso

```bash
# 1. Clonar el repositorio
git clone https://github.com/thomasnoah3076-coder/comparador-precios.git
cd comparador-precios

# 2. Crear y activar un entorno virtual
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux / Mac
source .venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Instalar el navegador que usa Playwright
playwright install chromium

# 5. Crear el archivo .env en la raíz del proyecto (ver tabla de variables abajo)

# 6. Inicializar la base de datos SQLite (desde la raíz del proyecto)
python -m database.schema
# (también funciona la ejecución directa: python database/schema.py)
```

> No existe un archivo `.env.example` en el repositorio. `TODO:` crear uno para facilitar el onboarding, con las claves de la tabla de configuración sin valores reales.

## Configuración

Variables de entorno leídas por `config/settings.py`. Ninguna de ellas está versionada — `.env` está excluido explícitamente en `.gitignore`.

| Variable | Descripción | Consumida en |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Token del bot de Telegram | `config/settings.py` (aún sin uso en ningún módulo de envío) |
| `TELEGRAM_CHAT_ID_GENERAL` | ID del chat/canal de Telegram para categoría "general" | `config/settings.py` → `CHATS_ID["general"]` |
| `TELEGRAM_CHAT_ID_PERFUMES` | ID del chat/canal para categoría "perfumes" | `config/settings.py` → `CHATS_ID["perfumes"]` |
| `TELEGRAM_CHAT_ID_TECNOLOGIA` | ID del chat/canal para categoría "tecnologia" | `config/settings.py` → `CHATS_ID["tecnologia"]` |
| `LOCAL_CURRENCY` | Código ISO de la moneda local para mostrar precios | `config/settings.py` → `DEFAULT_CURRENCY` |
| `EXCHANGE_RATE_API_KEY` | Clave de la API de tasas de cambio | `services/currency.py` |
| `EXCHANGE_RATE_API_URL` | URL base de la API de tasas de cambio | `services/currency.py` |

Adicionalmente, `config/settings.py` define un valor fijo en código (no viene de `.env`):

| Constante | Valor | Significado |
|---|---|---|
| `PRICE_DROP_THRESHOLD` | `0.15` | Caída de precio mínima (15 %) para considerar algo una oferta — aún no consumida por ningún analizador, ya que este módulo no existe todavía |

## Uso básico y ejemplos

**Inicializar (o reinicializar) el esquema de la base de datos:**

```bash
python -m database.schema
```

Ejecuta `init_sqlite_db()`, que crea las tablas `Productos`, `Historial_Precios` y `Metricas_Vendedor` en `database/tracker.db`.

> Ambas formas funcionan: `python -m database.schema` o la ejecución directa `python database/schema.py` (incluye un arranque de ruta condicionado que solo se activa al ejecutar el archivo como script). La inicialización **es idempotente** (`CREATE TABLE IF NOT EXISTS`): se puede ejecutar cuantas veces se quiera sin error y sin destruir tablas ni datos existentes (regla `docs/constitution.md` §3).

**Ejecutar el punto de entrada (consulta de extremo a extremo contra Amazon):**

```bash
python main.py
```

> Edita `PRODUCT_ID` (ASIN) y `URL_PRODUCTO` al inicio de `main.py`. `main.py` usa `asyncio.run(...)`, así que basta ejecutarlo con el intérprete del entorno virtual (`.venv/bin/python main.py` o con el venv activado). Los módulos de scrapers se importan con rutas absolutas de paquete (`from scrapers.BaseScraper import ...`), por lo que siempre hay que ejecutarlos desde la raíz del proyecto y **nunca** como ruta directa (`python scrapers/BaseScraper.py` falla con `ModuleNotFoundError`).

**Usar el conversor de divisas en un script propio:**

```python
from services.currency import convertir_moneda

resultado = convertir_moneda(100, "USD", "COP")  # devuelve el monto convertido (o el original si falla la conversión)
```

> La única pareja soportada es USD ↔ COP; `convertir_moneda(100, "USD", "USD")` devuelve el monto sin tocar la red, y otras parejas (p. ej. EUR) devuelven el monto con un aviso. La tasa del día se cachea en `database/tasas_cambio.json` (objeto único que se sobreescribe; si el registro es de hoy no se consulta la API).

> No existe todavía un ejemplo de uso end-to-end completo (scraper → conversión → base de datos): `main.py` ejecuta el scraping y la caché diaria, pero aún no llama a `convertir_moneda` ni persiste en SQLite.

## Scripts disponibles

El proyecto no define scripts en `pyproject.toml` ni entradas en `requirements.txt` del tipo consola. Los únicos puntos de entrada ejecutables directamente son bloques `if __name__ == "__main__":` dentro de módulos individuales:

| Comando | Qué hace |
|---|---|
| `python -m database.schema` (o `python database/schema.py`) | Crea las tablas de la base de datos SQLite (idempotente) |
| `python main.py` | Ejecuta la consulta de extremo a extremo de un producto de Amazon definido en `main.py` |

> `main.py` es el único punto de entrada que orquesta el flujo (scraping + caché diaria). La persistencia de resultados, la conversión de divisas y las notificaciones **aún no están conectadas** a él.

## Pruebas, calidad de código y cobertura

**No hay pruebas automatizadas versionadas:** no existe carpeta `tests/`. Sí están declarados `pytest` en `requirements.txt` (se usa con `.venv/bin/python -m pytest`, ya que `pytest` no está en el PATH global del sistema). El flujo de trabajo del proyecto (ver `AGENTS.md` §6.4) crea **baterías temporales aisladas** (sin red, sin `tracker.db`), las ejecuta y las elimina si todo pasa, conservándolas solo cuando hay fallos. Tampoco hay configuración de linters (`ruff`, `flake8`, `black`) ni de cobertura (`coverage.py`).

## Despliegue y entornos

No hay configuración de despliegue en el repositorio: no existe `Dockerfile`, workflow de GitHub Actions, ni definición de tareas programadas (cron, Task Scheduler) versionada. El objetivo declarado del proyecto es correr como "sistema programado", pero esa capa de automatización aún no está construida ni documentada en el código. Actualmente el proyecto se ejecuta de forma manual, en un entorno de desarrollo local **Linux** con entorno virtual `.venv` (Python 3.14.8 gestionado con pyenv; el proyecto se migró desde Windows en octubre de 2026).

## Seguridad, privacidad y manejo de datos

- `.env` está correctamente excluido de git vía `.gitignore`, junto con `.venv/` y archivos `.docx`.
- **`database/tracker.db` está versionado en git** (confirmado con `git ls-files`). Esto significa que los datos reales scrapeados (productos, precios, URLs) quedan almacenados de forma permanente en el historial del repositorio, incluso si en el futuro se elimina el archivo del working tree. Se recomienda añadir `*.db` al `.gitignore` y versionar únicamente el esquema (`schema.py`), no los datos generados.
- El proyecto obtiene datos de sitios de terceros (actualmente Amazon) mediante automatización de navegador. Esto tiene implicaciones de Términos de Servicio que exceden el alcance técnico de este README; la decisión de cómo y con qué frecuencia scrapear debe tomarse conscientemente por el mantenedor del proyecto.
- No se han identificado datos personales de terceros almacenados (los datos son de productos y vendedores públicos en los marketplaces).

## Solución de problemas frecuentes

**`ModuleNotFoundError: No module named 'config'` o `'scrapers'` al ejecutar un módulo**
Al ejecutar un archivo su directorio reemplaza a la raíz en `sys.path` y los paquetes del proyecto no se encuentran. Ejecuta desde la **raíz** y con `-m` (`python -m scrapers.algo`), o usa los puntos de entrada que ya lo resuelven: `database/schema.py` incluye un arranque de ruta condicionado (funciona directo y con `-m`), y el scraper se usa vía `python main.py` (no tiene bloque `__main__` propio).

**Amazon devuelve un CAPTCHA (`Robot Check`) o un error HTTP distinto de 200**
`BaseScraper.verificacion_de_estado_html()` lanza `Exception` con "HTML contiene indicadores de bloqueo" o "Error HTTP ..." antes de extraer datos, para no guardar datos nulos. Si ocurre de forma sostenida, revisa si se está raspando con demasiada frecuencia (la caché diaria de `ya_se_consulto_hoy` existe justo para limitar consultas repetidas).

**El scraper no encuentra precio principal (solo "15 opciones desde ...")**
El precio del buybox depende de la ubicación de entrega fijada en Miami (ZIP 33122). El widget de ubicación es *best-effort*: si falla se imprime "Aviso: no se pudo fijar la ubicación Miami" y se continúa sin precio principal.

**`json.decoder.JSONDecodeError` o respuesta rara de la API al convertir divisas**
`services/currency.py::obtener_tasas()` captura el JSON corrupto o vacío y lo **autoregenera** con la consulta del día (ya no hace falta borrar nada a mano). Si la API falla (clave inválida, sin red o estado ≠ 200), se imprime el motivo y se devuelve el monto original sin convertir (degradación elegante). La caché vive en `database/tasas_cambio.json` como objeto único `{"fecha", "COP", "USD"}`.

**`ImportError: cannot import name 'stealth_async'` de `playwright_stealth`**
El proyecto usa `playwright-stealth` 2.x: la API correcta es la clase `Stealth` con `apply_stealth_async(page)` (la función `stealth_async` era de la 1.x). Verificado en `requirements.txt` (`playwright-stealth>=1.0.6`) y en `scrapers/BaseScraper.py`.

## Guía de contribución

El proyecto es mantenido actualmente por un único desarrollador y no cuenta con un archivo `CONTRIBUTING.md`. El historial de git muestra uso ocasional de ramas con merge hacia `main` (por ejemplo, los commits `b843e98` y `8541243`). Para quien colabore:

- Sigue el estilo de comentarios y docstrings ya presente (ver [Convenciones de desarrollo](#convenciones-de-desarrollo)).
- Antes de scrapear una tienda nueva, valida manualmente los selectores CSS en las herramientas de desarrollador del navegador — el historial del proyecto muestra que estos cambian con frecuencia (caso eBay).
- No agregues archivos `.db` generados al control de versiones (ver [Seguridad](#seguridad-privacidad-y-manejo-de-datos)).

## Convenciones de desarrollo

Observadas de forma consistente en el código actual:

- **Comentarios y docstrings en español** en todo el proyecto (obligatorio según `docs/constitution.md`: identificadores, métodos y comentarios en español).
- **Manejo de errores** con `try/except` y mensajes de advertencia impresos por consola (`print(...)`) en lugar de un sistema de logging (`logging`).
- **Nombres de archivo de scrapers en PascalCase** (`BaseScraper.py`, `AmazonScraper.py`), distinto de la convención `snake_case` habitual para módulos en Python — mantenlo así por consistencia con el código existente al agregar un scraper nuevo, o decide formalmente migrar todos los nombres a una vez.
- **Flujo de trabajo con agentes IA** (`AGENTS.md`): leer `MEMORY.md` → proponer QUÉ/CÓMO → esperar aprobación → ejecutar → actualizar `MEMORY.md`. Las pruebas son siempre temporales y aisladas (§6.4).

## Roadmap

**Implementado (en el repositorio, verificado en código):**

- [x] Esquema SQLite (`Productos`, `Historial_Precios`, `Metricas_Vendedor`)
- [x] Conversión de divisas COP↔USD con caché diario en JSON
- [x] Contrato `BaseScraper` + extracción de HTML renderizado con Playwright **asíncrono** + `playwright-stealth`
- [x] Scraper concreto para **Amazon** (`AmazonScraper`), con detección de CAPTCHA y ubicación de entrega Miami
- [x] Verificación de si un producto ya se consultó en el día actual (`ya_se_consulto_hoy`)
- [x] Punto de entrada `main.py` de extremo a extremo (consulta de un producto de Amazon)
- [x] Persistencia: `INSERT` de los datos scrapeados en SQLite mediante la fachada transaccional `guardar_datos_producto` (conversión a COP previa con fallback honesto, historial append-only, métricas opcionales; crecimiento diario por `ya_se_consulto_hoy`)
- [x] Migración de `EbayScraper` a `AmazonScraper` y de Playwright síncrono a asíncrono (el pivote ya está comprometido al repositorio)

**Planificado (mencionado en documentación de contexto y/o discusiones de diseño, sin código en el repositorio todavía):**

- [ ] Conexión del resto del flujo: análisis del precio guardado → notificación (la persistencia ya cierra el ciclo de escritura)
- [ ] Analizador de ofertas que use `PRICE_DROP_THRESHOLD` contra el historial de precios
- [ ] Módulo de notificaciones por Telegram (`python-telegram-bot`)
- [ ] Estrategia de control de volumen para scraping sostenido: delays aleatorios, rotación de User-Agent, evaluación de proxies residenciales

## Fases de desarrollo

### Fase 1 — Andamiaje inicial del proyecto
- **Objetivo:** dejar creada la estructura mínima de archivos del repositorio.
- **Entregado:** `main.py` y `requirements.txt` vacíos, commit inicial.
- **Archivos/módulos:** `main.py`, `requirements.txt`.
- **Resultado:** repositorio inicializado, sin funcionalidad todavía.
- **Riesgos/limitaciones:** ninguno relevante, es un punto de partida.
- **Commits:** `7f6c86f`, `4e6281a`, `003e657` (13 ago 2026).

### Fase 2 — Documentación del entorno de desarrollo
- **Objetivo:** dejar registrado cómo crear y usar un entorno virtual de Python, como guía para el propio autor.
- **Entregado:** sección de README explicando qué es un entorno virtual y cómo activarlo/desactivarlo en Windows y Unix.
- **Archivos/módulos:** `README.md`.
- **Resultado:** documentación base, aún sin contenido técnico del proyecto en sí.
- **Riesgos/limitaciones:** este contenido educativo sobre entornos virtuales queda ahora reemplazado por el presente README, orientado al proyecto.
- **Commits:** `7dd24f5` (18 ago 2026).

### Fase 3 — Capa de persistencia (SQLite)
- **Objetivo:** definir dónde y cómo se guardarían productos, historial de precios y métricas de vendedor.
- **Entregado:** función `init_sqlite_db()` con la creación de las tablas `Productos`, `Historial_Precios` y `Metricas_Vendedor`; ruta de la base de datos centralizada en configuración.
- **Archivos/módulos:** `database/schema.py`, `database/tracker.db`, `config/settings.py` (ruta `DB_PATH_TRACKER`).
- **Resultado:** esquema de base de datos funcional y ejecutable.
- **Riesgos/limitaciones:** el archivo `tracker.db` quedó versionado en git desde este momento (ver [Seguridad](#seguridad-privacidad-y-manejo-de-datos)).
- **Commits:** `51208a3`, `726790d`, `b843e98` (19 ago 2026).

### Fase 4 — Configuración y variables de entorno
- **Objetivo:** centralizar configuración sensible (tokens, IDs de chat, claves de API) fuera del código fuente.
- **Entregado:** carga de `.env` con `python-dotenv`, definición de `TELEGRAM_BOT_TOKEN`, `CHATS_ID` por categoría, `DEFAULT_CURRENCY`; reglas de exclusión en `.gitignore`.
- **Archivos/módulos:** `config/config.py` (más adelante renombrado a `settings.py`), `.gitignore`.
- **Resultado:** variables de entorno cargándose correctamente y excluidas de git.
- **Riesgos/limitaciones:** ninguno identificado en el código revisado.
- **Commits:** `0a826dd`, `c849ed4` (22 ago 2026).

### Fase 5 — Servicio de conversión de divisas
- **Objetivo:** convertir montos entre COP y USD sin exceder el uso de una API externa de tasas de cambio.
- **Entregado:** función `currency_converter()` con lógica de caché diaria en `exchange_rates.json`; renombrado de `config.py` a `settings.py`; corrección del nombre de la variable de ruta de la base de datos.
- **Archivos/módulos:** `services/currency.py`, `database/exchange_rates.json`, `config/settings.py`.
- **Resultado:** conversión funcional con caché para evitar llamadas repetidas a la API el mismo día.
- **Riesgos/limitaciones:** el proveedor exacto de la API de tasas de cambio no está documentado explícitamente en el código (solo inferido por la forma de la respuesta esperada, `conversion_rates`).
- **Commits:** `f4b1b3f`, `99c49b5`, `73114bb`, `43dfaf7`, `11e5c6b` (25 ago 2026), `ff39cd9` (26 ago 2026).

### Fase 6 — Arquitectura de scraping y primer scraper funcional (eBay)
- **Objetivo:** definir un contrato común para cualquier scraper y entregar una primera implementación funcional contra una tienda real.
- **Entregado:** clase abstracta `BaseScraper` con `extraer_html()` (Playwright síncrono, headful) y el método abstracto `extraer_datos()`; clase concreta `EbayScraper` que extrae título, precio, moneda, vendedor, ventas y rating; limpieza de código no utilizado en `currency.py`; actualización de `.gitignore` para excluir `.docx`.
- **Archivos/módulos:** `scrapers/BaseScraper.py`, `scrapers/EbayScraper.py` (renombrado después a `AmazonScraper.py` en el commit `7e9250f`), `.gitignore`.
- **Resultado:** primer scraper end-to-end funcional de forma manual.
- **Riesgos/limitaciones:** en su momento requirió modo headful porque eBay bloqueaba `headless=True` (hoy el código corre headless con stealth contra Amazon); los selectores CSS están sujetos a romperse ante cambios de la plataforma; no hay reintentos ni backoff ante bloqueos.
- **Commits:** `b329a24`, `91a5973`, `5308a3a`, `add4041`, `8541243` (8 sep 2026), `7e9250f` (renombrado a Amazon).

### Fase 7 — Control de frecuencia de consultas
- **Objetivo:** evitar volver a scrapear el mismo producto más de una vez al día, como primera medida de control de volumen de peticiones.
- **Entregado:** función `ya_se_consulto_hoy(conn, product_id)` en `database/schema.py`, que consulta la fecha del último registro en `Historial_Precios`.
- **Archivos/módulos:** `database/schema.py`.
- **Resultado:** función implementada **y llamada desde `BaseScraper.obtener_datos()`** (el orquestador devuelve el registro guardado si ya se consultó hoy).
- **Riesgos/limitaciones:** tuvo dos defectos históricos, ambos corregidos: filtraba por `Historial_Precios.id` en vez de `producto_id`, y comparaba el `TIMESTAMP` completo con `date.today().isoformat()` (nunca coincidía). Sigue sin efecto práctico hasta que exista el `INSERT` de persistencia (sin filas, no hay nada que cachear).
- **Commits:** `cc825aa` (17 sep 2026).

### Fase 8 — Pivote a Amazon (comprometido al repositorio)
- **Objetivo:** reemplazar el scraper de eBay por uno para Amazon, con Playwright asíncrono, `playwright-stealth` y detección de bloqueos.
- **Entregado:** `AmazonScraper` (extracción del DOM con claves del contrato en español), `BaseScraper` asíncrono con `obtener_dom()`, `verificacion_de_estado_html()` (anti-CAPTCHA), ubicación de entrega Miami, `playwright-stealth` en `requirements.txt` y `main.py` como punto de entrada funcional.
- **Archivos/módulos:** `scrapers/AmazonScraper.py`, `scrapers/BaseScraper.py`, `main.py`, `requirements.txt`.
- **Resultado:** consulta de extremo a extremo verificada contra Amazon real (precio `42.7 USD`, rating `4.7`, `origen: scraping`).
- **Riesgos/limitaciones:** sin persistencia aún (los datos no se guardan en SQLite); sin validación bajo volumen sostenido; el widget de ubicación Miami es *best-effort*.
- **Commits:** `7e9250f`, `5678b05`, `77f2697`, `66a5c6e` (oct 2026).

## Decisiones técnicas y evolución del proyecto

| Decisión | Contexto | Alternativas consideradas | Motivo de elección | Consecuencias / trade-offs | Estado |
|---|---|---|---|---|---|
| Usar SQLite como base de datos | Proyecto personal, sin necesidad de servidor de base de datos dedicado | PostgreSQL, MySQL | Cero configuración, base de datos como archivo único, suficiente para el volumen esperado | No soporta bien concurrencia ni acceso remoto; adecuado solo mientras el proyecto no escale | Implementado |
| Enfocar el scraping en una sola tienda a la vez en lugar de múltiples en paralelo | Intentos previos con Mercado Libre fallaron: `requests`+BeautifulSoup no capturaba contenido dinámico, la API pública devolvía 403, y Playwright tenía bloqueos y esperas largas | Mantener varios scrapers en desarrollo simultáneo | Reducir complejidad y validar el flujo completo con una sola fuente antes de extender a otras tiendas | Tras una primera fase con eBay, hoy `AmazonScraper` es la única implementación concreta; el trabajo sobre Mercado Libre se descartó | Implementado (eBay reemplazado por Amazon) |
| Usar Playwright en vez de `requests` para obtener el HTML | El precio y título de productos se cargan vía JavaScript en Mercado Libre, eBay y Amazon, y `requests` no ejecuta JS | `requests` + BeautifulSoup (insuficiente, ya probado), Selenium | Playwright soporta esperar contenido dinámico y tiene mejor camino hacia técnicas de sigilo | Dependencia más pesada (requiere instalar binarios de navegador); necesidad de manejar timeouts | Implementado |
| Ejecutar el navegador en modo headless con `playwright-stealth` | Con `headless=True` puro, eBay devolvía bloqueos; el riesgo de detección se mantiene en Amazon | Mantener el antiguo modo headful (`headless=False`) | El stealth 2.x + cookies + ubicación Miami evitaron el bloqueo en las pruebas contra Amazon, y habilita ejecución sin gráficos | Sigue sin validarse bajo volumen sostenido; un CAPTCHA persistente aborta la ejecución (por diseño) | Implementado |
| Verificar diariamente si un producto ya fue consultado, antes de scrapear de nuevo | Necesidad de controlar el volumen de peticiones para reducir el riesgo de bloqueo | Un archivo de log aparte; un scheduler con estado en memoria | Reutilizar la tabla `Historial_Precios` ya existente, sin infraestructura nueva | Corregido en oct 2026 (filtro por `producto_id` y comparación solo de la parte de fecha); sin efecto práctico hasta que exista el `INSERT` de persistencia | Implementado |
| Cachear las tasas de cambio en un archivo JSON local en lugar de consultar la API en cada ejecución | Evitar llamadas innecesarias a una API externa de tasas de cambio | Consultar siempre la API; guardar las tasas en una tabla SQLite | La tasa solo necesita actualizarse una vez al día; un JSON es más simple que una tabla para este caso de uso | Posible desfase de hasta un día si la tasa cambia intradía | Implementado |
| Adoptar Playwright asíncrono + `playwright-stealth` para el scraper de Amazon | Se busca evitar el patrón de bloqueo visto con eBay y dejar la puerta abierta a concurrencia futura | Mantener Playwright síncrono (como el original de eBay); usar la Product Advertising API oficial de Amazon | La API asíncrona es la recomendada por Playwright para uso con stealth y permite concurrencia sin reescribir la base | La firma abstracta `extraer_datos` también se declaró `async` para que todo scraper futuro cumpla el contrato | Implementado |
| No duplicar el HTML scrapeado en archivos ni en otra base de datos | Se evaluó cachear el HTML por producto para depurar selectores sin re-scrapear | Guardar un `.html` por producto; crear una tabla o base de datos separada para el HTML crudo | Proyecto personal sin necesidad de escalar; el histórico relevante (precio) ya vive en SQLite | No queda registro de la página exacta que originó cada dato, lo que dificulta depurar selectores rotos retroactivamente | Decidido, sin código todavía en el repositorio |

## Licencia y créditos

**Autor:** Thomas Chaparro (`thomasnoah3076-coder`), identificado como autor de la totalidad de los commits del repositorio.

## Pendientes de documentar

- **`database/tracker.db` está versionado en git** con datos reales. `TODO:` decidir si se elimina del historial y se agrega `*.db` al `.gitignore`.
- **Proveedor real de la API de tasas de cambio no confirmado** — solo se infiere del formato de respuesta esperado (`conversion_rates`) en `services/currency.py`. `TODO:` documentar el proveedor exacto.
- **No existe `.env.example`** para facilitar el onboarding de nuevos colaboradores. `TODO:` crearlo con las claves listadas en la tabla de configuración, sin valores reales.
- **Módulos planeados aún inexistentes:** `notifications/telegram.py` y un analizador de ofertas. `TODO:` confirmar si siguen planeados (el alcance actual prioriza la persistencia en SQLite).
- **Versión de Python sin versionar en el repo:** el entorno usa 3.14.8 (pyenv), pero no hay `pyproject.toml` ni `.python-version`. `TODO:` versionarla.

> **Resueltos en octubre 2026:** `___init__.py` (ya renombrados a `__init__.py`); bug de `ya_se_consulto_hoy` (`producto_id` y comparación de fecha, ya corregidos); estado del pivote a Amazon (comprometido al repositorio, ver Fase 8); `main.py` implementado; ejecución directa de `database/schema.py` (arranque de ruta condicionado, ambos comandos funcionan); `init_sqlite_db()` ahora es idempotente (`CREATE TABLE IF NOT EXISTS`).

## Resumen de cambios propuestos

- Se generó este README desde cero, reemplazando el contenido anterior (una guía genérica sobre entornos virtuales de Python) por documentación específica del proyecto, basada en inspección directa del código fuente y del historial de git del repositorio real.
- Se reconstruyeron 8 fases de desarrollo con evidencia de commits; la Fase 8 (pivote a Amazon) quedó reescrita como **comprometida al repositorio** (antes documentada como "en diseño, sin código").
- Se documentaron las decisiones técnicas con contexto, alternativas y trade-offs, actualizando las filas obsoletas sobre eBay/headful/síncrono al estado real (Amazon/headless+stealth/asíncrono).
- **Actualización de octubre 2026 (auditoría código vs documentación):** se corrigieron todas las afirmaciones falsas detectadas (EbayScraper, `main.py` vacío, stealth/pytest "ausentes", Playwright síncrono, umbral 0.3, entorno Windows), se resolvieron los `TODO:` ya saldados y se añadieron los pendientes reales (`.env.example`, proveedor de la API).
- **Segunda corrección de octubre 2026:** se arreglaron los dos errores detectados por esa auditoría — el comando `python database/schema.py` (arranque de ruta condicionado: ahora funcionan tanto ese comando como `python -m database.schema`) y la no-idempotencia de `init_sqlite_db()` (`CREATE TABLE IF NOT EXISTS`: seguro de repetir sin destruir datos, conforme a `docs/constitution.md` §3).
- No se incluyeron secretos, tokens ni valores reales de variables de entorno en ningún ejemplo.
