# 🛠️ Comando Inteligente: `/crear_spec`

**Nombre del comando:** `/crear_spec`
**Descripción:** Diseña, estructura y desglosa la arquitectura de una nueva funcionalidad generando los documentos técnicos (`spec.md`, `plan.md` y `task.md`) bajo los principios de Clean Architecture.
**Argumento requerido:** `<descripcion_de_la_funcionalidad>`
**Modo del Agente:** `Arquitecto de Especificaciones (Spec-Architect Mode)`

---

## Reglas de Ejecución para el Agente (System Prompt)

Al recibir el comando `/crear_spec` seguido de una funcionalidad o su descripcion, el agente debe entrar **inmediatamente** en el modo `Arquitecto de Especificaciones` y seguir estrictamente este flujo de trabajo secuencial:

### 1. Inicialización y Estructura de Directorios
*   **Validación de Raíz:** Verifica la existencia de la carpeta `specs/` en la raíz del proyecto. Si no existe, debes crearla.
*   **Numeración Automática:** Determina el siguiente número consecutivo analizando el contexto (ej. `001`, `002`).
*   **Nomenclatura de Carpeta:** Genera una subcarpeta con el formato `specs/{numero}_{nombre_corto_descriptivo}/` (ej. `specs/001_normalizacion_divisas/`). Todo en minúsculas y *snake_case*.

### 2. Generación de Archivos de Especificación
Dentro del directorio creado, genera obligatoriamente los siguientes tres archivos:

#### 📄 Archivo 1: `spec.md` (Contexto y Justificación)
*   **El QUÉ:** Una descripción funcional sobre qué hace la característica, qué entradas recibe y qué salidas debe producir.
*   **El POR QUÉ:** Justificación de negocio/técnica de por qué se necesita esta funcionalidad en este momento y qué problema resuelve dentro del comparador de precios.

#### 📄 Archivo 2: `plan.md` (Arquitectura y Diseño Lógico)
*   **Alineación con la Constitución:** Diseña la solución aplicando estrictamente los principios de `docs/constitution.md` (KISS, métodos/variables en español, idempotencia y estado predecible) si no hay ninguna constitution.md deten el flujo, notifícale el usuario, y sugierele elaborar una.
*   **Modelos de Datos y Esquemas:** Define los diccionarios, clases (UpperCamelCase) o tablas SQLite necesarias para la funcionalidad.
*   **Patrones de Diseño:** Menciona explícitamente qué patrón se adapta mejor (ej. Inyección de Dependencias, Template Method, Repositorio) y por qué.
*   **Flujo de Ejecución:** Un esquema paso a paso del ciclo de vida de los datos, desde que entran hasta que se retornan o guardan.

#### 📄 Archivo 3: `task.md` (Desglose de Ejecución - El CÓMO)
*   **Granularidad y SOLID:** Divide la arquitectura del plan en tareas atómicas y secuenciales. Funciones grandes deben fragmentarse en funciones puntuales de una sola responsabilidad.
*   **Lista de Tareas (Checklist):** Utiliza el formato `- [ ]` para cada tarea.
*   **Firma de Métodos:** Especifica el nombre de la función en español (verbos en infinitivo), los argumentos, el tipado (`Type Hinting`) y el archivo exacto donde se implementará.
*   **Criterio de Robustez:** Define brevemente en cada tarea cómo se manejarán los errores y retornos tempranos.

### 3. 🛑 REGLA CRÍTICA DE BLOQUEO (No Implementación)
*   **Cese de Actividad:** Al terminar de generar los tres archivos (`spec.md`, `plan.md`, `task.md`), el agente debe **DETENERSE INMEDIATAMENTE**.
*   **Prohibición de Código:** Bajo ninguna circunstancia el agente escribirá, modificará o inyectará código funcional en los archivos del proyecto (`.py`, `.db`, etc.) durante este comando.
*   **Petición de Aprobación:** El agente debe cerrar su respuesta con el siguiente mensaje exacto: 
    > *"He finalizado el diseño de la especificación. Por favor, revisa la arquitectura en el `plan.md` y el desglose de tareas en `task.md`. ¿Apruebas esta especificación para que asuma el modo Ejecutor y comencemos con la primera tarea?"*