# comparador-precios

Rastreador de precios de Amazon escrito en Python: consulta un producto, guarda su historial en SQLite y compara el precio contra el histórico para detectar ofertas. Las notificaciones por Telegram están planificadas.

Proyecto personal de un solo desarrollador. **Estado: prototipo.** El flujo *scraping → base de datos* funciona de extremo a extremo; el analizador de ofertas está en implementación y las notificaciones no existen todavía.

## Qué hace

**Funciona hoy**
- Scrapea un producto de Amazon con Playwright (Chromium headless) y `playwright-stealth`, fija la entrega en Miami para el *buybox* y detecta bloqueos (CAPTCHA, HTTP ≠ 200) antes de extraer.
- Persiste cada consulta en SQLite en una sola transacción: producto, fila de historial y métricas del vendedor.
- Convierte el precio a COP y guarda también el original en USD.
- Cachea las tasas de cambio en un JSON que se renueva una vez al día.
- Evita repetir el scrape de un producto ya consultado el mismo día: devuelve la fila guardada.

**Todavía no**
- **Analizador de ofertas** (`services/analizador.py`, spec 002): comparará el precio actual con el mínimo histórico y aplicará `UMBRAL_CAIDA_PRECIO = 0.15`.
- Notificaciones por Telegram (`python-telegram-bot` está instalado pero ningún módulo lo usa).
- Delays aleatorios, rotación de User-Agent y proxies residenciales.
- Ejecución programada (scheduler).

## Stack

| Tecnología | Uso |
|---|---|
| Python 3.14 | Lenguaje del proyecto |
| SQLite (`sqlite3`, stdlib) | Productos, historial de precios, métricas de vendedor |
| Playwright (async) | Renderiza el HTML dinámico de Amazon |
| BeautifulSoup4 | Extrae los datos del DOM ya renderizado |
| playwright-stealth | Mitiga la detección de automatización |
| requests | Consulta la API de tasas de cambio |
| python-dotenv | Carga las variables de `.env` |
| pytest | Baterías de pruebas temporales |

## Arquitectura

Patrón **Template Method**: el orquestador maneja la infraestructura y el especialista solo conoce los selectores de la tienda.

```
                    main.py  (asyncio.run)
                        │
                        ▼
        ┌────────────────────────────────┐
        │ BaseScraper                    │  scrapers/BaseScraper.py
        │  obtener_datos()  → orquesta   │  Playwright, caché, BD
        │  obtener_dom()    → HTML       │
        └───────────────┬────────────────┘
                        │ hereda · extraer_datos() es abstracto
                        ▼
        ┌────────────────────────────────┐
        │ AmazonScraper                  │  scrapers/AmazonScraper.py
        │  solo selectores del DOM       │
        └────────────────────────────────┘

obtener_datos(producto_id, url)
   ├─ ¿consultado hoy? → ya_se_consulto_hoy() → fila de la BD
   └─ no → extraer_datos() → guardar_datos_producto() → SQLite
                                 └─ convertir_a_moneda_local() (COP)
```

**Flujo de datos**

1. `main.py` define el ASIN y la URL del producto, abre la conexión e inicializa el esquema.
2. `obtener_datos()` comprueba si el producto ya se consultó hoy; si es así devuelve el último registro (`origen: base_de_datos`).
3. Si no, `AmazonScraper.extraer_datos()` renderiza la página y devuelve las siete claves del contrato: `titulo`, `precio`, `moneda`, `url`, `vendedor`, `ventas`, `calificacion_promedio`.
4. `guardar_datos_producto()` convierte el precio a la moneda local, inserta el producto (`INSERT OR IGNORE` por `asin`), añade una fila al historial y registra las métricas si vienen completas. Todo en una transacción con `commit`/`rollback`.
5. *Pendiente:* el analizador decidirá si el precio actual es una oferta y un módulo de notificaciones enviará el aviso a Telegram.

**Esquema** ([`database/schema.py`](database/schema.py), idempotente con `CREATE TABLE IF NOT EXISTS`)

- `Productos` — identidad del artículo: `asin` (único), `titulo`, `url`, `vendedor`, `categoria` (opcional).
- `Historial_Precios` — *append-only*: `precio_local`, `moneda_local`, `precio_usd`, `fecha`.
- `Metricas_Vendedor` — `nombre_vendedor`, `total_ventas`, `calificacion_promedio`, `fecha_registro`.

## Estructura del proyecto

```
comparador-precios/
├── config/settings.py         # Rutas, .env, UMBRAL_CAIDA_PRECIO
├── database/schema.py         # Esquema, helpers de lectura y fachada transaccional
├── database/tracker.db        # Base de datos SQLite (versionada, ver más abajo)
├── scrapers/BaseScraper.py    # Orquestador: Playwright, caché diaria, persistencia
├── scrapers/AmazonScraper.py  # Selectores y extracción del DOM de Amazon
├── services/currency.py       # Conversión COP↔USD con caché diario
├── main.py                    # Punto de entrada
├── docs/constitution.md       # Reglas de desarrollo del proyecto
├── MEMORY.md / AGENTS.md      # Estado actual y guía para agentes de IA
└── requirements.txt
```

## Instalación

```bash
git clone https://github.com/thomasnoah3076-coder/comparador-precios.git
cd comparador-precios

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium

python -m database.schema          # crea las tablas (seguro de repetir)
```

