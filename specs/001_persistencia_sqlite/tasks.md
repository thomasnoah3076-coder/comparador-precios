# Tareas de Implementación

## Dependencias y Arquitectura

	- **Librerías:** `sqlite3` (stdlib), `dataclasses` (stdlib: `dataclass`, `fields`), `datetime` (stdlib: `date`), `time` (stdlib: `tzset`, para fijar la zona horaria de las pruebas de fecha), `asyncio` (stdlib: `asyncio.run`), `config.settings` (`DB_PATH_TRACKER`, `DEFAULT_CURRENCY`), `services.currency` (`convertir_a_moneda_local`, `convertir_moneda`, `DEFAULT_CURRENCY`), `unittest.mock` (stdlib: `Mock`; `monkeypatch` como fixture de pytest), `pytest` (batería temporal aislada).
- **Objetos / Modelos:** `ContratoDatos` (dataclass de validación), tablas `Productos`, `Historial_Precios` y `Metricas_Vendedor`, objetos `sqlite3.Connection` (una sola conexión compartida entre `main`, `BaseScraper` y la fachada), diccionario del Contrato §4 (`titulo`, `precio`, `moneda`, `url`, `vendedor`, `ventas`, `calificacion_promedio`) y diccionario de retorno con `origen`.
- **Métodos Globales:** `init_sqlite_db`, `ContratoDatos.filtrar_diccionario`, `ContratoDatos.__post_init__`, `convertir_a_moneda_local`, `convertir_moneda`, `buscar_id_producto`, `obtener_o_crear_producto`, `insertar_historial_precio`, `insertar_metricas_vendedor`, `guardar_datos_producto`, `ya_se_consulto_hoy`, `obtener_ultimo_registro`, `BaseScraper.__init__(conn)`, `BaseScraper.obtener_datos`, `BaseScraper.extraer_datos`, `main`.

## Tarea Principal 1: Esquema de la base de datos y contrato tipado

### Subtarea 1.1: `init_sqlite_db` — esquema de `Productos` y aviso de esquema antiguo
Flujo de comportamiento:
1. Abrir la conexión con `sqlite3.connect(DB_PATH_TRACKER)`, con la ruta importada de `config.settings`.
2. Ejecutar con `executescript` las tres sentencias `CREATE TABLE IF NOT EXISTS`: `Productos`, `Historial_Precios` y `Metricas_Vendedor`.
3. Definir `Productos` con `id INTEGER PRIMARY KEY AUTOINCREMENT`, `asin TEXT UNIQUE`, `titulo TEXT NOT NULL`, `url TEXT NOT NULL`, `vendedor TEXT NOT NULL`, `categoria TEXT` (nullable) y `fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP`.
4. Mantener `Historial_Precios` (`producto_id`, `precio_local`, `moneda_local`, `precio_usd`, `fecha`, foránea a `Productos`) y `Metricas_Vendedor` (`producto_id`, `nombre_vendedor`, `total_ventas`, `calificacion_promedio`, `fecha_registro`, foránea a `Productos`) sin cambios de columnas.
5. Consultar `PRAGMA table_info(Productos)` y comprobar únicamente la presencia de la columna `asin`.
6. Si falta `asin`, imprimir un aviso de esquema antiguo que indique regenerar `database/tracker.db`, sin borrar tablas ni datos.
7. Cerrar con `commit()` y `close()`, de modo que repetir la inicialización no altere ni duplique nada.

### Subtarea 1.2: `ContratoDatos` — definición de la dataclass
Flujo de comportamiento:
1. Declarar `ContratoDatos` con `@dataclass` en `database/schema.py`.
2. Declarar los siete campos con el mismo nombre y orden del Contrato §4: `titulo: str`, `precio: float`, `moneda: str`, `url: str`, `vendedor: str`.
3. Declarar `ventas: int | None = None` y `calificacion_promedio: float | None = None` con default explícito, para que un diccionario que omita esas claves se construya sin `TypeError` y el precio no se pierda.
4. Mantener la clase como validación interna del repositorio: el contrato público de `obtener_datos()` sigue siendo `dict`.

