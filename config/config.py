from pathlib import Path
from dotenv import load_dotenv
import os 

#Rutas de la carpeta del proyecto y la base de datos.
DB_PATH = Path(__file__).resolve().parent.parent / "database" / "tracker.db"

BASE_DIR = Path(__file__).resolve().parent.parent

# Generalmente se suele dejar esta función vacia, y por si sola buscará el archivo .env en el 
# directorio donde se ejecuta, pero como en este caso la estructura del proyecto es mas 
# compleja, es mejor especificar la ruta del archivo .env para que no haya problemas al
# ejecutar el proyecto desde otro directorio.
# Esta función carga las variables de entorno definidas en el archivo .env
load_dotenv(dotenv_path=BASE_DIR / ".env")

# Variables de entorno para el bot de Telegram y la configuración de la aplicación.
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Diccionario de IDs de chat de Telegram para diferentes categorías.
CHATS_ID = {
    "general": os.getenv("TELEGRAM_CHAT_ID_GENERAL"),
    "perfumes": os.getenv("TELEGRAM_CHAT_ID_PERFUMES"),
    "tecnologia": os.getenv("TELEGRAM_CHAT_ID_TECNOLOGIA")
}

# Codigo ISO de la moneda local para mostrar los precios en la moneda deseada.
DEFAULT_CURRENCY = os.getenv("LOCAL_CURRENCY")

# 30% de caída de precio.
PRICE_DROP_THRESHOLD = 0.3

# Clave de API para obtener la tasa de cambio de divisas.
EXCHANGE_RATE_API_KEY = os.getenv("EXCHANGE_RATE_API_KEY")

