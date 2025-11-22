from random import random
from flask import Blueprint, request, jsonify, make_response
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from utils.db import db
from utils.supabase_client import supabase
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
from io import BytesIO
import requests, time

from utils.logger import get_logger
from utils.servicios_externos import (VERIFICADOR_ACTIVIDAD_DIARIA,
                                      AUMENTAR_CONTADOR,
                                      AUMENTAR_EXPERIENCIA)
from models.producto import Producto
from schemas.producto import (producto_registro_schema,
                              producto_registro_schemas)
from schemas.producto import producto_consulta_schema
from schemas.producto import producto_detalle_schema
#from schemas.producto import producto_filtrado_schema


# Configurar el logger
logger = get_logger(__name__)

producto_routes = Blueprint("producto_routes", __name__)


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


#registro de producto
@producto_routes.route('/registro_producto', methods=['POST'])
def registro_producto():
    inicio_tiempo = time.time()
    try:
        datos = producto_registro_schema.load(request.get_json())
    except ValidationError as err:
        tiempo_respuesta = time.time() - inicio_tiempo
        logger.error(f"Error validación en registro_producto: {err.messages}. Tiempo: {tiempo_respuesta:.3f}s")
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
        logger.info(f"Producto registrado exitosamente: {nuevo_producto.id_producto}. Tiempo: {tiempo_respuesta:.3f}s")
    except IntegrityError as err:
        db.session.rollback()
        tiempo_respuesta = time.time() - inicio_tiempo
        logger.error(f"Error de integridad en registro_producto: {str(err.orig)}. Vendedor: {id_vendedor}. Tiempo: {tiempo_respuesta:.3f}s")
        return make_response(jsonify({
            "message": str(err.orig),
            "status": 400
            }),400)
    
    # Ejecutar verificacion de actividad diaria en background (NO bloquea)
    executor = ThreadPoolExecutor(max_workers=1)
    executor.submit(_registrar_actividad_diaria, id_vendedor)
    
    tiempo_respuesta = time.time() - inicio_tiempo
    logger.info(f"Actividad diaria registrada exitosamente para usuario {id_vendedor}. Tiempo: {tiempo_respuesta:.3f}s")


    # Ejecutar el aumento del contador de venta en background (NO bloquea)
    executor = ThreadPoolExecutor(max_workers=1)
    executor.submit(_aumentar_contador, id_vendedor, 1)
    
    tiempo_respuesta = time.time() - inicio_tiempo
    logger.info(f"Experiencia y contadores actualizados exitosamente para usuario {id_vendedor}. Tiempo: {tiempo_respuesta:.3f}s")

    # Ejecutar el aumento del contador de venta en background (NO bloquea)
    executor = ThreadPoolExecutor(max_workers=1)
    executor.submit(_aumentar_experiencia, id_vendedor, 1)

    tiempo_respuesta = time.time() - inicio_tiempo
    logger.info(f"Contador de ventas aumentado exitosamente para usuario {id_vendedor}. Tiempo: {tiempo_respuesta:.3f}s")

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
            logger.warning(f"No se encontraron productos con criterios - tipos: {tipos}, materiales: {materiales}. Tiempo: {tiempo_respuesta:.3f}s")
            return make_response(jsonify({
                "message": "No se encontraron productos con esos criterios",
                "status": 404
            }), 404)
        else:
            results = producto_consulta_schema.dump(productos_filtrados, many=True)
            tiempo_respuesta = time.time() - inicio_tiempo
            logger.info(f"Filtrado exitoso - productos encontrados: {len(productos_filtrados)}. Tiempo: {tiempo_respuesta:.3f}s")
            data = {
                "message": "Productos encontrados",
                "status": 200,
                "data": results
            }
            return make_response(jsonify(data), 200)
    
    except Exception as err:
        tiempo_respuesta = time.time() - inicio_tiempo
        logger.error(f"Error en listar_productos_por_tipo: {err}. Tiempo: {tiempo_respuesta:.3f}s")
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
        logger.error(f"Error validación en detalle_producto: {err.messages}. Tiempo: {tiempo_respuesta:.3f}s")
        return make_response(jsonify({"errors": err.messages, "status": 400}), 400)

    id_producto = datos["id_producto"]
    logger.info(f"Obteniendo detalle del producto: {id_producto}")

    producto = Producto.query.filter_by(id_producto=id_producto).first()

    if not producto:
        tiempo_respuesta = time.time() - inicio_tiempo
        logger.warning(f"Producto no encontrado: {id_producto}. Tiempo: {tiempo_respuesta:.3f}s")
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
    logger.info(f"detalle_producto exitoso para producto {id_producto}. Tiempo: {tiempo_respuesta:.3f}s")
    return make_response(jsonify(data), 200)