### Subtarea 1.3: `ContratoDatos.filtrar_diccionario` — conversión del diccionario al contrato
Flujo de comportamiento:
1. Recibir `datos: dict` como `classmethod` de `ContratoDatos`.
2. Verificar `isinstance(datos, dict)`; si no se cumple, lanzar `TypeError("Datos inválidos: se esperaba un diccionario")`.
3. Obtener los nombres válidos con `fields(cls)` de `dataclasses`.
4. Construir un diccionario solo con las claves del contrato, descartando `origen` y cualquier clave ajena.
5. Retornar `cls(**datos_filtrados)` y delegar la validación de tipos y valores a `__post_init__`; las claves ausentes opcionales toman su default `None`.

### Subtarea 1.4: `ContratoDatos.__post_init__` — validación de tipos y valores
Flujo de comportamiento:
1. Recorrer `titulo`, `moneda`, `url` y `vendedor`; si alguno no es `str`, lanzar `TypeError` indicando el nombre del campo.
2. Rechazar `bool` y los tipos no numéricos en `precio` con `TypeError`, y normalizar el valor aceptado a `float`.
3. Exigir `precio > 0` y lanzar `ValueError` en caso contrario (cero y negativos se consideran fallo de extracción).
4. Validar `ventas` como `int` que no sea `bool` únicamente cuando no sea `None`.
5. Validar `calificacion_promedio` como numérica que no sea `bool` únicamente cuando no sea `None`, normalizándola a `float`.
6. Lanzar siempre `TypeError` o `ValueError` en los rechazos, porque el valor retornado por `__post_init__` no cancela la construcción de la dataclass.

## Tarea Principal 2: Conversión a moneda local

### Subtarea 2.1: `convertir_a_moneda_local` — par precio/moneda para persistir
Flujo de comportamiento:
1. Importar `DEFAULT_CURRENCY` desde `config.settings` dentro de `services/currency.py`.
2. Si `DEFAULT_CURRENCY` es `None` o `""`, imprimir el aviso de conversión no disponible y retornar `(monto, moneda_origen)` sin acceder a la red.
3. Invocar `convertir_moneda(monto, moneda_origen, DEFAULT_CURRENCY)`, que ya degrada devolviendo el monto cuando la pareja no está soportada o la API falla.
4. Aplicar la regla de verdad: si el valor convertido es igual a `monto`, retornar `(monto, moneda_origen)` como fallback honesto.
5. En caso contrario, retornar `(monto_convertido, DEFAULT_CURRENCY)`.
6. No añadir `try/except`: la función delegada no propaga excepciones y la composición debe mantenerse legible.

## Tarea Principal 3: Repositorio de escritura en `database/schema.py`

### Subtarea 3.1: `buscar_id_producto` — resolución de ASIN a id entero
Flujo de comportamiento:
1. Recibir `conn: sqlite3.Connection` y `asin: str`.
2. Crear el cursor y ejecutar `SELECT id FROM Productos WHERE asin = ?` con el ASIN como parámetro.
3. Leer `fetchone()`; si no hay fila, retornar `None` de forma explícita.
4. Retornar el primer elemento de la fila como `int`.
5. No lanzar excepción por "producto no encontrado" y no escribir en la base de datos.

### Subtarea 3.2: `obtener_o_crear_producto` — identidad estable por ASIN
Flujo de comportamiento:
1. Recibir `conn`, `asin`, `titulo`, `url`, `vendedor` y `categoria: str | None = None`.
2. Ejecutar `INSERT OR IGNORE INTO Productos (asin, titulo, url, vendedor, categoria) VALUES (?, ?, ?, ?, ?)`: la sentencia garantiza una sola fila por ASIN y conserva la identidad del producto, y no actualiza metadatos (`titulo`, `url`, `vendedor`, `categoria`) en esta especificación.
3. Ejecutar `SELECT id FROM Productos WHERE asin = ?` para leer la fila existente o la recién creada.
4. Retornar el `id` entero obtenido.
5. No ejecutar `commit`: la transacción la cierra la fachada, de modo que un fallo posterior pueda revertirse.

