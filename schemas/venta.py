from utils.ma import ma
from marshmallow import fields, validates, ValidationError

from models.venta import Venta

#Schemas
class VentaRegistroSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Venta
        #load_instance = True
        include_fk = True
        fields = (
            'id_producto',
            'id_comprador',
            'id_vendedor'
        )

#Instancia de schemas
venta_registro_schema = VentaRegistroSchema()
venta_registro_schemas = VentaRegistroSchema(many=True)