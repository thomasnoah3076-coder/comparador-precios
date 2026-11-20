z# Especificación: Analizador de Ofertas

## 1. Objetivo (El Qué)

Implementar un módulo de **solo lectura** que determine si el precio más reciente de un producto registrado en `Historial_Precios` constituye una oferta, comparándolo con el mínimo de su historial previo y devolviendo un veredicto estructurado:

1. Leer el historial del producto en orden `fecha ASC, id ASC` mediante `obtener_historial_precios` de `database/esquema.py`.
2. Tomar la última fila de esa lista como **precio actual** (`precio_usd`) y el **mínimo de las filas anteriores** como precio de referencia, cálculo delegado en `obtener_precio_referencia`.
3. Calcular la caída porcentual `caida = max((precio_referencia − precio_actual) / precio_referencia, 0.0)`.
4. Marcar `es_oferta` cuando `caida >= UMBRAL_CAIDA_PRECIO`, umbral único importado de `config/settings.py`.

El análisis se hace exclusivamente sobre `precio_usd`, columna que es **USD por construcción**: el analizador asume que toda fila que compara está expresada en USD y las filas con precio en otra moneda quedan fuera de su alcance. El módulo no escribe en la base de datos y no navega. Quedan fuera de alcance las notificaciones, la automatización programada, el scraping de precios nuevos y el enganche en `main.py`.

## 2. Motivación (El Por Qué)

El historial que deja cada scrape está hoy sin consumidor; este módulo lo convierte en señal de compra y entrega el veredicto que el paso siguiente necesita sin lógica adicional.

- Detección automática de caídas de precio reales.
- Reutilización del historial ya persistido y verificado.
- Contrato de salida estable para el futuro notificador.
- Comparaciones consistentes en una sola moneda.

## 3. Propuesta Técnica

- **Componentes / Objetos:**
  - `config/settings.py`: `UMBRAL_CAIDA_PRECIO` como umbral único, importado por el analizador sin copia local, y `DB_PATH_TRACKER` como ruta de la base, leída como atributo del módulo en `main`.
  - `database/esquema.py`: helpers de lectura `obtener_historial_precios(conn, producto_id)`, `obtener_productos_con_historial(conn)` y `buscar_id_producto(conn, asin)`; sin tablas nuevas ni cambios de esquema.
  - `database/esquema.py`: `obtener_ultimo_registro` alineado a `ORDER BY fecha DESC, id DESC LIMIT 1`, sin cambio de contrato, para que su "último registro" coincida con el precio actual del analizador cuando dos filas comparten `fecha`.
  - Arranque de ruta condicionado en `services/analizador.py`: con `if __package__ in (None, "")` inserta la raíz del proyecto en `sys.path` antes de los imports absolutos del proyecto, usando `sys` y `pathlib`.
  - `services/analizador.py` (nuevo): funciones puras, constructora privada del veredicto y orquestadoras.
  - `Veredicto` (`dict` de 7 claves fijas): `asin`, `titulo`, `precio_referencia_usd`, `precio_actual_usd`, `caida_porcentual`, `es_oferta`, `moneda` (siempre `"USD"`).
  - Import literal desde el módulo de esquema: `from database.esquema import buscar_id_producto, obtener_historial_precios, obtener_productos_con_historial`.
- **Métodos Principales:**
  - `obtener_historial_precios` — historial ascendente del producto con filas `{fecha, precio_usd, titulo}`.
  - `obtener_productos_con_historial` — productos con al menos una fila de historial, como `{producto_id, asin}`.
  - `obtener_precio_referencia(precios: list[float]) -> float | None` — pura; recibe la lista **cruda** de precios previos, descarta los elementos no numéricos o `<= 0` antes del `min` y devuelve `None` únicamente cuando el conjunto válido queda vacío. Es el **único punto de filtrado** de precios.
  - `calcular_caida` — pura; caída porcentual con suelo `0.0`, precondición `precio_referencia > 0` y comparación `>=` cruda contra el umbral, sin tolerancia.
  - `_analizar_por_id(conn, producto_id, asin)` — privada; única constructora del veredicto, recibe el `producto_id` ya resuelto.
  - `analizar_oferta(conn, asin)` — resuelve el ASIN con `buscar_id_producto` y delega en `_analizar_por_id`.
  - `analizar_productos(conn)` — recorre el listado y delega en `_analizar_por_id` con el `producto_id` y el `asin` devueltos.
  - `main` — modo script de solo lectura para `python -m services.analizador <ASIN>` y `python services/analizador.py <ASIN>`.
