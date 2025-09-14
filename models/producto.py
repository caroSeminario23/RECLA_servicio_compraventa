from utils.db import db

class Producto(db.Model):
    _tablename_ = 'producto'

    #Características del producto
    id_producto = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True,
        nullable=True
    )

    id_vendedor = db.Column(
        db.Integer,
        nullable=True
    )

    url_foto = db.Column(
        db.Text,
        unique=True,
        nullable=True
    )

    precio = db.Column(
        db.Numeric(3, 2),
        nullable=True
    )

    cantidad = db.Column(
        db.Integer,
        nullable=True
    )

    descripcion = db.Column(
        db.String(150),
        nullable=True
    )

    comprado = db.Column(
        db.Boolean,
        nullable=True
    )

    tipo = db.Column(
        db.Integer,
        nullable=True
    )

    material = db.Column(
        db.String(7),
        nullable=True
    )
    nombre = db.Column(
        db.String(10),
        nullable=True
    )

    #Objeto
    def _init_(self,
                id_vendedor,
                url_foto,
                precio,
                cantidad,
                descripcion,
                comprado,
                tipo,
                material,
                nombre):
        self.id_vendedor = id_vendedor
        self.url_foto = url_foto
        self.precio = precio
        self.cantidad = cantidad
        self.descripcion = descripcion
        self.comprado = comprado
        self.tipo = tipo
        self.material = material
        self.nombre = nombre
