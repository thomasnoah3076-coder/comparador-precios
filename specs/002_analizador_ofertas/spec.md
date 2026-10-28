# Especificación: Analizador de Ofertas (Roadmap paso 4)

**Fecha:** Octubre 2026
**Origen:** Roadmap paso 4 de `MEMORY.md` §5 — *"Desarrollar Analizador de Ofertas: comparar el precio actual guardado en la BD con el historial para detectar caídas de precio"*.
**Estado:** Especificación inicial (pendiente de `plan.md` y de aprobación del Director).

---

## 1. Objetivo (El Qué)

Crear un módulo de **solo lectura** que evalúe si el precio más reciente de un producto registrado en `Historial_Precios` constituye una oferta, comparándolo contra su historial de precios y devolviendo un veredicto estructurado:

1. Leer del historial del producto los precios en USD (columna `precio_usd`, la única moneda estable garantizada en lectura) en orden cronológico.
2. Tomar el registro más reciente como **precio actual** y el **mínimo del historial anterior a él** como precio de referencia.
3. Calcular la caída porcentual: `caida = (precio_referencia − precio_actual) / precio_referencia`. Un valor positivo indica que el precio actual es menor que toda la historia previa del producto.
4. Marcar el veredicto como oferta cuando `caida >= UMBRAL_CAIDA_PRECIO`. La constante vive en `config/settings.py` (renombrada allí desde el `PRICE_DROP_THRESHOLD` nominal del roadmap, que hoy existe sin uso; nombre en español por §1 de la Constitución) y es la **única fuente de verdad**: `services/analizador.py` la importa y no define copia local.

El módulo **no escribe** en la base de datos, **no navega** (no invoca scrapers ni Playwright) y **no notifica** (Telegram es el paso 5).

## 2. Motivación (El Por Qué)

- La persistencia (spec 001) está completa y verificada: cada scrape deja una fila nueva en `Historial_Precios`. Ese historial acumulado es hoy **dato muerto**: nada lo consume. El analizador es el primer consumidor y convierte el historial en valor detectable.
- Es el cimiento directo del paso 5 del roadmap: el resultado estructurado (`es_oferta`, `caida_porcentual`, precios de referencia) es exactamente lo que el consumidor futuro de notificaciones Telegram necesitará para formatear y enviar, sin tocarle ninguna lógica.
- Detectar la caída contra el **mínimo histórico** (no contra el registro inmediatamente anterior) captura el caso real de compra: "hoy está más barato que en cualquier momento previo registrado", evitando falsos positivos cuando ayer subió y hoy volvió.
- Comparar en USD (`precio_usd`) evita comparar precios etiquetados en monedas distintas: cuando la conversión a COP no está disponible, la fila del historial cae en *fallback* honesto USD y `moneda_local` puede variar entre filas; el precio en USD no lo hace.

**Fuera de alcance:** notificaciones Telegram (paso 5, mencionado aquí solo como consumidor futuro, sin implementar), automatización con scheduler, scraping de precios nuevos y escrituras en la BD.

## 3. Propuesta Técnica

- **Componentes / Objetos:**
  - `services/analizador.py` (nuevo): dueño de la lógica de análisis. Importa `UMBRAL_CAIDA_PRECIO` desde `config.settings` (fuente única del umbral, sin constante local duplicada).
  - `database/schema.py` (modificado): dos helpers nuevos de **lectura** (el dueño del esquema); ninguna tabla nueva, ningún cambio de esquema.
  - `main.py` (sin cambios en este spec): la integración en el flujo principal se recibe en el plan al aprobarla.
- **Métodos Principales:**
  - `database::obtener_historial_precios(conn: sqlite3.Connection, producto_id: int) -> list[dict]` — consulta del historial: `SELECT h.fecha, h.precio_usd, p.titulo FROM Historial_Precios h JOIN Productos p ON p.id = h.producto_id WHERE h.producto_id = ? ORDER BY h.fecha ASC, h.id ASC` y devuelve la lista de filas como dicts `{fecha, precio_usd, titulo}`. El desempate temporal `id ASC` hace determinista el "más reciente" (la fila de `id` máximo, última de la lista) cuando dos inserciones comparten `fecha` —la resolución de `TIMESTAMP` es de segundos—. El JOIN con `Productos` es la fuente del `titulo` del veredicto. Read-only, sin `commit`.
  - `database::obtener_productos_con_historial(conn: sqlite3.Connection) -> list[dict]` — segunda consulta de lectura nueva: `SELECT DISTINCT p.id AS producto_id, p.asin FROM Productos p JOIN Historial_Precios h ON h.producto_id = p.id ORDER BY p.id ASC`; devuelve dicts `{producto_id, asin}` con los productos que tienen al menos una fila de historial. Read-only, sin `commit`.
  - `services/analizador::obtener_precio_referencia(precios: list[float]) -> float | None` — pura: devuelve el mínimo de la lista; `None` si la lista es vacía (retorno temprano, tipo explícito en todas las ramas).
  - `services/analizador::calcular_caida(precio_referencia: float, precio_actual: float) -> float` — pura, devuelve la caída porcentual; garantizada no-negativa (si `precio_actual >= precio_referencia`, devuelve `0.0`). Precondición `precio_referencia > 0`, garantizada por la fachada antes de llamarla (evita la división inválida).
  - `services/analizador::analizar_oferta(conn: sqlite3.Connection, asin: str) -> dict | None` — fachada del módulo. Resuelve `asin → producto_id` con `buscar_id_producto` (el identificador de entrada es siempre ASIN, nunca el id entero), obtiene el historial con `obtener_historial_precios`, extrae los precios `[fila["precio_usd"] for fila in filas]`, valida precondiciones y retorna el veredicto o `None` con aviso por consola. Jamás propaga excepciones hacia el llamador (degradación elegante, §4 de la Constitución).
  - Contrato de salida de `analizar_oferta` (dict de claves fijas): `asin` (str), `titulo` (str | None, tomado de la fila más reciente que devuelve `obtener_historial_precios` vía su JOIN con `Productos`), `precio_referencia_usd` (float), `precio_actual_usd` (float), `caida_porcentual` (float), `es_oferta` (bool), `moneda` (str, siempre `"USD"`). Un único conjunto de claves (régimen de la 4ª ronda: no duplicar caminos con claves divergentes).
  - `services/analizador::analizar_productos(conn: sqlite3.Connection) -> list[dict]` — obtiene el listado con `obtener_productos_con_historial` y aplica `analizar_oferta` a cada `asin`. Devuelve **solo los veredictos producidos** (la lista no contiene `None`): los productos sin análisis posible se omiten con aviso por consola. Un error en un producto no detiene la evaluación del siguiente (§4 de la Constitución).
