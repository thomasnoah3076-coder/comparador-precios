# 🤖 Directrices para Agentes de IA (Project Agents)

Este documento define el comportamiento, los roles y el flujo de trabajo estricto que cualquier Agente de IA debe seguir al colaborar en este proyecto.

## 1. Contexto del Proyecto
*   **Descripción:** Un comparador de precios personal y automatizado. Rastrea productos, guarda historiales, evalúa ofertas y enviará notificaciones por Telegram.
*   **Escala y Volumen:** Es un proyecto de **carácter personal**. Maneja un volumen de datos bajo/moderado (SQLite es suficiente), pero requiere **alta robustez** en la obtención de datos debido a los sistemas anti-scraping (especialmente de Amazon).
*   **Arquitectura:** Sigue el patrón *Template Method*. 
    *   El orquestador (`BaseScraper`) maneja la infraestructura: Playwright, base de datos SQLite, control de flujo y detección de bloqueos (CAPTCHAs).
    *   Los especialistas (ej. `AmazonScraper`) manejan únicamente la extracción de datos desde el DOM usando selectores específicos y retornan un contrato de datos estricto (`titulo`, `precio`, `moneda`, `url`, `vendedor`, `ventas`, `calificacion_promedio`).
*   **Stack Tecnológico:** Python, SQLite, Playwright, BeautifulSoup, python-dotenv.

## 2. Perfil del Usuario (El Director)
*   El usuario comprende la lógica de programación, el flujo de datos y la arquitectura de software.
*   Prefiere entender el **QUÉ** y el **POR QUÉ** antes del **CÓMO**. 
*   No se le debe abrumar con código fuente a menos que lo solicite explícitamente o sea el momento de la ejecución aprobada.
*   El usuario es el Director del proyecto; la IA actúa como Arquitecto (Planeación) y Desarrollador Senior (Ejecución).

## 3. Roles de la IA
La IA debe alternar entre dos modos o roles según la fase de la conversación:

### 🎭 Rol 1: El Arquitecto (Fase de Planeación)
*   **Objetivo:** Analizar problemas, diseñar soluciones lógicas y proponer la arquitectura.
*   **Comportamiento:** Evalúa el impacto de los cambios. Identifica fallas lógicas. Propone el *Qué* se va a hacer y de manera descriptiva el *Cómo*, **sin escribir el código final**.

### 🎭 Rol 2: El Ejecutor (Fase de Desarrollo)
*   **Objetivo:** Escribir código limpio, modular, escalable y con manejo de errores, basado *únicamente* en los planes aprobados por el Director.
*   **Comportamiento:** Implementa el código respetando el stack tecnológico y la separación de responsabilidades (ej. no mezclar lógica de BD dentro del scraper específico).

## 4. Flujo de Trabajo Obligatorio (Strict Workflow)
Para garantizar la continuidad y evitar que la IA alucine o repita errores, **CADA INTERACCIÓN** de ejecución debe seguir este ciclo:

1.  **Paso 0: Lectura de Memoria (Obligatorio).**
    *   Antes de planear o ejecutar nada, la IA debe solicitar o revisar el contenido del archivo `MEMORY.md` (el cual contiene el estado actual exacto del código y las últimas decisiones tomadas).
2.  **Paso 1: Propuesta (El QUÉ y el CÓMO).**
    *   Asumiendo el rol de *Arquitecto*, la IA debe presentar una propuesta clara de los pasos a seguir. Debe describir *qué* archivos modificará y *cómo* abordará la lógica, pidiendo la aprobación del Director.
3.  **Paso 2: Aprobación.**
    *   La IA entra en pausa y espera la confirmación explícita del usuario ("Adelante", "Aprobado", o correcciones a la propuesta).
4.  **Paso 3: Ejecución.**
    *   Asumiendo el rol de *Ejecutor*, la IA genera el código necesario siguiendo los estándares de calidad del proyecto.
5.  **Paso 4: Actualización de Estado (Cierre de Ciclo).**
    *   Tras una ejecución exitosa, la IA **debe** proponer la actualización del archivo `MEMORY.md` resumiendo lo que se acaba de implementar, para que el contexto no se pierda en futuros chats.
    *   Si durante el desarrollo se descubren nuevas reglas arquitectónicas o patrones recurrentes, la IA debe sugerir añadir una regla a este mismo archivo `AGENTS.md`.

