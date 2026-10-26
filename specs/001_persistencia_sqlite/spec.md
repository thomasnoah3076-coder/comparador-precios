# Spec 001 — Persistencia de datos en SQLite (Roadmap paso 3)

**Modo:** Arquitecto de Especificaciones (Spec-Architect Mode)
**Fecha:** Octubre 2026
**Origen:** Roadmap paso 3 de `MEMORY.md` — *"Conectar Retorno con SQLite"*.
**Estado:** Enmiendas 1-2 aplicadas. **En implementación** (parcial, con correcciones pendientes — ver `task.md`).

---

## El QUÉ

### Descripción funcional
El orquestador (`BaseScraper.obtener_datos()`) debe **guardar** en la base de datos local (`database/tracker.db`) los datos que hoy solo extrae y descarta. Concretamente, el sistema pasará de solo-leer a leer-escribir:

1. Al recibir los datos del contrato de un scrape, validarlos y persistirlos en las tres tablas existentes:
   - `Productos` → identidad del producto (una sola fila por producto).
   - `Historial_Precios` → una fila nueva **por cada scrape** (fecha + precio) = historial de precios creciente.
   - `Metricas_Vendedor` → fila de ventas/rating del scrape (solo si hay datos completos).
2. Resolver la relación entre el **ASIN** (identificador de negocio, string, ej. `"B09XLK9GVS"` que usa `main.py`) y el **id entero** (clave primaria de `Productos` de la que cuelgan las foráneas `producto_id`), mediante una nueva columna `asin TEXT UNIQUE`.
3. **Convertir el precio a la moneda local (COP)** justo antes de persistir, mediante el servicio de divisas existente (`services/currency.py`): `Historial_Precios.precio_local` guarda el valor convertido y `moneda_local` = `"COP"`, mientras `precio_usd` conserva el precio original del scraper. Si la conversión no está disponible (sin `.env` relleno, clave inválida o sin red), se aplica **fallback honesto**: el historial se registra en USD (nunca se etiqueta COP a un número no convertido). *(Enmienda 2 — anula la Decisión 2 "guardar en USD, conversión aparte".)*
4. Permitir que la re-ejecución del esquema genere un `tracker.db` con el nuevo diseño (regeneración aprobada; la BD actual tiene 0 filas).

### Entradas
- `datos: dict` — el Contrato de Datos de `MEMORY.md` §4: `titulo, precio, moneda, url, vendedor, ventas, calificacion_promedio`.
- `asín` (extraído de `main.py::PRODUCT_ID`) y `categoria: str | None` (opcional, hoy `None`).
- `conn: sqlite3.Connection` — conexión ya abierta por quien invoca (patrón actual).

### Salidas
- `bool` — `True` si el guardado fue atómico y completo; `False` si se omitió/falló (siempre con aviso por consola).
- El diccionario de retorno de `obtener_datos()` **no cambia** (mismas 7 claves + `origen`); la persistencia es un efecto lateral interno.
- Filas nuevas en las 3 tablas (con `precio_local` en COP si hubo conversión efectiva; si no, *fallback* en USD); `ya_se_consulto_hoy()` pasará a poder devolver `True` en ejecuciones posteriores del mismo día.

---

## El POR QUÉ

### Problema que resuelve
Hoy el sistema **no aprende de cada consulta**:

- `ya_se_consulto_hoy()` consulta `Historial_Precios`… que siempre está vacía → **nunca devuelve `True`** → se scrapeará el mismo producto cuantas veces se ejecute (riesgo de bloqueo anti-bot, consumo innecesario de red).
- `obtener_ultimo_registro()` no encuentra filas → **siempre devuelve `None`** → el camino "de caché" del orquestador es código muerto.
- Sin historial de precios **no existe el paso 4** (analizador de ofertas con `PRICE_DROP_THRESHOLD`) ni **el paso 5** (notificaciones de caída de precio por Telegram): no se puede comparar el precio actual contra el histórico si nunca se guardó el histórico.

### Justificación de negocio/técnica
- **Cimiento del roadmap:** los pasos 4 y 5 consumen directamente las filas que esta etapa crea. No se pueden construir sobre una BD vacía.
- **Eficiencia y anti-scraping:** activa la caché diaria (primera medida real de control de volumen de peticiones ya construida en el paso 7 histórico).
- **Arquitectura:** completa el Template Method — el orquestador ya posee la infraestructura de BD (lectura); le falta la escritura. La lógica SQL vive en `database/schema.py` (dueño del esquema), el scraper hijo sigue ajeno a la BD (SoC).
- **Momento:** es el siguiente paso no-completado del roadmap (`MEMORY.md` §5) y el plan consolidado ya tiene las 7 decisiones del Director cerradas (ver `plan.md`).

### Fuera de alcance de esta spec
- ~~Conversión de divisas a moneda local~~ — **pasó a estar DENTRO de alcance con la enmienda 2**: el guardado convierte a COP mediante `services/currency.py` con *fallback* en USD. La conversión real solo producirá pesos cuando el Director rellene `LOCAL_CURRENCY=COP`, `EXCHANGE_RATE_API_KEY` y `EXCHANGE_RATE_API_URL` en `.env`; hasta entonces el sistema guarda correctamente en USD sin convertir.
- Analizador de ofertas (roadmap paso 4) y notificaciones Telegram (paso 5).
- Decidir si `tracker.db` se saca de git (pendiente abierto del Director).

---

## Historial de decisiones y enmiendas

| # | Decisión / Enmienda | Contenido |
|---|---|---|
| 1 | `asin TEXT UNIQUE` en `Productos` | Clave de negocio para resolver ASIN string ↔ id entero. |
| 2 | ~~Guardar en USD, conversión aparte~~ | **Anulada por la enmienda 2.** |
| 3 | Métricas incompletas → sin fila | Si faltan `ventas` o `calificacion_promedio` (None), no se inserta en `Metricas_Vendedor`. |
| 4 | `categoria` opcional (nullable) | Columna relajada; hoy siempre `None`. |
| 5 | Dataclass interna de validación | `ContratoDatos` (stdlib); el contrato público sigue siendo `dict`. |
| 6 | Fallo de BD = best-effort | Aviso + `rollback` + `False`; nunca propaga. |
| 7 | Regenerar `tracker.db` | Borrar + init (verificado 0 filas). |
| 8 | Columna `titulo` en `Productos` | La columna antes llamada `nombre` pasa a llamarse **`titulo`** (Decisión del Director, 18 oct), alineada con la clave `titulo` del Contrato §4. `obtener_ultimo_registro` selecciona `p.titulo`. |
| Enmienda 1 | ASIN explícito en la fachada | `guardar_datos_producto(conn, asin, datos, categoria)` — el ASIN no puede salir del dict (el Contrato §4 es dato *extraído* de la página; el ASIN es contexto del *llamador*, `main.py::PRODUCT_ID`). |
| Enmienda 2 | Conversión a COP en el guardado | Helper `convertir_a_moneda_local(monto, moneda_origen) -> (monto, moneda)` en `services/currency.py` + 1 sola línea en la fachada (antes de la transacción). **Anula la Decisión 2.** Fallback honesto en USD si no hay conversión efectiva. Contrato de salida puro (sin claves COP en el dict de `obtener_datos()`). |