- **Librerías / Dependencias:** solo stdlib (`sqlite3`, `argparse` para el modo script, `typing`). Sin dependencias nuevas.
- **Flujo de Datos:**
  1. El llamador (`main.py` tras una consulta exitosa, o el modo script) abre la conexión, llama `analizar_oferta(conn, asin)` y recibe el veredicto o `None`.
  2. `analizar_oferta` valida `conn`/`asin` → `buscar_id_producto` → `obtener_historial_precios` (filas `{fecha, precio_usd, titulo}`) → extrae los floats `[fila["precio_usd"] for fila in filas]` → separa la última fila (actual) del resto → `obtener_precio_referencia(precios_previos)` → valida `precio_referencia > 0` → `calcular_caida` → veredicto, con `titulo` tomado de la fila más reciente.
  3. Casos sin análisis posible, todos devuelven `None` con aviso claro, sin lanzar: `conn` nulo/cerrada, `asin` vacío/no-str, producto inexistente, historial vacío, historial con un solo registro (no hay contra qué comparar) y `precio_referencia <= 0` (precondición de `calcular_caida`: la división sería inválida).
  4. `analizar_productos` obtiene `obtener_productos_con_historial` y repite el flujo del paso 2 por cada `asin`, omitiendo con aviso los productos sin análisis posible.
  5. Modo ejecutable: `python -m services.analizador <ASIN>` imprime el veredicto del producto; para permitir también la ejecución directa del archivo, incluir el arranque de ruta condicionado ya probado en `database/schema.py` (`if __package__ in (None, "")`).
  6. Validación de entradas explícita al inicio (`isinstance`) y el checker no depende de que la BD o los SELECT silencien errores.

## 4. Criterios de Aceptación

- Existe `services/analizador.py` con `analizar_oferta`, `analizar_productos`, `obtener_precio_referencia` y `calcular_caida`, todos con tipado explícito y nombres en español (§1/§2 de la Constitución); el umbral se consume importando `UMBRAL_CAIDA_PRECIO` desde `config.settings`, sin constante local duplicada.
- `config/settings.py` exporta `UMBRAL_CAIDA_PRECIO = 0.15` (renombre de `PRICE_DROP_THRESHOLD`, que no tenía otros usos que actualizar).
- Con un historial de ≥ 2 registros en USD donde el más reciente cae ≥ 15 % respecto al mínimo previo, `analizar_oferta` devuelve un dict con `es_oferta: True`, `caida_porcentual >= 0.15` y `titulo` no vacío (proveniente del JOIN con `Productos`).
- Con dos filas del mismo producto con `fecha` idéntica (mismo segundo), el precio actual es la fila de `id` máximo (desempate `ORDER BY fecha ASC, id ASC`): el veredicto es determinista e independiente del orden en que SQLite devuelva las filas.
- Con una caída < 15 % (o con precio actual igual o mayor que la referencia), `analizar_oferta` devuelve el veredicto con `es_oferta: False` y `caida_porcentual: 0.0` o positivo pequeño, distinguiendo claramente "no es oferta" de "sin datos" (que es `None`).
- Umbral en frontera: caída exacta del 15 % se marca como oferta (comparación con `>=`).
- Historial con un solo registro, historial vacío, producto inexistente, `asin` vacío/no-str, `conn` nulo/cerrada y `precio_referencia <= 0` devuelven `None` con aviso por consola, sin lanzar excepción (en particular, sin `ZeroDivisionError`).
- El análisis se realiza exclusivamente sobre `precio_usd`; las filas con `moneda_local` distinta (filas con COP real vs *fallback* USD) no distorsionan el cálculo.
- El módulo es de solo lectura: repetir el análisis N veces no altera ninguna tabla ni duplica filas (idempotencia, §3 de la Constitución).
- `analizar_productos` recorre varios productos vía `obtener_productos_con_historial`, devuelve solo veredictos (sin `None` intercalados) y un fallo en uno no impide el veredicto de los restantes.
- `py_compile` limpio y batería `pytest` aislada en verde (BD en `tmp_path` con `init_sqlite_db()`, sin red, sin `tracker.db` real); si todo pasa, temporales y cachés se eliminan conforme §6.4 de `AGENTS.md`.
