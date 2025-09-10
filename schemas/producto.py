from utils.ma import ma
from marshmallow import fields, validates, ValidationError

from models.producto import Producto

#validaciones
#SCHEMAS
class ProductoResgistroSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Producto
        fields = (
            'id_producto',
            'id_vendedor',
            'url_foto',
            'precio',
            'cantidad',
            'descripcion',
            'comprado',
            'tipo',
            'material'
        )
        
class IdProductoSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Producto
        fields = ('id_producto',)

class idVendedorSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Producto
        fields = ('id_vendedor',)

#Instancia de schemas
producto_registro_schema = ProductoResgistroSchema()
producto_registro_schemas = ProductoResgistroSchema(many=True)

id_producto_schema = IdProductoSchema()
id_producto_schemas = IdProductoSchema(many=True)

id_vendedor_schema = idVendedorSchema()
id_vendedor_schemas = idVendedorSchema(many=True)