Después crea un `.env` en la raíz con las variables de la tabla siguiente (no existe `.env.example` todavía).

## Configuración

| Variable | Uso |
|---|---|
| `LOCAL_CURRENCY` | Moneda de visualización (`COP`). Si falta o está vacía, se guarda el precio en USD |
| `EXCHANGE_RATE_API_KEY` | Clave de la API de tasas de cambio |
| `EXCHANGE_RATE_API_URL` | URL de la API (respuesta esperada: `conversion_rates.COP`) |
| `TELEGRAM_BOT_TOKEN` | Token del bot (aún sin uso) |
| `TELEGRAM_CHAT_ID_GENERAL` · `_PERFUMES` · `_TECNOLOGIA` | Chat por categoría (aún sin uso) |

Constantes fijas en [`config/settings.py`](config/settings.py):

| Constante | Valor | Significado |
|---|---|---|
| `DB_PATH_TRACKER` | `database/tracker.db` | Base de datos |
| `RUTA_TASAS_CAMBIO` | `database/tasas_cambio.json` | Caché del día: `{"fecha", "COP", "USD"}`, se sobrescribe |
| `UMBRAL_CAIDA_PRECIO` | `0.15` | Caída mínima (15 %) para considerar una oferta |

## Uso

| Comando | Qué hace |
|---|---|
| `python -m database.schema` | Crea las tres tablas (idempotente) |
| `python main.py` | Consulta de extremo a extremo; edita `PRODUCT_ID` y `URL_PRODUCTO` al inicio del archivo |
| `python -m services.analizador <ASIN>` | *Pendiente*: veredicto de oferta de un producto |

Ejecuta siempre desde la **raíz del proyecto** con `-m`: los módulos se importan como paquetes y `python scrapers/BaseScraper.py` falla (`python database/schema.py` sí funciona por su arranque de ruta condicionado).

Para usar el conversor desde otro script:

```python
from services.currency import convertir_moneda

convertir_moneda(100, "USD", "COP")   # solo USD ↔ COP; si falla la API devuelve el monto original
```

## Problemas frecuentes

- **`ModuleNotFoundError: No module named 'config'`** — estás ejecutando el archivo por ruta desde otro directorio. Usa `python -m ...` desde la raíz.
- **Amazon devuelve un CAPTCHA (`Robot Check`) o un HTTP distinto de 200** — `verificacion_de_estado_html()` lanza antes de extraer, para no guardar datos nulos. Si es sostenido, reduce la frecuencia de consulta.
- **No aparece el precio principal (solo «15 opciones desde…»)** — el precio del *buybox* depende de la ubicación de entrega (Miami, ZIP 33122). Ese paso es *best-effort*: si falla, se avisa por consola y se continúa.
- **`JSONDecodeError` o respuesta rara al convertir divisas** — la caché corrupta se autorregenera sola; si la API falla, se imprime el motivo y se devuelve el monto sin convertir.
- **`ImportError: cannot import name 'stealth_async'`** — `playwright-stealth` 2.x usa `Stealth().apply_stealth_async(page)`; la función `stealth_async` era de la 1.x.

## Calidad, pruebas y seguridad

- **No hay `tests/` versionado ni CI**, ni linters o cobertura configurados. Las baterías se crean como archivos temporales aislados (sin red ni acceso a `tracker.db`), se ejecutan y se borran si pasan (ver `AGENTS.md` §6.4). `pytest` está en `requirements.txt`: `.venv/bin/python -m pytest`.
- `.env` está excluido por `.gitignore`; no hay credenciales en el código.
- **`database/tracker.db` está versionado en git**, así que los datos scrapeados quedan en el historial del repositorio. Pendiente decidir si se retira del control de versiones.
- El proyecto automatiza un sitio de terceros: la decisión de con qué frecuencia scrapear es responsabilidad del mantenedor.

## Roadmap y decisiones

**Hecho**

- [x] Esquema SQLite (`Productos`, `Historial_Precios`, `Metricas_Vendedor`)
- [x] Conversión COP↔USD con caché diario en JSON
- [x] `BaseScraper` con Playwright async, stealth y detección de bloqueos
- [x] `AmazonScraper` con detección de CAPTCHA y ubicación Miami
- [x] Persistencia transaccional y caché diaria por producto
- [x] Punto de entrada `main.py` de extremo a extremo

**Pendiente**

- [ ] Analizador de ofertas contra el mínimo histórico (spec 002)
- [ ] Notificaciones por Telegram
- [ ] Control de volumen: delays, User-Agents, proxies
- [ ] Ejecución programada

**Decisiones clave**

- **SQLite**: cero configuración y archivo único; suficiente para un usuario.
- **Playwright en lugar de `requests`**: los precios se cargan con JavaScript, y `requests` no lo ejecuta.
- **Headless + stealth + ubicación Miami**: evita los bloqueos que aparecían con navegación normal.
- **Un marketplace a la vez**: se validó el flujo completo con Amazon antes de añadir fuentes nuevas.
- **Caché de tasas en JSON**: la tasa cambia una vez al día; un objeto único es más simple que una tabla.
- **Errores con `print`**: proyecto personal, sin `logging` por ahora.

**Pendiente de documentar:** `.env.example` con las claves sin valores, proveedor real de la API de tasas y versión de Python (`.python-version`).

## Autor

Thomas Chaparro ([`thomasnoah3076-coder`](https://github.com/thomasnoah3076-coder)).
