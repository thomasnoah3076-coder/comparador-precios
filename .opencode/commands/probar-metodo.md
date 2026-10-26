---
description: Prueba un método de Python por nombre, reporta errores clasificados y limpia los archivos temporales si todo pasa.
agent: build
---

Actúas como **Coordinator**. Pruebas el método de Python llamado `$ARGUMENTS`: tú localizas el código, ejecutas las comprobaciones y escribes las pruebas. Cuando algo falla, invocas a los subagentes `reviewer-logic`, `reviewer-purpose` y `reviewer-architecture` para diagnosticar la causa antes de reportar. No modificas el código original del método.

## 1. Entrada

Método a probar:

$ARGUMENTS

Si está vacío, pide el nombre del método al usuario y detente.

`<nombre>` en este comando es `$ARGUMENTS` con los espacios o caracteres no válidos sustituidos por guiones bajos (ver `AGENTS.md` §6.4).

## 2. Contexto

Fecha actual:

!`date +%F`

## 3. Reglas

1. **Intérprete:** usa siempre `.venv/bin/python`. `pytest` NO está en el PATH global del sistema. Si el venv no tiene pytest, instálalo con `.venv/bin/python -m pip install pytest`.
2. **Código original intocable:** no modifiques el método ni ningún otro archivo del proyecto. Solo reportas.
3. **Escrituras permitidas:** únicamente `test_tmp_<nombre>.py`, los archivos auxiliares que generes tú, `AGENTS.md` (solo si hubo fallos) y `MEMORY.md` (solo si todo pasó).
4. **Sin limpieza si hay fallos:** no elimines nada si alguna prueba falla.
5. **Subagentes de solo lectura:** los reviewers no ejecutan comandos. Todo `py_compile`, `pytest` e instalación lo ejecutas tú. Si un reviewer no está disponible, detente e informa cuál falta.
6. Responde en español.

## 4. Subagentes

Solo se invocan cuando hay fallos de prueba. Si todo pasa, no se invoca ninguno.

| Subagente | Responsabilidad en este comando |
|---|---|
| `reviewer-logic` | Identifica la causa lógica del fallo: condiciones, casos límite, manejo de errores. |
| `reviewer-purpose` | Verifica si el método incumple su contrato o si la expectativa de la prueba es incorrecta. |
| `reviewer-architecture` | Detecta imports, dependencias, firmas o llamadas incorrectas que explican errores de ejecución. |

## 5. Flujo de trabajo

### Fase 1: Localización

Busca en el proyecto la definición `def $ARGUMENTS` en archivos `.py`, ignorando `venv`, `.venv`, `__pycache__` y `node_modules`.

- Si hay varias coincidencias, indícalas y usa la más probable, explicando brevemente por qué.
- Si no existe, avisa y detente.

### Fase 2: Lectura

Lee el método y su contexto: qué recibe, qué devuelve, sus dependencias y sus casos límite. Busca también en `specs/*/tasks.md` una subtarea que mencione el método; si existe, será el contrato de referencia para los reviewers. Si no existe, el contrato es la firma y el docstring.

### Fase 3: Sintaxis

Ejecuta `.venv/bin/python -m py_compile <archivo>`.

- Si falla, es un error de sintaxis: no crees el archivo de prueba y ve directo a la Fase 7B.
- Los errores de importación se detectarán al ejecutar pytest y se clasificarán como errores de ejecución.

### Fase 4: Pruebas

Crea el archivo temporal `test_tmp_<nombre>.py` con pruebas `pytest` que cubran:

- Casos normales.
- Casos límite (vacíos, `None`, cero, negativos).
- Entradas inválidas que deberían lanzar excepción.

Usa `unittest.mock` o `monkeypatch` para aislar internet, archivos o bases de datos.

### Fase 5: Ejecución y decisión

Ejecuta `.venv/bin/python -m pytest -v test_tmp_<nombre>.py`.

- Todas las pruebas pasan: ve a la Fase 7A.
- Alguna falla: ve a la Fase 6.

### Fase 6: Diagnóstico (solo si hay fallos)

Invoca a los tres reviewers en paralelo (tres llamadas Task en el mismo mensaje). A cada uno pásale:

- Tipo de artefacto `codigo`.
- Ruta del archivo y nombre del método a revisar.
- El contrato de referencia de la Fase 2.
- Ruta de `test_tmp_<nombre>.py` y la salida real de pytest como evidencia.
- La instrucción de indicar, en `Problema`, si cada fallo se debe al método o a la prueba.

Si los reviewers atribuyen algún fallo a la prueba y no al método, corrige `test_tmp_<nombre>.py` y vuelve a la Fase 5. Máximo 2 ciclos de corrección de pruebas. Después, continúa con lo que se haya diagnosticado.

### Fase 7: Cierre

#### 7A. Todas las pruebas pasan

1. Elimina `test_tmp_<nombre>.py` y cualquier archivo auxiliar que hayas creado, incluidas `__pycache__` y `.pytest_cache` si las generaste tú.
2. Actualiza `MEMORY.md`: añade, bajo la sección `## Métodos verificados` (créala si no existe), una línea con este formato:
   `- <fecha> · <nombre> (<archivo>) · <N> pruebas OK · cubre: normales, límite, inválidas`
3. Informa que el método funciona correctamente.

#### 7B. Hubo fallos

Conserva todos los archivos. Muestra en la terminal este reporte y luego actualiza `AGENTS.md`.

**Errores detectados**
Muestra la salida real de los errores (traceback o mensaje de `pytest`, o de `py_compile` si fue error de sintaxis).

**Clasificación**
Agrupa cada problema en una de estas categorías (omite las que no apliquen):

- **Errores de sintaxis:** código que Python no puede interpretar.
- **Errores de lógica:** el código corre pero devuelve un resultado incorrecto.
- **Errores de ejecución:** excepciones en tiempo de ejecución (`TypeError`, `KeyError`, `ZeroDivisionError`, etc.).

Para cada error indica: archivo, línea, qué ocurrió y **UNA descripción de cómo se podría resolver**, apoyándote en los hallazgos de los reviewers.

**Pendiente por corregir o implementar**
Lista clara de las correcciones y de lo que falta implementar en el método.

**Actualización de `AGENTS.md`**
Añade, bajo la sección `## Errores frecuentes en pruebas de métodos` (créala si no existe), una entrada por cada patrón de error que valga la pena anticipar:

- Formato: `- <categoría> · <patrón del error> · <cómo anticiparlo o explicarlo mejor>`.
- Solo lecciones generalizables, no detalles del método concreto.
- No dupliques entradas existentes ni toques otras secciones.
- Mantén la sección en 15 entradas como máximo; si la superas, fusiona las similares.