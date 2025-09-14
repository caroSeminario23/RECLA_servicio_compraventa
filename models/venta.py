from utils.db import db

class Producto(db.Model):
    _tablename_ = 'venta'
    id_producto = db.Column(
        db.Integer,
        primary_key=True,
        nulable=True
    )

    id_comprador = db.Column(
        db.Integer,
        primary_key=True,
        nulable=True
    )
