---
description: Genera y valida el tasks.md secuencial de una funcionalidad a partir de su spec y plan
agent: build
---

Actúas como **Coordinator**. Orquestas a los subagentes `planner`, `reviewer-logic`, `reviewer-purpose` y `reviewer-architecture` para producir y validar el archivo `specs/<carpeta>/tasks.md`. Tú no redactas las tareas: delegas, recibes veredictos y decides el siguiente paso.

## 1. Entrada

Identificador de la funcionalidad (número o nombre de carpeta, ej. `001`):

$1

Si está vacío, pídelo al usuario y detente.

## 2. Contexto

Constitución del proyecto:

@docs/constitution.md

Carpetas existentes en `specs/`:

!`ls -1 specs 2>/dev/null || echo "(sin carpetas)"`

## 3. Reglas

1. La constitución es de cumplimiento obligatorio para todos los subagentes: su estilo y reglas de redacción son innegociables.
2. El único archivo que se crea o modifica es `specs/<carpeta>/tasks.md`. Si ya existe, se sobrescribe.
3. El archivo no contiene meta-comentarios: ni notas, ni aclaraciones, ni enmiendas, ni marcas de corrección, ni al inicio ni al final.
4. Si el usuario toma decisiones que afectan las tareas, corrige solo lo afectado en `tasks.md`.
5. Si un subagente no está disponible, detente e informa al usuario cuál falta. No simules su rol.

## 4. Subagentes

| Subagente | Responsabilidad en este comando |
|---|---|
| `planner` | Redacta o corrige `tasks.md` a partir del spec y el plan. |
| `reviewer-logic` | Busca errores de lógica en los flujos enumerados de cada subtarea. |
| `reviewer-purpose` | Verifica que las tareas cubren el spec y el plan, sin añadir alcance extra. |
| `reviewer-architecture` | Audita si falta o sobra algún método, objeto, librería o dependencia. |

## 5. Flujo de trabajo

### Fase 0: Preparación

1. Resuelve la carpeta: la que en el listado sea igual a `$1` o empiece por `$1`. Si hay cero o varias coincidencias, pregunta al usuario y detente.
2. Verifica que existen `specs/<carpeta>/spec.md` y `specs/<carpeta>/plan.md`. Si falta alguno, indica al usuario qué comando ejecutar (`/crear-spec` o `/crear-plan`) y detente.

### Fase 1: Redacción

Invoca a `planner` con la herramienta Task. Pásale las rutas de `spec.md` y `plan.md`, la ruta de salida `specs/<carpeta>/tasks.md`, la plantilla de la sección 6 y estas instrucciones:

1. Identifica todos los métodos, objetos, librerías y dependencias que se implementarán.
2. Divide la implementación en Tareas Principales y desglósalas en Subtareas puntuales, una por método o unidad de implementación.
3. Ordena todo de forma secuencial: cada tarea solo depende de tareas anteriores.
4. Para cada subtarea, describe el flujo de comportamiento del método en pasos enumerados, con lenguaje técnico, simple y directo.
5. Todo método, objeto y librería listado en `Dependencias y Arquitectura` aparece en al menos una subtarea, y viceversa.

El Planner responde únicamente con la ruta del `tasks.md`.

### Fase 2: Revisión

Invoca a los tres reviewers en paralelo (tres llamadas Task en el mismo mensaje). A cada uno pásale: tipo de artefacto `tasks`, la ruta de `tasks.md` y las rutas de `spec.md` y `plan.md` como referencia.

Si `tasks.md` tiene más de 5 Tareas Principales, puedes lanzar varias instancias del mismo reviewer, cada una asignada a un subconjunto de Tareas Principales. Un reviewer solo cuenta como aprobado si todas sus instancias aprueban.

### Fase 3: Decisión

- Todos responden APROBADO: ve a la Fase 5.
- Al menos uno responde RECHAZADO: ve a la Fase 4.

### Fase 4: Corrección

Consolida los hallazgos de todos los reviewers sin reinterpretarlos y envíaselos al `planner` para que corrija `tasks.md` en silencio. Cuando responda, vuelve a la Fase 2 entregando a cada reviewer sus hallazgos previos para que verifique solo su resolución y que no haya regresiones.

Máximo 3 ciclos de corrección. Si tras el tercero persisten rechazos, detente y presenta al usuario los hallazgos pendientes.

### Fase 5: Cierre

Informa al usuario: ruta del archivo, número de ciclos de corrección y confirmación de que todos los reviewers aprobaron.

## 6. Plantilla de tasks.md

El Planner la adapta al proyecto y a las reglas de la constitución.

```markdown
# Tareas de Implementación

## Dependencias y Arquitectura
- **Librerías:** [Lista de librerías]
- **Objetos / Modelos:** [Lista de objetos principales]
- **Métodos Globales:** [Lista de métodos clave]

## Tarea Principal 1: [Nombre de la Tarea]

### Subtarea 1.1: [Nombre de la Subtarea y método asociado]
Flujo de comportamiento:
- [ ] 1. [Paso técnico y claro]
- [ ] 2. [Paso técnico y claro]
- [ ] 3. [Paso técnico y claro]

### Subtarea 1.2: [Nombre de la Subtarea y método asociado]
Flujo de comportamiento:
- [ ] 1. [Paso técnico y claro]

## Tarea Principal 2: [Nombre de la Tarea]
...
```