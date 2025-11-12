from flask import Blueprint, request, jsonify, make_response
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from utils.db import db
import requests
import time

from utils.logger import get_logger
from utils.servicios_externos import VERIFICADOR_ACTIVIDAD_DIARIA, VERIFICADOR_EXPERIENCIA_CONTADORES
from models.producto import Producto
from schemas.producto import (producto_registro_schema,
                              producto_registro_schemas)
from schemas.producto import producto_consulta_schema
from schemas.producto import producto_detalle_schema
#from schemas.producto import producto_filtrado_schema


# Configurar el logger
logger = get_logger(__name__)

producto_routes = Blueprint("producto_routes", __name__)

#registro de producto
@producto_routes.route('/registro_producto', methods=['POST'])
def registro_producto():
    inicio_tiempo = time.time()
    try:
        datos = producto_registro_schema.load(request.get_json())
    except ValidationError as err:
        tiempo_respuesta = time.time() - inicio_tiempo
        logger.error(f"Error validación en registro_producto: {err.messages}. Tiempo: {tiempo_respuesta:.2f}s")
        return make_response(jsonify({"errors": err.messages, "status": 400}), 400)
    
    id_vendedor = datos["id_vendedor"]
    url_foto = datos["url_foto"]
    precio = datos["precio"]
    cantidad = datos["cantidad"]
    descripcion = datos["descripcion"]
    comprado = datos["comprado"]
    tipo = datos["tipo"]
    material = datos["material"]
    nombre = datos["nombre"]

    logger.info(f"Registrando producto: {nombre}, vendedor: {id_vendedor}, precio: {precio}")

    nuevo_producto = Producto(
        id_vendedor=id_vendedor,
        url_foto=url_foto,
        precio=precio,
        cantidad=cantidad,
        descripcion=descripcion,
        comprado=comprado,
        tipo=tipo,
        material=material,
        nombre=nombre
    )
    try:
        db.session.add(nuevo_producto)
        db.session.commit()
        tiempo_respuesta = time.time() - inicio_tiempo
        logger.info(f"Producto registrado exitosamente: {nuevo_producto.id_producto}. Tiempo: {tiempo_respuesta:.2f}s")
    except IntegrityError as err:
        db.session.rollback()
        tiempo_respuesta = time.time() - inicio_tiempo
        logger.error(f"Error de integridad en registro_producto: {str(err.orig)}. Vendedor: {id_vendedor}. Tiempo: {tiempo_respuesta:.2f}s")
        return make_response(jsonify({
            "message": str(err.orig),
            "status": 400
            }),400)
    
    # Llamar al servicio para que registre la actividad diaria
    servicio_actividad_diaria = VERIFICADOR_ACTIVIDAD_DIARIA

    respuesta_servicio = requests.post(servicio_actividad_diaria, json={
        "id_usuario": id_vendedor,
    })

    if respuesta_servicio.status_code != 200:
        tiempo_respuesta = time.time() - inicio_tiempo
        logger.error(f"Error al registrar actividad diaria para usuario {id_vendedor}. Tiempo: {tiempo_respuesta:.2f}s")
        return make_response(jsonify({
            "status": respuesta_servicio.status_code,
            "message": "Error al registrar actividad diaria"
        }), respuesta_servicio.status_code)
    
    tiempo_respuesta = time.time() - inicio_tiempo
    logger.info(f"Actividad diaria registrada exitosamente para usuario {id_vendedor}. Tiempo: {tiempo_respuesta:.2f}s")


    # Llamar al servicio para que aumente los puntos y contadores del vendedor
    servicio_experiencia_contadores = VERIFICADOR_EXPERIENCIA_CONTADORES

    respuesta_servicio2 = requests.post(servicio_experiencia_contadores, json={
        "id_usuario": id_vendedor,
        "motivo": 1
    })

    if respuesta_servicio2.status_code != 200:
        tiempo_respuesta = time.time() - inicio_tiempo
        logger.error(f"Error al actualizar experiencia y contadores para usuario {id_vendedor}. Tiempo: {tiempo_respuesta:.2f}s")
        return make_response(jsonify({
            "status": respuesta_servicio2.status_code,
            "message": "Error al actualizar experiencia y contadores"
        }), respuesta_servicio2.status_code)
    
    tiempo_respuesta = time.time() - inicio_tiempo
    logger.info(f"Experiencia y contadores actualizados exitosamente para usuario {id_vendedor}. Tiempo: {tiempo_respuesta:.2f}s")

    data = {
        "message": "Producto registrado exitosamente",
        "status": 201,
    }
    return make_response(jsonify(data), 201)



