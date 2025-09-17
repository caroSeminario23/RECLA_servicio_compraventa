from flask import Blueprint, request, jsonify, make_response
from marshmallow import ValidationError
from werkzeug.security import check_password_hash
from sqlalchemy.exc import IntegrityError
from utils.db import db
from models.venta import Venta
from schemas.venta import venta_registro_schema

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

    nueva_venta = Venta(
        id_producto=id_producto,
        id_comprador=id_comprador
    )
    try:
        db.session.add(nueva_venta)
        db.session.commit()
    except IntegrityError as err:
        return make_response(jsonify({
            "message": str(err.orig),
            "status": 400
            }),400)
    data = {
        "message": "Venta registrada exitosamente",
        "venta": venta_registro_schema.dump(nueva_venta)
    }
    return make_response(jsonify(data), 201)