### Subtarea 3.3: `insertar_historial_precio` — fila de precio por scrape
Flujo de comportamiento:
1. Recibir `conn`, `producto_id`, `precio_local`, `moneda_local` y `precio_usd`.
2. Ejecutar `INSERT INTO Historial_Precios (producto_id, precio_local, moneda_local, precio_usd) VALUES (?, ?, ?, ?)`.
3. Asignar `precio_local` y `moneda_local` al par devuelto por la conversión, y `precio_usd` al precio original del scraper.
4. Delegar la fecha al valor `DEFAULT CURRENT_TIMESTAMP` de la tabla.
5. No ejecutar `commit`.
6. No deduplicar por fecha: el historial es append-only por diseño, excepción aprobada por el Director para construir la serie temporal, de modo que cada scrape escribe su propia fila aunque ocurra el mismo día.

### Subtarea 3.4: `insertar_metricas_vendedor` — métricas solo con datos completos
Flujo de comportamiento:
1. Recibir `conn`, `producto_id`, `nombre_vendedor`, `total_ventas` y `calificacion_promedio`.
2. Si `total_ventas` o `calificacion_promedio` son `None`, retornar `False` sin ejecutar sentencia alguna, respetando los `NOT NULL` y sin inventar ceros.
3. Ejecutar `INSERT INTO Metricas_Vendedor (producto_id, nombre_vendedor, total_ventas, calificacion_promedio) VALUES (?, ?, ?, ?)`.
4. Retornar `True` cuando la fila se insertó.
5. No ejecutar `commit`.

### Subtarea 3.5: `guardar_datos_producto` — fachada transaccional de escritura
Flujo de comportamiento:
1. Recibir `conn`, `asin: str`, `datos: dict` y `categoria: str | None = None`.
2. Validar que `asin` sea `str` no vacío y que `conn` no sea `None`; si falla, imprimir el aviso correspondiente y retornar `False`.
3. Convertir `datos` con `ContratoDatos.filtrar_diccionario`, capturando `TypeError` y `ValueError` mediante el bloque de excepción general.
4. Calcular `precio_local, moneda_local = convertir_a_moneda_local(verificador_datos.precio, verificador_datos.moneda)` antes de iniciar la transacción, para que un fallo de divisas no arrastre un `rollback`.
5. Llamar `obtener_o_crear_producto` con `asin`, `titulo`, `url`, `vendedor` y `categoria`, y conservar el `producto_id` retornado.
6. Llamar `insertar_historial_precio` con `producto_id`, `precio_local`, `moneda_local` y el `precio` original como `precio_usd`.
7. Llamar `insertar_metricas_vendedor` con `producto_id`, `vendedor`, `ventas` y `calificacion_promedio`, registrando que un `False` corresponde a la omisión deliberada de la fila cuando faltan métricas (Decisión 3).
8. Ejecutar `conn.commit()` y retornar `True` cuando `Productos` e `Historial_Precios` se completaron y el `commit` tuvo éxito; la omisión de `Metricas_Vendedor` no convierte el resultado en `False`.
9. Ante cualquier excepción, ejecutar `conn.rollback()` dentro de un `try/except` propio que absorba fallos de la conexión, imprimir el aviso con el mensaje de la excepción y retornar `False` sin propagar.

## Tarea Principal 4: Lecturas que alimentan la caché diaria

### Subtarea 4.1: `ya_se_consulto_hoy` — comparación de fecha del último scrape
Flujo de comportamiento:
1. Recibir `conn` y `producto_id: int | None`.
2. Ejecutar `SELECT DATE(fecha, 'localtime') FROM Historial_Precios WHERE producto_id = ? ORDER BY fecha DESC LIMIT 1`, de modo que la comparación ocurra en una sola base temporal: `fecha` se escribe con `CURRENT_TIMESTAMP` (UTC) y se normaliza a local antes de comparar.
3. Si no hay fila o el valor es `None`, retornar `False`.
4. Comparar el valor retornado con `date.today().isoformat()`, que ya está en la misma base local, sin volver a convertir.
5. Retornar el resultado booleano de la comparación.

