# Plan 001 — Persistencia de datos en SQLite (Arquitectura y Diseño Lógico)

**Alimenta:** `spec.md` (QUÉ/POR QUÉ) → `task.md` (CÓMO ejecutable).
**Estado:** Enmiendas 1-2 aplicadas (ASIN en la fachada; conversión a COP con *fallback* honesto — anula la Decisión 2). **En implementación** (parcial, con correcciones pendientes — ver `task.md`).

---

## 1. Alineación con la Constitución (`docs/constitution.md`)

| Principio | Cómo se aplica en esta especificación |
|---|---|
| **KISS** | 0 módulos nuevos: el SQL vive en `database/schema.py` (ya es el repositorio). No se crea `services/persistence.py` ni dependencias nuevas (la validación usa **dataclass de stdlib**, no Pydantic). |
| **Métodos/variables en español** | Todas las funciones y parámetros en español: `buscar_id_producto`, `obtener_o_crear_producto`, `insertar_historial_precio`, `insertar_metricas_vendedor`, `guardar_datos_producto`. |
| **Idempotencia / estado predecible** | `init_sqlite_db()` sigue con `CREATE TABLE IF NOT EXISTS` (5ª ronda). `obtener_o_crear_producto` usa `INSERT OR IGNORE` por `asin` → repetir nunca duplica productos. El guardado es **transaccional** (commit único o rollback total): el estado de la BD es siempre "todo guardado" o "nada guardado", nunca parcial. |
| **Estado predecible ante errores** | Fallo de BD → `rollback` + aviso por consola + el scrape no se pierde (patrón *best-effort* ya usado con el widget de Miami). |
| **Separación de responsabilidades** | SQL solo en `database/schema.py`; orquestación solo en `BaseScraper`; `AmazonScraper` **no se modifica** y sigue sin saber que la BD existe. |

---

## 2. Modelos de datos y esquemas

### 2.1 Cambios de esquema en `Productos` (aprobados por el Director)

```sql
CREATE TABLE IF NOT EXISTS Productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asin TEXT UNIQUE,            -- NUEVO: clave de negocio (string, ej. "B09XLK9GVS")
    titulo TEXT NOT NULL,       -- Decisión 8 (Director): la columna se llama `titulo` (antes `nombre`), alineada con la clave del Contrato §4
    url TEXT NOT NULL,
    vendedor TEXT NOT NULL,
    categoria TEXT,              -- RELAJADO: NOT NULL → nullable (opcional hoy, la usará el paso 5)
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

- **Decisión 7 (Director):** regenerar `database/tracker.db` (borrar + init). Verificado: **0 filas** en las 3 tablas → nada que perder. Así se evita una migración `ALTER TABLE` (SQLite no permite relajar `NOT NULL`) y se mantiene no-destructividad real (no hay datos que destruir).
- `Historial_Precios` y `Metricas_Vendedor` **no cambian** (sus `NOT NULL` se respetan desde Python: ver §3.4).
- Se añade una comprobación de esquema en init (PRAGMA `table_info`): si `Productos` carece de la columna `asin` (BD vieja copiada a mano), imprimir aviso indicando que hay que regenerar el archivo — sin borrar nada automáticamente.

### 2.2 Dataclass de validación (Contrato §4 tipado)

- **Nombre:** `ContratoDatos` (UpperCamelCase, stdlib `dataclasses`).
- **Campos exactamente igual al Contrato `MEMORY.md` §4:** `titulo: str`, `precio: float`, `moneda: str`, `url: str`, `vendedor: str`, `ventas: int | None`, `calificacion_promedio: float | None`.
- **Uso interno:** `guardar_datos_producto` convierte el `dict` recibido a `ContratoDatos` antes de persistir; si el dict no tiene las claves o los tipos no casan → `ValueError` claro (capturado por la fachada → aviso + `False`).
- **No cambia el contrato público:** `obtener_datos()` sigue retornando `dict` (las 7 claves + `origen`); `main.py` no se toca en su parte de impresión.

### 2.3 Mapeo de columnas (Contrato → tablas)

| Contrato | Destino |
|---|---|
| *(ASIN, de `main.py::PRODUCT_ID`)* | `Productos.asin` |
| `titulo` | `Productos.titulo` |
| `url`, `vendedor`, (`categoria` opcional) | `Productos` |
| `precio` + `moneda` | `Historial_Precios.precio_usd` = precio original; `precio_local`/`moneda_local` = par devuelto por `convertir_a_moneda_local` (COP si hubo conversión efectiva; si no, el par origen — *fallback honesto*; enmienda 2) |
| `ventas`, `calificacion_promedio`, `vendedor` | `Metricas_Vendedor` (**solo si `ventas` y `calificacion_promedio` no son `None`**; si no → sin fila, `bool = False`) |

---

## 3. Patrones de diseño

1. **Template Method (consolidado):** `BaseScraper.obtener_datos()` define el esqueleto *consultar caché → extraer → persistir → retornar*; los pasos concretos son métodos/paquetes reutilizables. Se añade el paso que faltaba (persistir).
2. **Repositorio:** `database/schema.py` es la capa de repositorio (todo SQL vive ahí); el orquestador solo la invoca. Nada de SQL en `BaseScraper.py`.
3. **Fachada transaccional:** `guardar_datos_producto` es la única puerta de escritura; expone una operación atómica de alto nivel (`bool`) ocultando 3 inserts.
4. **Validación por contrato tipado (dataclass):** frontera de robustez entre lo que produce el scraper y lo que acepta la BD.
5. **Patrón de transacción a documentar:** *las funciones helper no hacen `commit`; solo la fachada cierra la transacción* (si cada helper hiciera commit, el rollback sería imposible → filas parciales).

---

## 4. Flujo de ejecución (ciclo de vida de los datos)

```
main.py
  │  init_sqlite_db()                ← arranque: BD regenerada/nueva si no existe
  │  AmazonScraper(conn).obtener_datos(ASIN, url)
  ▼
