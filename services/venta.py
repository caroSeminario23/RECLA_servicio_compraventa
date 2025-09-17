from flask import Blueprint, request, jsonify, make_response
from marshmallow import ValidationError
from werkzeug.security import check_password_hash
from sqlalchemy.exc import IntegrityError
from utils.db import db
from models.venta import Venta
from schemas.venta import venta_registro_schema
import requests

venta_routes = Blueprint("venta_routes", __name__)

#registro de venta
@venta_routes.route('/registro_venta', methods=['POST'])
def registro_venta():
    try:
        datos = venta_registro_schema.load(request.get_json())
    except ValidationError as err:
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
    except IntegrityError as err:
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
    try:
        #response = requests.post('http://127.0.0.1:5000/venta_routes/obtener_contador', json=payload)
        response = {
            "message": "Contador actualizado exitosamente",
            "status": 200
        }
        if response["status"] == 200:
            print(response["message"])
    except requests.RequestException as e:
        print(f"Error en la solicitud: {e}")

    data = {
        "message": "Venta registrada exitosamente",
        "venta": venta_registro_schema.dump(nueva_venta)
    }
    return make_response(jsonify(data), 201)
    