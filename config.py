from dotenv import load_dotenv
import os

load_dotenv()

# Cargar las variables de entorno desde el archivo .env
user = os.getenv('DB_USER')
pwd = os.getenv('DB_PASSWORD')
host = os.getenv('DB_HOST')
db = os.getenv('DB_NAME')
server = os.getenv('DB_SERVER')
port = os.getenv('DB_PORT')

# Crear la cadena de conexión
DATABASE_CONNECTION = f'{server}://{user}:{pwd}@{host}:{port}/{db}'