## 5. Estado Actual del Proyecto (Punto de Partida)
*   *Scrapers:* Foco exclusivo en el scraper de Amazon (`AmazonScraper`) para validar el flujo completo end-to-end.
*   *Bloqueo principal resuelto lógicamente:* Se separó la responsabilidad del `BaseScraper` (maneja BD y Playwright) y del `AmazonScraper` (solo extrae datos del DOM).
*   *Completado:* Detección de bloqueos de Amazon (CAPTCHAs) en `BaseScraper` (`verificacion_de_estado_html`), y `AmazonScraper` devolviendo el contrato de datos limpio.
*   *Pendiente Inmediato:* Implementar la persistencia en SQLite (roadmap paso 3 de `MEMORY.md`): los datos scrapeados aún no se insertan en la BD.

## 6. Diagnóstico y Reporte de Errores (Reglas Obligatorias)
Cuando se ejecute un método (p. ej. `/probar-metodo`) y algo falle, el agente DEBE aplicar estas reglas. El objetivo es que el Director entienda el **QUÉ falló, POR QUÉ y CÓMO se arregla** sin tener que leer el código.

### 6.1 Antes de reportar: separar la causa raíz de los síntomas
*   Ejecutar el fallo **una sola vez** y guardar el traceback real. No reportar de memoria ni "reconstruir" el error: copiar la salida literal de la terminal.
*   **Encadenar los errores:** un fallo de importación tapa todos los demás. Probar el método con un *stub* temporal (fuera del proyecto) para descubrir qué falla **después** de corregir el primer error, y reportar la cadena completa (`importación → ejecución → lógica`), no solo la primera capa.
*   Distinguir siempre: **fallo de entorno** (dependencia, `venv` roto, red) vs. **fallo del código**. Un `venv` apuntando a un intérprete inexistente no es un bug del método: declararlo aparte para no culpar al código.

### 6.2 Estructura mínima del reporte de errores
1.  **Errores detectados:** salida real (traceback / `pytest`) entre bloque de código.
2.  **Clasificación** en una de estas categorías, y para CADA error: `archivo:línea`, qué ocurrió y **UNA** frase con la solución propuesta:
    *   **Errores de sintaxis:** Python no puede interpretar el código.
    *   **Errores de lógica:** corre pero devuelve un resultado incorrecto (contrato roto, `0` donde debe haber `None`, etc.).
    *   **Errores de ejecución:** excepción en tiempo de ejecución (`TypeError`, `KeyError`, `AttributeError`, `ValueError`...).
3.  **Pendiente por corregir o implementar:** lista ordenada y accionable.

### 6.3 Errores conocidos del proyecto (anticiparlos, no redescubrirlos)
Estos patrones han fallado ya una vez. Verificarlos **antes** de concluir que un método funciona:
*   **`async` vs síncrono:** `BaseScraper.obtener_dom` es `async`. Si un método síncrono hace `self.obtener_dom(url)` sin `await`, no obtiene HTML: obtiene una corrutina y el fallo aparece más tarde dentro de BeautifulSoup. Verificar con `inspect.iscoroutinefunction`.
*   **Contrato de datos (MEMORY.md §4):** las claves deben ser `titulo`, `precio`, `moneda`, `url`, `vendedor`, `ventas`, `calificacion_promedio`. Devolver claves en inglés (`title`/`price`/...) o variantes propias (`nombre`/`rating`) es un **error de lógica**, aunque no lance excepción.
*   **Llamar a métodos inexistentes:** comprobar con `hasattr` que todo lo invocado en `extraer_datos` existe en la clase (p. ej. `extraer_ventas_y_rating` no existe).
*   **Comparaciones mal escritas:** `any(lista) in texto` lanza `TypeError: 'in <string>' requires string as left operand, not bool`. Lo correcto es `any(palabra in texto for palabra in lista)`.
*   **`None` implícito:** una función `-> str` sin `return` en todas las ramas devuelve `None`; usar `""` o `None` de forma **explícita** y documentada.
*   **Precio ausente:** devolver `0` es indistinguible de "gratis". El contrato exige `None` para "no encontrado".
*   **`.venv` roto / intérprete inexistente:** antes de ejecutar cualquier prueba, verificar que `.venv/bin/python` existe de verdad y que su versión coincide con `lib/pythonX.Y/site-packages` (en Oct 2026 el venv apuntaba a python3.12 mientras los paquetes —`greenlet` compilado— eran de python3.11, y no había `python3.11` en el sistema → `ModuleNotFoundError: greenlet._greenlet`). Es un **fallo de entorno**, no del método: declararlo aparte y no culpar al código.

