# Especificación: Persistencia de Datos en SQLite

## 1. Objetivo (El Qué)
El orquestador guarda en `database/tracker.db` los datos que el scraper ya extrae y hoy descarta, de modo que cada consulta deje historial de precios. `main.py` abre una sola conexión compartida con `sqlite3.connect(DB_PATH_TRACKER)` y la inyecta en `BaseScraper.__init__(conn)`, de forma que todo el ciclo de vida de la base de datos pertenece al orquestador; `init_sqlite_db()` es la única excepción y trabaja con su propia conexión de inicialización antes de que empiece ese ciclo. `BaseScraper.obtener_datos(asin, url)` recibe siempre el ASIN —nunca el id interno—, lo traduce a `producto_id` con `buscar_id_producto`, valida los datos contra el Contrato §4, los convierte a moneda local y los persiste de forma atómica en `Productos`, `Historial_Precios` y `Metricas_Vendedor`, sin alterar el diccionario que retorna al llamador.

## 2. Motivación (El Por Qué)
Sin filas escritas la caché diaria nunca se activa y no existe el historial que consumirán el analizador de ofertas y las notificaciones. Esta etapa completa el Template Method —lectura y escritura de la base de datos en el orquestador— y mantiene al scraper especialista ajeno a SQLite.

Beneficios:
- Historial de precios por producto y por scrape.
- Caché diaria activa (`ya_se_consulto_hoy`).
- Base lista para el analizador de ofertas.
- Identidad estable por ASIN, sin duplicados.
- Histórico con precios en moneda local.

## 3. Propuesta Técnica
- **Componentes / Objetos:**
  - `sqlite3.Connection`: una sola conexión compartida, creada en `main.py` con `sqlite3.connect(DB_PATH_TRACKER)`, inyectada en `BaseScraper.__init__(conn)` y cerrada en el `finally` de `main.py`.
  - `init_sqlite_db()`: excepción al ciclo anterior; abre su propia conexión de inicialización a partir de `DB_PATH_TRACKER`, ejecuta el DDL, confirma y la cierra antes de que empiece el ciclo del orquestador. No recibe la conexión compartida.
  - `ContratoDatos`: dataclass de la librería estándar que tipa las 7 claves del Contrato (`titulo`, `precio`, `moneda`, `url`, `vendedor`, `ventas`, `calificacion_promedio`) y descarta claves ajenas.
  - Tabla `Productos`: `asin TEXT UNIQUE`, `titulo`, `url`, `vendedor` y `categoria` opcional.
  - Tabla `Historial_Precios`: una fila por scrape con `precio_local`, `moneda_local` y `precio_usd`; `precio_usd` contiene siempre USD por construcción, porque Amazon entrega USD, y las filas con precio en otra moneda quedan fuera de alcance de esta etapa.
  - Tabla `Metricas_Vendedor`: `nombre_vendedor` obligatoria, alimentada desde la clave `vendedor` del Contrato §4, junto con `total_ventas` y `calificacion_promedio`; la fila se inserta solo cuando `total_ventas` y `calificacion_promedio` no son `None`.
  - **Ubicación:** `ContratoDatos`, `init_sqlite_db`, `buscar_id_producto`, `obtener_o_crear_producto`, `insertar_historial_precio`, `insertar_metricas_vendedor`, `guardar_datos_producto`, `ya_se_consulto_hoy` y `obtener_ultimo_registro` residen en `database/esquema.py`. Todas las rutas se expresan desde la raíz del proyecto.
- **Métodos Principales:**
  - `async def obtener_datos(asin: str, url: str) -> dict`: punto de entrada del orquestador; el ASIN es el identificador de negocio en texto y es siempre el valor que recibe, nunca el id interno.
  - `init_sqlite_db() -> bool`: crea las tres tablas con `CREATE TABLE IF NOT EXISTS`, de modo que repetirla no altera datos; retorna `True` cuando el esquema queda válido y `False` cuando falta la columna `asin`. En el caso `False` imprime el aviso que indica regenerar `database/tracker.db` sin que el código borre nada, y `main.py` termina antes de llamar a `obtener_datos()`, para no ejecutar un `SELECT` sobre una tabla sin esa columna.
  - `guardar_datos_producto(conn, asin, datos, categoria=None) -> bool`: única fachada transaccional y único punto que ejecuta `commit` o `rollback` sobre la conexión compartida; un `commit` completo o `rollback` total, nunca propaga.
  - `ContratoDatos.filtrar_diccionario()` y `ContratoDatos.__post_init__()`: filtran claves ajenas (`origen`) y validan tipos en todos los campos, con dos comprobaciones de contenido: `precio > 0` y `moneda` no vacía. `titulo`, `url` y `vendedor` aceptan cadena vacía; solo el ASIN se rechaza vacío. La excepción de `moneda` se justifica porque un valor vacío rompe la conversión y el invariante de `precio_usd`.
  - `convertir_a_moneda_local(monto, moneda_origen)`: par precio/moneda local; sin conversión efectiva devuelve el par de origen.
  - `buscar_id_producto(conn, asin) -> int | None`: único traductor entre el ASIN y el id entero interno de `Productos`, o `None` si el producto no existe.
  - `obtener_o_crear_producto(...)`, `insertar_historial_precio(...)` e `insertar_metricas_vendedor(conn, producto_id, nombre_vendedor, total_ventas, calificacion_promedio) -> bool`: escrituras atómicas que operan sobre la conexión recibida sin abrir, cerrar ni confirmar.
  - `ya_se_consulto_hoy(conn, producto_id)` y `obtener_ultimo_registro(conn, producto_id)`: habilitan la caché diaria y el camino de lectura. `producto_id` es exclusivamente el id entero interno de `Productos`; la columna `fecha` se escribe con `CURRENT_TIMESTAMP` en UTC y `ya_se_consulto_hoy` la compara mediante `DATE(fecha, 'localtime')` contra la fecha local dada por `date.today()`.
  - `Historial_Precios` es de solo-anexado por decisión del Director, porque representa una serie temporal. Es la excepción explícita a la regla de upsert de la constitución §3: la ausencia de duplicados diarios depende exclusivamente de la guarda de caché del orquestador, y una llamada directa a `guardar_datos_producto` añade una fila por invocación.