- **Guardas, en orden por función:**
  - `analizar_oferta`: `conn` inválida → `asin` no `str` o vacío → producto inexistente (`buscar_id_producto` devuelve `None`).
  - `analizar_productos`: `conn` inválida → descarta con aviso los `asin` nulos.
  - `_analizar_por_id`: `asin` no `str` o vacío → historial vacío → un solo registro → conjunto previo sin precios válidos (referencia `None`) → precio actual no positivo (`<= 0`); la comprobación de `None` se mantiene solo como defensa declarada de la función, porque `Historial_Precios.precio_usd` es `REAL NOT NULL` y ese caso no se siembra por base de datos.
- **Librerías / Dependencias:** `sqlite3`, `argparse`, `sys`, `pathlib` (todas stdlib); sin dependencias nuevas. El analizador no invoca `services.currency`: ese módulo solo se carga de forma transitiva al importar `database/esquema.py`, y nunca se llama a la conversión.
- **Flujo de Datos:**
  ```
  ASIN --> buscar_id_producto (solo fachada individual) ---+
  listado --> obtener_productos_con_historial ------------+--> _analizar_por_id
  _analizar_por_id --> obtener_historial_precios --> ultima fila = precio actual
  filas anteriores --> precios_previos (crudos) --> obtener_precio_referencia
  obtener_precio_referencia --> minimo valido filtrado, o None si no hay precios validos
  guardas (historial vacio, un solo registro, referencia None, actual no positivo) --> None con aviso
  calcular_caida(referencia, actual) --> Veredicto (es_oferta = caida >= UMBRAL_CAIDA_PRECIO)
  ```

## 4. Criterios de Aceptación

- Existe `services/analizador.py` con `obtener_precio_referencia`, `calcular_caida`, `_analizar_por_id`, `analizar_oferta` y `analizar_productos`, todos con tipado explícito, nombres en español y tipo de retorno respetado en cada rama.
- `config/settings.py` expone `UMBRAL_CAIDA_PRECIO` como única constante de umbral, y el analizador la consume por importación, sin definir una constante propia.
- Con `precio_referencia_usd` de 100.00 y precio actual de 85.00, el veredicto trae `caida_porcentual` igual a 0.15 y `es_oferta: True`, porque la comparación es `>=` cruda contra el umbral y ese par se cumple en coma flotante.
- Con una caída inferior al 15 %, o con el precio actual igual o mayor que la referencia, el veredicto trae `es_oferta: False` y `caida_porcentual` igual a `0.0` o positiva pequeña, resultado distinguible del `None` de "sin datos".
- `obtener_precio_referencia([100, 0, 90])` devuelve 100.0 y una lista cuya totalidad de elementos es no numérica o `<= 0` devuelve `None`, porque el descarte ocurre en el único punto de filtrado de la función pura.
- Un historial de precios `{100, 0, 90}` tomando `90` como precio actual produce `precio_referencia_usd` 100.0 y `caida_porcentual` 0.1, porque las filas de precio inválido se descartan antes de calcular el mínimo.
- Con dos filas del mismo producto que comparten `fecha`, `obtener_ultimo_registro` y el analizador devuelven el mismo precio actual, y el veredicto se repite idéntico en ejecuciones sucesivas.
- `conn` inválida, `asin` no `str` o vacío, producto inexistente, historial vacío, historial de un solo registro, conjunto previo sin precios válidos y precio actual no positivo (`<= 0`) hacen que `analizar_oferta` devuelva `None` con aviso por consola y sin lanzar excepción, en particular sin `ZeroDivisionError`.
- Cualquier `sqlite3.Error` de lectura hace que `analizar_oferta` devuelva `None` con aviso, que el lote omita ese producto y continúe con el siguiente, y en ningún caso se degrada a un veredicto con `es_oferta: False`.
- Filas con `moneda_local` COP y filas con *fallback* USD mezcladas en el mismo producto producen el mismo veredicto que una serie homogénea, porque solo se lee `precio_usd` y no se promete nada sobre monedas distintas de USD.
- Repetir `analizar_oferta` y `analizar_productos` varias veces deja las tres tablas con los mismos conteos, sin `commit`, `rollback`, `close` ni sentencias de escritura.
- `analizar_productos` recorre varios productos vía `obtener_productos_con_historial`, descarta con aviso los `asin` nulos, devuelve veredictos parciales cuando alguno se descarta o falla y devuelve `[]` únicamente cuando ninguna entrada produce veredicto (conexión inválida o todos los productos descartados); nunca devuelve `None` ni `None` intercalados, y usa las mismas claves que el camino individual.
- `python services/analizador.py <ASIN>` y `python -m services.analizador <ASIN>` imprimen el veredicto sobre una conexión `mode=ro` abierta con la ruta de `settings.DB_PATH_TRACKER`, y cuando el archivo no existe el modo script avisa y sale sin crear ni modificar `database/tracker.db`.
