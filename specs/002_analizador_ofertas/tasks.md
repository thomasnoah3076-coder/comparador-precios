# Tareas de Implementación

## Dependencias y Arquitectura

- **Librerías:** `sqlite3` (stdlib: conexión recibida y `OperationalError` del lock), `argparse` (stdlib: parseo del ASIN solo en el bloque `__main__`), `sys` (stdlib: `sys.path` en el arranque de ruta y `sys.argv` en las pruebas), `pathlib` (stdlib: `Path` para la raíz del proyecto y la comprobación de existencia de la BD), `os` (stdlib: copia de `os.environ` para fijar el `PYTHONPATH` del subproceso), `config.settings` (`UMBRAL_CAIDA_PRECIO`, `DB_PATH_TRACKER` leído como atributo del módulo), `database.schema` (`buscar_id_producto`, `obtener_historial_precios`, `obtener_productos_con_historial`, `obtener_ultimo_registro`, `init_sqlite_db` para la BD temporal, y `obtener_o_crear_producto`, `insertar_historial_precio` e `insertar_metricas_vendedor`, usados solo para sembrar la BD temporal de la batería, sin `commit`, que lo aporta la fixture de la Subtarea 7.1.2), `services.currency` (dependencia transitiva de `database.schema` por `convertir_a_moneda_local`, cargada en el arranque, parcheada por la fixture y nunca invocada), `pytest` (batería temporal aislada) con las fixtures `monkeypatch`, `capsys` y `tmp_path`, `inspect` (stdlib: firmas y valores de retorno en la verificación), `runpy` y `subprocess` (stdlib: ejecución directa y como paquete del modo script).
- **Objetos / Modelos:** `FilaHistorial` (`dict`: `fecha: str`, `precio_usd: float`, `titulo: str`), `ProductoConHistorial` (`dict`: `producto_id: int`, `asin: str | None`), `Veredicto` (`dict` de siete claves fijas: `asin`, `titulo`, `precio_referencia_usd`, `precio_actual_usd`, `caida_porcentual`, `es_oferta`, `moneda`), `sqlite3.Connection` única del llamador (compartida, sin `row_factory` mutado, abierta en `mode=ro` por el modo script) y `Path` de la BD en `settings.DB_PATH_TRACKER`.
- **Métodos Globales:** `UMBRAL_CAIDA_PRECIO`, `obtener_historial_precios`, `obtener_productos_con_historial`, `obtener_ultimo_registro`, `obtener_precio_referencia`, `calcular_caida`, `_analizar_por_id`, `analizar_oferta`, `analizar_productos`, `main`, bloque `if __name__ == "__main__"`.

## Tarea Principal 1: Umbral único de caída en la configuración

### Subtarea 1.1: `UMBRAL_CAIDA_PRECIO` — renombre de la constante en `config/settings.py`
Flujo de comportamiento:
- [x] 1. Renombrar `PRICE_DROP_THRESHOLD = 0.15` a `UMBRAL_CAIDA_PRECIO = 0.15` en `config/settings.py`, conservando el valor `0.15` y el comentario del porcentaje.
- [x] 2. Mantener intactos `BASE_DIR`, `DB_PATH_TRACKER`, `RUTA_TASAS_CAMBIO`, las variables de Telegram, `DEFAULT_CURRENCY` y las de la API de divisas.
- [x] 3. Comprobar que ningún módulo de `config/`, `database/`, `services/`, `scrapers/` ni `main.py` importa ni referencia el nombre viejo; el único consumidor nuevo será `services/analizador.py`.
- [x] 4. No definir ninguna otra constante de umbral en el proyecto: `UMBRAL_CAIDA_PRECIO` es la única fuente de verdad y el analizador la importa sin copia local.

## Tarea Principal 2: Helpers de lectura en `database/schema.py`