### Subtarea 4.2: `obtener_ultimo_registro` — registro servido desde la base de datos
Flujo de comportamiento:
1. Recibir `conn` y `producto_id: int | None`.
2. Ejecutar el `SELECT` sobre `Productos p` con subconsultas al último `precio_usd` de `Historial_Precios`, y al último `total_ventas` y `calificacion_promedio` de `Metricas_Vendedor`.
3. Seleccionar las columnas `p.titulo`, `p.url` y `p.vendedor` y usar `id = ?` como filtro.
4. Servir el precio como `precio` y la moneda como `"USD"` fija, porque el precio devuelto es el original que produce `AmazonScraper` (solo USD) y el diccionario de `obtener_datos()` no expone COP; `precio_local` y `moneda_local` quedan reservados al histórico.
5. Si no hay fila, retornar un diccionario con las siete claves del Contrato §4 en `None`.
6. Si hay fila, retornar el diccionario con exactamente las claves `titulo`, `precio`, `moneda`, `url`, `vendedor`, `ventas` y `calificacion_promedio`, con las mismas claves y la misma moneda que el camino de scraping.

## Tarea Principal 5: Orquestación de la persistencia en `BaseScraper`

### Subtarea 5.1: `BaseScraper.obtener_datos` — resolución de identidad y caché diaria
			 Flujo de comportamiento:
1. Mantener la firma `async def obtener_datos(self, product_id: str, url: str) -> dict`, donde `product_id: str` es el ASIN por compatibilidad con la firma pública del plan.
2. Resolver el identificador con `buscar_id_producto(self.conn, product_id)` (el `producto_id` recibido es el ASIN de `main.py`).
3. Si el identificador no es `None` y `ya_se_consulto_hoy(self.conn, identificador)` es `True`, obtener `registro = obtener_ultimo_registro(self.conn, identificador)`.
4. Añadir `registro["origen"] = "base_de_datos"` y retornar el registro sin abrir el navegador.
5. Si el identificador es `None` o la caché está vencida, continuar con la extracción, evitando cualquier consulta de caché sobre un identificador nulo.

### Subtarea 5.2: `BaseScraper.obtener_datos` — extracción, persistencia best-effort y retorno
Flujo de comportamiento:
1. Obtener `datos = await self.extraer_datos(url)`, que realiza una única navegación y devuelve el Contrato §4.
2. Asignar `datos["origen"] = "scraping"`.
3. Invocar `guardar_datos_producto(self.conn, product_id, datos)` pasando el ASIN explícito como segundo argumento y dejando que `categoria` tome su default `None`, porque `obtener_datos` no recibe categoría y no se inventa un valor; descartar deliberadamente el `bool` retornado.
4. Imprimir o no el aviso de fallo desde la fachada, sin interrumpir el flujo del orquestador.
5. Retornar `datos` con las siete claves y `origen`, de forma que el consumidor reciba las mismas claves que en el camino de base de datos.
6. Si `extraer_datos` lanza una excepción, dejarla subir a `main.py` sin persistir nada.

## Tarea Principal 6: Arranque y regeneración de la base de datos

### Subtarea 6.1: `main` — inicialización del esquema y ejecución del ciclo completo
Flujo de comportamiento:
1. Importar `asyncio`, `init_sqlite_db` desde `database.schema` y `DB_PATH_TRACKER` desde `config.settings`.
2. Abrir `conn = sqlite3.connect(DB_PATH_TRACKER)`.
3. Llamar `init_sqlite_db()` antes de cualquier lectura o escritura para garantizar el esquema con `asin`.
4. Retirar de `main.py` el bloque `PRAGMA table_info(Productos)` con su aviso de esquema antiguo y el `print` de depuración de columnas: esa validación queda solo en `init_sqlite_db`.
5. Definir o restaurar `PRODUCT_ID` (ASIN) y `URL_PRODUCTO` como constantes del módulo.
6. Instanciar `AmazonScraper(conn)`, de modo que `BaseScraper.__init__(conn)` comparta la misma conexión de lectura y escritura con `obtener_datos`.
7. Ejecutar `asyncio.run(AmazonScraper(conn).obtener_datos(PRODUCT_ID, URL_PRODUCTO))` e imprimir el diccionario devuelto con las siete claves y `origen`.
8. Depender de las Subtareas 5.1 y 5.2, que son las que escriben en la base de datos y cierran el ciclo.

### Subtarea 6.2: `tracker.db` — regeneración con el esquema nuevo
Flujo de comportamiento:
1. Verificar que las tres tablas de `database/tracker.db` están vacías antes de tocarlas.
2. Eliminar el archivo `database/tracker.db`.
3. Ejecutar `init_sqlite_db()` para crear el archivo con las columnas `asin`, `titulo` y `categoria` en `Productos`.
4. Confirmar con `PRAGMA table_info(Productos)` que la columna `asin` existe, sin ejecutar migraciones `ALTER TABLE`.

