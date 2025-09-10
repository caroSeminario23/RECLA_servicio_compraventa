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
        db.text,
        unique=True,
        nullable=True
    )

    precio = db.Column(
        db.numeric(3, 2),
        nullable=True
    )

    cantidad = db.Column(
        db.integer,
        nullable=True
    )

    descripcion = db.Column(
        db.string(150),
        nullable=True
    )

    comprado = db.Column(
        db.boolean,
        nullable=True
    )

    tipo = db.Column(
        db.integer,
        nullable=True
    )

    material = db.Column(
        db.string(7),
        nulable=True
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
                material):
        self.id_vendedor = id_vendedor
        self.url_foto = url_foto
        self.precio = precio
        self.cantidad = cantidad
        self.descripcion = descripcion
        self.comprado = comprado
        self.tipo = tipo
        self.material = material