### Subtarea 2.1: `obtener_historial_precios` — historial ascendente de un producto con su título
Flujo de comportamiento:
- [x] 1. Declarar `def obtener_historial_precios(conn: sqlite3.Connection, producto_id: int) -> list[dict]` en `database/schema.py`, junto a `buscar_id_producto`, con docstring en español y type hints (§1/§2 de la Constitución).
- [x] 2. Ejecutar con `conn.execute` la sentencia `SELECT h.fecha, h.precio_usd, p.titulo FROM Historial_Precios h JOIN Productos p ON p.id = h.producto_id WHERE h.producto_id = ? ORDER BY h.fecha ASC, h.id ASC`, pasando `producto_id` como parámetro de la tupla.
- [ ] 3. Leer todas las filas con `fetchall()` y convertir cada tupla a `dict` con `zip` de los nombres de columna declarados en el `SELECT` (`fecha`, `precio_usd`, `titulo`), produciendo objetos `FilaHistorial`.
- [ ] 4. Retornar la lista en orden ascendente con retorno explícito en todas las ramas: `[]` cuando el producto no tiene filas, nunca `None`.
- [ ] 5. No ejecutar `commit`, `rollback` ni `close` sobre la conexión del llamador y no asignar `conn.row_factory`: la conexión es compartida con `main.py` y con las funciones de escritura.
- [ ] 6. No ejecutar sentencias de escritura: la función es de solo lectura y repetirla no altera ninguna tabla.
- [ ] 7. Reubicar en `database/schema.py` el bloque `if __package__ in (None, "")` por encima de `from services.currency import convertir_a_moneda_local`, el único import absoluto del proyecto que hoy lo precede, conservando la inserción idempotente `if str(raiz) not in sys.path`: en su posición actual el import falla antes de que el guard se ejecute y `python database/schema.py` no arranca.

### Subtarea 2.2: `obtener_productos_con_historial` — listado de productos analizables
Flujo de comportamiento:
- [ ]1. Declarar `def obtener_productos_con_historial(conn: sqlite3.Connection) -> list[dict]` en `database/schema.py`, con docstring en español y type hints.
- [ ]2. Ejecutar `SELECT DISTINCT p.id AS producto_id, p.asin FROM Productos p JOIN Historial_Precios h ON h.producto_id = p.id ORDER BY p.id ASC` sin parámetros.
- [ ]3. Convertir las tuplas con `fetchall()` y `zip` de los nombres de columna declarados (`producto_id`, `asin`), produciendo objetos `ProductoConHistorial`.
- [ ]4. Aceptar `asin` en `None` sin filtrar en el helper: `Productos.asin` es `UNIQUE` pero no `NOT NULL`, y la guarda del ASIN pertenece a `_analizar_por_id`.
- [ ]5. Retornar `[]` cuando ningún producto tiene historial, con retorno explícito, y no ejecutar `commit`, `rollback` ni `close` sobre la conexión del llamador.
- [ ]6. No tocar `conn.row_factory` ni el esquema: la consulta es de solo lectura.

### Subtarea 2.3: `obtener_ultimo_registro` — desempate temporal alineado al analizador
Flujo de comportamiento:
- [ ]1. Localizar en `obtener_ultimo_registro` la subconsulta que sirve el precio: `SELECT precio_usd FROM Historial_Precios WHERE producto_id = p.id ORDER BY fecha DESC LIMIT 1`.
- [ ]2. Añadir el desempate `id DESC` a esa subconsulta, quedando `ORDER BY fecha DESC, id DESC LIMIT 1`, el mismo criterio de `obtener_historial_precios` leído en sentido inverso cuando dos filas comparten `fecha`.
- [ ]3. No modificar las subconsultas de `Metricas_Vendedor` (`total_ventas` y `calificacion_promedio`), ni las columnas servidas, ni el contrato de siete claves con moneda `"USD"`.
- [ ]4. No alterar las funciones de escritura (`obtener_o_crear_producto`, `insertar_historial_precio`, `insertar_metricas_vendedor`, `guardar_datos_producto`) ni el esquema de las tres tablas.

## Tarea Principal 3: Funciones puras del analizador