## Tarea Principal 7: Verificación aislada

### Subtarea 7.1: Comprobación de esquema e idempotencia del ASIN
Flujo de comportamiento:
1. Fijar la ruta de prueba con `monkeypatch.setattr(database.schema, "DB_PATH_TRACKER", str(tmp_path / "tracker.db"))` antes de inicializar y abrir la conexión temporal, sin tocar `database/tracker.db`, porque `init_sqlite_db()` no recibe ruta y usa la importada a nivel de módulo; aislar además la conversión de divisas con `monkeypatch.setattr(services.currency, "DEFAULT_CURRENCY", "")` antes de cualquier guardado, de modo que `convertir_a_moneda_local` retorne el par de origen sin `requests.get` y sin escribir `database/tasas_cambio.json`.
2. Ejecutar `init_sqlite_db()` dos veces seguidas y comprobar que las tablas persisten sin error.
3. Insertar el mismo ASIN dos veces con `obtener_o_crear_producto` y verificar una sola fila en `Productos` con el mismo `id`.
4. Ejecutar `guardar_datos_producto` dos veces, con `DEFAULT_CURRENCY` anulado, y verificar dos filas en `Historial_Precios` para el mismo `producto_id`, porque el historial es append-only por diseño y no se deduplica por fecha.

### Subtarea 7.2: Comprobación de atomicidad y contrato inválido
Flujo de comportamiento:
1. Provocar un fallo en una de las funciones internas, con `services.currency.DEFAULT_CURRENCY` anulado para que la conversión no salga a la red, y verificar que el conteo de filas en las tres tablas queda en cero tras el `rollback`.
2. Verificar el resultado `False` cuando el diccionario llega sin claves obligatorias, con `precio` no numérico o con `precio` menor o igual a cero.
3. Verificar el resultado `False` con `datos=None`, con `datos` en forma de lista y con `conn` cerrada, manteniendo `DEFAULT_CURRENCY` anulado porque la conversión ocurre antes de tocar la base de datos.
4. Confirmar que la conexión nunca propaga la excepción de escritura.

### Subtarea 7.3: Comprobación de métricas opcionales y conversión
Flujo de comportamiento:
1. Guardar un contrato con `ventas` o `calificacion_promedio` en `None` explícito, con `DEFAULT_CURRENCY` anulado, y verificar `True` con cero filas en `Metricas_Vendedor`.
2. Guardar un diccionario que omite por completo las claves `ventas` y `calificacion_promedio`, con `DEFAULT_CURRENCY` anulado, y verificar que la dataclass las resuelve por su default `None`, que el resultado es `True` y que el precio queda en `Historial_Precios` con cero filas en `Metricas_Vendedor`.
3. Guardar un contrato con ambas métricas, con `DEFAULT_CURRENCY` anulado, y verificar una fila en `Metricas_Vendedor`.
4. Con `monkeypatch.setattr(services.currency, "DEFAULT_CURRENCY", "")`, verificar que `Historial_Precios` guarda el par origen sin etiquetar `COP`.
5. Con `monkeypatch.setattr(services.currency, "DEFAULT_CURRENCY", "COP")` y `monkeypatch.setattr(services.currency, "convertir_moneda", Mock(...))`, verificar que `precio_local` es el valor convertido y `moneda_local` es `COP`, sin acceso a red; el parcheo se aplica sobre `services.currency` y no sobre `config.settings`, porque ese módulo liga `DEFAULT_CURRENCY` y `convertir_moneda` al importarse y el valor ya ligado no cambia; cualquier prueba que ejercite la conversión real debe apuntar `services.currency.RUTA_TASAS_CAMBIO` a `tmp_path` para no escribir `database/tasas_cambio.json`.

