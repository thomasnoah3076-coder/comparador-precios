---
description: Genera y valida el spec.md de una nueva funcionalidad
agent: build
---
 
Actúas como **Coordinator**. Orquestas a los subagentes `planner`, `reviewer-logic`, `reviewer-purpose` y `reviewer-architecture` para producir y validar el archivo `specs/<NNN_descripcion_corta>/spec.md`. Tú no redactas el spec: delegas, recibes veredictos y decides el siguiente paso.
 
## 1. Entrada
 
Funcionalidad solicitada:
 
$ARGUMENTS
 
Si la descripción está vacía, pídela al usuario y detente.
 
## 2. Contexto
 
Constitución del proyecto:
 
@docs/constitution.md
 
Carpetas existentes en `specs/`:
 
!`ls -1 specs 2>/dev/null || echo "(sin carpetas)"`
 
## 3. Reglas
 
1. La constitución es de cumplimiento obligatorio para todos los subagentes: tono, formato y reglas de redacción.
2. El único archivo que se crea o modifica es `spec.md` (y su carpeta, si es nueva).
3. El archivo no contiene meta-comentarios: ni notas, ni aclaraciones, ni enmiendas, ni marcas de corrección.
4. Si un subagente no está disponible, detente e informa al usuario cuál falta. No simules su rol.
5. Si el usuario ajusta decisiones después de la generación, corrige solo lo afectado en `spec.md`.
## 4. Subagentes
 
| Subagente | Responsabilidad en este comando |
|---|---|
| `planner` | Resuelve la carpeta de destino y redacta o corrige `spec.md`. |
| `reviewer-logic` | Busca contradicciones y errores de lógica en la propuesta. |
| `reviewer-purpose` | Verifica que el spec resuelve la solicitud original del usuario. |
| `reviewer-architecture` | Audita si falta o sobra algún método, objeto, clase, patrón o librería. |
 
## 5. Flujo de trabajo
 
### Fase 1: Redacción
 
Invoca a `planner` con la herramienta Task. Pásale la funcionalidad solicitada, el listado de `specs/`, la plantilla de la sección 6 y estas reglas de carpeta:
 
- Si la funcionalidad pertenece a una carpeta existente, usa esa carpeta (si ya contiene `spec.md`, actualízalo).
- Si es nueva, crea `specs/<NNN>_<descripcion_corta>/` con el siguiente número correlativo de tres dígitos y la descripción en snake_case (ej. `001_persistencia_sqlite`).
El Planner responde únicamente con la ruta del `spec.md`.
 
### Fase 2: Revisión
 
Invoca a los tres reviewers en paralelo (tres llamadas Task en el mismo mensaje). A cada uno pásale: tipo de artefacto `spec`, la ruta del archivo y la funcionalidad solicitada original.
 
### Fase 3: Decisión
 
- Los tres responden APROBADO: ve a la Fase 5.
- Al menos uno responde RECHAZADO: ve a la Fase 4.
### Fase 4: Corrección
 
Consolida los hallazgos de todos los reviewers sin reinterpretarlos y envíaselos al `planner` para que corrija `spec.md`. Cuando responda, vuelve a la Fase 2 entregando a cada reviewer sus hallazgos previos para que verifique solo su resolución y que no haya regresiones.
 
Máximo 3 ciclos de corrección. Si tras el tercero persisten rechazos, detente y presenta al usuario los hallazgos pendientes.
 
### Fase 5: Cierre
 
Informa al usuario: ruta del archivo, número de ciclos de corrección y confirmación de que los tres reviewers aprobaron.
 
## 6. Plantilla de spec.md
 
El Planner la adapta siempre a las reglas de la constitución.
 
```markdown
# Especificación: [Nombre de la Funcionalidad]
 
## 1. Objetivo (El Qué)
[Descripción técnica y concisa de lo que se va a implementar]
 
## 2. Motivación (El Por Qué)
[Justificación técnica o de negocio. Beneficios esperados]
 
## 3. Propuesta Técnica
- **Componentes / Objetos:** [Clases, modelos o componentes nuevos o modificados]
- **Métodos Principales:** [Firmas de funciones clave y su propósito]
- **Librerías / Dependencias:** [Dependencias necesarias para la implementación]
- **Flujo de Datos:** [Cómo interactúan los componentes]
 
## 4. Criterios de Aceptación
- [Condición verificable que demuestra que la funcionalidad está completa]
```