### Subtarea 3.1: encabezado de `services/analizador.py` — imports y arranque de ruta condicionado
Flujo de comportamiento:
- [ ]1. Crear `services/analizador.py` e importar primero solo la stdlib: `sqlite3`, `argparse`, `sys` y `Path` de `pathlib`; los hints de las firmas usan los genéricos nativos (`list[float]`, `float | None`, `dict | None`, `list[dict]`) y no requieren `import typing`. Las librerías del módulo son exactamente esas cuatro: el archivo no contiene `import typing` ni ninguna referencia a `typing.`, de modo que la mención de `typing` en `spec.md` §3 queda sustituida por esta lista.
- [ ]2. Colocar inmediatamente después, y **antes** de cualquier import absoluto del proyecto, el arranque de ruta condicionado: `if __package__ in (None, ""):` con `raiz = Path(__file__).resolve().parent.parent` e inserción idempotente `if str(raiz) not in sys.path: sys.path.insert(0, str(raiz))`.
- [ ]3. Importar después del guard los módulos del proyecto: `from config import settings`, `from config.settings import UMBRAL_CAIDA_PRECIO` y `from database.schema import buscar_id_producto, obtener_historial_precios, obtener_productos_con_historial`.
- [ ]4. No definir ninguna constante de umbral local, ni importar Playwright, `requests` o `services.currency`; `services.currency` se carga solo de forma transitiva desde `database.schema` y el analizador no invoca la conversión de moneda.
- [ ]5. Declarar las firmas con los genéricos nativos explícitos en todas las ramas de retorno (`list[float]`, `float | None`, `dict | None`, `list[dict]`), sin `import typing`, según §2 de la Constitución.

### Subtarea 3.2: `obtener_precio_referencia` — mínimo del historial previo
Flujo de comportamiento:
- [ ]1. Declarar `def obtener_precio_referencia(precios: list[float]) -> float | None` como función pura: sin conexión, sin archivos, sin `print` y sin leer `UMBRAL_CAIDA_PRECIO`.
- [ ]2. Retornar temprano `None` cuando `precios` esté vacío, porque no existe historial previo contra el que comparar.
- [ ]3. Retornar `min(precios)` en la rama con datos, con tipo explícito `float | None` en ambos caminos.
- [ ]4. No mutar la lista recibida: el llamador reutiliza las filas del historial para el precio actual.

### Subtarea 3.3: `calcular_caida` — caída porcentual con suelo cero
Flujo de comportamiento:
- [ ]1. Declarar `def calcular_caida(precio_referencia: float, precio_actual: float) -> float` como función pura, sin `print` y sin consultar el umbral: la decisión de oferta vive en `_analizar_por_id`.
- [ ]2. Documentar la precondición `precio_referencia > 0`: la garantiza `_analizar_por_id` antes de llamarla para evitar la división inválida, y la función no captura `ZeroDivisionError`.
- [ ]3. Calcular `caida = (precio_referencia - precio_actual) / precio_referencia`, que marca positivo cuando el precio actual es menor que la referencia.
- [ ]4. Retornar `max(caida, 0.0)` para que el resultado sea no-negativo cuando el precio actual iguala o supera la referencia; el veredicto es entonces "no es oferta", nunca una caída negativa.

## Tarea Principal 4: Veredicto por producto

### Subtarea 4.1: `_analizar_por_id` — única constructora del veredicto
Flujo de comportamiento:
- [ ]1. Declarar `def _analizar_por_id(conn: sqlite3.Connection, producto_id: int, asin: str | None) -> dict | None`; la firma admite `None` porque el batch le entrega `Productos.asin`, que no es `NOT NULL`, y el `producto_id` llega ya resuelto.
- [ ]2. Primera guarda: si `asin` no es `str` o queda vacío tras `strip()`, imprimir el aviso "Sin análisis: ASIN inválido." y retornar `None`, antes de leer el historial.
- [ ]3. Leer `filas = obtener_historial_precios(conn, producto_id)`, usando el nombre importado en este módulo, y mantener el orden ascendente que devuelve el helper.
- [ ]4. Segunda guarda: si `len(filas) == 0`, imprimir el aviso "Sin análisis: historial vacío." y retornar `None`.
- [ ]5. Tercera guarda: si `len(filas) == 1`, imprimir el aviso "Sin análisis: el historial tiene un solo registro." y retornar `None`, porque no hay contra qué comparar y un `es_oferta: False` confundiría "no es oferta" con "sin datos".
- [ ]6. Separar el historial: `fila_actual = filas[-1]` (la más reciente por `fecha ASC, id ASC`), `precio_actual = fila_actual["precio_usd"]` y `precios_previos = [fila["precio_usd"] for fila in filas[:-1]]`.
- [ ]7. Calcular `precio_referencia = obtener_precio_referencia(precios_previos)`.
- [ ]8. Cuarta guarda, antes de cualquier comparación numérica: si `precio_referencia is None`, imprimir el aviso correspondiente y retornar `None`, porque `None > 0` lanza `TypeError` en Python 3.
- [ ]9. Quinta guarda: si `precio_referencia <= 0`, imprimir el aviso de referencia no positiva y retornar `None`, evitando la división inválida de `calcular_caida`.
- [ ]10. Sexta guarda, independiente de la anterior: si `precio_actual is None` o `precio_actual <= 0`, imprimir el aviso de precio actual no positivo y retornar `None`, porque un `0` produciría una caída del `100 %` y un falso `es_oferta: True`.
- [ ]11. Calcular `caida_porcentual = calcular_caida(precio_referencia, precio_actual)` con la referencia ya validada como positiva.
- [ ]12. Construir y retornar el `Veredicto` con exactamente siete claves: `asin` (el `str` ya validado), `titulo` (de `fila_actual["titulo"]`, `str | None`), `precio_referencia_usd` (`float`), `precio_actual_usd` (`float`), `caida_porcentual` (`float`), `es_oferta` (`caida_porcentual >= UMBRAL_CAIDA_PRECIO`, comparación `>=`) y `moneda` (`"USD"` fijo).
- [ ]13. Ser la única función que arma el diccionario del veredicto: ningún otro camino lo reconstruye ni renombra claves.
- [ ]14. No escribir, no hacer `commit`, `rollback` ni `close`, y no capturar las excepciones de SQLite: las degrada el llamador.

