import logging
from logging.handlers import RotatingFileHandler
import os

def get_logger(name):
    """
    Retorna un logger configurado con manejo de archivos.
    
    Args:
        name: Nombre del logger (típicamente __name__)
    
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)

    # Si el logger ya tiene handlers, devolverlo
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Crear directorio de logs si no existe
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Handler para archivo con rotación
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10485760,  # 10MB
        backupCount=10
    )
    file_handler.setLevel(logging.DEBUG)
    
    # Formato con timestamp
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Evitar propagación duplicada
    logger.propagate = False
    
    return logger