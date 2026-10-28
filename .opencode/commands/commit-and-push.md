---
description: Crea commits atómicos con los cambios del proyecto y los sube a GitHub por SSH
agent: build
---

Actúas como el agente primario. Revisas los cambios pendientes del proyecto, los agrupas en commits atómicos con mensajes claros y los subes a GitHub por SSH. Este comando no usa subagentes: sus riesgos (archivos equivocados, secretos, autenticación) se comprueban de forma determinista con git y no requieren revisión de código.

## 1. Entrada

Indicaciones opcionales para el mensaje (alcance, motivo, número de issue):

$ARGUMENTS

Si está vacío, deriva el mensaje del diff.

## 2. Contexto

Rama y estado (la primera línea indica si hay commits locales por subir):

!`git status -sb 2>&1`

Remotos configurados:

!`git remote -v 2>&1`

Resumen de cambios respecto a `HEAD`:

!`git diff HEAD --stat 2>&1`

Últimos commits (de aquí solo toma el idioma del historial):

!`git log --oneline -5 2>&1`

Si alguna salida muestra un error de git, trátalo como un fallo de la Fase 1.

## 3. Reglas

1. **Prohibido reescribir o forzar:** nunca uses `--force`, `--force-with-lease`, `--no-verify`, `--amend`, `reset --hard` ni `rebase`.
2. **Configuración intocable:** no modifiques la configuración de git (`user.name`, `user.email`, hooks) ni la de SSH (`~/.ssh`, `ssh-agent`, `ssh config`). La única excepción es cambiar la URL de `origin` a SSH (Fase 5).
3. **Stage explícito:** agrega archivos por ruta. Nunca uses `git add -A` ni `git add .`.
4. **Sin secretos:** nunca incluyas en un commit archivos ni contenido sensibles (ver Fase 2).
5. **Respeta hooks y firma:** si un hook falla, detente e informa. No lo evites.
6. **No toques el código:** solo ejecutas operaciones de git. No edites archivos del proyecto.
7. **Ante lo inesperado, detente y pregunta.** No improvises.
8. Responde en español.

## 4. Flujo de trabajo

### Fase 1: Verificación del entorno

1. Confirma que estás dentro de un repositorio git.
2. Confirma que hay una rama activa. Si `HEAD` está desacoplado, detente e informa.
3. Confirma que `git config user.name` y `git config user.email` tienen valor. Si falta alguno, detente y pide al usuario que lo configure.

### Fase 2: Análisis de cambios

1. Si no hay cambios que commitear:
   - Si hay commits locales por subir (`ahead` en el estado), ve a la Fase 5.
   - Si no, informa que no hay nada que hacer y detente.
2. Lee el diff de cada archivo modificado y el contenido de los archivos nuevos para entender qué cambió y por qué.
3. **Excluye** siempre estos archivos y avisa en el informe final:
   - Entornos y cachés: `.venv`, `venv`, `__pycache__`, `.pytest_cache`, `node_modules`.
   - Pruebas temporales: `test_tmp_*.py`.
   - Archivos de más de 100 MB (GitHub los bloquea).
4. **Detén el proceso y pregunta al usuario** si detectas algún archivo sensible: `.env*`, `*.pem`, `*.key`, `id_rsa*`, archivos de credenciales o secretos; o contenido con claves privadas, tokens o contraseñas en el diff. No los incluyas. Si el archivo no está en `.gitignore`, sugiere añadirlo, sin editarlo tú.

### Fase 3: Agrupación y mensajes

1. Agrupa los cambios por unidad lógica: cada commit debe representar un solo cambio coherente (ej. documentación de `specs/` aparte del código, una corrección aparte de una funcionalidad nueva). Si todo es una sola unidad, haz un solo commit.
2. Redacta el mensaje de cada commit con el formato de la sección 5, apoyándote en las indicaciones del usuario si las hay.

### Fase 4: Commit

Para cada grupo, en orden:

1. `git add -- <archivos del grupo>`.
2. Verifica con `git diff --cached --stat` que solo están los archivos del grupo.
3. `git commit -m "<resumen>" -m "<cuerpo>"` (omite el segundo `-m` si no hay cuerpo).
4. Si un hook modifica archivos y rechaza el commit, vuelve a agregarlos y reintenta una sola vez. Si falla de nuevo, detente e informa.

### Fase 5: Push por SSH

1. Obtén la URL de `origin` con `git remote get-url origin`.
   - Si no existe `origin`, detente e informa. No inventes un remoto.
   - Si es HTTPS de GitHub (`https://github.com/OWNER/REPOSITORY.git`), cámbiala a SSH con `git remote set-url origin git@github.com:OWNER/REPOSITORY.git` y verifica con `git remote -v`.
   - Si ya es SSH (`git@github.com:...`), continúa.
   - Si el host no es `github.com`, detente y pregunta.
2. Comprueba la autenticación con `ssh -o BatchMode=yes -T git@github.com`. El éxito se reconoce por el mensaje de autenticación exitosa; que el código de salida sea 1 es normal.
   - Si falla (por ejemplo `Permission denied (publickey)` o una clave con passphrase sin agente), detente, muestra el error y remite al usuario a la guía de GitHub: https://docs.github.com/es/authentication/connecting-to-github-with-ssh. No generes claves ni toques `~/.ssh`.
3. Sube la rama:
   - Si ya tiene upstream: `git push origin <rama>`.
   - Si no lo tiene: `git push -u origin <rama>`.
4. Si el push es rechazado (por ejemplo, el remoto tiene commits que no tienes), detente, muestra el error y deja que el usuario decida cómo integrarlos. No fuerces el push.

### Fase 6: Informe final

Muestra:

- Los commits creados (hash corto y resumen, con `git log --oneline`).
- La rama y el remoto SSH usados.
- Si cambiaste la URL de `origin` de HTTPS a SSH.
- El resultado del push.
- Los archivos excluidos y el motivo.

## 5. Formato del mensaje de commit

Redacta en el idioma del historial reciente; si está vacío, en español. Usa modo imperativo.

```
<Resumen en imperativo, máximo 50 caracteres, sin punto final>

<Cuerpo opcional: qué cambió y por qué, líneas de máximo 72 caracteres>

<Referencia opcional: Refs #N o Fixes #N, solo si el usuario indicó el issue>
```

- El resumen debe completar la frase "Si se aplica, este commit...".
- Deja una línea en blanco entre el resumen y el cuerpo.
- Incluye cuerpo solo cuando el porqué no sea evidente por el resumen.