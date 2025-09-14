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
            'material',
            'nombre'
        )
class ProductoConsultaSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Producto
        fields = (
            'id_producto',
            'url_foto',
            'precio',
            'cantidad',
            'nombre'
        )        
class ProductoDetalleSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Producto
        fields = (
            'id_producto',
            'nombre_vendedor',
            'descripcion',
            'tipo',
            'material'
        )
class ProductoFiltradoSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Producto
        fields = (
            'tipo',
            'material'
        )



#Instancia de schemas
producto_registro_schema = ProductoResgistroSchema()
producto_registro_schemas = ProductoResgistroSchema(many=True)

producto_consulta_schema = ProductoConsultaSchema()
producto_consulta_schemas = ProductoConsultaSchema(many=True)

producto_detalle_schema = ProductoDetalleSchema()
producto_detalle_schemas = ProductoDetalleSchema(many=True)

producto_filtrado_schema = ProductoFiltradoSchema()
producto_filtrado_schemas = ProductoFiltradoSchema(many=True)