- **Librerías / Dependencias:** `sqlite3`, `dataclasses` y `datetime` de la librería estándar; `../../services/divisas.py` (`convertir_a_moneda_local`) y `config/settings.py` (`DB_PATH_TRACKER`). Sin dependencias nuevas.
- **Flujo de Datos:**
  ```
  main.py: init_sqlite_db()            # conexión de inicialización propia: DDL, commit, close
      ├─ False → aviso + fin, sin abrir el navegador
      └─ True  → conn = sqlite3.connect(DB_PATH_TRACKER)
          → obtener_datos(asin, url)
          ├─ producto_id = buscar_id_producto(conn, asin)
          ├─ producto_id existe y ya_se_consulto_hoy(conn, producto_id)
          │     → obtener_ultimo_registro → origen "base_de_datos"
          ├─ extraer_datos(url) → 7 claves del Contrato → origen "scraping"
          └─ guardar_datos_producto(conn, asin, datos)
               1. ContratoDatos valida; inválido → aviso + False
               2. convertir_a_moneda_local(precio, moneda) → (precio_local, moneda_local)
               3. obtener_o_crear_producto → insertar_historial_precio → insertar_metricas_vendedor
               4. commit, o error → rollback + aviso + False
          → return datos (7 claves + origen)
          finally: conn.close()
  ```
  El camino de scraping construye `AmazonScraper(conn)` y lo ejecuta entre la apertura y el cierre de la conexión. La ejecución siguiente del mismo día encuentra la fila del historial y sirve el registro desde la base de datos sin abrir el navegador. Un fallo de extracción se manifiesta como la excepción con mensaje amigable que lanza `verificacion_de_estado_html` —respuesta HTTP distinta de 200 o HTML con indicadores de bloqueo—, que se propaga sin captura hasta `main.py`; es una excepción deliberada y acotada al ciclo de un solo producto frente a la degradación por lote de la constitución §4.

## 4. Criterios de Aceptación
- Ejecutar `main.py` con un producto nuevo escribe una fila en `Productos` y una fila por scrape en `Historial_Precios`; cuando el scraper entrega USD, `precio_usd` coincide con el precio extraído.
- Ejecutar `obtener_datos()` una segunda vez el mismo día para el mismo ASIN retorna `origen: "base_de_datos"` sin navegar y sin insertar filas nuevas, siempre que la primera escritura haya retornado `True`.
- Un scrape a las 21:00 locales del día X cuenta como consultado el día X y deja de contar el día X+1; la comparación de `fecha` usa la fecha local.
- Repetir el mismo ASIN no duplica la fila de `Productos` ni cambia su id, y el ASIN llega intacto a la fachada sin pasar por el id interno.
- `Metricas_Vendedor` recibe una fila solo cuando `total_ventas` y `calificacion_promedio` no son `None`, con `nombre_vendedor` tomado de `vendedor`; con datos incompletos el guardado retorna `True` y no inserta métricas.
- Con conversión efectiva, `Historial_Precios` guarda el monto convertido y `moneda_local` igual a la moneda local configurada; sin conversión, guarda el monto original con su moneda de origen, nunca la moneda local sobre un valor no convertido.
- Un diccionario inválido (`precio` no numérico, precio no positivo, claves obligatorias ausentes o `datos` sin ser dict), `moneda=""`, un ASIN vacío o una conexión inválida producen `False` con aviso por consola y cero filas escritas.
- Un fallo en cualquier paso de la escritura deja las tres tablas sin filas parciales, retorna `False` y no propaga la excepción; ese `False` deja solo el aviso por consola y no altera el diccionario que `obtener_datos()` retorna.
- El diccionario retornado por `obtener_datos()` contiene las mismas 7 claves más `origen` en los caminos de scraping y de base de datos, con independencia de que `guardar_datos_producto` retorne `True` o `False`.
- `init_sqlite_db()` puede ejecutarse varias veces seguidas sin errores ni pérdida de datos y retorna `True`; sobre una base existente sin la columna `asin` retorna `False`, el aviso por consola nombra la columna `asin` e indica regenerar `database/tracker.db`, y `main.py` termina sin invocar `obtener_datos()` y sin abrir el navegador.
- Un fallo de extracción del ciclo de un solo producto se propaga como la excepción con mensaje amigable de `verificacion_de_estado_html`, no escribe ninguna fila y no se imprime ningún aviso adicional desde el flujo de persistencia.