BaseScraper.obtener_datos(product_id=ASIN, url)
  │
  ├─ 1. id = buscar_id_producto(conn, ASIN)          [SELECT; sin red]
  │       └─ si id existe y ya_se_consulto_hoy(conn, id):
  │              registro = obtener_ultimo_registro(conn, id)
  │              registro["origen"] = "base_de_datos"  → RETURN (caché diaria ✓)
  │
  ├─ 2. datos = await extraer_datos(url)             [Playwright + contrato §4]
  │       └─ si falla: excepción sube a main.py (sin persistir nada) ← RETURN
  │
  ├─ 3. datos["origen"] = "scraping"
  │
  ├─ 4. guardar_datos_producto(conn, ASIN, datos)      [BEST-EFFORT]
  │       │ 4a. validar dict con dataclass ContratoDatos
  │       │       └─ inválido → print aviso → RETURN False (los datos se conservan)
  │       │ 4a-bis. precio_local, moneda_local = convertir_a_moneda_local(precio, moneda)  [enmienda 2]
  │       │       └─ sin conversión efectiva → (precio, moneda)  [fallback honesto en USD]
  │       │ 4b. BEGIN (implícito) →
  │       │     obtener_o_crear_producto(conn, ASIN, ...) → id  [INSERT OR IGNORE + SELECT]
  │       │     insertar_historial_precio(id, precio_local, moneda_local, precio_usd)
  │       │     insertar_metricas_vendedor(...) → bool (omite fila si hay None)
  │       │ 4c. COMMIT  ─ o ─  CUALQUIER ERROR → ROLLBACK + aviso → False
  │
  └─ 5. RETURN datos (mismas 7 claves + origen)       ← main.py lo imprime
