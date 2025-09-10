from flask import Blueprint, request, jsonify, make_response
from marshmallow import ValidationError
from werkzeug.security import check_password_hash
from sqlalchemy.exc import IntegrityError
from utils.db import db

from models.producto import Producto
from schemas.producto import producto_registro_schema, producto_registro_schemas
from schemas.producto import id_producto_schema
from schemas.producto import id_vendedor_schema

#registro de producto
