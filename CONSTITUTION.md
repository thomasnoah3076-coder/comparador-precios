# Constitución del Proyecto (Code Constitution)

Este documento establece las leyes inmutables de desarrollo para este proyecto. Cualquier agente de IA o desarrollador que escriba, modifique o audite código aquí **debe** cumplir estrictamente con los siguientes principios.

## 1. Idioma y Nomenclatura Estricta (Todo en Español)
Para garantizar la coherencia cognitiva y facilitar la lectura por parte del Director del proyecto, **todos los identificadores definidos por el usuario deben estar en español**.

*   **Variables:** `precio_actual`, `enlace_producto`, `titulo_limpio` (NUNCA `current_price`, `product_url`).
*   **Métodos y Funciones (Verbos en infinitivo):** `obtener_dom()`, `extraer_precio()`, `verificar_bloqueo()` (NUNCA `get_dom()`, `extract_price()`).
*   **Clases (Sustantivos, UpperCamelCase):** `ScraperBase`, `ScraperAmazon`, `GestorBaseDatos`. *(Nota: Los archivos existentes como `BaseScraper` migrarán gradualmente a esta nomenclatura de ser necesario, pero los métodos internos deben ser en español desde ya).*
*   **Comentarios y Docstrings:** Todo comentario explicativo debe estar redactado en español claro y conciso.
*   *Excepción única:* Las palabras reservadas de Python (`if`, `for`, `class`, `def`), librerías externas o claves de diccionarios que requieran interactuar con APIs externas (ej. JSONs de respuesta) permanecerán en su formato original.

## 2. Simplicidad y Legibilidad (KISS)
El código se lee muchas más veces de las que se escribe. Se prioriza la claridad sobre la "astucia" o la compresión excesiva del código.

*   **Una función = Una responsabilidad:** Si un método tiene la palabra "y" en su descripción verbal (ej. "extrae el precio *y* lo guarda en la base de datos"), debe dividirse en dos métodos.
*   **Sin anidamientos profundos:** Evitar múltiples niveles de `if / else` o bucles dentro de bucles. Utilizar retornos tempranos (*early returns* o cláusulas de guarda) para manejar errores al inicio de la función.
*   **Tipado explícito (Type Hinting):** Todos los métodos deben declarar qué reciben y qué retornan (ej. `def extraer_precio(html: str) -> float:`).

## 3. Idempotencia y Estado Predecible
La ejecución del sistema debe ser segura de repetir. Ejecutar el orquestador una vez, dos veces o diez veces seguidas el mismo día para el mismo producto **no debe alterar destructivamente ni duplicar la base de datos**.

*   **Scraping sin estado:** Un método de extracción (`extraer_datos`) siempre debe devolver el mismo diccionario dado el mismo HTML de entrada. No debe modificar variables globales ni depender de ejecuciones anteriores.
*   **Base de datos tolerante a repeticiones:** Las consultas SQL (SQLite) deben usar `INSERT OR REPLACE` o estructuras `ON CONFLICT (id_producto, fecha) DO UPDATE` para asegurar que si se scrapea dos veces el mismo día, solo se actualice el registro, sin duplicar filas.
*   **Archivos estáticos:** El manejo del JSON de divisas o la creación de la `.db` debe verificar primero si ya existen, sin sobreescribir destructivamente en cada inicio.

## 4. Mantenibilidad en el Tiempo (Arquitectura)
El proyecto debe sobrevivir a los cambios estructurales de las tiendas web.

*   **Aislamiento del Orquestador:** Las fallas de la web (timeouts, CAPTCHAs, cambios de diseño en Amazon) son inevitables. Estos errores deben capturarse mediante bloques `try-except` manejados. Un error en un producto no debe detener la evaluación del siguiente.
*   **Degradación Elegante:** Si el orquestador detecta un error de red o la imposibilidad de encontrar un precio, el sistema debe registrar el incidente (log/print amigable) y devolver un valor por defecto o nulo de forma controlada, cerrando la sesión del navegador correctamente.