```

**Efecto en la siguiente ejecución del mismo día:** el paso 1 encontrará filas → `ya_se_consulto_hoy` devuelve `True` → se sirve de la BD y **no se vuelve a scrapear** (cierre del bucle).

---

## 5. Firma de las funciones nuevas (`database/schema.py`)

| Función                                                  | Recibe                                                                                                                  | Retorna             | Robustez                                                                                                                                                                                                                                                                                                                                                                          |
| -------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `buscar_id_producto`                                     | `conn, asin: str`                                                                                                       | `int \| None`       | Solo SELECT; nunca lanza por "no encontrado" (None explícito).                                                                                                                                                                                                                                                                                                                    |
| `obtener_o_crear_producto`                               | `conn, asin, titulo, url, vendedor, categoria: str \| None = None`                                                      | `int`               | `INSERT OR IGNORE` por `asin` + SELECT → id estable sin duplicados. **No hace commit** (lo cierra la fachada).                                                                                                                                                                                                                                                                    |
| `insertar_historial_precio`                              | `conn, producto_id: int, precio_local: float, moneda_local: str, precio_usd: float`                                     | `None`              | Fecha por `DEFAULT CURRENT_TIMESTAMP`; un INSERT simple. No hace commit.                                                                                                                                                                                                                                                                                                          |
| `insertar_metricas_vendedor`                             | `conn, producto_id: int, nombre_vendedor: str \| None, total_ventas: int \| None, calificacion_promedio: float \| None` | `bool`              | `False` si falta algún dato (respeta `NOT NULL` sin inventar ceros); `True` si insertó. No hace commit.                                                                                                                                                                                                                                                                           |
| `guardar_datos_producto`                                 | `conn, asin: str, datos: dict, categoria: str \| None = None`                                                           | `bool`              | Valida con `ContratoDatos`; calcula el par local con `convertir_a_moneda_local` **antes** de la transacción (enmienda 2); pasa `asin` a `obtener_o_crear_producto`; `try/except` granular con `rollback` + aviso; nunca propaga (best-effort). Única que hace `commit`.                                                                                                           |
| `convertir_a_moneda_local` *(en `services/currency.py`)* | `monto: float, moneda_origen: str`                                                                                      | `tuple[float, str]` | **Enmienda 2.** Lee `DEFAULT_CURRENCY` (= `LOCAL_CURRENCY` del `.env`); si no está configurado → `(monto, moneda_origen)` sin red; si no, `convertir_moneda(...)` con **regla de verdad**: solo etiqueta la moneda destino si el valor efectivamente cambió (`convertido != monto`; la tasa USD→COP jamás es 1). **Sin `try/except`:** desde la 6ª ronda `convertir_moneda` jamás lanza excepciones (KISS; la garantía se verifica con la batería) — nunca propaga. |

> **Nota (enmienda):** el ASIN **no está en el dict** `datos` — el Contrato §4 es lo que el scraper *extrajo* de la página, mientras que el ASIN es contexto del *llamador*: nace en `main.py::PRODUCT_ID` → `obtener_datos(product_id, url)` y de ahí se pasa explícito a la fachada. Las alternativas (parsearlo de `datos["url"]`, frágil con `amzn.to`/`/gp/product/`; o meterlo al Contrato, que es genérico entre tiendas y no cambia por decisión del Director) se descartaron por KISS y por contrato.

> **Nota (enmienda 2 — conversión a COP):** la Decisión 2 (*"guardar en USD, conversión aparte"*) quedó **anulada** por petición del Director: su moneda local son los pesos colombianos. La conversión vive en un helper de `services/currency.py` (su módulo natural) y la fachada solo hace **1 línea** de orquestación *antes* del `BEGIN`: así un fallo del servicio de divisas no arrastra un `rollback` que pierda el precio (**`convertir_moneda` jamás lanza excepciones**: degrada devolviendo el monto — garantía verificada en la 6ª ronda con su batería de 13 pruebas, por lo que ni C0 ni la fachada necesitan `try/except` por la conversión). El dict de retorno de `obtener_datos()` **no expone COP** (contrato puro, Decisión 5 intacta): el precio convertido vive solo en la BD. *Decisión del Director: fallback honesto — si la conversión falla/no está configurada, la fila se guarda en USD con su moneda real; jamás se etiqueta COP a un monto no convertido (evita filas mixtas que envenenarían el analizador del paso 4).*

`BaseScraper` solo importa y llama `buscar_id_producto` y `guardar_datos_producto` (la fachada internamente usa las otras 3). Firma de `obtener_datos` **sin cambios de nombre**: `(product_id: str, url: str) -> dict`.

---

## 6. Archivos implicados

| Archivo | Acción |
|---|---|
| `database/schema.py` | MODIFICAR: CREATE TABLE de `Productos` (asin + categoria nullable), aviso de esquema viejo, 5 funciones nuevas, dataclass `ContratoDatos`. |
| `scrapers/BaseScraper.py` | MODIFICAR: flujo de `obtener_datos()` (paso 1 de resolución ASIN, paso 4 de persistencia best-effort). |
| `main.py` | MODIFICAR: llamar `init_sqlite_db()` al arrancar. |
| `services/currency.py` | MODIFICAR: helper `convertir_a_moneda_local` (regla de verdad + fallback; enmienda 2). |
| `database/tracker.db` | REGENERAR (borrar + init) — decisión 7 del Director. |
| `specs/001_persistencia_sqlite/*` | ESTOS 3 documentos. |
| `MEMORY.md` / `README.md` / `AGENTS.md` | ACTUALIZAR al cierre (paso 3 completado, 6ª ronda de patrones). |

**Verificación (previa a docs/commit):** `py_compile` + batería temporal aislada `test_tmp_*` (BD en `tmp_path`, sin red ni `tracker.db` real): esquema regenerado, idempotencia del ASIN, historial creciente con `ya_se_consulto_hoy` en `True`, métricas omitidas con `None`, atomicidad (rollback sin filas parciales), contrato inválido rechazado, camino best-effort, conversión (fallback sin destino, COP con `convertir_moneda` mockeado — sin red) y bucle completo de `obtener_datos()` con `extraer_datos` mockeado. Verde → limpieza §6.4; rojo → conservar y reporte §6.2.
