from flask import Blueprint, request, jsonify, make_response
from marshmallow import ValidationError
#from werkzeug.security import check_password_hash
from sqlalchemy.exc import IntegrityError
from concurrent.futures import ThreadPoolExecutor
import requests
import time

from utils.db import db
from utils.logger import get_logger
from models.venta import Venta
from schemas.venta import venta_registro_schema
from utils.servicios_externos import AUMENTAR_CONTADOR, AUMENTAR_EXPERIENCIA, VERIFICADOR_ACTIVIDAD_DIARIA

# Configurar el logger
logger = get_logger(__name__)

venta_routes = Blueprint("venta_routes", __name__)


# REGISTRAR ACTIVIDAD DIARIA EN BACKGROUND
def _registrar_actividad_diaria(id_usuario):
    """Ejecuta en background sin bloquear la respuesta"""
    try:
        respuesta = requests.post(VERIFICADOR_ACTIVIDAD_DIARIA, 
            json={'id_usuario': id_usuario},
            timeout=3)
        if respuesta.status_code != 201:
            logger.error(f"Error al registrar actividad diaria: {respuesta.text}")
    except Exception as e:
        logger.error(f"Error en registrar actividad diaria background task: {e}")


# AUMENTAR CONTADOR DE COMPRA O VENTA EN BACKGROUND
def _aumentar_contador(id_usuario, motivo):
    """Ejecuta en background sin bloquear la respuesta"""
    try:
        respuesta = requests.post(AUMENTAR_CONTADOR, 
            json={'id_usuario': id_usuario, 'motivo': motivo},
            timeout=3)
        if respuesta.status_code != 200:
            logger.error(f"Error al aumentar contador: {respuesta.text}")
    except Exception as e:
        logger.error(f"Error en aumentar contador background task: {e}")


# AUMENTAR EXPERIENCIA DE COMPRA O VENTA EN BACKGROUND
def _aumentar_experiencia(id_usuario, motivo):
    """Ejecuta en background sin bloquear la respuesta"""
    try:
        respuesta = requests.post(AUMENTAR_EXPERIENCIA, 
            json={'id_usuario': id_usuario, 'motivo': motivo},
            timeout=3)
        if respuesta.status_code != 200:
            logger.error(f"Error al aumentar experiencia: {respuesta.text}")
    except Exception as e:
        logger.error(f"Error en aumentar experiencia background task: {e}")
        

#registro de venta
@venta_routes.route('/registro_venta', methods=['POST'])
def registro_venta():
    inicio_tiempo = time.time()
    
    try:
        datos = venta_registro_schema.load(request.get_json())
    except ValidationError as err:
        tiempo_respuesta = time.time() - inicio_tiempo
        logger.error(f"Error validación en registro_venta: {err.messages}. Tiempo: {tiempo_respuesta:.3f}s")
        return make_response(jsonify({"errors": err.messages, "status": 400}), 400)

    id_producto = datos["id_producto"]
    id_comprador = datos["id_comprador"]
    id_vendedor = datos["id_vendedor"]

    nueva_venta = Venta(
        id_producto=id_producto,
        id_comprador=id_comprador,
        id_vendedor=id_vendedor
    )
    try:
        db.session.add(nueva_venta)
        db.session.commit()
        logger.info(f"Venta registrada en BD exitosamente: {nueva_venta.id_venta}")
    except IntegrityError as err:
        db.session.rollback()
        tiempo_respuesta = time.time() - inicio_tiempo
        logger.error(f"Error de integridad en registro_venta: {str(err.orig)}. Producto: {id_producto}, Comprador: {id_comprador}. Tiempo: {tiempo_respuesta:.3f}s")
        return make_response(jsonify({
            "message": str(err.orig),
            "status": 400
            }),400)
    ##requesta devuelve status_code
        ##Servicio contador
    id_comprador = nueva_venta.id_comprador
    id_vendedor = nueva_venta.id_vendedor
    payload = {
        "id_comprador": id_comprador,
        "id_vendedor": id_vendedor
    }

    logger.info(f"Actualizando contadores para Comprador: {id_comprador}, Vendedor: {id_vendedor}")

    '''
    try:
        #response = requests.post('http://127.0.0.1:5000/venta_routes/obtener_contador', json=payload)
        response = {
            "message": "Contador actualizado exitosamente",
            "status": 200
        }
        if response["status"] == 200:
            logger.info(f"Contadores actualizados exitosamente - {response['message']}")
        else:
            logger.warning(f"Respuesta inesperada al actualizar contadores: {response['status']}")

    except requests.RequestException as e:
        tiempo_respuesta = time.time() - inicio_tiempo
        logger.error(f"Error en solicitud de contador para venta {nueva_venta.id_venta}: {e}. Tiempo: {tiempo_respuesta:.3f}s")

    tiempo_respuesta = time.time() - inicio_tiempo
    logger.info(f"registro_venta exitoso - Venta: {nueva_venta.id_venta}. Tiempo: {tiempo_respuesta:.3f}s")
    '''

    # Ejecutar verificacion de actividad diaria en background (NO bloquea)
    executor = ThreadPoolExecutor(max_workers=1)
    executor.submit(_registrar_actividad_diaria, id_vendedor)
    
    tiempo_respuesta = time.time() - inicio_tiempo
    logger.info(f"Actividad diaria registrada exitosamente para usuario {id_vendedor}. Tiempo: {tiempo_respuesta:.3f}s")


    # Ejecutar el aumento del contador de venta en background (NO bloquea)
    executor = ThreadPoolExecutor(max_workers=1)
    executor.submit(_aumentar_contador, id_vendedor, 2)
    
    tiempo_respuesta = time.time() - inicio_tiempo
    logger.info(f"Experiencia y contadores actualizados exitosamente para usuario {id_vendedor}. Tiempo: {tiempo_respuesta:.3f}s")

    # Ejecutar el aumento del contador de venta en background (NO bloquea)
    executor = ThreadPoolExecutor(max_workers=1)
    executor.submit(_aumentar_experiencia, id_vendedor, 2)

    tiempo_respuesta = time.time() - inicio_tiempo
    logger.info(f"Contador de ventas aumentado exitosamente para usuario {id_vendedor}. Tiempo: {tiempo_respuesta:.3f}s")



    data = {
        "message": "Venta registrada exitosamente",
        "venta": venta_registro_schema.dump(nueva_venta)
    }
    return make_response(jsonify(data), 201)
    