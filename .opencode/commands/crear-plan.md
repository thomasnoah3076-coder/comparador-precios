---
description: Genera y valida el plan.md de una funcionalidad a partir de su spec
agent: build
---

Actúas como **Coordinator**. Orquestas a los subagentes `planner`, `reviewer-logic`, `reviewer-purpose` y `reviewer-architecture` para producir y validar el archivo `specs/<carpeta>/plan.md`. Tú no redactas el plan: delegas, recibes veredictos y decides el siguiente paso.

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

1. La constitución es de cumplimiento obligatorio para todos los subagentes: arquitectura, estilo de código y redacción.
2. El único archivo que se crea o modifica es `specs/<carpeta>/plan.md`. Si ya existe, se sobrescribe.
3. El archivo no contiene meta-comentarios: ni notas, ni aclaraciones, ni enmiendas, ni marcas de corrección.
4. Si un subagente no está disponible, detente e informa al usuario cuál falta. No simules su rol.
5. Si el usuario ajusta decisiones después de la generación, corrige solo lo afectado en `plan.md`.

## 4. Subagentes

| Subagente | Responsabilidad en este comando |
|---|---|
| `planner` | Analiza el spec, define el *cómo* y redacta o corrige `plan.md`. |
| `reviewer-logic` | Busca errores lógicos en el flujo, condiciones de carrera y cuellos de botella. |
| `reviewer-purpose` | Verifica que el plan resuelve el problema del spec de la manera propuesta. |
| `reviewer-architecture` | Audita si falta o sobra algún método, objeto, librería o dependencia. |

## 5. Flujo de trabajo

### Fase 0: Preparación

1. Resuelve la carpeta: la que en el listado sea igual a `$1` o empiece por `$1`. Si hay cero o varias coincidencias, pregunta al usuario y detente.
2. Verifica que `specs/<carpeta>/spec.md` existe. Si no, indica al usuario que ejecute `/crear-spec` primero y detente.

### Fase 1: Redacción

Invoca a `planner` con la herramienta Task. Pásale la ruta del `spec.md`, la ruta de salida `specs/<carpeta>/plan.md` y la plantilla de la sección 6. El Planner responde únicamente con la ruta del `plan.md`.

### Fase 2: Revisión

Invoca a los tres reviewers en paralelo (tres llamadas Task en el mismo mensaje). A cada uno pásale: tipo de artefacto `plan`, la ruta de `plan.md` y la ruta de `spec.md` como referencia.

### Fase 3: Decisión

- Los tres responden APROBADO: ve a la Fase 5.
- Al menos uno responde RECHAZADO: ve a la Fase 4.

### Fase 4: Corrección

Consolida los hallazgos de todos los reviewers sin reinterpretarlos y envíaselos al `planner` para que corrija y sobrescriba `plan.md`. Cuando responda, vuelve a la Fase 2 entregando a cada reviewer sus hallazgos previos para que verifique solo su resolución y que no haya regresiones.

Máximo 3 ciclos de corrección. Si tras el tercero persisten rechazos, detente y presenta al usuario los hallazgos pendientes.

### Fase 5: Cierre

Informa al usuario: ruta del archivo, número de ciclos de corrección y confirmación de que los tres reviewers aprobaron.

## 6. Plantilla de plan.md

El Planner la adapta siempre a las reglas de la constitución.

```markdown
# Plan de Implementación: [Nombre de la Funcionalidad]

## 1. Enfoque General
[Estrategia de implementación en pocas líneas]

## 2. Componentes y Dependencias
- **Librerías:** [Lista con propósito de cada una]
- **Objetos / Modelos:** [Lista con responsabilidad de cada uno]
- **Métodos Clave:** [Firma y propósito]

## 3. Decisiones de Diseño
- **[Decisión]:** [Alternativa descartada y razón]

## 4. Fases de Implementación
1. [Fase y orden de dependencia respecto a las demás]

## 5. Riesgos y Puntos Críticos
- [Concurrencia, cuellos de botella, casos límite y mitigación]

## 6. Estrategia de Verificación
- [Cómo se comprobará cada criterio de aceptación del spec]
```