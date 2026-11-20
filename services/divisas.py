
import json
from datetime import date
import requests
from config.settings import (
    RUTA_TASAS_CAMBIO,
    EXCHANGE_RATE_API_KEY,
    EXCHANGE_RATE_API_URL,
    DEFAULT_CURRENCY
)

# Segundos máximos de espera a la API de divisas (evita colgar el proceso: un cuelgue
# de red NO es una excepción, el try/except no lo salvaría sin un timeout).
TIMEOUT_API_SEGUNDOS = 10


def convertir_moneda(monto: float, moneda_origen: str, moneda_destino: str) -> float:
    if moneda_origen == moneda_destino:
        return monto

    pareja_soportada = (
        moneda_origen == "USD" and moneda_destino == "COP"
    ) or (
        moneda_origen == "COP" and moneda_destino == "USD"
    )
    if not pareja_soportada:
        print(f"Par de monedas no soportado: {moneda_origen} -> {moneda_destino}.")
        print("Solo se convierte entre USD y COP. Se devuelve el monto sin convertir.")
        return monto

    try:
        usd_en_cop = obtener_tasas()
        if usd_en_cop is None:
            return monto
        return calcular_monto(monto, moneda_origen, usd_en_cop)
    except Exception as error:
        print(f"Error inesperado al convertir la moneda: {error}")
        return monto


def obtener_tasas() -> float | None:
    hoy = date.today().isoformat()

    try:
        with open(RUTA_TASAS_CAMBIO, "r", encoding="utf-8") as archivo_lectura:
            registro = json.load(archivo_lectura)

        if isinstance(registro, dict) and registro.get("fecha") == hoy:
            return float(registro["COP"])
        if isinstance(registro, dict):
            print(f"La tasa cacheada es del {registro.get('fecha')}: se consulta la API.")

    except FileNotFoundError:
        print("No existe el archivo de tasas: se consultará la API.")
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        print("El archivo de tasas está vacío o corrupto: se regenerará con la API.")

    try:
        respuesta = requests.get(
            EXCHANGE_RATE_API_URL,
            params={"apikey": EXCHANGE_RATE_API_KEY},
            timeout=TIMEOUT_API_SEGUNDOS,
        )
    except requests.RequestException as error:
        print(f"No se pudo consultar la API de divisas: {error}")
        return None

    if respuesta.status_code != 200:
        print(f"La API de divisas respondió con estado {respuesta.status_code}.")
        return None

    try:
        usd_en_cop = round(float(respuesta.json()["conversion_rates"]["COP"]), 2)
    except (KeyError, TypeError, ValueError):
        print("La respuesta de la API no tiene el formato esperado (conversion_rates.COP).")
        return None

    if usd_en_cop <= 0:
        print("La tasa recibida no es válida (cero o negativa).")
        return None

    # --- 3. Caché: se SOBRESCRIBE el JSON con el único registro del día ---
    guardar_tasas({
        "fecha": hoy,
        "COP": usd_en_cop,
        "USD": round(1 / usd_en_cop, 8),
    })
    return usd_en_cop


def calcular_monto(monto: float, moneda_origen: str, usd_en_cop: float) -> float:

    match moneda_origen:
        case "USD":
            return monto * usd_en_cop
        case "COP":
            return monto / usd_en_cop
    print(f"Moneda de origen no soportada: {moneda_origen}.")
    return monto


def guardar_tasas(tasas: dict) -> None:
    with open(RUTA_TASAS_CAMBIO, "w", encoding="utf-8") as archivo_escritura:
        json.dump(tasas, archivo_escritura, indent=4, ensure_ascii=False)

def convertir_a_moneda_local(monto: float, moneda_origen: str) -> tuple[float, str]:
    if DEFAULT_CURRENCY is None or DEFAULT_CURRENCY == "":
        print("No se puede convertir moneda.")
        return monto, moneda_origen

    monto_convertido = convertir_moneda(monto, moneda_origen, DEFAULT_CURRENCY)

    if monto_convertido == monto: # Si el monto no cambio quiere decir que la moneda ya estaba en pesos colombianos.
        return monto, moneda_origen
    return monto_convertido, DEFAULT_CURRENCY