### Subtarea 4.2: `analizar_oferta` — fachada de análisis por ASIN
Flujo de comportamiento:
- [ ]1. Declarar `def analizar_oferta(conn: sqlite3.Connection, asin: str) -> dict | None` como fachada pública del módulo.
- [ ]2. Primera guarda: si `conn is None`, imprimir el aviso "Sin análisis: conexión inválida." y retornar `None`.
- [ ]3. Segunda guarda: si `asin` no es `str` o queda vacío tras `strip()`, imprimir el aviso "Sin análisis: ASIN inválido." y retornar `None`.
- [ ]4. Envolver el resto del cuerpo en `try/except Exception` para no propagar excepciones al llamador (degradación elegante, §4 de la Constitución).
- [ ]5. Resolver el identificador con `producto_id = buscar_id_producto(conn, asin)`: la entrada es siempre el ASIN, nunca el id entero.
- [ ]6. Si `producto_id is None`, imprimir el aviso de producto no registrado y retornar `None`.
- [ ]7. Delegar en `return _analizar_por_id(conn, producto_id, asin)`, pasando el ASIN validado para que el veredicto lo devuelva en `asin`.
- [ ]8. En el bloque de excepción, imprimir el aviso "Sin análisis: <mensaje de la excepción>." y retornar `None`, sin `commit`, `rollback` ni `close` sobre la conexión del llamador y sin convertir un fallo de lectura en "no es oferta".

## Tarea Principal 5: Fachada de lote

### Subtarea 5.1: `analizar_productos` — veredictos de todos los productos con historial
Flujo de comportamiento:
- [ ]1. Declarar `def analizar_productos(conn: sqlite3.Connection) -> list[dict]` con retorno `[]` garantizado, nunca `None`, en todas las ramas.
- [ ]2. Primera guarda: si `conn is None`, imprimir el aviso "Sin análisis: conexión inválida." y retornar `[]`.
- [ ]3. Obtener el listado con `obtener_productos_con_historial(conn)` dentro de `try/except Exception`; si falla, imprimir el aviso con el mensaje de la excepción y retornar `[]`.
- [ ]4. Recorrer el listado con un acumulador `veredictos: list[dict] = []` y, por cada elemento `ProductoConHistorial`, llamar `_analizar_por_id(conn, producto["producto_id"], producto["asin"])` sin volver a resolver el ASIN.
- [ ]5. Añadir al acumulador solo los veredictos no nulos; cuando la función devuelve `None` (ASIN inválido, historial insuficiente, precios inválidos) ya fue avisado dentro de `_analizar_por_id`, así que se continúa con el siguiente producto.
- [ ]6. Envolver cada iteración en `try/except Exception`: ante un fallo de SQLite o un dato atípico, imprimir el aviso "Sin análisis para <asin>: <mensaje>." y continuar con el producto siguiente, de modo que un error no detenga el lote.
- [ ]7. Retornar la lista final sin `None` intercalados y sin veredictos con `asin: None`, porque la guarda de la Subtarea 4.1 descarta esos productos.
- [ ]8. No escribir ni hacer `commit`/`rollback`/`close`, y aceptar el coste `N + 1` consultas (el listado más un historial por producto).

## Tarea Principal 6: Modo ejecutable

