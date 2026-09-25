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
- Conversión de montos entre COP y USD, con caché diario de tasas de cambio en un archivo JSON local (`services/currency.py`, `database/exchange_rates.json`).
- Contrato abstracto de scraper (`BaseScraper`) con extracción de HTML renderizado vía Playwright (`scrapers/BaseScraper.py`).
- Implementación concreta de scraper para eBay que extrae título, precio, moneda, vendedor, ventas y rating (`scrapers/EbayScraper.py`).
- Función para verificar si un producto ya fue consultado en el día actual, como base para controlar el volumen de peticiones (`database/schema.py::ya_se_consulto_hoy`).
- Carga de variables de entorno sensibles desde `.env`, excluido de control de versiones (`config/settings.py`).

**Planificado, mencionado en diseño o en documentación de contexto, pero AÚN NO presente en el código del repositorio** (ver [Roadmap](#roadmap)):

- Scraper para Amazon (`scrapers/amazon.py` o equivalente).
- Orquestador general (`main.py` existe pero está vacío).
- Analizador de ofertas que compare el precio actual contra el historial.
- Módulo de notificaciones por Telegram (`python-telegram-bot` está en `requirements.txt` pero no se usa en ningún módulo todavía).
- Rotación de proxies residenciales, delays aleatorios y rotación de User-Agents para scraping en segundo plano sostenido.

## Estado actual y nivel de madurez

**Prototipo en desarrollo activo, no apto para producción ni para ejecución desatendida (segundo plano) todavía.**

Evidencia concreta del estado:

- `main.py` existe pero está vacío: no hay ningún punto de entrada que conecte scraping, conversión de divisas, base de datos y notificaciones.
- El único scraper funcional (`EbayScraper`) se ejecuta actualmente con Playwright en modo **headful** (`headless=False`), es decir, requiere una interfaz gráfica visible — no está listo para correr como proceso en segundo plano en un servidor.
- No existen pruebas automatizadas, ni configuración de integración continua.
- No hay módulo de notificaciones ni de análisis de ofertas implementado.

## Stack tecnológico

| Tecnología | Uso en el proyecto | Justificación |
|---|---|---|
| **Python** | Lenguaje principal de todo el proyecto | Ecosistema maduro para scraping, manejo de datos y APIs |
| **SQLite** (`sqlite3`, stdlib) | Persistencia de productos, historial de precios y métricas de vendedor | Cero configuración, base de datos como archivo único, adecuada para un proyecto de un solo usuario |
| **Playwright** (`playwright.sync_api`) | Renderizado de páginas con contenido dinámico (JavaScript) antes de extraer datos | `requests` + `BeautifulSoup` resultó insuficiente contra Mercado Libre y eBay por carga dinámica de contenido |
| **BeautifulSoup4** | Parseo del HTML ya renderizado por Playwright, búsqueda por selectores CSS | Estándar de facto en Python para extracción de datos de HTML |
| **requests** | Consumo de la API de tasas de cambio en `services/currency.py` | Cliente HTTP simple para APIs que no requieren renderizado |
| **python-dotenv** | Carga de variables sensibles desde `.env` | Evita hardcodear tokens y claves en el código fuente |
| **python-telegram-bot** | Declarado en `requirements.txt` para el futuro módulo de notificaciones | Aún sin uso en el código; ver [Roadmap](#roadmap) |

> `playwright-stealth` se ha evaluado en discusiones de diseño para mitigar la detección de automatización, pero **no está en `requirements.txt` ni en ningún módulo del repositorio actual**.

## Arquitectura del sistema

El proyecto sigue un patrón de **scrapers intercambiables sobre un contrato común**, más un conjunto de servicios independientes (divisas, base de datos) que aún no están conectados entre sí por un orquestador.

```
┌─────────────────────┐
│   BaseScraper (ABC)  │  scrapers/BaseScraper.py
│  - extraer_html()    │  (Playwright sync, headful)
│  - extraer_datos()   │  (método abstracto)
└──────────┬───────────┘
           │ hereda
┌──────────▼───────────┐
│    EbayScraper        │  scrapers/EbayScraper.py
│  extraer_datos(url)   │  → dict: nombre, precio, moneda,
│                       │    url, vendedor, ventas, rating
└───────────────────────┘

┌───────────────────────┐        ┌──────────────────────────┐
│ services/currency.py   │        │  database/schema.py       │
│ currency_converter()   │        │  init_sqlite_db()          │
│ (caché en JSON diario) │        │  ya_se_consulto_hoy()      │
└───────────────────────┘        └──────────────────────────┘

┌───────────────────────┐
│   config/settings.py   │  Carga .env, rutas, umbral de oferta,
│                        │  IDs de chat de Telegram por categoría
└───────────────────────┘

              main.py  ← VACÍO. No existe orquestación real todavía.
```

**Flujo de datos conceptual** (tal como está diseñado en la documentación de contexto del proyecto, aunque `main.py` todavía no lo implementa):

1. Se define una URL de producto de una tienda soportada.
2. El scraper concreto (actualmente solo `EbayScraper`) renderiza la página con Playwright y extrae los datos con BeautifulSoup.
3. `services/currency.py` convierte el precio a la moneda local y/o USD, usando la tasa cacheada del día si ya existe.
4. Los datos se persisten en `database/tracker.db` (tablas `Productos`, `Historial_Precios`, `Metricas_Vendedor`).
5. *(No implementado)* Un analizador compararía el precio actual contra el historial para decidir si es una oferta.
6. *(No implementado)* Un módulo de notificaciones enviaría un mensaje a Telegram, al chat correspondiente según `CHATS_ID` en `config/settings.py`.

## Estructura de directorios

```
comparador-precios/
├── config/
│   ├── ___init__.py        # ⚠️ nombre con 3 guiones bajos, ver "Pendientes de documentar"
│   └── settings.py         # Rutas, variables de entorno, umbral de oferta
├── database/
│   ├── ___init__.py        # ⚠️ mismo problema de nombre
│   ├── schema.py           # init_sqlite_db() y ya_se_consulto_hoy()
│   ├── tracker.db           # Base de datos SQLite real (versionada en git, ver Seguridad)
│   └── exchange_rates.json # Caché diario de tasas de cambio (generado en ejecución)
├── scrapers/
│   ├── ___init__.py        # ⚠️ mismo problema de nombre
│   ├── BaseScraper.py      # Clase abstracta común a cualquier scraper
│   └── EbayScraper.py      # Único scraper concreto implementado
├── services/
│   ├── __init__.py         # Correcto (2 guiones bajos)
│   └── currency.py         # Conversión COP↔USD con caché JSON
├── main.py                  # Vacío — orquestador pendiente de implementar
├── requirements.txt
├── .gitignore
└── README.md
```

## Requisitos previos

- Python instalado (versión mínima no fijada en el repositorio — `TODO:` confirmar versión objetivo; no hay `pyproject.toml` ni `.python-version`).
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

# 6. Inicializar la base de datos SQLite
python database/schema.py
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
| `PRICE_DROP_THRESHOLD` | `0.3` | Caída de precio mínima (30 %) para considerar algo una oferta — aún no consumida por ningún analizador, ya que este módulo no existe todavía |

## Uso básico y ejemplos

**Inicializar (o reinicializar) el esquema de la base de datos:**

```bash
python database/schema.py
```

Ejecuta `init_sqlite_db()`, que crea las tablas `Productos`, `Historial_Precios` y `Metricas_Vendedor` en `database/tracker.db`.

**Probar el scraper de eBay de forma manual** (bloque `if __name__ == "__main__":` incluido en el propio archivo, con una URL de ejemplo hardcodeada):

```bash
python -m scrapers.EbayScraper
```

> Se ejecuta con `-m` desde la raíz del proyecto porque `EbayScraper.py` importa `BaseScraper` con una ruta absoluta de paquete (`from scrapers.BaseScraper import BaseScraper`); ejecutarlo como `python scrapers/EbayScraper.py` directamente falla con `ImportError`.

**Usar el conversor de divisas en un script propio:**

```python
from services.currency import currency_converter

resultado = currency_converter(100, "USD", "COP")
```

> No existe todavía un ejemplo de uso end-to-end (scraper → conversión → base de datos), porque `main.py` no está implementado.

## Scripts disponibles

El proyecto no define scripts en `pyproject.toml` ni entradas en `requirements.txt` del tipo consola. Los únicos puntos de entrada ejecutables directamente son bloques `if __name__ == "__main__":` dentro de módulos individuales:

| Comando | Qué hace |
|---|---|
| `python database/schema.py` | Crea las tablas de la base de datos SQLite |
| `python -m scrapers.EbayScraper` | Ejecuta una extracción de prueba contra una URL de eBay fija en el código |

`main.py` está vacío — no hay todavía un script único que orqueste el flujo completo.

## Pruebas, calidad de código y cobertura

No hay pruebas automatizadas en el repositorio: no existe carpeta `tests/`, ni `pytest`, `unittest` u otro framework en `requirements.txt`. Tampoco hay configuración de linters (`ruff`, `flake8`, `black`) ni de cobertura (`coverage.py`). La validación actual del comportamiento se hace de forma manual, ejecutando los bloques `__main__` de cada módulo contra datos reales.

## Despliegue y entornos

No hay configuración de despliegue en el repositorio: no existe `Dockerfile`, workflow de GitHub Actions, ni definición de tareas programadas (cron, Task Scheduler) versionada. El objetivo declarado del proyecto es correr como "sistema programado", pero esa capa de automatización aún no está construida ni documentada en el código. Actualmente el proyecto solo se ha ejecutado de forma manual, en un entorno de desarrollo local en Windows con entorno virtual `.venv`.

## Seguridad, privacidad y manejo de datos

- `.env` está correctamente excluido de git vía `.gitignore`, junto con `.venv/` y archivos `.docx`.
- **`database/tracker.db` está versionado en git** (confirmado con `git ls-files`). Esto significa que los datos reales scrapeados (productos, precios, URLs) quedan almacenados de forma permanente en el historial del repositorio, incluso si en el futuro se elimina el archivo del working tree. Se recomienda añadir `*.db` al `.gitignore` y versionar únicamente el esquema (`schema.py`), no los datos generados.
- El proyecto obtiene datos de sitios de terceros (eBay, y en diseño, Amazon) mediante automatización de navegador. Esto tiene implicaciones de Términos de Servicio que exceden el alcance técnico de este README; la decisión de cómo y con qué frecuencia scrapear debe tomarse conscientemente por el mantenedor del proyecto.
- No se han identificado datos personales de terceros almacenados (los datos son de productos y vendedores públicos en los marketplaces).

## Solución de problemas frecuentes

**`ImportError: attempted relative import` o `ModuleNotFoundError` al ejecutar `EbayScraper.py`**
Ejecuta el módulo con `python -m scrapers.EbayScraper` desde la raíz del proyecto, no `python scrapers/EbayScraper.py` directamente.

**eBay devuelve una página de bloqueo genérica en vez del contenido real**
Ocurre específicamente cuando Playwright se lanza con `headless=True`. La mitigación actual en el código es mantener `headless=False` (modo headful) en `scrapers/BaseScraper.py`. Esto es una solución temporal: impide ejecutar el scraper en un servidor sin interfaz gráfica.

**`json.decoder.JSONDecodeError` al convertir divisas**
`services/currency.py` ya captura esta excepción cuando `database/exchange_rates.json` está corrupto o vacío, y devuelve el monto original sin convertir. Si ocurre, revisa o borra manualmente ese archivo para que se regenere.

**`playwright_stealth` lanza `ImportError: cannot import name 'stealth_async'`**
Aplica solo si se integra `playwright-stealth` (todavía no está en el repositorio). Las versiones 2.x de esa librería reemplazaron la función `stealth_async` por la clase `Stealth` con el método `apply_stealth_async(page)`.

## Guía de contribución

El proyecto es mantenido actualmente por un único desarrollador y no cuenta con un archivo `CONTRIBUTING.md`. El historial de git muestra uso ocasional de ramas con merge hacia `main` (por ejemplo, los commits `b843e98` y `8541243`). Para quien colabore:

- Sigue el estilo de comentarios y docstrings ya presente (ver [Convenciones de desarrollo](#convenciones-de-desarrollo)).
- Antes de scrapear una tienda nueva, valida manualmente los selectores CSS en las herramientas de desarrollador del navegador — el historial del proyecto muestra que estos cambian con frecuencia (caso eBay).
- No agregues archivos `.db` generados al control de versiones (ver [Seguridad](#seguridad-privacidad-y-manejo-de-datos)).

## Convenciones de desarrollo

Observadas de forma consistente en el código actual:

- **Comentarios y docstrings en español** en todo el proyecto.
- **Estructura de docstring** con secciones `Parámetros:`, `Retorna:` y `Funcionamiento:` (ver `scrapers/EbayScraper.py`, `scrapers/BaseScraper.py`).
- **Manejo de errores** con `try/except` y mensajes de advertencia impresos por consola (`print(...)`) en lugar de un sistema de logging (`logging`).
- **Nombres de archivo de scrapers en PascalCase** (`BaseScraper.py`, `EbayScraper.py`), distinto de la convención `snake_case` habitual para módulos en Python — mantenlo así por consistencia con el código existente al agregar un scraper nuevo, o decide formalmente migrar todos los nombres a la vez.

## Roadmap

**Implementado (en el repositorio, verificado en código):**

- [x] Esquema SQLite (`Productos`, `Historial_Precios`, `Metricas_Vendedor`)
- [x] Conversión de divisas COP↔USD con caché diario en JSON
- [x] Contrato `BaseScraper` + extracción de HTML renderizado con Playwright
- [x] Scraper concreto para eBay
- [x] Verificación de si un producto ya se consultó en el día actual (`ya_se_consulto_hoy`)

**Planificado (mencionado en documentación de contexto y/o discusiones de diseño, sin código en el repositorio todavía):**

- [ ] Scraper para Amazon, con Playwright en modo asíncrono y `playwright-stealth` para mitigar detección de automatización
- [ ] Orquestador (`main.py`) que conecte scraping → conversión → persistencia → análisis → notificación
- [ ] Analizador de ofertas que use `PRICE_DROP_THRESHOLD` contra el historial de precios
- [ ] Módulo de notificaciones por Telegram (`python-telegram-bot`)
- [ ] Estrategia de control de volumen para scraping sostenido: delays aleatorios, rotación de User-Agent, evaluación de proxies residenciales
- [ ] Migrar (o justificar explícitamente no migrar) `EbayScraper` de Playwright síncrono a asíncrono, para mantener consistencia con el diseño planteado para Amazon

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
- **Archivos/módulos:** `scrapers/BaseScraper.py`, `scrapers/EbayScraper.py`, `.gitignore`.
- **Resultado:** primer scraper end-to-end funcional de forma manual (bloque `__main__` con una URL real de prueba).
- **Riesgos/limitaciones:** el scraper requiere modo headful (`headless=False`) porque eBay bloquea el contenido real cuando detecta `headless=True`; los selectores CSS de eBay están sujetos a romperse ante cambios de la plataforma; no hay reintentos ni backoff ante bloqueos.
- **Commits:** `b329a24`, `91a5973`, `5308a3a`, `add4041`, `8541243` (8 sep 2026).

### Fase 7 — Control de frecuencia de consultas
- **Objetivo:** evitar volver a scrapear el mismo producto más de una vez al día, como primera medida de control de volumen de peticiones.
- **Entregado:** función `ya_se_consulto_hoy(conn, product_id)` en `database/schema.py`, que consulta la fecha del último registro en `Historial_Precios`.
- **Archivos/módulos:** `database/schema.py`.
- **Resultado:** función implementada, aunque **todavía no está siendo llamada desde ningún scraper ni desde un orquestador** (`main.py` sigue vacío).
- **Riesgos/limitaciones:** la consulta SQL filtra por `Historial_Precios.id = ?`, no por `producto_id`, lo cual parece no corresponder con la intención de la función (buscar el último registro de un producto específico); requiere confirmación y posible corrección por parte del autor (ver [Pendientes de documentar](#pendientes-de-documentar)).
- **Commits:** `cc825aa` (17 sep 2026).

### Fase 8 — Exploración de pivote a Amazon (en diseño, no comprometida al repositorio)
- **Objetivo:** evaluar reemplazar o complementar el scraper de eBay con uno para Amazon, dado el interés en un catálogo más amplio, e incorporar medidas de sigilo (`playwright-stealth`) y una reescritura a Playwright asíncrono.
- **Entregado:** *ningún archivo de esta fase está presente en el repositorio a la fecha de este README.* El trabajo se ha realizado como discusión de diseño y prototipos sueltos (scripts de prueba de conectividad contra Amazon, boceto de un `ScraperBase` asíncrono con verificación de fecha antes de abrir el navegador).
- **Archivos/módulos:** ninguno confirmado en el repositorio; se discutieron rutas propuestas como `scrapers/base.py` y `scrapers/amazon.py`, que **no coinciden con los nombres reales ya existentes** (`scrapers/BaseScraper.py`, `scrapers/EbayScraper.py`).
- **Resultado:** pruebas exploratorias fuera del repositorio indican que Playwright con `playwright-stealth` no fue bloqueado por Amazon en una consulta aislada de un solo producto; no se ha validado comportamiento bajo volumen sostenido.
- **Riesgos/limitaciones:** decisión de arquitectura no cerrada (¿se reemplaza eBay o se mantiene en paralelo?); inconsistencia pendiente entre Playwright síncrono (eBay, ya en el repo) y asíncrono (Amazon, en diseño); `playwright-stealth` no está en `requirements.txt`.
- **Commits:** ninguno — fase sin representación en el historial de git a la fecha.

## Decisiones técnicas y evolución del proyecto

| Decisión | Contexto | Alternativas consideradas | Motivo de elección | Consecuencias / trade-offs | Estado |
|---|---|---|---|---|---|
| Usar SQLite como base de datos | Proyecto personal, sin necesidad de servidor de base de datos dedicado | PostgreSQL, MySQL | Cero configuración, base de datos como archivo único, suficiente para el volumen esperado | No soporta bien concurrencia ni acceso remoto; adecuado solo mientras el proyecto no escale | Implementado |
| Enfocar el scraping en una sola tienda a la vez (eBay) en lugar de múltiples en paralelo | Intentos previos con Mercado Libre fallaron: `requests`+BeautifulSoup no capturaba contenido dinámico, la API pública devolvía 403, y Playwright tenía bloqueos y esperas largas | Mantener varios scrapers (Mercado Libre + eBay) en desarrollo simultáneo | Reducir complejidad y validar el flujo completo con una sola fuente antes de extender a otras tiendas | `EbayScraper` es hoy la única implementación concreta; el trabajo sobre Mercado Libre se descartó | Implementado (parcialmente en revisión por el pivote a Amazon en diseño) |
| Usar Playwright en vez de `requests` para obtener el HTML | El precio y título de productos se cargan vía JavaScript en Mercado Libre y eBay, y `requests` no ejecuta JS | `requests` + BeautifulSoup (insuficiente, ya probado), Selenium | Playwright soporta esperar contenido dinámico y tiene mejor camino hacia técnicas de sigilo | Dependencia más pesada (requiere instalar binarios de navegador); necesidad de manejar timeouts | Implementado |
| Ejecutar el navegador en modo headful (`headless=False`) en `BaseScraper` | Con `headless=True`, eBay devuelve una página de bloqueo genérica en vez del contenido real | Forzar `headless=True` con medidas de sigilo adicionales | Mientras no exista una solución de sigilo robusta integrada, el modo headful evita el bloqueo observado | No es viable para ejecución en segundo plano real (requiere entorno gráfico o `Xvfb`); mayor consumo de recursos | Solución temporal, pendiente de revisión |
| Verificar diariamente si un producto ya fue consultado, antes de scrapear de nuevo | Necesidad de controlar el volumen de peticiones para reducir el riesgo de bloqueo | Un archivo de log aparte; un scheduler con estado en memoria | Reutilizar la tabla `Historial_Precios` ya existente, sin infraestructura nueva | La consulta actual (`WHERE id = ?`) parece no filtrar correctamente por producto — pendiente de corrección | Implementado con un defecto pendiente de confirmar |
| Cachear las tasas de cambio en un archivo JSON local en lugar de consultar la API en cada ejecución | Evitar llamadas innecesarias a una API externa de tasas de cambio | Consultar siempre la API; guardar las tasas en una tabla SQLite | La tasa solo necesita actualizarse una vez al día; un JSON es más simple que una tabla para este caso de uso | Posible desfase de hasta un día si la tasa cambia intradía | Implementado |
| Adoptar Playwright asíncrono + `playwright-stealth` para el futuro scraper de Amazon | Se busca evitar el patrón de bloqueo visto con eBay y dejar la puerta abierta a concurrencia futura | Mantener Playwright síncrono (como en `EbayScraper`); usar la Product Advertising API oficial de Amazon | La API asíncrona es la recomendada por Playwright para uso con stealth y permite concurrencia sin reescribir la base | Introduce una inconsistencia de estilo (síncrono en eBay, asíncrono en Amazon) pendiente de unificar o justificar | En diseño, sin código en el repositorio |
| No duplicar el HTML scrapeado en archivos ni en otra base de datos | Se evaluó cachear el HTML por producto para depurar selectores sin re-scrapear | Guardar un `.html` por producto; crear una tabla o base de datos separada para el HTML crudo | Proyecto personal sin necesidad de escalar; el histórico relevante (precio) ya vive en SQLite | No queda registro de la página exacta que originó cada dato, lo que dificulta depurar selectores rotos retroactivamente | Decidido, sin código todavía en el repositorio |

## Licencia y créditos

No se encontró ningún archivo `LICENSE` en el repositorio. `TODO:` el autor debe definir y añadir una licencia explícita (por ejemplo, MIT, si el proyecto se comparte públicamente).

**Autor:** Thomas Chaparro (`thomasnoah3076-coder`), identificado como autor de la totalidad de los commits del repositorio.

## Pendientes de documentar

- **Nombres de archivo `___init__.py`** en `config/`, `database/` y `scrapers/` tienen tres guiones bajos en vez de dos (`___init__.py` en lugar de `__init__.py`), a diferencia de `services/__init__.py`, que sí está correcto. `TODO:` confirmar si es un error tipográfico o intencional.
- **Posible error funcional en `ya_se_consulto_hoy`** (`database/schema.py`): filtra por `Historial_Precios.id = ?` en vez de `producto_id = ?`, lo que no parece corresponder con el objetivo de "saber si un producto específico ya fue consultado hoy". `TODO:` confirmar con el autor y corregir si aplica.
- **`database/tracker.db` está versionado en git** con datos reales. `TODO:` decidir si se elimina del historial y se agrega `*.db` al `.gitignore`.
- **Versión de Python objetivo no especificada** (no hay `pyproject.toml` ni `.python-version`). `TODO:` confirmar la versión mínima soportada.
- **Proveedor real de la API de tasas de cambio no confirmado** — solo se infiere del formato de respuesta esperado (`conversion_rates`) en `services/currency.py`. `TODO:` documentar el proveedor exacto.
- **No existe `.env.example`** para facilitar el onboarding de nuevos colaboradores. `TODO:` crearlo con las claves listadas en la tabla de configuración, sin valores reales.
- **Estado real del pivote a Amazon**: existen discusiones de diseño avanzadas (Playwright asíncrono, `playwright-stealth`, verificación de fecha antes de abrir el navegador, un `ScraperBase` rediseñado), pero **nada de esto está comprometido al repositorio** a la fecha de este README. `TODO:` el autor debe decidir si continúa por esta vía y comprometer el código correspondiente.
- **Módulos mencionados en la documentación de contexto del proyecto pero inexistentes en el repositorio:** `notifications/telegram.py`, un analizador de ofertas, y cualquier orquestador real en `main.py`. `TODO:` confirmar si siguen planeados o si el alcance cambió.

## Resumen de cambios propuestos

- Se generó este README desde cero, reemplazando el contenido anterior (una guía genérica sobre entornos virtuales de Python) por documentación específica del proyecto, basada en inspección directa del código fuente y del historial de git del repositorio real.
- Se reconstruyeron 7 fases de desarrollo con evidencia de commits, más una octava fase (pivote a Amazon) documentada como "en diseño, sin código en el repositorio", para no dar la impresión de que ya está implementada.
- Se documentaron 8 decisiones técnicas con contexto, alternativas y trade-offs, incluyendo dos inconsistencias detectadas entre lo discutido en sesiones de diseño y lo realmente presente en el código (nombres de archivo de scraper, y síncrono vs. asíncrono en Playwright).
- Se dejaron señaladas explícitamente, con `TODO:`, todas las afirmaciones que requieren confirmación humana: versión de Python, proveedor de la API de tasas de cambio, posible bug en `ya_se_consulto_hoy`, ausencia de licencia, y el estado real (no comprometido) del scraper de Amazon.
- No se incluyeron secretos, tokens ni valores reales de variables de entorno en ningún ejemplo.
