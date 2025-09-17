from utils.db import db

class Venta(db.Model):
    __tablename__ = 'venta'
    id_producto = db.Column(
        db.Integer,
        db.ForeignKey('producto.id_producto'),
        primary_key=True,
        nullable=True
    )

    id_comprador = db.Column(
        db.Integer,
        primary_key=True,
        nullable=True
    )
    id_vendedor = db.Column(
        db.Integer,
        nullable=True
    )