Patrones detectados en la **2ª ronda de pruebas** (Oct 2026, `AmazonScraper.extraer_datos` async):
*   **Doble navegación:** `obtener_datos` baja el DOM con `obtener_dom(url)` y se lo pasa a `extraer_datos`, pero `extraer_datos` vuelve a llamar a `obtener_dom(url)`. Se navega dos veces y, encima, se le pasa un HTML donde la firma espera una URL. *(Verificado corregido: hoy `obtener_datos` solo hace `await self.extraer_datos(url)` y la extracción navega una única vez.)*
*   **Conversión numérica sin podar el texto:** `float("1,234.99")`, `int("1234 ratings")` y `float("4.7 de 5")` lanzan `ValueError`. Antes de convertir: quitar comas de miles, y quedarse con el primer grupo numérico vía `re.match(r"\d+(?:[.,]\d+)?", texto)`.
*   **Condicional demasiado exigente:** exigir `if tag_entero and tag_decimal` descarta precios válidos enteros ("29" sin fracción). Si falta la parte decimal, asumir `".00"`.
*   **Comparación de mayúsculas/minúsculas asimétrica:** `formato_cop` contiene `'COP'` pero se compara contra `moneda.lower()`, que es `'cop'` → la moneda COP **nunca** se detecta. Normalizar ambos lados (`lower()`) antes de comparar.
*   **`0` como "sin dato":** `extraer_calificacion_promedio` devuelve `0` si no hay rating, mientras que precio y ventas devuelven `None`. Elegir UN criterio (`None`) y aplicarlo en todo el contrato.
*   **Falta validación de entrada:** `extraer_datos` no valida `url` (`None`, vacía o no-str) y no lanza nada; las pruebas `pytest.raises` quedan en `DID NOT RAISE`. Validar al inicio con `if not isinstance(url, str) or not url.strip(): raise ValueError(...)`.
*   **Bloque `__main__` no ejecutable:** `python scrapers/AmazonScraper.py` da `ModuleNotFoundError: No module named 'scrapers'` (la raíz del proyecto no está en `sys.path` cuando se ejecuta el archivo directamente). Ejecutar con `python -m scrapers.AmazonScraper` desde la raíz; además harían falta `conn` en el constructor y `await` en la llamada.

Patrones detectados en la **3ª ronda de pruebas** (Oct 2026, `AmazonScraper.extraer_calificacion_promedio`, 13 pruebas en verde):
*   **Nombre "mangled"/con typos en la consigna:** el encargo puede nombrar el método en lenguaje natural (`extrear calificacion promedio de amazon scraper`). Buscar por **coincidencia parcial** (`calificacion_promedio`) en `*.py`, avisar el nombre real (`extraer_calificacion_promedio`) y **no concluir que no existe**.
*   **Anotación de retorno vs ramas reales:** una firma `-> float` con `return None` en dos ramas es un **error de contrato/tipado**, NO de ejecución (no lanza nada). Anticiparlo comparando la anotación con cada `return` y clasificarlo como lógica/contrato.
*   **Regex anclado al inicio rechaza negativos:** `re.match(r'\d+(?:[.,]\d+)?', ...)` exige que el texto **empiece** por dígito → `"-4.7 de 5"` devuelve `None` (no `-4.7`). Es una observación de lógica (correcto: los ratings no son negativos), no un fallo de ejecución.
*   **`AttributeError` "natural" ≠ validación explícita:** si el método no valida su argumento, pasarle `None`/`int`/`str` lanza `AttributeError` al acceder a `.select_one`, lo que hace **pasar** `pytest.raises(AttributeError)`. Distinguir en el reporte "lanza por accidente" de "valida a propósito"; si no lanzara, sería `DID NOT RAISE` (§6.3).
*   **`0` explícito ≠ `None`:** `"0 de 5"` → `0.0` (rating real) y `"Sin reseñas"`/tag ausente → `None`. Verificar **ambas** ramas para no confundir "cero de cinco" con "sin dato".
*   **Verificado corregido:** `extraer_calificacion_promedio` ya **no** devuelve `0` cuando falta el rating; devuelve `None` (confirmado con `test_sin_rating_devuelve_none_no_cero`). El patrón de la 2ª ronda *"`0` como sin dato"* quedó resuelto para este método.
*   **Selectores por clase genérica = frágiles entre productos:** `span.a-size-small.a-color-base` (rating) **no existe en algunos productos** y el método falla al cambiar de producto. Para el rating usar el **`data-hook` oficial de Amazon** `span[data-hook="rating-out-of-text"]` (texto `"4.7 out of 5"`, 1 coincidencia estable). Regla general: preferir atributos **`data-hook`** de Amazon sobre clases CSS genéricas, y **verificar contra el DOM real de varios productos** (Playwright) antes de concluir que un selector es robusto.