### Subtarea 6.1: `main` — ejecución de solo lectura sobre la BD existente
Flujo de comportamiento:
- [ ]1. Declarar `def main() -> None` y construir `argparse.ArgumentParser` con un único argumento posicional y obligatorio `asin`, más su descripción; `argparse` no se usa en ninguna función de biblioteca.
- [ ]2. Parsear con `parse_args()` y leer la ruta con `ruta = Path(settings.DB_PATH_TRACKER)`, como atributo del módulo `settings` para que la ruta sea parcheable en pruebas.
- [ ]3. Si `not ruta.exists()`, imprimir el aviso de BD inexistente con la ruta esperada y salir con `raise SystemExit(1)`: `sqlite3.connect` crearía un archivo vacío y el `SELECT` fallaría después con `no such table`, dejando un rastro de escritura en una operación de solo lectura.
- [ ]4. Inicializar `conn = None` antes del `try` y abrir `conn = sqlite3.connect(f"file:{ruta}?mode=ro", uri=True)` dentro de él, cerrando en el `finally` solo con `if conn is not None: conn.close()`: si `sqlite3.connect` falla (ruta que no es un archivo regular, permisos, archivo ilegible) el `finally` no debe sustituir el error real por un `UnboundLocalError`; el cierre pertenece al script, no a las fachadas.
- [ ]5. Llamar `veredicto = analizar_oferta(conn, argumentos.asin)`.
- [ ]6. Si `veredicto is None`, imprimir el aviso "Sin análisis: no hay veredicto para el ASIN indicado." y retornar sin más operaciones.
- [ ]7. Si hay veredicto, imprimir sus siete campos con un bucle `for campo, valor in veredicto.items()`; ninguna función del módulo devuelve el veredicto por `stdout`.

### Subtarea 6.2: bloque `if __name__ == "__main__"` — entrada del script
Flujo de comportamiento:
- [ ]1. Añadir al final del archivo `if __name__ == "__main__": main()`, sin lógica adicional en el bloque.
- [ ]2. Verificar que `python -m services.analizador <ASIN>` funciona desde la raíz del proyecto y que `python services/analizador.py <ASIN>` funciona gracias al guard de la Subtarea 3.1.
- [ ]3. No leer `sys.argv` fuera de `main()`, para que `analizar_oferta` y `analizar_productos` sean reutilizables por un llamador externo y testeables sin parchear argumentos.

## Tarea Principal 7: Verificación aislada

### Subtarea 7.1: entorno temporal, firmas del módulo y umbral único
Flujo de comportamiento:
- [ ]1. Crear el archivo temporal `test_tmp_analizador_ofertas.py`, con nombre sin `/` ni espacios (§6.4 de `AGENTS.md`), y una fixture que parchee **ambos** nombres de la ruta antes de inicializar: `monkeypatch.setattr(config.settings, "DB_PATH_TRACKER", str(tmp_path / "tracker.db"))` y `monkeypatch.setattr(database.schema, "DB_PATH_TRACKER", str(tmp_path / "tracker.db"))`, porque `schema.py` ata la ruta por valor y `init_sqlite_db()` usa ese global; en la misma fixture aislar `services.currency`, que ata por valor `DEFAULT_CURRENCY` y `RUTA_TASAS_CAMBIO`, con `monkeypatch.setattr(services.currency, "DEFAULT_CURRENCY", None)` y `monkeypatch.setattr(services.currency, "RUTA_TASAS_CAMBIO", str(tmp_path / "tasas_cambio.json"))`, para que ninguna ruta de conversión alcance la red ni el JSON real de `database/`.
- [ ]2. Inicializar la BD temporal con `init_sqlite_db()` y abrir la conexión de prueba a `tmp_path`, sin tocar `database/tracker.db`; como `obtener_o_crear_producto` e `insertar_historial_precio` no confirman la transacción, toda siembra de la batería termina con `conn.commit()` para que una conexión nueva (el `main()` de la Subtarea 7.8 y los subprocesos de la Subtarea 7.9) vea los datos.
- [ ]3. Importar `services.analizador` y comprobar con `inspect.signature` la existencia y las firmas de `analizar_oferta`, `analizar_productos`, `obtener_precio_referencia`, `calcular_caida` y `_analizar_por_id`, y que cada `return` respeta el tipo declarado, incluidos `None` y `[]`.
- [ ]4. Comprobar `config.settings.UMBRAL_CAIDA_PRECIO == 0.15`, que `PRICE_DROP_THRESHOLD` ya no existe en el módulo y que `services.analizador` no define una constante de umbral propia.
- [ ]5. Comprobar que la cadena `database.schema → services.currency` se importa sin red y que ninguna prueba invoca `convertir_a_moneda_local`.

