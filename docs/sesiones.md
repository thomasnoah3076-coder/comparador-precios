# Sesiones de desarrollo

## Porcentaje general de desarrollo del proyecto: 15/100

### Etapa 2 - Analizador de ofertas

#### Sesión 1 - 2026-11-20
<!-- hasta: 07acb1e · etapa: 16% · proyecto: 15% -->
- Se renombró `services/currency.py` a `services/divisas.py` y se actualizaron sus referencias (0b19296, e04e094).
- Se añadió el desempate `id DESC` en `obtener_ultimo_registro` para fechas iguales (e822110).
- Se adaptaron los dos `spec.md` a la plantilla de `crear-spec` y se marcaron subtareas en las tasks de la 002 (1ba2828, cad0d81).
- Se añadió el glosario y una sección de claridad documental (deac0a4).
- Se precisó la plantilla de los comandos `crear` (07acb1e).
- Se probaron 3 métodos del analizador con 39 pruebas en verde: `obtener_precio_referencia`, `calcular_caida` y `_analizar_por_id`.
- Se corrigió la spec 002 al mínimo crudo de `obtener_precio_referencia` y se actualizaron `MEMORY.md` y `AGENTS.md`.
- Se corrigió el nombre de `resumir-sesion.md` (espacio final) para que OpenCode lo detecte como comando.

En esta sesión se avanzó 16% de la etapa actual (4/25 subtareas) y 15% de la totalidad del proyecto (7/48 subtareas).

##### Pendiente
- Implementadas pero sin figurar en `## Métodos verificados` de `MEMORY.md`: 1.1 (umbral), 2.1 (`obtener_historial_precios`), 2.3 (`obtener_ultimo_registro`) y 3.1 (encabezado del módulo).
- Sin implementar en la 002: `analizar_oferta` (4.2), `analizar_productos` (5.1), `main` (6.1) y el bloque `__main__` (6.2).
- Sin ejecutar: la batería aislada 7.1-7.10 y el cierre documental 8.1-8.3 de la 002.
- Sin fallos abiertos: no quedaron archivos `test_tmp_*` ni pruebas en rojo.

##### Repasar
- ¿Cómo se usa `try/except Exception` en `analizar_oferta` para degradar errores de SQLite sin convertirlos en "no es oferta"?
- ¿Cómo se usa `argparse` para declarar un argumento posicional obligatorio y salir con `SystemExit(1)`?
- ¿Cómo se usa `sqlite3.connect("file:...?mode=ro", uri=True)` para abrir la base en solo lectura y cerrarla en `finally`?
- ¿Cómo se usa `monkeypatch.setattr` para parchear `settings.DB_PATH_TRACKER` y `database.esquema.DB_PATH_TRACKER`?
- ¿Cómo se usa `runpy.run_path` y `runpy.run_module` para probar la ejecución directa y como paquete?