#listar productos por tipo y material
@producto_routes.route('/filtrar_productos', methods=['POST'])
def listar_productos_por_tipo():
    inicio_tiempo = time.time()

    try:
        data = request.get_json()
        tipos = data.get("tipo", [])  # Espera lista de enteros
        materiales = data.get("material", "")  # Espera string tipo "1,2"

        logger.info(f"Filtrando productos - tipos: {tipos}, materiales: {materiales}")

        # Filtrar primero por tipo y comprado
        query = Producto.query
        if tipos:
            query = query.filter(Producto.tipo.in_(tipos))
        productos = query.filter(Producto.comprado == False).all()

        logger.info(f"Productos encontrados sin filtro de material: {len(productos)}")

        # Ahora filtrar por material en la lista resultante
        lista_materiales = [m.strip() for m in materiales.split(',') if m.strip()]
        productos_filtrados = []
        if lista_materiales:
            for producto in productos:
                materiales_producto = [mat.strip() for mat in producto.material.split(',')]
                if any(mat in materiales_producto for mat in lista_materiales):
                    productos_filtrados.append(producto)
        else:
            productos_filtrados = productos

        if not productos_filtrados:
            tiempo_respuesta = time.time() - inicio_tiempo
            logger.warning(f"No se encontraron productos con criterios - tipos: {tipos}, materiales: {materiales}. Tiempo: {tiempo_respuesta:.2f}s")
            return make_response(jsonify({
                "message": "No se encontraron productos con esos criterios",
                "status": 404
            }), 404)
        else:
            results = producto_consulta_schema.dump(productos_filtrados, many=True)
            tiempo_respuesta = time.time() - inicio_tiempo
            logger.info(f"Filtrado exitoso - productos encontrados: {len(productos_filtrados)}. Tiempo: {tiempo_respuesta:.2f}s")
            data = {
                "message": "Productos encontrados",
                "status": 200,
                "data": results
            }
            return make_response(jsonify(data), 200)
    
    except Exception as err:
        tiempo_respuesta = time.time() - inicio_tiempo
        logger.error(f"Error en listar_productos_por_tipo: {err}. Tiempo: {tiempo_respuesta:.2f}s")
        return make_response(jsonify({
            'status': 500,
            'message': 'Error procesando la solicitud'
        }), 500)



#Detalle producto
@producto_routes.route('/producto_detalle', methods=['POST'])
def detalle_producto():
    inicio_tiempo = time.time()
    try:
        datos = producto_detalle_schema.load(request.get_json())
    except ValidationError as err:
        tiempo_respuesta = time.time() - inicio_tiempo
        logger.error(f"Error validación en detalle_producto: {err.messages}. Tiempo: {tiempo_respuesta:.2f}s")
        return make_response(jsonify({"errors": err.messages, "status": 400}), 400)

    id_producto = datos["id_producto"]
    logger.info(f"Obteniendo detalle del producto: {id_producto}")

    producto = Producto.query.filter_by(id_producto=id_producto).first()

    if not producto:
        tiempo_respuesta = time.time() - inicio_tiempo
        logger.warning(f"Producto no encontrado: {id_producto}. Tiempo: {tiempo_respuesta:.2f}s")
        return make_response(jsonify({
            "message": "Producto no encontrado",
            "status": 404
        }), 404)
    else:
        result = producto_detalle_schema.dump(producto)
        data = {
            "message": "Producto encontrado",
            "status": 200,
            "data": result
        }

    #llamar a microservicio usuario para obtener nombre del vendedor
    #Se crea la trama para enviar por post
    #Se llama al servicio de usuario
    ##requesta devuelve status_code

    id_vendedor = producto.id_vendedor
    payload = {'id_vendedor': id_vendedor}

    logger.info(f"Obteniendo datos del vendedor: {id_vendedor}")
    try:
        response = requests.post('http://127.0.0.1:5000/usuario_routes/obtener_username_vendedor', json=payload)
        logger.info(f"Respuesta del servicio de vendedor - Status: {response.status_code}")
        '''response = {
            "data": {
                "username": "Esmeraldo"
            },
            "message": "Vendedor encontrado",
            "status": 200
        }
        data['data']['nombre_vendedor'] = response['data']['username']
        '''
        logger.info(f"Datos del vendedor obtenidos exitosamente para vendedor: {id_vendedor}")
        if response.status_code == 200:
            usuario = response.json()
            # Extraer el nombre del vendedor del campo correcto
            data['data']['nombre_vendedor'] = usuario['data']['username']
            logger.info(f"Nombre vendedor obtenido exitosamente para vendedor: {id_vendedor} - {usuario['data']['username']}")
        else:
            data['data']['nombre_vendedor'] = 'Desconocido'
            logger.warning(f"Respuesta inesperada del servicio de vendedor - Status: {response.status_code}")

    except requests.RequestException as e:
        logger.error(f"Error en solicitud del vendedor para producto {id_producto}: {e}")
        data['data']['nombre_vendedor'] = 'Desconocido'

    except (KeyError, ValueError) as e:
        logger.error(f"Error al procesar respuesta del vendedor para producto {id_producto}: {e}")
        data['data']['nombre_vendedor'] = 'Desconocido'
        
    tiempo_respuesta = time.time() - inicio_tiempo
    logger.info(f"detalle_producto exitoso para producto {id_producto}. Tiempo: {tiempo_respuesta:.2f}s")
    return make_response(jsonify(data), 200)