### Subtarea 7.4: Comprobación del ciclo completo, bordes de fecha y limpieza
Flujo de comportamiento:
1. Ejecutar `py_compile` sobre `database/schema.py`, `services/currency.py`, `scrapers/BaseScraper.py` y `main.py`.
2. Fijar la ruta temporal con `monkeypatch.setattr(database.schema, "DB_PATH_TRACKER", str(tmp_path / "tracker.db"))` y abrir la conexión de prueba.
3. Parchear el destino real con `monkeypatch.setattr` sobre `scrapers.AmazonScraper.AmazonScraper.extraer_datos` o sobre el atributo homónimo de la instancia bajo prueba, que es `AmazonScraper` y no `BaseScraper`: la subclase sobrescribe el método, así que parchear `BaseScraper.extraer_datos` no intercepta `self.extraer_datos(url)` y la prueba navegaría de verdad a Amazon. Ejecutar `AmazonScraper(conn).obtener_datos` con la base de datos temporal y `services.currency.DEFAULT_CURRENCY` anulado, verificando el origen `scraping` y las filas persistidas con el par de moneda de origen.
4. Ejecutar `obtener_datos` una segunda vez el mismo día, con el mismo mock y `DEFAULT_CURRENCY` anulado, y verificar `origen` igual a `base_de_datos` sin nueva navegación ni nueva escritura.
5. Comparar las claves del diccionario devuelto en ambos caminos, verificar que coinciden y que la moneda es `"USD"` en los dos, igual que el precio original.
6. Fijar la base temporal de la prueba de fecha con `monkeypatch.setenv("TZ", "America/Bogota")` y `time.tzset()`, y calcular la fecha local esperada a partir del offset UTC de cada hora insertada, para que el borde UTC→local exista de verdad en lugar de coincidir con la fecha UTC.
7. Insertar solo el scrape nocturno del producto A con la `fecha` explícita, porque `insertar_historial_precio` delega en `DEFAULT CURRENT_TIMESTAMP`: un `TIMESTAMP` UTC equivalente a las 21:00 locales del día X (02:00 UTC del día X+1). Con `database.schema.date` parcheado al día local X, verificar que `ya_se_consulto_hoy(conn, id_producto_a)` devuelve `True`; con el día X+1, verificar que devuelve `False`.
8. Insertar la mañana siguiente (07:00 locales del día X+1) para un producto/ASIN B distinto y verificar `True` con `date` fijado en X+1, evaluando fila por fila y por producto: `ya_se_consulto_hoy` filtra por `producto_id` y lee la última fila (`ORDER BY fecha DESC LIMIT 1`), así que usar un segundo producto evita que la fila de B oculte la de A.
9. Ejecutar toda la batería con `pytest` fuera de la base de datos real, sin acceso a red y sin escribir archivos del proyecto.
10. Si todo pasa, eliminar los archivos temporales, `__pycache__` y `.pytest_cache`; si algo falla, conservarlos junto con las trazas para su revisión.

## Tarea Principal 8: Cierre documental

Depende de la Tarea Principal 7 con la batería en verde.

### Subtarea 8.1: `MEMORY.md` — estado del roadmap
Flujo de comportamiento:
1. Registrar el paso 3 ("Conectar Retorno con SQLite") como completado en §5 y actualizar el apartado "En Progreso".
2. Añadir en §3 el registro de la ronda correspondiente: columna `asin` y esquema regenerado, fachada transaccional única, conversión a COP con fallback honesto y anulación de la Decisión 2.
3. Mantener §4 sin cambios: el contrato sigue con las siete claves y el valor en COP vive solo en la base de datos.

### Subtarea 8.2: `README.md` — árbol, esquema y roadmap
Flujo de comportamiento:
1. Actualizar el árbol de archivos y el esquema SQL de `Productos` con `asin`, `titulo` y `categoria` nullable.
2. Marcar en "Características implementadas", "Flujo de datos" y en el roadmap que la escritura en SQLite ya está implementada, manteniendo como pendientes el analizador de ofertas y las notificaciones.
3. No tocar las secciones históricas, que documentan lo entregado entonces.

### Subtarea 8.3: `AGENTS.md` — pendiente inmediato y patrones
Flujo de comportamiento:
1. Sustituir en §5 el "Pendiente Inmediato" de persistencia por el paso 4 (analizador de ofertas).
2. Añadir en §6.3 los patrones nuevos de la ronda: helpers sin `commit` con fachada única transaccional; SQLite no relaja `NOT NULL` y exige regeneración; el ASIN string se resuelve antes del `SELECT` que espera `producto_id` entero; `INSERT OR IGNORE` como idempotencia sin actualizar metadatos.
3. No tocar las secciones históricas de rondas anteriores.
