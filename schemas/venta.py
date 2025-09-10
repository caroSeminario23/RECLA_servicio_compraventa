from utils.ma import ma
from marshmallow import fields, validates, ValidationError

from models.venta import Venta

#Schemas
class VentaRegistroSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Venta
        fields = (
            'id_producto',
            'id_comprador'
        )

#Instancia de schemas
venta_registro_schema = VentaRegistroSchema()
venta_registro_schemas = VentaRegistroSchema(many=True)