Patrones detectados en la **4ª ronda** (Oct 2026, auditoría código vs documentación, 13 pruebas en verde):
*   **`TIMESTAMP` vs `date` en comparaciones:** `fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP` guarda `'2026-10-14 12:15:20'`, y compararlo con `date.today().isoformat()` (`'2026-10-14'`) con `==` **nunca es verdadero** → `ya_se_consulto_hoy()` devolvía siempre `False` y la caché diaria estaba inoperante. Corregido con `.startswith(hoy)`. Regla: ante fechas de BD, comparar solo la parte de fecha o usar `DATE(fecha)` en SQL.
*   **Claves divergentes entre caminos del orquestador:** `obtener_datos()` puede devolver el registro de la BD o el del scraping; si un camino usa `nombre`/`rating` y el otro `titulo`/`calificacion_promedio`, `main.py` imprime claves distintas según el origen. Corregido en `obtener_ultimo_registro()`. Regla: **ambos caminos deben producir exactamente las mismas claves** (contrato MEMORY §4) y cubrirlo con una prueba que compare los dos diccionarios.
*   **Firma abstracta sync ≠ firma concreta async:** `@abstractmethod def extraer_datos` con `async def extraer_datos` en la hija no lanza error en Python, pero `await` en el orquestador rompería con cualquier implementación síncrona futura. Corregido: la abstracta ahora es `async def`. Verificar con `inspect.iscoroutinefunction` en **ambas**.
*   **Función que imprime pero no retorna:** `currency_converter()` ejecutaba `amount_calculate(...)` sin `return`, así que el valor convertido solo aparecía por consola y la función devolvía `None` (el ejemplo del README obtenía `None`). Regla: si la función promete un resultado (`-> float` o se asigna a una variable), **todas** las ramas felices deben llevar `return` explícito.

Patrones detectados en la **5ª ronda** (Oct 2026, corrección de los 2 errores hallados en la auditoría, 7 pruebas en verde):
*   **Ejecución directa vs `-m` (`sys.path`):** al ejecutar `python database/schema.py`, Python pone en `sys.path` el directorio del archivo (`database/`), no la raíz del proyecto → `from config.settings import ...` lanza `ModuleNotFoundError: No module named 'config'`. Corregido con un **arranque de ruta condicionado** en `schema.py`: `if __package__ in (None, ""): sys.path.insert(0, raíz_del_proyecto)`. El guard es clave: al importar como paquete (`__package__ == "database"`) o correr con `-m`, **no** se toca `sys.path` (verificado: sin duplicados). Regla: si un módulo debe poder ejecutarse directamente, usar este patrón; el test adecuado es un **subproceso con `runpy.run_path(..., run_name='sin_puntos')`** en un cwd aislado (reproduce el `__package__` vacío del script directo SIN disparar el bloque `__main__` ni tocar la BD real).
*   **`CREATE TABLE` sin `IF NOT EXISTS`:** `init_sqlite_db()` reventaba con `sqlite3.OperationalError: table Productos already exists` al re-ejecutarse, contraviniendo la regla de idempotencia de `docs/constitution.md` §3 ("La ejecución del sistema debe ser segura de repetir"). Corregido con `IF NOT EXISTS` en los 3 `CREATE TABLE` (no destructivo: tablas/datos existentes sobreviven — cubierto con prueba que inserta fila, re-inicializa y verifica). Regla: toda creación de tablas/archivos en el arranque del sistema debe ser idempotente; verificar con una doble ejecución en la batería.

### 6.4 Reglas de los archivos de prueba temporales
*   Un nombre de archivo **no puede contener `/` ni espacios**: si la consigna pide una URL en el nombre, sanitizar y guardar la URL dentro del archivo; si el nombre viene del método con espacios/typos (p. ej. `test_tmp_extrear calificacion promedio ... .py`), pasar los espacios a guiones bajos —**un módulo Python/pytest no puede tener espacios: rompe la recolección**— y dejar la equivalencia en un comentario cabecera.
*   Aislar SIEMPRE red, archivos y BD (`monkeypatch`/`unittest.mock`). Ninguna prueba debe depender de Amazon ni de `tracker.db`.
*   Si **todas** las pruebas pasan → borrar el archivo temporal, `__pycache__` y `.pytest_cache` y anunciar el éxito.
*   Si **alguna** prueba falla → conservarlo TODO (prueba, cachés y trazas) para que el Director pueda revisarlo, y generar el reporte de la §6.2.