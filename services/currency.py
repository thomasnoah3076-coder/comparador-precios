import requests
from config.settings import (
    EXCHANGE_RATE_API_KEY,
    EXCHANGE_RATE_API_URL,
    DB_PATH_EXCHANGE_RATES,
)
import json
from datetime import date, datetime

def currency_converter(monto, moneda_origen, moneda_destino):
    try:
        DB_PATH_EXCHANGE_RATES.parent.mkdir(parents=True, exist_ok=True)  # Crea la carpeta si no existe
        if DB_PATH_EXCHANGE_RATES.is_file(): # Verifica la existencia de un archivo.
            try:
                print ("El archivo exchange_rates.json existe.")
                with open(DB_PATH_EXCHANGE_RATES, "r", encoding="utf-8") as a_lectura: # Lee el archivo .json
                    lista = json.load(a_lectura)
                if lista and lista[-1].get("date") == datetime.today().strftime("%Y-%m-%d"): # Si la lista tiene elementos y su ultima posición hay un diccionario con la clave "date" y es igual a hoy utiliza los valores del diccionario.
                    USD_en_COP = lista[-1].get("COP")
                    COP_en_USD = lista[-1].get("USD")
                    print("Tasas de cambio ya consultadas el dia de hoy.")
                else:
                    respuesta = requests.get(EXCHANGE_RATE_API_URL, params={"apikey": EXCHANGE_RATE_API_KEY}) # Se hace dentro de un diccionario, por buenas practicas de seguridad y por practicidad.
                    if (respuesta.status_code == 200):
                        data = respuesta.json() # Convierte la respuesta en un diccionario de Python    
                        USD_en_COP = round(data["conversion_rates"]["COP"],2) # Accede al diccionario y vuelves a acceder al diccionario de conversion_rates y luego a la clave COP para obtener el valor de la tasa de cambio.
                        COP_en_USD = round(1 / USD_en_COP, 8)
                        lista.append({"date":datetime.today().strftime("%Y-%m-%d"), "COP":USD_en_COP, "USD":COP_en_USD})
                        with open(DB_PATH_EXCHANGE_RATES, "w", encoding="utf-8") as a_escritura:
                            json.dump(lista, a_escritura, indent=4, ensure_ascii=False)
                        print("Tasa de cambio nueva ha sido guardada.")
                    else: 
                        print(f"Error al obtener la tasa de cambio: {respuesta.status_code}")

                match moneda_origen:
                    case "USD":
                        monto_en_COP = monto * USD_en_COP
                        print(f"{monto} dólares son {monto_en_COP} pesos colombianos.")
                        return monto_en_COP

                    case "COP":
                        monto_en_USD = monto * COP_en_USD
                        print(f"{monto} pesos colombianos son {monto_en_USD} dólares.")
                        return monto_en_USD

                    case _:
                        print("Moneda de origen no soportada.")
                        return monto
                print(f"Un dolar es igual a: {USD_en_COP} pesos colombianos.")
            except json.decoder.JSONDecodeError:
                print("El archivo json esta corrupto o vacio.")
                return monto

            
        else:
            print("El archivo no existe :( No te preocupes vamos a crearlo ahora :)")
            with open(DB_PATH_EXCHANGE_RATES, "w", encoding="utf-8") as a_escritura: # El modo w o write tambien sirve para crear un archivo si este no se encuentra
                json.dump([], a_escritura, indent=4, ensure_ascii=False)
            return monto

    except Exception as e:
        print(f"Error al procesar la respuesta: {e}")

if __name__ == "__main__":
    currency_converter(100000,"COP","USD")