### Subtarea 7.2: caída suficiente, frontera y caída insuficiente
Flujo de comportamiento:
- [ ]1. Sembrar un producto y tres filas de historial en la BD temporal con `obtener_o_crear_producto` + `insertar_historial_precio` (nunca con `guardar_datos_producto`, que dispararía `convertir_a_moneda_local`), con la última un 20 % por debajo del mínimo previo, y verificar `es_oferta: True`, `caida_porcentual >= 0.15` y `titulo` no vacío proveniente del JOIN con `Productos`.
- [ ]2. Frontera exacta: `precio_referencia_usd = 100.0` con `precio_actual_usd = 85.0` → `es_oferta: True`, porque el cociente `15.0 / 100.0` coincide con el `double` de `0.15`; con `precio_actual_usd = 85.01` → `es_oferta: False`.
- [ ]3. Caída insuficiente y precio igual o mayor que la referencia → veredicto con `es_oferta: False` y `caida_porcentual == 0.0` o positivo pequeño, comprobando que es un `dict` y no `None`.
- [ ]4. Comprobar el conjunto exacto de siete claves del veredicto, sus tipos y `moneda == "USD"` en todos los casos de esta subtarea.

### Subtarea 7.3: desempate temporal y precios inválidos
Flujo de comportamiento:
- [ ]1. Insertar con `INSERT` directo (nunca con `guardar_datos_producto`) dos filas del mismo producto con `fecha` idéntica y `precio_usd` distinto, y verificar que el precio actual es el de `id` mayor; repetir la consulta varias veces para confirmar que el veredicto no depende del orden interno de SQLite.
- [ ]2. Verificar que `obtener_ultimo_registro` devuelve el mismo precio para ese producto, por el desempate alineado de la Subtarea 2.3.
- [ ]3. Referencia inválida: primera fila con `precio_usd` cero y caso con `precio_usd` negativo, insertadas con SQL directo → `None` con aviso, sin `ZeroDivisionError` ni `TypeError`.
- [ ]4. Precio actual inválido: fila más reciente con `precio_usd` cero y caso con `precio_usd` negativo → `None` con aviso, nunca `es_oferta: True` con caída `1.0` o mayor.

### Subtarea 7.4: casos sin análisis posible
Flujo de comportamiento:
- [ ]1. Verificar `None` con aviso distinto en historial vacío y en historial con un solo registro.
- [ ]2. Verificar `None` con aviso cuando el ASIN no está registrado en `Productos`.
- [ ]3. Verificar `None` con aviso "ASIN inválido" para `asin` vacío, `asin` con solo espacios y `asin` no-`str` (`None`, `123`), sin excepción.
- [ ]4. Verificar `None` con aviso con `conn` `None` y con `conn` cerrada, sin propagar `sqlite3.ProgrammingError`.
- [ ]5. Verificar `[]`, nunca `None`, en `analizar_productos` con `conn` `None` y con `conn` cerrada.

### Subtarea 7.5: moneda estable y solo lectura
Flujo de comportamiento:
- [ ]1. Mezclar, con `INSERT` directo (nunca con `guardar_datos_producto`), filas con `moneda_local` `COP` real y filas con *fallback* USD en el mismo producto, con precios en `precio_usd` conocidos, y verificar que el veredicto depende solo de `precio_usd`.
- [ ]2. Sembrar al menos una fila en cada una de las tres tablas y contar sus filas desde una segunda conexión al archivo parcheado de `tmp_path` antes y después de ejecutar `analizar_oferta` y `analizar_productos` cinco veces; los conteos deben ser idénticos y mayores que cero en las tres tablas, para que la comprobación no se cumpla de forma vacua sobre una BD sin filas.
- [ ]3. Verificar que `database/tracker.db` no cambia de contenido ni de fecha de modificación en toda la batería.

