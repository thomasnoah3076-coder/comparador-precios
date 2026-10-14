---
description: Prueba un método de Python por nombre, reporta errores clasificados y limpia los archivos temporales si todo pasa.
agent: build
---

Vas a probar el método de Python llamado `$ARGUMENTS`.

## Pasos

1. **Localiza el método.** Busca en el proyecto la definición `def $ARGUMENTS` (en archivos `.py`, ignorando `venv`, `.venv`, `__pycache__` y `node_modules`). Si hay varias coincidencias, indícalas y usa la más probable. Si no existe, avisa y detente.

2. **Lee el método y su contexto.** Entiende qué recibe, qué devuelve, sus dependencias y sus casos límite.

3. **Revisa sintaxis e importación.** Ejecuta `.venv/bin/python -m py_compile <archivo>` (usa el intérprete del entorno virtual del proyecto).

4. **Crea un archivo de prueba temporal** llamado `test_tmp_$ARGUMENTS.py` con pruebas `pytest` que cubran:
   - Casos normales.
   - Casos límite (vacíos, `None`, cero, negativos).
   - Entradas inválidas que deberían lanzar excepción.
   Usa `unittest.mock` o `monkeypatch` para aislar internet, archivos o bases de datos.

5. **Ejecuta las pruebas** con `.venv/bin/python -m pytest -v test_tmp_$ARGUMENTS.py` (¡`pytest` NO está en el PATH global del sistema; usa siempre el intérprete de `.venv`!). Si el venv no tiene pytest, instálalo con `.venv/bin/python -m pip install pytest`. Si `$ARGUMENTS` contiene espacios o typos, sustitúyelos por guiones bajos en el nombre del archivo (ver `AGENTS.md` §6.4).

6. **Decide qué hacer con el archivo temporal:**
   - **Si TODAS las pruebas pasan:** elimina `test_tmp_$ARGUMENTS.py` y cualquier otro archivo auxiliar que hayas creado (incluida la carpeta `__pycache__` y `.pytest_cache` si las generaste tú). Informa que el método funciona correctamente.
   - **Si ALGUNA prueba falla:** NO elimines el archivo de prueba. Conserva todo para que el usuario pueda revisarlo.

## Si hubo fallos, muestra en la terminal este reporte

### Errores detectados
Muestra la salida real de los errores (traceback o mensaje de `pytest`).

### Clasificación
Agrupa cada problema en una de estas categorías (omite las que no apliquen):

- **Errores de sintaxis:** código que Python no puede interpretar.
- **Errores de lógica:** el código corre pero devuelve un resultado incorrecto.
- **Errores de ejecución:** excepciones en tiempo de ejecución (`TypeError`, `KeyError`, `ZeroDivisionError`, etc.).

Para cada error indica: archivo, línea, qué ocurrió y **UNA descripción de cómo se podría resolver**.

### Pendiente por corregir o implementar
Lista clara de las correcciones y de lo que falta implementar en el método.

## Reglas

- No modifiques el código original del método; solo reporta.
- Solo crea archivos de prueba temporales.
- No elimines nada si hubo algún fallo.
- Responde en español.
- Actualiza AGENTS.md para que los agentes anticipen y mejoren su explicacion de errores.
- Actualiza MEMORY.md solo cuando sea exitosa la prueba.