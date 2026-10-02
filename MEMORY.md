# 🧠 Memoria del Proyecto (Project Memory)

**Última actualización:** (Septiembre 2026)
**Estado Global:** Fase de Desarrollo Inicial / Refactorización de Arquitectura de Scraping.

## 1. Visión General del Proyecto
Sistema programado en Python para comparar precios de productos en línea, registrar el historial en una base de datos local (SQLite), evaluar si el precio es una buena oferta, convertir divisas y enviar notificaciones vía Telegram.

## 2. Trayectoria y Decisiones Arquitectónicas (Historial)
* **Pivote de Plataformas (Mercado Libre -> eBay -> Amazon):** 
  * *Contexto:* Inicialmente se intentó scrapear Mercado Libre (usando requests/BS4 y luego APIs), pero se encontraron bloqueos 403 y contenido dinámico complejo. 
  * *Decisión:* Se decidió simplificar el alcance a **una sola tienda inicial** para validar todo el flujo de trabajo (End-to-End). Actualmente, el foco principal de desarrollo es **Amazon**.
* **Patrón de Diseño "Template Method" (Separación de Responsabilidades):**
  * *Problema:* Mezclar lógica de base de datos, control de navegador y selectores de tiendas en un solo archivo hace que el código sea frágil e inescalable.
  * *Solución:* 
    * **`BaseScraper` (Orquestador):** Se encarga exclusivamente de la infraestructura. Conecta con la BD, verifica si ya se consultó hoy, levanta `Playwright`, maneja las esperas y detecta bloqueos de seguridad (CAPTCHAs).
    * **`AmazonScraper` (Especialista):** No sabe nada de bases de datos ni de navegadores. Solo recibe un DOM (HTML) validado, aplica selectores CSS, limpia los datos (ej. quitar el símbolo "$" del precio) y retorna un diccionario estandarizado.
* **Manejo de Anti-Scraping (Amazon):**
  * *Decisión:* Antes de extraer cualquier dato, el `BaseScraper` debe validar el estado HTTP y buscar huellas de bloqueo en el DOM (ej. `<form action="/errors/validateCaptcha">` o `<title>Robot Check</title>`). Si hay bloqueo, se aborta la ejecución para no guardar datos nulos ni quemar el proxy/IP local.

## 3. Estado Actual del Código
* **Completado:** 
  * Entorno virtual (`.venv`) configurado correctamente.
  * Base de datos (`tracker.db`) y esquema inicial definidos en SQLite.
  * Carga de variables de entorno (`.env`, `config/settings.py`).
  * Servicio de conversión de divisas (`services/currency.py`) con caché en JSON.
  * Estructura base del `BaseScraper` (flujo de consulta a BD -> extracción de DOM).
* **En Progreso:**
  * Configuración del Scraper de Amazon.
  * Refinamiento del `BaseScraper` para que sea agnóstico a los selectores.

## 4. Contrato de Datos (Data Contract)
Cualquier scraper específico (ej. `AmazonScraper`) DEBE retornar al `BaseScraper` un diccionario con la siguiente estructura estandarizada:
* `title` (str): Nombre del producto.
* `price` (float): Precio numérico limpio (sin símbolos ni comas).
* `currency` (str): Moneda original (ej. "USD", "COP").
* `url` (str): Enlace directo al producto.
* `available` (bool): Disponibilidad de stock.

## 5. Próximos Pasos (Roadmap Inmediato)
Los agentes deben ejecutar estas tareas en orden, proponiendo y esperando aprobación para cada una:

1. **Implementar Detección de Bloqueos en `BaseScraper`:** Añadir la lógica que verifique si el DOM devuelto por Playwright es un CAPTCHA de Amazon antes de intentar extraer datos.
2. **Crear `AmazonScraper` (El Especialista):** Desarrollar la clase que reciba el DOM limpio, aplique los selectores para extraer título, precio, etc., y devuelva el formato establecido en el Contrato de Datos.
3. **Conectar Retorno con SQLite:** Asegurar que el `BaseScraper` tome los datos extraídos y haga el `INSERT` o `UPDATE` correspondiente en la base de datos para guardar el historial.
4. **Desarrollar Analizador de Ofertas:** Crear el script que compare el precio actual guardado en la BD con el historial para detectar caídas de precio.
5. **Integrar Notificaciones:** Conectar los resultados del analizador con el bot de Telegram.