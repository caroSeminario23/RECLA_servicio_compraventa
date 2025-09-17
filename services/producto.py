from flask import Blueprint, request, jsonify, make_response
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from utils.db import db
import requests

from models.producto import Producto
from schemas.producto import producto_registro_schema
from schemas.producto import producto_consulta_schema
from schemas.producto import producto_detalle_schema
from schemas.producto import producto_filtrado_schema



producto_routes = Blueprint("producto_routes", __name__)



#registro de producto
@producto_routes.route('/registro_producto', methods=['POST'])
def registro_producto():
    try:
        datos = producto_registro_schema.load(request.get_json())
    except ValidationError as err:
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
    except IntegrityError as err:
        return make_response(jsonify({
            "message": str(err.orig),
            "status": 400
            }),400)
    data = {
        "message": "Producto registrado exitosamente",
        "status": 201,
    }
    return make_response(jsonify(data), 201)




#listar productos por tipo y material
@producto_routes.route('/filtrar_productos', methods=['POST'])
def listar_productos_por_tipo():
    data = request.get_json()
    tipos = data.get("tipo", [])  # Espera lista de enteros
    materiales = data.get("material", "")  # Espera string tipo "1,2"

    # Filtrar primero por tipo y comprado
    query = Producto.query
    if tipos:
        query = query.filter(Producto.tipo.in_(tipos))
    productos = query.filter(Producto.comprado == False).all()

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
        return make_response(jsonify({
            "message": "No se encontraron productos con esos criterios",
            "status": 404
        }), 404)
    else:
        results = producto_consulta_schema.dump(productos_filtrados, many=True)
        data = {
            "message": "Productos encontrados",
            "status": 200,
            "data": results
        }
        return make_response(jsonify(data), 200)





#Detalle producto
@producto_routes.route('/producto_detalle', methods=['POST'])
def detalle_producto():
    try:
        datos = producto_detalle_schema.load(request.get_json())
    except ValidationError as err:
        return make_response(jsonify({"errors": err.messages, "status": 400}), 400)

    id_producto = datos["id_producto"]


    producto = Producto.query.filter_by(id_producto=id_producto).first()

    if not producto:
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
    try:
        #response = requests.post('http://127.0.0.1:5000/usuario_routes/obtener_username_vendedor', json=payload)
        response = {
            "data": {
                "username": "Esmeraldo"
            },
            "message": "Vendedor encontrado",
            "status": 200
        }
        data['data']['nombre_vendedor'] = response['data']['username']
        '''if response.status == 200:
            usuario = response.json()
            # Extraer el nombre del vendedor del campo correcto
            data['data']['nombre_vendedor'] = usuario['data']['username']
        else:
            data['data']['nombre_vendedor'] = 'Desconocido'''
    except requests.RequestException:
        data['data']['nombre_vendedor'] = 'Desconocido'

    return make_response(jsonify(data), 200)



##Producto consulta
@producto_routes.route('/consulta_producto', methods=['POST'])
def consulta_producto():
    try:
        datos = producto_consulta_schema.load(request.get_json())
    except ValidationError as err:
        return make_response(jsonify({"errors": err.messages, "status": 400}), 400)

    id_producto = datos["id_producto"]

    producto = Producto.query.filter_by(id_producto=id_producto).first()

    if not producto:
        return make_response(jsonify({
            "message": "Producto no encontrado",
            "status": 404
        }), 404)
    else:
        result = producto_consulta_schema.dump(producto)
        data = {
            "message": "Producto encontrado",
            "status": 200,
            "data": result
        }
        return make_response(jsonify(data), 200)