##Producto consulta
@producto_routes.route('/consulta_producto', methods=['POST'])
def consulta_producto():
    inicio_tiempo = time.time()
    try:
        datos = producto_consulta_schema.load(request.get_json())
    except ValidationError as err:
        tiempo_respuesta = time.time() - inicio_tiempo
        logger.error(f"Error validación en consulta_producto: {err.messages}. Tiempo: {tiempo_respuesta:.3f}s")
        return make_response(jsonify({"errors": err.messages, "status": 400}), 400)

    id_producto = datos["id_producto"]
    logger.info(f"Consultando producto: {id_producto}")

    producto = Producto.query.filter_by(id_producto=id_producto).first()

    if not producto:
        tiempo_respuesta = time.time() - inicio_tiempo
        logger.warning(f"Producto no encontrado en consulta: {id_producto}. Tiempo: {tiempo_respuesta:.3f}s")
        return make_response(jsonify({
            "message": "Producto no encontrado",
            "status": 404
        }), 404)
    else:
        result = producto_consulta_schema.dump(producto)
        tiempo_respuesta = time.time() - inicio_tiempo
        logger.info(f"consulta_producto exitosa para producto {id_producto}. Tiempo: {tiempo_respuesta:.3f}s")
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
            logger.warning(f"No se encontraron productos para vendedor: {id_vendedor}. Tiempo: {tiempo_respuesta:.3f}s")
            return make_response(jsonify({
                "message": "No se encontraron productos",
                "status": 404
            }), 404)
        
        resultado = producto_registro_schemas.dump(productos, many=True)

        tiempo_respuesta = time.time() - inicio_tiempo
        logger.info(f"listar_productos_vendedor exitosa para vendedor: {id_vendedor}. Tiempo: {tiempo_respuesta:.3f}s")
        data = {
            "message": "Productos encontrados",
            "status": 200,
            "data": resultado
        }

        return make_response(jsonify(data), 200)
        
    except Exception as e:
        tiempo_respuesta = time.time() - inicio_tiempo
        logger.error(f"Error en listar_productos_vendedor: {e}. Tiempo: {tiempo_respuesta:.3f}s")
        return make_response(jsonify({
            'status': 500,
            'message': 'Error procesando la solicitud',
            'error': str(e)
        }), 500)
    

# CARGAR IMAGEN EN SUPABASE
@producto_routes.route('/cargar_imagen', methods=['POST'])
def cargar_imagen():
    inicio_tiempo = time.time()
    try:
        # Validar que exista el archivo y los campos JSON
        if 'imagen' not in request.files:
            tiempo_respuesta = time.time() - inicio_tiempo
            logger.error(f"Falta el archivo de imagen en la solicitud. Tiempo: {tiempo_respuesta:.3f}s")
            return make_response(jsonify({
                'status': 400,
                'message': 'Falta el archivo de imagen'
            }), 400)
        

        required_fields = ['id_usuario', 'nombre_producto']
        if not request.form or not all(field in request.form for field in required_fields):
            tiempo_respuesta = time.time() - inicio_tiempo
            logger.error(f"Faltan campos requeridos en la solicitud. Tiempo: {tiempo_respuesta:.3f}s")
            return make_response(jsonify({
                'status': 400,
                'message': 'Faltan campos requeridos: id_usuario, nombre_producto'
            }), 400)

        imagen = request.files['imagen']
        id_usuario = request.form['id_usuario']
        nombre_producto = request.form['nombre_producto']

        id_adicional = random()
        cadena_nombre = f"{id_usuario}_{nombre_producto}_{id_adicional}"

        # Simulación de URL de la imagen cargada
        url_imagen = subir_imagen_a_supabase(imagen, cadena_nombre)

        tiempo_respuesta = time.time() - inicio_tiempo
        logger.info(f"Imagen cargada exitosamente. Tiempo: {tiempo_respuesta:.3f}s")
        data = {
            "message": "Imagen cargada exitosamente",
            "status": 200,
            "data": url_imagen
        }

        return make_response(jsonify(data), 200)

    except Exception as e:
        tiempo_respuesta = time.time() - inicio_tiempo
        logger.error(f"Error al cargar imagen: {e}. Tiempo: {tiempo_respuesta:.3f}s")
        return make_response(jsonify({
            'status': 500,
            'message': 'Error al cargar la imagen',
            'error': str(e)
        }), 500)
    


def subir_imagen_a_supabase(imagen, cadena_nombre, porcentaje_reduccion=50):
    """
    Redimensiona la imagen por porcentaje, la convierte a WebP y la sube a Supabase
    
    Args:
        imagen: Archivo de imagen cargado
        cadena_nombre: Nombre para guardar en Supabase
        porcentaje_reduccion: Porcentaje del tamaño original (default 50%)
    """
    try:
        # Leer la imagen del archivo cargado
        imagen_pil = Image.open(imagen)
        
        # Calcular nuevas dimensiones por porcentaje
        factor = porcentaje_reduccion / 100
        nuevo_ancho = int(imagen_pil.width * factor)
        nuevo_alto = int(imagen_pil.height * factor)
        
        # Redimensionar manteniendo la proporción
        imagen_pil = imagen_pil.resize((nuevo_ancho, nuevo_alto), Image.Resampling.LANCZOS)
        
        logger.info(f"Imagen redimensionada al {porcentaje_reduccion}% - Dimensiones: {nuevo_ancho}x{nuevo_alto}")
        
        # Convertir a RGB si tiene transparencia (RGBA)
        if imagen_pil.mode in ('RGBA', 'LA', 'P'):
            fondo = Image.new('RGB', imagen_pil.size, (255, 255, 255))
            fondo.paste(imagen_pil, mask=imagen_pil.split()[-1] if imagen_pil.mode == 'RGBA' else None)
            imagen_pil = fondo
        
        # Guardar en BytesIO como WebP
        buffer_webp = BytesIO()
        imagen_pil.save(buffer_webp, format='WEBP', quality=85, optimize=True)
        buffer_webp.seek(0)
        
        # Subir a Supabase
        bucket_name = "recla-images"
        carpeta_supabase = f"productos_usuarios/{cadena_nombre}.webp"
        
        llamado_carpeta = supabase.storage.from_(bucket_name)
        llamado_carpeta.upload(
            carpeta_supabase, 
            buffer_webp.read(),
            {'cacheControl': '3600', 'upsert': 'true', 'contentType': 'image/webp'}
        )
        
        webp_url = llamado_carpeta.get_public_url(carpeta_supabase)
        logger.info(f"Imagen convertida a WebP y cargada en Supabase: {webp_url}")
        
        return webp_url
        
    except Exception as e:
        logger.error(f"Error al procesar imagen en Supabase: {e}")
        raise