##Producto consulta
@producto_routes.route('/consulta_producto', methods=['POST'])
def consulta_producto():
    inicio_tiempo = time.time()
    try:
        datos = producto_consulta_schema.load(request.get_json())
    except ValidationError as err:
        tiempo_respuesta = time.time() - inicio_tiempo
        logger.error(f"Error validación en consulta_producto: {err.messages}. Tiempo: {tiempo_respuesta:.2f}s")
        return make_response(jsonify({"errors": err.messages, "status": 400}), 400)

    id_producto = datos["id_producto"]
    logger.info(f"Consultando producto: {id_producto}")

    producto = Producto.query.filter_by(id_producto=id_producto).first()

    if not producto:
        tiempo_respuesta = time.time() - inicio_tiempo
        logger.warning(f"Producto no encontrado en consulta: {id_producto}. Tiempo: {tiempo_respuesta:.2f}s")
        return make_response(jsonify({
            "message": "Producto no encontrado",
            "status": 404
        }), 404)
    else:
        result = producto_consulta_schema.dump(producto)
        tiempo_respuesta = time.time() - inicio_tiempo
        logger.info(f"consulta_producto exitosa para producto {id_producto}. Tiempo: {tiempo_respuesta:.2f}s")
        data = {
            "message": "Producto encontrado",
            "status": 200,
            "data": result
        }
        return make_response(jsonify(data), 200)
    

# ============================================
# Mostrar productos de un vendedor específico
@producto_routes.route('/listar_productos_vendedor', methods=['POST'])
def listar_productos_vendedor():
    inicio_tiempo = time.time()
    try:
        # Validar que existe el JSON y el campo
        field_required = ['id_vendedor']
        if not request.json or not all(field in request.json for field in field_required):
            return make_response(jsonify({
                'status': 400,
                'message': 'Faltan campos requeridos'
            }), 400)

        id_vendedor = request.json.get('id_vendedor')

        # Validar que no sea None o vacío
        if id_vendedor is None or str(id_vendedor).strip() == '':
            return make_response(jsonify({
                'status': 400,
                'message': 'id_vendedor no puede ser nulo o vacío'
            }), 400)
        
        productos = Producto.query.filter_by(id_vendedor=id_vendedor, comprado=False).all()

        if not productos:
            tiempo_respuesta = time.time() - inicio_tiempo
            logger.warning(f"No se encontraron productos para vendedor: {id_vendedor}. Tiempo: {tiempo_respuesta:.2f}s")
            return make_response(jsonify({
                "message": "No se encontraron productos",
                "status": 404
            }), 404)
        
        resultado = producto_registro_schemas.dump(productos, many=True)

        tiempo_respuesta = time.time() - inicio_tiempo
        logger.info(f"listar_productos_vendedor exitosa para vendedor: {id_vendedor}. Tiempo: {tiempo_respuesta:.2f}s")
        data = {
            "message": "Productos encontrados",
            "status": 200,
            "data": resultado
        }

        return make_response(jsonify(data), 200)
        
    except Exception as e:
        tiempo_respuesta = time.time() - inicio_tiempo
        logger.error(f"Error en listar_productos_vendedor: {e}. Tiempo: {tiempo_respuesta:.2f}s")
        return make_response(jsonify({
            'status': 500,
            'message': 'Error procesando la solicitud',
            'error': str(e)
        }), 500)