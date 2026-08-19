# Comparador de precios con Python🐍.

---
## Entorno virtual en Python🔒.
### ¿Qué es?
Un entorno virtual es un espacio de desarrollo aislado en el que se instalan dependencias que tienen la propiedad de ser independientes entre si. 
Por ejemplo, si se desarrolla un proyecto en determinado año y posteriormente se quiere hacer otro proyecto con un versión diferente de alguna dependencia que compartan, si esta se actualiza de manera global, afectara el funcionamiento del proyecto anterior. Esta es la problemática que solucionan los entornos virtuales.
### ¿Cómo crear un entorno virtual?
A partir de la versión 3.3, Python ya cuanta con un modulo integrado y especializado en entornos virtuales. Podemos crear el entorno virtual con el comando:
- `python -m venv <nombre del venv>`

Por convención se suele llamar .venv ya que VSC ya identifica esta carpeta como un entorno virtual.
#### ¿Cómo activarlo? ¿Cómo desactivarlo?
En Windows, para activar un entorno virtual  se usa el comando:
- `nombre_entorno\Scripts\activate`

Y en Linux o Mac:
- `source nombre_entorno\bin\activate`

En ambos casos debería aparecer un (venv) al inicio de la linea de comandos.
Para desactivarlo se usa el comando:
- `deactivate`