### Subtarea 7.6: comportamiento del lote
Flujo de comportamiento:
- [ ]1. Producto con una sola fila de historial → se omite con aviso y no aparece en la lista devuelta.
- [ ]2. Sustituir `services.analizador.obtener_historial_precios` (el nombre importado en el módulo del analizador, no `database.schema.obtener_historial_precios`) por una función que lanza `sqlite3.OperationalError` para un producto: ese no aparece en el resultado, los demás veredictos se producen igual, la lista no contiene `None` y las claves son las mismas que las del camino individual.
- [ ]3. `conn` inválida o fallo de `obtener_productos_con_historial` → `[]` con aviso, nunca `None`.
- [ ]4. Fila de `Productos` con `asin` `NULL` y con historial, sembrada con `INSERT` directo (nunca con `guardar_datos_producto`) → se omite con aviso y ningún veredicto del lote contiene `asin: None`.
- [ ]5. Comparar el veredicto del lote con el de `analizar_oferta` para el mismo ASIN y exigir diccionarios idénticos en claves y valores.

### Subtarea 7.7: lock de escritor concurrente
Flujo de comportamiento:
- [ ]1. Abrir una conexión auxiliar sobre la BD temporal con `isolation_level=None`, ejecutar `BEGIN EXCLUSIVE` y dejar un `INSERT` sin confirmar: es el lock exclusivo que sí bloquea a los lectores con el journal por defecto (una transacción diferida con `INSERT` solo retiene el lock `RESERVED` y el lector leería la última versión confirmada); la conexión de lectura se abre con `sqlite3.connect(ruta, timeout=0.1)` para que el `OperationalError: database is locked` llegue sin agotar los cinco segundos por defecto.
- [ ]2. Verificar que el producto se reporta como "sin análisis" con aviso en `analizar_oferta` y que se omite en `analizar_productos`, nunca con `es_oferta: False`.
- [ ]3. Cerrar la conexión auxiliar con su `rollback` al final de la prueba, sin dejar la BD bloqueada para el resto de la batería.

### Subtarea 7.8: modo script y BD ausente
Flujo de comportamiento:
- [ ]1. Parchear `config.settings.DB_PATH_TRACKER` y `database.schema.DB_PATH_TRACKER` hacia `tmp_path`, fijar `sys.argv = ["analizador", <ASIN>]` y capturar la salida con `capsys`: `main()` imprime el veredicto del producto.
- [ ]2. Comprobar tras la ejecución que `database/tracker.db` no cambia de contenido ni de fecha de modificación.
- [ ]3. Apuntar `DB_PATH_TRACKER` a un archivo inexistente de `tmp_path` y verificar aviso claro, `SystemExit` con código distinto de cero y que el archivo **no** se crea.

### Subtarea 7.9: ejecución directa y como paquete
Flujo de comportamiento:
- [ ]1. Ejecución directa: resolver la ruta del módulo a **absoluta antes** del `chdir`, usar un `cwd` temporal vacío y un `PYTHONPATH` sin la raíz del proyecto (copia de `os.environ` con la raíz eliminada del valor heredado); el envoltorio `python -c` no importa ningún módulo del proyecto, imprime `RAIZ_ANTES` con `sys.path.count(str(raiz))`, ejecuta `runpy.run_path(<ruta absoluta>, run_name="analizador")` e imprime `RAIZ_DESPUES` con el mismo recuento.
- [ ]2. Exigir sobre la salida de ese mismo subproceso `RAIZ_ANTES == 0` y `RAIZ_DESPUES == 1`, de modo que la aserción falla si el guard falta, si está colocado detrás de un import absoluto del proyecto o si inserta la raíz dos veces.
- [ ]3. Con la raíz ya resuelta, parchear en `globals_modulo` el `DB_PATH_TRACKER` del módulo `settings` y el de `database.schema` (ya cargado en `sys.modules`), fijar `sys.argv` y llamar `globals_modulo["main"]()`: imprime el veredicto desde la BD de `tmp_path` sin abrir `database/tracker.db`.
- [ ]4. Como paquete: subproceso con `cwd` en la raíz del proyecto o con `PYTHONPATH` apuntando a ella, los dos `DB_PATH_TRACKER` parcheados hacia `tmp_path`, `sys.argv` fijado y `runpy.run_module("services.analizador", run_name="__main__")`; la única aserción es que el veredicto impreso coincide con el de la ejecución directa, sin recuento de `sys.path`.
- [ ]5. Verificar que `import services.analizador` no altera `sys.path`.

### Subtarea 7.10: `py_compile` y cierre de la batería
Flujo de comportamiento:
- [ ]1. Ejecutar `py_compile` sobre `config/settings.py`, `database/schema.py` y `services/analizador.py`.
- [ ]2. Ejecutar toda la batería con `.venv/bin/python -m pytest`, sin acceso a red, sin escribir archivos del proyecto y sin tocar `database/tracker.db`.
- [ ]3. Si todas las pruebas pasan, eliminar el archivo temporal, `__pycache__` y `.pytest_cache` conforme §6.4 de `AGENTS.md`; si alguna falla, conservarlo todo con las trazas y reportar según §6.2.

## Tarea Principal 8: Cierre documental

Depende de la Tarea Principal 7 con la batería en verde.

### Subtarea 8.1: `README.md` — umbral, analizador implementado y modo de uso
Flujo de comportamiento:
- [ ]1. Sustituir las tres referencias a `PRICE_DROP_THRESHOLD` por `UMBRAL_CAIDA_PRECIO` en las características, la tabla de constantes y el roadmap, eliminando en esa misma edición la condición de "aún sin consumir" y la nota de que "este módulo no existe todavía": la constante queda descrita como la caída mínima del 15 % que el analizador consume.
- [ ]2. Mover la viñeta del analizador de ofertas de la sección "Planificado… AÚN NO presente" a las características implementadas, y corregir las afirmaciones de "Estado actual" y de "Arquitectura del sistema" que niegan su existencia ("No hay módulo de notificaciones ni analizador de ofertas implementados", "aún no existe analizador de ofertas ni notificaciones que consuman ese historial"), manteniendo las notificaciones de Telegram como pendientes.
- [ ]3. Añadir `services/analizador.py` al árbol de archivos, documentar el comando `python -m services.analizador <ASIN>` en el ejemplo de uso y añadir su fila a la tabla de "Scripts disponibles", junto a `python -m database.schema` y `python main.py`, ajustando la presentación de la tabla para que la invocación con `-m` figure entre las formas de ejecutar esos bloques `if __name__ == "__main__":`.
- [ ]4. Marcar como implementado el paso 5 del flujo de datos (el analizador compara el precio actual contra el historial con `UMBRAL_CAIDA_PRECIO`), dejar el paso 6 de Telegram como no implementado y ajustar el encabezado del flujo, que hoy anuncia implementado solo hasta el paso 4.
- [ ]5. Marcar el paso 4 del roadmap como implementado y mantener como pendientes las notificaciones de Telegram y el enganche en `main.py`; no tocar las secciones históricas que documentan lo entregado entonces.
- [ ]6. En "Pendientes de documentar", retirar "un analizador de ofertas" de la viñeta "Módulos planeados aún inexistentes", de modo que solo `notifications/telegram.py` quede como módulo planeado, y sustituir el paréntesis "el alcance actual prioriza la persistencia en SQLite" por la prioridad vigente, las notificaciones de Telegram sobre el historial ya persistido.

### Subtarea 8.2: `MEMORY.md` — estado del roadmap
Flujo de comportamiento:
- [ ]1. Registrar el paso 4 ("Desarrollar Analizador de Ofertas") como completado en §5, sustituyendo en esa misma línea `PRICE_DROP_THRESHOLD = 0.15` por `UMBRAL_CAIDA_PRECIO = 0.15` e indicando que el renombre se aplicó en `config/settings.py`, y actualizar el estado global con el paso 5 como siguiente.
- [ ]2. Añadir en §3 el registro de la ronda: helpers de lectura sin `commit`, `_analizar_por_id` como única constructora del veredicto, umbral único en `config.settings` y solo lectura verificada.
- [ ]3. Mantener §4 sin cambios: el contrato de datos del scraper sigue con las siete claves.

### Subtarea 8.3: `AGENTS.md` — pendiente inmediato y patrones de la ronda
Flujo de comportamiento:
- [ ]1. Sustituir en §5 el "Pendiente Inmediato" del analizador por el paso 5 (notificaciones de Telegram) e indicar que el umbral se llama ya `UMBRAL_CAIDA_PRECIO`.
- [ ]2. Añadir en §6.3 los patrones de la ronda: guardas en orden fijo antes de una comparación numérica, `0` en la fila actual como falso `es_oferta: True`, constructora única del veredicto entre fachada y lote, y guard de `sys.path` antes del primer import absoluto del proyecto.
- [ ]3. No tocar las secciones históricas de rondas anteriores.
